import copy, unittest, tempfile, pathlib, json, os
from unittest.mock import patch
import publication_guard as guard
from publication_guard import check
from approval_revision import revision
class Guard(unittest.TestCase):
 def setUp(self):
  self.a={'updated':'x','tz':'Asia/Yekaterinburg','doctors':{'a':{'name':'A'}},'months':{'2026-12':{'status':'preliminary','version':1,'duty':{'2026-12-01':['a']},'confirm':{'version':1,'need':['a'],'confirmed':[],'published':'2026-11-16T00:00:00Z','disagreed':0}}}}
  self.b=copy.deepcopy(self.a)
 def test_intermediate(self):
  self.b['months']['2026-12']['confirm']['confirmed']=['a'];self.assertEqual(check(self.a,self.b,['dezhurstva/data/schedule.json']),['2026-12'])
 def test_reassignment(self):
  self.b['months']['2026-12']['duty']['2026-12-01']=[]
  with self.assertRaises(ValueError):check(self.a,self.b,[])
 def test_sibling(self):
  with self.assertRaises(ValueError):check(self.a,self.b,['pso/index.html'])
 def test_final(self):
  m=self.b['months']['2026-12'];m['status']='final';m['confirm']['confirmed']=['a'];m['finalization']={'digest':revision(m,self.b)}
  self.assertEqual(check(self.a,self.b,[]),['2026-12'])
 def test_final_review_notice(self):
  self.a['months']['2026-12']['status']='final';self.b=copy.deepcopy(self.a)
  self.b['months']['2026-12']['confirm']['reviewRequired']=True
  self.b['months']['2026-12']['confirm']['reviewCheckedAt']='2026-11-17T00:00:00Z'
  self.assertEqual(check(self.a,self.b,[]),['2026-12'])
 def test_new_generated_and_hostile_untracked(self):
  self.b['months']['2026-12']['confirm']['confirmed']=['a']
  with tempfile.TemporaryDirectory() as temp:
   oldcwd=os.getcwd();os.chdir(temp)
   try:
    pathlib.Path('dezhurstva/data').mkdir(parents=True);pathlib.Path('dezhurstva/files').mkdir()
    pathlib.Path('dezhurstva/data/schedule.json').write_text(json.dumps(self.b))
    for name in ('hashes.json','pdf.json'):pathlib.Path('dezhurstva/files/'+name).write_text('{}')
    untracked=['dezhurstva/files/2026-12.pdf','dezhurstva/files/2026-12-print.pdf']
    def command(args):
     if args[1]=='show':return json.dumps(self.a).encode() if args[2].endswith('schedule.json') else b'{}'
     if args[1]=='diff':return b'dezhurstva/data/schedule.json\n'
     if args[1]=='ls-files':return ('\n'.join(untracked)+'\n').encode()
     raise AssertionError(args)
    with patch.object(guard.subprocess,'check_output',side_effect=command),patch('sys.argv',['guard','--base','source']):guard.main()
    untracked.append('other-app/index.html')
    with patch.object(guard.subprocess,'check_output',side_effect=command),patch('sys.argv',['guard','--base','source']),self.assertRaises(ValueError):guard.main()
   finally:os.chdir(oldcwd)
 def test_existing_final(self):
  self.a['months']['2026-12']['status']='final'
  with self.assertRaises(ValueError):check(self.a,self.b,[])
if __name__=='__main__':unittest.main()

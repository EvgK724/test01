import json,pathlib,subprocess,unittest
from approval_revision import revision
class Parity(unittest.TestCase):
 def test_unicode(self):
  m={'version':2,'title':'Декабрь','duty':{'2026-12-01':['a']},'confirm':{'version':2,'need':['a'],'published':'2026-11-16T00:00:00Z','confirmed':['a']},'status':'final','final_at':'ignored'}
  d={'tz':'Asia/Yekaterinburg','doctors':{'a':{'name':'Ёжик','code':'Ё'}}}
  script="global.Utilities={DigestAlgorithm:{SHA_256:1},Charset:{UTF_8:1},computeDigest:(_,s)=>[...require('crypto').createHash('sha256').update(s).digest()]};const {revision}=require('./Code.gs'); const x=JSON.parse(process.argv[1]);process.stdout.write(revision(x.m,x.d));"
  actual=subprocess.check_output(['node','-e',script,json.dumps({'m':m,'d':d},ensure_ascii=False)],cwd=pathlib.Path(__file__).parent).decode()
  self.assertEqual(actual,revision(m,d))
if __name__=='__main__':unittest.main()

import io,json,os,pathlib,tempfile,unittest
from unittest.mock import patch
import pages_release as p
class Pages(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.cwd=os.getcwd();os.chdir(self.tmp.name)
  pathlib.Path('dezhurstva/data').mkdir(parents=True);pathlib.Path('dezhurstva/files').mkdir()
  pathlib.Path('dezhurstva/data/schedule.json').write_text(json.dumps({'months':{'2026-12':{'confirm':{'version':1}}}}))
  pathlib.Path('dezhurstva/files/pdf.json').write_text('{}');pathlib.Path('dezhurstva/index.html').write_text('test');pathlib.Path('dezhurstva/files/2026-12.xlsx').write_bytes(b'xlsx')
  self.sha='a'*40;self.commit=self.sha;self.source={'branch':'main','path':'/'}
 def tearDown(self):os.chdir(self.cwd);self.tmp.cleanup()
 def api(self,path,method='GET'):
  if path=='/pages':return {'build_type':'legacy','source':self.source}
  if path=='/commits/main':return {'sha':self.sha}
  if path=='/pages/builds':return {'url':p.API+'/pages/builds/42'}
  if path=='/pages/builds/latest':return {'status':'built','commit':self.commit}
  raise AssertionError(path)
 def live(self,url,**kw):return io.BytesIO(pathlib.Path(url.removeprefix(p.LIVE).split('?')[0]).read_bytes())
 def test_publish(self):
  with patch.object(p,'request',side_effect=self.api),patch.object(p.urllib.request,'urlopen',side_effect=self.live),patch('sys.argv',['x','--commit',self.sha]):p.main()
 def test_different_commit(self):
  self.commit='b'*40
  with patch.object(p,'request',side_effect=self.api),patch('sys.argv',['x','--commit',self.sha,'--wait','0']),self.assertRaises((ValueError,TimeoutError)):p.main()
 def test_main_race(self):
  api=self.api
  def raced(path,method='GET'):return {'sha':'b'*40} if path=='/commits/main' else api(path,method)
  with patch.object(p,'request',side_effect=raced),patch('sys.argv',['x','--commit',self.sha]),self.assertRaises(ValueError):p.main()
 def test_latest_url(self):
  api=self.api
  def latest(path,method='GET'):
   if path=='/pages/builds':return {'url':p.API+'/pages/builds/latest'}
   if path=='/pages/builds/latest':return {'status':'built','commit':self.sha}
   return api(path,method)
  with patch.object(p,'request',side_effect=latest),patch.object(p.urllib.request,'urlopen',side_effect=self.live),patch('sys.argv',['x','--commit',self.sha]):p.main()
 def test_response_url_is_not_followed(self):
  api=self.api
  def hostile(path,method='GET'):
   if path=='/pages/builds':return {'url':'https://example.invalid/steal'}
   return api(path,method)
  with patch.object(p,'request',side_effect=hostile),patch.object(p.urllib.request,'urlopen',side_effect=self.live),patch('sys.argv',['x','--commit',self.sha]):p.main()
 def test_main_moved_even_when_expected_build_completed(self):
  api=self.api;calls=0
  def raced(path,method='GET'):
   nonlocal calls
   if path=='/commits/main':
    calls+=1
    return {'sha':self.sha if calls==1 else 'b'*40}
   return api(path,method)
  with patch.object(p,'request',side_effect=raced),patch('sys.argv',['x','--commit',self.sha]),self.assertRaisesRegex(ValueError,'main moved'):p.main()
 def test_expected_build_error(self):
  api=self.api
  def failed(path,method='GET'):
   if path=='/pages/builds/latest':return {'status':'errored','commit':self.sha}
   return api(path,method)
  with patch.object(p,'request',side_effect=failed),patch('sys.argv',['x','--commit',self.sha]),self.assertRaisesRegex(ValueError,'Pages build failed'):p.main()
 def test_stale_build_error_is_not_our_result(self):
  api=self.api
  def stale(path,method='GET'):
   if path=='/pages/builds/latest':return {'status':'errored','commit':'b'*40}
   return api(path,method)
  with patch.object(p,'request',side_effect=stale),patch('sys.argv',['x','--commit',self.sha,'--wait','0']),self.assertRaises(TimeoutError):p.main()
 def test_no_source_migration(self):
  self.source={'branch':'main','path':'/docs'}
  with patch.object(p,'request',side_effect=self.api),patch('sys.argv',['x','--commit',self.sha,'--wait','0']),self.assertRaises((ValueError,TimeoutError)):p.main()
 def test_recovered_no_extra_build(self):
  with patch.object(p,'request',side_effect=AssertionError('No API needed')),patch.object(p.urllib.request,'urlopen',side_effect=self.live),patch('sys.argv',['x','--commit',self.sha,'--if-needed']):p.main()
if __name__=='__main__':unittest.main()

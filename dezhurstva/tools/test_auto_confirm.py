import unittest,datetime as dt
from auto_confirm import validate,revision,digest
class Tests(unittest.TestCase):
 def setUp(self):
  self.m={'version':1,'status':'preliminary','duty':{'2026-12-01':['a']},'confirm':{'version':1,'published':'2026-11-16T00:00:00Z','need':['a']}}
  self.d={'tz':'Asia/Yekaterinburg','doctors':{'a':{'name':'A'}}};self.now=dt.datetime(2026,11,16,12,tzinfo=dt.timezone.utc)
  self.a=dict(receiptIds=[],ok=True,schema=1,identity='self-declared',month='2026-12',version=1,digest=revision(self.m,self.d),rosterHash=digest(['a']),nonce='nonce',sourceComplete=True,required=1,agreed=1,disagreed=0,ambiguous=0,waiting=0,allAgreed=True,checkedAt='2026-11-16T12:00:00Z')
 def call(self):return validate(self.a,self.m,'2026-12','nonce',self.now,self.d)
 def test_all(self):self.assertTrue(self.call())
 def test_stale(self):
  self.a['checkedAt']='2026-11-16T11:50:00Z'
  with self.assertRaises(ValueError):self.call()
 def test_wrong_nonce(self):
  self.a['nonce']='wrong'
  with self.assertRaises(ValueError):self.call()
 def test_truthy(self):
  self.a['ok']='true'
  with self.assertRaises(ValueError):self.call()
 def test_rename(self):
  self.d['doctors']['a']['name']='B'
  with self.assertRaises(ValueError):self.call()
 def test_disagree(self):
  self.a.update(agreed=0,disagreed=1,allAgreed=False);self.assertFalse(self.call())
 def test_bad_sum(self):
  self.a['waiting']=1
  with self.assertRaises(ValueError):self.call()
 def test_public_identity_fields_rejected(self):
  self.a['confirmed']=['a']
  with self.assertRaises(ValueError):self.call()
 def test_status_not_revision(self):
  before=revision(self.m,self.d);self.m['status']='final';self.assertEqual(before,revision(self.m,self.d))
if __name__=='__main__':unittest.main()

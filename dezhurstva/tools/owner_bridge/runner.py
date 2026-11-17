"""Reviewed-host adapter. Disabled until environment config is explicitly installed.
No private owner Google code or ACL identities are distributed in this package.
"""
import datetime,json,os,pathlib,re,subprocess,urllib.request,urllib.parse
from queue_consumer import consume
from delivery import git
from real_renderer import render
from release_boundary import sha
class Redirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,url):
  u=urllib.parse.urlsplit(url)
  if u.scheme!='https' or u.hostname!='script.googleusercontent.com' or u.username or u.password or u.port not in (None,443):raise ValueError('UNAPPROVED_REDIRECT')
  return super().redirect_request(req,fp,code,msg,headers,url)
def endpoint_from_env():
 endpoint=os.environ.get('DUTY_OWNER_READER_URL','')
 if not re.fullmatch(r'https://script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec',endpoint):raise ValueError('APPROVED_READER_NOT_CONFIGURED')
 return endpoint
def fetch(endpoint,action,nonce,approval_id=None):
 if action not in ('catalog','read') or not re.fullmatch('[0-9a-f]{32}',nonce):raise ValueError('REQUEST_SCHEMA')
 q={'action':action,'nonce':nonce}
 if action=='read':
  if not re.fullmatch('[0-9a-f]{32}',approval_id or ''):raise ValueError('APPROVAL_ID')
  q['approvalId']=approval_id
 req=urllib.request.Request(endpoint+'?'+urllib.parse.urlencode(q),headers={'Cache-Control':'no-cache'})
 with urllib.request.build_opener(Redirect()).open(req,timeout=30) as r:
  raw=r.read(32769)
  if r.status!=200 or len(raw)>32768:raise ValueError('HTTP_OR_SIZE')
  return json.loads(raw)
def main():
 repo=pathlib.Path.cwd();expected=os.environ.get('DUTY_OWNER_SOURCE_SHA','')
 if os.environ.get('DUTY_OWNER_RUNNER_ENABLED')!='true' or not re.fullmatch('[0-9a-f]{40}',expected):raise ValueError('DEPLOYMENT_NOT_ENABLED')
 # Pin executable sources to reviewed release, while later data-only commits may advance main.
 paths=git(repo,'ls-files','dezhurstva/tools','.github/workflows/duty-owner-drafts.yml').splitlines()
 pinned=git(repo,'ls-tree','-r','--name-only',expected,'--','dezhurstva/tools','.github/workflows/duty-owner-drafts.yml').splitlines()
 if set(paths)!=set(pinned):raise ValueError('SOURCE_SET_CHANGED')
 for rel in paths:
  old=subprocess.check_output(['git','show',expected+':'+rel],cwd=repo)
  if (repo/rel).read_bytes()!=old:raise ValueError('SOURCE_PIN_CHANGED')
 endpoint=endpoint_from_env()
 def renderer(d,v,r,h):
  pins={p:sha((repo/p).read_bytes()) for p in git(repo,'ls-files','dezhurstva').splitlines()}
  return render(d,v,r,h,pins)
 def pages(commit):
  subprocess.run(['python','-B','dezhurstva/tools/pages_release.py','--commit',commit,'--if-needed'],cwd=repo,check=True,capture_output=True)
 result=consume(repo,lambda n:fetch(endpoint,'catalog',n),lambda aid,n:fetch(endpoint,'read',n,aid),lambda:datetime.datetime.now(datetime.timezone.utc),pages,renderer)
 # No approval IDs, endpoint URLs, raw payloads or identities in console output.
 print(json.dumps({'empty':result['empty'],'results':[{'status':r['status'],'pages':r.get('pages'),'organizerReviewRequired':r.get('organizerReviewRequired')} for r in result['results']]}))
 if any(r.get('organizerReviewRequired') or r.get('pages')!='VERIFIED' for r in result['results']):raise ValueError('PUBLISHED_STATE_REQUIRES_REVIEW')
if __name__=='__main__':
 try:main()
 except Exception:
  print('Owner draft runner stopped; preserve existing state and inspect restricted diagnostics.');raise SystemExit(1)

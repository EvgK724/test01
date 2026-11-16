"""Request EXISTING legacy Pages build, poll exact build, verify live bytes.
Uses ephemeral GITHUB_TOKEN; never creates/updates Pages settings or credentials.
"""
import argparse,hashlib,json,os,pathlib,time,urllib.request,urllib.error,subprocess
API='https://api.github.com/repos/EvgK724/test01'
LIVE='https://evgk724.github.io/test01/'
def request(path,method='GET'):
 req=urllib.request.Request(API+path,method=method,headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
 with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
def main():
 p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--wait',type=int,default=420);p.add_argument('--if-needed',action='store_true');a=p.parse_args()
 if not __import__('re').fullmatch('[0-9a-f]{40}',a.commit):raise ValueError('sha')
 if a.if_needed:
  schedule=json.loads(pathlib.Path('dezhurstva/data/schedule.json').read_text())
  checkfiles=['dezhurstva/data/schedule.json','dezhurstva/index.html']
  checkfiles += ['dezhurstva/files/'+mk+'.xlsx' for mk,m in schedule['months'].items() if m.get('confirm')]
  pp=pathlib.Path('dezhurstva/files/pdf.json')
  if pp.exists():checkfiles += ['dezhurstva/files/'+mk+suffix for mk in json.loads(pp.read_text()) for suffix in ('.pdf','-print.pdf')]
  checkfiles += [str(p) for p in pathlib.Path('dezhurstva/cal').glob('*.ics')]
  same=True
  for path in checkfiles:
   try:
    with urllib.request.urlopen(LIVE+path+'?verify='+a.commit,timeout=30) as r:matches=r.read(16*1024*1024)==pathlib.Path(path).read_bytes()
   except urllib.error.HTTPError as e:
    if e.code!=404:raise
    matches=False
   same=same and matches
  if same:print(json.dumps({'unchanged':True}));return
 # Refuse source migration or surprise source path.
 site=request('/pages')
 if site.get('build_type') not in ('legacy',None) or site.get('source')!={'branch':'main','path':'/'}:raise ValueError('unexpected Pages source')
 main=request('/commits/main')['sha']
 if main!=a.commit:raise ValueError('main moved; retry from fresh checkout')
 request('/pages/builds',method='POST')
 # API response URLs can vary. Poll only our fixed repository endpoint;
 # never follow a URL supplied in the response, and require exact commit.
 build_id='latest'
 deadline=time.monotonic()+a.wait
 while True:
  status=request('/pages/builds/'+build_id)
  if request('/commits/main')['sha']!=a.commit:raise ValueError('main moved during build; retry revalidation')
  if status.get('commit')==a.commit:
   if status.get('status')=='built':break
   if status.get('status')=='errored':raise ValueError('Pages build failed')
  if time.monotonic()>=deadline:raise TimeoutError('Pages pending; retry publication only')
  time.sleep(15)
 if status.get('commit')!=a.commit:raise ValueError('Pages built different SHA; revalidate')
 schedule=json.loads(pathlib.Path('dezhurstva/data/schedule.json').read_text())
 files=['dezhurstva/data/schedule.json','dezhurstva/index.html']
 files += ['dezhurstva/files/'+mk+'.xlsx' for mk,m in schedule['months'].items() if m.get('confirm')]
 pdf=json.loads(pathlib.Path('dezhurstva/files/pdf.json').read_text())
 files += ['dezhurstva/files/'+mk+suffix for mk in pdf for suffix in ('.pdf','-print.pdf')]
 files += [str(p) for p in pathlib.Path('dezhurstva/cal').glob('*.ics')]
 for f in files:
  expected=hashlib.sha256(pathlib.Path(f).read_bytes()).digest()
  for attempt in range(5):
   with urllib.request.urlopen(LIVE+f+'?verify='+a.commit,timeout=30) as r: actual=hashlib.sha256(r.read(16*1024*1024+1)).digest()
   if actual==expected:break
   if attempt==4:raise ValueError('live bytes differ: '+f)
   time.sleep(10)
 print(json.dumps({'published':a.commit,'build':build_id,'verified':files}))
if __name__=='__main__':main()

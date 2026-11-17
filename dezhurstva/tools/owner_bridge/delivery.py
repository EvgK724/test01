"""Local-only bridge prototype. No live URL/credentials/workflow installed.
Use one concurrency group with existing Duty job; still enforce remote CAS.
Google snapshot vs Git commit is NOT atomic: late revoke requires human review.
"""
import copy,datetime,json,pathlib,re,secrets,subprocess
from public_digest import digest
FIXED_ENDPOINT='UNCONFIGURED_REQUIRES_OWNER_APPROVAL'

def checked(response,nonce,now):
 base={'schema','kind','nonce','checkedAt','status'}
 if type(response)is not dict or response.get('schema')!=1 or type(response.get('schema'))is not int or response.get('kind')!='APPROVED_PRELIMINARY' or response.get('nonce')!=nonce:raise ValueError('SCHEMA')
 at=datetime.datetime.fromisoformat(response['checkedAt'].replace('Z','+00:00'))
 if at.tzinfo is None or not 0<=(now-at).total_seconds()<=120:raise ValueError('STALE')
 if response['status']=='UNAVAILABLE':
  if set(response)!=base:raise ValueError('SCHEMA')
  raise ValueError('REVOKED_STALE_OR_UNAPPROVED')
 if response['status']!='READY' or set(response)!=base|{'payload','payloadHash'}:raise ValueError('SCHEMA')
 p=response['payload']
 if set(p)!={'approvalId','draft','version','baseVersion'} or not re.fullmatch('[0-9a-f]{32}',p['approvalId']):raise ValueError('PAYLOAD')
 if type(p['version'])is not int or type(p['baseVersion'])is not int or p['baseVersion']<0 or p['version']!=p['baseVersion']+1:raise ValueError('VERSION')
 if digest(p)!=response['payloadHash']:raise ValueError('HASH')
 d=p['draft']
 if set(d)!={'month','order','shift','off','duty','marks'} or not re.fullmatch(r'20\d\d-(0[1-9]|1[0-2])',d['month']) or d['month']<'2027-01':raise ValueError('DRAFT')
 if not isinstance(d['order'],list) or not d['order'] or len(set(d['order']))!=len(d['order']) or any(not re.fullmatch(r'[a-z0-9_-]+',x) for x in d['order']):raise ValueError('ROSTER')
 import calendar
 days=[f"{d['month']}-{i:02}" for i in range(1,calendar.monthrange(int(d['month'][:4]),int(d['month'][5:]))[1]+1)]
 if sorted(d['duty'])!=days or any(type(v)is not list or len(v)!=1 or v[0]not in d['order'] for v in d['duty'].values()):raise ValueError('DUTY')
 if type(d['off'])is not list or len(set(d['off']))!=len(d['off']) or any(x not in days for x in d['off']):raise ValueError('OFF')
 if set(d['shift'])!={'work','off'} or any(type(v)is not list or len(v)!=2 or any(not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d',x) for x in v) for v in d['shift'].values()):raise ValueError('SHIFT')
 from vacation_marks import validate
 validate(d)
 return copy.deepcopy(p)

def git(repo,*args):return subprocess.check_output(['git',*args],cwd=repo,text=True).strip()
def read(repo,path):return json.loads((pathlib.Path(repo)/path).read_text())
RECEIPTS='dezhurstva/data/publication-receipts.json'
SCHEDULE='dezhurstva/data/schedule.json'
def receipt_state(receipts,p):
 matches=[r for r in receipts if r['approvalId']==p['approvalId']]
 if len(matches)>1:raise ValueError('DUPLICATE_RECEIPTS')
 if matches:
  if matches[0]['payloadHash']!=digest(p):raise ValueError('APPROVAL_REUSE_DIFFERENT_PAYLOAD')
  return True
 return False

def publication_commit(repo,approval_id):
 # Durable receipt history, not memory or local runner state; no force-history claims.
 for commit in git(repo,'log','--reverse','--format=%H','origin/main','--',RECEIPTS).splitlines():
  rs=json.loads(git(repo,'show',f'{commit}:{RECEIPTS}'))
  if any(r['approvalId']==approval_id for r in rs):return commit
 raise ValueError('RECEIPT_COMMIT_NOT_FOUND')
def finish_committed(repo,commit,receipt,pages_verify,needs_review,recovered):
 result={'status':'COMMITTED_REQUIRES_REVIEW' if needs_review else 'ALREADY_COMMITTED' if recovered else 'COMMITTED',
         'commit':commit,'publicationCommit':publication_commit(repo,receipt['approvalId']),
         'organizerReviewRequired':needs_review,'approvalId':receipt['approvalId']}
 # Outcome remains reportable even if Pages is down. Receipt mandates recheck on every retry.
 try:pages_verify(commit);result['pages']='VERIFIED'
 except Exception:result['pages']='FAILED_RETRY_SAME_COMMIT';result['pagesError']='PAGES_UNAVAILABLE'
 return result

def deliver(repo,trusted_transport,clock,pages_verify,*,renderer=None,push=None,before_push=None,expected_approval_id=None):
 # Callbacks are host capabilities, NOT upload parameters. Real fixed endpoint transport not configured.
 if git(repo,'status','--porcelain'):raise ValueError('DIRTY')
 git(repo,'fetch','origin','main');base=git(repo,'rev-parse','origin/main')
 if git(repo,'rev-parse','HEAD')!=base:raise ValueError('LOCAL_BASE_CHANGED')
 rp=pathlib.Path(repo)/RECEIPTS;receipts=json.loads(rp.read_text()) if rp.exists() else []
 # Inspect durable history FIRST. Revocation/outage cannot hide committed outcomes.
 nonce=secrets.token_hex(16)
 try:p=checked(trusted_transport(nonce),nonce,clock())
 except Exception:
  matches=[r for r in receipts if r['approvalId']==expected_approval_id] if expected_approval_id else []
  if len(matches)!=1:raise
  return finish_committed(repo,base,matches[0],pages_verify,True,True)
 if expected_approval_id is not None and p['approvalId']!=expected_approval_id:raise ValueError('APPROVAL_SELECTOR_MISMATCH')
 if receipt_state(receipts,p):
  return finish_committed(repo,base,next(r for r in receipts if r['approvalId']==p['approvalId']),pages_verify,False,True)
 data=read(repo,SCHEDULE);mk=p['draft']['month'];old=data['months'].get(mk,{})
 if old.get('version',0)!=p['baseVersion']:raise ValueError('BASE_VERSION_CHANGED')
 if any(x not in data['doctors'] for x in p['draft']['order']):raise ValueError('UNKNOWN_DOCTOR')
 if not callable(renderer):raise ValueError('TRUSTED_REAL_RENDERER_REQUIRED')
 files=renderer(p['draft'],p['version'],repo,base)
 # Renderer returns reviewed artifacts only; durable receipt is added by bridge itself.
 if type(files)is not dict or SCHEDULE not in files or 'dezhurstva/index.html' not in files or RECEIPTS in files:raise ValueError('RENDERER_FILES')
 permitted={SCHEDULE,'dezhurstva/index.html','dezhurstva/files/hashes.json','dezhurstva/files/pdf.json'}|{f'dezhurstva/cal/{x}.ics' for x in list(data['doctors'])+['all']}|{f'dezhurstva/files/{mk}{x}' for x in ('.xlsx','.pdf','-print.pdf')}
 if not set(files)<=permitted or any(type(v)is not bytes for v in files.values()):raise ValueError('RENDERER_ALLOWLIST')
 generated=json.loads(files[SCHEDULE]);m=generated['months'][mk]
 if m.get('status')!='preliminary' or m.get('version')!=p['version'] or any(m.get(k)!=p['draft'][k] for k in ('order','shift','off','duty','marks')):raise ValueError('RENDERER_BINDING')
 if {k:v for k,v in generated['months'].items() if k!=mk}!={k:v for k,v in data['months'].items() if k!=mk}:raise ValueError('OTHER_MONTH_CHANGED')
 receipt={'approvalId':p['approvalId'],'payloadHash':digest(p),'month':mk,'version':p['version'],'recoveryPolicy':'RECHECK_OWNER_OR_REQUIRE_REVIEW'};receipts.append(receipt)
 files[RECEIPTS]=(json.dumps(receipts,ensure_ascii=False,sort_keys=True)+'\n').encode()
 for path,content in files.items():
  dst=pathlib.Path(repo)/path;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(content)
 paths=set(git(repo,'status','--porcelain').splitlines())
 # Stage only exact known paths; never git add directory or staging workspace.
 git(repo,'add','--',*sorted(files))
 if set(git(repo,'diff','--cached','--name-only').splitlines())!=set(files):raise ValueError('STAGED_ALLOWLIST')
 nonce=secrets.token_hex(16);fresh=checked(trusted_transport(nonce),nonce,clock())
 if fresh!=p:raise ValueError('OWNER_STATE_CHANGED')
 git(repo,'fetch','origin','main')
 if git(repo,'rev-parse','origin/main')!=base:raise ValueError('REMOTE_BASE_CHANGED')
 git(repo,'-c','user.name=github-actions[bot]','-c','user.email=41898282+github-actions[bot]@users.noreply.github.com','commit','-qm','Publish approved preliminary schedule with durable receipt')
 commit=git(repo,'rev-parse','HEAD')
 # Race hook only for synthetic tests. Real normal push rejects concurrent non-FF update.
 if before_push:before_push()
 try:
  if push:push(repo)
  else:git(repo,'push','origin','HEAD:main')
 except Exception:
  git(repo,'fetch','origin','main')
  remote=git(repo,'rev-parse','origin/main')
  raw=git(repo,'show',f'{remote}:{RECEIPTS}') if subprocess.run(['git','cat-file','-e',f'{remote}:{RECEIPTS}'],cwd=repo,capture_output=True).returncode==0 else '[]'
  if not receipt_state(json.loads(raw),p):raise ValueError('PUSH_NOT_CONFIRMED_REBUILD_FROM_REMOTE')
  commit=remote
 # If revoke happens after last read but before push it cannot be atomic with Google.
 # Preserve committed schedule; signal review, never silently delete publication.
 nonce=secrets.token_hex(16)
 try:after=checked(trusted_transport(nonce),nonce,clock());needs_review=after!=p
 except Exception:needs_review=True
 return finish_committed(repo,commit,receipt,pages_verify,needs_review,False)

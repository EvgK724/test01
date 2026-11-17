"""Reconstructed bounded queue orchestration; no endpoint/trigger configured."""
import datetime,json,re,secrets,pathlib
from public_digest import digest
from delivery import checked,deliver,git,SCHEDULE,RECEIPTS,finish_committed

def catalog_checked(r,nonce,now):
 if type(r)is not dict or set(r)!={'schema','kind','nonce','checkedAt','status','approvalIds'} or type(r['schema'])is not int or r['schema']!=1 or r['kind']!='APPROVAL_CATALOG' or r['nonce']!=nonce or r['status']!='READY':raise ValueError('CATALOG_SCHEMA')
 at=datetime.datetime.fromisoformat(r['checkedAt'].replace('Z','+00:00'))
 if at.tzinfo is None or not 0<=(now-at).total_seconds()<=120:raise ValueError('CATALOG_STALE')
 ids=r['approvalIds']
 if type(ids)is not list or len(ids)>500 or any(type(x)is not str or not re.fullmatch('[0-9a-f]{32}',x)for x in ids) or len(set(ids))!=len(ids):raise ValueError('CATALOG_IDS')
 return ids

def consume(repo,catalog,selected,clock,pages_verify,renderer):
 if not callable(pages_verify) or not callable(renderer):raise ValueError('VERIFIERS_REQUIRED')
 if git(repo,'status','--porcelain'):raise ValueError('DIRTY')
 git(repo,'fetch','origin','main');base=git(repo,'rev-parse','origin/main')
 if git(repo,'rev-parse','HEAD')!=base:raise ValueError('LOCAL_BASE_CHANGED')
 n=secrets.token_hex(16);ids=catalog_checked(catalog(n),n,clock())
 rp=pathlib.Path(repo)/RECEIPTS;rs=json.loads(rp.read_text())if rp.exists()else []
 seen=[r['approvalId']for r in rs]
 if len(seen)!=len(set(seen)):raise ValueError('DUPLICATE_RECEIPTS')
 pending=[];unavailable=[]
 for aid in ids:
  if aid in seen:continue
  n=secrets.token_hex(16)
  try:p=checked(selected(aid,n),n,clock())
  except ValueError as e:
   if str(e)=='REVOKED_STALE_OR_UNAPPROVED':unavailable.append(aid);continue
   raise
  if p['approvalId']!=aid:raise ValueError('APPROVAL_SELECTOR_MISMATCH')
  pending.append(p)
 pairs=[(p['draft']['month'],p['baseVersion'])for p in pending]
 if len(pairs)!=len(set(pairs)):raise ValueError('QUEUE_BASE_CONFLICT')
 data=json.loads((pathlib.Path(repo)/SCHEDULE).read_text());results=[]
 # Only the latest durable receipt per month represents the active publication.
 latest={r['month']:r for r in rs}
 replacements={p['draft']['month'] for p in pending
               if p['baseVersion']==data['months'].get(p['draft']['month'],{}).get('version',0)}
 for month,r in latest.items():
  if month in replacements:continue # explicitly approved exact-base replacement, rechecked by deliver
  aid=r['approvalId'];n=secrets.token_hex(16)
  try:
   p=checked(selected(aid,n),n,clock());review=p['approvalId']!=aid or digest(p)!=r['payloadHash']
  except Exception:review=True
  result=finish_committed(repo,base,r,pages_verify,review,True);results.append(result)
  if result.get('organizerReviewRequired') or result.get('pages')!='VERIFIED':
   return {'results':results,'unavailableApprovals':unavailable,'empty':False}
 for p in sorted(pending,key=lambda p:(p['draft']['month'],p['baseVersion'])):
  mk=p['draft']['month'];current=data['months'].get(mk,{}).get('version',0)
  if p['baseVersion']!=current:raise ValueError('QUEUE_BASE_VERSION_CHANGED')
  aid=p['approvalId'];result=deliver(repo,lambda nonce: selected(aid,nonce),clock,pages_verify,renderer=renderer,expected_approval_id=aid);results.append(result)
  if result.get('organizerReviewRequired') or result.get('pages')!='VERIFIED':break
  data=json.loads((pathlib.Path(repo)/SCHEDULE).read_text())
 return {'results':results,'unavailableApprovals':unavailable,'empty':not pending and not rs}

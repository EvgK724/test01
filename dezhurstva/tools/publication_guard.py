"""Fail-closed invariants after existing build. Does not publish."""
import argparse,json,pathlib,subprocess
from approval_revision import revision

def check(before,after,paths):
 if before.keys()!=after.keys():raise ValueError('top-level schema changed')
 for k in before:
  if k not in ('updated','months') and before[k]!=after[k]:raise ValueError('unrelated data changed')
 if before['months'].keys()!=after['months'].keys():raise ValueError('month added/removed')
 changed=[]
 for mk,a in before['months'].items():
  b=after['months'][mk]
  if a==b:continue
  if a.get('status')=='final':
   old=json.loads(json.dumps(a));new=json.loads(json.dumps(b))
   for k in ('reviewRequired','reviewCheckedAt'):old['confirm'].pop(k,None);new['confirm'].pop(k,None)
   if old!=new or b['confirm'].get('reviewRequired') is not True:raise ValueError('final month modified beyond review notice')
   changed.append(mk);continue
  if a.get('status')!='preliminary':raise ValueError('other month changed')
  if revision(a,before)!=revision(b,after):raise ValueError('schedule content changed')
  if b.get('status') not in ('preliminary','final'):raise ValueError('bad status')
  if b.get('status')=='final':
   c=b['confirm'];f=b.get('finalization',{})
   if c['confirmed']!=c['need'] or c['disagreed']!=0 or f.get('digest')!=revision(b,after):raise ValueError('invalid finalization')
  changed.append(mk)
 allowed={'dezhurstva/data/schedule.json','dezhurstva/index.html','dezhurstva/files/hashes.json','dezhurstva/files/pdf.json'}
 allowed|={'dezhurstva/cal/'+w+'.ics' for w in [*before['doctors'],'all']}
 allowed|={f'dezhurstva/files/{m}{s}' for m in changed for s in ('.xlsx','.pdf','-print.pdf')}
 if not set(paths)<=allowed:raise ValueError('outside publication allowlist')
 if not changed and paths:raise ValueError('artifacts changed without data')
 return changed

def main():
 p=argparse.ArgumentParser();p.add_argument('--base',required=True);a=p.parse_args()
 before=json.loads(subprocess.check_output(['git','show',a.base+':dezhurstva/data/schedule.json']))
 after=json.loads(pathlib.Path('dezhurstva/data/schedule.json').read_text())
 paths=subprocess.check_output(['git','diff','--name-only',a.base]).decode().splitlines()
 # Untracked output must not slip through git add; candidate installation files are already committed.
 untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard']).decode().splitlines()
 paths=sorted(set(paths+untracked))
 changed=check(before,after,paths)
 for name in ('hashes.json','pdf.json'):
  path='dezhurstva/files/'+name
  old=json.loads(subprocess.check_output(['git','show',a.base+':'+path]))
  new=json.loads(pathlib.Path(path).read_text())
  for m in set(old)|set(new):
   if m not in changed and old.get(m)!=new.get(m):raise ValueError('other month artifact index changed')
 print(json.dumps({'changedMonths':changed,'paths':paths}))
if __name__=='__main__':main()

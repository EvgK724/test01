"""Extracted r7 renderer, no owner authentication claim. Real publish/build/PDF.
Only trusted bridge calls after approved-only endpoint validation; no CLI.
"""
import json,pathlib,tempfile,shutil,subprocess,re,hashlib
from release_boundary import check_head,sha,canon

def render(draft,expected_version,repo,head,pins):
 repo=pathlib.Path(repo).resolve();check_head(repo,head)
 tracked=subprocess.check_output(['git','ls-files','-z','dezhurstva'],cwd=repo).decode().split('\0');tracked=[p for p in tracked if p]
 # All tracked source bytes pinned by trusted host; no pin supplied by export.
 if {p:sha((repo/p).read_bytes()) for p in tracked if (repo/p).is_file()}!=pins:raise ValueError('SOURCE_PINS_CHANGED')
 def fresh():
  f=transport(e['scheduleId'],e['scheduleHash']);validate_export(f,clock())
  strip=lambda x:{k:v for k,v in x.items() if k not in ('checkedAt','exportHash')}
  if strip(e)!=strip(f):raise ValueError('OWNER_STATE_CHANGED')
 from vacation_marks import validate
 validate(draft)
 month=draft['month'];before=json.loads((repo/'dezhurstva/data/schedule.json').read_text());old=before['months'].get(month,{})
 version=max(old.get('version',0),(old.get('confirm')or{}).get('version',0))+1
 with tempfile.TemporaryDirectory(prefix='private-preliminary-') as td:
  stage=pathlib.Path(td)
  for rel in tracked:
   parts=pathlib.PurePosixPath(rel).parts
   if any(p in ('private','__pycache__','.env') for p in parts) or rel.endswith(('.key','.pem')):continue
   src=repo/rel
   if src.is_symlink() or not src.is_file():raise ValueError('UNSAFE_TRACKED_FILE')
   dest=stage/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
  path=stage/'input.json';payload=dict(draft);payload['marks']=draft['marks'];payload['title']=['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'][int(month[5:])-1]+' '+month[:4];path.write_text(canon(payload))
  subprocess.run(['python','-B',str(stage/'dezhurstva/tools/publish.py'),month,str(path)],cwd=stage,check=True,capture_output=True);path.unlink()
  schedule=json.loads((stage/'dezhurstva/data/schedule.json').read_text());m=schedule['months'][month]
  if m.get('status')!='preliminary' or m.get('version')!=version or 'finalization'in m or 'final_at'in m:raise ValueError('WRONG_PUBLICATION_STATE')
  for k in ('order','shift','off','duty','marks'):
   if m[k]!=draft[k]:raise ValueError('APPROVED_DRAFT_CHANGED')
  if m.get('marks')!=draft['marks'] or m['confirm']['need']!=draft['order']:raise ValueError('PUBLIC_FIELDS')
  if {k:v for k,v in before.items() if k not in ('updated','months')}!={k:v for k,v in schedule.items() if k not in ('updated','months')}:raise ValueError('OTHER_DATA_CHANGED')
  if {k:v for k,v in before['months'].items() if k!=month}!={k:v for k,v in schedule['months'].items() if k!=month}:raise ValueError('OTHER_MONTH_CHANGED')
  ids=list(before['doctors'])
  if any(not re.fullmatch(r'[A-Za-z0-9_-]+',i) for i in ids):raise ValueError('UNSAFE_DOCTOR_ID')
  allow={'dezhurstva/index.html','dezhurstva/data/schedule.json','dezhurstva/files/hashes.json','dezhurstva/files/pdf.json'}|{f'dezhurstva/cal/{i}.ics' for i in ids+['all']}|{f'dezhurstva/files/{month}{s}' for s in ('.xlsx','.pdf','-print.pdf')}
  for s in ('.xlsx','.pdf','-print.pdf'):
   if not(stage/f'dezhurstva/files/{month}{s}').is_file():raise ValueError('ARTIFACT_MISSING')
  # Historic cache metadata must remain byte-semantically bound to old artifacts.
  for filename in ('pdf.json','hashes.json'):
   oldpath=repo/'dezhurstva/files'/filename
   oldmeta=json.loads(oldpath.read_text()) if oldpath.exists() else {}
   newmeta=json.loads((stage/'dezhurstva/files'/filename).read_text())
   if {k:v for k,v in oldmeta.items() if k!=month}!={k:v for k,v in newmeta.items() if k!=month}:raise ValueError('HISTORICAL_ARTIFACT_METADATA_CHANGED')
  inline=re.search(r'<script id="data"[^>]*>(.*?)</script>',(stage/'dezhurstva/index.html').read_text(),re.S)
  if not inline or json.loads(inline[1])['months'][month]!=m:raise ValueError('HTML_BINDING')
  files={}
  for p in stage.rglob('*'):
   if not p.is_file():continue
   rel=str(p.relative_to(stage));src=repo/rel
   if src.is_file() and src.read_bytes()==p.read_bytes():continue
   if rel not in allow:raise ValueError('UNEXPECTED_DIFF')
   files[rel]=p.read_bytes()
  check_head(repo,head)
  if version!=expected_version:raise ValueError('APPROVED_VERSION_CHANGED')
  return files

"""Run existing builder without generating missing PDFs for unrelated months."""
import argparse,json,pathlib,subprocess,hashlib
from approval_revision import revision
import build,make_pdf

def main():
 p=argparse.ArgumentParser();p.add_argument('--base',required=True);a=p.parse_args()
 old=json.loads(subprocess.check_output(['git','show',a.base+':dezhurstva/data/schedule.json']))
 new=json.loads(pathlib.Path('dezhurstva/data/schedule.json').read_text())
 changed={k for k,v in new['months'].items() if old['months'].get(k)!=v}
 if not changed:return
 # Scope all artifact indexes and bytes, not just PDF rendering.
 build.main(artifact_months=changed)
 # Existing build catches PDF exceptions; never treat that as publish success.
 pdf=json.loads(pathlib.Path('dezhurstva/files/pdf.json').read_text())
 for mk in changed:
  m=json.loads(json.dumps(new['months'][mk]))
  if m.get('confirm'):m['confirm']['digest']=revision(m,new)
  expected=hashlib.sha1(json.dumps(['pdf',build.PDF_FORMAT,m,{i:new['doctors'][i]['name'] for i in m['order']}],ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:12]
  if pdf.get(mk,{}).get('v')!=expected:raise ValueError('PDF metadata not current: '+mk)
  for suffix in ('.pdf','-print.pdf'):
   raw=pathlib.Path('dezhurstva/files/'+mk+suffix).read_bytes()
   if not raw.startswith(b'%PDF-') or len(raw)<1000:raise ValueError('invalid PDF: '+mk)
   from pypdf import PdfReader
   reader=PdfReader('dezhurstva/files/'+mk+suffix,strict=True)
   if reader.is_encrypted or len(reader.pages)!=1:raise ValueError('unexpected PDF pages/encryption: '+mk)
  from openpyxl import load_workbook
  wb=load_workbook('dezhurstva/files/'+mk+'.xlsx',read_only=True)
  if len(wb.worksheets)!=1 or any(ws.sheet_state!='visible' for ws in wb):raise ValueError('unexpected workbook sheets')
  wb.close()
if __name__=='__main__':main()

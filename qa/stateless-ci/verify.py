import hashlib,json,pathlib,zipfile,re,subprocess
from pypdf import PdfReader
root=pathlib.Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
archive=root/'synthetic.zip';assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['archive_sha256']
out=root/'unpacked';out.mkdir()
with zipfile.ZipFile(archive) as z:
 assert set(z.namelist())==set(manifest['files'])
 for name in z.namelist():
  p=pathlib.PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts
  content=z.read(name);assert hashlib.sha256(content).hexdigest()==manifest['files'][name]
  dst=out/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(content)
for p in out.rglob('*.html'):
 html=p.read_text()
 for forbidden in ['localStorage','sessionStorage','serviceWorker','indexedDB','document.cookie','BroadcastChannel','AKfy','script.google.com','caches.']:assert forbidden not in html,forbidden
 assert "connect-src 'none'" in html
 for attrs,code in re.findall(r'<script([^>]*)>(.*?)</script>',html,re.S):
  if 'application/json' not in attrs:subprocess.run(['node','-e',"new(require('node:vm').Script)(require('node:fs').readFileSync(0,'utf8'))"],input=code,text=True,check=True)
for p in out.rglob('*.pdf'):
 r=PdfReader(p);assert len(r.pages)==1
 page=r.pages[0];assert abs(float(page.mediabox.width)-841.8898)<.01 and abs(float(page.mediabox.height)-595.2756)<.01
 text=page.extract_text();assert '2027' in text and text.count('+')==31
 assert not page.get('/Annots') and '/OpenAction' not in r.trailer['/Root']
print('PASS exact reviewed archive/file hashes, stateless HTML, JS syntax, actual A4 PDFs. No deployment, app network, or persistent storage.')

from pathlib import Path,PurePosixPath
import zipfile,hashlib,json,subprocess,sys,tempfile,os,re
base=Path(__file__).resolve().parent
assert hashlib.sha256((base/'source.zip').read_bytes()).hexdigest()=='13e3bc23be58c903a9fe1ac8476a860e4b8ee2969a89ecee6a7484fd0043b746'
manifest=json.loads((base/'manifest.json').read_text())
with tempfile.TemporaryDirectory() as td:
 root=Path(td)
 with zipfile.ZipFile(base/'source.zip') as z:
  assert set(z.namelist())==set(manifest) and len(z.namelist())==len(manifest)
  for name in z.namelist():
   assert not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts and not name.endswith(('.b64','.pyc'))
   raw=z.read(name);assert hashlib.sha256(raw).hexdigest()==manifest[name]
   if not name.endswith('.ttf'):assert not re.search(r'script.google.com|AKfycb|Лекерова|Леонард|Кардашина|Клепиков|Омутов',raw.decode(),re.I)
   p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 assert "const WISH_SIGNALS_URL = '';" in (root/'source/dezhurstva/tools/template.html').read_text()
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
 subprocess.run([sys.executable,'-B','-m','unittest','test_delivery','test_queue','test_pdf_offline','test_confirm_build.ScopedConfirmation','-v'],cwd=root,env=env,check=True)
 print('PASS source-built real PDF/XLSX/HTML, scoped finalization and local-bare-Git delivery. No external endpoint, deploy, secrets, or production change.')

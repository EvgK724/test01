import hashlib,json,subprocess
def sha(b):return hashlib.sha256(b).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)
def check_head(repo,head):
 if subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip()!=head or subprocess.check_output(["git","status","--porcelain"],cwd=repo,text=True).strip():raise ValueError("BASE_CHANGED")

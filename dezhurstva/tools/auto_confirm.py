#!/usr/bin/env python3
"""Aggregate transport + strict finalization. Never imports private sheet rows."""
import argparse, datetime as dt, hashlib, json, pathlib, re, secrets, urllib.request

from approval_revision import canonical, digest, revision
def utc(x):
    d=dt.datetime.fromisoformat(x.replace('Z','+00:00'))
    if d.tzinfo is None:raise ValueError('timezone missing')
    return d.astimezone(dt.timezone.utc)
def validate(a,m,mk,nonce,now,data):
    c=m['confirm'];n=len(c['need'])
    if c.get('digest') is not None and c['digest']!=revision(m,data):raise ValueError('stored digest differs; republish as new version')
    if type(c['version']) is not int or c['version']<1 or m.get('version')!=c['version']:raise ValueError('local version')
    if not n or len(set(c['need']))!=n:raise ValueError('roster')
    expected={'ok':True,'schema':1,'identity':'self-declared','month':mk,'version':c['version'],'digest':revision(m,data),'rosterHash':digest(c['need']),'nonce':nonce,'sourceComplete':True,'required':n}
    for k,v in expected.items():
        if type(a.get(k)) is not type(v) or a[k]!=v:raise ValueError('aggregate mismatch: '+k)
    if not 0 <= (now-utc(a['checkedAt'])).total_seconds() <=120:raise ValueError('stale aggregate')
    for k in ('required','agreed','disagreed','ambiguous','waiting'):
        if type(a.get(k)) is not int or not 0<=a[k]<=n:raise ValueError('count')
    if sum(a[k] for k in ('agreed','disagreed','ambiguous','waiting'))!=n:raise ValueError('count sum')
    allowed=set(expected)|{'checkedAt','agreed','disagreed','ambiguous','waiting','allAgreed','receiptIds'}
    if set(a)!=allowed:raise ValueError('unexpected aggregate fields')
    ids=a.get('receiptIds')
    if not isinstance(ids,list) or len(ids)>n or len(set(ids))!=len(ids) or ids!=sorted(ids) or any(not isinstance(i,str) or not re.fullmatch(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}',i) for i in ids):raise ValueError('receiptIds')
    ready=a['agreed']==n and a['disagreed']==a['ambiguous']==a['waiting']==0
    if type(a.get('allAgreed')) is not bool or a['allAgreed']!=ready:raise ValueError('inconsistent decision')
    return ready
class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,url):
        from urllib.parse import urlparse
        u=urlparse(url)
        if u.scheme!='https' or u.hostname!='script.googleusercontent.com' or u.username or u.password:raise ValueError('unexpected redirect')
        return super().redirect_request(req,fp,code,msg,headers,url)
def fetch(endpoint,mk,nonce):
    if not re.fullmatch(r'https://script\.google\.com/macros/s/[-\w]+/exec',endpoint):raise ValueError('endpoint')
    url=endpoint+'?month='+mk+'&nonce='+nonce
    with urllib.request.build_opener(Redirect()).open(url,timeout=30) as r:
        if r.status!=200:raise ValueError('http')
        b=r.read(16385)
        if len(b)>16384:raise ValueError('response too large')
        return json.loads(b)
def main():
    p=argparse.ArgumentParser();p.add_argument('--endpoint',required=True);p.add_argument('--schedule',default='dezhurstva/data/schedule.json');p.add_argument('--apply',action='store_true');args=p.parse_args()
    path=pathlib.Path(args.schedule);old=path.read_bytes();data=json.loads(old);changed=False;objections=[]
    for mk,m in data['months'].items():
        if m.get('status') not in ('preliminary','final') or not m.get('confirm'):continue
        if m.get('status')=='final' and not m.get('finalization'):continue
        nonce=secrets.token_hex(16);a=fetch(args.endpoint,mk,nonce);now=dt.datetime.now(dt.timezone.utc)
        ready=validate(a,m,mk,nonce,now,data)
        # Second fresh snapshot, do not carry a stored decision across network retry.
        nonce=secrets.token_hex(16);b=fetch(args.endpoint,mk,nonce);now=dt.datetime.now(dt.timezone.utc)
        ready=validate(b,m,mk,nonce,now,data)
        if m['status']=='final':
            if not ready:
                objections.append({'month':mk,'version':m['confirm']['version'],'status':'organizer-review-required','checkedAt':b['checkedAt']})
                if m['confirm'].get('reviewRequired') is not True:
                    m['confirm']['reviewRequired']=True;m['confirm']['reviewCheckedAt']=b['checkedAt'];changed=True
            continue
        fields={'confirmed':[],'agreedCount':b['agreed'],'disagreed':b['disagreed'],'receiptIds':b['receiptIds']}
        if any(m['confirm'].get(k)!=v for k,v in fields.items()):
            m['confirm'].update(fields);m['confirm']['checkedAt']=b['checkedAt'];changed=True
        if not ready:continue
        m['status']='final';m['final_at']=now.isoformat().replace('+00:00','Z')
        m['confirm']['confirmed']=list(m['confirm']['need']);m['confirm']['agreedCount']=len(m['confirm']['need']);m['confirm']['disagreed']=0;m['confirm']['receiptIds']=[]
        m['finalization']={'digest':b['digest'],'checkedAt':b['checkedAt'],'identity':'self-declared','semantics':'snapshot-at-receipt; later objections require organizer review'}
        changed=True
    if changed and args.apply:
        if path.read_bytes()!=old:raise ValueError('schedule changed during check')
        data['updated']=dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z')
        path.write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n')
    print(json.dumps({'changed':changed,'applied':bool(changed and args.apply),'lateObjections':objections}))
if __name__=='__main__':main()

"""Publish only authorized research source/evidence, never main or financial actions."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import urllib.request

BRANCH='research/2026-10-13-extended-validation'
REPO='DashSaman/Arz'

def main():
    p=argparse.ArgumentParser();p.add_argument('--source-manifest');p.add_argument('--reports');a=p.parse_args()
    if bool(a.source_manifest)==bool(a.reports):raise ValueError('Choose exactly one publication mode')
    if os.environ.get('GITHUB_REPOSITORY')!=REPO or os.environ.get('GITHUB_REF_NAME')!=BRANCH:raise ValueError('Unauthorized repository or branch')
    expected=os.environ['GITHUB_SHA'];token=os.environ['GH_RESEARCH_TOKEN']
    base='https://api.github.com/repos/'+REPO
    def api(method,path,body=None):
        payload=json.dumps(body).encode() if body is not None else None
        req=urllib.request.Request(base+path,data=payload,method=method,
          headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=40) as r:return json.loads(r.read())
    if api('GET','/git/ref/heads/'+BRANCH)['object']['sha']!=expected:raise RuntimeError('Concurrent branch change; refusing overwrite')
    if a.source_manifest:
        inventory=json.loads(Path(a.source_manifest).read_text());files=[]
        for name,digest in inventory.items():
            if not (name.startswith('src/arz_extended/') or name.startswith('tests/test_extended') or name.startswith('docs/en/extended_') or name.startswith('docs/fa/extended_') or name.startswith('reports/extended_backtests/') or name in ('scripts/run_extended.py','scripts/publish_extended.py','configs/extended_preregistration.json')):raise ValueError('Source path outside allowlist')
            f=Path(name)
            if f.is_symlink() or '..' in f.parts or f.is_absolute():raise ValueError('Unsafe publication path')
            if hashlib.sha256(f.read_bytes()).hexdigest()!=digest:raise ValueError('Source digest changed')
            files.append(f)
        message='feat: publish isolated compound research engine and passing regression tests before market evaluation'
    else:
        root=Path(a.reports)
        if root.is_absolute() or '..' in root.parts or not str(root).startswith('reports/extended_backtests/run_'):raise ValueError('Unsafe report root')
        files=[f for f in root.rglob('*') if f.is_file() and not f.is_symlink()]
        if any(f.suffix not in ('.json','.csv','.txt','.md','.gz') for f in files):raise ValueError('Unexpected report type')
        message='research: publish measured extended experiment results; live trading remains disabled'
    if len(files)>100 or sum(f.stat().st_size for f in files)>14000000:raise ValueError('Research publication size bound exceeded')
    if any(f.stat().st_size>8000000 for f in files):raise ValueError('Single report too large for this bounded delivery')
    tree=[]
    for f in files:
        data=f.read_bytes()
        if f.suffix=='.gz':
            blob=api('POST','/git/blobs',{'content':base64.b64encode(data).decode(),'encoding':'base64'})
            tree.append({'path':str(f),'mode':'100644','type':'blob','sha':blob['sha']})
        else:tree.append({'path':str(f),'mode':'100644','type':'blob','content':data.decode('utf-8')})
    commit=api('GET','/git/commits/'+expected)
    created_tree=api('POST','/git/trees',{'base_tree':commit['tree']['sha'],'tree':tree})
    new=api('POST','/git/commits',{'message':message,'tree':created_tree['sha'],'parents':[expected]})
    if api('GET','/git/ref/heads/'+BRANCH)['object']['sha']!=expected:raise RuntimeError('Concurrent update before ref mutation; commit left unreferenced')
    api('PATCH','/git/refs/heads/'+BRANCH,{'sha':new['sha'],'force':False})
    if api('GET','/git/ref/heads/'+BRANCH)['object']['sha']!=new['sha']:raise RuntimeError('Published ref verification failed')
    print('PUBLISHED_RESEARCH_COMMIT',new['sha'],'files',len(files),'bytes',sum(f.stat().st_size for f in files),flush=True)

if __name__=='__main__':main()

from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json,subprocess,tempfile,os,threading
class Provider(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  self.rfile.read(int(self.headers['Content-Length']))
  body=b'{"error":{"message":"fixture stopped before inference"}}'
  self.send_response(400);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
class Server:
 def __init__(self,repo,env):
  self.p=subprocess.Popen(['codex','app-server','--stdio'],cwd=repo,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
  self.n=0; self.rpc('initialize',{'clientInfo':{'name':'history-fixture','version':'1'},'capabilities':{'experimentalApi':True}});self.send({'method':'initialized'})
 def send(self,msg):self.p.stdin.write(json.dumps(msg)+'\n');self.p.stdin.flush()
 def read(self):
  raw=self.p.stdout.readline()
  if not raw:raise RuntimeError('host exited')
  return json.loads(raw),len(raw.encode())
 def rpc(self,method,params):
  self.n+=1; self.send(dict(method=method,params=params,id=self.n))
  while True:
   msg,n=self.read()
   if msg.get('id')==self.n:
    if 'error' in msg:raise RuntimeError(msg['error'].get('message','')[:220])
    return msg['result'],n
 def close(self):
  self.p.terminate();self.p.wait(timeout=8)
with tempfile.TemporaryDirectory(prefix='keel-history-') as tmp, ThreadingHTTPServer(('127.0.0.1',0),Provider) as provider:
 root=Path(tmp);repo=root/'repo';profile=root/'profile';home=root/'home'
 for d in (repo,profile,home):d.mkdir()
 subprocess.run(['git','init','-q',str(repo)],check=True)
 (profile/'config.toml').write_text(f'model="fixture"\nmodel_provider="fixture"\n[model_providers.fixture]\nname="fixture"\nbase_url="http://127.0.0.1:{provider.server_port}/v1"\nwire_api="responses"\nrequires_openai_auth=false\nrequest_max_retries=0\nstream_max_retries=0\n')
 env=dict(PATH=os.environ['PATH'],HOME=str(home),CODEX_HOME=str(profile))
 threading.Thread(target=provider.serve_forever,daemon=True).start()
 host=Server(repo,env)
 try:
  seed,_=host.rpc('thread/start',dict(cwd=str(repo),sandbox='read-only',approvalPolicy='never'))
  tid=seed['thread']['id']
  for i in range(22):
   host.rpc('turn/start',dict(threadId=tid,input=[dict(type='text',text=str(i)+'X'*(800*1024))]))
   while host.read()[0].get('method')!='turn/completed':pass
 finally:host.close()
 for omit in (False,True):
  host=Server(repo,env)
  try:
   r,size=host.rpc('thread/resume',dict(threadId=tid,**({'excludeTurns':True} if omit else {})))
   print('excludeTurns',omit,'response bytes',size,'turns',len(r['thread']['turns']),'same original',r['thread']['id']==tid,flush=True)
   assert r['thread']['id']==tid and r['thread']['cwd']==str(repo) and r['approvalPolicy']=='never' and r['sandbox']['type']=='readOnly'
   if omit:assert size<1024*1024 and r['thread']['turns']==[]
   else:assert size>16*1024*1024
  finally:host.close()
 provider.shutdown()

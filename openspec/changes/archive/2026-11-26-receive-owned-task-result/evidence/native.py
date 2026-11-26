from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
import hashlib,json,os,subprocess,tempfile,threading,time,re
REPO=Path.cwd()
class Provider(BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def do_POST(self):
  req=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  self.server.count+=1
  if self.server.count==1:
   assert self.server.task in json.dumps(req['input'])
   item={'type':'function_call','name':'exec_command','call_id':'review','arguments':json.dumps({'cmd':'git show HEAD:input.txt | sha256sum; test ! -w .git/keel-chat'})}
  else:
   outputs=[i for i in req['input'] if i.get('type')=='function_call_output' and i.get('call_id')=='review']
   assert len(outputs)==1 and self.server.digest in str(outputs[0]) and 'code 0' in str(outputs[0])
   item={'type':'message','role':'assistant','id':'review-answer','phase':'final_answer','content':[{'type':'output_text','text':json.dumps({'taskId':self.server.task,'result':self.server.digest})}]}
  resp={'id':'resp-fixture','usage':{'input_tokens':0,'output_tokens':0,'total_tokens':0}}
  events=[{'type':'response.created','response':resp},{'type':'response.output_item.done','item':item},{'type':'response.completed','response':resp}]
  body=''.join('event: '+e['type']+'\ndata: '+json.dumps(e)+'\n\n' for e in events).encode()
  self.send_response(200);self.send_header('Content-Type','text/event-stream');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
with tempfile.TemporaryDirectory(prefix='keel-result-native-') as d,ThreadingHTTPServer(('127.0.0.1',0),Provider) as provider:
 root=Path(d);home=root/'home';repo=root/'project';config=root/'config'
 for directory in (home,repo,config):directory.mkdir()
 env=dict(PATH=os.environ['PATH'],HOME=str(home),CODEX_HOME=str(config))
 def run(args,**kwargs):return subprocess.run(args,cwd=repo,env=env,text=True,capture_output=True,timeout=30,**kwargs)
 def cli(*args,owner=False,check=True):
  p=subprocess.run(['node',str(REPO/'bin/keel.js'),*args,'--json'],cwd=repo,env=dict(env,**({'KEEL_CHAT_ROLE':'caller'} if owner else {})),text=True,capture_output=True,timeout=30)
  if check and p.returncode:raise RuntimeError(p.stderr)
  return p
 (repo/'input.txt').write_text('public review specimen\n');provider.digest=hashlib.sha256((repo/'input.txt').read_bytes()).hexdigest()
 run(['git','init','-q'],check=True);run(['git','add','input.txt'],check=True);run(['git','-c','user.name=fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture'],check=True)
 (config/'config.toml').write_text(f'model="fixture"\nmodel_provider="fixture"\n[model_providers.fixture]\nname="fixture"\nbase_url="http://127.0.0.1:{provider.server_port}/v1"\nwire_api="responses"\nrequires_openai_auth=false\nrequest_max_retries=0\nstream_max_retries=0\n[projects.{json.dumps(str(repo))}]\ntrust_level="trusted"\n')
 provider.count=0;threading.Thread(target=provider.serve_forever,daemon=True).start();sock=root/'native.sock'
 p=subprocess.Popen(['codex','app-server','--listen','unix://'+str(sock)],cwd=repo,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  for _ in range(100):
   if sock.exists():break
   time.sleep(.05)
  cli('codex','start','--role','reviewer','--socket',str(sock))
  cli('chat','group','create','reviews','--member','reviewer',owner=True)
  provider.task=json.loads(cli('chat','todo','reviews','--assignee','reviewer','Review the fixed input.',owner=True).stdout)['id']
  cli('tick')
  for _ in range(30):
   res=cli('chat','show',provider.task,'--collect',owner=True,check=False)
   if res.returncode==0:break
   time.sleep(.15)
  assert res.returncode==0,res.stderr
  result=json.loads(res.stdout);assert result['result']['text']==provider.digest and result['task']['state']=='open'
  assert provider.count==2
 finally:
  p.terminate();p.wait(timeout=6);provider.shutdown()
 assert json.loads(cli('chat','show',provider.task,owner=True).stdout)['result']==result['result']
 print('Real Codex: read-only mailbox, exact commit content SHA-256 returned through final native message, open task, offline reread, 2 loopback requests.')

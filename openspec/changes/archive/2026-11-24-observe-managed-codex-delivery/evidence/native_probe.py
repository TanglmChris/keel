from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json, os, subprocess, sys, tempfile, threading, time

def sse(events):
    return ''.join(f'event: {event["type"]}\ndata: {json.dumps(event)}\n\n' for event in events).encode()

class Provider(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))))
        self.server.requests.append(request)
        if len(self.server.requests) == 1:
            tools = {item.get('name') for item in request.get('tools', [])}
            assert 'exec_command' in tools, sorted(str(tool) for tool in tools)
            call = {
                "type":"function_call","call_id":"keel-fixture-write","name":"exec_command",
                "arguments":json.dumps({"cmd":"printf 'started\n' >> keel-marker.txt; sleep 7; printf 'finished\n' >> keel-marker.txt","yield_time_ms":1000}),
            }
            body = sse([
                {"type":"response.created","response":{"id":"fixture-write"}},
                {"type":"response.output_item.done","item":call},
                {"type":"response.completed","response":{"id":"fixture-write",
                    "usage":{"input_tokens":0,"input_tokens_details":None,"output_tokens":0,"output_tokens_details":None,"total_tokens":0}}},
            ])
            self.send_response(200)
            self.send_header("Content-Type","text/event-stream")
        else:
            body = json.dumps({"error":{"type":"usage_limit_reached","message":"fixture usage limit","plan_type":"plus","resets_at":2000000000}}).encode()
            self.send_response(429)
            self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)


repo = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory(prefix="keel-544-native-observe-") as raw, ThreadingHTTPServer(("127.0.0.1",0),Provider) as server:
    server.requests=[]
    threading.Thread(target=server.serve_forever,daemon=True).start()
    root=Path(raw)
    fixture=root/'worktree'; profile=root/'profile'; home=root/'home'
    for directory in (fixture,profile,home):
        directory.mkdir()
    subprocess.run(['git','init','-q',str(fixture)],check=True)
    (profile/'config.toml').write_text(f"""model="fixture"
model_provider="keel_fixture"
[model_providers.keel_fixture]
name="Local fixture"
base_url="http://127.0.0.1:{server.server_port}/v1"
wire_api="responses"
requires_openai_auth=false
request_max_retries=0
stream_max_retries=0
[projects.{json.dumps(str(fixture))}]
trust_level="trusted"
""")
    env=dict(PATH=os.environ['PATH'],CODEX_HOME=str(profile),HOME=str(home))
    socket=root/'codex.sock'
    host=subprocess.Popen(['codex','app-server','--listen',f'unix://{socket}'],cwd=fixture,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def keel(action, *args):
        value=subprocess.run(['node',str(repo/'bin/keel.js'),'codex',action,'--repo',str(fixture),'--role','fixture-worker','--json',*args],cwd=fixture,env=env,text=True,capture_output=True,timeout=12)
        assert value.returncode==0,value.stderr
        return json.loads(value.stdout)
    try:
        deadline=time.monotonic()+5
        while not socket.exists() and host.poll() is None and time.monotonic()<deadline:
            time.sleep(.05)
        assert socket.exists()
        started=keel('start','--socket',str(socket))
        sent=keel('deliver','--record','fixture-task','--text','Run the harmless fixture command.')
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            result=keel('status','--record','fixture-task','--observe')
            if result['observation']['state']=='resource-exhausted':
                break
            time.sleep(.1)
        assert result['turn']==sent['turn'] and result['thread']==started['thread']
        assert result['observation']=={'state':'resource-exhausted','backgroundTerminals':'present'},result['observation']
        assert (fixture/'keel-marker.txt').read_text()=='started\n'
        print('public CLI: exact native turn = resource-exhausted, background terminal = present',flush=True)
        deadline=time.monotonic()+9
        while time.monotonic()<deadline:
            result=keel('status','--record','fixture-task','--observe')
            if result['observation']['backgroundTerminals']=='none-observed':
                break
            time.sleep(.25)
        assert result['observation']=={'state':'resource-exhausted','backgroundTerminals':'none-observed'},result['observation']
        assert (fixture/'keel-marker.txt').read_text()=='started\nfinished\n'
        assert len(server.requests)==2, len(server.requests)
        print('after the original terminal finished: exact turn still resource-exhausted, inventory none-observed, 2 provider requests total',flush=True)
    finally:
        host.terminate()
        host.wait(timeout=5)
        server.shutdown()
    after = keel('status','--record','fixture-task','--observe')
    assert after['observation']=={'state':'unknown','backgroundTerminals':'unknown'},after['observation']
    assert after['turn']==sent['turn'] and after['thread']==started['thread']
    print('after stopping the isolated endpoint: native observations unknown, original receipt preserved')

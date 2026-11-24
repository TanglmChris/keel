from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from queue import Queue
import json, os, re, subprocess, tempfile, threading, time
import pexpect

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
                "arguments":json.dumps({"cmd":"printf 'keel-fixture-written\n' >> keel-marker.txt"}),
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

class ClaudeProvider(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def do_POST(self):
        request=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
        self.server.calls.append({
            'path': self.path.split('?')[0],
            'stream': request.get('stream'),
            'has_tools': any(tool.get('name')=='Bash' for tool in request.get('tools',[])),
            'has_receipt': any(item.get('type')=='tool_result' and item.get('tool_use_id')=='toolu_keel_fixture' for message in request.get('messages',[]) if isinstance(message.get('content'),list) for item in message['content'] if isinstance(item,dict)),
        })
        if len(self.server.calls)==1 and any(tool.get('name')=='Bash' for tool in request.get('tools',[])):
            use={"id":"toolu_keel_fixture","type":"tool_use","name":"Bash","input":{}}
            msg={"id":"msg_keel_fixture","type":"message","role":"assistant","content":[],"model":request["model"],"stop_reason":None,"stop_sequence":None,"usage":{"input_tokens":8,"output_tokens":1}}
            frames=[
                ("message_start",{"message":msg}),
                ("content_block_start",{"index":0,"content_block":use}),
                ("content_block_delta",{"index":0,"delta":{"type":"input_json_delta","partial_json":json.dumps({"command":self.server.fixture_command,"description":"Write the disposable marker"})}}),
                ("content_block_stop",{"index":0}),
                ("message_delta",{"delta":{"stop_reason":"tool_use","stop_sequence":None},"usage":{"output_tokens":7}}),
                ("message_stop",{}),
            ]
            body="".join(f"event: {kind}\ndata: {json.dumps(dict(value,type=kind))}\n\n" for kind,value in frames).encode()
            self.send_response(200)
            self.send_header("Content-Type","text/event-stream")
        else:
            message={"id":"msg_keel_fixture_complete","type":"message","role":"assistant","content":[],"model":request["model"],"stop_reason":None,"stop_sequence":None,"usage":{"input_tokens":8,"output_tokens":1}}
            frames=[
                ("message_start",{"message":message}),
                ("content_block_start",{"index":0,"content_block":{"type":"text","text":""}}),
                ("content_block_delta",{"index":0,"delta":{"type":"text_delta","text":"Fixture continuation completed."}}),
                ("content_block_stop",{"index":0}),
                ("message_delta",{"delta":{"stop_reason":"end_turn","stop_sequence":None},"usage":{"output_tokens":5}}),
                ("message_stop",{}),
            ]
            body="".join(f"event: {kind}\ndata: {json.dumps(dict(value,type=kind))}\n\n" for kind,value in frames).encode()
            self.send_response(200)
            self.send_header("Content-Type","text/event-stream")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_claude_proof(root, checkout):
    config = root/'claude-profile'; home = root/'claude-home'
    config.mkdir(); home.mkdir()
    payload = checkout/'complete-fixture.sh'
    payload.write_text("#!/bin/sh\nset -eu\ntest \"$(cat keel-marker.txt)\" = keel-fixture-written\ntest \"$(wc -l < keel-marker.txt)\" -eq 1\ntest ! -e keel-continuation.txt\nprintf '%s\\n' keel-fixture-continued > keel-continuation.txt\n")
    with ThreadingHTTPServer(("127.0.0.1",0),ClaudeProvider) as server:
        server.calls = []
        server.fixture_command = f"bash {payload}"
        threading.Thread(target=server.serve_forever,daemon=True).start()
        env=dict(PATH=os.environ["PATH"],HOME=str(home),TERM="xterm-256color",CLAUDE_CONFIG_DIR=str(config),ANTHROPIC_API_KEY="keel-disposable-fixture-only",
                 ANTHROPIC_BASE_URL=f"http://127.0.0.1:{server.server_port}",CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1",
                 DISABLE_TELEMETRY="1",CLAUDE_CODE_MAX_RETRIES="0")
        flags=["--permission-mode","plan","--tools","","--setting-sources","","--strict-mcp-config","--mcp-config",'{"mcpServers":{}}']
        cli = pexpect.spawn("claude", flags, cwd=str(checkout), env=env, encoding="utf-8", dimensions=(42,120))
        try:
            cli.expect(r"Choose.{0,80}terminal", timeout=15)
            time.sleep(.6)
            cli.send("\r")
            cli.expect(r"Detected a custom API key", timeout=15)
            cli.expect(r"fixture-only", timeout=5)
            time.sleep(.5)
            cli.send("\x1b[A")
            time.sleep(.2)
            cli.send("\r")
            cli.expect(r"Security notes", timeout=10)
            cli.expect(r"Press .*to continue", timeout=5)
            time.sleep(.3)
            cli.send("\r")
            cli.expect(re.escape(str(checkout)), timeout=5)
            cli.expect(r"trust(?:\s|\x1b\[[0-?]*[ -/]*[@-~])+this(?:\s|\x1b\[[0-?]*[ -/]*[@-~])+folder", timeout=5)
            time.sleep(.3)
            cli.send("\x1b[B")
            time.sleep(.2)
            cli.send("\r")
            trusted=False
            for _ in range(30):
                for candidate in (home/'.claude.json', config/'.claude.json'):
                    try:
                        projects=json.loads(candidate.read_text()).get('projects',{})
                    except (FileNotFoundError,ValueError):
                        continue
                    trusted=projects.get(str(checkout),{}).get('hasTrustDialogAccepted') is True
                    if trusted:
                        break
                if trusted:
                    break
                time.sleep(.2)
            print("isolated workspace trusted through native dialog",trusted,flush=True)
            assert trusted, "native trust status was not persisted in an isolated profile"
        finally:
            cli.close(force=True)
        def run(*args):
            return subprocess.run(["claude",*args],cwd=checkout,env=env,capture_output=True,text=True,timeout=12)
        flags=["--permission-mode","default","--tools","Bash","--allowedTools",f"Bash({server.fixture_command})","--setting-sources","","--strict-mcp-config","--mcp-config",'{"mcpServers":{}}']
        job = None
        def run(*args):
            return subprocess.run(["claude",*args],cwd=checkout,env=env,capture_output=True,text=True,timeout=12)
        try:
            start=run("Run the preapproved fixture verification.", "--bg","--name","keel-isolated-continuation","--model","claude-sonnet-4-6",*flags)
            match=re.search(r'backgrounded\s*·\s*([\da-f]{8})\b',start.stdout,re.I)
            assert start.returncode==0 and match,start.stderr
            job=match.group(1)
            marker=checkout/'keel-continuation.txt'
            deadline=time.monotonic()+12
            while time.monotonic()<deadline:
                rows=json.loads(run("agents","--all","--json").stdout)
                state=next((row for row in rows if row["name"]=="keel-isolated-continuation"),{})
                if any(call["has_receipt"] for call in server.calls) and marker.exists():
                    break
                time.sleep(.2)
            assert any(call["has_receipt"] for call in server.calls) and marker.exists(), (server.calls,state.get("status"),state.get("state"))
            assert (checkout/'keel-marker.txt').read_text()=='keel-fixture-written\n'
            assert marker.read_text()=='keel-fixture-continued\n'
            print('same worktree: Codex source exited; Claude verified one original line and wrote one new continuation artifact',flush=True)
        finally:
            if job is not None:
                assert run("stop",job).returncode==0
            server.shutdown()

with tempfile.TemporaryDirectory(prefix="keel-544-codex-effect-") as cwd, ThreadingHTTPServer(("127.0.0.1",0),Provider) as server:
    server.requests = []
    threading.Thread(target=server.serve_forever, daemon=True).start()
    root = Path(cwd)
    checkout = root/'worktree'; profile = root/'profile'; home = root/'home'
    for directory in (checkout,profile,home):
        directory.mkdir()
    subprocess.run(['git','init','-q',str(checkout)],check=True)
    (profile/'config.toml').write_text(f'''model="fixture"
model_provider="keel_fixture"
[model_providers.keel_fixture]
name="Local fixture"
base_url="http://127.0.0.1:{server.server_port}/v1"
wire_api="responses"
requires_openai_auth=false
request_max_retries=0
stream_max_retries=0
[projects.{json.dumps(str(checkout))}]
trust_level="trusted"
''')
    env = dict(PATH=os.environ["PATH"], CODEX_HOME=str(profile), HOME=str(home))
    process = subprocess.Popen(["codex","app-server","--stdio"],cwd=checkout,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
    events = Queue()
    notifications = []
    def read():
        for line in process.stdout:
            events.put(json.loads(line))
    threading.Thread(target=read,daemon=True).start()
    def send(data):
        process.stdin.write(json.dumps(data)+'\n')
        process.stdin.flush()
    next_id = 0
    def rpc(method, params):
        global next_id
        next_id += 1
        send(dict(id=next_id,method=method,params=params))
        while True:
            value = events.get(timeout=12)
            if value.get('id') == next_id:
                assert 'error' not in value, value
                return value['result']
            notifications.append(value)
    try:
        rpc("initialize",{"clientInfo":{"name":"keel-effect-fixture","version":"1"},"capabilities":{"experimentalApi":True}})
        send({"method":"initialized"})
        thread = rpc("thread/start",{"cwd":str(checkout),"model":"fixture","sandbox":"workspace-write","approvalPolicy":"never"})['thread']['id']
        expected_turn = rpc("turn/start",{"threadId":thread,"input":[{"type":"text","text":"Write the disposable fixture marker."}]})['turn']['id']
        while not any(event.get('method')=='turn/completed' for event in notifications):
            notifications.append(events.get(timeout=12))
        turn = next(event['params']['turn'] for event in notifications if event.get('method')=='turn/completed')
        info = (turn.get('error') or {}).get('codexErrorInfo')
        assert (turn['id'],turn['status'],info)==(expected_turn,'failed','usageLimitExceeded'), (turn['status'],info)
        assert len(server.requests)==2, len(server.requests)
        receipts = [item for item in server.requests[1].get('input',[]) if item.get('call_id')=='keel-fixture-write' and item.get('type')=='function_call_output']
        assert receipts, 'tool output disappeared from the following request'
        assert (checkout/'keel-marker.txt').read_text()=='keel-fixture-written\n'
        print('native tool committed one fixture file; one correlated structured tool output; native turn failed usageLimitExceeded')
        print('the worktree effect precedes the account-limit-shaped native receipt')
    finally:
        process.terminate()
        process.wait(timeout=5)
        server.shutdown()
    assert process.poll() is not None
    run_claude_proof(root, checkout)

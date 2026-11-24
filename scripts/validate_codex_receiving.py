#!/usr/bin/env python3
"""Public-interface checks for Codex hooks; native tests are opt-in."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import shlex
import shutil
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/keel"
CLI = ROOT / "bin/keel.js"
RECEIVER = PLUGIN / "scripts/codex-mail-hook.js"
HOOK_LABELS = {
    ("SessionStart", "session-start.js"): "Keel: Session context",
    ("SessionStart", "codex-mail-hook.js"): "Keel: Mail at session start",
    ("UserPromptSubmit", "codex-mail-hook.js"): "Keel: Mail before prompt",
    ("PreToolUse", "pretooluse-guard.js"): "Keel: Write guard",
}


def check_hook_labels(hooks):
    event_names = {name[0].lower(): name[0] for name in HOOK_LABELS}
    found = {
        key: hook.get("statusMessage")
        for hook in hooks
        for key in HOOK_LABELS
        if event_names.get(hook.get("eventName", "").lower()) == key[0]
        and key[1] in hook["command"]
    }
    assert found == HOOK_LABELS, f"Keel hook labels missing or ambiguous: {found}"



def run(args, cwd=ROOT, env=None, input=None, check=True, timeout=30):
    result = subprocess.run(args, cwd=cwd, env=env, input=input, text=True,
                            capture_output=True, timeout=timeout)
    if check and result.returncode:
        raise AssertionError(f"{args}: exit {result.returncode}\n{result.stdout}{result.stderr}")
    return result


def mail(repo, *args, role="receiver"):
    env = dict(os.environ, KEEL_MAIL_ROLE=role)
    return run(["node", str(CLI), "mail", *args], cwd=repo, env=env)


def inbox(repo):
    return {str(p.relative_to(repo)): p.read_bytes()
            for p in (repo / ".git/keel-mailbox").rglob("*") if p.is_file()}


def invoke(repo, event, provider=None, timeout_ms=None):
    env = dict(os.environ, KEEL_MAIL_ROLE="receiver",
               KEEL_CLI=provider or shlex.join(["node", str(CLI)]))
    if timeout_ms:
        env["KEEL_HOOK_TIMEOUT_MS"] = str(timeout_ms)
    result = run(["node", str(RECEIVER), event], cwd=repo, env=env,
                 input=json.dumps({"cwd": str(repo), "hook_event_name": event}))
    assert not result.stderr, result.stderr
    return json.loads(result.stdout) if result.stdout.strip() else None


def read_hook_response(script, repo, event, env=None):
    proc = subprocess.Popen(
        ["node", str(PLUGIN / "scripts" / script)],
        cwd=repo, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True,
    )
    try:
        proc.stdin.write(json.dumps({"cwd": str(repo), **event}))
        proc.stdin.close()
        proc.stdin = None
        # Exercise the real pipe. A reader that has not been scheduled must
        # still receive the whole JSON response when it starts draining.
        time.sleep(0.3)
        out, err = proc.communicate(timeout=12)
        assert proc.returncode == 0 and not err, (proc.returncode, err)
        try:
            return json.loads(out)["hookSpecificOutput"]
        except (ValueError, KeyError) as error:
            raise AssertionError(f"{script}: hook response truncated ({len(out)} characters)") from error
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)


def buffered_output():
    with tempfile.TemporaryDirectory(prefix="keel-codex-hook-output-") as raw:
        repo = Path(raw)
        change = repo / "openspec/changes/probe"
        change.mkdir(parents=True)
        context = {
            "status": "ready",
            "selection": {"change": "probe", "task": "1.1", "source": "fixture"},
            "read": ["fixture/" + "a" * 180000 + "/projection-tail"],
        }
        provider = repo / "cli.js"
        provider.write_text(
            "process.stdout.write(process.argv[2] === '--version' ? '5.231.5' : "
            + json.dumps(json.dumps(context)) + ")",
            encoding="utf-8",
        )
        env = dict(os.environ, KEEL_CLI=shlex.join(["node", str(provider)]))
        projection = read_hook_response("session-start.js", repo, {"hook_event_name": "SessionStart"}, env)
        assert "/projection-tail" in projection["additionalContext"]
        tasks = change / "tasks.md"
        tasks.write_text("- [ ] 1.1 Write in Touch only\n", encoding="utf-8")
        touch = [f"src/fixture-{index:05d}.js" for index in range(12000)]
        manifest = {
            "schema": "keel-write-guard/v1", "change": "probe", "task": "1.1",
            "authority": [{"path": str(tasks.relative_to(repo)), "sha256": hashlib.sha256(tasks.read_bytes()).hexdigest()}],
            "touch": touch,
        }
        (repo / "keel").mkdir()
        (repo / "keel/guard.json").write_text(json.dumps(manifest), encoding="utf-8")
        decision = read_hook_response("pretooluse-guard.js", repo, {
            "hook_event_name": "PreToolUse", "tool_name": "Edit",
            "tool_input": {"file_path": str(repo / "src/outside.js")},
        })
        assert decision["permissionDecision"] == "deny"
        assert touch[-1] in decision["permissionDecisionReason"]
    print("codex hook output: complete SessionStart projection and PreToolUse verdict")


def behavior():
    manifest = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text())
    assert manifest.get("hooks") == "./hooks/codex.json", "Codex still uses the args-only shared hooks"
    hooks = json.loads((PLUGIN / "hooks/codex.json").read_text())["hooks"]
    assert set(hooks) == {"SessionStart", "PreToolUse", "UserPromptSubmit"}
    assert not any(field in json.dumps(hooks) for field in ["asyncRewake", "watchPaths", "FileChanged"])
    declared = [dict(h, eventName=event) for event, groups in hooks.items() for g in groups for h in g["hooks"]]
    check_hook_labels(declared)
    buffered_output()
    commands = [h["command"] for h in declared]
    for script in ["session-start.js", "pretooluse-guard.js", "codex-mail-hook.js"]:
        assert any(script in command for command in commands), script
    with tempfile.TemporaryDirectory(prefix="keel-codex-mail-") as raw:
        repo = Path(raw)
        run(["git", "init", "-q", str(repo)])
        assert invoke(repo, "session-start") is None
        assert invoke(repo, "user-prompt-submit") is None
        sent = json.loads(mail(repo, "send", "--to", "receiver", "--subject", "delivery probe",
                               "--body", "PRIVATE_BODY_NOT_CONTEXT", "--json", role="sender").stdout)
        before = inbox(repo)
        for event, native in [("session-start", "SessionStart"),
                              ("user-prompt-submit", "UserPromptSubmit"),
                              ("user-prompt-submit", "UserPromptSubmit")]:
            output = invoke(repo, event)
            assert set(output) == {"hookSpecificOutput"}
            specific = output["hookSpecificOutput"]
            assert set(specific) == {"hookEventName", "additionalContext"}
            assert specific["hookEventName"] == native
            text = specific["additionalContext"]
            for expected in [sent["id"], "sender", "delivery probe", "keel mail read", "not", "authorization"]:
                assert expected in text, (expected, text)
            assert "PRIVATE_BODY_NOT_CONTEXT" not in text
            assert inbox(repo) == before, "notice consumed or changed mail"
        mail(repo, "read", "--id", sent["id"])
        assert invoke(repo, "user-prompt-submit") is None
        unbound = dict(os.environ)
        unbound.pop("KEEL_MAIL_ROLE", None)
        unbound["KEEL_CLI"] = shlex.join(["node", str(CLI)])
        assert not run(["node", str(RECEIVER), "session-start"], cwd=repo,
                       env=unbound, input=json.dumps({"cwd": str(repo)})).stdout.strip()
        for name, source in [
            ("exit", "process.exit(1)"),
            ("invalid", "process.stdout.write('not JSON')"),
            ("wrong-shape", "process.stdout.write(JSON.stringify({decision:'block'}))"),
            ("timeout", "setTimeout(()=>{},2000)"),
            ("blocked", "process.exit(2)"),
        ]:
            boundary = repo / f"{name}.js"
            boundary.write_text(source)
            output = invoke(repo, "user-prompt-submit", shlex.join(["node", str(boundary)]), 50)
            assert set(output) == {"systemMessage"}, output
            assert "keel mail list" in output["systemMessage"]
    print("codex-receiving: startup/next-input, repeated non-consuming notices, quiet inboxes and failure fallback passed")


def hooks_list(repo, env):
    """Ask the real app-server to discover hooks; no turn or model is started."""
    process = subprocess.Popen(["codex", "app-server", "--stdio"], cwd=repo, env=env,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True, bufsize=1)
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    def rpc(number, method, params):
        process.stdin.write(json.dumps({"id": number, "method": method, "params": params}) + "\n")
        process.stdin.flush()
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if selector.select(1):
                line = process.stdout.readline()
                if not line:
                    raise AssertionError("Codex app-server exited before hooks/list")
                value = json.loads(line)
                if value.get("id") == number:
                    assert "error" not in value, value
                    return value["result"]
        raise AssertionError(f"Codex app-server timed out: {method}")
    try:
        rpc(1, "initialize", {"clientInfo": {"name": "keel-receiving-probe", "version": "1"},
                             "capabilities": {"experimentalApi": True}})
        process.stdin.write('{"method":"initialized"}\n'); process.stdin.flush()
        return rpc(2, "hooks/list", {"cwds": [str(repo)]})["data"][0]
    finally:
        selector.close()
        process.terminate(); process.wait(timeout=5)


def native():
    assert shutil.which("codex"), "native probe requires the Codex CLI"
    requests = []
    class Capture(BaseHTTPRequestHandler):
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            # Deliberately stop at the model boundary: no model or other agent
            # runs, no tool is requested, and no remote inference is contacted.
            body = b'{"error":{"message":"Keel probe captured the request; no model executes","type":"invalid_request_error"}}'
            self.send_response(400); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        def log_message(self, *args):
            pass
    with tempfile.TemporaryDirectory(prefix="keel-native-codex-") as raw:
        base = Path(raw); repo = base / "consumer"; home = base / "codex-home"
        repo.mkdir(); home.mkdir(); run(["git", "init", "-q", str(repo)])
        shutil.copytree(PLUGIN, repo / "plugins/keel")
        market = repo / ".agents/plugins/marketplace.json"
        market.parent.mkdir(parents=True)
        market.write_bytes((ROOT / ".agents/plugins/marketplace.json").read_bytes())
        server = ThreadingHTTPServer(("127.0.0.1", 0), Capture)
        worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
        try:
            config = f'''model = "keel-probe"
model_provider = "keel_probe"
[model_providers.keel_probe]
name = "Keel local request capture"
base_url = "http://127.0.0.1:{server.server_port}/v1"
wire_api = "responses"
requires_openai_auth = false
request_max_retries = 0
stream_max_retries = 0
[projects.{json.dumps(str(repo))}]
trust_level = "trusted"
'''
            (home / "config.toml").write_text(config)
            env = dict(os.environ, CODEX_HOME=str(home), KEEL_MAIL_ROLE="receiver",
                       KEEL_CLI=shlex.join(["node", str(CLI)]))
            env.pop("OPENAI_API_KEY", None)
            run(["node", str(CLI), "--init", "--target", "codex"], cwd=repo, env=env)
            run(["codex", "plugin", "marketplace", "add", str(repo)], cwd=repo, env=env)
            run(["codex", "plugin", "add", "keel@keel-marketplace"], cwd=repo, env=env)
            found = hooks_list(repo, env)
            assert not found["errors"], found
            hooks = found["hooks"]
            assert len(hooks) == 4, hooks
            check_hook_labels(hooks)
            assert all(h["trustStatus"] == "untrusted" for h in hooks), hooks
            assert all(".js" in h["command"] for h in hooks), hooks
            assert {h["eventName"] for h in hooks} == {"preToolUse", "sessionStart", "userPromptSubmit"}
            sent = json.loads(mail(repo, "send", "--to", "receiver", "--subject", "native-delivery-proof",
                                   "--body", "BODY_MUST_STAY_LOCAL", "--json", role="sender").stdout)
            before = inbox(repo)
            command = ["codex", "exec", "--ephemeral", "--json", "--sandbox", "read-only",
                       "-C", str(repo), "Keel runtime probe: do not execute tools."]
            untrusted = run(command, cwd=repo, env=env, check=False, timeout=40)
            assert requests, f"No local model request: {untrusted.stderr}"
            assert "native-delivery-proof" not in json.dumps(requests[-1]), "untrusted hook ran"
            requests.clear()
            # The only bypass is this isolated invocation, after reviewing the
            # repository's hook sources. Never write personal persisted trust.
            trusted = run(command[:2] + ["--dangerously-bypass-hook-trust"] + command[2:],
                          cwd=repo, env=env, check=False, timeout=40)
            assert requests, f"No trusted local model request: {trusted.stderr}"
            text = json.dumps(requests[-1])
            for expected in [sent["id"], "native-delivery-proof", "keel mail read", "authorization",
                             "Keel session projection (disposable", "context status: idle"]:
                assert expected in text, (expected, trusted.stdout, trusted.stderr)
            assert text.count("native-delivery-proof") >= 2, "startup and prompt contexts were not both delivered"
            assert "BODY_MUST_STAY_LOCAL" not in text
            assert inbox(repo) == before, "native hook consumed mail"
            assert all(h["trustStatus"] == "untrusted" for h in hooks_list(repo, env)["hooks"])
            print(run(["codex", "--version"], cwd=repo, env=env).stdout.strip())
            print("native: four executable hooks discovered; untrusted hooks skipped; disposable idle projection and startup/prompt notices reached the real Codex model request; inbox unchanged; no model executed or persisted trust granted")
        finally:
            server.shutdown(); server.server_close(); worker.join(timeout=5)


def consumer():
    """The current test driver owns the full Keel flow; Codex is not a delegate."""
    with tempfile.TemporaryDirectory(prefix="keel-codex-consumer-") as raw:
        repo = Path(raw)
        run(["git", "init", "-q", str(repo)])
        env = dict(os.environ, CODEX_HOME=str(repo / "codex-home"))
        def cli(*args):
            return run(["node", str(CLI), *args], cwd=repo, env=env)
        cli("--init", "--target", "codex")
        doctor = cli("--doctor", "--target", "codex").stdout
        assert "OpenSpec action skills: ok" in doctor, doctor
        assert "OpenSpec commands: ok" in doctor, doctor
        assert "overlay: ok" in doctor, doctor
        assert "guard enforcement: manual" in doctor, doctor
        name = "codex-acceptance-probe"
        cli("openspec", "new", "change", name)
        change = repo / "openspec/changes" / name
        (change / "proposal.md").write_text("## Why\nPublic deterministic behavior proof in a clean Codex consumer.\n")
        (change / "design.md").write_text("## Decisions\n- D1 — A public executable must print `hello keel`. Basis: disposable acceptance fixture.\n")
        spec = change / "specs/greeting/spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text('''## ADDED Requirements
### Requirement: Public greeting
The executable SHALL print exactly `hello keel`.
#### Scenario: Greeting runs
- **WHEN** `node hello.js` runs
- **THEN** stdout is exactly `hello keel` followed by one newline.
''')
        (change / "tasks.md").write_text('''## 1. Probe
- [ ] 1.1 Print the public greeting
  - Covers:
    - D1
    - greeting / Public greeting
  - Touch:
    - hello.js
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node hello.js` prints exactly `hello keel`.
  - Evidence:
    - Contract: pending
## Invalidates
- None.
## Expectation Coverage
- E1: D1 and greeting / Public greeting are observed through node. Covered by: 1.1
''')
        started = json.loads(cli("gate", "task-start", ".", "--change", name, "--task", "1.1",
                                 "--target", "codex", "--record", "--json").stdout)
        assert started["status"] == "pass", started
        assert not (repo / "keel/guard.json").exists(), "Codex claimed an automatic guard"
        red = run(["node", "hello.js"], cwd=repo, check=False)
        assert red.returncode != 0
        (repo / "hello.js").write_text('console.log("hello keel");\n')
        green = run(["node", "hello.js"], cwd=repo)
        assert green.stdout == "hello keel\n"
        tasks = (change / "tasks.md").read_text()
        for key, value in {
            "M1": "Exit 0, public node output exactly hello keel.",
            "M1.red": "Exit 1, MODULE_NOT_FOUND before implementation.",
            "M1.green": "Exit 0, public node output exactly hello keel.",
            "Status": "pass", "Acceptance check": "Node executed the public greeting and output matched exactly.",
            "Scope check": "Only hello.js was written as the product; task record lives in its own change.",
            "Findings": "none",
        }.items():
            tasks = tasks.replace(f"- {key}: pending", f"- {key}: {value}")
        (change / "tasks.md").write_text(tasks)
        completed = json.loads(cli("gate", "task-complete", ".", "--change", name,
                                   "--task", "1.1", "--json").stdout)
        assert completed["status"] == "pass", completed
        (change / "tasks.md").write_text(tasks.replace("- [ ]", "- [x]"))
        closed = json.loads(cli("gate", "change-close", ".", "--change", name,
                                "--action", "archive", "--json").stdout)
        assert closed["status"] == "pass", closed
        print("consumer: clean Codex init/doctor, proposal, recorded task-start, public red/green behavior, Review, task-complete and change-close passed; guard enforcement remained manual")


UPGRADE_HOOK = r"""const fs = require("fs");
try { fs.readFileSync(0, "utf8"); } catch {}
const v = JSON.parse(fs.readFileSync(__dirname + "/../.codex-plugin/plugin.json", "utf8")).version;
const name = process.argv[2] === "ss" ? "SessionStart" : "UserPromptSubmit";
process.stdout.write(JSON.stringify({hookSpecificOutput: {hookEventName: name,
  additionalContext: `UPGRADE-PROBE version=${v} dir=${__dirname}`}}));
"""


def write_upgrade_plugin(repo, version):
    plugin = repo / "plugins/probe"
    if plugin.exists():
        shutil.rmtree(plugin)
    (plugin / ".codex-plugin").mkdir(parents=True)
    (plugin / "scripts").mkdir()
    (plugin / "hooks").mkdir()
    (plugin / ".codex-plugin/plugin.json").write_text(json.dumps(
        {"name": "probe", "version": version, "hooks": "./hooks/codex.json"}))
    (plugin / "scripts/hook.js").write_text(UPGRADE_HOOK)
    (plugin / "hooks/codex.json").write_text(json.dumps({"hooks": {
        "SessionStart": [{"hooks": [{"type": "command", "timeout": 10,
                                     "command": 'node "${PLUGIN_ROOT}/scripts/hook.js" ss'}]}],
        "UserPromptSubmit": [{"hooks": [{"type": "command", "timeout": 10,
                                         "command": 'node "${PLUGIN_ROOT}/scripts/hook.js" ups'}]}]}}))


class AppServer:
    """A long-lived `codex app-server`, the shape a running Codex session has."""
    def __init__(self, repo, env):
        self.process = subprocess.Popen(["codex", "app-server"], cwd=repo, env=env, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.number = 0
        self.rpc("initialize", {"clientInfo": {"name": "keel-upgrade-probe", "version": "1"},
                                "capabilities": {"experimentalApi": True}})
        self.process.stdin.write('{"method":"initialized"}\n'); self.process.stdin.flush()

    def pump(self, seconds):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if self.selector.select(0.5):
                if not self.process.stdout.readline():
                    raise AssertionError("Codex app-server exited")

    def rpc(self, method, params):
        self.number += 1
        number = self.number
        self.process.stdin.write(json.dumps({"id": number, "method": method, "params": params}) + "\n")
        self.process.stdin.flush()
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if self.selector.select(1):
                line = self.process.stdout.readline()
                if not line:
                    raise AssertionError(f"Codex app-server exited during {method}")
                value = json.loads(line)
                if value.get("id") == number:
                    assert "error" not in value, value
                    return value["result"]
        raise AssertionError(f"Codex app-server timed out: {method}")

    def close(self):
        self.selector.close()
        self.process.terminate(); self.process.wait(timeout=5)


def native_upgrade():
    """#204: a running Codex session's next hook runs the upgraded plugin.

    Isolated CODEX_HOME, a request-capture endpoint so no model runs, and a
    throwaway plugin whose hooks report their own version and directory. The
    hooks are trusted in the isolated config only, by the hashes app-server
    reports, never in the personal one."""
    assert shutil.which("codex"), "native upgrade probe requires the Codex CLI"
    requests = []
    class Capture(BaseHTTPRequestHandler):
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            body = b'{"error":{"message":"Keel probe captured the request; no model executes","type":"invalid_request_error"}}'
            self.send_response(400); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        def log_message(self, *args):
            pass
    import re
    with tempfile.TemporaryDirectory(prefix="keel-native-upgrade-") as raw:
        base = Path(raw); repo = base / "repo"; home = base / "codex-home"
        repo.mkdir(); home.mkdir(); run(["git", "init", "-q", str(repo)])
        market = repo / ".agents/plugins/marketplace.json"
        market.parent.mkdir(parents=True)
        market.write_text(json.dumps({"name": "probe-market", "plugins": [
            {"name": "probe", "source": {"source": "local", "path": "./plugins/probe"},
             "policy": {"installation": "AVAILABLE"}}]}))
        write_upgrade_plugin(repo, "1.0.0")
        server = ThreadingHTTPServer(("127.0.0.1", 0), Capture)
        worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
        app = None
        try:
            (home / "config.toml").write_text(f"""model = "keel-probe"
model_provider = "keel_probe"
[model_providers.keel_probe]
name = "Keel local request capture"
base_url = "http://127.0.0.1:{server.server_port}/v1"
wire_api = "responses"
requires_openai_auth = false
request_max_retries = 0
stream_max_retries = 0
[projects.{json.dumps(str(repo))}]
trust_level = "trusted"
""")
            env = dict(os.environ, CODEX_HOME=str(home)); env.pop("OPENAI_API_KEY", None)
            run(["codex", "plugin", "marketplace", "add", str(repo)], cwd=repo, env=env)
            run(["codex", "plugin", "add", "probe@probe-market"], cwd=repo, env=env)
            app = AppServer(repo, env)
            hooks = app.rpc("hooks/list", {"cwds": [str(repo)]})["data"][0]["hooks"]
            app.close(); app = None
            with open(home / "config.toml", "a") as config:
                for hook in hooks:
                    config.write(f'\n[hooks.state.{json.dumps(hook["key"])}]\n'
                                 f'trusted_hash = {json.dumps(hook["currentHash"])}\n')

            def turn(thread, text):
                before = len(requests)
                app.rpc("turn/start", {"threadId": thread, "input": [{"type": "text", "text": text}]})
                deadline = time.monotonic() + 30
                while len(requests) == before and time.monotonic() < deadline:
                    app.pump(1)
                assert len(requests) > before, f"no model request for {text!r}"
                return set(re.findall(r"UPGRADE-PROBE version=(\S+) dir=([^\s\"\\]+)", json.dumps(requests[-1])))

            app = AppServer(repo, env)
            cache = home / "plugins/cache/probe-market/probe"
            thread = app.rpc("thread/start", {"cwd": str(repo)})["thread"]["id"]
            first = turn(thread, "upgrade probe one")
            assert {v for v, _ in first} == {"1.0.0"}, first
            write_upgrade_plugin(repo, "2.0.0")
            run(["codex", "plugin", "add", "probe@probe-market"], cwd=repo, env=env)
            assert sorted(p.name for p in cache.iterdir()) == ["2.0.0"], sorted(p.name for p in cache.iterdir())
            trust = [h["trustStatus"] for h in app.rpc("hooks/list", {"cwds": [str(repo)]})["data"][0]["hooks"]]
            assert trust == ["trusted", "trusted"], trust
            second = turn(thread, "upgrade probe two")
            fresh = {(v, d) for v, d in second if v == "2.0.0"}
            assert fresh and all(d.startswith(os.path.realpath(cache / "2.0.0")) for _, d in fresh), second
            print(run(["codex", "--version"], cwd=repo, env=env).stdout.strip())
            print("native-upgrade: after codex plugin add of 2.0.0 under a running app-server, the same thread's next hook ran 2.0.0 from its new directory; 1.0.0's directory was deleted and both hooks stayed trusted; no model executed and no personal trust was written")
        finally:
            if app is not None:
                app.close()
            server.shutdown(); server.server_close(); worker.join(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", action="store_true")
    parser.add_argument("--consumer", action="store_true")
    parser.add_argument("--native-upgrade", action="store_true")
    args = parser.parse_args()
    if args.native_upgrade:
        native_upgrade()
    elif args.native:
        native()
    elif args.consumer:
        consumer()
    else:
        behavior()

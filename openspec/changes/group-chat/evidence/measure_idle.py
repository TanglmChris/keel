import importlib.util, json, os, subprocess, sys, tempfile, time
from pathlib import Path
ROOT = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("fs", ROOT / "scripts/fake_slack.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def git(cwd, *a): subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True)
with tempfile.TemporaryDirectory() as raw, m.FakeSlack() as slack:
    base = Path(raw); env = {k: v for k, v in os.environ.items() if k not in ("KEEL_CHAT_ROLE", "KEEL_MAIL_ROLE")}
    env.update(KEEL_HOME=str(base / "home"), KEEL_SLACK_API_BASE=slack.api_base, KEEL_SLACK_BOT_TOKEN="xoxb-t", KEEL_SLACK_APP_TOKEN="xapp-t", KEEL_CHAT_MACHINE="measure")
    for i in range(3):
        repo = base / f"p{i}"; repo.mkdir()
        git(repo, "init", "-q"); git(repo, "-c", "user.email=a@b", "-c", "user.name=a", "commit", "-q", "--allow-empty", "-m", "s")
        k = lambda *a: subprocess.run(["node", str(ROOT / "bin/keel.js"), "chat", *a], cwd=repo, env=env, capture_output=True, text=True)
        k("role", "--set", "rtl"); k("group", "create", "soc")
        for n in range(50): k("post", "soc", f"history {n}")
        (repo / "keel").mkdir(); (repo / "keel/chat.json").write_text(json.dumps({"slack": {"enabled": True, "owner": "U", "members": {"U": "owner"}, "channels": {"soc": f"C{i}"}}}))
        k("bridge", "add")
    p = subprocess.Popen(["node", str(ROOT / "bin/keel.js"), "chat", "bridge", "run"], cwd=base / "p0", env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    slack.wait_for(lambda: slack.sockets, 15); time.sleep(10)  # past the initial flush and catch-up
    rss, cpu = [], []
    t0 = time.time(); cpu_t0 = None
    for _ in range(12):
        out = subprocess.run(["ps", "-o", "rss=,time=", "-p", str(p.pid)], capture_output=True, text=True).stdout.split()
        rss.append(int(out[0]))
        mm, ss = out[1].split(":"); secs = int(mm) * 60 + float(ss)
        cpu.append(secs)
        time.sleep(5)
    wall = time.time() - t0
    p.terminate(); p.wait(timeout=10)
    print(f"idle rss: min {min(rss)/1024:.1f} MB, max {max(rss)/1024:.1f} MB over {wall:.0f}s, 3 projects x 50 records; cpu time {cpu[-1]-cpu[0]:.2f}s in {wall:.0f}s wall = {(cpu[-1]-cpu[0])/wall*100:.2f}% of one core")

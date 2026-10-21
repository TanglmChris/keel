"""Keel validation: shift (split from validate_plugin.py, #409)."""
from __future__ import annotations

import contextlib
import json
import gzip
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import ast
import atexit
import signal
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from validation.common import (
    BOOTSTRAP_BLOCK_BYTE_BUDGET,
    ROOT,
    extract_managed_block,
    chat_environment,
    chat_json,
    chat_log,
    chat_logs_snapshot,
    chat_records_with,
    chat_scratch_group,
    chat_session_start,
    chat_wake_scratch,
    chat_worktree,
    host_project_name,
    mailbox_common_dir,
    mailbox_repository,
    report,
    run_keel,
    run_session_start_hook,
    session_start_context,
    shift_scratch,
    snapshot_files,
    task_capsule_compact_fixture,
    task_contract_fixture,
    write_authorize_config,
    write_text,
)
from validation import registry


def validate_two_live_sessions_on_one_role_scenario() -> int:
    """Issue #369 point 4: two live sessions bound to one role are reported.

    On 2026-10-18 a desktop PM session and its CLI copy both ran as `iecc-pm`
    in one worktree: both posted under the one name and shared one read
    cursor, and neither knew. Each session now records itself under the role;
    with two live ones `keel context`, `keel chat post` and `keel chat unread`
    say so, and the warning goes once one has ended.
    """
    label = "two-live-sessions-on-one-role:"
    with tempfile.TemporaryDirectory(prefix="keel-twins-369-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)
        write_text(verify / "openspec/specs/.keep", "")
        other = subprocess.Popen(["sleep", "300"])
        try:
            def as_session(sid: str, pid: int) -> dict:
                return {**env, "CLAUDE_CODE_ENTRYPOINT": "cli", "CLAUDE_CODE_SESSION_ID": sid, "CLAUDE_PID": str(pid)}

            def start(sid: str, pid: int) -> None:
                subprocess.run(["node", str(ROOT / "bin" / "keel.js"), "chat", "hook", "session-start"], cwd=verify,
                               env=as_session(sid, pid), text=True, capture_output=True, check=False,
                               input=json.dumps({"cwd": str(verify), "hook_event_name": "SessionStart", "session_id": sid, "source": "startup"}))

            start("sess-a", os.getpid())
            alone = json.loads(run_keel(verify, "context", "--json", env=as_session("sess-a", os.getpid())).stdout)
            if any("live sessions" in w for w in alone.get("warnings", [])):
                report(f"{label} one session was reported as two: {alone.get('warnings')!r}")
                return 1
            start("sess-b", other.pid)
            context = json.loads(run_keel(verify, "context", "--json", env=as_session("sess-a", os.getpid())).stdout)
            warning = next((w for w in context.get("warnings", []) if "live sessions" in w), "")
            for needle in ("verify", "sess-a", "sess-b", "read cursor"):
                if needle not in warning:
                    report(f"{label} keel context's warning does not name {needle!r}: {context.get('warnings')!r}")
                    return 1
            posted = run_keel(verify, "chat", "post", "soc", "hello", env=as_session("sess-a", os.getpid()))
            if "live sessions" not in posted.stderr:
                report(f"{label} keel chat post does not warn: {posted.stdout!r} {posted.stderr!r}")
                return 1
            read = run_keel(verify, "chat", "unread", "--json", env=as_session("sess-a", os.getpid()))
            if "live sessions" not in read.stderr:
                report(f"{label} keel chat unread does not warn: {read.stderr!r}")
                return 1
            json.loads(read.stdout)
            other.kill()
            other.wait()
            after = json.loads(run_keel(verify, "context", "--json", env=as_session("sess-a", os.getpid())).stdout)
            if any("live sessions" in w for w in after.get("warnings", [])):
                report(f"{label} the warning stayed after one session ended: {after.get('warnings')!r}")
                return 1
        finally:
            if other.poll() is None:
                other.kill()
    if "two-live-sessions-on-one-role" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("two-live-sessions-on-one-role scenario passed.")
    return 0


def validate_patrol_rearm_scenario() -> int:
    """Issue #260: the patrolling role is reminded to re-arm its schedule.

    `patrol:` names the role and interval; that role's `keel context`, session
    projection, and `keel shift resume` remind it; other roles and a broken
    declaration are quiet. Keel schedules nothing.
    """
    label = "patrol-rearm:"
    with tempfile.TemporaryDirectory(prefix="keel-patrol-rearm-") as raw:
        base = Path(raw)
        repo = mailbox_repository(base / "repo")
        write_text(repo / "openspec/specs/.keep", "")
        write_authorize_config(repo, "patrol:\n  role: iecc-pm\n  every: 30m\n")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", "patrol"], cwd=repo, check=True, capture_output=True)
        pm = chat_worktree(repo, base / "pm")
        rtl = chat_worktree(repo, base / "rtl")
        env = chat_environment()
        run_keel(pm, "chat", "role", "--set", "iecc-pm", env=env)
        run_keel(rtl, "chat", "role", "--set", "rtl", env=env)

        def look(cwd: Path) -> tuple[dict, str]:
            context = json.loads(run_keel(cwd, "context", "--json", env=env).stdout)
            session = run_session_start_hook(
                cwd, {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(cwd)},
                keel_cli=f'node "{ROOT / "bin" / "keel.js"}"',
            )
            return context, session_start_context(session) or ""

        context, note = look(pm)
        if context.get("patrol") != {"role": "iecc-pm", "every": "30m"}:
            report(f"{label} the coordinator's context carries patrol {context.get('patrol')!r}.")
            return 1
        if "keel patrol" not in note or "30m" not in note:
            report(f"{label} the coordinator's projection does not remind it: {note!r}")
            return 1
        ready = run_keel(pm, "shift", "ready", "next: keep patrolling", env=env)
        if ready.returncode != 0:
            report(f"{label} keel shift ready failed: {ready.stdout} {ready.stderr}")
            return 1
        resumed = run_keel(pm, "shift", "resume", env=env)
        tail = resumed.stdout.strip().splitlines()[-1] if resumed.stdout.strip() else ""
        if "keel patrol" not in tail or "30m" not in tail:
            report(f"{label} keel shift resume does not end with the reminder: {resumed.stdout!r}")
            return 1

        context, note = look(rtl)
        if "patrol" in context:
            report(f"{label} another role carries patrol: {context.get('patrol')!r}")
            return 1
        if "keel patrol" in note:
            report(f"{label} another role's projection reminds it: {note!r}")
            return 1

        write_authorize_config(pm, "patrol:\n  role: iecc-pm\n  every: soon\n")
        broken = json.loads(run_keel(pm, "context", "--json", env=env).stdout)
        if "patrol" in broken:
            report(f"{label} a malformed declaration still reminds: {broken.get('patrol')!r}")
            return 1
        if not any("patrol" in w for w in broken.get("warnings", [])):
            report(f"{label} the malformed declaration is not reported: {broken.get('warnings')!r}")
            return 1
    report("patrol-rearm scenario passed.")
    return 0


def validate_patrol_host_task_scenario() -> int:
    """Issue #295: `patrol:` names the host task; `keel patrol task` renders it.

    The rendered task carries the id, a cron from `every:`, the declared model
    or none, and a prompt running the change-based patrol by path; it writes
    nothing. A declared host task changes the reminder.
    """
    label = "patrol-host-task:"
    with tempfile.TemporaryDirectory(prefix="keel-patrol-host-") as raw:
        base = Path(raw)
        repo = mailbox_repository(base / "repo")
        write_text(repo / "openspec/specs/.keep", "")
        declaration = "patrol:\n  role: rtl\n  every: 30m\n  host_task: soc-patrol\n"
        write_authorize_config(repo, declaration)
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", "patrol"], cwd=repo, check=True, capture_output=True)
        rtl = chat_worktree(repo, base / "rtl")
        env = chat_environment()

        unbound = run_keel(rtl, "patrol", "task", env=env)
        if unbound.returncode == 0:
            report(f"{label} keel patrol task was accepted with no worktree bound to rtl.")
            return 1
        run_keel(rtl, "chat", "role", "--set", "rtl", env=env)
        before = subprocess.run(["git", "status", "--porcelain"], cwd=rtl, capture_output=True, text=True).stdout
        task = run_keel(rtl, "patrol", "task", env=env)
        if task.returncode != 0:
            report(f"{label} keel patrol task failed: {task.stdout} {task.stderr}")
            return 1
        for needle in ("soc-patrol", "*/30 * * * *", "no model is declared",
                       f"keel patrol --repo {rtl.resolve()} --since-last --notify"):
            if needle not in task.stdout:
                report(f"{label} the rendered task does not carry {needle!r}: {task.stdout!r}")
                return 1
        after = subprocess.run(["git", "status", "--porcelain"], cwd=rtl, capture_output=True, text=True).stdout
        if before != after:
            report(f"{label} keel patrol task changed the worktree: {after!r}")
            return 1
        write_authorize_config(rtl, declaration + "  model: small-model\n")
        modelled = run_keel(rtl, "patrol", "task", env=env)
        if "small-model" not in modelled.stdout:
            report(f"{label} the declared model is not rendered: {modelled.stdout!r}")
            return 1
        if "no model is declared" in modelled.stdout:
            report(f"{label} a declared model is still reported as undeclared: {modelled.stdout!r}")
            return 1

        context = json.loads(run_keel(rtl, "context", "--json", env=env).stdout)
        if (context.get("patrol") or {}).get("hostTask") != "soc-patrol":
            report(f"{label} keel context carries patrol {context.get('patrol')!r}.")
            return 1
        session = run_session_start_hook(
            rtl, {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(rtl)},
            keel_cli=f'node "{ROOT / "bin" / "keel.js"}"',
        )
        note = session_start_context(session) or ""
        if "soc-patrol" not in note or "still enabled" not in note:
            report(f"{label} the session-start note does not name the host task: {note!r}")
            return 1
        if "re-create it with the host" in note:
            report(f"{label} the note still asks to re-create a session schedule: {note!r}")
            return 1

        write_authorize_config(rtl, "patrol:\n  role: rtl\n  every: 30m\n  host_task: Bad_Id\n")
        broken = json.loads(run_keel(rtl, "context", "--json", env=env).stdout)
        if not any("host_task" in w and "Bad_Id" in w for w in broken.get("warnings", [])):
            report(f"{label} a malformed host_task is not reported by name: {broken.get('warnings')!r}")
            return 1
    report("patrol-host-task scenario passed.")
    return 0


def validate_patrol_since_last_scenario() -> int:
    """Issue #295: a scheduled patrol reports only what changed, once.

    `--since-last` records a baseline, then reports changed entries and exits
    2; `--notify` sends them to the coordinator as one message from
    `keel-patrol`; an unchanged run is quiet. `--notify` alone is refused.
    """
    label = "patrol-since-last:"
    with tempfile.TemporaryDirectory(prefix="keel-patrol-since-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)

        def patrol(*args: str) -> subprocess.CompletedProcess[str]:
            return run_keel(rtl, "patrol", *args, env=env)

        def notices() -> list[str]:
            return chat_records_with(rtl, "dm-keel-patrol--rtl", "changed")

        alone = patrol("--notify")
        if alone.returncode != 1:
            report(f"{label} --notify without --since-last exited {alone.returncode}.")
            return 1
        first = patrol("--since-last", "--notify")
        if first.returncode != 0:
            report(f"{label} the first run exited {first.returncode}: {first.stdout!r} {first.stderr!r}")
            return 1
        if "baseline recorded" not in first.stdout:
            report(f"{label} the first run did not record a baseline: {first.stdout!r}")
            return 1
        if notices():
            report(f"{label} the baseline run sent a notice.")
            return 1
        readied = run_keel(verify, "shift", "ready", "verify note", env=env)
        if readied.returncode != 0:
            report(f"{label} verify's ready failed: {readied.stderr}")
            return 1
        for args in (["commit", "-q", "--allow-empty", "-m", "landed"], ["push", "-q", "origin", "HEAD"]):
            subprocess.run(["git", *args], cwd=rtl, check=True, capture_output=True)
        second = patrol("--since-last", "--notify")
        if second.returncode != 3:
            report(f"{label} the run after a change exited {second.returncode}: {second.stdout!r} {second.stderr!r}")
            return 1
        changed = [line for line in second.stdout.splitlines() if line.startswith("changed:")]
        if not any("shift" in line and "verify" in line for line in changed):
            report(f"{label} the shift status change is not reported: {second.stdout!r}")
            return 1
        if not any("remote" in line for line in changed):
            report(f"{label} the remote tip change is not reported: {second.stdout!r}")
            return 1
        # Shift-status and remote changes are not risks (#307 part 3): printed, not sent.
        if notices():
            report(f"{label} a run with no risk sent the coordinator a notice: {notices()!r}")
            return 1
        third = patrol("--since-last", "--notify")
        if third.returncode != 0:
            report(f"{label} an unchanged run exited {third.returncode}: {third.stdout!r}")
            return 1
        if "changed:" in third.stdout:
            report(f"{label} an unchanged run reported a change: {third.stdout!r}")
            return 1
        if notices():
            report(f"{label} an unchanged run sent a notice.")
            return 1
    report("patrol-since-last scenario passed.")
    return 0


def validate_patrol_exit_says_who_acts_scenario() -> int:
    """Issue #350: `keel patrol` exited 2 on pure state changes too.

    A coordinator's schedule wakes its model on exit 2, so a run that only
    moved state or told other roles cost a model turn for nothing. Exit 2 now
    means the coordinator has something to act on — a risk, or its own wait
    met — and exit 3 means patrol recorded or delivered something for others.
    """
    label = "patrol-exit-says-who-acts:"
    with tempfile.TemporaryDirectory(prefix="keel-patrol-350-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)

        def patrol(*args: str) -> subprocess.CompletedProcess[str]:
            return run_keel(rtl, "patrol", *args, env=env)

        def push() -> str:
            for args in (["commit", "-q", "--allow-empty", "-m", "landed"], ["push", "-q", "origin", "HEAD"]):
                subprocess.run(["git", *args], cwd=rtl, check=True, capture_output=True)
            return subprocess.run(["git", "rev-parse", "HEAD"], cwd=rtl, text=True, capture_output=True, check=True).stdout.strip()

        if patrol("--since-last", "--notify").returncode != 0:
            report(f"{label} the baseline run did not exit 0.")
            return 1
        push()
        moved = patrol("--since-last", "--notify")
        if moved.returncode != 3:
            report(f"{label} a run whose only news is the remote tip exited {moved.returncode}, not 3: {moved.stdout!r}")
            return 1
        (rtl / "stray.txt").write_text("x\n")
        risky = patrol("--since-last", "--notify")
        if risky.returncode != 2:
            report(f"{label} a run that found a risk exited {risky.returncode}, not 2: {risky.stdout!r}")
            return 1
        (rtl / "stray.txt").unlink()

        sha = push()
        run_keel(verify, "chat", "wait", "soc", "--commit", sha, "rerun when it lands", env=env)
        theirs = patrol()
        if theirs.returncode != 3:
            report(f"{label} a run that met another role's wait exited {theirs.returncode}, not 3: {theirs.stdout!r}")
            return 1
        sha = push()
        run_keel(rtl, "chat", "wait", "soc", "--commit", sha, "merge the next slice", env=env)
        mine = patrol()
        if mine.returncode != 2:
            report(f"{label} a run that met the coordinator's own wait exited {mine.returncode}, not 2: {mine.stdout!r}")
            return 1
        helped = run_keel(rtl, "patrol", "--help", env=env)
        if "3:" not in helped.stdout:
            report(f"{label} --help does not document exit 3: {helped.stdout!r}")
            return 1
    if "patrol-exit-says-who-acts" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("patrol-exit-says-who-acts scenario passed.")
    return 0


def validate_patrol_next_scenario() -> int:
    """Issue #356: a patrol recommends when to run next.

    With `cadence: adaptive` the first matching rule picks the delay — risk,
    quota, night, busy, idle — and each case has a failing arm: the same
    fixture without its condition gives another rule. A fixed `every:` keeps
    today's cadence.
    """
    label = "patrol-next:"
    with tempfile.TemporaryDirectory(prefix="keel-patrol-356-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)

        def config(extra: str) -> None:
            write_authorize_config(rtl, "patrol:\n  role: rtl\n  every: 60m\n" + extra)

        def patrol(*args: str) -> dict:
            result = run_keel(rtl, "patrol", "--json", *args, env=env)
            return json.loads(result.stdout) if result.stdout.strip().startswith("{") else {"raw": result.stdout + result.stderr}

        def expect(name: str, payload: dict, rule: str, seconds: int | None) -> bool:
            if payload.get("next_rule") != rule:
                report(f"{label} {name}: next_rule {payload.get('next_rule')!r}, not {rule!r}: {payload!r}")
                return False
            if seconds is not None and payload.get("next_after_s") != seconds:
                report(f"{label} {name}: next_after_s {payload.get('next_after_s')!r}, not {seconds}")
                return False
            return True

        config("")
        if not expect("fixed", patrol(), "fixed", 3600):
            return 1
        config("  cadence: adaptive\n")
        if not expect("idle", patrol(), "idle", 3 * 3600):
            return 1
        subprocess.run(["node", str(ROOT / "bin" / "keel.js"), "chat", "hook", "session-start"], cwd=verify, env=env,
                       text=True, capture_output=True, check=False,
                       input=json.dumps({"cwd": str(verify), "hook_event_name": "SessionStart", "session_id": "v1", "source": "startup"}))
        if not expect("busy", patrol(), "busy", 3600):
            return 1
        patrol("--quota", "92")
        if not expect("quota", patrol("--quota", "92"), "quota", 4 * 3600):
            return 1
        # The risk is a clean checkout turning dirty, so the config is committed first.
        subprocess.run(["git", "add", "-A"], cwd=rtl, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", "cadence"], cwd=rtl, check=True, capture_output=True)
        patrol("--since-last")
        (rtl / "stray.txt").write_text("x\n")
        if not expect("risk", patrol("--since-last"), "risk", 30 * 60):
            return 1
        (rtl / "stray.txt").unlink()
        patrol("--since-last")
        now = datetime.now()
        start = (now - timedelta(minutes=30)).strftime("%H:%M")
        end_at = now + timedelta(minutes=90)
        config(f"  cadence: adaptive\n  idle: 2h\n  quiet: {start}-{end_at.strftime('%H:%M')}\n")
        night = patrol()
        if not expect("night", night, "night", None):
            return 1
        if not 80 * 60 <= night.get("next_after_s", 0) <= 91 * 60:
            report(f"{label} night: next_after_s {night.get('next_after_s')} does not end at the window's end.")
            return 1
        config("  cadence: adaptive\n  busy: 45m\n  min: 50m\n")
        if not expect("busy clamped to min", patrol(), "busy", 50 * 60):
            return 1
        text = run_keel(rtl, "patrol", env=env).stdout
        if not re.search(r"^next: 50m \(busy\)$", text, re.M):
            report(f"{label} the text output has no `next: 50m (busy)` line: {text!r}")
            return 1
        log = (mailbox_common_dir(rtl) / "keel-chat" / "patrol" / "log" / "rtl.log").read_text(encoding="utf-8").splitlines()
        if not log[-1].endswith("next=50m (busy)"):
            report(f"{label} the run log does not record the next run: {log[-1]!r}")
            return 1
    if "patrol-next" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("patrol-next scenario passed.")
    return 0


def validate_launchd_stable_node_scenario() -> int:
    """Issue #387: a launchd job must name a node that outlives `brew upgrade`.

    `keel tick task` printed `process.execPath`, Homebrew's versioned Cellar
    path, which is gone after an upgrade; launchd then fails silently every
    interval. The jobs now name the `node` on PATH that is the same binary (the
    symlink the package manager keeps current), leave plugin cache directories
    out of PATH, and `keel --doctor` reports a job whose node no longer exists.
    """
    label = "launchd-stable-node:"
    with tempfile.TemporaryDirectory(prefix="keel-launchd-387-") as raw:
        base = Path(raw)
        rtl, cx, env, _ = chat_wake_scratch(base)
        real = os.path.realpath(shutil.which("node") or "node")
        versioned = base / "cellar" / "node" / "9.9.9" / "bin"
        versioned.mkdir(parents=True)
        (versioned / "node").symlink_to(real)
        stable = base / "bin"
        stable.mkdir()
        (stable / "node").symlink_to(versioned / "node")
        cache = base / "home" / ".claude" / "plugins" / "cache" / "keel-marketplace" / "keel" / "5.149.0" / "bin"
        cache.mkdir(parents=True)
        path = os.pathsep.join([str(cache), str(stable), os.environ.get("PATH", "")])
        env = {**env, "PATH": path}
        write_text(rtl / "openspec/specs/.keep", "")
        write_authorize_config(rtl, "patrol:\n  role: rtl\n  every: 60m\n  runner: tick\n")
        subprocess.run(["git", "add", "-A"], cwd=rtl, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", "tick"], cwd=rtl, check=True, capture_output=True)

        def keel(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run([str(stable / "node"), str(ROOT / "bin" / "keel.js"), *args], cwd=cwd, env=env,
                                  text=True, capture_output=True, check=False)

        def program(plist: str) -> str:
            return (re.search(r"<key>ProgramArguments</key>\s*<array>\s*<string>(.*?)</string>", plist, re.S) or [None, ""])[1]

        def path_of(plist: str) -> str:
            return (re.search(r"<key>PATH</key>\s*<string>(.*?)</string>", plist, re.S) or [None, ""])[1]

        task = keel(rtl, "tick", "task")
        if task.returncode != 0:
            report(f"{label} keel tick task failed: {task.stderr!r}")
            return 1
        if program(task.stdout) != str(stable / "node"):
            report(f"{label} the tick job names the versioned node: {program(task.stdout)!r}, not {str(stable / 'node')!r}")
            return 1
        if str(stable) not in path_of(task.stdout).split(os.pathsep) or "plugins/cache" in path_of(task.stdout):
            report(f"{label} the tick job's PATH is not the stable directories without the plugin cache: {path_of(task.stdout)!r}")
            return 1

        added = keel(cx, "chat", "wake", "add")
        plists = sorted((base / "agents").glob("dev.keel.chat-wake.*.plist"))
        if added.returncode != 0 or len(plists) != 1:
            report(f"{label} keel chat wake add wrote {len(plists)} LaunchAgents: {(added.stdout + added.stderr).strip()!r}")
            return 1
        waker = plists[0].read_text(encoding="utf-8")
        if program(waker) != str(stable / "node"):
            report(f"{label} the chat waker's LaunchAgent names the versioned node: {program(waker)!r}")
            return 1
        if "plugins/cache" in path_of(waker):
            report(f"{label} the chat waker's LaunchAgent keeps a plugin cache directory in PATH: {path_of(waker)!r}")
            return 1

        gone = base / "Cellar" / "node" / "0.0.0" / "bin" / "node"
        broken = base / "agents" / "dev.keel.tick.x.plist"
        broken.write_text(task.stdout[task.stdout.index("<?xml"):task.stdout.index("</plist>") + 8].replace(str(stable / "node"), str(gone)), encoding="utf-8")
        problem = keel(rtl, "--doctor")
        line = next((l for l in problem.stdout.splitlines() if l.startswith("launchd: problem")), "")
        for needle in ("dev.keel.tick.x.plist", str(gone), "keel tick task"):
            if needle not in line:
                report(f"{label} doctor does not name {needle!r} for a job whose node is gone: {problem.stdout!r}")
                return 1
        broken.write_text(broken.read_text(encoding="utf-8").replace(str(gone), str(stable / "node")), encoding="utf-8")
        fine = keel(rtl, "--doctor")
        if "launchd: ok" not in fine.stdout or "launchd: problem" in fine.stdout:
            report(f"{label} doctor does not report ok once the node exists: {fine.stdout!r}")
            return 1
    if "launchd-stable-node" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("launchd-stable-node scenario passed.")
    return 0


def validate_shift_slash_command_scenario() -> int:
    """Issue #386: a session changes its own shift with one slash command.

    `/keel:shift` is a command file in the Claude plugin that orders what a
    session does: check, settle each loose end (a keep-awake the host started,
    such as `caffeinate`, is not one), write the note, `ready --wake`. The
    scenario finds it through the root manifest and runs its own fenced `keel
    shift` lines in a clean worktree bound to a role, so a flag `keel` no
    longer accepts, or a heredoc that stores nothing, fails it.
    """
    label = "shift-slash-command:"
    manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    declared = manifest.get("commands") or []
    if not declared:
        report(f"{label} the root manifest declares no command")
        return 1
    files = [ROOT / entry for entry in declared if (ROOT / entry).name == "shift.md"]
    if len(files) != 1 or not files[0].is_file():
        report(f"{label} the root manifest's commands {declared!r} do not resolve to one plugins/keel/commands/shift.md")
        return 1
    if files[0].relative_to(ROOT).parts[:3] != ("plugins", "keel", "commands"):
        report(f"{label} the command is not under plugins/keel/commands: {files[0]}")
        return 1
    text = files[0].read_text(encoding="utf-8")
    front = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not front or not re.search(r"^description: \S", front.group(1), re.M):
        report(f"{label} the command has no front matter with a description.")
        return 1
    for needle in ("caffeinate", "--force-reason", "self-shift", "end your turn"):
        if needle not in text:
            report(f"{label} the command does not say {needle!r}.")
            return 1
    blocks = re.findall(r"```bash\n(.*?)```", text, re.S)
    lines = [b for b in blocks if b.lstrip().startswith("keel shift")]
    if [b.split()[2] for b in lines] != ["check", "ready"]:
        report(f"{label} the command's keel shift blocks are not check, then ready: {[b.split()[:3] for b in lines]!r}")
        return 1
    with tempfile.TemporaryDirectory(prefix="keel-shift-386-") as raw:
        base = Path(raw)
        _rtl, verify, env, _ = shift_scratch(base)
        shim = base / "shim"
        write_text(shim / "keel", f'#!/bin/sh\nexec node "{ROOT / "bin" / "keel.js"}" "$@"\n')
        (shim / "keel").chmod(0o755)
        env = {**env, "PATH": f"{shim}{os.pathsep}{os.environ.get('PATH', '')}", "KEEL_SHIFT_WAKE_TIMEOUT_MS": "2000"}
        checked = subprocess.run(["sh", "-c", lines[0]], cwd=verify, env=env, text=True, capture_output=True, check=False)
        if checked.returncode != 0:
            report(f"{label} the command's check line exited {checked.returncode} in a clean worktree: {checked.stdout!r} {checked.stderr!r}")
            return 1
        handed = subprocess.run(["sh", "-c", lines[1]], cwd=verify, env=env, text=True, capture_output=True, check=False)
        if handed.returncode != 0:
            report(f"{label} the command's ready line exited {handed.returncode}: {handed.stdout!r} {handed.stderr!r}")
            return 1
        body = re.search(r"<<'EOF'\n(.*?)\nEOF", lines[1], re.S)
        stored = mailbox_common_dir(verify) / "keel-chat" / "shift" / "verify.md"
        if not body:
            report(f"{label} the command's ready line carries no quoted heredoc: {lines[1]!r}")
            return 1
        if not stored.exists():
            report(f"{label} the command's ready line stored no note at {stored}: {handed.stdout!r}")
            return 1
        if body.group(1).strip() not in stored.read_text(encoding="utf-8"):
            report(f"{label} the stored note is not the heredoc's: {stored.read_text(encoding='utf-8')!r}")
            return 1
        if "wake is armed" not in handed.stdout:
            report(f"{label} the command's ready line did not arm the wake: {handed.stdout!r}")
            return 1
    if "shift-slash-command" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("shift-slash-command scenario passed.")
    return 0


def validate_tick_runs_due_patrol_scenario() -> int:
    """The owner's CLI waker (2026-10-19, #356): `keel tick` runs the patrol when due.

    A host scheduler (launchd) calls `keel tick` every few minutes; each call
    is one model-free step. It fetches and patrols only once the last run's
    recommended `next_at` has passed, records the next one, and otherwise exits
    quietly. `keel tick task` prints the launchd job and creates nothing.
    """
    label = "tick-runs-due-patrol:"
    with tempfile.TemporaryDirectory(prefix="keel-tick-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)
        write_text(rtl / "openspec/specs/.keep", "")
        write_authorize_config(rtl, "patrol:\n  role: rtl\n  every: 60m\n  runner: tick\n  cadence: adaptive\n")
        subprocess.run(["git", "add", "-A"], cwd=rtl, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", "tick"], cwd=rtl, check=True, capture_output=True)
        store_root = mailbox_common_dir(rtl) / "keel-chat"
        log = store_root / "patrol" / "log" / "rtl.log"
        state = store_root / "tick" / "state.json"

        def tick(*args: str) -> subprocess.CompletedProcess[str]:
            return run_keel(verify, "tick", "--repo", str(rtl), *args, env=env)

        def runs() -> int:
            return len(log.read_text(encoding="utf-8").splitlines()) if log.exists() else 0

        first = tick()
        if first.returncode != 0:
            report(f"{label} the first tick exited {first.returncode}: {first.stdout!r} {first.stderr!r}")
            return 1
        if runs() != 1:
            report(f"{label} the first tick did not run the patrol once: {runs()} log lines; {first.stdout!r}")
            return 1
        saved = json.loads(state.read_text(encoding="utf-8")) if state.exists() else {}
        if not saved.get("patrol", {}).get("next_at"):
            report(f"{label} the tick did not record the next patrol: {saved!r}")
            return 1
        second = tick()
        if second.returncode != 0 or runs() != 1:
            report(f"{label} a tick before next_at ran the patrol: {runs()} log lines; {second.stdout!r}")
            return 1
        if "not due" not in second.stdout:
            report(f"{label} a skipped tick does not say the patrol is not due: {second.stdout!r}")
            return 1
        saved["patrol"]["next_at"] = "2000-01-01T00:00:00+00:00"
        state.write_text(json.dumps(saved), encoding="utf-8")
        tick()
        if runs() != 2:
            report(f"{label} a tick after next_at did not run the patrol: {runs()} log lines.")
            return 1

        rendered = run_keel(rtl, "tick", "task", env=env)
        if rendered.returncode != 0:
            report(f"{label} keel tick task failed: {rendered.stderr!r}")
            return 1
        for needle in ("<key>Label</key>", "<key>StartInterval</key>", "<integer>300</integer>", "<string>tick</string>",
                       f"<string>{os.path.realpath(rtl)}</string>", "launchctl bootstrap", "Keel creates nothing"):
            if needle not in rendered.stdout:
                report(f"{label} keel tick task does not carry {needle!r}: {rendered.stdout!r}")
                return 1
        if list((base / "home").glob("**/*.plist")) if (base / "home").exists() else []:
            report(f"{label} keel tick task wrote a plist.")
            return 1

        context = json.loads(run_keel(rtl, "context", "--json", env=env).stdout)
        if (context.get("patrol") or {}).get("runner") != "tick":
            report(f"{label} the coordinator's context does not carry runner tick: {context.get('patrol')!r}")
            return 1
        session = run_session_start_hook(
            rtl, {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(rtl)},
            keel_cli=f'node "{ROOT / "bin" / "keel.js"}"',
        )
        reminder = session_start_context(session) or ""
        if "re-create it with the host" in reminder:
            report(f"{label} with runner: tick the coordinator is still told to re-create a session schedule: {reminder!r}")
            return 1
        if "keel tick" not in reminder:
            report(f"{label} with runner: tick the projection does not name keel tick: {reminder!r}")
            return 1
    if "tick-runs-due-patrol" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("tick-runs-due-patrol scenario passed.")
    return 0


def validate_patrol_nudge_scenario() -> int:
    """Issues #307 part 1 and #313: the patrol nudges idle roles directly.

    Addressed unread records nudge once per window; a closed todo nudges a
    shift change at that task boundary, naming `--wake` only while another
    todo is open; a self-initiated note nudges a resume; a parked note and
    the patrol's own messages never do; context is no longer an input.
    """
    label = "patrol-nudge:"
    with tempfile.TemporaryDirectory(prefix="keel-patrol-nudge-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)
        env = {**env, "KEEL_SHIFT_WAKE_TIMEOUT_MS": "1"}
        lint = chat_worktree(rtl, base / "lint")
        subprocess.run(["git", "push", "-q", "-u", "origin", "HEAD"], cwd=lint, check=True, capture_output=True)
        run_keel(lint, "chat", "role", "--set", "lint", env=env)
        run_keel(rtl, "chat", "group", "add", "soc", "lint", env=env)
        todo_ids = []
        for text in ("R009 timing fix", "R010 lint cleanup"):
            made = run_keel(rtl, "chat", "todo", "soc", "--assignee", "lint", text, "--json", env=env)
            todo_ids.append(json.loads(made.stdout)["id"])
        run_keel(lint, "chat", "read", env=env)
        run_keel(rtl, "chat", "post", "soc", "@verify please rerun R007", env=env)
        time.sleep(1.2)

        def nudge(*args: str) -> subprocess.CompletedProcess[str]:
            return run_keel(rtl, "patrol", "--nudge", "--idle", "1s", *args, env=env)

        def nudged(result: subprocess.CompletedProcess[str]) -> list[str]:
            return [line for line in result.stdout.splitlines() if line.startswith("nudged ")]

        def told_lint(needle: str) -> str:
            return "\n".join(chat_records_with(rtl, "dm-keel-patrol--lint", needle))

        seen: list[str] = []
        first = nudge()
        seen += nudged(first)
        if "nudged verify: unread" not in nudged(first):
            report(f"{label} verify was not nudged for unread: {first.stdout!r} {first.stderr!r}")
            return 1
        if any(line.startswith("nudged lint") for line in nudged(first)):
            report(f"{label} lint was nudged before any task closed: {nudged(first)!r}")
            return 1
        if first.returncode != 3:
            report(f"{label} a run that nudged exited {first.returncode}, not 3.")
            return 1
        if run_keel(verify, "chat", "notice", "--check", env=env).returncode != 0:
            report(f"{label} the nudge does not wake verify.")
            return 1
        run_keel(lint, "chat", "done", todo_ids[0], env=env)
        time.sleep(1.2)
        second = nudge()
        seen += nudged(second)
        if nudged(second) != ["nudged lint: shift"]:
            report(f"{label} closing a todo should nudge only lint's shift: {second.stdout!r} {second.stderr!r}")
            return 1
        if "keel shift ready --wake" not in told_lint("R009"):
            report(f"{label} with a todo still open, the shift nudge does not name ready --wake: {told_lint('R009')!r}")
            return 1
        if "Remote Control" not in told_lint("R009"):
            report(f"{label} the shift nudge does not name Remote Control.")
            return 1
        time.sleep(1.2)
        third = nudge()
        seen += nudged(third)
        if nudged(third):
            report(f"{label} a run with nothing new nudged: {nudged(third)!r}")
            return 1
        if third.returncode != 0:
            report(f"{label} a run that nudged nobody exited {third.returncode}.")
            return 1
        run_keel(lint, "chat", "done", todo_ids[1], env=env)
        time.sleep(1.2)
        fourth = nudge()
        seen += nudged(fourth)
        if "nudged lint: shift" not in nudged(fourth):
            report(f"{label} closing the last todo did not nudge lint: {fourth.stdout!r}")
            return 1
        last = told_lint("R010")
        if "wait for the coordinator" not in last:
            report(f"{label} with no todo left, the shift nudge does not say to wait for the coordinator: {last!r}")
            return 1
        if "--wake" in last:
            report(f"{label} with no todo left, the shift nudge still names --wake: {last!r}")
            return 1
        armed = run_keel(lint, "shift", "ready", "--wake", "lint note", env=env)
        if armed.returncode != 0:
            report(f"{label} lint's ready --wake failed: {armed.stderr}")
            return 1
        if run_keel(verify, "shift", "ready", "--force-reason", "parked by the coordinator", "verify parked", env=env).returncode != 0:
            report(f"{label} verify's ready failed.")
            return 1
        time.sleep(1.2)
        fifth = nudge()
        seen += nudged(fifth)
        if "nudged lint: resume" not in nudged(fifth):
            report(f"{label} lint's self-initiated note was not nudged to resume: {fifth.stdout!r}")
            return 1
        if "nudged verify: resume" in nudged(fifth):
            report(f"{label} verify's parked note was nudged to resume.")
            return 1
        if "nudged lint: unread" in seen:
            report(f"{label} lint was nudged over the patrol's own message.")
            return 1
        retired = nudge("--context", "lint=62")
        if retired.returncode != 1:
            report(f"{label} --context exited {retired.returncode}.")
            return 1
        if "retired" not in retired.stderr:
            report(f"{label} the --context refusal does not say it was retired: {retired.stderr!r}")
            return 1
    report("patrol-nudge scenario passed.")
    return 0


def validate_patrol_escalate_scenario() -> int:
    """Issue #307 part 3: only risks reach the coordinator; every run is logged."""
    label = "patrol-escalate:"
    with tempfile.TemporaryDirectory(prefix="keel-patrol-escalate-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)
        env = {**env, "KEEL_PATROL_UNREAD_EVERY_MS": "1"}
        runs = 0

        def patrol(*args: str) -> subprocess.CompletedProcess[str]:
            nonlocal runs
            runs += 1
            return run_keel(rtl, "patrol", "--since-last", "--notify", "--idle", "1s", *args, env=env)

        def sent(needle: str) -> int:
            return len(chat_records_with(rtl, "dm-keel-patrol--rtl", needle))

        patrol()
        write_text(rtl / "dirty.txt", "left behind\n")
        dirty = patrol()
        if sent("uncommitted") != 1:
            report(f"{label} the dirty checkout was not sent once: {dirty.stdout!r} {dirty.stderr!r}")
            return 1
        if not any(line.startswith("risk:") for line in dirty.stdout.splitlines()):
            report(f"{label} the risk is not printed: {dirty.stdout!r}")
            return 1
        patrol("--disk-free-gb", "12")
        if sent("free disk is 12 GB") != 1:
            report(f"{label} low disk was not sent once.")
            return 1
        patrol("--disk-free-gb", "12")
        if sent("free disk") != 1:
            report(f"{label} low disk was sent again without changing.")
            return 1
        if sent("uncommitted") != 1:
            report(f"{label} the still-dirty checkout was sent again.")
            return 1
        run_keel(rtl, "chat", "post", "soc", "@verify rerun R007 please", env=env)
        time.sleep(1.2)
        patrol("--nudge")
        time.sleep(0.2)
        second = patrol("--nudge")
        if sent("2 nudges") != 1:
            report(f"{label} two unanswered nudges were not escalated once: {second.stdout!r}")
            return 1
        if "verify" not in "\n".join(chat_records_with(rtl, "dm-keel-patrol--rtl", "2 nudges")):
            report(f"{label} the escalation does not name verify.")
            return 1
        log = mailbox_common_dir(rtl) / "keel-chat" / "patrol" / "log" / "rtl.log"
        lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        if len(lines) != runs:
            report(f"{label} the run log holds {len(lines)} lines for {runs} runs.")
            return 1
        if not all("exit=" in line and "risks=" in line for line in lines):
            report(f"{label} a run log line lacks exit= or risks=: {lines!r}")
            return 1
    report("patrol-escalate scenario passed.")
    return 0


def validate_patrol_quota_scenario() -> int:
    """Issue #307 part 2: quota thresholds once per period; nudges pause near the limit."""
    label = "patrol-quota:"
    with tempfile.TemporaryDirectory(prefix="keel-patrol-quota-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)
        env = {**env, "KEEL_PATROL_UNREAD_EVERY_MS": "1"}
        run_keel(rtl, "chat", "post", "soc", "@verify rerun R007 please", env=env)
        time.sleep(1.2)

        def patrol(quota: str) -> subprocess.CompletedProcess[str]:
            return run_keel(rtl, "patrol", "--since-last", "--notify", "--nudge", "--idle", "1s", "--quota", quota, env=env)

        expected = {"50": None, "91": "past 90%", "93": None, "96": "past 95%", "10": None, "92": "past 90%"}
        for quota, want in expected.items():
            result = patrol(quota)
            lines = [line for line in result.stdout.splitlines() if line.startswith("risk: weekly quota")]
            if want is None and lines:
                report(f"{label} quota {quota} reported {lines!r}.")
                return 1
            if want is not None and len(lines) != 1:
                report(f"{label} quota {quota} should report one quota line: {result.stdout!r} {result.stderr!r}")
                return 1
            if want is not None and want not in lines[0]:
                report(f"{label} quota {quota} should report {want!r}: {lines[0]!r}")
                return 1
            if quota == "50" and "nudged verify: unread" not in result.stdout:
                report(f"{label} verify was not nudged at 50%: {result.stdout!r}")
                return 1
            if quota == "91" and "nudged verify" in result.stdout:
                report(f"{label} verify was nudged at 91%: {result.stdout!r}")
                return 1
            if quota == "91" and "nudges paused: quota at 91%" not in result.stdout:
                report(f"{label} the pause is not said at 91%: {result.stdout!r}")
                return 1
        sent = chat_records_with(rtl, "dm-keel-patrol--rtl", "weekly quota")
        if len(sent) != 3:
            report(f"{label} expected three quota messages to rtl, found {len(sent)}.")
            return 1
        refused = run_keel(rtl, "patrol", "--quota", "120", env=env)
        if refused.returncode != 1:
            report(f"{label} --quota 120 exited {refused.returncode}.")
            return 1
    report("patrol-quota scenario passed.")
    return 0


def validate_coordinator_patrol_scenario() -> int:
    """Issue #260: declared waits, and a patrol that notifies once.

    `keel chat wait` records what a role waits for; `keel patrol` marks a held
    condition met and direct-messages the waiter, writes nothing when nothing
    holds, and exits 0 (quiet), 2 (wrote), or 1 (error).
    """
    label = "coordinator-patrol:"
    with tempfile.TemporaryDirectory(prefix="keel-patrol-") as raw:
        base = Path(raw)
        rtl, verify, env = chat_scratch_group(base)
        origin = base / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True, capture_output=True)
        for args in (["remote", "add", "origin", str(origin)], ["push", "-q", "origin", "main"],
                     ["switch", "-q", "-c", "feature"], ["commit", "-q", "--allow-empty", "-m", "fix"]):
            subprocess.run(["git", *args], cwd=rtl, check=True, capture_output=True)
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=rtl, check=True, capture_output=True, text=True).stdout.strip()

        def chat(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
            return run_keel(cwd, "chat", *args, env=env)

        def patrol(*args: str) -> subprocess.CompletedProcess[str]:
            return run_keel(rtl, "patrol", *args, env=env)

        waited = chat(verify, "wait", "soc", "--commit", sha, "rerun R007 when the fix lands")
        if waited.returncode != 0:
            report(f"{label} keel chat wait failed: {waited.stdout} {waited.stderr}")
            return 1
        waits = chat_json(chat(rtl, "waits", "--json")).get("waits", [])
        if [(w.get("from"), w.get("condition")) for w in waits] != [("verify", f"commit {sha} on origin")]:
            report(f"{label} waits lists {waits!r}.")
            return 1
        if chat_json(chat(rtl, "unread", "--json")).get("unread"):
            report(f"{label} a wait left rtl something unread.")
            return 1
        for what, result in (
            ("no condition", chat(verify, "wait", "soc")),
            ("both conditions", chat(verify, "wait", "soc", "--commit", sha, "--issue", "42", "--closed")),
        ):
            if result.returncode == 0:
                report(f"{label} a wait with {what} was accepted.")
                return 1
            if "--commit" not in result.stderr or "--issue" not in result.stderr:
                report(f"{label} a wait with {what} was refused without naming both forms: {result.stderr}")
                return 1

        before = chat_logs_snapshot(rtl)
        quiet = patrol()
        if quiet.returncode != 0:
            report(f"{label} patrol before the push exited {quiet.returncode}: {quiet.stdout} {quiet.stderr}")
            return 1
        if chat_logs_snapshot(rtl) != before:
            report(f"{label} a quiet patrol wrote to the chat.")
            return 1
        if "verify" not in quiet.stdout:
            report(f"{label} the digest does not list verify: {quiet.stdout!r}")
            return 1

        subprocess.run(["git", "push", "-q", "origin", "feature"], cwd=rtl, check=True, capture_output=True)
        landed = patrol()
        if landed.returncode != 3:
            report(f"{label} patrol after the push exited {landed.returncode}, not 3: {landed.stdout} {landed.stderr}")
            return 1
        if chat_json(chat(rtl, "waits", "--json")).get("waits"):
            report(f"{label} the met wait is still listed.")
            return 1
        texts = [r.get("text", "") for r in chat_json(chat(verify, "unread", "--json")).get("unread", [])]
        if not any(sha[:7] in text for text in texts):
            report(f"{label} verify has no unread message naming the commit: {texts!r}")
            return 1
        before = chat_logs_snapshot(rtl)
        again = patrol()
        if again.returncode != 0:
            report(f"{label} a second patrol exited {again.returncode}, not 0.")
            return 1
        if chat_logs_snapshot(rtl) != before:
            report(f"{label} a second patrol wrote again.")
            return 1

        chat(verify, "wait", "soc", "--issue", "42", "--closed")
        unchecked = patrol()
        if unchecked.returncode != 0:
            report(f"{label} patrol without --issues exited {unchecked.returncode}, not 0.")
            return 1
        if "unchecked" not in unchecked.stdout:
            report(f"{label} patrol without --issues does not report the issue wait unchecked: {unchecked.stdout!r}")
            return 1
        issues = base / "issues.json"
        issues.write_text(json.dumps([{"number": 42, "title": "clock fix", "state": "CLOSED", "labels": [], "updatedAt": "2026-10-11T00:00:00Z"}]), encoding="utf-8")
        closed = patrol("--issues", str(issues))
        if closed.returncode != 3:
            report(f"{label} patrol with issue 42 closed exited {closed.returncode}, not 3: {closed.stdout} {closed.stderr}")
            return 1
    report("coordinator-patrol scenario passed.")
    return 0


def validate_patrol_issue_routing_scenario() -> int:
    """Issue #242: `issue_roles:` routes each labelled issue update once.

    The label's role gets one direct message per `updatedAt`, deduped against
    the chat; an unreadable line is reported and routes nothing.
    """
    label = "patrol-issue-routing:"
    with tempfile.TemporaryDirectory(prefix="keel-patrol-issues-") as raw:
        base = Path(raw)
        rtl, verify, env = chat_scratch_group(base)
        write_authorize_config(rtl, "issue_roles:\n  role:verify: verify\n  this line has no role\n")
        issues = base / "issues.json"

        def patrol(updated: str) -> subprocess.CompletedProcess[str]:
            issues.write_text(json.dumps([{
                "number": 157, "title": "rerun on new commit", "state": "OPEN",
                "labels": [{"name": "role:verify"}], "updatedAt": updated,
            }]), encoding="utf-8")
            return run_keel(rtl, "patrol", "--issues", str(issues), env=env)

        def notices() -> list:
            return [r.get("text", "") for r in chat_json(run_keel(verify, "chat", "unread", "--json", env=env)).get("unread", []) if "#157" in r.get("text", "")]

        first = patrol("2026-10-11T01:00:00Z")
        if first.returncode != 3:
            report(f"{label} the first patrol exited {first.returncode}, not 3: {first.stdout} {first.stderr}")
            return 1
        if len(notices()) != 1:
            report(f"{label} verify has {len(notices())} notices about #157, not 1.")
            return 1
        if "this line has no role" not in first.stdout:
            report(f"{label} the unreadable issue_roles line is not reported: {first.stdout!r}")
            return 1
        before = chat_logs_snapshot(rtl)
        same = patrol("2026-10-11T01:00:00Z")
        if same.returncode != 0:
            report(f"{label} the same update exited {same.returncode}, not 0.")
            return 1
        if chat_logs_snapshot(rtl) != before:
            report(f"{label} the same update was sent again.")
            return 1
        later = patrol("2026-10-11T02:00:00Z")
        if later.returncode != 3:
            report(f"{label} a later update exited {later.returncode}, not 3.")
            return 1
        if len(notices()) != 2:
            report(f"{label} a later update left {len(notices())} notices, not 2.")
            return 1
    report("patrol-issue-routing scenario passed.")
    return 0


def validate_worktree_overview_scenario() -> int:
    """Read every worktree through the CLI without fetching or changing chat."""
    label = "worktree-overview:"
    with tempfile.TemporaryDirectory(prefix="keel-worktree-overview-") as raw:
        base = Path(raw).resolve()
        repo, remote = base / "repo", base / "remote.git"
        repo.mkdir()
        env = os.environ.copy()
        env.pop("KEEL_CHAT_ROLE", None)
        env.pop("KEEL_MAIL_ROLE", None)

        def git(*args: str, cwd: Path = repo) -> str:
            return subprocess.run(
                ["git", *args], cwd=cwd, env=env, check=True,
                capture_output=True, text=True,
            ).stdout.strip()

        git("init", "-q", "-b", "main")
        git("config", "user.email", "test@example.invalid")
        git("config", "user.name", "Worktree test")
        (repo / "seed").write_text("base\n", encoding="utf-8")
        git("add", "seed")
        git("commit", "-qm", "base #99")
        git("init", "--bare", "-q", str(remote))
        git("remote", "add", "origin", str(remote))
        git("push", "-qu", "origin", "main")
        git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
        a, b, gone = base / "a", base / "b", base / "gone"
        git("worktree", "add", "-qb", "feature", str(a), "main")
        git("branch", "--set-upstream-to=origin/main", "feature")
        (a / "feature").write_text("feature\n", encoding="utf-8")
        git("add", "feature", cwd=a)
        git("commit", "-qm", "feature #12", "-m", "References #12 again", cwd=a)
        git("worktree", "add", "-q", "--detach", str(b), "main")
        (b / "uncommitted").write_text("dirty\n", encoding="utf-8")
        git("worktree", "add", "-q", "--detach", str(gone), "main")
        git("worktree", "lock", "--reason", "test lock", str(a))
        shutil.rmtree(gone)
        bound = run_keel(a, "chat", "role", "--set", "pm", env=env)
        if bound.returncode != 0:
            report(f"{label} could not bind pm: {bound.stderr}")
            return 1
        chat = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir")) / "keel-chat"
        stamp = datetime.now(timezone.utc).isoformat()
        write_text(chat / "presence" / "pm.json", json.dumps({"state": "online", "last_active": stamp}))

        def snapshot() -> dict[str, bytes]:
            return {str(file.relative_to(chat)): file.read_bytes()
                    for file in chat.rglob("*") if file.is_file()}

        before = snapshot()
        repository_before = {str(file.relative_to(repo)): file.read_bytes()
                             for file in repo.rglob("*") if file.is_file()}

        def overview(*args: str) -> subprocess.CompletedProcess[str]:
            # An override for the invoking session must not bind every worktree.
            return run_keel(b, "worktrees", "--repo", str(repo), *args,
                            env={**env, "KEEL_CHAT_ROLE": "caller"})

        result = overview("--json")
        if result.returncode != 0:
            report(f"{label} --json failed: {result.stderr}")
            return 1
        try:
            payload = json.loads(result.stdout)
            rows = {row["path"]: row for row in payload["worktrees"]}
        except (ValueError, KeyError, TypeError):
            report(f"{label} --json lacks worktree data: {result.stdout}")
            return 1
        if set(rows) != {str(repo), str(a), str(b), str(gone)}:
            report(f"{label} did not list every worktree: {rows}")
            return 1
        for tree, expected in (
            (a, {"branch": "feature", "ahead": 1, "behind": 0, "issues": [12],
                 "role": "pm", "upstream": "origin/main", "dirty": 0,
                 "locked": "test lock", "prunable": None}),
            (b, {"branch": None, "dirty": 1, "role": None, "presence": None,
                 "ahead": None, "behind": None, "upstream": None, "issues": []}),
            (gone, {"missing": True}),
        ):
            for key, value in expected.items():
                if rows[str(tree)].get(key) != value:
                    report(f"{label} {tree.name}'s {key} differs: {rows[str(tree)]}")
                    return 1
        if rows[str(a)].get("presence") != {"state": "online", "last_active": stamp}:
            report(f"{label} a's presence differs: {rows[str(a)]}")
            return 1
        for tree in (repo, a, b):
            row = rows[str(tree)]
            if row.get("head") != git("rev-parse", "--short", "HEAD", cwd=tree):
                report(f"{label} {tree.name}'s short head differs: {row}")
                return 1
            expected_commit = {"subject": git("log", "-1", "--format=%s", cwd=tree),
                               "time": git("log", "-1", "--format=%cI", cwd=tree)}
            if row.get("lastCommit") != expected_commit:
                report(f"{label} {tree.name}'s last commit differs: {row}")
                return 1
        if not rows[str(gone)].get("prunable"):
            report(f"{label} missing worktree lacks Git's prunable marker: {rows[str(gone)]}")
            return 1
        text = overview()
        if text.returncode != 0:
            report(f"{label} text output failed: {text.stderr}")
            return 1
        for needle in ("main", "as of the last fetch", str(a), str(b), str(gone), "missing"):
            if needle not in text.stdout:
                report(f"{label} text output lacks {needle!r}: {text.stdout}")
                return 1
        issues = base / "issues.json"
        updated = "2026-10-05T08:00:00Z"
        write_text(issues, json.dumps([{"number": 12, "updatedAt": updated}]))
        timed = overview("--issues", str(issues), "--json")
        if timed.returncode != 0:
            report(f"{label} passed issues file failed: {timed.stderr}")
            return 1
        timed_rows = {row["path"]: row for row in json.loads(timed.stdout)["worktrees"]}
        if timed_rows[str(a)].get("issueUpdates") != [{"number": 12, "updatedAt": updated}]:
            report(f"{label} issue 12 does not carry the passed updatedAt: {timed.stdout}")
            return 1
        timed_text = overview("--issues", str(issues))
        if updated not in timed_text.stdout:
            report(f"{label} text output lacks issue 12's passed time: {timed_text.stdout}")
            return 1
        write_text(issues, "[]")
        absent = overview("--issues", str(issues), "--json")
        if absent.returncode != 0:
            report(f"{label} empty issue array failed: {absent.stderr}")
            return 1
        absent_rows = {row["path"]: row for row in json.loads(absent.stdout)["worktrees"]}
        if absent_rows[str(a)].get("issueUpdates") != [{"number": 12, "updatedAt": None}]:
            report(f"{label} absent issue time is not null: {absent.stdout}")
            return 1
        bad = base / "bad.json"
        for content in ("not JSON", "{}", '[{"number": 12}]'):
            write_text(bad, content)
            refused = overview("--issues", str(bad))
            if refused.returncode != 1:
                report(f"{label} malformed --issues did not exit 1: {refused.returncode}")
                return 1
            if str(bad) not in refused.stderr:
                report(f"{label} malformed --issues does not name the file: {refused.stderr}")
                return 1
            if refused.stdout:
                report(f"{label} malformed --issues printed partial output: {refused.stdout}")
                return 1
        missing = base / "missing.json"
        refused = overview("--issues", str(missing))
        if refused.returncode != 1:
            report(f"{label} missing --issues did not exit 1: {refused.returncode}")
            return 1
        if str(missing) not in refused.stderr:
            report(f"{label} missing --issues does not name the file: {refused.stderr}")
            return 1
        if refused.stdout:
            report(f"{label} missing --issues printed partial output: {refused.stdout}")
            return 1
        if snapshot() != before:
            report(f"{label} the chat store's files changed")
            return 1
        repository_after = {str(file.relative_to(repo)): file.read_bytes()
                            for file in repo.rglob("*") if file.is_file()}
        if repository_after != repository_before:
            report(f"{label} the repository's files changed (including Git indexes and refs)")
            return 1
    report(f"{label} scenario passed")
    return 0


def validate_shift_resume_checks_commits_scenario() -> int:
    """Issue #347: a shift note's commit ids go stale before the next shift reads it.

    `keel shift resume` lists each commit id and `<branch> @ <sha>` the note
    names, checked against the remote-tracking refs as of the last fetch:
    already in the default branch, branch moved, branch gone, or not found.
    It fetches nothing.
    """
    label = "shift-resume-checks-commits:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-347-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)

        def git(*args: str) -> str:
            return subprocess.run(["git", *args], cwd=rtl, text=True, capture_output=True, check=True).stdout.strip()

        git("commit", "-q", "--allow-empty", "-m", "landed")
        git("push", "-q", "origin", "HEAD")
        landed = git("rev-parse", "HEAD")
        default = git("rev-parse", "--abbrev-ref", "HEAD")
        tree = git("rev-parse", "HEAD^{tree}")
        old = git("commit-tree", tree, "-p", landed, "-m", "feat one")
        git("push", "-q", "origin", f"{old}:refs/heads/feat")
        new = git("commit-tree", tree, "-p", old, "-m", "feat two")
        git("push", "-q", "origin", f"{new}:refs/heads/feat")
        note = (f"A84 {landed[:8]} is waiting to be merged. feat @ {old[:8]} waits for the push window. "
                f"gone-branch @ {landed[:8]} too. deadbee1 was the old base. Dated 20261018.")
        readied = run_keel(verify, "shift", "ready", note, env=env)
        if readied.returncode != 0:
            report(f"{label} ready failed: {readied.stderr}")
            return 1
        resumed = run_keel(verify, "shift", "resume", env=env)
        if resumed.returncode != 0:
            report(f"{label} resume failed: {resumed.stderr}")
            return 1
        lines = resumed.stdout.splitlines()

        def line_for(token: str) -> str:
            return next((l for l in lines if l.lstrip().startswith(("- " + token, token))), "")

        checks = (
            (landed[:8], f"already in origin/{default}"),
            (f"feat @ {old[:8]}", f"branch moved: now {new[:8]}"),
            (f"gone-branch @ {landed[:8]}", "branch gone"),
            ("deadbee1", "not found"),
        )
        for token, want in checks:
            found = line_for(token)
            if want not in found:
                report(f"{label} {token!r} is not marked {want!r}: {found!r} in {resumed.stdout!r}")
                return 1
        if line_for("20261018"):
            report(f"{label} a date was read as a commit id: {resumed.stdout!r}")
            return 1

        # A short sha can be all digits (about 2% of them): one named after `@`,
        # or one that resolves to a commit, is still a commit id.
        digits, n = "", 0
        while not digits:
            n += 1
            candidate = git("commit-tree", tree, "-p", landed, "-m", f"digits {n}")
            if candidate[:8].isdigit():
                digits = candidate
        git("push", "-q", "origin", f"{digits}:refs/heads/digits-branch")
        run_keel(verify, "shift", "ready", f"digits-branch @ {digits[:8]} is the tip. Also see {digits[:8]}.", env=env)
        again = run_keel(verify, "shift", "resume", env=env).stdout.splitlines()
        pair = next((l for l in again if l.startswith(f"- digits-branch @ {digits[:8]}")), "")
        if "current" not in pair:
            report(f"{label} an all-digit sha after `@` is not marked current: {pair!r} in {again!r}")
            return 1
        if not any(l.startswith(f"- {digits[:8]}:") for l in again):
            report(f"{label} an all-digit sha that resolves to a commit is not listed: {again!r}")
            return 1
        if "not fetched" not in resumed.stdout:
            report(f"{label} the check does not say it did not fetch: {resumed.stdout!r}")
            return 1
    if "shift-resume-checks-commits" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("shift-resume-checks-commits scenario passed.")
    return 0


def validate_shift_role_elsewhere_scenario() -> int:
    """Issues #290, #291: a note filed under the role from another worktree.

    `ready --role` files it under the role; an unbound worktree refuses to
    misfile while role requests are open; status names what works for a
    worktree note.
    """
    label = "shift-role-elsewhere:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-elsewhere-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)
        loose = chat_worktree(rtl, base / "loose")
        loose2 = chat_worktree(rtl, base / "loose2")
        for tree in (loose, loose2):
            subprocess.run(["git", "push", "-q", "-u", "origin", "HEAD"], cwd=tree, check=True, capture_output=True)

        def shift(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
            return run_keel(cwd, "shift", *args, env=env)

        shift(rtl, "request", "verify")
        common = mailbox_common_dir(rtl) / "keel-chat" / "shift"
        misfiled = shift(loose, "ready", "worked on R008 here")
        if misfiled.returncode == 0:
            report(f"{label} ready in an unbound worktree with verify's request open was accepted.")
            return 1
        if "--role verify" not in misfiled.stderr:
            report(f"{label} the refusal does not name --role verify: {misfiled.stderr}")
            return 1
        if list((common / "worktree").glob("*.md")) if (common / "worktree").exists() else []:
            report(f"{label} a refused ready still wrote a worktree note.")
            return 1
        wrong = shift(loose, "ready", "--role", "rtl", "x")
        if wrong.returncode == 0:
            report(f"{label} ready --role rtl, which has no open request, was accepted.")
            return 1
        filed = shift(loose, "ready", "--role", "verify", "worked on R008 in loose")
        if filed.returncode != 0:
            report(f"{label} ready --role verify failed: {filed.stdout} {filed.stderr}")
            return 1
        if not (common / "verify.md").exists():
            report(f"{label} ready --role verify did not file the note under verify.")
            return 1
        started = shift(rtl, "start", "verify")
        if started.returncode != 0:
            report(f"{label} keel shift start verify was refused: {started.stderr}")
            return 1
        lone = shift(loose2, "ready", "--force-reason", "the coordinator opens it", "nothing requested here")
        if lone.returncode != 0:
            report(f"{label} ready in an unbound worktree with no open request failed: {lone.stderr}")
            return 1
        status = shift(rtl, "status").stdout
        line = next((l for l in status.splitlines() if "loose2" in l), "")
        if str(loose2.resolve()) not in line or "keel shift resume" not in line:
            report(f"{label} the worktree note's status line does not name its path and keel shift resume: {line!r}")
            return 1
        if "keel shift start worktree" in status:
            report(f"{label} status still suggests keel shift start for a worktree note: {status!r}")
            return 1
    report("shift-role-elsewhere scenario passed.")
    return 0


def validate_shift_self_scenario() -> int:
    """Issue #293: a role with no coordinator changes its own shift.

    It cannot start itself, `ready` says nobody will start the new session,
    status says its own next session resumes the note, and a new session in
    an unbound worktree resumes it with `--role`.
    """
    label = "shift-self:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-self-") as raw:
        base = Path(raw)
        rtl, _verify, env, _ = shift_scratch(base)
        pm = chat_worktree(rtl, base / "pm")
        other = chat_worktree(rtl, base / "other")
        for tree in (pm, other):
            subprocess.run(["git", "push", "-q", "-u", "origin", "HEAD"], cwd=tree, check=True, capture_output=True)
        run_keel(pm, "chat", "role", "--set", "pm", env=env)

        def shift(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
            return run_keel(cwd, "shift", *args, env=env)

        readied = shift(pm, "ready", "pm note: next is R009")
        if readied.returncode != 0:
            report(f"{label} pm's ready failed: {readied.stderr}")
            return 1
        if "nobody" not in readied.stdout:
            report(f"{label} ready does not say nobody is set to start the new session: {readied.stdout!r}")
            return 1
        if "--wake" not in readied.stdout:
            report(f"{label} ready does not name --wake: {readied.stdout!r}")
            return 1
        if "The coordinator's `keel shift start` then wakes" in readied.stdout:
            report(f"{label} ready still promises a coordinator's start to a role nobody asked: {readied.stdout!r}")
            return 1
        itself = shift(pm, "start", "pm")
        if itself.returncode == 0:
            report(f"{label} keel shift start pm by pm was accepted.")
            return 1
        if "ready --wake" not in itself.stderr:
            report(f"{label} the refusal does not name ready --wake: {itself.stderr}")
            return 1
        if chat_log(rtl, "dm-pm--pm").exists():
            report(f"{label} a refused self-start still created dm-pm--pm.")
            return 1
        status = shift(rtl, "status").stdout
        line = next((l for l in status.splitlines() if l.startswith("pm:")), "")
        if "own next session" not in line:
            report(f"{label} status does not say pm's own next session resumes its note: {line!r}")
            return 1
        misbound = shift(rtl, "resume", "--role", "pm")
        if misbound.returncode == 0:
            report(f"{label} resume --role pm in rtl's worktree was accepted.")
            return 1
        resumed = shift(other, "resume", "--role", "pm")
        if resumed.returncode != 0:
            report(f"{label} resume --role pm in an unbound worktree failed: {resumed.stderr}")
            return 1
        if "next is R009" not in resumed.stdout:
            report(f"{label} resume --role pm did not print pm's note: {resumed.stdout!r}")
            return 1
        if (mailbox_common_dir(rtl) / "keel-chat" / "shift" / "pm.md").exists():
            report(f"{label} pm's note still waits after resume --role pm.")
            return 1
    report("shift-self scenario passed.")
    return 0


def validate_shift_self_wake_scenario() -> int:
    """Issue #293: `ready --wake` wakes the role's next session, once.

    A `compact` start does not trigger the waiter; a `clear` start does, and
    the role then has exactly one waking record from `keel-shift`. Without a
    chat role, `--wake` is refused.
    """
    label = "shift-self-wake:"
    protocol = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    line = next((l for l in protocol.splitlines() if l.startswith("- Keel schedules nothing")), "")
    if "keel shift ready --wake" not in line:
        report(f"{label} the protocol's scheduling line does not name the keel shift ready --wake exception: {line!r}")
        return 1
    with tempfile.TemporaryDirectory(prefix="keel-shift-wake-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)
        env = {**env, "KEEL_SHIFT_WAKE_POLL_MS": "100", "KEEL_SHIFT_WAKE_SETTLE_MS": "500", "KEEL_SHIFT_WAKE_TIMEOUT_MS": "20000"}
        loose = chat_worktree(rtl, base / "loose")
        subprocess.run(["git", "push", "-q", "-u", "origin", "HEAD"], cwd=loose, check=True, capture_output=True)

        def shift(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
            return run_keel(cwd, "shift", *args, env=env)

        def session_start(source: str) -> None:
            subprocess.run(
                ["node", str(ROOT / "bin" / "keel.js"), "chat", "hook", "session-start"],
                cwd=verify, env=env, text=True, capture_output=True, check=False,
                input=json.dumps({"cwd": str(verify), "source": source, "hook_event_name": "SessionStart"}),
            )

        def wakes() -> list[str]:
            return chat_records_with(rtl, "dm-keel-shift--verify", "keel shift resume")

        unbound = shift(loose, "ready", "--wake", "loose note")
        if unbound.returncode == 0:
            report(f"{label} ready --wake in an unbound worktree with no --role was accepted.")
            return 1
        armed = shift(verify, "ready", "--wake", "verify note: next is R010")
        if armed.returncode != 0:
            report(f"{label} ready --wake failed: {armed.stderr}")
            return 1
        session_start("compact")
        time.sleep(1)
        if wakes():
            report(f"{label} a compact start triggered the wake.")
            return 1
        session_start("clear")
        deadline = time.time() + 5
        while time.time() < deadline and not wakes():
            time.sleep(0.1)
        found = wakes()
        if len(found) != 1:
            report(f"{label} expected exactly one wake record from keel-shift after the clear start, found {len(found)}.")
            return 1
        if "from: keel-shift" not in found[0]:
            report(f"{label} the wake record is not from keel-shift: {found[0]!r}")
            return 1
        time.sleep(0.5)
        if len(wakes()) != 1:
            report(f"{label} the waiter wrote more than one wake record.")
            return 1
        checked = run_keel(verify, "chat", "notice", "--check", env=env)
        if checked.returncode != 0:
            report(f"{label} keel chat notice --check for verify does not see the wake (exit {checked.returncode}).")
            return 1
    report("shift-self-wake scenario passed.")
    return 0


def validate_role_drift_scenario() -> int:
    """Issue #301: bindings that drift from where sessions run are reported.

    A binding to a removed worktree and a role with a waiting note and no
    session are named by `keel patrol`, `keel --doctor`, and an unbound
    session's projection; `keel chat role --prune` removes only the former.
    """
    label = "role-drift:"
    with tempfile.TemporaryDirectory(prefix="keel-role-drift-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)
        ghost = chat_worktree(rtl, base / "ghost")
        run_keel(ghost, "chat", "role", "--set", "ghost", env=env)
        subprocess.run(["git", "worktree", "remove", "--force", str(ghost)], cwd=rtl, check=True, capture_output=True)
        loose = chat_worktree(rtl, base / "loose")
        write_text(loose / "openspec/specs/.keep", "")
        readied = run_keel(verify, "shift", "ready", "verify note", env=env)
        if readied.returncode != 0:
            report(f"{label} verify's ready failed: {readied.stderr}")
            return 1

        patrolled = run_keel(rtl, "patrol", env=env)
        drift = [line for line in patrolled.stdout.splitlines() if line.startswith("drift:")]
        if not any("ghost" in line and "/ghost" in line for line in drift):
            report(f"{label} keel patrol does not report ghost's removed worktree: {patrolled.stdout!r} {patrolled.stderr!r}")
            return 1
        if not any("verify" in line and "shift note" in line for line in drift):
            report(f"{label} keel patrol does not report verify as unattended: {patrolled.stdout!r}")
            return 1
        doctor = run_keel(rtl, "--doctor", env=env).stdout
        doctor_drift = [line for line in doctor.splitlines() if line.startswith("chat roles: drift")]
        if not any("ghost" in line for line in doctor_drift):
            report(f"{label} keel --doctor does not report ghost: {doctor_drift!r}")
            return 1
        if not any("verify" in line for line in doctor_drift):
            report(f"{label} keel --doctor does not report verify: {doctor_drift!r}")
            return 1
        context = json.loads(run_keel(loose, "context", "--json", env=env).stdout)
        if "verify" not in (context.get("unattendedRoles") or []):
            report(f"{label} an unbound worktree's context does not name verify: {context.get('unattendedRoles')!r}")
            return 1
        session = run_session_start_hook(
            loose, {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(loose)},
            keel_cli=f'node "{ROOT / "bin" / "keel.js"}"',
        )
        note = session_start_context(session) or ""
        if "verify" not in note:
            report(f"{label} the unbound session's note does not name verify: {note!r}")
            return 1
        pruned = run_keel(rtl, "chat", "role", "--prune", env=env)
        if "Pruned ghost" not in pruned.stdout:
            report(f"{label} keel chat role --prune did not prune ghost: {pruned.stdout!r} {pruned.stderr!r}")
            return 1
        roles = json.loads((mailbox_common_dir(rtl) / "keel-chat" / "roles.json").read_text(encoding="utf-8"))
        if "ghost" in roles.values():
            report(f"{label} roles.json still binds ghost: {roles!r}")
            return 1
        if sorted(set(roles.values())) != ["rtl", "verify"]:
            report(f"{label} prune changed other bindings: {roles!r}")
            return 1
        again = run_keel(rtl, "chat", "role", "--prune", env=env)
        if "No binding" not in again.stdout:
            report(f"{label} a second prune did not say there was nothing to prune: {again.stdout!r}")
            return 1
    report("role-drift scenario passed.")
    return 0


def validate_host_run_session_scenario() -> int:
    """Issue #300: a scheduled run started in a role's worktree is not that role.

    Its first prompt, starting `<scheduled-task`, restores the presence its
    SessionStart replaced; its hooks then write and inject nothing, its end
    changes nothing, and it never fires `ready --wake`. An ordinary clear
    still wakes the role once, after the wake settles.
    """
    label = "host-run-session:"
    with tempfile.TemporaryDirectory(prefix="keel-host-run-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)
        env = {**env, "KEEL_SHIFT_WAKE_POLL_MS": "100", "KEEL_SHIFT_WAKE_SETTLE_MS": "1500", "KEEL_SHIFT_WAKE_TIMEOUT_MS": "30000"}
        presence = mailbox_common_dir(rtl) / "keel-chat" / "presence" / "verify.json"

        def hook(event: str, payload: dict) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["node", str(ROOT / "bin" / "keel.js"), "chat", "hook", event],
                cwd=verify, env=env, text=True, capture_output=True, check=False,
                input=json.dumps({"cwd": str(verify), **payload}),
            )

        def wakes() -> list[str]:
            return chat_records_with(rtl, "dm-keel-shift--verify", "keel shift resume")

        def current() -> str:
            return presence.read_text(encoding="utf-8") if presence.exists() else ""

        hook("session-start", {"hook_event_name": "SessionStart", "source": "startup", "session_id": "s1"})
        hook("user-prompt-submit", {"hook_event_name": "UserPromptSubmit", "session_id": "s1", "prompt": "hello"})
        armed = run_keel(verify, "shift", "ready", "--wake", "verify note", env=env)
        if armed.returncode != 0:
            report(f"{label} ready --wake failed: {armed.stderr}")
            return 1
        run_keel(rtl, "chat", "post", "soc", "@verify something to read", env=env)
        before = current()
        hook("session-start", {"hook_event_name": "SessionStart", "source": "startup", "session_id": "run1"})
        prompted = hook("user-prompt-submit", {"hook_event_name": "UserPromptSubmit", "session_id": "run1",
                                               "prompt": '<scheduled-task name="patrol">\nrun the patrol'})
        if current() != before:
            report(f"{label} the host run's presence was not restored:\nbefore {before}\nafter {current()}")
            return 1
        if prompted.stdout.strip():
            report(f"{label} the host run's prompt hook injected output: {prompted.stdout!r}")
            return 1
        time.sleep(3)
        if wakes():
            report(f"{label} the host run's start fired the wake.")
            return 1
        hook("session-end", {"hook_event_name": "SessionEnd", "session_id": "run1"})
        if current() != before:
            report(f"{label} the host run's end changed presence:\nbefore {before}\nafter {current()}")
            return 1
        hook("session-start", {"hook_event_name": "SessionStart", "source": "clear", "session_id": "s2"})
        hook("user-prompt-submit", {"hook_event_name": "UserPromptSubmit", "session_id": "s2", "prompt": "carry on"})
        deadline = time.time() + 6
        while time.time() < deadline and not wakes():
            time.sleep(0.1)
        if len(wakes()) != 1:
            report(f"{label} expected one wake after the clear start, found {len(wakes())}.")
            return 1
        task_config = "patrol:\n  role: verify\n  every: 30m\n"
        write_text(verify / "keel" / "config.yaml", task_config)
        task = run_keel(verify, "patrol", "task", env=env)
        if "bound to no role" not in task.stdout:
            report(f"{label} keel patrol task does not say to create the task from a folder bound to no role: {task.stdout!r} {task.stderr!r}")
            return 1
    report("host-run-session scenario passed.")
    return 0


def validate_shift_keeps_transcripts_scenario() -> int:
    """Issue #343: a shift's conversation outlives the host's transcript file.

    Claude deletes transcripts after `cleanupPeriodDays` (30 by default), so
    when a role's session starts a new transcript the hook copies the ended
    one into Keel's store; `history` and `--grep` read the copy once the
    host's file is gone, and `--grep` reads a Codex rollout too.
    """
    label = "shift-keeps-transcripts:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-343-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)
        store_root = mailbox_common_dir(rtl) / "keel-chat"
        kept_dir = store_root / "shift" / "transcripts" / "verify"
        transcripts = base / "transcripts"
        transcripts.mkdir()

        def claude_transcript(name: str, said: str) -> Path:
            path = transcripts / f"{name}.jsonl"
            path.write_text("\n".join(json.dumps(record) for record in (
                {"type": "user", "timestamp": "2026-10-12T01:00:00.000Z", "message": {"role": "user", "content": "carry on"}},
                {"type": "assistant", "timestamp": "2026-10-12T01:00:05.000Z",
                 "message": {"role": "assistant", "content": [{"type": "text", "text": said}]}},
            )) + "\n", encoding="utf-8")
            return path

        def hook(transcript: Path, session: str) -> None:
            for event, name in (("session-start", "SessionStart"), ("user-prompt-submit", "UserPromptSubmit")):
                subprocess.run(
                    ["node", str(ROOT / "bin" / "keel.js"), "chat", "hook", event],
                    cwd=verify, env=env, text=True, capture_output=True, check=False,
                    input=json.dumps({"cwd": str(verify), "hook_event_name": name, "session_id": session,
                                      "prompt": "go", "source": "startup", "transcript_path": str(transcript)}),
                )

        def history(*args: str) -> subprocess.CompletedProcess[str]:
            return run_keel(verify, "shift", "history", *args, env=env)

        a = claude_transcript("a", "The arbiter retry budget is four cycles.")
        b = claude_transcript("b", "Resumed from the note.")
        hook(a, "s1")
        hook(b, "s1")
        kept_a = kept_dir / "a.jsonl.gz"
        if not kept_a.is_file():
            report(f"{label} no kept copy of transcript A under {kept_dir}: {sorted(p.name for p in kept_dir.glob('*')) if kept_dir.exists() else 'no directory'}")
            return 1
        if gzip.decompress(kept_a.read_bytes()) != a.read_bytes():
            report(f"{label} the kept copy of A is not A's bytes.")
            return 1
        if (kept_dir / "b.jsonl.gz").exists():
            report(f"{label} the current transcript B was copied while it is still being written.")
            return 1

        a.unlink()
        listed = history("verify")
        line_a = next((l for l in listed.stdout.splitlines() if str(a) in l), "")
        if "(missing)" in line_a:
            report(f"{label} A, deleted but kept, is still listed as missing: {line_a!r}")
            return 1
        if "(kept)" not in line_a:
            report(f"{label} A, deleted but kept, is not marked (kept): {line_a!r}")
            return 1
        found = history("verify", "--grep", "retry budget")
        if found.returncode != 0:
            report(f"{label} --grep for a phrase in the kept copy of A exited {found.returncode}: {found.stdout!r} {found.stderr!r}")
            return 1
        if "retry budget" not in found.stdout:
            report(f"{label} --grep does not print the phrase from the kept copy of A: {found.stdout!r}")
            return 1

        # A Codex rollout is searched the same way.
        c = transcripts / "rollout-c.jsonl"
        c.write_text("\n".join(json.dumps(record) for record in (
            {"timestamp": "2026-10-18T09:50:18.096Z", "type": "session_meta", "payload": {}},
            {"timestamp": "2026-10-18T09:50:21.766Z", "type": "response_item",
             "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "Check the FIFO depth for the IECC lane."}]}},
            {"timestamp": "2026-10-18T09:50:23.621Z", "type": "response_item",
             "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "ok"}]}},
        )) + "\n", encoding="utf-8")
        hook(c, "s2")
        found = history("verify", "--grep", "FIFO depth")
        if found.returncode != 0:
            report(f"{label} --grep for a phrase in a Codex rollout exited {found.returncode}: {found.stdout!r} {found.stderr!r}")
            return 1
        if "FIFO depth" not in found.stdout:
            report(f"{label} --grep does not print the phrase from a Codex rollout: {found.stdout!r}")
            return 1

        # A transcript that grew after its copy is copied again.
        with b.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"type": "assistant", "timestamp": "2026-10-12T02:00:00.000Z",
                                     "message": {"role": "assistant", "content": [{"type": "text", "text": "late line"}]}}) + "\n")
        d = claude_transcript("d", "Next shift.")
        hook(d, "s3")
        kept_b = kept_dir / "b.jsonl.gz"
        if not kept_b.is_file():
            report(f"{label} B ended and has no kept copy.")
            return 1
        if gzip.decompress(kept_b.read_bytes()) != b.read_bytes():
            report(f"{label} B's kept copy does not match B after it ended.")
            return 1
        with b.open("a", encoding="utf-8") as handle:
            handle.write("{}\n")
        e = claude_transcript("e", "Another shift.")
        hook(e, "s4")
        if gzip.decompress(kept_b.read_bytes()) != b.read_bytes():
            report(f"{label} B grew after its copy and was not copied again.")
            return 1
    report("shift-keeps-transcripts scenario passed.")
    return 0


def validate_shift_keeps_found_transcripts_scenario() -> int:
    """Issue #361: a transcript `history` finds but never recorded is kept too.

    Transcripts from before segments were recorded (#304) are listed
    `(found)`; the hook copied only recorded segments, and `history` read a
    copy only through a segment record, so the oldest conversations were the
    ones left unkept.
    """
    label = "shift-keeps-found-transcripts:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-361-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)
        kept_dir = mailbox_common_dir(rtl) / "keel-chat" / "shift" / "transcripts" / "verify"
        roles = json.loads((mailbox_common_dir(rtl) / "keel-chat" / "roles.json").read_text(encoding="utf-8"))
        bound = next(path for path, role in roles.items() if role == "verify")
        project = base / "claude-config" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", bound)
        project.mkdir(parents=True)
        env = {**env, "CLAUDE_CONFIG_DIR": str(base / "claude-config")}

        def transcript(name: str, opening: str, said: str) -> Path:
            path = project / f"{name}.jsonl"
            path.write_text("\n".join(json.dumps(record) for record in (
                {"type": "user", "timestamp": "2026-10-02T01:00:00.000Z", "cwd": bound, "message": {"role": "user", "content": opening}},
                {"type": "assistant", "timestamp": "2026-10-02T01:00:05.000Z", "cwd": bound,
                 "message": {"role": "assistant", "content": [{"type": "text", "text": said}]}},
            )) + "\n", encoding="utf-8")
            return path

        def hook(path: Path) -> None:
            for event, name in (("session-start", "SessionStart"), ("user-prompt-submit", "UserPromptSubmit")):
                subprocess.run(
                    ["node", str(ROOT / "bin" / "keel.js"), "chat", "hook", event],
                    cwd=verify, env=env, text=True, capture_output=True, check=False,
                    input=json.dumps({"cwd": str(verify), "hook_event_name": name, "session_id": "s1",
                                      "prompt": "go", "source": "startup", "transcript_path": str(path)}),
                )

        old = transcript("old", "start the shift", "The ECC syndrome table was settled on day one.")
        scheduled = transcript("patrol", '<scheduled-task name="patrol">run', "patrol ran")
        listed = run_keel(verify, "shift", "history", "verify", env=env)
        if "(found)" not in next((l for l in listed.stdout.splitlines() if "old.jsonl" in l), ""):
            report(f"{label} the unrecorded transcript is not listed as found: {listed.stdout!r} {listed.stderr!r}")
            return 1
        hook(transcript("a", "carry on", "first recorded shift"))
        hook(transcript("b", "carry on", "second recorded shift"))
        kept_old = kept_dir / "old.jsonl.gz"
        if not kept_old.is_file():
            report(f"{label} a segment change left the found transcript unkept: "
                   f"{sorted(p.name for p in kept_dir.glob('*')) if kept_dir.exists() else 'no directory'}")
            return 1
        if gzip.decompress(kept_old.read_bytes()) != old.read_bytes():
            report(f"{label} the found transcript's copy is not its bytes.")
            return 1
        if (kept_dir / "patrol.jsonl.gz").exists():
            report(f"{label} a scheduled run's transcript was kept as the role's conversation.")
            return 1
        if (kept_dir / "b.jsonl.gz").exists():
            report(f"{label} the current transcript was copied while it is still being written.")
            return 1

        old.unlink()
        listed = run_keel(verify, "shift", "history", "verify", env=env)
        line = next((l for l in listed.stdout.splitlines() if "old.jsonl" in l), "")
        if "(missing)" in line:
            report(f"{label} the found transcript, deleted but kept, is listed missing: {listed.stdout!r}")
            return 1
        if "(kept)" not in line:
            report(f"{label} the found transcript, deleted but kept, is not listed (kept): {listed.stdout!r}")
            return 1
        found = run_keel(verify, "shift", "history", "verify", "--grep", "syndrome table", env=env)
        if "syndrome table" not in found.stdout:
            report(f"{label} --grep does not search the found transcript's copy: {found.stdout!r} {found.stderr!r}")
            return 1
        hook(transcript("c", "carry on", "third recorded shift"))
        listed = run_keel(verify, "shift", "history", "verify", env=env)
        if sum(1 for l in listed.stdout.splitlines() if "old.jsonl" in l) != 1:
            report(f"{label} another segment change did not leave the kept found transcript listed once: {listed.stdout!r}")
            return 1
    if "shift-keeps-found-transcripts" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("shift-keeps-found-transcripts scenario passed.")
    return 0


def validate_shift_history_scenario() -> int:
    """Issue #304: a cleared shift's conversation stays findable.

    The hooks record each transcript a role's session runs in; a scheduled
    run's is undone; `keel shift history` lists and greps them; `ready` and
    the clear hint name the history and Remote Control.
    """
    label = "shift-history:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-history-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)
        transcripts = base / "transcripts"
        transcripts.mkdir()

        def transcript(name: str, said: str) -> Path:
            path = transcripts / f"{name}.jsonl"
            path.write_text("\n".join(json.dumps(record) for record in (
                {"type": "user", "timestamp": "2026-10-12T01:00:00.000Z", "message": {"role": "user", "content": "carry on with R008"}},
                {"type": "assistant", "timestamp": "2026-10-12T01:00:05.000Z",
                 "message": {"role": "assistant", "content": [{"type": "text", "text": said}]}},
            )) + "\n", encoding="utf-8")
            return path

        a = transcript("a", "The timing fix for the clock gate lands in R008 after the review.")
        b = transcript("b", "Resumed from the note.")
        c = transcript("c", "patrol run")

        def hook(event: str, payload: dict) -> None:
            subprocess.run(
                ["node", str(ROOT / "bin" / "keel.js"), "chat", "hook", event],
                cwd=verify, env=env, text=True, capture_output=True, check=False,
                input=json.dumps({"cwd": str(verify), **payload}),
            )

        def history(*args: str) -> subprocess.CompletedProcess[str]:
            return run_keel(verify, "shift", "history", *args, env=env)

        hook("session-start", {"hook_event_name": "SessionStart", "source": "startup", "session_id": "s1", "transcript_path": str(a)})
        hook("user-prompt-submit", {"hook_event_name": "UserPromptSubmit", "session_id": "s1", "prompt": "go", "transcript_path": str(a)})
        readied = run_keel(verify, "shift", "ready", "verify note", env=env)
        if "keel shift history verify" not in readied.stdout:
            report(f"{label} ready does not name keel shift history verify: {readied.stdout!r} {readied.stderr!r}")
            return 1
        if "Remote Control" not in readied.stdout:
            report(f"{label} the clear hint does not name Remote Control: {readied.stdout!r}")
            return 1
        hook("session-start", {"hook_event_name": "SessionStart", "source": "clear", "session_id": "s1", "transcript_path": str(b)})
        hook("user-prompt-submit", {"hook_event_name": "UserPromptSubmit", "session_id": "s1", "prompt": "resume", "transcript_path": str(b)})
        hook("session-start", {"hook_event_name": "SessionStart", "source": "startup", "session_id": "run1", "transcript_path": str(c)})
        hook("user-prompt-submit", {"hook_event_name": "UserPromptSubmit", "session_id": "run1",
                                    "prompt": '<scheduled-task name="patrol">run', "transcript_path": str(c)})

        listed = history("verify")
        if listed.returncode != 0:
            report(f"{label} keel shift history failed: {listed.stderr}")
            return 1
        lines = [line for line in listed.stdout.splitlines() if ".jsonl" in line]
        if len(lines) != 2:
            report(f"{label} expected two transcript segments, got: {listed.stdout!r}")
            return 1
        if str(b) not in lines[0] or "now" not in lines[0]:
            report(f"{label} the newest segment is not B, still current: {lines[0]!r}")
            return 1
        if str(a) not in lines[1] or "now" in lines[1]:
            report(f"{label} the older segment is not A, ended: {lines[1]!r}")
            return 1
        if str(c) in listed.stdout:
            report(f"{label} the scheduled run's transcript is listed: {listed.stdout!r}")
            return 1
        found = history("verify", "--grep", "clock gate")
        if found.returncode != 0:
            report(f"{label} --grep for a phrase in A exited {found.returncode}: {found.stdout!r} {found.stderr!r}")
            return 1
        if "clock gate" not in found.stdout or str(a) not in found.stdout:
            report(f"{label} --grep does not print the phrase under A: {found.stdout!r}")
            return 1
        missing = history("verify", "--grep", "nothing like this")
        if missing.returncode != 1:
            report(f"{label} --grep for an absent phrase exited {missing.returncode}.")
            return 1
        as_json = json.loads(history("verify", "--json").stdout)
        if [seg.get("transcript") for seg in as_json.get("segments", [])] != [str(b), str(a)]:
            report(f"{label} --json segments are {as_json.get('segments')!r}.")
            return 1

        # Earlier history, kept by Claude before Keel recorded anything (D6).
        roles = json.loads((mailbox_common_dir(rtl) / "keel-chat" / "roles.json").read_text(encoding="utf-8"))
        bound = next(path for path, role in roles.items() if role == "verify")
        project = base / "claude-config" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", bound)
        project.mkdir(parents=True)
        (project / "d.jsonl").write_text("\n".join(json.dumps(record) for record in (
            {"type": "user", "timestamp": "2026-10-04T13:19:18.000Z", "cwd": bound, "message": {"role": "user", "content": "start the shift"}},
            {"type": "assistant", "timestamp": "2026-10-04T13:27:58.000Z", "cwd": bound,
             "message": {"role": "assistant", "content": [{"type": "text", "text": "The DMC arbiter plan was agreed on the first day."}]}},
        )) + "\n", encoding="utf-8")
        (project / "e.jsonl").write_text(json.dumps(
            {"type": "user", "timestamp": "2026-10-12T11:57:15.000Z", "cwd": bound, "message": {"role": "user", "content": '<scheduled-task name="patrol">run'}}
        ) + "\n", encoding="utf-8")
        found_env = {**env, "CLAUDE_CONFIG_DIR": str(base / "claude-config")}
        earlier = run_keel(verify, "shift", "history", "verify", env=found_env)
        d_line = next((line for line in earlier.stdout.splitlines() if "d.jsonl" in line), "")
        if "(found)" not in d_line:
            report(f"{label} the earlier transcript D is not listed as found: {earlier.stdout!r} {earlier.stderr!r}")
            return 1
        if "e.jsonl" in earlier.stdout:
            report(f"{label} the scheduled run E is listed: {earlier.stdout!r}")
            return 1
        arbiter = run_keel(verify, "shift", "history", "verify", "--grep", "arbiter plan", env=found_env)
        if "arbiter plan" not in arbiter.stdout:
            report(f"{label} --grep does not search the earlier transcript D: {arbiter.stdout!r}")
            return 1
    report("shift-history scenario passed.")
    return 0


def validate_shift_coordinator_last_scenario() -> int:
    """Issue #289: the coordinator starts the others before its own shift ends.

    Its check reports a waiting, unstarted note and its ready is refused until
    it starts that role; a successor's resume lists who still waits; the
    request and ready name session state a clear destroys.
    """
    label = "shift-coordinator-last:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-coordinator-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)

        def shift(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
            return run_keel(cwd, "shift", *args, env=env)

        shift(rtl, "request", "verify")
        request_text = "\n".join(chat_records_with(rtl, "dm-rtl--verify", "Shift change requested"))
        if "scheduled jobs" not in request_text:
            report(f"{label} the request does not name scheduled jobs: {request_text!r}")
            return 1
        readied = shift(verify, "ready", "verify note")
        if readied.returncode != 0:
            report(f"{label} verify's ready failed: {readied.stderr}")
            return 1
        if "scheduled jobs" not in readied.stdout:
            report(f"{label} ready's output does not name scheduled jobs: {readied.stdout!r}")
            return 1
        checked = shift(rtl, "check", "--json")
        items = json.loads(checked.stdout).get("items", [])
        if checked.returncode != 1:
            report(f"{label} rtl's check exited {checked.returncode} with verify unstarted, not 1.")
            return 1
        if not any(i.get("kind") == "unstarted" and "verify" in i.get("detail", "") for i in items):
            report(f"{label} rtl's check has no unstarted item for verify: {items!r}")
            return 1
        if shift(rtl, "ready", "rtl note").returncode == 0:
            report(f"{label} rtl's ready was accepted with verify unstarted.")
            return 1
        shift(rtl, "start", "verify")
        after = json.loads(shift(rtl, "check", "--json").stdout).get("items", [])
        if any(i.get("kind") == "unstarted" for i in after):
            report(f"{label} rtl's check still reports unstarted after start: {after!r}")
            return 1

        shift(verify, "resume")
        shift(rtl, "request", "verify")
        shift(verify, "ready", "verify note, second round")
        forced = shift(rtl, "ready", "--force-reason", "user is away", "rtl note")
        if forced.returncode != 0:
            report(f"{label} rtl's ready --force-reason failed: {forced.stderr}")
            return 1
        resumed = shift(rtl, "resume")
        if "verify" not in resumed.stdout or "keel shift start" not in resumed.stdout:
            report(f"{label} rtl's resume does not list verify as waiting for keel shift start: {resumed.stdout!r}")
            return 1
    report("shift-coordinator-last scenario passed.")
    return 0


def validate_shift_change_scenario() -> int:
    """Owner's decision of 2026-10-05: a role's session changes shift through Keel.

    The coordinator requests it, the role's readiness check names every loose
    end, `ready` stores the shift note outside the worktree and closes the
    request, `start` wakes the cleared role only once the note waits, the
    session-start notice points to the note, and `resume` consumes it.
    """
    label = "shift-change:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-") as raw:
        base = Path(raw)
        rtl, verify, env = chat_scratch_group(base)
        remote = base / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=rtl, check=True)
        for tree in (rtl, verify):
            subprocess.run(["git", "push", "-q", "-u", "origin", "HEAD"], cwd=tree, check=True, capture_output=True)
        common = mailbox_common_dir(rtl) / "keel-chat"
        signal = common / "signal" / "verify"

        def shift(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
            return run_keel(cwd, "shift", *args, env=env)

        def notice() -> str:
            # The SessionStart projection, which every host runs (shift-without-role D3).
            session = run_session_start_hook(
                verify, {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(verify)},
                keel_cli=f'node "{ROOT / "bin" / "keel.js"}"', extra_env={k: v for k, v in env.items() if k.startswith("KEEL_")},
            )
            return session_start_context(session) or ""

        size = signal.stat().st_size if signal.exists() else 0
        requested = shift(rtl, "request", "verify")
        if requested.returncode != 0:
            report(f"{label} keel shift request failed: {requested.stderr.strip()}")
            return 1
        request = [r for r in chat_records_with(rtl, "dm-rtl--verify", "shift") if "kind: todo" in r and "keel-shift" in r]
        if not request:
            report(f"{label} no keel-shift todo reached dm-rtl--verify: {requested.stdout.strip()}")
            return 1
        if "assignee: verify" not in request[0]:
            report(f"{label} the shift request is not assigned to verify:\n{request[0]}")
            return 1
        if not signal.exists():
            report(f"{label} the request created no signal file for verify.")
            return 1
        if signal.stat().st_size <= size:
            report(f"{label} the request did not touch verify's signal file.")
            return 1
        if shift(rtl, "start", "verify").returncode == 0:
            report(f"{label} keel shift start succeeded before verify was ready.")
            return 1

        # Every kind of loose end at once.
        write_text(verify / "scratch.txt", "uncommitted\n")
        write_text(verify / "pushed-not.txt", "x\n")
        subprocess.run(["git", "add", "pushed-not.txt"], cwd=verify, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "local only"], cwd=verify, check=True)
        write_text(verify / "keel" / "guard.json", "{}\n")
        leased = run_keel(verify, "lock", "acquire", "main-checkout", "--for", "1h", "--note", "shift fixture", env=env)
        if leased.returncode != 0:
            report(f"{label} could not acquire the shift fixture lease: {leased.stderr}")
            return 1
        other_lease = run_keel(rtl, "lock", "acquire", "other-worktree", "--for", "1h", "--note", "other session", env=env)
        if other_lease.returncode != 0:
            report(f"{label} could not acquire the other worktree's lease: {other_lease.stderr}")
            return 1
        lease_file = common / "locks" / "main-checkout.json"
        lease_before = lease_file.read_bytes()
        # A Claude scratchpad of a session started in verify, and one of a
        # session started elsewhere (shift-temp-owner D1).
        scratch = Path(tempfile.gettempdir()) / f"claude-{os.getuid()}"
        slug = re.sub(r"[^A-Za-z0-9]", "-", str(verify.resolve()))
        temp_tree = scratch / slug / f"keel-test-{os.getpid()}" / "scratchpad" / "own-tmp-tree"
        other_tree = scratch / "-some-other-dir" / f"keel-test-{os.getpid()}" / "scratchpad" / "other-tmp-tree"
        for tree in (temp_tree, other_tree):
            tree.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "worktree", "add", "-q", "--detach", str(temp_tree)], cwd=verify, check=True, capture_output=True)
        run_keel(rtl, "chat", "todo", "soc", "--assignee", "verify", "Rerun the regression", env=env)
        # Its own session, as a job a session leaves behind would be: the check
        # skips its own command line's process group.
        sleeper = subprocess.Popen(["sleep", "60"], cwd=verify, start_new_session=True)
        try:
            checked = shift(verify, "check", "--json")
            if checked.returncode != 1:
                report(f"{label} keel shift check exited {checked.returncode} with loose ends present.")
                return 1
            text = checked.stdout
            lock_items = [item for item in chat_json(checked).get("items", []) if item["kind"] == "lock"]
            if len(lock_items) != 1:
                report(f"{label} expected exactly one held-worktree lock item: {text}")
                return 1
            for needle in ("main-checkout", "verify", "shift fixture", json.loads(lease_before)["expires"]):
                if needle not in lock_items[0]["detail"]:
                    report(f"{label} lock item omits {needle!r}: {lock_items}")
                    return 1
            if lease_file.read_bytes() != lease_before:
                report(f"{label} shift check changed the live lease")
                return 1
            for needle in ("scratch.txt", "local only", "guard.json", str(sleeper.pid), temp_tree.name, "Rerun the regression", "main-checkout"):
                if needle not in text:
                    report(f"{label} keel shift check does not name {needle!r}: {text.strip()[:600]}")
                    return 1
            refused = shift(verify, "ready", "next: rerun R007")
            if refused.returncode == 0:
                report(f"{label} keel shift ready succeeded with loose ends present.")
                return 1
            if "scratch.txt" not in refused.stdout + refused.stderr:
                report(f"{label} the refused ready does not name the loose ends: {refused.stderr.strip()}")
                return 1
            if (common / "shift" / "verify.md").exists():
                report(f"{label} a refused ready stored a note.")
                return 1
        finally:
            sleeper.kill()
            sleeper.wait()

        (verify / "scratch.txt").unlink()
        (verify / "keel" / "guard.json").unlink()
        released = run_keel(verify, "lock", "release", "main-checkout", env=env)
        if released.returncode != 0:
            report(f"{label} could not release the shift fixture lease: {released.stderr}")
            return 1
        after_release = shift(verify, "check", "--json")
        if any(item["kind"] == "lock" for item in chat_json(after_release).get("items", [])):
            report(f"{label} shift check retained a lock item after release: {after_release.stdout}")
            return 1
        subprocess.run(["git", "push", "-q"], cwd=verify, check=True, capture_output=True)
        subprocess.run(["git", "worktree", "remove", "--force", str(temp_tree)], cwd=verify, check=True)
        todo_id = next(r for r in chat_records_with(rtl, "soc", "Rerun the regression"))
        open_todo = re.search(r"^id: (\S+)", todo_id, re.M).group(1)
        run_keel(verify, "chat", "done", open_todo, env=env)
        run_keel(verify, "chat", "read", env=env)
        clean = shift(verify, "check")
        if clean.returncode != 0:
            report(f"{label} keel shift check is not ready on a clean worktree: {clean.stdout.strip()} {clean.stderr.strip()}")
            return 1
        subprocess.run(["git", "worktree", "add", "-q", "--detach", str(other_tree)], cwd=verify, check=True, capture_output=True)
        try:
            foreign = shift(verify, "check")
            if foreign.returncode != 0:
                report(f"{label} another session's temporary worktree blocked the check: {foreign.stdout.strip()}")
                return 1
            if "other-tmp-tree" not in foreign.stdout:
                report(f"{label} another session's temporary worktree is not listed as a note: {foreign.stdout.strip()}")
                return 1
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(other_tree)], cwd=verify, check=False, capture_output=True)
            shutil.rmtree(scratch / slug / f"keel-test-{os.getpid()}", ignore_errors=True)
            shutil.rmtree(scratch / "-some-other-dir" / f"keel-test-{os.getpid()}", ignore_errors=True)

        ready = shift(verify, "ready", "next: rerun R007 on 1b64e8c")
        if ready.returncode != 0:
            report(f"{label} keel shift ready failed on a clean worktree: {ready.stderr.strip()}")
            return 1
        note = common / "shift" / "verify.md"
        if not note.exists():
            report(f"{label} no shift note was stored at {note}.")
            return 1
        if "rerun R007 on 1b64e8c" not in note.read_text(encoding="utf-8"):
            report(f"{label} the stored shift note lacks the text given to ready.")
            return 1
        for needle in ("clear_session", "/clear"):
            if needle not in ready.stdout:
                report(f"{label} keel shift ready does not say how to clear the session ({needle!r}): {ready.stdout.strip()}")
                return 1
        reply = chat_records_with(rtl, "dm-rtl--verify", "done")
        if not reply:
            report(f"{label} ready did not reply done to the request.")
            return 1
        if "kind: done" not in "".join(chat_records_with(rtl, "dm-rtl--verify", "")):
            report(f"{label} the shift request was not closed.")
            return 1

        status = shift(rtl, "status")
        if "verify: note waiting" not in status.stdout:
            report(f"{label} keel shift status does not list verify with a waiting note: {status.stdout.strip()}")
            return 1
        if "keel shift resume" not in notice():
            report(f"{label} the session-start notice does not point to the waiting note.")
            return 1

        size = signal.stat().st_size
        started = shift(rtl, "start", "verify", "then pick up #157")
        if started.returncode != 0:
            report(f"{label} keel shift start failed after ready: {started.stderr.strip()}")
            return 1
        if not chat_records_with(rtl, "dm-rtl--verify", "keel shift resume"):
            report(f"{label} the cold-start message does not name keel shift resume.")
            return 1
        if signal.stat().st_size <= size:
            report(f"{label} the cold-start message did not touch verify's signal file.")
            return 1

        resumed = shift(verify, "resume")
        if resumed.returncode != 0:
            report(f"{label} keel shift resume failed: {resumed.stderr.strip()}")
            return 1
        if "rerun R007 on 1b64e8c" not in resumed.stdout:
            report(f"{label} keel shift resume did not print the note: {resumed.stdout.strip()}")
            return 1
        if note.exists():
            report(f"{label} resume left the note waiting.")
            return 1
        if not list((common / "shift" / "history").glob("verify-*.md")):
            report(f"{label} resume did not keep the note in history.")
            return 1
        if not chat_records_with(rtl, "dm-rtl--verify", "on shift"):
            report(f"{label} resume did not tell the coordinator verify is on shift.")
            return 1
        if "keel shift resume" in notice():
            report(f"{label} the notice still points to a note already resumed.")
            return 1
        again = shift(verify, "resume")
        if "no shift note" not in again.stdout.lower():
            report(f"{label} a second resume does not say no note waits: {again.stdout.strip()} {again.stderr.strip()}")
            return 1

    for relative in ("docs/shift-change.md", "docs/shift-change.zh-CN.md"):
        if not (ROOT / relative).exists():
            report(f"{label} {relative} is missing.")
            return 1
    for readme, guide in (("README.md", "docs/shift-change.md"), ("README.zh-CN.md", "docs/shift-change.zh-CN.md")):
        if guide not in (ROOT / readme).read_text(encoding="utf-8"):
            report(f"{label} {readme} does not link {guide}.")
            return 1
    if "shift-change" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("shift-change scenario passed.")
    return 0


def validate_self_shift_authorization_scenario() -> int:
    """Issue #319: `self-shift` lets a desktop session take its own three steps.

    The name is read and listed by `--doctor`, a scoped form is refused, and a
    desktop `keel shift ready --wake` says the steps are standing-authorized
    only when the repository declares it.
    """
    label = "self-shift-authorization:"
    with tempfile.TemporaryDirectory(prefix="keel-self-shift-") as raw:
        base = Path(raw)
        _rtl, verify, env, _ = shift_scratch(base)
        env = {**env, "KEEL_SHIFT_WAKE_TIMEOUT_MS": "2000"}
        desktop = {**env, "CLAUDE_CODE_ENTRYPOINT": "claude-desktop", "CLAUDE_CODE_HOST_SESSION_ID": "local_test-319"}
        config = verify / "keel" / "config.yaml"
        reason = ("--force-reason", "the fixture config is uncommitted")

        def declare(*entries: str) -> None:
            write_text(config, "authorize:\n" + "".join(f"  - {entry}\n" for entry in entries))

        declare("commit", "self-shift")
        doctor = run_keel(verify, "--doctor", env=env)
        if "self-shift" not in doctor.stdout or "unrecognized" in (doctor.stdout + doctor.stderr).lower():
            report(f"{label} self-shift was not read and listed as a standing authorization: {doctor.stdout.strip()} {doctor.stderr.strip()}")
            return 1
        granted = run_keel(verify, "shift", "ready", "--wake", *reason, "verify note: R015", env=desktop)
        if "Standing-authorized by `self-shift`" not in granted.stdout:
            report(f"{label} a desktop ready --wake with self-shift declared does not say the steps are standing-authorized: {granted.stdout.strip()} {granted.stderr.strip()}")
            return 1
        # Three once the Remote Control step went (#324).
        if "take these four steps now" not in granted.stdout:
            report(f"{label} a desktop ready --wake with self-shift declared does not cover four steps: {granted.stdout.strip()}")
            return 1
        run_keel(verify, "shift", "resume", env=desktop)

        declare("commit")
        asked = run_keel(verify, "shift", "ready", "--wake", *reason, "verify note: R016", env=desktop)
        if "Standing-authorized by `self-shift`" in asked.stdout:
            report(f"{label} a desktop ready --wake without self-shift says the steps are standing-authorized: {asked.stdout.strip()}")
            return 1
        if "self-shift" not in asked.stdout:
            report(f"{label} a desktop ready --wake without self-shift does not name the declaration that would allow it: {asked.stdout.strip()}")
            return 1
        run_keel(verify, "shift", "resume", env=desktop)

        declare("commit", "self-shift:anything")
        scoped = run_keel(verify, "--doctor", env=env)
        combined = scoped.stdout + scoped.stderr
        if "self-shift:anything" not in combined or "commit: authorized" in combined:
            report(f"{label} a scoped self-shift was not refused by name: {combined.strip()}")
            return 1

    for relative in ("README.md", "docs/shift-change.md", "docs/shift-change.zh-CN.md"):
        if "self-shift" not in (ROOT / relative).read_text(encoding="utf-8"):
            report(f"{label} {relative} does not name self-shift.")
            return 1
    if "self-shift-authorization" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("self-shift-authorization scenario passed.")
    return 0


def validate_shift_restore_authorization_scenario() -> int:
    """Issue #319: `shift-restore` lets a woken desktop shift restore itself.

    The name is read and listed by `--doctor`, a scoped form is refused, and
    a desktop `keel shift resume` says the restore is standing-authorized only
    when the repository declares it.
    """
    label = "shift-restore-authorization:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-restore-") as raw:
        base = Path(raw)
        _rtl, verify, env, _ = shift_scratch(base)
        env = {**env, "KEEL_SHIFT_WAKE_TIMEOUT_MS": "2000"}
        desktop = {**env, "CLAUDE_CODE_ENTRYPOINT": "claude-desktop", "CLAUDE_CODE_HOST_SESSION_ID": "local_test-319"}
        config = verify / "keel" / "config.yaml"

        def declare(*entries: str) -> None:
            write_text(config, "authorize:\n" + "".join(f"  - {entry}\n" for entry in entries))

        declare("commit", "shift-restore")
        doctor = run_keel(verify, "--doctor", env=env)
        if "shift-restore" not in doctor.stdout:
            report(f"{label} keel --doctor does not list shift-restore: {doctor.stdout.strip()} {doctor.stderr.strip()}")
            return 1
        if "unrecognized" in (doctor.stdout + doctor.stderr).lower():
            report(f"{label} shift-restore was not read as a standing authorization: {doctor.stdout.strip()} {doctor.stderr.strip()}")
            return 1
        run_keel(verify, "shift", "ready", "--wake", "--force-reason", "the fixture config is uncommitted", "verify note: R013", env=desktop)
        granted = run_keel(verify, "shift", "resume", env=desktop)
        if "Standing-authorized by `shift-restore`" not in granted.stdout:
            report(f"{label} a desktop resume with shift-restore declared does not say it is standing-authorized: {granted.stdout.strip()}")
            return 1

        declare("commit")
        run_keel(verify, "shift", "ready", "--wake", "--force-reason", "the fixture config is uncommitted", "verify note: R014", env=desktop)
        asked = run_keel(verify, "shift", "resume", env=desktop)
        if "Standing-authorized" in asked.stdout:
            report(f"{label} a desktop resume without shift-restore says the restore is standing-authorized: {asked.stdout.strip()}")
            return 1
        if "shift-restore" not in asked.stdout:
            report(f"{label} a desktop resume without shift-restore does not name the declaration that would allow it: {asked.stdout.strip()}")
            return 1

        declare("commit", "shift-restore:anything")
        scoped = run_keel(verify, "--doctor", env=env)
        combined = scoped.stdout + scoped.stderr
        if "shift-restore:anything" not in combined or "commit: authorized" in combined:
            report(f"{label} a scoped shift-restore was not refused by name: {combined.strip()}")
            return 1

    if "shift-restore" not in (ROOT / "README.md").read_text(encoding="utf-8"):
        report(f"{label} README.md does not document shift-restore.")
        return 1
    if "shift-restore-authorization" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("shift-restore-authorization scenario passed.")
    return 0


def validate_shift_await_clear_scenario() -> int:
    """`keel shift await-clear` returns once the outgoing process is gone.

    The desktop wake starts at once and waits on it, so it can never land
    before the clear (D1, D2 of shift-desktop-wake-in-a-minute).
    """
    label = "shift-await-clear:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-await-") as raw:
        base = Path(raw)
        _rtl, verify, env, _ = shift_scratch(base)
        # Reaped as soon as it exits, as the app reaps its session's process;
        # an unreaped zombie still answers kill(pid, 0).
        brief = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(1)"])
        reaper = threading.Thread(target=brief.wait)
        reaper.start()
        started = time.monotonic()
        gone = run_keel(verify, "shift", "await-clear", "--pid", str(brief.pid), "--timeout-ms", "15000", env=env)
        reaper.join()
        if gone.returncode != 0:
            report(f"{label} await-clear did not exit 0 once the process exited: {gone.returncode} {gone.stdout.strip()} {gone.stderr.strip()}")
            return 1
        if "cleared" not in gone.stdout:
            report(f"{label} await-clear did not say `cleared` once the process exited: {gone.stdout.strip()}")
            return 1
        if time.monotonic() - started > 10:
            report(f"{label} await-clear took more than 10 s to notice the process exited.")
            return 1
        live = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        try:
            held = run_keel(verify, "shift", "await-clear", "--pid", str(live.pid), "--timeout-ms", "500", env=env)
        finally:
            live.kill()
            live.wait()
        if held.returncode != 1:
            report(f"{label} await-clear on a live process did not exit 1: {held.returncode} {held.stdout.strip()} {held.stderr.strip()}")
            return 1
        if "not cleared" not in held.stdout:
            report(f"{label} await-clear on a live process did not say `not cleared`: {held.stdout.strip()}")
            return 1
        desktop = {**env, "KEEL_SHIFT_WAKE_TIMEOUT_MS": "2000", "CLAUDE_CODE_ENTRYPOINT": "claude-desktop",
                   "CLAUDE_CODE_HOST_SESSION_ID": "local_test-319", "KEEL_SHIFT_DESKTOP_PID": "4242"}
        armed = run_keel(verify, "shift", "ready", "--wake", "verify note: next is R031", env=desktop)
        note = mailbox_common_dir(verify) / "keel-chat" / "shift" / "verify.md"
        if armed.returncode != 0:
            report(f"{label} a desktop ready --wake failed: {armed.stderr.strip()}")
            return 1
        if "Desktop process: 4242." not in note.read_text(encoding="utf-8"):
            report(f"{label} a desktop ready --wake does not record the desktop process.")
            return 1
    if "shift-await-clear" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("shift-await-clear scenario passed.")
    return 0


def validate_shift_start_desktop_scenario() -> int:
    """`keel shift start` names the wake step for a note written on the desktop app.

    A desktop session with no running process sees no chat record, so the
    start record alone wakes nobody there (#320, D1 of
    shift-start-desktop-wake). Elsewhere the output is unchanged.
    """
    label = "shift-start-desktop:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-start-desktop-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)
        desktop = {**env, "CLAUDE_CODE_ENTRYPOINT": "claude-desktop", "CLAUDE_CODE_HOST_SESSION_ID": "local_test-320", "KEEL_SHIFT_DESKTOP_PID": "4242"}
        ready = run_keel(verify, "shift", "ready", "verify note: next is R030", env=desktop)
        if ready.returncode != 0:
            report(f"{label} ready on the desktop app failed: {ready.stderr.strip()}")
            return 1
        started = run_keel(rtl, "shift", "start", "verify", env=env)
        if started.returncode != 0:
            report(f"{label} start failed: {started.stderr.strip()}")
            return 1
        read = run_keel(verify, "chat", "read", "dm-rtl--verify", env=env)
        if "keel shift resume" not in read.stdout:
            report(f"{label} the start record did not reach dm-rtl--verify: {read.stdout.strip()} {read.stderr.strip()}")
            return 1
        for needle in ("send_message", "get_session", "unarchive_session", "local_test-320", "keel shift resume"):
            if needle not in started.stdout:
                report(f"{label} start for a desktop note does not name {needle}: {started.stdout.strip()}")
                return 1
        if "Woke" in started.stdout:
            report(f"{label} start for a desktop note still says it woke the role: {started.stdout.strip()}")
            return 1
        run_keel(verify, "shift", "resume", env=env)
        plain = run_keel(verify, "shift", "ready", "verify note: next is R031", env=env)
        if plain.returncode != 0:
            report(f"{label} ready outside the desktop app failed: {plain.stderr.strip()}")
            return 1
        other = run_keel(rtl, "shift", "start", "verify", env=env)
        if "Woke verify" not in other.stdout or "send_message" in other.stdout:
            report(f"{label} start for a note with no desktop session changed: {other.stdout.strip()}")
            return 1
    for relative, word in (("docs/shift-change.md", "#320"), ("docs/shift-change.zh-CN.md", "#320")):
        if word not in (ROOT / relative).read_text(encoding="utf-8"):
            report(f"{label} {relative} does not mention {word}.")
            return 1
    if "shift-start-desktop" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("shift-start-desktop scenario passed.")
    return 0


# A claude for the hand-over's host contract (#408): `agents --json` from a rows
# file, `stop` that drops the row's status and pid at once and ends the process
# a second later (`late`) or never (`never`), as measured on 2.1.304 (row 0.32 s,
# return 0.98 s, exit 3.2 s), `rm` that logs whether that process was still
# running, and a new session for `--bg`.
HANDOVER_CONTRACT_FAKE = """#!/usr/bin/env python3
import json, os, subprocess, sys
agents, calls, mode = os.environ['FAKE_AGENTS'], os.environ['FAKE_CALLS'], os.environ.get('FAKE_STOP_MODE', 'late')
argv = sys.argv[1:]
def running(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True
rows = json.loads(open(agents).read())
record = {'argv': argv}
if argv[:1] == ['rm']:
    gone = [row for row in rows if row['id'] == argv[1]]
    record['alive'] = bool(gone) and bool(gone[0].get('_pid')) and running(gone[0]['_pid'])
    rows = [row for row in rows if row['id'] != argv[1]]
open(calls, 'a').write(json.dumps(record) + '\\n')
if argv[:2] == ['agents', '--json']:
    print(json.dumps([{k: v for k, v in row.items() if not k.startswith('_')} for row in rows])); sys.exit(0)
if argv[:1] == ['stop']:
    for row in rows:
        if row['id'] == argv[1] and 'status' in row:
            pid = row.pop('pid', None); row.pop('status', None); row['state'] = 'stopped'; row['_pid'] = pid
            if pid and mode == 'late':
                subprocess.Popen(['sh', '-c', f'sleep 1; kill {pid}'], start_new_session=True,
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    open(agents, 'w').write(json.dumps(rows)); print('stopped ' + argv[1]); sys.exit(0)
if argv[:1] == ['--bg']:
    rows.append({'kind': 'background', 'name': 'verify', 'sessionId': 'newsess1-0000-0000-0000-000000000000', 'id': 'newsess1',
                 'status': 'busy', 'state': 'working', 'pid': os.getpid(), 'cwd': os.getcwd(), 'startedAt': 1792600000000})
    open(agents, 'w').write(json.dumps(rows)); print('backgrounded · newsess1 · verify'); sys.exit(0)
open(agents, 'w').write(json.dumps(rows)); print('ok')
"""


def detached_sleeper() -> int:
    """A process that is not this one's child, so a kill reaps it instead of leaving a zombie."""
    return int(subprocess.run(["sh", "-c", "sleep 600 >/dev/null 2>&1 & echo $!"], text=True,
                              capture_output=True, check=True).stdout.strip())


def validate_shift_cli_removes_after_exit_scenario() -> int:
    """Issue #408: a hand-over never removes a session whose process still runs.

    Measured on Claude Code 2.1.304 (2026-10-21): after `claude stop` the row
    loses `status` and `pid` at 0.32 s, the command returns at 0.98 s, and the
    process exits about 3.2 s in. Since #418 the session just handed over is
    removed by default, so the removal waits for the process the note recorded.
    """
    label = "shift-cli-removes-after-exit:"
    OLD = "5b14fbae-b6aa-40b6-a72a-b3f89d2c6eea"
    for mode in ("late", "never"):
        with tempfile.TemporaryDirectory(prefix="keel-shift-408a-") as raw:
            base = Path(raw)
            rtl, verify, env, _ = shift_scratch(base)
            agents, calls, fake, config = base / "agents.json", base / "calls.jsonl", base / "fake-claude", base / "claude"
            write_text(fake, HANDOVER_CONTRACT_FAKE)
            fake.chmod(0o755)
            write_text(config / "projects" / host_project_name(verify) / f"{OLD}.jsonl",
                       json.dumps({"type": "user", "message": {"role": "user", "content": "carry on"}}) + "\n")
            process = detached_sleeper()
            try:
                agents.write_text(json.dumps([{"kind": "background", "name": "verify", "sessionId": OLD, "id": OLD[:8],
                                               "status": "idle", "state": "done", "pid": process, "cwd": str(verify),
                                               "startedAt": 1792500000000}]))
                calls.write_text("")
                env = {**env, "KEEL_CLAUDE": str(fake), "CLAUDE_CONFIG_DIR": str(config), "FAKE_AGENTS": str(agents),
                       "FAKE_CALLS": str(calls), "FAKE_STOP_MODE": mode, "KEEL_SHIFT_HANDOVER_TIMEOUT_MS": "1",
                       "KEEL_SHIFT_EXIT_WAIT_MS": "5000" if mode == "late" else "1500"}
                cli_env = {**env, "CLAUDE_CODE_ENTRYPOINT": "cli", "CLAUDE_CODE_SESSION_ID": OLD, "CLAUDE_PID": str(process)}
                readied = run_keel(verify, "shift", "ready", "--wake", "next: rerun R030", env=cli_env)
                if readied.returncode != 0:
                    report(f"{label} ready --wake failed: {readied.stderr!r}")
                    return 1
                run_keel(verify, "tick", "--repo", str(rtl), env=env)
                removals = [json.loads(line) for line in calls.read_text().splitlines() if json.loads(line)["argv"][:1] == ["rm"]]
                status = run_keel(rtl, "shift", "status", env=env).stdout
                if mode == "late":
                    if [r["argv"][1] for r in removals] != [OLD[:8]]:
                        report(f"{label} the hand-over did not remove the session just handed over once its process exited: {removals!r}")
                        return 1
                    if removals[0]["alive"]:
                        report(f"{label} `claude rm` of the session just handed over ran while its process was still running.")
                        return 1
                else:
                    if removals:
                        report(f"{label} a session whose process never exited was removed: {removals!r}")
                        return 1
                    if f"claude attach {OLD[:8]}" not in status:
                        report(f"{label} shift status does not say the old session is kept for `claude attach`: {status!r}")
                        return 1
            finally:
                with contextlib.suppress(OSError):
                    os.kill(process, signal.SIGKILL)
    if label.rstrip(":") not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report(f"{label.rstrip(':')} scenario passed.")
    return 0


def validate_shift_cli_names_host_failure_scenario() -> int:
    """Issue #408: a hand-off the host cannot be asked about says why it waits."""
    label = "shift-cli-names-host-failure:"
    OLD = "5b14fbae-b6aa-40b6-a72a-b3f89d2c6eea"
    for case, needle in (("missing", "claude was not found"), ("garbled", "agents --json")):
        with tempfile.TemporaryDirectory(prefix="keel-shift-408b-") as raw:
            base = Path(raw)
            rtl, verify, env, _ = shift_scratch(base)
            claude = base / "no-claude"
            if case == "garbled":
                write_text(claude, "#!/bin/sh\necho 'not a list'\n")
                claude.chmod(0o755)
            env = {**env, "KEEL_CLAUDE": str(claude), "KEEL_SHIFT_HANDOVER_TIMEOUT_MS": "1"}
            cli_env = {**env, "CLAUDE_CODE_ENTRYPOINT": "cli", "CLAUDE_CODE_SESSION_ID": OLD, "CLAUDE_PID": str(os.getpid())}
            readied = run_keel(verify, "shift", "ready", "--wake", "next: rerun R031", env=cli_env)
            if readied.returncode != 0:
                report(f"{label} ready --wake failed ({case}): {readied.stderr!r}")
                return 1
            run_keel(verify, "tick", "--repo", str(rtl), env=env)
            status = run_keel(rtl, "shift", "status", env=env).stdout
            if "pending" not in status:
                report(f"{label} the hand-off is no longer pending ({case}): {status!r}")
                return 1
            if needle not in status:
                report(f"{label} shift status does not name why the hand-off waits ({case}, expected {needle!r}): {status!r}")
                return 1
    if label.rstrip(":") not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report(f"{label.rstrip(':')} scenario passed.")
    return 0


def validate_tick_retries_failed_wake_scenario() -> int:
    """Issue #408: a tick retries a failed wake a bounded number of times.

    A tick marked the role woken whether or not the resume worked, so one
    failure was never retried; a removed session is not tried again either.
    """
    label = "tick-retries-failed-wake:"
    for case in ("failing", "removed"):
        with tempfile.TemporaryDirectory(prefix="keel-tick-408c-") as raw:
            base = Path(raw)
            rtl, verify, env, _ = shift_scratch(base)
            calls = base / "calls.jsonl"
            fake = base / "fake-claude"
            listed = "['sess-verify-1']" if case == "failing" else "['other-0000']"
            write_text(fake, "#!/usr/bin/env python3\nimport json, sys\n"
                       f"open({str(calls)!r}, 'a').write(json.dumps(sys.argv[1:]) + '\\n')\n"
                       "if sys.argv[1:3] == ['agents', '--json']:\n"
                       f"    print(json.dumps([{{'kind': 'background', 'sessionId': s, 'id': s[:8]}} for s in {listed}])); sys.exit(0)\n"
                       "if sys.argv[1:2] == ['--bg']:\n    print('Workspace not trusted.', file=sys.stderr); sys.exit(1)\n")
            fake.chmod(0o755)
            env = {**env, "KEEL_CLAUDE": str(fake)}
            dead = subprocess.Popen(["true"])
            dead.wait()
            chat_session_start(verify, env, "sess-verify-1", dead.pid)
            run_keel(rtl, "chat", "dm", "verify", "rerun R032", env=env)
            for _ in range(4):
                run_keel(verify, "tick", "--repo", str(rtl), env=env)
            made = [json.loads(line) for line in calls.read_text().splitlines()] if calls.exists() else []
            resumes = [call for call in made if call[:2] == ["--bg", "--resume"]]
            lookups = [call for call in made if call[:2] == ["agents", "--json"]]
            if case == "failing" and len(resumes) != 3:
                report(f"{label} four ticks tried a failing resume {len(resumes)} times, not 3.")
                return 1
            if case == "removed" and resumes:
                report(f"{label} a removed session was resumed: {resumes!r}")
                return 1
            if case == "removed" and len(lookups) != 1:
                report(f"{label} four ticks looked up a removed session {len(lookups)} times, not once.")
                return 1
    if label.rstrip(":") not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report(f"{label.rstrip(':')} scenario passed.")
    return 0


HANDOVER_RETRY_FAKE = """#!/usr/bin/env python3
import json, os, sys, time
agents, calls = os.environ['FAKE_AGENTS'], os.environ['FAKE_CALLS']
argv = sys.argv[1:]
def load():
    return json.loads(open(agents).read())
def save(rows):
    tmp = agents + '.' + str(os.getpid())
    open(tmp, 'w').write(json.dumps(rows)); os.replace(tmp, agents)
open(calls, 'a').write(json.dumps({'argv': argv}) + '\\n')
if argv[:2] == ['agents', '--json']:
    print(json.dumps([{k: v for k, v in row.items() if not k.startswith('_')} for row in load()])); sys.exit(0)
if argv[:1] == ['stop']:
    rows = load()
    for row in rows:
        if row['id'] == argv[1] and 'status' in row:
            row.pop('status', None); pid = row.pop('pid', None); row['state'] = 'stopped'
            if pid:
                try:
                    os.kill(pid, 9)
                except OSError:
                    pass
    save(rows); print('stopped ' + argv[1]); sys.exit(0)
if argv[:1] == ['--bg'] and '--resume' not in argv:
    failing = os.environ.get('FAKE_BG_FAILS', '0')
    count = os.environ['FAKE_CALLS'] + '.starts'
    made = int(open(count).read()) if os.path.exists(count) else 0
    open(count, 'w').write(str(made + 1))
    if failing == 'always' or made < int(failing):
        print('Workspace not trusted.', file=sys.stderr); sys.exit(1)
    new = 'newsess%d-0000-0000-0000-000000000000' % (made + 1)
    rows = load()
    rows.append({'kind': 'background', 'name': argv[2], 'sessionId': new, 'id': new[:8], 'status': 'busy', 'state': 'working',
                 'pid': os.getpid(), 'cwd': os.getcwd(), 'startedAt': int(time.time() * 1000)})
    save(rows)
    time.sleep(float(os.environ.get('FAKE_BG_SLEEP', '0')))
    print('backgrounded · ' + new[:8] + ' · ' + argv[2]); sys.exit(0)
print('ok')
"""


def handover_retry_scratch(base: Path, old: str) -> dict:
    """A verify hand-off queued from an idle CLI session, against HANDOVER_RETRY_FAKE."""
    rtl, verify, env, _ = shift_scratch(base)
    agents, calls, fake = base / "agents.json", base / "calls.jsonl", base / "fake-claude"
    write_text(fake, HANDOVER_RETRY_FAKE)
    fake.chmod(0o755)
    process = detached_sleeper()
    agents.write_text(json.dumps([{"kind": "background", "name": "verify · 10-20 09:00", "sessionId": old, "id": old[:8],
                                   "status": "idle", "state": "done", "pid": process, "cwd": str(verify),
                                   "startedAt": 1792500000000}]))
    calls.write_text("")
    exited = subprocess.Popen(["true"])
    exited.wait()
    env = {**env, "KEEL_CLAUDE": str(fake), "FAKE_AGENTS": str(agents), "FAKE_CALLS": str(calls),
           "KEEL_SHIFT_HANDOVER_TIMEOUT_MS": "1", "KEEL_SHIFT_EXIT_WAIT_MS": "500"}
    cli_env = {**env, "CLAUDE_CODE_ENTRYPOINT": "cli", "CLAUDE_CODE_SESSION_ID": old, "CLAUDE_PID": str(exited.pid)}
    readied = run_keel(verify, "shift", "ready", "--wake", "next: rerun R040", env=cli_env)
    if readied.returncode != 0:
        raise RuntimeError(f"ready --wake failed: {readied.stderr!r}")
    queue = mailbox_common_dir(rtl) / "keel-chat" / "shift" / "queue" / "verify.json"

    def starts() -> int:
        return sum(1 for line in calls.read_text().splitlines()
                   if json.loads(line)["argv"][:1] == ["--bg"] and "--resume" not in json.loads(line)["argv"])

    return {"rtl": rtl, "verify": verify, "env": env, "agents": agents, "calls": calls, "queue": queue,
            "starts": starts, "process": process,
            "tick": lambda extra=None: run_keel(verify, "tick", "--repo", str(rtl), env={**env, **(extra or {})}),
            "keel": ["node", str(ROOT / "bin" / "keel.js")]}


def validate_shift_cli_handover_claims_once_scenario() -> int:
    """Issue #408, second loop: one pending hand-off starts one session.

    Runners claim the entry as `starting` before any host call (D1). So two
    ticks and a waiter running at the same moment start one session. A runner
    killed after `claude --bg` listed the new session is settled by adopting
    that session, not by starting another (D2, D3).
    """
    label = "shift-cli-handover-claims-once:"
    OLD = "5b14fbae-b6aa-40b6-a72a-b3f89d2c6eea"
    with tempfile.TemporaryDirectory(prefix="keel-shift-408c-") as raw:
        s = handover_retry_scratch(Path(raw), OLD)
        try:
            race = {**s["env"], "FAKE_BG_SLEEP": "1", "KEEL_SHIFT_HANDOVER_POLL_MS": "50", "KEEL_SHIFT_HANDOVER_TIMEOUT_MS": "8000"}
            runners = [subprocess.Popen([*s["keel"], "tick", "--repo", str(s["rtl"])], cwd=s["verify"], env=race,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for _ in range(2)]
            runners.append(subprocess.Popen([*s["keel"], "shift", "handover-wait", "--role", "verify", "--repo", str(s["verify"])],
                                            cwd=s["verify"], env=race, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            for runner in runners:
                runner.wait(timeout=60)
            entry = json.loads(s["queue"].read_text())
            if s["starts"]() != 1 or entry["state"] != "delivered":
                report(f"{label} two ticks and a waiter at once ran `claude --bg` {s['starts']()} times; the entry is {entry['state']}.")
                return 1
        finally:
            with contextlib.suppress(OSError):
                os.kill(s["process"], signal.SIGKILL)

    with tempfile.TemporaryDirectory(prefix="keel-shift-408d-") as raw:
        s = handover_retry_scratch(Path(raw), OLD)
        try:
            slow = {**s["env"], "FAKE_BG_SLEEP": "30"}
            runner = subprocess.Popen([*s["keel"], "tick", "--repo", str(s["rtl"])], cwd=s["verify"], env=slow,
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            deadline = time.time() + 20
            while s["starts"]() < 1 and time.time() < deadline:
                time.sleep(0.1)
            time.sleep(0.5)
            os.killpg(runner.pid, signal.SIGKILL)
            runner.wait()
            # The next tick comes minutes later, when any lock the dead runner left reads as stale.
            for lock in s["queue"].parent.glob("*.lock"):
                os.utime(lock, (time.time() - 600, time.time() - 600))
            s["tick"]()
            entry = json.loads(s["queue"].read_text())
            if s["starts"]() != 1:
                report(f"{label} a tick after the runner died mid-start ran `claude --bg` again: {s['starts']()} starts; the entry is {entry['state']}.")
                return 1
            if entry["state"] != "delivered" or not entry.get("adopted") or entry.get("new_session") != "newsess1":
                report(f"{label} the entry left by a runner that died mid-start was not delivered with the listed session: {entry!r}")
                return 1
        finally:
            with contextlib.suppress(OSError):
                os.kill(s["process"], signal.SIGKILL)
    if label.rstrip(":") not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report(f"{label.rstrip(':')} scenario passed.")
    return 0


def validate_shift_cli_retries_failed_handover_scenario() -> int:
    """Issue #408, second loop: a failed hand-off is retried within a bound (D4, D5).

    The tick makes up to three start attempts per entry. After the last one,
    status and the patrol name `keel chat wake now <role>`. The tick does not
    retry when the old session runs again, or when the entry predates the
    attempt count.
    """
    label = "shift-cli-retries-failed-handover:"
    OLD = "5b14fbae-b6aa-40b6-a72a-b3f89d2c6eea"
    for case in ("always", "third", "resumed", "legacy"):
        with tempfile.TemporaryDirectory(prefix="keel-shift-408e-") as raw:
            s = handover_retry_scratch(Path(raw), OLD)
            try:
                fails = {"FAKE_BG_FAILS": "2" if case == "third" else "always"}
                s["tick"](fails)
                if case == "resumed":
                    rows = json.loads(s["agents"].read_text())
                    rows[0].update({"status": "idle", "state": "done", "pid": s["process"]})
                    s["agents"].write_text(json.dumps(rows))
                if case == "legacy":
                    entry = json.loads(s["queue"].read_text())
                    entry.pop("attempts", None)
                    s["queue"].write_text(json.dumps(entry))
                for _ in range(4 if case in ("always", "third") else 2):
                    s["tick"](fails)
                entry = json.loads(s["queue"].read_text())
                status = run_keel(s["rtl"], "shift", "status", env=s["env"]).stdout
                if case == "always":
                    if s["starts"]() != 3:
                        report(f"{label} five ticks ran a failing `claude --bg` {s['starts']()} times, not 3.")
                        return 1
                    patrolled = run_keel(s["rtl"], "patrol", env=s["env"]).stdout
                    if entry["state"] != "failed":
                        report(f"{label} after three failed starts the entry is {entry['state']}, not failed.")
                        return 1
                    if "keel chat wake now verify" not in status:
                        report(f"{label} after three failed starts, shift status does not name `keel chat wake now verify`: {status!r}")
                        return 1
                    if "keel chat wake now verify" not in patrolled:
                        report(f"{label} after three failed starts, the patrol does not name `keel chat wake now verify`: {patrolled!r}")
                        return 1
                elif case == "third":
                    if s["starts"]() != 3 or entry["state"] != "delivered" or entry.get("new_session") != "newsess3":
                        report(f"{label} a start that fails twice was not delivered on the third attempt: {s['starts']()} starts, {entry!r}")
                        return 1
                elif s["starts"]() != 1 or entry["state"] != "failed":
                    report(f"{label} a failed hand-off was retried although {'its old session runs again' if case == 'resumed' else 'it records no attempts'}: {s['starts']()} starts, {entry['state']}.")
                    return 1
            finally:
                with contextlib.suppress(OSError):
                    os.kill(s["process"], signal.SIGKILL)
    if label.rstrip(":") not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report(f"{label.rstrip(':')} scenario passed.")
    return 0


def validate_shift_cli_self_shift_scenario() -> int:
    """Issues #357 and #388 on the CLI (owner, 2026-10-19): hand over, promptly, and retire.

    A CLI session cannot clear itself. `keel shift ready --wake` there queues
    the hand-off and leaves a waiter that, once the old session has finished,
    retires it (stop, rename by resuming it with `/rename`, stop) and starts a
    new session in the role's worktree that runs `keel shift resume`. `keel
    tick` carries out a queued hand-off too, and the two start one session. A
    session that is busy, or waiting for input (blocked on a question), is left
    alone; its job state is not read (#393). `keel shift status` shows the queue, and a
    failed start is a patrol risk.
    """
    label = "shift-cli-self-shift:"
    OLD = "5b14fbae-b6aa-40b6-a72a-b3f89d2c6eea"
    with tempfile.TemporaryDirectory(prefix="keel-shift-357-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)
        calls, agents, fail, norename = base / "claude-calls.jsonl", base / "agents.json", base / "fail-start", base / "no-rename"
        stoplag = base / "stop-lag"
        fake = base / "fake-claude"
        # The fake answers with the shapes measured on Claude Code 2.1.303: a live row has `status`, `state` and `pid`; a stopped one has `state: stopped` and neither.
        # `stop` drops the row's status at once and ends its process later (#397: 0.83 s against 2.68 s measured): about a second
        # later with `stop-lag` holding `late`, never with `never`, at once otherwise. A resume while the process runs starts a copy that takes the name.
        write_text(fake, "#!/usr/bin/env python3\nimport json, os, subprocess, sys\n"
                   f"agents, fail, norename, stoplag = {str(agents)!r}, {str(fail)!r}, {str(norename)!r}, {str(stoplag)!r}\n"
                   f"open({str(calls)!r}, 'a').write(json.dumps({{'argv': sys.argv[1:], 'cwd': os.getcwd(), 'claude_env': sorted(k for k in os.environ if k.startswith('CLAUDE'))}}) + '\\n')\n"
                   "argv = sys.argv[1:]\n"
                   "def running(pid):\n"
                   "    try:\n        os.kill(pid, 0)\n    except OSError:\n        return False\n    return True\n"
                   "rows = json.loads(open(agents).read())\n"
                   "if argv[:2] == ['agents', '--json']:\n"
                   "    print(json.dumps([{k: v for k, v in row.items() if not k.startswith('_')} for row in rows])); sys.exit(0)\n"
                   "if argv[:1] == ['stop']:\n"
                   "    lag = open(stoplag).read().strip() if os.path.exists(stoplag) else 'now'\n"
                   "    for row in rows:\n        if row['id'] == argv[1] and 'status' in row:\n"
                   "            pid = row.pop('pid', None); row.pop('status', None); row['state'] = 'stopped'; row['_pid'] = pid\n"
                   "            if pid and lag == 'now':\n                os.kill(pid, 15)\n"
                   "            elif pid and lag == 'late':\n                subprocess.Popen(['sh', '-c', f'sleep 1; kill {pid}'], start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
                   "    open(agents, 'w').write(json.dumps(rows)); print('stopped ' + argv[1]); sys.exit(0)\n"
                   "if argv[:2] == ['--bg', '--resume']:\n"
                   "    name = argv[3].split(None, 1)[1]\n"
                   "    live = [row for row in rows if row['sessionId'] == argv[2] and ('status' in row or (row.get('_pid') and running(row['_pid'])))]\n"
                   "    if live:\n"
                   "        copy = {k: v for k, v in live[0].items() if not k.startswith('_')}\n"
                   "        rows.append({**copy, 'sessionId': 'c0c0c0c0-0000-0000-0000-000000000000', 'id': 'c0c0c0c0', 'name': name, 'status': 'idle', 'state': 'working'})\n"
                   "        print('note: session ' + argv[2][:8] + ' is already running in the background, so this started a copy as c0c0c0c0.')\n"
                   "    for row in rows:\n        if row['sessionId'] == argv[2] and not live and not os.path.exists(norename):\n            row['name'] = name\n"
                   "    open(agents, 'w').write(json.dumps(rows)); print('backgrounded · ' + ('c0c0c0c0' if live else argv[2][:8])); sys.exit(0)\n"
                   "if argv[:1] == ['--bg'] and os.path.exists(fail):\n    print('Workspace not trusted.', file=sys.stderr); sys.exit(1)\n"
                   "if argv[:1] == ['--bg']:\n    print('backgrounded · newsess1 · verify'); sys.exit(0)\n"
                   "print('stopped')\n")
        fake.chmod(0o755)
        env = {**env, "KEEL_CLAUDE": str(fake), "KEEL_SHIFT_HANDOVER_POLL_MS": "200", "KEEL_SHIFT_HANDOVER_TIMEOUT_MS": "20000"}
        # With the waiter given no time, a hand-over is the tick's alone.
        tick_only = {**env, "KEEL_SHIFT_HANDOVER_TIMEOUT_MS": "1"}
        cli_env = {**env, "CLAUDE_CODE_ENTRYPOINT": "cli", "CLAUDE_CODE_SESSION_ID": OLD, "CLAUDE_PID": str(os.getpid())}
        queue = mailbox_common_dir(rtl) / "keel-chat" / "shift" / "queue"

        children: list[int] = []

        def end_children() -> None:
            for pid in children:
                with contextlib.suppress(OSError):
                    os.kill(pid, signal.SIGTERM)

        atexit.register(end_children)

        def agents_row(status: str | None, state: str, name: str = "verify") -> None:
            row = {"kind": "background", "name": name, "sessionId": OLD, "id": OLD[:8], "state": state, "cwd": str(verify)}
            if status:
                # The session's process: a real one, detached so that once killed it is reaped
                # rather than left a zombie the hand-over would still see running.
                started = subprocess.run(["sh", "-c", "sleep 600 >/dev/null 2>&1 & echo $!"], capture_output=True, text=True, check=True)
                children.append(int(started.stdout.strip()))
                row["status"] = status
                row["pid"] = children[-1]
            if status == "waiting":
                row["waitingFor"] = "input needed"
            agents.write_text(json.dumps([row]))

        def rows() -> list[dict]:
            return [json.loads(line) for line in calls.read_text().splitlines()] if calls.exists() else []

        def acted() -> list[list[str]]:
            return [r["argv"] for r in rows() if r["argv"][:2] != ["agents", "--json"]]

        def starts() -> list[dict]:
            return [r for r in rows() if r["argv"][:1] == ["--bg"] and "--resume" not in r["argv"]]

        def tick() -> subprocess.CompletedProcess[str]:
            return run_keel(verify, "tick", "--repo", str(rtl), env=tick_only)

        def status_text() -> str:
            return run_keel(rtl, "shift", "status", env=env).stdout

        def wait_for(condition, seconds: float = 10.0) -> bool:
            deadline = time.time() + seconds
            while time.time() < deadline:
                if condition():
                    return True
                time.sleep(0.2)
            return condition()

        agents_row("busy", "working")
        readied = run_keel(verify, "shift", "ready", "--wake", "next: rerun R012", env=cli_env)
        if readied.returncode != 0:
            report(f"{label} ready --wake in a CLI session failed: {readied.stdout!r} {readied.stderr!r}")
            return 1
        # #418: nothing is kept by default, so the old session is removed and read through Keel's copy.
        if "keel shift history verify --show" not in readied.stdout or "--wake" in readied.stderr:
            report(f"{label} ready --wake in a CLI session does not say how the old session is read once removed: {readied.stdout!r}")
            return 1
        note = next((mailbox_common_dir(rtl) / "keel-chat" / "shift").glob("verify.md"), None)
        if not note:
            report(f"{label} ready --wake stored no note for verify.")
            return 1
        if f"CLI session: {OLD}." not in note.read_text(encoding="utf-8"):
            report(f"{label} the note does not record the CLI session.")
            return 1

        # A busy session, and one blocked on a question (measured: status waiting, state blocked), are left alone.
        time.sleep(1.0)
        if acted():
            report(f"{label} the hand-over acted while the old session was busy: {acted()!r}")
            return 1
        if "pending" not in status_text():
            report(f"{label} shift status does not show the pending hand-off: {status_text()!r}")
            return 1
        agents_row("waiting", "blocked")
        time.sleep(1.0)
        if acted():
            report(f"{label} the hand-over cut off a session blocked on a question (status waiting): {acted()!r}")
            return 1

        # Finished: idle, though its state still labels its last message `working` (#393, keel-maint's
        # ended turn). The waiter stops it and starts the next, named for its start, with no tick (#399).
        agents_row("idle", "working")
        if not wait_for(lambda: len(starts()) >= 1):
            report(f"{label} the waiter did not hand over without a tick: {acted()!r}")
            return 1
        order = acted()
        if any(argv[:2] == ["--bg", "--resume"] for argv in order):
            report(f"{label} the hand-over woke the old session to rename it: {order!r}")
            return 1
        if order[:1] != [["stop", OLD[:8]]] or len(order) != 2:
            report(f"{label} the old session was not retired as one stop before the new start: {order!r}")
            return 1
        named = re.compile(r"^verify · \d{2}-\d{2} \d{2}:\d{2}$")
        if order[1][:2] != ["--bg", "-n"] or not named.match(order[1][2]) or order[1][3:5] != ["--permission-mode", "auto"]:
            report(f"{label} the new session is not started as `verify · <MM-DD HH:MM>`: {order[1]!r}")
            return 1
        if "keel shift resume" not in order[1][-1] or "--resume" in order[1]:
            report(f"{label} the new session does not start fresh with a keel shift resume prompt: {order[1]!r}")
            return 1
        if os.path.realpath(starts()[0]["cwd"]) != os.path.realpath(verify):
            report(f"{label} the new session started in {starts()[0]['cwd']}, not verify's worktree.")
            return 1
        leaked = [r for r in rows() if r["claude_env"]]
        if leaked:
            report(f"{label} a claude the hand-over ran inherited the old session's {leaked[0]['claude_env']!r}.")
            return 1
        text = status_text()
        for needle in ("delivered", "newsess1", f"claude attach {OLD[:8]}", order[1][2]):
            if needle not in text:
                report(f"{label} shift status does not show {needle!r} for the delivered hand-off: {text!r}")
                return 1
        tick()
        if len(starts()) != 1 or len(acted()) != 2:
            report(f"{label} a tick after the hand-over acted again: {acted()!r}")
            return 1

        # The tick and the waiter start one session: a fresh lock holds the tick off.
        calls.write_text("")
        agents_row("idle", "done")
        run_keel(verify, "shift", "ready", "--wake", "next: rerun R014", env={**cli_env, "KEEL_SHIFT_HANDOVER_TIMEOUT_MS": "1"})
        lock = queue / "verify.lock"
        write_text(lock, "held")
        tick()
        if acted():
            report(f"{label} a tick acted while another hand-over held the lock: {acted()!r}")
            return 1
        lock.unlink()
        tick()
        if len(starts()) != 1:
            report(f"{label} the tick did not start one session once the lock was gone: {acted()!r}")
            return 1
        tick()
        if len(starts()) != 1:
            report(f"{label} a second tick started another session.")
            return 1

        # A start that fails stays visible and is a patrol risk.
        calls.write_text("")
        agents_row("idle", "done")
        write_text(fail, "x")
        run_keel(verify, "shift", "ready", "--wake", "next: rerun R013", env={**cli_env, "KEEL_SHIFT_HANDOVER_TIMEOUT_MS": "1"})
        tick()
        text = status_text()
        for needle in ("failed", "Workspace not trusted"):
            if needle not in text:
                report(f"{label} a failed start does not show {needle!r}: {text!r}")
                return 1
        patrolled = run_keel(rtl, "patrol", env=env).stdout
        if not re.search(r"risk: .*verify.*hand-off", patrolled):
            report(f"{label} the patrol does not report the failed hand-off as a risk: {patrolled!r}")
            return 1
    if "shift-cli-self-shift" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("shift-cli-self-shift scenario passed.")
    return 0


def validate_shift_cli_keeps_old_sessions_scenario() -> int:
    """Issue #397 (owner, 2026-10-20): each CLI shift leaves a stopped session, and the list kept growing.

    After a delivered hand-over, the newest `shift: keep_old_sessions:`
    (default 0 since #418, so the shift just handed over goes too) stopped background sessions in the role's bound worktrees stay
    listed; each older one is removed with `claude rm` once Keel's store holds
    a copy of its transcript. Only a session with a transcript, the host's or
    Keel's copy, counts (#401): one whose transcript is nowhere takes no slot and
    stays, and so do another role's sessions and the new one.
    """
    label = "shift-cli-keeps-old-sessions:"
    OLD = "5b14fbae-b6aa-40b6-a72a-b3f89d2c6eea"
    with tempfile.TemporaryDirectory(prefix="keel-shift-397-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)
        calls, agents = base / "claude-calls.jsonl", base / "agents.json"
        config_dir = base / "claude-config"
        kept_dir = mailbox_common_dir(rtl) / "keel-chat" / "shift" / "transcripts" / "verify"
        fake = base / "fake-claude"
        # Shapes measured on Claude Code 2.1.303: a live row has `status` and `pid`, a stopped one neither (#397 F3);
        # `rm` drops the row and leaves the transcript (F4). Each `rm` logs whether Keel's copy was there when it ran.
        write_text(fake, "#!/usr/bin/env python3\nimport json, os, sys\n"
                   f"agents, kept = {str(agents)!r}, {str(kept_dir)!r}\n"
                   "argv = sys.argv[1:]\n"
                   "rows = json.loads(open(agents).read())\n"
                   "record = {'argv': argv}\n"
                   "if argv[:1] == ['rm']:\n"
                   "    gone = [row for row in rows if row['id'] == argv[1]]\n"
                   "    record['kept'] = bool(gone) and os.path.exists(os.path.join(kept, gone[0]['sessionId'] + '.jsonl.gz'))\n"
                   "    rows = [row for row in rows if row['id'] != argv[1]]\n"
                   f"open({str(calls)!r}, 'a').write(json.dumps(record) + '\\n')\n"
                   "if argv[:2] == ['agents', '--json']:\n    print(json.dumps(rows)); sys.exit(0)\n"
                   "if argv[:1] == ['stop']:\n"
                   "    for row in rows:\n        if row['id'] == argv[1]:\n            row.pop('status', None); row.pop('pid', None); row['state'] = 'stopped'\n"
                   "if argv[:1] == ['--bg'] and '--resume' not in argv:\n"
                   "    rows.append({'kind': 'background', 'name': 'verify', 'sessionId': 'newsess1-0000-0000-0000-000000000000', 'id': 'newsess1',\n"
                   "                 'status': 'busy', 'state': 'working', 'pid': os.getpid(), 'cwd': os.getcwd(), 'startedAt': 1792500000000})\n"
                   "    open(agents, 'w').write(json.dumps(rows)); print('backgrounded · newsess1 · verify'); sys.exit(0)\n"
                   "open(agents, 'w').write(json.dumps(rows)); print('ok'); sys.exit(0)\n")
        fake.chmod(0o755)
        env = {**env, "KEEL_CLAUDE": str(fake), "CLAUDE_CONFIG_DIR": str(config_dir), "KEEL_SHIFT_HANDOVER_TIMEOUT_MS": "1"}
        # The process the note records has exited by the time the hand-over removes the session,
        # as on the host; #408 makes the removal wait for it.
        exited = subprocess.Popen(["true"])
        exited.wait()
        cli_env = {**env, "CLAUDE_CODE_ENTRYPOINT": "cli", "CLAUDE_CODE_SESSION_ID": OLD, "CLAUDE_PID": str(exited.pid)}
        roles = json.loads((mailbox_common_dir(rtl) / "keel-chat" / "roles.json").read_text(encoding="utf-8"))
        bound = {role: path for path, role in roles.items()}

        def transcript(cwd: str, session: str, said: str) -> None:
            project = config_dir / "projects" / re.sub(r"[^A-Za-z0-9]", "-", cwd)
            project.mkdir(parents=True, exist_ok=True)
            (project / f"{session}.jsonl").write_text("\n".join(json.dumps(record) for record in (
                {"type": "user", "timestamp": "2026-10-19T01:00:00.000Z", "cwd": cwd, "message": {"role": "user", "content": "carry on"}},
                {"type": "assistant", "timestamp": "2026-10-19T01:00:05.000Z", "cwd": cwd,
                 "message": {"role": "assistant", "content": [{"type": "text", "text": said}]}},
            )) + "\n", encoding="utf-8")

        def old_row(n: int, cwd: str, with_transcript: bool = True) -> dict:
            session = f"0{n}0{n}0{n}0{n}-0000-0000-0000-00000000000{n}"
            if with_transcript:
                transcript(cwd, session, f"old shift {n}")
            return {"kind": "background", "name": "verify", "sessionId": session, "id": session[:8], "state": "stopped",
                    "cwd": cwd, "startedAt": 1792400000000 + n * 1000}

        def setup(keep: str | None, olds: list[dict]) -> None:
            calls.write_text("")
            config = verify / "keel" / "config.yaml"
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text(f"shift:\n  keep_old_sessions: {keep}\n" if keep is not None else "", encoding="utf-8")
            subprocess.run(["git", "add", "keel/config.yaml"], cwd=verify, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", f"keep {keep}"], cwd=verify, check=True, capture_output=True)
            subprocess.run(["git", "push", "-q", "origin", "HEAD"], cwd=verify, check=True, capture_output=True)
            transcript(bound["verify"], OLD, "the shift handing over")
            live = {"kind": "background", "name": "verify", "sessionId": OLD, "id": OLD[:8], "status": "idle", "state": "working",
                    "cwd": bound["verify"], "startedAt": 1792490000000}
            agents.write_text(json.dumps([*olds, live]))
            readied = run_keel(verify, "shift", "ready", "--wake", "next: rerun R020", env=cli_env)
            if readied.returncode != 0:
                raise RuntimeError(f"ready --wake failed: {readied.stderr!r}")
            run_keel(verify, "tick", "--repo", str(rtl), env=env)

        def removed() -> list[dict]:
            return [json.loads(line) for line in calls.read_text().splitlines() if json.loads(line)["argv"][:1] == ["rm"]]

        # #401: a session never given a prompt has no transcript and is not a shift, so it takes no kept slot even
        # when it is newer than the others; one whose host transcript is gone but Keel holds a copy still counts.
        copy_only = old_row(1, bound["verify"], with_transcript=False)
        kept_dir.mkdir(parents=True, exist_ok=True)
        (kept_dir / f"{copy_only['sessionId']}.jsonl.gz").write_bytes(gzip.compress(b'{"type": "user"}\n'))
        olds = [copy_only, old_row(2, bound["verify"]), old_row(3, bound["verify"]), old_row(4, bound["verify"]),
                old_row(6, bound["verify"], with_transcript=False), old_row(5, bound["rtl"])]
        setup("2", olds)
        gone = removed()
        if not gone:
            report(f"{label} the hand-over removed no old session: {calls.read_text()!r}")
            return 1
        ids = sorted(r["argv"][1] for r in gone)
        if ids != ["01010101", "02020202", "03030303"]:
            report(f"{label} with keep_old_sessions 2 the removed sessions are {ids!r}, "
                   "not the oldest beyond the two newest with a transcript.")
            return 1
        if not all(r["kept"] for r in gone):
            report(f"{label} a session was removed before Keel's store held its transcript: {gone!r}")
            return 1
        left = {row["id"] for row in json.loads(agents.read_text())}
        for keep_id, why in (("06060606", "the session with no transcript"), ("05050505", "rtl's session"),
                             ("newsess1", "the new session"), (OLD[:8], "the shift just handed over"), ("04040404", "the second newest old session")):
            if keep_id not in left:
                report(f"{label} {why} ({keep_id}) was removed: {sorted(left)!r}")
                return 1
        text = run_keel(rtl, "shift", "status", env=env).stdout
        if "01010101" not in text or "02020202" not in text:
            report(f"{label} shift status does not name the removed sessions: {text!r}")
            return 1

        # #418 (owner, 2026-10-21): no declaration keeps none, so the shift just handed over leaves the
        # session list too; a value that is not a whole number is named and none are kept.
        for keep in (None, "many"):
            olds = [old_row(1, bound["verify"]), old_row(2, bound["verify"]), old_row(4, bound["verify"])]
            setup(keep, olds)
            ids = sorted(r["argv"][1] for r in removed())
            if ids != sorted(["01010101", "02020202", "04040404", OLD[:8]]):
                report(f"{label} the default keeps the wrong number of old sessions (keep_old_sessions {keep!r}): removed {ids!r}")
                return 1
            if not all(r["kept"] for r in removed()):
                report(f"{label} a session was removed before Keel's store held its transcript: {removed()!r}")
                return 1
            if f"keel shift history verify --show {OLD[:8]}" not in run_keel(rtl, "shift", "status", env=env).stdout:
                report(f"{label} shift status does not say how the removed old shift is read: {run_keel(rtl, 'shift', 'status', env=env).stdout!r}")
                return 1
            if keep == "many" and "keep_old_sessions" not in run_keel(rtl, "shift", "status", env=env).stdout:
                report(f"{label} an unreadable keep_old_sessions is not named: {run_keel(rtl, 'shift', 'status', env=env).stdout!r}")
                return 1
    if "shift-cli-keeps-old-sessions" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("shift-cli-keeps-old-sessions scenario passed.")
    return 0


def validate_shift_history_show_scenario() -> int:
    """Issue #397 (owner, 2026-10-20): a shift no longer in `claude agents` can be read in full.

    `keel shift history <role> --show <id>` prints the whole conversation of the
    segment whose transcript name starts with the id — prompts, replies, tool
    calls and results, in order and in full — from the host's file or, once that
    is gone, Keel's kept copy. An id that names no segment exits 1.
    """
    label = "shift-history-show:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-show-") as raw:
        base = Path(raw)
        rtl, verify, env, _ = shift_scratch(base)
        roles = json.loads((mailbox_common_dir(rtl) / "keel-chat" / "roles.json").read_text(encoding="utf-8"))
        bound = next(path for path, role in roles.items() if role == "verify")
        project = base / "claude-config" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", bound)
        project.mkdir(parents=True)
        env = {**env, "CLAUDE_CONFIG_DIR": str(base / "claude-config")}
        session = "4162aee5-7549-4801-b52f-871d553bdb5a"
        long_reply = "The arbiter keeps read priority over refresh. " * 12 + "End of the long reply."
        records = (
            {"type": "user", "timestamp": "2026-10-14T15:35:29.000Z", "cwd": bound, "message": {"role": "user", "content": "rerun R012 and report"}},
            {"type": "assistant", "timestamp": "2026-10-14T15:35:40.000Z", "cwd": bound,
             "message": {"role": "assistant", "content": [{"type": "text", "text": long_reply},
                                                          {"type": "tool_use", "id": "toolu_1", "name": "Bash", "input": {"command": "make sim R012"}}]}},
            {"type": "user", "timestamp": "2026-10-14T15:36:02.000Z", "cwd": bound,
             "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_1", "content": "R012 PASS 4096/4096 vectors"}]}},
        )
        old = project / f"{session}.jsonl"
        old.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

        def hook(path: Path) -> None:
            for event, name in (("session-start", "SessionStart"), ("user-prompt-submit", "UserPromptSubmit")):
                subprocess.run(
                    ["node", str(ROOT / "bin" / "keel.js"), "chat", "hook", event],
                    cwd=verify, env=env, text=True, capture_output=True, check=False,
                    input=json.dumps({"cwd": str(verify), "hook_event_name": name, "session_id": "s1",
                                      "prompt": "go", "source": "startup", "transcript_path": str(path)}),
                )

        # The next shift's segments make Keel keep the old transcript; then the host's file goes.
        for name in ("a", "b"):
            path = project / f"{name}.jsonl"
            path.write_text(json.dumps({"type": "user", "timestamp": "2026-10-15T01:00:00.000Z", "cwd": bound,
                                        "message": {"role": "user", "content": "carry on"}}) + "\n", encoding="utf-8")
            hook(path)
        old.unlink()
        shown = run_keel(verify, "shift", "history", "verify", "--show", session[:8], env=env)
        if shown.returncode != 0:
            report(f"{label} --show of a kept shift exited {shown.returncode}: {shown.stdout!r} {shown.stderr!r}")
            return 1
        if "rerun R012 and report" not in shown.stdout:
            report(f"{label} --show printed no conversation: {shown.stdout!r} {shown.stderr!r}")
            return 1
        if session not in shown.stdout or "2026-10-14" not in shown.stdout.splitlines()[0]:
            report(f"{label} --show's header does not name the transcript and its time span: {shown.stdout.splitlines()[:2]!r}")
            return 1
        if long_reply not in shown.stdout:
            report(f"{label} --show cut the assistant's reply short: {shown.stdout!r}")
            return 1
        order = [shown.stdout.find(text) for text in ("rerun R012 and report", long_reply, "make sim R012", "R012 PASS 4096/4096 vectors")]
        if -1 in order:
            report(f"{label} --show leaves out the prompt, reply, tool call or result: {order!r} {shown.stdout!r}")
            return 1
        if order != sorted(order):
            report(f"{label} --show does not print the prompt, reply, tool call and result in order: {order!r} {shown.stdout!r}")
            return 1
        if "Bash" not in shown.stdout:
            report(f"{label} --show does not name the tool called: {shown.stdout!r}")
            return 1

        unknown = run_keel(verify, "shift", "history", "verify", "--show", "00000000", env=env)
        if unknown.returncode != 1:
            report(f"{label} --show of an unknown id did not exit 1: {unknown.returncode} {unknown.stdout!r} {unknown.stderr!r}")
            return 1
        if "no segment" not in (unknown.stdout + unknown.stderr).lower():
            report(f"{label} --show of an unknown id does not say no segment matches: {unknown.stdout!r} {unknown.stderr!r}")
            return 1
    if "shift-history-show" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("shift-history-show scenario passed.")
    return 0


def validate_shift_desktop_wake_overdue_scenario() -> int:
    """`keel shift status` flags a desktop note whose wake is overdue.

    A wake task that never runs leaves no trace anywhere else; the waiting
    note with its recorded desktop session is the one place a coordinator or
    patrol can see it (D2 of shift-desktop-wake-confirm).
    """
    label = "shift-desktop-wake-overdue:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-overdue-") as raw:
        base = Path(raw)
        _rtl, verify, env, _ = shift_scratch(base)
        env = {**env, "KEEL_SHIFT_WAKE_TIMEOUT_MS": "2000"}
        desktop = {**env, "CLAUDE_CODE_ENTRYPOINT": "claude-desktop", "CLAUDE_CODE_HOST_SESSION_ID": "local_test-319"}
        armed = run_keel(verify, "shift", "ready", "--wake", "verify note: next is R021", env=desktop)
        if armed.returncode != 0:
            report(f"{label} ready --wake on the desktop app failed: {armed.stderr.strip()}")
            return 1
        young = run_keel(verify, "shift", "status", env={**env, "KEEL_SHIFT_WAKE_OVERDUE_MS": "3600000"})
        if "overdue" in young.stdout:
            report(f"{label} a note written just now is already called overdue: {young.stdout.strip()}")
            return 1
        late = run_keel(verify, "shift", "status", env={**env, "KEEL_SHIFT_WAKE_OVERDUE_MS": "0"})
        for needle in ("overdue", "local_test-319", "list_task_runs", "send_message"):
            if needle not in late.stdout:
                report(f"{label} status past the overdue time does not name {needle}: {late.stdout.strip()}")
                return 1
        # Without the override the overdue time is three minutes (D4 of
        # shift-desktop-wake-in-a-minute).
        note = mailbox_common_dir(verify) / "keel-chat" / "shift" / "verify.md"
        for minutes, flagged in ((2, False), (4, True)):
            then = time.time() - minutes * 60
            os.utime(note, (then, then))
            row = run_keel(verify, "shift", "status", env=env)
            if ("overdue" in row.stdout) != flagged:
                report(f"{label} a desktop note written {minutes} minutes ago is {'not ' if flagged else ''}flagged overdue by default: {row.stdout.strip()}")
                return 1
        run_keel(verify, "shift", "resume", env=env)
        plain = run_keel(verify, "shift", "ready", "--wake", "verify note: next is R022", env=env)
        if plain.returncode != 0:
            report(f"{label} ready --wake outside the desktop app failed: {plain.stderr.strip()}")
            return 1
        other = run_keel(verify, "shift", "status", env={**env, "KEEL_SHIFT_WAKE_OVERDUE_MS": "0"})
        if "overdue" in other.stdout:
            report(f"{label} a note with no desktop session is called overdue: {other.stdout.strip()}")
            return 1
    for relative, word in (("docs/shift-change.md", "overdue"), ("docs/shift-change.zh-CN.md", "超时")):
        if word not in (ROOT / relative).read_text(encoding="utf-8"):
            report(f"{label} {relative} does not say {word}.")
            return 1
    if "shift-desktop-wake-overdue" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("shift-desktop-wake-overdue scenario passed.")
    return 0


def validate_shift_desktop_wake_scenario() -> int:
    """Issue #319: on the desktop app a clear starts no session until a prompt.

    `ready --wake` there records the session id and prints the partner recipe
    (a one-shot scheduled task that `send_message`s the session, which turns
    Remote Control back on first) instead of promising the waiter wakes it;
    `resume` there says to restore Remote Control. Elsewhere nothing changes.
    """
    label = "shift-desktop-wake:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-desktop-") as raw:
        base = Path(raw)
        _rtl, verify, env, _ = shift_scratch(base)
        env = {**env, "KEEL_SHIFT_WAKE_TIMEOUT_MS": "2000"}
        # The pid is pinned so the scenario does not depend on running under a `claude` process (CI does not).
        desktop = {**env, "CLAUDE_CODE_ENTRYPOINT": "claude-desktop", "CLAUDE_CODE_HOST_SESSION_ID": "local_test-319", "KEEL_SHIFT_DESKTOP_PID": "4242"}
        note = mailbox_common_dir(verify) / "keel-chat" / "shift" / "verify.md"

        armed = run_keel(verify, "shift", "ready", "--wake", "verify note: next is R011", env=desktop)
        if armed.returncode != 0:
            report(f"{label} ready --wake on the desktop app failed: {armed.stderr.strip()}")
            return 1
        if "Desktop session: local_test-319" not in note.read_text(encoding="utf-8"):
            report(f"{label} the note does not record the desktop session id.")
            return 1
        # Remote Control stays on: a clear is accepted with it on, and turning it
        # off waits for a person's approval (#324 comments 6164793777, 6165454422).
        for needle in ('set_remote_control("self", false)', "cannot be cleared"):
            if needle in armed.stdout:
                report(f"{label} the desktop clear hint still says {needle}: {armed.stdout.strip()}")
                return 1
        # The task, then rename and clear at once, so the wake cannot fire
        # before the clear (#319 comments 6143435530, 6144856601).
        for needle in ("create_scheduled_task", "send_message", "local_test-319", "set_session_title",
                       "mcp__ccd_session_mgmt__set_remote_control", "shift-restore"):
            if needle not in armed.stdout:
                report(f"{label} the desktop clear hint does not name {needle}: {armed.stdout.strip()}")
                return 1
        task = armed.stdout.find("create_scheduled_task")
        if not task < armed.stdout.find("set_session_title", task) < armed.stdout.find("clear_session", task):
            report(f"{label} the desktop clear hint does not order create_scheduled_task, set_session_title, clear_session: {armed.stdout.strip()}")
            return 1
        if "new address" not in armed.stdout:
            report(f"{label} the desktop clear hint does not say Remote Control reconnects under a new address: {armed.stdout.strip()}")
            return 1
        # Dismissing bound PRs did not keep the app's auto-archive off the
        # cleared session: the engine archives on every PR the session ever
        # had, and `get_status` cannot see that set (#326 comment 6163697376).
        for needle in ("unbind_pr", "get_status"):
            if needle in armed.stdout:
                report(f"{label} the desktop clear hint still names {needle}: {armed.stdout.strip()}")
                return 1
        # The wake unarchives first, then sends (#326 D2 of shift-desktop-unarchive-wake).
        for needle in ("get_session", "unarchive_session", "mcp__ccd_session_mgmt__get_session",
                       "mcp__ccd_session_mgmt__unarchive_session"):
            if needle not in armed.stdout:
                report(f"{label} the desktop clear hint does not name {needle}: {armed.stdout.strip()}")
                return 1
        look = armed.stdout.find("get_session")
        if not look < armed.stdout.find("unarchive_session") < armed.stdout.find("send_message", look):
            report(f"{label} the wake does not check get_session, then unarchive_session, then send_message: {armed.stdout.strip()}")
            return 1
        # The wake starts at once and waits for the clear itself, so no minute
        # tick sits in the shift (D3 of shift-desktop-wake-in-a-minute).
        for needle in ("await-clear", "run_scheduled_task", "keel-shift-wake-verify",
                       "mcp__scheduled-tasks__run_scheduled_task"):
            if needle not in armed.stdout:
                report(f"{label} the desktop clear hint does not name {needle}: {armed.stdout.strip()}")
                return 1
        for needle in ("fireAt", "three minutes"):
            if needle in armed.stdout:
                report(f"{label} the desktop clear hint still schedules the wake ({needle}): {armed.stdout.strip()}")
                return 1
        made = armed.stdout.find("create_scheduled_task")
        run = armed.stdout.find("run_scheduled_task", made + 1)
        if not made < run < armed.stdout.find("set_session_title", run) < armed.stdout.find("clear_session", run):
            report(f"{label} the desktop clear hint does not order create, run_scheduled_task, rename, clear: {armed.stdout.strip()}")
            return 1
        waits = armed.stdout.find("await-clear")
        if not waits < armed.stdout.find("get_session", waits) < armed.stdout.find("send_message", waits):
            report(f"{label} the wake does not await the clear before get_session and send_message: {armed.stdout.strip()}")
            return 1
        # The wake confirms delivery: anything but delivered or queued after the
        # archived retry is a failed wake the owner hears about (D1 of
        # shift-desktop-wake-confirm).
        for needle in ("PushNotification", "WAKE FAILED", "delivered"):
            if needle not in armed.stdout[armed.stdout.find("send_message"):]:
                report(f"{label} the desktop wake does not say {needle} after send_message: {armed.stdout.strip()}")
                return 1
        if "archived copy" in armed.stdout:
            report(f"{label} the desktop clear hint still says the rename tells an archived copy apart: {armed.stdout.strip()}")
            return 1
        if "mcp__ccd_session_mgmt__clear_session" in armed.stdout:
            report(f"{label} the desktop clear hint still blames approval of clear_session: {armed.stdout.strip()}")
            return 1
        if "The wake is armed" in armed.stdout:
            report(f"{label} the desktop clear hint still says the waiter wakes the new session: {armed.stdout.strip()}")
            return 1
        resumed = run_keel(verify, "shift", "resume", env=desktop)
        if "next is R011" not in resumed.stdout:
            report(f"{label} resume on the desktop app did not print the note: {resumed.stdout.strip()} {resumed.stderr.strip()}")
            return 1
        if "set_remote_control" not in resumed.stdout or "get_session" not in resumed.stdout:
            report(f"{label} resume on the desktop app does not say to check Remote Control and turn it back on if off: {resumed.stdout.strip()}")
            return 1
        if "set_session_title" not in resumed.stdout:
            report(f"{label} resume on the desktop app does not say to rename the session back: {resumed.stdout.strip()}")
            return 1

        plain = run_keel(verify, "shift", "ready", "--wake", "verify note: next is R012", env=env)
        if plain.returncode != 0:
            report(f"{label} ready --wake outside the desktop app failed: {plain.stderr.strip()}")
            return 1
        if "The wake is armed" not in plain.stdout:
            report(f"{label} outside the desktop app the clear hint no longer says the wake is armed: {plain.stdout.strip()}")
            return 1
        for needle in ("send_message", "create_scheduled_task", "set_session_title", "shift-restore",
                       "unbind_pr", "get_session", "unarchive_session"):
            if needle in plain.stdout:
                report(f"{label} outside the desktop app the clear hint names {needle}: {plain.stdout.strip()}")
                return 1
        if "Desktop session:" in note.read_text(encoding="utf-8"):
            report(f"{label} a note written outside the desktop app records a desktop session.")
            return 1
        again = run_keel(verify, "shift", "resume", env=env)
        if "set_remote_control" in again.stdout or "set_session_title" in again.stdout:
            report(f"{label} resume outside the desktop app names the desktop restore: {again.stdout.strip()}")
            return 1

    for relative in ("docs/shift-change.md", "docs/shift-change.zh-CN.md"):
        text = (ROOT / relative).read_text(encoding="utf-8")
        for stale in ("unbind_pr", "cannot be cleared"):
            if stale in text:
                report(f"{label} {relative} still says {stale}.")
                return 1
        for needle in ("send_message", "set_remote_control", "set_session_title", "shift-restore",
                       "get_session", "unarchive_session", "PushNotification", "WAKE FAILED",
                       "await-clear", "run_scheduled_task"):
            if needle not in text:
                report(f"{label} {relative} does not name {needle} for the desktop app.")
                return 1
    if "shift-desktop-wake" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("shift-desktop-wake scenario passed.")
    return 0


def validate_shift_without_role_scenario() -> int:
    """Owner's remark of 2026-10-05: a shift change needs no chat role.

    In a worktree with no `keel chat` role, `ready` keeps the note per
    worktree, `keel context` and the SessionStart projection point to it
    without changing the context's status, and `resume` consumes it.
    """
    label = "shift-without-role:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-norole-") as raw:
        base = Path(raw)
        repo = mailbox_repository(base / "solo")
        env = chat_environment()
        common = mailbox_common_dir(repo) / "keel-chat"

        def context() -> dict:
            return chat_json(run_keel(repo, "context", "--json", env=env))

        before = context().get("status")
        # Issue #317: nothing wakes the session after a clear here, so plain
        # `ready` is refused and points to a role and --wake.
        plain = run_keel(repo, "shift", "ready", "next: rerun R007", env=env)
        if plain.returncode != 1:
            report(f"{label} plain ready in a worktree without a chat role exited {plain.returncode}, not 1: {plain.stdout.strip()}")
            return 1
        if "keel chat role --set" not in plain.stderr:
            report(f"{label} the refusal does not name `keel chat role --set`: {plain.stderr.strip()}")
            return 1
        if "--wake" not in plain.stderr:
            report(f"{label} the refusal does not name --wake: {plain.stderr.strip()}")
            return 1
        if list((common / "shift" / "worktree").glob("*.md")):
            report(f"{label} the refused ready stored a worktree note.")
            return 1
        ready = run_keel(repo, "shift", "ready", "--force-reason", "the owner opens it", "next: rerun R007", env=env)
        if ready.returncode != 0:
            report(f"{label} keel shift ready --force-reason refused in a worktree without a chat role: {ready.stderr.strip()}")
            return 1
        if "the owner opens it" not in ready.stdout:
            report(f"{label} the clear hint does not name who starts the new session: {ready.stdout.strip()}")
            return 1
        notes = list((common / "shift" / "worktree").glob("*.md"))
        if len(notes) != 1:
            report(f"{label} ready kept {len(notes)} worktree notes under keel-chat/shift/worktree/, not one.")
            return 1
        if "Started by hand: the owner opens it" not in notes[0].read_text(encoding="utf-8"):
            report(f"{label} the note does not record who starts the new session.")
            return 1
        if "Left as is" in notes[0].read_text(encoding="utf-8"):
            report(f"{label} the note lists loose ends left as is when the check found none.")
            return 1
        text = run_keel(repo, "context", env=env).stdout
        if "keel shift resume" not in text:
            report(f"{label} keel context does not point to the waiting note: {text.strip()}")
            return 1
        if context().get("status") != before:
            report(f"{label} the waiting note changed the context status from {before!r} to {context().get('status')!r}.")
            return 1
        session = run_session_start_hook(
            repo, {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(repo)},
            keel_cli=f'node "{ROOT / "bin" / "keel.js"}"',
        )
        if "keel shift resume" not in (session_start_context(session) or ""):
            report(f"{label} the SessionStart projection does not point to the waiting note.")
            return 1
        resumed = run_keel(repo, "shift", "resume", env=env)
        if "rerun R007" not in resumed.stdout:
            report(f"{label} keel shift resume did not print the note: {resumed.stdout.strip()} {resumed.stderr.strip()}")
            return 1
        if notes[0].exists():
            report(f"{label} resume left the worktree note waiting.")
            return 1
        if not list((common / "shift" / "history").glob("*.md")):
            report(f"{label} resume did not keep the note in history.")
            return 1
        if "keel shift resume" in run_keel(repo, "context", env=env).stdout:
            report(f"{label} keel context still points to a note already resumed.")
            return 1

        # Issue #261: `--file -` is stdin, and an unreadable file is a named refusal.
        missing = base / "missing-note.md"
        refused = run_keel(repo, "shift", "ready", "--force-reason", "the owner opens it", "--file", str(missing), env=env)
        if re.search(r"^\s+at ", refused.stderr, re.M):
            report(f"{label} an unreadable --file escaped as an uncaught exception: {refused.stderr.strip()}")
            return 1
        if refused.returncode != 1:
            report(f"{label} an unreadable --file exited {refused.returncode}, not 1: {refused.stderr.strip()}")
            return 1
        if not refused.stderr.startswith("keel shift:"):
            report(f"{label} an unreadable --file was not refused as a keel shift error: {refused.stderr.strip()}")
            return 1
        if str(missing) not in refused.stderr:
            report(f"{label} the refusal of an unreadable --file does not name the path: {refused.stderr.strip()}")
            return 1
        piped = subprocess.run(
            ["node", str(ROOT / "bin" / "keel.js"), "shift", "ready", "--force-reason", "the owner opens it", "--file", "-"],
            cwd=repo, env=env, input="next: from stdin via --file -\n",
            text=True, encoding="utf-8", errors="replace", capture_output=True, check=False,
        )
        if piped.returncode != 0:
            report(f"{label} keel shift ready --file - failed: {piped.stderr.strip()}")
            return 1
        notes = list((common / "shift" / "worktree").glob("*.md"))
        if len(notes) != 1:
            report(f"{label} keel shift ready --file - kept {len(notes)} worktree notes, not one.")
            return 1
        if "from stdin via --file -" not in notes[0].read_text(encoding="utf-8"):
            report(f"{label} the note stored by keel shift ready --file - lacks the text given on stdin.")
            return 1

    for relative, needle in (("docs/shift-change.md", "no chat role"), ("docs/shift-change.zh-CN.md", "不绑定聊天角色")):
        text = (ROOT / relative).read_text(encoding="utf-8")
        if needle not in text:
            report(f"{label} {relative} does not say a chat role is optional ({needle!r}).")
            return 1
        intro = text.split("## ", 1)[0]
        if "--wake" not in intro:
            report(f"{label} {relative} does not say an unbound self-shift needs --wake.")
            return 1
        if "--force-reason" not in intro:
            report(f"{label} {relative} does not say --force-reason files an unbound self-shift by hand.")
            return 1
    if "shift-without-role" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("shift-without-role scenario passed.")
    return 0


def per_worktree_change(repo: Path, name: str, *, blocked: bool = False, owner: str | None = None) -> None:
    """An actionable change; `blocked` drops its evidence-first Reason so it cannot compile."""
    tasks = task_capsule_compact_fixture()
    if blocked:
        tasks = "".join(line for line in tasks.splitlines(keepends=True) if "- Reason:" not in line)
    write_text(repo / f"openspec/changes/{name}/proposal.md", f"## Why\n\n{name}.\n\n## What Changes\n\n- {name}.\n")
    write_text(repo / f"openspec/changes/{name}/tasks.md", tasks)
    if owner:
        write_text(repo / f"openspec/changes/{name}/.openspec.yaml", f"schema: spec-driven\nkeel:\n  owner: {owner}\n")


def validate_context_per_worktree_scenario() -> int:
    """Issue #241: a change that belongs to another worktree is context here.

    Ownership is the change's `owner:` role first, then committed branch
    history beyond the default branch; a change belonging elsewhere is listed
    and does not set this session's status. Explicit selection still reaches it.
    """
    label = "context-per-worktree:"
    with tempfile.TemporaryDirectory(prefix="keel-context-worktree-") as raw:
        base = Path(raw)
        main = mailbox_repository(base / "main")
        per_worktree_change(main, "broken", blocked=True)
        per_worktree_change(main, "owned", owner="verify")
        subprocess.run(["git", "add", "-A"], cwd=main, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", "changes"], cwd=main, check=True, capture_output=True)
        rtl = chat_worktree(main, base / "rtl")
        verify = chat_worktree(main, base / "verify")
        review = chat_worktree(main, base / "review")
        env = chat_environment()
        for cwd, role in ((rtl, "rtl"), (verify, "verify"), (review, "review")):
            run_keel(cwd, "chat", "role", "--set", role, env=env)
        (rtl / "openspec/changes/broken/proposal.md").write_text("## Why\n\nbroken, edited on rtl.\n\n## What Changes\n\n- broken.\n", encoding="utf-8")
        subprocess.run(["git", "commit", "-q", "-am", "edit broken"], cwd=rtl, check=True, capture_output=True)

        def context(cwd: Path, *args: str) -> dict:
            result = run_keel(cwd, "context", "--json", *args, env=env)
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"error": (result.stdout or result.stderr).strip()}

        here = context(review)
        if here.get("status") != "idle":
            report(f"{label} review is {here.get('status')!r}, not idle: {here}")
            return 1
        elsewhere = {e.get("change"): e for e in here.get("elsewhere", [])}
        broken = elsewhere.get("broken", {})
        if broken.get("status") != "blocked":
            report(f"{label} review does not list broken as blocked: {here.get('elsewhere')!r}")
            return 1
        if broken.get("worktree") != str(rtl.resolve()):
            report(f"{label} review does not place broken in worktree rtl: {here.get('elsewhere')!r}")
            return 1
        if elsewhere.get("owned", {}).get("owner") != "verify":
            report(f"{label} review does not list owned as belonging to verify: {here.get('elsewhere')!r}")
            return 1

        theirs = context(rtl)
        if theirs.get("status") != "blocked":
            report(f"{label} rtl is {theirs.get('status')!r}, not blocked by its own change: {theirs}")
            return 1
        if [e.get("change") for e in theirs.get("elsewhere", [])] != ["owned"]:
            report(f"{label} rtl does not list only owned as elsewhere: {theirs.get('elsewhere')!r}")
            return 1

        owner = context(verify)
        if (owner.get("selection") or {}).get("change") != "owned":
            report(f"{label} verify does not select its owned change: {owner}")
            return 1
        if owner.get("status") != "ready":
            report(f"{label} verify's owned change is {owner.get('status')!r}, not ready: {owner}")
            return 1

        explicit = context(review, "--change", "broken")
        if (explicit.get("selection") or {}).get("change") != "broken" and explicit.get("status") != "blocked":
            report(f"{label} explicit selection in review did not reach broken: {explicit}")
            return 1
    report("context-per-worktree scenario passed.")
    return 0


def validate_session_role_identity_scenario() -> int:
    """Issue #245: the chat role is the session's identity.

    `keel context` carries the bound role and the SessionStart projection
    names it; an unbound worktree among bound ones is reminded; a repository
    with no roles is unchanged.
    """
    label = "session-role-identity:"
    with tempfile.TemporaryDirectory(prefix="keel-role-identity-") as raw:
        base = Path(raw)
        repo = mailbox_repository(base / "repo")
        plain = mailbox_repository(base / "plain")
        # The SessionStart hook projects only where OpenSpec is present.
        for root in (repo, plain):
            write_text(root / "openspec/specs/.keep", "")
            subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-q", "-m", "openspec"], cwd=root, check=True, capture_output=True)
        rtl = chat_worktree(repo, base / "rtl")
        loose = chat_worktree(repo, base / "loose")
        env = chat_environment()
        run_keel(rtl, "chat", "role", "--set", "rtl", env=env)

        def both(cwd: Path) -> tuple[dict, str]:
            context = json.loads(run_keel(cwd, "context", "--json", env=env).stdout)
            session = run_session_start_hook(
                cwd, {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(cwd)},
                keel_cli=f'node "{ROOT / "bin" / "keel.js"}"',
            )
            return context, session_start_context(session) or ""

        context, note = both(rtl)
        if context.get("role") != "rtl":
            report(f"{label} rtl's context carries role {context.get('role')!r}, not 'rtl'.")
            return 1
        if "chat role: rtl" not in note:
            report(f"{label} rtl's projection does not name its role: {note!r}")
            return 1

        context, note = both(loose)
        if context.get("role") is not None:
            report(f"{label} the unbound worktree carries role {context.get('role')!r}.")
            return 1
        if not any("keel chat role --set" in w for w in context.get("warnings", [])):
            report(f"{label} the unbound worktree is not reminded: {context.get('warnings')!r}")
            return 1
        if "keel chat role --set" not in note:
            report(f"{label} the unbound worktree's projection carries no reminder: {note!r}")
            return 1

        context, note = both(plain)
        if "role" not in context:
            report(f"{label} a role-less repository's context has no role field: {context}")
            return 1
        if context.get("role") is not None:
            report(f"{label} a role-less repository carries role {context.get('role')!r}.")
            return 1
        if any("keel chat role --set" in w for w in context.get("warnings", [])):
            report(f"{label} a role-less repository is warned: {context.get('warnings')!r}")
            return 1
        if "chat role:" in note:
            report(f"{label} a role-less repository's projection has a role line: {note!r}")
            return 1
    report("session-role-identity scenario passed.")
    return 0


def validate_idle_recent_issues_scenario() -> int:
    """Issue #278: an idle result points at the issues the branch referenced.

    From Git alone, newest first and without repeats, in a separate field the
    session projection prints; nothing on the default branch.
    """
    label = "idle-recent-issues:"
    with tempfile.TemporaryDirectory(prefix="keel-idle-recent-") as raw:
        base = Path(raw)
        repo = mailbox_repository(base / "repo")
        write_text(repo / "openspec/specs/.keep", "")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", "openspec"], cwd=repo, check=True, capture_output=True)
        work = chat_worktree(repo, base / "work")
        for message in ("fix the lock lease (#162)", "context per worktree, #182", "follow-up for #162"):
            subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", message], cwd=work, check=True, capture_output=True)

        def look(cwd: Path) -> tuple[dict, str]:
            context = json.loads(run_keel(cwd, "context", "--json").stdout)
            session = run_session_start_hook(
                cwd, {"hook_event_name": "SessionStart", "source": "compact", "cwd": str(cwd)},
                keel_cli=f'node "{ROOT / "bin" / "keel.js"}"',
            )
            return context, session_start_context(session) or ""

        on_main, main_note = look(repo)
        context, note = look(work)
        if context.get("status") != "idle":
            report(f"{label} the worktree is {context.get('status')!r}, not idle.")
            return 1
        if (context.get("recent") or {}).get("issues") != [162, 182]:
            report(f"{label} recent is {context.get('recent')!r}, not issues [162, 182].")
            return 1
        if context.get("reasons") != on_main.get("reasons"):
            report(f"{label} recent issues changed the reasons: {context.get('reasons')!r}")
            return 1
        if "recently referenced: #162, #182" not in note:
            report(f"{label} the projection does not print the recent issues: {note!r}")
            return 1
        if "recent" in on_main:
            report(f"{label} the default branch carries recent: {on_main.get('recent')!r}")
            return 1
        if "recently referenced" in main_note:
            report(f"{label} the default branch's projection prints recent issues: {main_note!r}")
            return 1
    report("idle-recent-issues scenario passed.")
    return 0


def validate_read_only_role_scenario() -> int:
    """Issue #246: a role listed in `read_only_roles:` infers nothing.

    `keel context` reports one idle line naming the role, the session note
    stops asking to select an owner, a malformed entry is reported, and
    explicit selection still works.
    """
    label = "read-only-role:"
    with tempfile.TemporaryDirectory(prefix="keel-read-only-") as raw:
        repo = mailbox_repository(Path(raw) / "repo")
        per_worktree_change(repo, "first")
        per_worktree_change(repo, "second")
        write_authorize_config(repo, "read_only_roles:\n  - review\n  - Not A Role\n")
        env = chat_environment()
        run_keel(repo, "chat", "role", "--set", "review", env=env)
        result = run_keel(repo, "context", "--json", env=env)
        try:
            context = json.loads(result.stdout)
        except json.JSONDecodeError:
            report(f"{label} keel context printed no JSON: {result.stdout} {result.stderr}")
            return 1
        if context.get("status") != "idle":
            report(f"{label} a read-only role is {context.get('status')!r}, not idle: {context}")
            return 1
        reasons = context.get("reasons", [])
        if len(reasons) != 1:
            report(f"{label} the read-only result has {len(reasons)} reasons, not one: {reasons!r}")
            return 1
        if "review" not in reasons[0]:
            report(f"{label} the read-only reason does not name review: {reasons!r}")
            return 1
        if (context.get("readOnly") or {}).get("role") != "review":
            report(f"{label} the result carries no readOnly naming review: {context.get('readOnly')!r}")
            return 1
        if not any("Not A Role" in warning for warning in context.get("warnings", [])):
            report(f"{label} the malformed entry is not reported: {context.get('warnings')!r}")
            return 1
        session = run_session_start_hook(
            repo, {"hook_event_name": "SessionStart", "source": "compact", "cwd": str(repo)},
            keel_cli=f'node "{ROOT / "bin" / "keel.js"}"',
        )
        note = session_start_context(session) or ""
        if "read-only session (role review)" not in note:
            report(f"{label} the compaction note does not name the read-only session: {note!r}")
            return 1
        if "select an owner" in note:
            report(f"{label} the compaction note still asks a read-only session to select an owner: {note!r}")
            return 1
        explicit = json.loads(run_keel(repo, "context", "--json", "--change", "first", env=env).stdout)
        if (explicit.get("selection") or {}).get("change") != "first":
            report(f"{label} explicit selection in a read-only session did not select first: {explicit}")
            return 1
    report("read-only-role scenario passed.")
    return 0


def validate_stateless_continuity_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-context-") as raw_tmp:
        root = Path(raw_tmp)
        repo = root / "explicit"
        repo.mkdir()
        write_text(
            repo / "openspec/changes/demo/tasks.md",
            task_contract_fixture(),
        )

        explicit = run_keel(
            repo,
            "context",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if explicit.returncode != 0:
            report("stateless-continuity scenario could not resolve an explicit task.")
            report((explicit.stderr or explicit.stdout).strip())
            return 1
        try:
            payload = json.loads(explicit.stdout)
        except json.JSONDecodeError:
            report("stateless-continuity scenario expected keel context --json output.")
            report(explicit.stdout.strip())
            return 1
        expected = {
            "schemaVersion": 1,
            "status": "ready",
            "selection": {
                "source": "explicit",
                "change": "demo",
                "task": "1.1",
            },
        }
        expected_kind = "task-start"
        if payload.get("nextAction", {}).get("kind") != expected_kind:
            report(
                "stateless-continuity scenario explicit selection reported "
                f"next action {payload.get('nextAction')!r}."
            )
            return 1
        for key, value in expected.items():
            if payload.get(key) != value:
                report(
                    "stateless-continuity scenario explicit selection mismatch: "
                    f"{key}={payload.get(key)!r}"
                )
                return 1

        write_text(
            repo / "openspec/changes/other/tasks.md",
            "# Tasks\n\n## Invalidates\n\n- None.\n\n- [ ] 1.1 Other task\n",
        )
        write_text(
            repo / "keel/HANDOFF.md",
            "---\n"
            "schema: keel-handoff/v1\n"
            "owner: openspec/changes/other/tasks.md#1.1\n"
            "action: task-start\n"
            "reason: Explicit precedence fixture\n"
            "---\n",
        )
        explicit_again = run_keel(
            repo,
            "context",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        explicit_again_payload = json.loads(explicit_again.stdout)
        if (
            explicit_again.returncode != 0
            or explicit_again_payload.get("selection")
            != {"source": "explicit", "change": "demo", "task": "1.1"}
        ):
            report("stateless-continuity scenario did not prioritize explicit selection.")
            report((explicit_again.stderr or explicit_again.stdout).strip())
            return 1

        inferred_repo = root / "inferred"
        inferred_repo.mkdir()
        tasks_path = inferred_repo / "openspec/changes/only/tasks.md"
        write_text(
            tasks_path,
            task_contract_fixture() + "- [ ] 1.2 Second slice\n",
        )
        before_context = snapshot_files(inferred_repo)
        inferred = run_keel(inferred_repo, "context", "--json")
        after_context = snapshot_files(inferred_repo)
        if inferred.returncode != 0:
            report("stateless-continuity scenario could not infer a unique task.")
            report((inferred.stderr or inferred.stdout).strip())
            return 1
        inferred_payload = json.loads(inferred.stdout)
        if (
            inferred_payload.get("status") != "ready"
            or inferred_payload.get("selection")
            != {"source": "inferred", "change": "only", "task": "1.1"}
            or inferred_payload.get("nextAction", {}).get("kind") != "task-start"
        ):
            report("stateless-continuity scenario unique inference mismatch.")
            report(inferred.stdout.strip())
            return 1
        if before_context != after_context:
            report("stateless-continuity scenario persisted context state.")
            return 1

        write_text(
            tasks_path,
            "# Tasks\n\n## Invalidates\n\n- None.\n\n"
            "- [x] 1.1 First slice\n"
            "- [x] 1.2 Second slice\n",
        )
        recomputed = run_keel(inferred_repo, "context", "--json")
        recomputed_payload = json.loads(recomputed.stdout)
        if (
            recomputed.returncode != 0
            or recomputed_payload.get("status") != "ready"
            or recomputed_payload.get("selection")
            != {"source": "inferred", "change": "only", "task": None}
            or recomputed_payload.get("nextAction", {}).get("kind")
            != "change-close"
        ):
            report("stateless-continuity scenario did not recompute completed state.")
            report((recomputed.stderr or recomputed.stdout).strip())
            return 1

        evidence_repo = root / "evidence"
        evidence_repo.mkdir()
        write_text(
            evidence_repo / "openspec/changes/evidence-ready/tasks.md",
            task_contract_fixture(evidence=("M1: passed",)).replace(
                "      - Status: pending\n",
                "      - Status: pass\n",
            ),
        )
        evidence_ready = run_keel(evidence_repo, "context", "--json")
        evidence_payload = json.loads(evidence_ready.stdout)
        if (
            evidence_ready.returncode != 0
            or evidence_payload.get("nextAction", {}).get("kind") != "task-complete"
        ):
            report("stateless-continuity scenario missed evidence-ready completion.")
            report((evidence_ready.stderr or evidence_ready.stdout).strip())
            return 1

        ambiguous_repo = root / "ambiguous"
        ambiguous_repo.mkdir()
        for change in ("alpha", "beta"):
            write_text(
                ambiguous_repo / f"openspec/changes/{change}/tasks.md",
                task_contract_fixture(),
            )
        write_text(ambiguous_repo / "src/unrelated.txt", "dirty warning\n")
        git_init = subprocess.run(
            ["git", "init", "--quiet"],
            cwd=ambiguous_repo,
            capture_output=True,
            text=True,
            check=False,
        )
        if git_init.returncode != 0:
            report("stateless-continuity scenario could not initialize Git fixture.")
            return 1
        ambiguous = run_keel(ambiguous_repo, "context", "--json")
        ambiguous_payload = json.loads(ambiguous.stdout)
        if (
            ambiguous.returncode != 0
            or ambiguous_payload.get("status") != "ambiguous"
            or ambiguous_payload.get("selection") is not None
            or not any("alpha" in reason and "beta" in reason for reason in ambiguous_payload.get("reasons", []))
            or not any("src/unrelated.txt" in warning for warning in ambiguous_payload.get("warnings", []))
        ):
            report("stateless-continuity scenario guessed among multiple candidates.")
            report((ambiguous.stderr or ambiguous.stdout).strip())
            return 1

        write_text(
            ambiguous_repo / "keel/HANDOFF.md",
            "---\n"
            "schema: keel-handoff/v1\n"
            "owner: openspec/changes/beta/tasks.md#1.1\n"
            "action: task-start\n"
            "reason: Human selected beta\n"
            "---\n",
        )
        handoff = run_keel(ambiguous_repo, "context", "--json")
        handoff_payload = json.loads(handoff.stdout)
        if (
            handoff.returncode != 0
            or handoff_payload.get("status") != "ready"
            or handoff_payload.get("selection")
            != {"source": "handoff", "change": "beta", "task": "1.1"}
            or handoff_payload.get("nextAction", {}).get("kind") != "task-start"
        ):
            report("stateless-continuity scenario did not prioritize valid HANDOFF.")
            report((handoff.stderr or handoff.stdout).strip())
            return 1

        human = run_keel(ambiguous_repo, "context")
        for expected_text in (
            "Keel context: ready",
            "Next action: task-start",
            "Selection: beta#1.1 (handoff)",
        ):
            if human.returncode != 0 or expected_text not in human.stdout:
                report("stateless-continuity scenario human output diverged from JSON.")
                report((human.stderr or human.stdout).strip())
                return 1

        cleared = run_keel(
            ambiguous_repo,
            "context",
            "--clear-handoff",
            "--json",
        )
        cleared_payload = json.loads(cleared.stdout)
        if (
            cleared.returncode != 0
            or (ambiguous_repo / "keel/HANDOFF.md").exists()
            or cleared_payload.get("status") != "ambiguous"
        ):
            report("stateless-continuity scenario clear did not restore inference.")
            report((cleared.stderr or cleared.stdout).strip())
            return 1

        stale_repo = root / "stale"
        stale_repo.mkdir()
        write_text(
            stale_repo / "openspec/changes/current/tasks.md",
            "# Tasks\n\n## Invalidates\n\n- None.\n\n- [ ] 1.1 Current task\n",
        )
        write_text(
            stale_repo / "keel/HANDOFF.md",
            "---\n"
            "schema: keel-handoff/v1\n"
            "owner: openspec/changes/missing/tasks.md#1.1\n"
            "action: task-start\n"
            "reason: Stale fixture\n"
            "---\n",
        )
        stale = run_keel(stale_repo, "context", "--json")
        stale_payload = json.loads(stale.stdout)
        if (
            stale.returncode != 0
            or stale_payload.get("status") != "blocked"
            or stale_payload.get("selection") is not None
            or not any("missing" in reason.lower() for reason in stale_payload.get("reasons", []))
        ):
            report("stateless-continuity scenario stale HANDOFF fell through.")
            report((stale.stderr or stale.stdout).strip())
            return 1

        write_text(
            stale_repo / "openspec/changes/current/tasks.md",
            "# Tasks\n\n## Invalidates\n\n- None.\n\n- [x] 1.1 Current task\n",
        )
        write_text(
            stale_repo / "keel/HANDOFF.md",
            "---\n"
            "schema: keel-handoff/v1\n"
            "owner: openspec/changes/current/tasks.md#1.1\n"
            "action: task-start\n"
            "reason: Completed fixture\n"
            "---\n",
        )
        completed_owner = run_keel(stale_repo, "context", "--json")
        completed_payload = json.loads(completed_owner.stdout)
        if (
            completed_owner.returncode != 0
            or completed_payload.get("status") != "blocked"
            or not any(
                "already complete" in reason
                for reason in completed_payload.get("reasons", [])
            )
        ):
            report("stateless-continuity scenario accepted completed HANDOFF owner.")
            report((completed_owner.stderr or completed_owner.stdout).strip())
            return 1

        write_text(
            stale_repo / "openspec/changes/current/tasks.md",
            "# Tasks\n\n## Invalidates\n\n- None.\n\n- [ ] 1.1 Current task\n",
        )
        write_text(
            stale_repo / "keel/HANDOFF.md",
            "---\n"
            "schema: keel-handoff/v1\n"
            "owner: openspec/changes/current/tasks.md#1.1\n"
            "action: task-start\n"
            "reason: Extra-field fixture\n"
            "summary: copied state is forbidden\n"
            "---\n",
        )
        extra_field = run_keel(stale_repo, "context", "--json")
        if (
            extra_field.returncode != 0
            or json.loads(extra_field.stdout).get("status") != "blocked"
        ):
            report("stateless-continuity scenario accepted non-pointer HANDOFF state.")
            report((extra_field.stderr or extra_field.stdout).strip())
            return 1

        write_text(
            stale_repo / "keel/HANDOFF.md",
            "---\n"
            "schema: keel-handoff/v1\n"
            "owner: openspec/changes/current/tasks.md#1.1\n",
        )
        parse_failure = run_keel(stale_repo, "context", "--json")
        if (
            parse_failure.returncode == 0
            or "context input error" not in parse_failure.stderr
        ):
            report("stateless-continuity scenario did not expose HANDOFF parse failure.")
            report((parse_failure.stderr or parse_failure.stdout).strip())
            return 1

        discuss_repo = root / "discuss"
        discuss_repo.mkdir()
        write_text(
            discuss_repo / "openspec/changes/seed/notes.md",
            "# Discussion seed\n",
        )
        discuss = run_keel(discuss_repo, "context", "--json")
        if (
            discuss.returncode != 0
            or json.loads(discuss.stdout).get("nextAction", {}).get("kind") != "discuss"
        ):
            report("stateless-continuity scenario missed discuss transition.")
            report((discuss.stderr or discuss.stdout).strip())
            return 1

        author_repo = root / "author"
        author_repo.mkdir()
        write_text(
            author_repo / "openspec/changes/draft/proposal.md",
            "# Proposal\n",
        )
        author = run_keel(author_repo, "context", "--json")
        if (
            author.returncode != 0
            or json.loads(author.stdout).get("nextAction", {}).get("kind") != "author"
        ):
            report("stateless-continuity scenario missed author transition.")
            report((author.stderr or author.stdout).strip())
            return 1

        idle_repo = root / "idle"
        idle_repo.mkdir()
        write_text(idle_repo / ".codex/memories/native.md", "not authority\n")
        write_text(idle_repo / ".claude/goals/native.md", "not authority\n")
        before_idle = snapshot_files(idle_repo)
        idle = run_keel(idle_repo, "context", "--json")
        after_idle = snapshot_files(idle_repo)
        idle_payload = json.loads(idle.stdout)
        if (
            idle.returncode != 0
            or idle_payload.get("status") != "idle"
            or idle_payload.get("selection") is not None
            or idle_payload.get("nextAction", {}).get("kind") != "none"
        ):
            report("stateless-continuity scenario no-work state was not idle.")
            report((idle.stderr or idle.stdout).strip())
            return 1
        if before_idle != after_idle:
            report("stateless-continuity scenario changed native runtime state.")
            return 1

        install_repo = root / "install"
        install_repo.mkdir()
        installed = run_keel(install_repo, "--install", "--target", "codex")
        if installed.returncode != 0:
            report("stateless-continuity scenario install failed.")
            report((installed.stderr or installed.stdout).strip())
            return 1
        if (install_repo / "keel/HANDOFF.md").exists():
            report("stateless-continuity scenario new install created HANDOFF.")
            return 1
        installed_context = run_keel(install_repo, "context", "--json")
        if (
            installed_context.returncode != 0
            or json.loads(installed_context.stdout).get("status") != "idle"
        ):
            report("stateless-continuity scenario absent HANDOFF blocked inference.")
            report((installed_context.stderr or installed_context.stdout).strip())
            return 1

        init_repo = root / "init"
        init_repo.mkdir()
        initialized = run_keel(init_repo, "--init", "--target", "opencode")
        if (
            initialized.returncode != 0
            or (init_repo / "keel/HANDOFF.md").exists()
        ):
            report("stateless-continuity scenario new init created HANDOFF.")
            report((initialized.stderr or initialized.stdout).strip())
            return 1

        legacy_bytes = (
            "# HANDOFF\r\n\r\n"
            "active-change: preserve-me\r\n"
            "说明: 不要改写\r\n"
        ).encode("utf-8")
        legacy_path = install_repo / "keel/HANDOFF.md"
        legacy_path.parent.mkdir(parents=True, exist_ok=True)
        legacy_path.write_bytes(legacy_bytes)
        legacy_install = run_keel(install_repo, "--install", "--target", "codex")
        if (
            legacy_install.returncode != 0
            or legacy_path.read_bytes() != legacy_bytes
            or "handoff: legacy" not in legacy_install.stdout.lower()
        ):
            report("stateless-continuity scenario install did not preserve legacy HANDOFF.")
            report((legacy_install.stderr or legacy_install.stdout).strip())
            return 1
        legacy_check = run_keel(install_repo, "--check", "--target", "codex")
        if (
            legacy_check.returncode != 0
            or legacy_path.read_bytes() != legacy_bytes
            or "handoff: legacy" not in legacy_check.stdout.lower()
            or "keel context --clear-handoff" not in legacy_check.stdout
        ):
            report("stateless-continuity scenario check did not diagnose legacy HANDOFF.")
            report((legacy_check.stderr or legacy_check.stdout).strip())
            return 1
        legacy_doctor = run_keel(install_repo, "--doctor", "--target", "codex")
        if (
            legacy_doctor.returncode != 0
            or legacy_path.read_bytes() != legacy_bytes
            or "handoff: legacy" not in legacy_doctor.stdout.lower()
        ):
            report("stateless-continuity scenario doctor did not preserve legacy HANDOFF.")
            report((legacy_doctor.stderr or legacy_doctor.stdout).strip())
            return 1
        legacy_context = run_keel(install_repo, "context", "--json")
        legacy_payload = json.loads(legacy_context.stdout)
        if (
            legacy_context.returncode != 0
            or legacy_payload.get("status") != "blocked"
            or legacy_path.read_bytes() != legacy_bytes
        ):
            report("stateless-continuity scenario legacy context was not conservative.")
            report((legacy_context.stderr or legacy_context.stdout).strip())
            return 1

        backlog_repo = root / "backlog"
        backlog_repo.mkdir()
        write_text(
            backlog_repo / "openspec/changes/executable/tasks.md",
            task_contract_fixture(),
        )
        write_text(
            backlog_repo / "openspec/changes/follow-up-backlog/tasks.md",
            "# Follow-up Backlog\n\n## Deferred Items\n\nNone.\n",
        )
        backlog_context = run_keel(backlog_repo, "context", "--json")
        backlog_payload = json.loads(backlog_context.stdout)
        if (
            backlog_context.returncode != 0
            or backlog_payload.get("status") != "ready"
            or backlog_payload.get("selection")
            != {"source": "inferred", "change": "executable", "task": "1.1"}
            or not any(
                "follow-up-backlog" in warning
                for warning in backlog_payload.get("warnings", [])
            )
        ):
            report(
                "stateless-continuity scenario let a storage-only backlog create ambiguity."
            )
            report((backlog_context.stderr or backlog_context.stdout).strip())
            return 1

        anchor_repo = root / "anchor"
        anchor_repo.mkdir()
        anchor_tasks = task_contract_fixture()
        anchor_path = anchor_repo / "openspec/changes/demo/tasks.md"
        write_text(anchor_path, anchor_tasks)
        anchored_start = run_keel(
            anchor_repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        anchored_payload = json.loads(anchored_start.stdout)
        anchor = (
            anchored_payload.get("contract", {})
            .get("fingerprint", {})
            .get("value", "")
        )
        if anchored_start.returncode != 0 or not re.fullmatch(r"[0-9a-f]{64}", anchor):
            report("stateless-continuity scenario could not create a task anchor.")
            report((anchored_start.stderr or anchored_start.stdout).strip())
            return 1
        anchored_tasks = anchor_tasks.replace(
            "  - Evidence:\n",
            "  - Evidence:\n"
            f"    - Contract: keel-task-capsule/v1 sha256:{anchor}\n",
        )
        write_text(anchor_path, anchored_tasks)
        matching = run_keel(
            anchor_repo,
            "context",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        matching_payload = json.loads(matching.stdout)
        if (
            matching.returncode != 0
            or matching_payload.get("status") != "ready"
            or matching_payload.get("nextAction", {}).get("kind") != "task-start"
        ):
            report("stateless-continuity scenario did not resume a matching anchor.")
            report((matching.stderr or matching.stdout).strip())
            return 1

        write_text(
            anchor_path,
            anchored_tasks.replace("src/feature.js", "src/drifted-feature.js"),
        )
        drifted_context = run_keel(
            anchor_repo,
            "context",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        drifted_payload = json.loads(drifted_context.stdout)
        if (
            drifted_context.returncode != 0
            or drifted_payload.get("status") != "blocked"
            or not any(
                "fingerprint" in reason.lower() or "drift" in reason.lower()
                for reason in drifted_payload.get("reasons", [])
            )
        ):
            report("stateless-continuity scenario accepted a drifted task anchor.")
            report((drifted_context.stderr or drifted_context.stdout).strip())
            return 1

        drifted_projection = run_keel(
            anchor_repo,
            "project",
            "--target",
            "codex",
            "--event",
            "resume",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        drifted_projection_payload = json.loads(drifted_projection.stdout)
        if (
            drifted_projection.returncode != 0
            or drifted_projection_payload.get("status") != "blocked"
            or drifted_projection_payload.get("projection") is not None
        ):
            report("stateless-continuity scenario projected a drifted task anchor.")
            report(
                (drifted_projection.stderr or drifted_projection.stdout).strip()
            )
            return 1

        write_text(
            anchor_repo / "keel/HANDOFF.md",
            "---\n"
            "schema: keel-handoff/v1\n"
            "owner: openspec/changes/demo/tasks.md#1.1\n"
            "action: task-start\n"
            "reason: Handoff anchor fixture\n"
            "---\n",
        )
        drifted_handoff = run_keel(anchor_repo, "context", "--json")
        drifted_handoff_payload = json.loads(drifted_handoff.stdout)
        if (
            drifted_handoff.returncode != 0
            or drifted_handoff_payload.get("status") != "blocked"
            or not any(
                "fingerprint" in reason.lower() or "drift" in reason.lower()
                for reason in drifted_handoff_payload.get("reasons", [])
            )
        ):
            report("stateless-continuity scenario let HANDOFF bypass a drifted anchor.")
            report((drifted_handoff.stderr or drifted_handoff.stdout).strip())
            return 1

        write_text(anchor_path, anchored_tasks)
        matching_handoff = run_keel(anchor_repo, "context", "--json")
        matching_handoff_payload = json.loads(matching_handoff.stdout)
        if (
            matching_handoff.returncode != 0
            or matching_handoff_payload.get("status") != "ready"
            or matching_handoff_payload.get("selection")
            != {"source": "handoff", "change": "demo", "task": "1.1"}
            or matching_handoff_payload.get("nextAction", {}).get("kind") != "task-start"
        ):
            report("stateless-continuity scenario did not resume a matching HANDOFF anchor.")
            report((matching_handoff.stderr or matching_handoff.stdout).strip())
            return 1

    report("stateless-continuity scenario passed.")
    return 0


def validate_memory_rule_reaches_every_repo_scenario() -> int:
    """Issue #416 (owner, 2026-10-21): memory hygiene is part of the Keel protocol.

    A consuming repository carries only the bootstrap block, so the rule goes
    there: memory holds only what the next session would get wrong without it
    and the repository cannot answer, one fact per entry, rechecked after a
    fix, at a release and at a shift change. `keel shift check` reminds the
    session before the hand-off note, as a note that never blocks readiness.
    Keel reads no memory.
    """
    label = "memory-rule-reaches-every-repo:"
    with tempfile.TemporaryDirectory(prefix="keel-memory-416-") as raw:
        base = Path(raw)
        repo = base / "fresh"
        repo.mkdir()
        installed = run_keel(repo, "--install")
        if installed.returncode != 0:
            report(f"{label} keel --install failed: {(installed.stderr or installed.stdout).strip()!r}")
            return 1
        block = extract_managed_block((repo / "AGENTS.md").read_text(encoding="utf-8")) or ""
        if not re.search(r"memory[^\n]*repository cannot answer", block, re.IGNORECASE):
            report(f"{label} the installed bootstrap does not say memory holds only what the repository cannot answer: {block!r}")
            return 1
        if not re.search(r"memory[^\n]*shift change", block, re.IGNORECASE):
            report(f"{label} the installed bootstrap does not name a memory recheck at a shift change.")
            return 1
        if len(block.encode("utf-8")) > BOOTSTRAP_BLOCK_BYTE_BUDGET:
            report(f"{label} the installed bootstrap is {len(block.encode('utf-8'))} bytes, over the {BOOTSTRAP_BLOCK_BYTE_BUDGET}-byte budget.")
            return 1

        rtl, verify, env, _ = shift_scratch(base / "team")
        text = run_keel(verify, "shift", "check", env=env)
        if text.returncode != 0:
            report(f"{label} keel shift check exited {text.returncode} in a clean bound worktree: {text.stdout!r}")
            return 1
        if "keel shift check: ready" not in text.stdout:
            report(f"{label} a clean bound worktree is not reported ready: {text.stdout!r}")
            return 1
        if not re.search(r"^note: memory: .*hand-off note", text.stdout, re.MULTILINE):
            report(f"{label} keel shift check prints no memory note: {text.stdout!r}")
            return 1
        listed = json.loads(run_keel(verify, "shift", "check", "--json", env=env).stdout)
        if listed.get("ready") is not True or listed.get("items"):
            report(f"{label} the memory note changed readiness: {listed!r}")
            return 1
        if not any(note.startswith("memory:") for note in listed.get("notes", [])):
            report(f"{label} keel shift check --json carries no memory note: {listed.get('notes')!r}")
            return 1
    command = (ROOT / "plugins/keel/commands/shift.md").read_text(encoding="utf-8")
    if "memory" not in command.split("## 2.", 1)[0]:
        report(f"{label} /keel:shift step 1 does not tell the session to act on the memory note.")
        return 1
    if label.rstrip(":") not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report(f"{label.rstrip(':')} scenario passed.")
    return 0

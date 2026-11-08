"""Keel validation: chatwake (#516). A record wakes a session once, and the wake lists what is new."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from validation.common import (
    PLUGIN_ROOT,
    ROOT,
    chat_json,
    chat_scratch_group,
    report,
    run_keel,
)

SCRIPT = ROOT / PLUGIN_ROOT / "scripts/mail-hook.js"
HOST_EVENTS = {
    "session-start": "SessionStart",
    "user-prompt-submit": "UserPromptSubmit",
    "file-changed": "FileChanged",
    "session-end": "SessionEnd",
}


def hook_payload(cwd: Path, event: str, session: str | None) -> str:
    payload = {"hook_event_name": HOST_EVENTS[event], "cwd": str(cwd)}
    if session is not None:
        payload["session_id"] = session
    return json.dumps(payload)


def run_hook(cwd: Path, env: dict, event: str, session: str | None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", str(SCRIPT), event], cwd=cwd, env=env, text=True, capture_output=True, check=False,
        input=hook_payload(cwd, event, session),
    )


def start_hooks(cwd: Path, env: dict, event: str, session: str, count: int) -> list[subprocess.Popen]:
    return [
        subprocess.Popen(
            ["node", str(SCRIPT), event], cwd=cwd, env=env, text=True, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        for _ in range(count)
    ]


def world(prefix: str):
    raw = tempfile.TemporaryDirectory(prefix=prefix)
    base = Path(raw.name).resolve()
    rtl, verify, env = chat_scratch_group(base)
    env["KEEL_CLI"] = f'node "{ROOT / "bin" / "keel.js"}"'
    return raw, rtl, verify, env


def mention(rtl: Path, env: dict, text: str) -> str:
    return chat_json(run_keel(rtl, "chat", "post", "soc", f"@verify {text}", "--json", env=env)).get("id", "")


def validate_chat_wake_once_scenario() -> int:
    label = "chat-wake-once:"
    raw, rtl, verify, env = world("keel-wake-once-")
    with raw:
        first = mention(rtl, env, "first")
        woke = run_hook(verify, env, "file-changed", "s1")
        if woke.returncode != 2:
            report(f"{label} the first FileChanged exited {woke.returncode}, not 2: {woke.stderr.strip()}")
            return 1
        if first not in woke.stderr:
            report(f"{label} the first wake does not name the record {first}: {woke.stderr.strip()}")
            return 1
        again = run_hook(verify, env, "file-changed", "s1")
        if again.returncode != 0:
            report(f"{label} the second FileChanged for the same record exited {again.returncode}, not 0: {again.stderr.strip()}")
            return 1
        if again.stderr.strip():
            report(f"{label} the second FileChanged wrote {again.stderr.strip()!r} for a record already announced")
            return 1

        second = mention(rtl, env, "second")
        later = run_hook(verify, env, "file-changed", "s1")
        if later.returncode != 2:
            report(f"{label} a later mention exited {later.returncode}, not 2: {later.stderr.strip()}")
            return 1
        if second not in later.stderr:
            report(f"{label} the later wake does not name {second}: {later.stderr.strip()}")
            return 1
        if first in later.stderr:
            report(f"{label} the later wake repeats the record already announced ({first}): {later.stderr.strip()}")
            return 1
        if "2 unread" not in later.stderr:
            report(f"{label} the later wake does not state the total unread (2): {later.stderr.strip()}")
            return 1

        other = run_hook(verify, env, "file-changed", "s2")
        if other.returncode != 2:
            report(f"{label} another session's first FileChanged exited {other.returncode}, not 2")
            return 1
        for record in (first, second):
            if record not in other.stderr:
                report(f"{label} another session was not told {record}: {other.stderr.strip()}")
                return 1

        for _ in range(2):
            anonymous = run_hook(verify, env, "file-changed", None)
            if anonymous.returncode != 2:
                report(f"{label} a payload without a session id exited {anonymous.returncode}, not 2")
                return 1
    report("chat-wake-once scenario passed.")
    return 0


def validate_chat_wake_race_scenario() -> int:
    label = "chat-wake-race:"
    raw, rtl, verify, env = world("keel-wake-race-")
    with raw:
        mention(rtl, env, "once")
        procs = start_hooks(verify, env, "file-changed", "s1", 8)
        payload = hook_payload(verify, "file-changed", "s1")
        codes = []
        for proc in procs:
            proc.communicate(payload)
            codes.append(proc.returncode)
        winners = [c for c in codes if c == 2]
        if len(winners) != 1:
            report(f"{label} {len(winners)} of 8 simultaneous hooks announced the record, not 1: {codes}")
            return 1
        quiet = [c for c in codes if c == 0]
        if len(quiet) != 7:
            report(f"{label} the other hooks did not all exit 0: {codes}")
            return 1
    report("chat-wake-race scenario passed.")
    return 0


def validate_chat_wake_after_notice_scenario() -> int:
    label = "chat-wake-after-notice:"
    raw, rtl, verify, env = world("keel-wake-notice-")
    with raw:
        first = mention(rtl, env, "first")
        start = run_hook(verify, env, "session-start", "s1")
        if first not in chat_json(start).get("hookSpecificOutput", {}).get("additionalContext", ""):
            report(f"{label} SessionStart did not list the mention it is meant to have shown: {start.stdout.strip()}")
            return 1
        after_start = run_hook(verify, env, "file-changed", "s1")
        if after_start.returncode != 0:
            report(f"{label} FileChanged exited {after_start.returncode} for a record SessionStart already listed: {after_start.stderr.strip()}")
            return 1

        second = mention(rtl, env, "second")
        prompt = run_hook(verify, env, "user-prompt-submit", "s1")
        if second not in chat_json(prompt).get("hookSpecificOutput", {}).get("additionalContext", ""):
            report(f"{label} UserPromptSubmit did not list the later mention: {prompt.stdout.strip()}")
            return 1
        after_prompt = run_hook(verify, env, "file-changed", "s1")
        if after_prompt.returncode != 0:
            report(f"{label} FileChanged exited {after_prompt.returncode} for a record a prompt notice already listed: {after_prompt.stderr.strip()}")
            return 1

        run_keel(verify, "chat", "notice", env=env)
        run_keel(verify, "chat", "check", env=env)
        third = mention(rtl, env, "third")
        run_keel(verify, "chat", "notice", env=env)
        run_keel(verify, "chat", "check", env=env)
        unannounced = run_hook(verify, env, "file-changed", "s1")
        if unannounced.returncode != 2:
            report(f"{label} `keel chat notice` and `check` marked a record announced; FileChanged exited {unannounced.returncode}, not 2")
            return 1
        if third not in unannounced.stderr:
            report(f"{label} the wake after notice and check does not name {third}: {unannounced.stderr.strip()}")
            return 1

        run_hook(verify, env, "session-start", "s1")
        resumed = run_hook(verify, env, "file-changed", "s1")
        if resumed.returncode != 0:
            report(f"{label} FileChanged exited {resumed.returncode} after a second SessionStart listed everything unread")
            return 1

        mention(rtl, env, "fourth")
        run_hook(verify, env, "session-end", "s1")
        restarted = run_hook(verify, env, "file-changed", "s1")
        if restarted.returncode != 2:
            report(f"{label} FileChanged exited {restarted.returncode} for a session id that ended, not 2")
            return 1
    report("chat-wake-after-notice scenario passed.")
    return 0

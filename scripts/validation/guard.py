"""Keel validation: guard (split from validate_plugin.py, #409)."""
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
    portable_projection_bytes,
    BOOTSTRAP_BLOCK_BYTE_BUDGET,
    PLUGIN_ROOT,
    ROOT,
    chat_environment,
    chat_logs_snapshot,
    chat_worktree,
    config_header_problem,
    guard_task_fixture,
    mailbox_repository,
    plant_handoff_package,
    report,
    run_hook_script,
    run_keel,
    run_node_expression,
    run_session_start_hook,
    snapshot_files,
    stub_output,
    task_capsule_compact_fixture,
    task_contract_fixture,
    tracker_owner_tasks,
    write_authorize_config,
    write_gate_fixture,
    write_install_record,
    write_text,
)
from validation import registry


def validate_guard_scope_is_the_repository_scenario() -> int:
    """Issue #31: a decision needing no manifest sat downstream of reading one.

    Whether a target lies outside the repository is computable from the event's
    cwd and target path alone, but the invalid-manifest denial ran first, so a
    corrupt `keel/guard.json` denied writes to files the guard never protected.
    The precedence is what is asserted here, not the passthrough: a scenario
    checking only that an out-of-repo path passes under a valid manifest would
    have passed before this change too.
    """
    hook = ROOT / "plugins/keel/scripts/pretooluse-guard.js"
    if not hook.is_file():
        report(f"guard-scope-is-the-repository: missing hook {hook}.")
        return 1

    with tempfile.TemporaryDirectory(prefix="keel-guard-scope-") as raw:
        root = Path(raw)
        repo = root / "repo"
        outside = root / "scratch"
        outside.mkdir(parents=True)
        write_text(repo / "src/feature.js", "// product\n")
        # A live spec, so the Covers source lands outside the record layer and
        # authority drift can actually fire. Drifting the change's own tasks.md
        # produces no drift at all, because the record layer exempts it.
        live = repo / "openspec/specs/demo-cap/spec.md"
        write_text(
            live,
            "# demo-cap\n\n## Purpose\n\nFixture.\n\n"
            "### Requirement: The system emits a feed status\n"
            "The system SHALL emit the recorded feed status.\n\n"
            "#### Scenario: A status is emitted\n"
            "- **WHEN** the feed runs\n- **THEN** the status is recorded\n",
        )
        write_text(
            repo / "openspec/changes/demo/tasks.md",
            "# Tasks\n\n## Invalidates\n\n- None.\n\n"
            "- [ ] 1.1 Exercise the guard\n"
            "  - Covers:\n    - demo-cap / The system emits a feed status\n"
            "  - Touch:\n    - src/feature.js\n"
            "  - Verify:\n    - Strategy: evidence-first\n    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n    - M1: node test.js\n"
            "  - Evidence:\n    - Contract: pending\n    - M1: pending\n"
            "    - Review:\n      - Status: pending\n"
            "      - Acceptance check: pending\n      - Scope check: pending\n"
            "      - Findings: pending\n    - Blocker: none\n",
        )
        started = run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
            "--record", "--json",
        )
        if started.returncode != 0:
            report("guard-scope-is-the-repository: the fixture did not start.")
            report((started.stdout or started.stderr).strip())
            return 1
        manifest_path = repo / "keel/guard.json"
        manifest_text = manifest_path.read_text(encoding="utf-8")
        hashed = [
            item["path"] for item in json.loads(manifest_text).get("authority", [])
        ]
        if "openspec/specs/demo-cap/spec.md" not in hashed:
            report(
                "guard-scope-is-the-repository: the fixture hashed no authority "
                f"outside the change directory, so drift cannot fire: {hashed}."
            )
            return 1

        def decide(target: Path) -> str:
            event = json.dumps({
                "cwd": str(repo),
                "tool_name": "Edit",
                "tool_input": {"file_path": str(target)},
            })
            result = subprocess.run(
                ["node", str(hook)],
                input=event,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            out = (result.stdout or "").strip()
            if not out:
                return "allow"
            payload = json.loads(out)["hookSpecificOutput"]
            return payload.get("permissionDecisionReason", "deny")

        def expect(label: str, target: Path, allow: bool, needle: str = "") -> bool:
            verdict = decide(target)
            if allow:
                if verdict != "allow":
                    report(f"guard-scope-is-the-repository: {label} was denied.")
                    report(f"  {verdict}")
                    return False
                return True
            if verdict == "allow":
                report(f"guard-scope-is-the-repository: {label} was allowed.")
                return False
            if needle and needle not in verdict:
                report(
                    f"guard-scope-is-the-repository: {label} was denied for the "
                    f"wrong reason; expected {needle!r}."
                )
                report(f"  {verdict}")
                return False
            return True

        scratch = outside / "notes.md"
        # M2 — the in-repository denials must survive the reordering.
        checks = [
            expect("an in-Touch write", repo / "src/feature.js", True),
            expect(
                "an in-repository path outside Touch",
                repo / "other.js",
                False,
                "outside Touch",
            ),
            expect(
                "the guarded change's own records",
                repo / "openspec/changes/demo/notes.md",
                True,
            ),
            expect("an out-of-repository write", scratch, True),
        ]

        # M1, first half — genuine authority drift.
        write_text(live, live.read_text(encoding="utf-8") + "\nDRIFTED\n")
        checks.append(
            expect("an in-Touch write under drift", repo / "src/feature.js", False, "drift")
        )
        checks.append(
            expect("an out-of-repository write under drift", scratch, True)
        )

        # M1, second half — the corrupt manifest, which is the reported defect.
        manifest_path.write_text("{ not json", encoding="utf-8")
        checks.append(
            expect("an out-of-repository write under a corrupt manifest", scratch, True)
        )
        checks.append(
            expect(
                "an in-repository write under a corrupt manifest",
                repo / "src/feature.js",
                False,
                "invalid",
            )
        )
        if not all(checks):
            return 1
    if "guard-scope-is-the-repository" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "guard-scope-is-the-repository: the scenario registry does not "
            "include it."
        )
        return 1
    report("guard-scope-is-the-repository scenario passed.")
    return 0


def validate_default_completion_attributes_writes_scenario() -> int:
    """A write outside Touch has to fail the gate the author actually runs.

    `attributionResult` refuses an out-of-Touch path in full — diff, union with
    the dirty set, `pathAllowed` filter, `outside-touch` problem — behind
    `if (!base) return { problems: [] }`. Without `--base` the whole comparison
    is skipped and the paths are printed as a warning instead. Measured at
    5.15.0 on one tree and one task: `pass` with the offending path in a
    warning, `fail` once `--base HEAD` was added.

    It was found by it happening. During the 5.15.0 release task a file was
    written that the task had not declared, through a `python3` heredoc in
    Bash — the write guard binds the host's file-writing tools and cannot bind
    a shell — and `task-complete` returned `pass`. A human reading `git status`
    caught it. Nobody reads `git status` in an unattended run, and this
    repository admits work into unattended runs by declaration.

    The base does not have to come from the caller. `task-start` already writes
    the manifest at the instant the task is authorized; recording what was
    dirty then answers "did this task write it" without asking Git to answer
    "which task wrote it", which is the question it cannot answer in a
    half-finished change.

    Issue #72: recording only the path, not its content, meant a path already
    dirty at task start was exempt for the rest of the task's life, even after
    the task wrote it again — the common case, since most tasks in this
    repository start on a tree a prior task already legitimately touched. M2
    proves the fix: a dirty-at-start path the task modifies again is
    attributed, while M1's own dirty-at-start path (never touched again) stays
    exempt.
    """
    label = "default-completion-attributes-writes"

    def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True
        )

    def tasks_doc() -> str:
        return (
            "# Tasks\n\n## Invalidates\n\n- None.\n\n"
            "- [ ] 1.1 Exercise task contract\n"
            "  - Covers:\n    - E1: Public behavior passes.\n"
            "  - Touch:\n    - src/declared.js\n"
            "  - Verify:\n    - Strategy: evidence-first\n    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
            "    - M1: node test.js asserts the recorded feed status\n"
            "  - Evidence:\n    - Contract: pending\n    - M1: the suite passed\n"
            "    - Review:\n      - Status: pass\n"
            "      - Acceptance check: behavior asserted at the interface\n"
            "      - Scope check: only Touch files changed\n"
            "      - Findings: none\n"
            "    - Blocker: none\n"
        )

    with tempfile.TemporaryDirectory(prefix="keel-default-attribution-") as raw:
        repo = (Path(raw) / "repo").resolve()
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "t@example.com")
        git(repo, "config", "user.name", "keel-test")
        write_text(repo / "src/declared.js", "// product\n")
        write_text(repo / "src/undeclared.js", "// product\n")
        write_text(repo / "src/already-dirty.js", "// product\n")
        write_text(repo / "openspec/changes/demo/tasks.md", tasks_doc())
        git(repo, "add", "-A")
        git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "base")

        def start(*extra: str) -> subprocess.CompletedProcess[str]:
            return run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
                "--record", *extra, "--json",
            )

        def gate(*extra: str) -> dict:
            return json.loads(
                run_keel(
                    repo, "gate", "task-complete", "--change", "demo",
                    "--task", "1.1", *extra, "--json",
                ).stdout
            )

        def outside(payload: dict) -> list[str]:
            return [
                problem.get("message", "")
                for problem in payload.get("problems", [])
                if problem.get("code") == "outside-touch"
            ]

        # A path already dirty before the task is authorized. It must stay
        # unattributed afterwards: subtracting the start set is what removes
        # the false-positive class that made automatic attribution unsafe.
        write_text(repo / "src/already-dirty.js", "// touched before the task\n")

        if start().returncode != 0:
            report(f"{label} could not authorize the fixture task.")
            return 1

        # M1 — the reported defect. A write the guard never saw, and the gate
        # invoked the way an author actually invokes it.
        write_text(repo / "src/undeclared.js", "// written outside Touch\n")
        payload = gate()
        problems = outside(payload)
        if not any("src/undeclared.js" in message for message in problems):
            report(
                f"{label} M1 a path written outside Touch after task start was "
                "not refused by the default completion gate. The boundary "
                "holds only when the caller asks for it."
            )
            report(f"  status={payload.get('status')!r}")
            for warning in payload.get("warnings", []):
                report(f"  warning: {warning}")
            return 1
        if payload.get("status") != "fail":
            report(
                f"{label} M1 the gate named the out-of-Touch path but did not "
                f"fail; got status {payload.get('status')!r}. A boundary that "
                "reports without refusing is not a boundary."
            )
            return 1
        if any("src/already-dirty.js" in message for message in problems):
            report(
                f"{label} M1 a path that was already dirty when the task "
                "started was attributed to the task. The recorded set is not "
                "being subtracted, so an unrelated dirty worktree fails the "
                "gate."
            )
            return 1

        # M2 — issue #72: a path already dirty at task start is exempt only
        # while its content stays the one recorded then. A task that goes on
        # to modify that same path has written it, and the boundary M1 proved
        # above must still catch that write instead of exempting it forever
        # because it happened to be dirty at the start too.
        write_text(
            repo / "src/already-dirty.js", "// touched again by the task\n"
        )
        payload = gate()
        problems = outside(payload)
        if not any("src/already-dirty.js" in message for message in problems):
            report(
                f"{label} M2 a path already dirty at task start, then "
                "modified again by the task, was not attributed. Recording "
                "only the path (not its content) at task start exempts every "
                "later write to it, not just the one that predates the task."
            )
            report(f"  status={payload.get('status')!r}")
            for warning in payload.get("warnings", []):
                report(f"  warning: {warning}")
            return 1
        if payload.get("status") != "fail":
            report(
                f"{label} M2 the gate named the re-touched path but did not "
                f"fail; got status {payload.get('status')!r}."
            )
            return 1

        # M1 — an explicit base answers the question the caller asked, which is
        # the broader one: everything since that commit, including what was
        # already dirty when the task started.
        base_problems = outside(gate("--base", "HEAD"))
        if not any("src/already-dirty.js" in message for message in base_problems):
            report(
                f"{label} M1 an explicit --base did not attribute a path that "
                "changed since that base, so the recorded set is overriding "
                "the base the caller supplied instead of yielding to it."
            )
            for message in base_problems:
                report(f"  {message}")
            return 1

        # M1 — no record means no attribution. A manifest written before this
        # existed, or a cleared one, must not be read as a clean start: absence
        # of a record is not a record of absence.
        run_keel(repo, "guard", "clear")
        if start("--no-guard").returncode != 0:
            report(f"{label} could not re-authorize without a manifest.")
            return 1
        payload = gate()
        if outside(payload):
            report(
                f"{label} M1 the gate attributed paths with no recorded "
                "task-start set. A missing record is being read as a clean "
                "start, which fails every completion in a dirty repository."
            )
            for message in outside(payload):
                report(f"  {message}")
            return 1
        if not any(
            "not attributed" in warning for warning in payload.get("warnings", [])
        ):
            report(
                f"{label} M1 with no record the gate neither attributed nor "
                "reported the dirty paths, so the fallback lost the semantic "
                "review evidence it is supposed to preserve."
            )
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


CJK_PATH = "src/摄影光影规划工具.js"


SPACE_PATH = "src/has space.js"


QUOTE_PATH = 'src/has"quote.js'


BACKSLASH_PATH = "src/back\\slash.js"


def validate_git_paths_carry_no_escaping_scenario() -> int:
    """Issue #40: a Chinese filename in Touch was reported as outside Touch.

    Git escapes any path holding a non-ASCII byte to octal and wraps it in
    quotes. `gitPaths` then ran `line.slice(3).trim().replace(/\\\\/g, "/")`,
    which left the quotes in place and turned `\\346` into `/346`, so the path
    the task declared on the first line of its Touch could never match. The
    rewrite was defending against a Windows separator Git does not emit on any
    platform.

    Measured 2026-08-02: `core.quotepath=false` removes the octal but still
    quotes a path holding a space, a quote, or a backslash, and `status
    --short` and `diff --name-only` do not even agree on which cases they
    quote. `-z` emits raw bytes in every one of those cases, which deletes the
    problem instead of decoding it.
    """
    label = "git-paths-carry-no-escaping"
    interesting = (CJK_PATH, SPACE_PATH, QUOTE_PATH, BACKSLASH_PATH)

    def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True
        )

    def tasks_doc(touch: tuple[str, ...]) -> str:
        touch_lines = "".join(f"    - {item}\n" for item in touch)
        return (
            "# Tasks\n\n## Invalidates\n\n- None.\n\n"
            "- [ ] 1.1 Exercise task contract\n"
            "  - Covers:\n    - E1: Public behavior passes.\n"
            "  - Touch:\n"
            f"{touch_lines}"
            "  - Verify:\n    - Strategy: evidence-first\n    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
            "    - M1: node test.js asserts the recorded feed status\n"
            "  - Evidence:\n    - Contract: pending\n    - M1: the suite passed\n"
            "    - Review:\n      - Status: pass\n"
            "      - Acceptance check: behavior asserted at the interface\n"
            "      - Scope check: only Touch files changed\n"
            "      - Findings: none\n"
            "    - Blocker: none\n"
        )

    with tempfile.TemporaryDirectory(prefix="keel-git-paths-") as raw:
        root = Path(raw).resolve()
        repo = root / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "t@example.com")
        git(repo, "config", "user.name", "keel-test")
        # Left at the Git default on purpose. The point is that Keel reads a
        # form that carries no escaping, not that it asks the repository to
        # stop escaping — a per-repository setting is exactly the environment
        # coupling this change exists to remove.
        for item in interesting:
            write_text(repo / item, "// product\n")
        tasks = repo / "openspec/changes/demo/tasks.md"
        write_text(tasks, tasks_doc(interesting))
        git(repo, "add", "-A")
        git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "base")

        def gate(*extra: str) -> dict:
            return json.loads(
                run_keel(
                    repo, "gate", "task-complete", "--change", "demo",
                    "--task", "1.1", *extra, "--json",
                ).stdout
            )

        def record() -> bool:
            return (
                run_keel(
                    repo, "gate", "task-start", "--change", "demo", "--task",
                    "1.1", "--record", "--no-guard", "--json",
                ).returncode
                == 0
            )

        def outside(payload: dict) -> list[str]:
            return [
                problem.get("message", "")
                for problem in payload.get("problems", [])
                if problem.get("code") == "outside-touch"
            ]

        if not record():
            report(f"{label} could not record an anchor on the fixture.")
            return 1

        # M1 — the reported defect, on its own, through both readers.
        write_text(repo / CJK_PATH, "// changed\n")
        for reader, extra in (("dirty worktree", ()), ("explicit base", ("--base", "HEAD"))):
            payload = gate(*extra)
            problems = outside(payload)
            if problems:
                report(
                    f"{label} M1 the {reader} reader called a path outside "
                    "Touch that Touch declares on its own line, so the "
                    "non-ASCII path never survived the read."
                )
                for message in problems:
                    report(f"  {message}")
                return 1
            if payload.get("status") != "pass":
                report(
                    f"{label} M1 the {reader} reader did not attribute the "
                    "non-ASCII path outside Touch, but the gate still did not "
                    f"pass; status was {payload.get('status')!r}."
                )
                for problem in payload.get("problems", []):
                    report(f"  {problem.get('code')}: {problem.get('message')}")
                return 1

        # M2 — the characters Git quotes even with `core.quotepath=false`, and
        # the ones the two subcommands disagree about.
        for item in (SPACE_PATH, QUOTE_PATH, BACKSLASH_PATH):
            write_text(repo / item, "// changed\n")
        for reader, extra in (("dirty worktree", ()), ("explicit base", ("--base", "HEAD"))):
            problems = outside(gate(*extra))
            if problems:
                report(
                    f"{label} M2 the {reader} reader called a declared path "
                    "outside Touch once spaces, quotes, or backslashes were "
                    "involved."
                )
                for message in problems:
                    report(f"  {message}")
                return 1

        # Still M2: a separator rewrite makes two different files look like one.
        # `src/back/slash.js` is a real nested file the task never declared, and
        # it must not be admitted by a Touch entry naming `src/back\slash.js`.
        write_text(repo / "src/back/slash.js", "// undeclared\n")
        problems = outside(gate("--base", "HEAD"))
        if len(problems) != 1 or "src/back/slash.js" not in problems[0]:
            report(
                f"{label} M2 a nested file the task never declared was not the "
                "one outside-Touch problem, so a Touch entry naming a file with "
                "a literal backslash is still admitting a different file; got "
                f"{problems!r}."
            )
            return 1
        (repo / "src/back/slash.js").unlink()
        (repo / "src/back").rmdir()

        # M3 — a rename is one record plus a bare second field in `-z` form and
        # a single ` -> ` line otherwise. Only the unattributed-dirty warning
        # shows what that parser produced: with an explicit base the diff
        # reports both endpoints itself, so a dropped endpoint would be
        # invisible there.
        git(repo, "checkout", "-q", "--", ".")
        renamed = "src/重命名 后.js"
        git(repo, "mv", CJK_PATH, renamed)
        payload = gate()
        dirty = [
            warning
            for warning in payload.get("warnings", [])
            if "not attributed without an explicit base" in warning
        ]
        if len(dirty) != 1:
            report(
                f"{label} M3 the gate did not emit exactly one "
                "unattributed-dirty warning to read the rename out of; got "
                f"{payload.get('warnings')!r}."
            )
            return 1
        for endpoint, which in ((CJK_PATH, "old"), (renamed, "new")):
            if endpoint not in dirty[0]:
                report(
                    f"{label} M3 the {which} endpoint of the rename is missing "
                    "from the dirty-path warning, so one endpoint was dropped "
                    "or damaged by the read."
                )
                report(f"  {dirty[0]}")
                return 1
        if "\\3" in dirty[0] or "/346" in dirty[0]:
            report(
                f"{label} M3 the warning names an escaped form of a rename "
                "endpoint."
            )
            report(f"  {dirty[0]}")
            return 1
        git(repo, "reset", "-q", "--hard", "HEAD")

        # M4 — the same reader inside `keel context`.
        git(repo, "reset", "-q", "--hard", "HEAD")
        write_text(repo / CJK_PATH, "// changed again\n")
        context = json.loads(run_keel(repo, "context", "--json").stdout)
        warnings = " ".join(context.get("warnings", []))
        if CJK_PATH not in warnings:
            report(
                f"{label} M4 `keel context` did not report the uncommitted "
                "non-ASCII path as the filesystem spells it."
            )
            report(f"  warnings: {context.get('warnings')!r}")
            return 1
        if "\\3" in warnings or "/3" in warnings:
            report(
                f"{label} M4 `keel context` reported an escaped form of the "
                "path alongside or instead of the real one."
            )
            report(f"  warnings: {context.get('warnings')!r}")
            return 1
    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_guard_containment_is_resolved_scenario() -> int:
    """The guard decided containment by comparing two strings for one file.

    `path.relative(repo, path.resolve(repo, target))` never follows a symbolic
    link, while the `cwd` the host reports usually has already been resolved by
    the operating system. A file reached through a link to the repository then
    looked like a path outside it, and the guard returned before reading the
    manifest at all. Measured 2026-08-02: the same out-of-Touch file was denied
    by its resolved path and allowed through a link to the same directory.
    """
    label = "guard-containment-is-resolved"
    with tempfile.TemporaryDirectory(prefix="keel-containment-") as raw:
        # Resolved deliberately: the fixture's own link is what varies here, so
        # the temp root must not smuggle in a second one. macOS hands out
        # `/var/folders/...`, which is itself a link to `/private/var/...`.
        root = Path(raw).resolve()
        repo = root / "real" / "repo"
        write_text(repo / "src/allowed.js", "// product\n")
        write_text(repo / "src/denied.js", "// product\n")
        write_text(
            repo / "openspec/specs/demo-cap/spec.md",
            "# demo-cap\n\n## Purpose\n\nFixture.\n\n"
            "### Requirement: The system emits a feed status\n"
            "The system SHALL emit the recorded feed status.\n\n"
            "#### Scenario: A status is emitted\n"
            "- **WHEN** the feed runs\n- **THEN** the status is recorded\n",
        )
        write_text(
            repo / "openspec/changes/demo/tasks.md",
            "# Tasks\n\n## Invalidates\n\n- None.\n\n"
            "- [ ] 1.1 Exercise the guard\n"
            "  - Covers:\n    - demo-cap / The system emits a feed status\n"
            "  - Touch:\n    - src/allowed.js\n    - docs/**\n"
            "  - Verify:\n    - Strategy: evidence-first\n    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
            "    - M1: node test.js asserts the recorded feed status\n"
            "  - Evidence:\n    - Contract: pending\n    - M1: pending\n",
        )
        link = root / "link"
        link.symlink_to(repo, target_is_directory=True)

        started = run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
            "--record", "--json",
        )
        if started.returncode != 0 or not (repo / "keel/guard.json").is_file():
            report(f"{label} could not start a guard to probe.")
            report((started.stderr or started.stdout).strip())
            return 1

        def probe(cwd: Path, target: Path) -> str:
            event = edit_event(cwd, target, tool="Write")
            decision = pretooluse_decision(run_pretooluse_guard_hook(repo, event))
            if decision is None:
                return "allow"
            if "error" in decision:
                return f"error({decision['error']})"
            return decision.get("permissionDecision", "unknown")

        def expect(check: str, cwd: Path, target: Path, want: str) -> bool:
            got = probe(cwd, target)
            if got == want:
                return True
            spelling = "through the symlink" if str(link) in str(target) else "by its resolved path"
            report(
                f"{label} {check}: a write to {target.name} {spelling} was "
                f"{got!r}, not {want!r}. One file must get one containment "
                "answer however its path is spelled."
            )
            report(f"  cwd={cwd}")
            report(f"  target={target}")
            return False

        # M1 — the host reports the resolved cwd, which is the common case and
        # the one the bypass was measured against.
        if not all([
            expect("M1", repo, repo / "src/denied.js", "deny"),
            expect("M1", repo, link / "src/denied.js", "deny"),
            expect("M1", repo, repo / "src/allowed.js", "allow"),
            expect("M1", repo, link / "src/allowed.js", "allow"),
        ]):
            return 1

        # M2 — and the reverse, because the hook does not choose which form of
        # `cwd` the host hands it.
        if not all([
            expect("M2", link, repo / "src/denied.js", "deny"),
            expect("M2", link, link / "src/denied.js", "deny"),
            expect("M2", link, repo / "src/allowed.js", "allow"),
            expect("M2", link, link / "src/allowed.js", "allow"),
        ]):
            return 1

        # M3 — a guarded write is usually a file that does not exist yet, so
        # containment has to come from an ancestor. Both directions, because
        # resolving too eagerly denies legitimate new files.
        if not all([
            expect("M3", repo, repo / "src/not-yet.js", "deny"),
            expect("M3", repo, link / "src/not-yet.js", "deny"),
            expect("M3", repo, repo / "docs/not-yet.md", "allow"),
            expect("M3", repo, link / "docs/not-yet.md", "allow"),
        ]):
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_guard_manifest_ignored_scenario() -> int:
    """Issue #11: the guard manifest was written but declared ignorable nowhere.

    Every gate run left an untracked `keel/guard.json` in the project, and
    because completion attributes working-tree paths against Touch, that is a
    permanent exception the author re-adjudicates at every completion.
    """
    with tempfile.TemporaryDirectory(prefix="keel-guard-ignore-") as raw:
        project = Path(raw)
        init = run_keel(project, "--install", "--target", "claude")
        if init.returncode != 0:
            report("guard-manifest-ignored: keel --install failed.")
            report((init.stderr or init.stdout).strip())
            return 1
        ignore_path = project / "keel/.gitignore"
        if not ignore_path.is_file():
            report(
                "guard-manifest-ignored: keel --install did not scaffold "
                "keel/.gitignore."
            )
            return 1
        declared = ignore_path.read_text(encoding="utf-8")
        if "guard.json" not in declared:
            report(
                "guard-manifest-ignored: the scaffolded keel/.gitignore does "
                "not declare the guard manifest."
            )
            report(declared)
            return 1

        # git must actually honour the declaration: initialize a repository,
        # write a manifest through a passing task-start, and confirm the path
        # never appears in porcelain status.
        if subprocess.run(
            ["git", "init", "--quiet"], cwd=project, capture_output=True
        ).returncode != 0:
            report("guard-manifest-ignored: git init failed in the fixture.")
            return 1
        write_text(
            project / "openspec/changes/demo/tasks.md",
            tracker_owner_tasks("none", "Covered by: 1.1").replace(
                "- [x] 1.1", "- [ ] 1.1"
            ),
        )
        started = run_keel(
            project, "gate", "task-start",
            "--change", "demo", "--task", "1.1", "--json",
        )
        if started.returncode != 0 or not (project / "keel/guard.json").is_file():
            report(
                "guard-manifest-ignored: the fixture did not produce a guard "
                "manifest to test the declaration against."
            )
            report((started.stderr or started.stdout).strip())
            return 1
        status = subprocess.run(
            ["git", "status", "--short", "--untracked-files=all"],
            cwd=project, capture_output=True, encoding="utf-8",
        )
        if "guard.json" in (status.stdout or ""):
            report(
                "guard-manifest-ignored: git still reports the guard manifest "
                "after a gate run, so the declaration does not take effect."
            )
            report(status.stdout or "")
            return 1

        # Scaffold once: a project's own file is never rewritten.
        own = "# mine\nguard.json\nscratch/\n"
        write_text(ignore_path, own)
        again = run_keel(project, "--install", "--target", "claude")
        if again.returncode != 0 or ignore_path.read_text(encoding="utf-8") != own:
            report(
                "guard-manifest-ignored: a second install overwrote the "
                "project's own keel/.gitignore."
            )
            report((again.stderr or again.stdout).strip())
            return 1

    if not (ROOT / "keel/.gitignore").is_file():
        report(
            "guard-manifest-ignored: Keel's own repository does not declare "
            "the guard manifest ignorable."
        )
        return 1
    if "guard-manifest-ignored" not in {name for name, _ in registry.SCENARIOS}:
        report("guard-manifest-ignored: the scenario registry does not include it.")
        return 1
    report("guard-manifest-ignored scenario passed.")
    return 0


def validate_guard_status_is_not_enforcement_scenario() -> int:
    """Issue #14: `Guard: started` means the manifest was written.

    Authors read it as "writes are being checked now". The two came apart when a
    session kept plugin state that predated a marketplace switch: the manifest
    was valid and keel's PreToolUse hook never ran. Keel cannot observe the hook
    from the repository, so the result must say so rather than imply otherwise.
    """
    needles = ("enforcement", "runtime hook", "cannot observe")
    # Assertive claims only: the honest sentence legitimately denies that a
    # written manifest proves anything, so a bare "writes are checked" substring
    # would match the denial itself.
    forbidden = (
        "enforcement is active",
        "enforcement is live",
        "writes are guarded",
    )
    with tempfile.TemporaryDirectory(prefix="keel-guard-honesty-") as raw:
        project = Path(raw)
        write_text(
            project / "openspec/changes/demo/tasks.md",
            tracker_owner_tasks("none", "Covered by: 1.1").replace(
                "- [x] 1.1", "- [ ] 1.1"
            ),
        )
        started = run_keel(
            project, "guard", "start",
            "--change", "demo", "--task", "1.1", "--json",
        )
        if started.returncode != 0:
            report("guard-status-is-not-enforcement: keel guard start failed.")
            report((started.stderr or started.stdout).strip())
            return 1
        for label, result in (
            ("start", started),
            (
                "status",
                run_keel(project, "guard", "status", "--json"),
            ),
        ):
            payload = json.loads(result.stdout) if result.stdout else {}
            warnings = " ".join(payload.get("warnings", []))
            missing = [needle for needle in needles if needle not in warnings]
            if missing:
                report(
                    f"guard-status-is-not-enforcement: keel guard {label} does "
                    "not state that the status describes the manifest and that "
                    "enforcement depends on a runtime hook Keel cannot observe; "
                    f"missing {missing}."
                )
                report(result.stdout or result.stderr or "")
                return 1
            if not payload.get("status"):
                report(
                    f"guard-status-is-not-enforcement: keel guard {label} lost "
                    "its status value."
                )
                return 1
            human = run_keel(
                project,
                "guard",
                *(("start", "--change", "demo", "--task", "1.1", "--force")
                  if label == "start" else ("status",)),
            )
            if "runtime hook" not in (human.stdout or ""):
                report(
                    f"guard-status-is-not-enforcement: the human-readable keel "
                    f"guard {label} output omits the enforcement boundary."
                )
                report(human.stdout or human.stderr or "")
                return 1
            for phrase in forbidden:
                if phrase in warnings or phrase in (human.stdout or ""):
                    report(
                        f"guard-status-is-not-enforcement: keel guard {label} "
                        f"asserts observed enforcement: {phrase!r}."
                    )
                    return 1
        # The pre-existing durability statement must survive alongside it.
        status_payload = json.loads(
            run_keel(project, "guard", "status", "--json").stdout
        )
        if not any(
            "durable authority" in warning
            for warning in status_payload.get("warnings", [])
        ):
            report(
                "guard-status-is-not-enforcement: the existing durable-authority "
                "statement was dropped."
            )
            return 1
    if "guard-status-is-not-enforcement" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "guard-status-is-not-enforcement: the scenario registry does not "
            "include it."
        )
        return 1
    report("guard-status-is-not-enforcement scenario passed.")
    return 0


def validate_guard_warnings_are_concise_scenario() -> int:
    """Issue #92 item 1: shorten the two standing guard warnings.

    The owner authorized shortening wording, not removing content: every
    idea `guard-status-is-not-enforcement` checks for must still resolve, but
    the combined text must drop below the byte counts `#92` measured before
    this fix (398 for `guard status`, 397 for `guard clear`, on a fresh
    directory with no manifest).
    """
    baseline = {"status": 398, "clear": 397}
    with tempfile.TemporaryDirectory(prefix="keel-guard-concise-") as raw:
        project = Path(raw)
        for label, before in baseline.items():
            result = run_keel(project, "guard", label)
            out = result.stdout or ""
            if len(out) >= before:
                report(
                    f"guard-warnings-are-concise: keel guard {label} is "
                    f"{len(out)} chars, not shorter than the {before}-char "
                    "baseline #92 measured before the wording was shortened."
                )
                return 1
    if "guard-warnings-are-concise" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "guard-warnings-are-concise: the scenario registry does not "
            "include it."
        )
        return 1
    report("guard-warnings-are-concise scenario passed.")
    return 0


def validate_guard_keeps_loaded_logic_under_manifest_scenario() -> int:
    """Issue #204: the write guard waits for the active task before adopting.

    While a task's guard manifest exists, the guard the session loaded keeps
    deciding, so a mid-task update cannot change what is allowed. The first
    check after the manifest is gone runs the installed copy, and a copy that
    cannot run leaves the loaded guard's decision in place.
    """
    label = "guard-keeps-loaded-logic-under-manifest:"
    with tempfile.TemporaryDirectory(prefix="keel-handoff-guard-", ignore_cleanup_errors=True) as raw:
        tmp = Path(raw)
        plugins_dir = tmp / "plugins"
        cache = plugins_dir / "cache/m/keel"
        loaded = plant_handoff_package(cache / "5.0.0", "5.0.0")
        newer = plant_handoff_package(cache / "5.1.0", "5.1.0", stubs=("pretooluse-guard.js",))
        write_install_record(plugins_dir, newer)

        repo = tmp / "repo"
        repo.mkdir()
        write_text(repo / "openspec/changes/demo/tasks.md", guard_task_fixture())
        write_text(repo / "src/feature.js", "// fixture\n")
        gate = run_keel(repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json")
        manifest = repo / "keel/guard.json"
        if gate.returncode != 0 or not manifest.is_file():
            report(f"{label} the fixture task did not start a guard: {gate.stdout}{gate.stderr}")
            return 1
        guard = loaded / "plugins/keel/scripts/pretooluse-guard.js"
        event = json.dumps(edit_event(repo, repo / "b.txt", "Write"))

        under = run_hook_script(guard, [], event, repo)
        decision = pretooluse_decision(under) if stub_output(under) is None else None
        if stub_output(under) is not None:
            report(f"{label} the guard handed off while a manifest was active: {under.stdout!r}")
            return 1
        if not decision or decision.get("permissionDecision") != "deny":
            report(f"{label} the loaded guard did not deny b.txt under the manifest: {decision!r}")
            return 1

        manifest.unlink()
        after = run_hook_script(guard, [], event, repo)
        if stub_output(after) is None:
            report(f"{label} the guard did not hand off once the manifest was gone: "
                   f"stdout={after.stdout!r} stderr={after.stderr!r}")
            return 1

        # A copy that cannot finish in time leaves the loaded guard's decision.
        # With no manifest the loaded guard allows silently, so the fallback is
        # observable as empty output rather than the stub's.
        slow = run_hook_script(guard, [], event, repo,
                               {"HANDOFF_STUB_SLEEP_MS": "5000", "KEEL_HOOK_FORWARD_TIMEOUT_MS": "300"})
        if stub_output(slow) is not None:
            report(f"{label} a timed-out hand-off still relayed the newer guard: {slow.stdout!r}")
            return 1
        if slow.returncode != 0:
            report(f"{label} a timed-out hand-off made the guard exit {slow.returncode}: {slow.stderr!r}")
            return 1
        if slow.stdout.strip():
            report(f"{label} a timed-out hand-off did not leave the loaded guard's silent allow: {slow.stdout!r}")
            return 1

    if "guard-keeps-loaded-logic-under-manifest" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("guard-keeps-loaded-logic-under-manifest scenario passed.")
    return 0


STANDING_AUTHORIZATION_ACTIONS = (
    "commit",
    "push",
    "release",
    "archive",
    "continuation",
    "protocol-refresh",
    "chat-reply",
)


def validate_authorize_block_reads_every_line_scenario() -> int:
    """Issue #275: no line of `authorize:` is dropped silently.

    An item with a space used to end the block, dropping it and every later
    entry while doctor said ok; a trailing comment dropped its item too.
    """
    label = "authorize-block-reads-every-line:"
    with tempfile.TemporaryDirectory(prefix="keel-authorize-275-") as raw_tmp:
        root = Path(raw_tmp)
        spaced = root / "spaced"
        spaced.mkdir()
        write_authorize_config(spaced, "authorize:\n  - commit\n  - push:main branch\n  - release\n")
        doctor = run_keel(spaced, "--doctor")
        if doctor.returncode == 0:
            report(f"{label} an item with a space was not refused: {doctor.stdout}")
            return 1
        if "push:main branch" not in doctor.stdout + doctor.stderr:
            report(f"{label} the refusal does not name `push:main branch`: {doctor.stdout}")
            return 1
        if "commit: authorized" in doctor.stdout:
            report(f"{label} the entries beside the refused one stayed authorized.")
            return 1

        commented = root / "commented"
        subprocess.run(["git", "init", "-q", "-b", "main", str(commented)], check=True, capture_output=True)
        write_authorize_config(
            commented,
            "authorize:\n  - commit  # owner, 2026-10-11\n  - push:claude/*  # sessions push their own branches\n",
        )
        out = run_keel(commented, "--doctor").stdout
        if "commit: authorized" not in out:
            report(f"{label} a trailing comment dropped `commit`: {out}")
            return 1
        push_line = next((l for l in out.splitlines() if l.strip().startswith("push:")), "")
        if "claude/*" not in push_line or "#" in push_line:
            report(f"{label} the push line does not read the glob without its comment: {push_line!r}")
            return 1
        event = {"tool_name": "Bash", "tool_input": {"command": "git push origin HEAD:main"}, "cwd": str(commented)}
        decision = pretooluse_decision(run_pretooluse_guard_hook(commented, event))
        if not decision or decision.get("permissionDecision") != "deny":
            report(f"{label} the push guard did not read a commented glob: {decision!r}")
            return 1
    report("authorize-block-reads-every-line scenario passed.")
    return 0


def validate_push_protected_declaration_scenario() -> int:
    """Issue #280: `push-protected:<glob>[@<role>]` is accepted and reported."""
    label = "push-protected-declaration:"
    with tempfile.TemporaryDirectory(prefix="keel-push-protected-") as raw_tmp:
        root = Path(raw_tmp)

        def fixture(name: str, entries: list[str]) -> Path:
            repo = root / name
            repo.mkdir()
            write_authorize_config(repo, "authorize:\n" + "".join(f"  - {e}\n" for e in entries))
            return repo

        doctor = run_keel(fixture("good", ["push:claude/*", "push-protected:main@iecc-pm"]), "--doctor")
        line = next((l for l in doctor.stdout.splitlines() if l.strip().startswith("push-protected:")), "")
        if "authorized" not in line or "main@iecc-pm" not in line:
            report(f"{label} doctor's push-protected line is {line!r}.")
            report(doctor.stdout)
            return 1
        if "asks the user" not in doctor.stdout:
            report(f"{label} doctor does not say each protected push is asked: {doctor.stdout}")
            return 1
        for name, entries, needle in (
            ("bad-role", ["push-protected:main@Not"], "push-protected:main@Not"),
            ("mixed", ["push", "push-protected:main"], "push-protected:main"),
        ):
            refused = run_keel(fixture(name, entries), "--doctor")
            if refused.returncode == 0:
                report(f"{label} {entries!r} was accepted.")
                return 1
            if needle not in refused.stdout + refused.stderr:
                report(f"{label} {entries!r} was refused without naming {needle!r}: {refused.stdout}")
                return 1
    report("push-protected-declaration scenario passed.")
    return 0


def validate_authorize_push_close_cleanup_scenario() -> int:
    """Issue #257: `push:<glob>`, `issue-close:<owner>/<repo>`, `cleanup:scratch`.

    Each is reported with its scope, a task with no boundary inherits all of
    them, and each wrong form is refused naming the form it needs.
    """
    label = "authorize-push-close-cleanup:"
    with tempfile.TemporaryDirectory(prefix="keel-authorize-257-") as raw_tmp:
        root = Path(raw_tmp)

        def fixture(name: str, entries: list[str]) -> Path:
            repo = root / name
            repo.mkdir()
            write_authorize_config(repo, "authorize:\n" + "".join(f"  - {e}\n" for e in entries))
            return repo

        good = fixture("good", ["push:claude/*", "push:worktree-*", "issue-close:acme/widgets", "cleanup:scratch"])
        doctor = run_keel(good, "--doctor")
        lines = doctor.stdout.splitlines()

        def line_for(action: str) -> str:
            return next((l for l in lines if l.strip().startswith(f"{action}:")), "")

        for action, needles in (
            ("push", ("authorized", "claude/*", "worktree-*")),
            ("issue-close", ("authorized", "acme/widgets")),
            ("cleanup", ("authorized", "scratch")),
        ):
            line = line_for(action)
            missing = [n for n in needles if n not in line]
            if missing:
                report(f"{label} doctor's {action} line lacks {missing!r}: {line!r}")
                report(doctor.stdout)
                return 1
        if "write guard enforces" not in doctor.stdout:
            report(f"{label} doctor does not say the write guard enforces the push globs.")
            report(doctor.stdout)
            return 1

        write_text(good / "openspec/changes/inherit/tasks.md", task_capsule_compact_fixture().replace(
            "  - Autonomy boundary:\n    - Default: hard-stop\n    - Pre-authorized fallback: none\n", ""))
        started = run_keel(good, "gate", "task-start", "--change", "inherit", "--task", "1.1", "--json")
        text = started.stdout
        inherited = "push:claude/*, push:worktree-*, issue-close:acme/widgets, cleanup:scratch"
        if inherited not in text:
            report(f"{label} the inherited autonomy entry does not name all four: {text[:1500]}")
            return 1

        for name, entries, needles in (
            ("mixed", ["push", "push:claude/*"], ("push", "push:claude/*")),
            ("bare-close", ["issue-close"], ("issue-close:<owner>/<repo>",)),
            ("cleanup-runs", ["cleanup:runs"], ("cleanup:scratch",)),
            ("bad-glob", ["push:main?"], ("push:main?", "push:<branch glob>")),
        ):
            refused = run_keel(fixture(name, entries), "--doctor")
            if refused.returncode == 0:
                report(f"{label} {entries!r} was accepted.")
                return 1
            missing = [n for n in needles if n not in refused.stdout + refused.stderr]
            if missing:
                report(f"{label} {entries!r} was refused without naming {missing!r}: {refused.stdout}")
                return 1
    report("authorize-push-close-cleanup scenario passed.")
    return 0


def validate_standing_authorization_declaration_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-authorize-") as raw_tmp:
        root = Path(raw_tmp)

        # M1 — a declared action is authorized; an undeclared one is not.
        declared = root / "declared"
        declared.mkdir()
        write_authorize_config(
            declared,
            "fast_check: echo declared-check\n"
            "authorize:\n"
            "  - commit\n"
            "  - push\n",
        )
        out = run_keel(declared, "--doctor").stdout
        if "Standing authorization:" not in out:
            report("standing-authorization: doctor has no standing authorization surface.")
            report(out)
            return 1
        for needle in ("commit: authorized", "push: authorized"):
            if needle not in out:
                report(f"standing-authorization: declared action not reported: {needle}")
                report(out)
                return 1
        for needle in (
            "release: not authorized",
            "archive: not authorized",
            "continuation: not authorized",
        ):
            if needle not in out:
                report(f"standing-authorization: undeclared action not reported: {needle}")
                report(out)
                return 1

        # M2 — absent, blockless, and empty declarations all authorize nothing,
        # and none of them disturbs the fast_check surface that shares the file.
        absent = root / "absent"
        absent.mkdir()
        blockless = root / "blockless"
        blockless.mkdir()
        write_authorize_config(blockless, "fast_check: echo blockless-check\n")
        empty = root / "empty"
        empty.mkdir()
        write_authorize_config(
            empty, "fast_check: echo empty-check\nauthorize:\n"
        )
        for repo, label, fast in (
            (absent, "absent", None),
            (blockless, "blockless", "echo blockless-check"),
            (empty, "empty", "echo empty-check"),
        ):
            out = run_keel(repo, "--doctor").stdout
            if "authorize: none" not in out:
                report(
                    f"standing-authorization: {label} repo does not report an "
                    "undeclared authorization surface."
                )
                report(out)
                return 1
            if "authorized" in out.replace("not authorized", ""):
                report(
                    f"standing-authorization: {label} repo reports an authorized action."
                )
                report(out)
                return 1
            expected_fast = f"fast_check: ok - declared in keel/config.yaml: {fast}"
            if fast is not None and expected_fast not in out:
                report(
                    f"standing-authorization: {label} repo lost its fast_check line."
                )
                report(out)
                return 1
            if fast is None and "fast_check: none" not in out:
                report("standing-authorization: absent repo lost its fast_check line.")
                report(out)
                return 1

        # M3 — an unrecognized name is reported with the accepted set, exits
        # non-zero, and authorizes nothing that sits beside it.
        unknown = root / "unknown"
        unknown.mkdir()
        write_authorize_config(
            unknown,
            "authorize:\n  - commit\n  - deploy\n",
        )
        result = run_keel(unknown, "--doctor")
        combined = result.stdout + result.stderr
        if result.returncode == 0:
            report("standing-authorization: an unrecognized action name exited zero.")
            report(combined)
            return 1
        if "deploy" not in combined:
            report("standing-authorization: the error does not name the offending entry.")
            report(combined)
            return 1
        for action in STANDING_AUTHORIZATION_ACTIONS:
            if action not in combined:
                report(
                    "standing-authorization: the error does not name accepted "
                    f"action {action}."
                )
                report(combined)
                return 1
        if "commit: authorized" in combined:
            report(
                "standing-authorization: a rejected declaration still authorized "
                "the entry beside the bad one."
            )
            report(combined)
            return 1

    report("standing-authorization-declaration scenario passed.")
    return 0


def validate_standing_authorization_sync_confusion_scenario() -> int:
    """`sync` is a `change-close --action` value, not an `authorize:` name (#93).

    A reader who copies `sync` from `change-close --action sync|archive` into
    `authorize:` gets the generic unrecognized-action message, which never says
    why `sync` in particular is wrong or what to write instead — and the
    failure was reported only by `keel --doctor`, an explicitly-invoked
    diagnostic, not by `keel context`, the command a session runs first.
    """
    label = "standing-authorization-sync-confusion"
    with tempfile.TemporaryDirectory(prefix="keel-authorize-sync-") as raw_tmp:
        root = Path(raw_tmp)

        # M1 — `sync` gets a sentence naming the `change-close --action`
        # confusion and pointing at `archive`; an unrelated typo does not.
        sync_repo = root / "sync"
        sync_repo.mkdir()
        write_authorize_config(sync_repo, "authorize:\n  - sync\n")
        doctor = run_keel(sync_repo, "--doctor")
        combined = doctor.stdout + doctor.stderr
        for needle in ("change-close --action", "declare `archive`"):
            if needle not in combined:
                report(
                    f"{label} M1 the doctor message does not name the sync "
                    f"confusion: {needle!r}."
                )
                report(combined)
                return 1

        typo_repo = root / "typo"
        typo_repo.mkdir()
        write_authorize_config(typo_repo, "authorize:\n  - deploy\n")
        typo_doctor = run_keel(typo_repo, "--doctor")
        typo_combined = typo_doctor.stdout + typo_doctor.stderr
        if "deploy" not in typo_combined:
            report(f"{label} M1 the typo repo's own offending entry went unreported.")
            report(typo_combined)
            return 1
        if "change-close --action" in typo_combined:
            report(
                f"{label} M1 a genuine typo (`deploy`) still received the "
                "sync-specific sentence."
            )
            report(typo_combined)
            return 1

        # M2 — the same broken declaration surfaces in `keel context`'s
        # warnings, and does not disturb status or nextAction, exactly as an
        # uncommitted git path is reported without changing selection.
        context = json.loads(run_keel(sync_repo, "context", "--json").stdout)
        warnings = " ".join(context.get("warnings", []))
        if "change-close --action" not in warnings or "sync" not in warnings:
            report(
                f"{label} M2 `keel context` did not report the broken "
                "authorize: declaration."
            )
            report(f"  warnings: {context.get('warnings')!r}")
            return 1
        if context.get("status") != "idle":
            report(f"{label} M2 the broken declaration changed context's status: {context.get('status')!r}")
            return 1
        if context.get("nextAction", {}).get("kind") != "none":
            report(
                "{} M2 the broken declaration changed context's nextAction: {!r}".format(
                    label, context.get("nextAction")
                )
            )
            return 1

        typo_context = json.loads(run_keel(typo_repo, "context", "--json").stdout)
        typo_warnings = " ".join(typo_context.get("warnings", []))
        if "deploy" not in typo_warnings:
            report(
                f"{label} M2 `keel context` did not report the typo repo's "
                "broken authorize: declaration at all."
            )
            report(f"  warnings: {typo_context.get('warnings')!r}")
            return 1
        if "change-close --action" in typo_warnings:
            report(
                f"{label} M2 a genuine typo (`deploy`) still received the "
                "sync-specific sentence inside `keel context`'s warning."
            )
            report(f"  warnings: {typo_context.get('warnings')!r}")
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def standing_authorization_task(boundary: str = "") -> str:
    return (
        "- [ ] 1.1 Behavior\n"
        "  - Covers:\n"
        "    - E1: public behavior\n"
        "  - Touch:\n"
        "    - src/feature.js\n"
        "  - Verify:\n"
        "    - Strategy: evidence-first\n"
        "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "    - M1: node test.js proves the public behavior\n"
        + boundary
        + "  - Evidence:\n"
        "    - Contract: pending\n"
        "    - M1: pending\n"
        "    - Review:\n"
        "      - Status: pending\n"
        "      - Acceptance check: pending\n"
        "      - Scope check: pending\n"
        "      - Findings: pending\n"
        "    - Blocker: none\n"
    )


def standing_authorization_autonomy(repo: Path) -> list[str] | None:
    result = run_keel(
        repo,
        "gate",
        "task-start",
        "--change",
        "demo",
        "--task",
        "1.1",
        "--json",
        "--no-guard",
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    contract = payload.get("contract") or {}
    capsule = contract.get("capsule") or {}
    boundaries = capsule.get("boundaries") or {}
    return boundaries.get("autonomy")


def validate_standing_authorization_inheritance_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-authinherit-") as raw_tmp:
        root = Path(raw_tmp)

        # M1 — a task that authored no boundary inherits the declaration, and
        # the capsule says where the authorization came from.
        inherits = root / "inherits"
        inherits.mkdir()
        write_gate_fixture(inherits, standing_authorization_task())
        write_authorize_config(inherits, "authorize:\n  - commit\n")
        autonomy = standing_authorization_autonomy(inherits)
        if autonomy is None:
            report("standing-authorization-inheritance: task-start returned no capsule autonomy.")
            return 1
        inherited = [entry for entry in autonomy if "commit" in entry]
        if not inherited:
            report(
                "standing-authorization-inheritance: a declared action did not "
                f"reach the capsule autonomy boundary: {autonomy}"
            )
            return 1
        if not any("keel/config.yaml" in entry for entry in inherited):
            report(
                "standing-authorization-inheritance: the inherited entry does "
                f"not name the repository declaration as its source: {autonomy}"
            )
            return 1

        # M2 — an authored boundary is returned unchanged, with nothing
        # inherited beside it.
        authored = root / "authored"
        authored.mkdir()
        write_gate_fixture(
            authored,
            standing_authorization_task(
                "  - Autonomy boundary:\n"
                "    - Default: hard-stop\n"
                "    - Pre-authorized fallback: revert the fixture file and record M1\n"
            ),
        )
        write_authorize_config(authored, "authorize:\n  - commit\n  - push\n")
        autonomy = standing_authorization_autonomy(authored)
        if autonomy is None:
            report("standing-authorization-inheritance: authored-boundary task did not compile.")
            return 1
        if "Pre-authorized fallback: revert the fixture file and record M1" not in autonomy:
            report(
                "standing-authorization-inheritance: the authored boundary was "
                f"not preserved: {autonomy}"
            )
            return 1
        if any("keel/config.yaml" in entry for entry in autonomy):
            report(
                "standing-authorization-inheritance: the declaration overrode an "
                f"authored boundary: {autonomy}"
            )
            return 1

        # M3 — an action the declaration does not name still hard-stops.
        autonomy = standing_authorization_autonomy(inherits)
        if autonomy is None:
            report("standing-authorization-inheritance: re-compilation returned no autonomy.")
            return 1
        if any("push" in entry or "release" in entry for entry in autonomy):
            report(
                "standing-authorization-inheritance: an undeclared action was "
                f"authorized: {autonomy}"
            )
            return 1
        if not any(entry.startswith("Default: hard-stop") for entry in autonomy):
            report(
                "standing-authorization-inheritance: the hard-stop default "
                f"disappeared for undeclared actions: {autonomy}"
            )
            return 1

    report("standing-authorization-inheritance scenario passed.")
    return 0


def write_precedent(
    store: Path,
    name: str,
    *,
    category: str = "external interface",
    status: str = "recorded",
    decision: str = "Return 404 rather than 200 with an empty body.",
    rationale: str | None = "A 200 teaches every caller to parse the body to learn it failed.",
) -> None:
    store.mkdir(parents=True, exist_ok=True)
    body = (
        f"# {name}\n\n"
        f"Applies when: a handler must report that a resource is absent.\n\n"
        f"- Category: {category}\n"
        f"- Status: {status}\n\n"
        "## Decision\n\n"
        f"{decision}\n"
    )
    if rationale is not None:
        body += f"\n## Rationale\n\n{rationale}\n"
    (store / f"{name}.md").write_text(body, encoding="utf-8")


def validate_precedent_store_declaration_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-precedent-") as raw_tmp:
        root = Path(raw_tmp)

        # A store deliberately placed OUTSIDE every repository that reads it.
        shared = root / "shared-store"
        write_precedent(shared, "absent-resource-status")
        write_precedent(shared, "irreversible-cost", status="authorized")

        def declare(repo: Path, store: str | None) -> None:
            (repo / "keel").mkdir(parents=True, exist_ok=True)
            body = "fast_check: echo check\n"
            if store is not None:
                body += f"precedents: {store}\n"
            (repo / "keel" / "config.yaml").write_text(body, encoding="utf-8")

        # M1 — a declared, existing store is reported with its counts.
        declared = root / "declared"
        declared.mkdir()
        declare(declared, str(shared).replace("\\", "/"))
        out = run_keel(declared, "--doctor").stdout
        if "Precedent store:" not in out:
            report("precedent-store: doctor has no precedent surface.")
            report(out)
            return 1
        for needle in ("precedents: 2", "authorized: 1"):
            if needle not in out:
                report(f"precedent-store: doctor does not report {needle}.")
                report(out)
                return 1

        # M1 (continued) — an undeclared store leaves every surface alone.
        silent = root / "silent"
        silent.mkdir()
        declare(silent, None)
        silent_out = run_keel(silent, "--doctor").stdout
        if "precedents: none" not in silent_out:
            report("precedent-store: an undeclared store is not reported as none.")
            report(silent_out)
            return 1
        if "fast_check: ok - declared in keel/config.yaml: echo check" not in silent_out:
            report("precedent-store: the fast_check surface changed.")
            report(silent_out)
            return 1

        # M2 — two repositories declaring the same out-of-tree path read the
        # same precedents, which is the whole point of a declarable path.
        second = root / "second"
        second.mkdir()
        declare(second, str(shared).replace("\\", "/"))
        second_out = run_keel(second, "--doctor").stdout
        if "precedents: 2" not in second_out or "authorized: 1" not in second_out:
            report("precedent-store: a second repo did not read the shared store.")
            report(second_out)
            return 1

        # M2 (continued) — a declared path that does not exist degrades to the
        # no-store behavior. This is the state CI and every clone land in.
        missing = root / "missing"
        missing.mkdir()
        declare(missing, str(root / "not-here").replace("\\", "/"))
        missing_result = run_keel(missing, "--doctor")
        if "precedents: none" not in missing_result.stdout:
            report("precedent-store: a missing store path did not degrade to none.")
            report(missing_result.stdout)
            return 1
        if missing_result.returncode != run_keel(silent, "--doctor").returncode:
            report("precedent-store: a missing store path changed the doctor exit code.")
            return 1

        # M3 — completeness is a presence check, not a judgement.
        incomplete_store = root / "incomplete-store"
        write_precedent(incomplete_store, "no-reason", rationale=None)
        incomplete = root / "incomplete"
        incomplete.mkdir()
        declare(incomplete, str(incomplete_store).replace("\\", "/"))
        out = run_keel(incomplete, "--doctor").stdout
        if "incomplete: 1" not in out or "no-reason" not in out:
            report("precedent-store: a precedent with no rationale was not named incomplete.")
            report(out)
            return 1

        opaque_store = root / "opaque-store"
        write_precedent(opaque_store, "unevaluable", rationale="qqq")
        opaque = root / "opaque"
        opaque.mkdir()
        declare(opaque, str(opaque_store).replace("\\", "/"))
        out = run_keel(opaque, "--doctor").stdout
        if "incomplete: 0" not in out:
            report(
                "precedent-store: a rationale Keel cannot evaluate was reported "
                "incomplete; the check must be presence, not judgement."
            )
            report(out)
            return 1

        # M4 — reading a store performs no network access.
        #
        # Proxy environment variables do NOT prove this: Node's fetch ignores
        # HTTP_PROXY entirely, so a run under them passes whether or not the
        # code reaches the network. Instead, preload a module that makes every
        # network primitive throw. Then a passing run is evidence that none was
        # called, and any added network call fails loudly.
        guard = root / "no-network.cjs"
        guard.write_text(
            "const fail = (what) => {\n"
            "  throw new Error('network attempted: ' + what);\n"
            "};\n"
            "require('net').Socket.prototype.connect = () => fail('net.connect');\n"
            "const http = require('http');\n"
            "http.request = () => fail('http.request');\n"
            "http.get = () => fail('http.get');\n"
            "const https = require('https');\n"
            "https.request = () => fail('https.request');\n"
            "https.get = () => fail('https.get');\n"
            "const dns = require('dns');\n"
            "dns.lookup = () => fail('dns.lookup');\n"
            "dns.resolve = () => fail('dns.resolve');\n"
            "globalThis.fetch = () => fail('fetch');\n",
            encoding="utf-8",
        )
        env = dict(os.environ)
        env["NODE_OPTIONS"] = f"--require {str(guard).replace(chr(92), '/')}"
        offline = run_keel(declared, "--doctor", env=env)
        if "precedents: 2" not in offline.stdout:
            report(
                "precedent-store: reading the store attempted network access, "
                "or failed under the no-network guard."
            )
            report((offline.stderr or offline.stdout).strip())
            return 1

    report("precedent-store-declaration scenario passed.")
    return 0


def validate_triage_declaration_scenario() -> int:
    """Which work may start without asking is a declaration, never an inference.

    The command must evaluate what it is handed. Keel does not fetch the issue,
    because a gate that reaches the network trades the local, offline,
    deterministic evaluation that makes its answer worth anything.
    """

    def declare(repo: Path, body: str | None) -> None:
        (repo / "keel").mkdir(parents=True, exist_ok=True)
        text = "fast_check: echo check\n"
        if body is not None:
            text += body
        (repo / "keel" / "config.yaml").write_text(text, encoding="utf-8")

    def triage(repo: Path, labels: str, env: dict | None = None) -> dict | None:
        result = run_keel(repo, "triage", ".", "--labels", labels, "--json", env=env)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return None

    with tempfile.TemporaryDirectory(prefix="keel-triage-") as raw_tmp:
        root = Path(raw_tmp)

        # M1 — a declared label admits; anything else is refused by name.
        declared = root / "declared"
        declared.mkdir()
        declare(declared, "triage:\n  - auto\n")
        admitted = triage(declared, "auto,bug")
        if admitted is None or admitted.get("status") != "admit":
            report(f"triage: a declared label did not admit: {admitted}")
            return 1
        if "auto" not in (admitted.get("reason") or ""):
            report(f"triage: the admission does not name the label: {admitted}")
            return 1
        refused = triage(declared, "bug,docs")
        if refused is None or refused.get("status") != "refuse":
            report(f"triage: an undeclared label was admitted: {refused}")
            return 1
        reason = refused.get("reason") or ""
        for needle in ("bug", "docs", "auto"):
            if needle not in reason:
                report(
                    "triage: the refusal must name both the labels carried and "
                    f"the labels accepted; missing {needle}: {reason}"
                )
                return 1

        # M2 — no policy refuses everything, and says so in those words.
        for label, body in (("absent", None), ("empty", "triage:\n")):
            silent = root / label
            silent.mkdir()
            declare(silent, body)
            result = triage(silent, "auto")
            if result is None or result.get("status") != "refuse":
                report(f"triage: the {label} policy admitted an issue: {result}")
                return 1
            reason = result.get("reason") or ""
            if "no triage policy" not in reason.lower():
                report(
                    f"triage: the {label} refusal does not distinguish an "
                    f"undeclared policy from an unsuitable issue: {reason}"
                )
                return 1
            out = run_keel(silent, "--doctor").stdout
            if "triage: none" not in out:
                report(f"triage: doctor does not report the {label} triage surface.")
                report(out)
                return 1
        out = run_keel(declared, "--doctor").stdout
        if "Unattended triage:" not in out or "triage: ok" not in out:
            report("triage: doctor does not report a declared triage surface.")
            report(out)
            return 1

        # M3 — no network, and the same inputs give the same answer.
        guard = root / "no-network.cjs"
        guard.write_text(
            "const fail = (what) => {\n"
            "  throw new Error('network attempted: ' + what);\n"
            "};\n"
            "require('net').Socket.prototype.connect = () => fail('net.connect');\n"
            "const http = require('http');\n"
            "http.request = () => fail('http.request');\n"
            "http.get = () => fail('http.get');\n"
            "const https = require('https');\n"
            "https.request = () => fail('https.request');\n"
            "https.get = () => fail('https.get');\n"
            "const dns = require('dns');\n"
            "dns.lookup = () => fail('dns.lookup');\n"
            "globalThis.fetch = () => fail('fetch');\n",
            encoding="utf-8",
        )
        env = dict(os.environ)
        env["NODE_OPTIONS"] = f"--require {str(guard).replace(chr(92), '/')}"
        # Two distinct failures, reported distinctly. Collapsing them would let
        # a wrong verdict be reported as a network attempt, which sends the
        # reader to the wrong place — the exact diagnostic failure this repo
        # already has a rule against.
        offline = triage(declared, "auto", env=env)
        if offline is None:
            report(
                "triage: no JSON under the no-network guard, so evaluation "
                "attempted network access or crashed."
            )
            return 1
        if offline.get("status") != "admit":
            report(
                "triage: the offline run reached a different verdict than the "
                f"online one: {offline}"
            )
            return 1
        again = triage(declared, "auto", env=env)
        if offline != again:
            report(f"triage: the same inputs gave different answers: {offline} != {again}")
            return 1

    report("triage-declaration scenario passed.")
    return 0


def validate_triage_admits_from_the_repository_scenario() -> int:
    """The owner's decision belongs in the owner's file, not on the reporter's issue.

    A label records "this may run unattended" in a field the person who filed
    the issue can see, in the vocabulary they were asked to file under. The
    second source moves that decision into keel/config.yaml without giving it
    up to inference: a number is applied by hand to one issue, exactly as a
    label is. Reported as #62.
    """

    def declare(repo: Path, body: str) -> None:
        (repo / "keel").mkdir(parents=True, exist_ok=True)
        (repo / "keel" / "config.yaml").write_text(
            f"fast_check: echo check\n{body}", encoding="utf-8"
        )

    def triage(repo: Path, *args: str) -> dict | None:
        result = run_keel(repo, "triage", ".", *args, "--json")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            # Reported here rather than at the call site. "did not admit" and
            # "did not run" are two different diagnoses, and a caller checking
            # `verdict is None or verdict["status"] != "admit"` would send the
            # reader looking for a verdict in a run that produced none.
            report(
                f"keel triage {' '.join(args)} printed no JSON "
                f"(exit {result.returncode}): "
                f"{(result.stderr or result.stdout).strip()}"
            )
            return None

    def make(root: Path, name: str, body: str) -> Path:
        repo = root / name
        repo.mkdir()
        declare(repo, body)
        return repo

    nested = "triage:\n  labels:\n    - auto\n  issues:\n    - 62\n"

    with tempfile.TemporaryDirectory(prefix="keel-triage-repo-") as raw_tmp:
        root = Path(raw_tmp)

        # M1 — a number listed in the repository's own file admits, and says so.
        numbers = make(root, "numbers", "triage:\n  issues:\n    - 62\n    - 58\n")
        admitted = triage(numbers, "--issue", "62", "--labels", "bug")
        if admitted is None or admitted.get("status") != "admit":
            report(f"M1 a declared issue number did not admit: {admitted}")
            return 1
        reason = admitted.get("reason") or ""
        if "62" not in reason or "keel/config.yaml" not in reason:
            report(
                "M1 the admission does not name the number and the file that "
                f"lists it, so a reader cannot tell which source answered: {reason}"
            )
            return 1
        if admitted.get("sources") != ["issue"]:
            report(f"M1 the admitting source is not reported as the issue: {admitted}")
            return 1
        refused = triage(numbers, "--issue", "61", "--labels", "bug")
        if refused is None or refused.get("status") != "refuse":
            report(f"M1 an unlisted number was admitted: {refused}")
            return 1

        # M2 — the flat form is what every installed repository has. Its
        # entries keep their exact meaning, down to the reason text, and none
        # of them is read as a number.
        flat = make(root, "flat", "triage:\n  - auto\n")
        legacy_admit = triage(flat, "--labels", "auto,bug")
        if legacy_admit is None or legacy_admit.get("status") != "admit":
            report(f"M2 the bare list stopped admitting its labels: {legacy_admit}")
            return 1
        expected_admit = (
            "admitted by declared label auto; admission starts work and decides "
            "nothing after it — every later gate still applies and a material "
            "decision still stops for the owner."
        )
        if (legacy_admit.get("reason") or "") != expected_admit:
            report(
                "M2 the bare list's admission reason changed from the 5.23.0 "
                f"text: {legacy_admit.get('reason')!r}"
            )
            return 1
        if legacy_admit.get("sources") != ["label"]:
            report(f"M2 the bare list's admitting source is not the label: {legacy_admit}")
            return 1
        legacy_refuse = triage(flat, "--labels", "bug")
        expected_refuse = "the issue carries bug and this repository accepts auto."
        if legacy_refuse is None or legacy_refuse.get("status") != "refuse":
            report(f"M2 the bare list admitted an undeclared label: {legacy_refuse}")
            return 1
        if (legacy_refuse.get("reason") or "") != expected_refuse:
            report(
                "M2 the bare list's refusal reason changed from the 5.23.0 "
                f"text: {legacy_refuse.get('reason')!r}"
            )
            return 1
        # The entry is the label `auto`, not the number 62 — a bare token must
        # not have been reclassified, because that would move an authorization
        # boundary in a repository nobody edited.
        by_number = triage(flat, "--issue", "62", "--labels", "bug")
        if by_number is None or by_number.get("status") != "refuse":
            report(f"M2 a bare list entry was read as an issue number: {by_number}")
            return 1

        # M2 — and either source admits alone when both are declared.
        both = make(root, "both", nested)
        for args, source in (
            (("--labels", "auto"), "label"),
            (("--issue", "62"), "issue"),
        ):
            verdict = triage(both, *args)
            if verdict is None or verdict.get("status") != "admit":
                report(f"M2 the {source} source did not admit alone: {verdict}")
                return 1
        neither = triage(both, "--labels", "bug", "--issue", "7")
        if neither is None or neither.get("status") != "refuse":
            report(f"M2 an issue matching neither source was admitted: {neither}")
            return 1
        neither_reason = neither.get("reason") or ""
        for needle in ("bug", "7", "auto", "62"):
            if needle not in neither_reason:
                report(
                    "M2 the refusal must name what the issue carried and both "
                    f"halves of what is accepted; missing {needle}: {neither_reason}"
                )
                return 1

        # M3 — a declaration Keel cannot fully read admits nothing, including
        # the half it did read, and names the part that failed.
        unreadable = {
            "hash": ("triage:\n  issues:\n    - '#62'\n  labels:\n    - auto\n", "#62"),
            "unknown-key": (
                "triage:\n  authors:\n    - someone\n  labels:\n    - auto\n",
                "authors",
            ),
            "mixed": ("triage:\n  - auto\n  issues:\n    - 62\n", "auto"),
            "inline": ("triage: { issues: [62] }\n", "issues"),
        }
        undeclared = make(root, "undeclared", "")
        undeclared_reason = (triage(undeclared, "--labels", "auto") or {}).get(
            "reason"
        ) or ""
        for name, (body, needle) in unreadable.items():
            repo = make(root, name, body)
            # Every fixture above carries something Keel *did* read — the label
            # `auto`, or the number 62. A partial read would admit here.
            verdict = triage(repo, "--labels", "auto", "--issue", "62")
            if verdict is None or verdict.get("status") != "refuse":
                report(
                    f"M3 the {name} declaration admitted on the half Keel could "
                    f"read: {verdict}"
                )
                return 1
            reason = verdict.get("reason") or ""
            if needle not in reason:
                report(
                    f"M3 the {name} refusal does not name the entry it could not "
                    f"read ({needle}): {reason}"
                )
                return 1
            if reason == undeclared_reason:
                report(
                    f"M3 the {name} refusal is word for word the undeclared-policy "
                    "refusal, so a broken declaration reads as an absent one."
                )
                return 1
            if "could not" not in reason.lower():
                report(f"M3 the {name} refusal does not say it could not read: {reason}")
                return 1

        # M3 — and the CLI refuses the same spelling it refuses in the file,
        # and refuses to answer with no issue attributes at all.
        hashed = run_keel(numbers, "triage", ".", "--issue", "#62")
        if hashed.returncode == 0:
            report("M3 --issue accepted a number Keel refuses in the declaration.")
            return 1
        empty = run_keel(numbers, "triage", ".")
        if empty.returncode == 0:
            report("M3 triage answered with neither labels nor an issue number.")
            return 1

        # M4 — what may start work here is answerable from one command.
        doctor_both = run_keel(both, "--doctor").stdout
        if "Unattended triage:" not in doctor_both or "triage: ok" not in doctor_both:
            report(f"M4 doctor does not report a declared triage surface:\n{doctor_both}")
            return 1
        for needle in ("auto", "62"):
            if needle not in doctor_both:
                report(
                    f"M4 doctor omits the declared {needle} source, so the surface "
                    f"under-reports what may start work:\n{doctor_both}"
                )
                return 1
        doctor_numbers = run_keel(numbers, "--doctor").stdout
        if "triage: ok" not in doctor_numbers or "62" not in doctor_numbers:
            report(f"M4 doctor does not report an issues-only policy:\n{doctor_numbers}")
            return 1
        if "labelled" in doctor_numbers:
            report(
                "M4 doctor names labels for a repository that declared none:\n"
                f"{doctor_numbers}"
            )
            return 1
        doctor_broken = run_keel(root / "hash", "--doctor").stdout
        if "triage: ok" in doctor_broken:
            report(
                "M4 doctor reports an unreadable declaration as a working policy:\n"
                f"{doctor_broken}"
            )
            return 1
        if "#62" not in doctor_broken:
            report(
                "M4 doctor does not name what it could not read, so the owner "
                f"cannot tell a broken declaration from an absent one:\n{doctor_broken}"
            )
            return 1

    # M5 — the surfaces an owner reads must state the second source. Phrases,
    # not keywords: "issue number" appearing anywhere would satisfy a keyword
    # check while the page still teaches that a label is the only unit. The
    # alignment skill points at the protocol's own statement instead of
    # repeating it (keel-unattended-triage's "A secondary surface points
    # instead of repeating" scenario), so only the three full surfaces below
    # are held to the phrase itself; the skill copies are held to the pointer.
    full_surfaces = {
        "config": ROOT / "keel/config.yaml",
        "protocol": ROOT / "AGENTS.md",
        "readme": ROOT / "README.md",
    }
    stale = "A label is the unit"
    for label, path in full_surfaces.items():
        if not path.is_file():
            report(f"M5 missing surface: {path}")
            return 1
        content = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
        if "issue number" not in content:
            report(f"M5 {label} does not state the issue-number source: {path}")
            return 1
        if stale in content:
            report(
                f"M5 {label} still says {stale!r}, which stopped being true when "
                f"a second source was declared: {path}"
            )
            return 1

    canonical = ROOT / "src/skills/align-expectations/SKILL.md"
    distributed = ROOT / PLUGIN_ROOT / "skills/align-expectations/SKILL.md"
    for label, path in (("canonical skill", canonical), ("distributed skill", distributed)):
        if not path.is_file():
            report(f"M5 missing surface: {path}")
            return 1
        content = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
        if "AGENTS.md" not in content or "states no separate copy" not in content:
            report(
                f"M5 {label} does not point to the protocol's issue-number "
                f"statement: {path}"
            )
            return 1
    if canonical.read_bytes() != portable_projection_bytes(distributed):
        report("M5 the canonical and distributed skills diverged.")
        return 1

    report("triage-admits-from-the-repository scenario passed.")
    return 0


def validate_delegation_resident_text_scenario() -> int:
    """The resident protocol, the config header, and both templates agree.

    Every one of these states a default that a declaration now changes, and a
    default stated unconditionally is the thing a reader trusts.
    """

    def flat(path: Path) -> str:
        return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))

    # M1 — the resident protocol carries the subagent rule and the model limit.
    # Since #414 a subagent is the model's choice and is treated as the main
    # agent is; the gates and the Touch guard are what bind it.
    agents = ROOT / "AGENTS.md"
    text = flat(agents)
    for needle in (
        "is the model's choice and is treated as the main agent is",
        "the evidence rules apply to whoever runs a step",
        "never a model name",
        "declared rather than inferred from a task's size",
    ):
        if re.sub(r"\s+", " ", needle) not in text:
            report(f"delegation-resident-text: AGENTS.md omits: {needle}")
            return 1

    # M1 — the consumer bootstrap carries the subagent sentence, not the
    # delegation clause. Its block has a byte budget (BOOTSTRAP_BLOCK_BYTE_BUDGET)
    # with little headroom, and delegation is inert until declared, so an
    # installing repository that declares nothing is fully served by the
    # sentence already there. What the check enforces is that the sentence stays
    # true by default, and that the budget is not quietly spent later — the
    # budget moved once, in 5.63.0 for the routing rule (#131), with the argument
    # recorded at the constant; a raise with no reason beside it is the drift
    # this guards.
    bootstrap = ROOT / "assets/bootstrap/AGENTS.md"
    boot = flat(bootstrap)
    if re.sub(r"\s+", " ", "is the model's choice and is treated as the main agent is") not in boot:
        report("delegation-resident-text: the bootstrap lost its subagent sentence.")
        return 1
    block = bootstrap.read_text(encoding="utf-8")
    body = block.split("<!-- keel:start", 1)[1].split("<!-- keel:end -->", 1)[0]
    size = len(("<!-- keel:start" + body + "<!-- keel:end -->").encode())
    if size >= BOOTSTRAP_BLOCK_BYTE_BUDGET:
        report(
            f"delegation-resident-text: the bootstrap block is {size} bytes, "
            f"over its {BOOTSTRAP_BLOCK_BYTE_BUDGET}-byte budget."
        )
        return 1

    # M1 — the config header counts its declarations correctly.
    config = ROOT / "keel/config.yaml"
    cfg = flat(config)
    # Derived from the module that reads the declarations, not restated here. The
    # literal this replaces had been hand-bumped twice, and the second bump was
    # found by a red suite run in a scenario named for something else (#143).
    declarations = [
        name
        for name in run_node_expression(
            ROOT,
            "process.stdout.write("
            "require('./src/core/config.js').CONFIG_DECLARATIONS.join(','))",
        ).strip().split(",")
        if name
    ]
    if not declarations:
        report(
            "delegation-resident-text: src/core/config.js exports no declaration "
            "list, so the header cannot be checked against what Keel reads."
        )
        return 1
    header_problem = config_header_problem(declarations, cfg)
    if header_problem:
        report(f"delegation-resident-text: {header_problem}")
        return 1

    # M2 — both task templates state the new default, and the source and its
    # installed copy stay byte-identical.
    source = ROOT / "assets/openspec/schemas/keel-spec-driven/templates/tasks.md"
    installed = ROOT / "openspec/schemas/keel-spec-driven/templates/tasks.md"
    for path in (source, installed):
        body = flat(path)
        # Since #414 the template states the subagent sentence and the default
        # continuation, and no longer limits helpers or delegates.
        if re.sub(r"\s+", " ", "subagent is the model's choice, treated as the main agent is") not in body:
            report(f"delegation-resident-text: {path.relative_to(ROOT)} does not state the subagent default.")
            return 1
        if "cross-task continuation stay unauthorized" in body:
            report(f"delegation-resident-text: {path.relative_to(ROOT)} still says continuing needs authorization.")
            return 1
    if source.read_bytes() != installed.read_bytes():
        report("delegation-resident-text: the template source and its installed copy diverged.")
        return 1

    report("delegation-resident-text scenario passed.")
    return 0


def validate_delegation_overlay_scenario() -> int:
    """The overlay tells a delegate what it may do and what it settles.

    A subagent reading only this text must not conclude it can complete a
    task, and must not conclude it may implement without a declaration.
    """

    generated = [
        ROOT / ".claude/skills/openspec-apply-change/SKILL.md",
        ROOT / ".claude/skills/openspec-archive-change/SKILL.md",
        ROOT / ".codex/skills/openspec-apply-change/SKILL.md",
        ROOT / ".codex/skills/openspec-archive-change/SKILL.md",
    ]
    for path in generated:
        if not path.exists():
            report(f"delegation-overlay: missing generated surface {path.relative_to(ROOT)}")
            return 1

    # M1 — the surface says what binds a subagent and nothing else (#414): it
    # is the model's choice and is treated as the main agent is. Asserted on
    # every generated copy, because the overlay is what a subagent on that
    # surface actually reads.
    needles = (
        "A subagent is the model's choice and is treated as the main agent is",
        "the `Touch` write guard, and the evidence rules apply to whoever runs a step",
    )
    for path in generated:
        text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
        for needle in needles:
            if re.sub(r"\s+", " ", needle) not in text:
                report(f"delegation-overlay: {path.relative_to(ROOT)} omits: {needle}")
                return 1
        # The old unconditional sentence must be gone, or a reader finds both
        # and has to guess which one governs.
        # Both stale sentences, not just the one in the shared gate. The apply
        # action body carried its own copy, and a surface stating the rule
        # unconditionally beside the conditional one leaves a delegate free to
        # cite whichever it prefers.
        for stale in (
            "Target-native subagents return report/evidence only; the current agent reviews the output before acting.",
            "Target-native subagents return report/evidence only; they cannot mark tasks complete",
            "Delegation is refused with no active guard manifest",
            "re-runs each `M<n>` check itself before recording Evidence",
        ):
            if re.sub(r"\s+", " ", stale) in text:
                report(f"delegation-overlay: {path.relative_to(ROOT)} still carries an unconditional sentence: {stale[:60]}")
                return 1

    # M2 — every copy of a given action carries a byte-identical overlay
    # block. bin/keel.js exports nothing, so the generator cannot be called
    # directly; comparing the copies to each other catches the failure that
    # matters — one surface hand-edited or left stale while the others move.
    blocks: dict[str, dict[str, str]] = {"apply": {}, "archive": {}}
    for path in generated:
        text = path.read_text(encoding="utf-8")
        try:
            body = text.split("<!-- keel:openspec-surface-overlay", 1)[1]
            body = body.split("<!-- keel:openspec-surface-overlay:end -->", 1)[0]
        except IndexError:
            report(f"delegation-overlay: {path.relative_to(ROOT)} carries no overlay block.")
            return 1
        action = "archive" if "archive" in str(path).lower() else "apply"
        blocks[action][str(path.relative_to(ROOT))] = body
    for action, copies in blocks.items():
        if len(copies) < 2:
            continue
        first_name, first_body = next(iter(copies.items()))
        for name, body in copies.items():
            if body != first_body:
                report(
                    f"delegation-overlay: the {action} overlay diverged between "
                    f"{first_name} and {name}."
                )
                return 1

    report("delegation-overlay scenario passed.")
    return 0


def validate_delegation_guard_binds_scenario() -> int:
    """The guard binds a delegated writer identically, and always did.

    This change added no enforcement. It was verified by probe on 2026-08-01 —
    a spawned subagent's write outside Touch was denied with the same message
    the current agent receives, while its write inside Touch succeeded — and
    that probe is fixed here so the property cannot regress unnoticed.

    The manifest scopes a repository and a task, never the identity of the
    process performing the write, which is why nothing had to be built.
    """

    def event(repo: Path, target: str) -> dict:
        return {
            "cwd": str(repo),
            "tool_name": "Write",
            "tool_input": {"file_path": str(repo / target)},
            # A delegate is the same hook input with an agent identity on it.
            # If enforcement ever keyed on this, the assertions below diverge.
            "agent_id": "probe-delegate",
            "agent_type": "general-purpose",
        }

    with tempfile.TemporaryDirectory(
        prefix="keel-delguard-", ignore_cleanup_errors=True
    ) as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()
        write_text(repo / "openspec/changes/demo/tasks.md", guard_task_fixture())
        write_text(repo / "src/feature.js", "// fixture\n")
        write_text(repo / "README.md", "fixture\n")
        started = run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
        )
        if started.returncode != 0:
            report("delegation-guard-binds: task-start did not arm the guard.")
            report((started.stderr or started.stdout).strip())
            return 1

        # M1 — outside Touch is denied, and with the same reason the current
        # agent receives. The two decisions are compared rather than each
        # checked for the word "deny", so a delegate-specific message would
        # fail here even though it also denied.
        delegate = pretooluse_decision(run_pretooluse_guard_hook(repo, event(repo, "README.md")))
        current = run_pretooluse_guard_hook(repo, {
            "cwd": str(repo),
            "tool_name": "Write",
            "tool_input": {"file_path": str(repo / "README.md")},
        })
        agent = pretooluse_decision(current)
        if delegate is None:
            report("delegation-guard-binds: a delegate's out-of-Touch write was not decided.")
            return 1
        if delegate.get("permissionDecision") != "deny":
            report(f"delegation-guard-binds: a delegate wrote outside Touch: {delegate}")
            return 1
        if delegate != agent:
            report(
                "delegation-guard-binds: a delegate received a different decision "
                f"than the current agent: {delegate} != {agent}"
            )
            return 1

        # M1 control — inside Touch succeeds. Without this, a hook that denied
        # everything would satisfy the assertion above, and the original probe
        # would have proven only that subagents cannot write at all.
        allowed = pretooluse_decision(run_pretooluse_guard_hook(repo, event(repo, "src/feature.js")))
        if allowed is not None and allowed.get("permissionDecision") == "deny":
            report(f"delegation-guard-binds: a delegate's in-Touch write was denied: {allowed}")
            return 1

        # M2 — every manifest state applies to a delegate.
        manifest = repo / "keel/guard.json"
        saved = manifest.read_text(encoding="utf-8")

        manifest.write_text("{ not json", encoding="utf-8")
        corrupt = pretooluse_decision(run_pretooluse_guard_hook(repo, event(repo, "src/feature.js")))
        if corrupt is None or corrupt.get("permissionDecision") != "deny":
            report(f"delegation-guard-binds: an invalid manifest did not fail closed: {corrupt}")
            return 1
        # And the repository boundary still precedes every manifest decision.
        outside = pretooluse_decision(run_pretooluse_guard_hook(repo, {
            "cwd": str(repo),
            "tool_name": "Write",
            "tool_input": {"file_path": str(Path(raw_tmp) / "outside.txt")},
            "agent_id": "probe-delegate",
            "agent_type": "general-purpose",
        }))
        if outside is not None and outside.get("permissionDecision") == "deny":
            report(f"delegation-guard-binds: an out-of-repository path was denied: {outside}")
            return 1
        manifest.write_text(saved, encoding="utf-8")

        # Drift is asserted on a non-record authority entry. The manifest's own
        # `openspec/changes/<change>/tasks.md` is deliberately exempt — that is
        # the record layer, where a checkbox and Evidence are written during the
        # task — so drifting it must NOT deny, and asserting otherwise would
        # assert the opposite of the spec.
        record_only = json.loads(saved)
        record_only["authority"][0]["sha256"] = "0" * 64
        manifest.write_text(json.dumps(record_only, indent=2) + "\n", encoding="utf-8")
        record_drift = pretooluse_decision(run_pretooluse_guard_hook(repo, event(repo, "src/feature.js")))
        if record_drift is not None and record_drift.get("permissionDecision") == "deny":
            report(
                "delegation-guard-binds: a changed record-layer file was treated "
                f"as authority drift: {record_drift}"
            )
            return 1

        drifted = json.loads(saved)
        drifted["authority"].append({
            "path": "src/feature.js",
            "sha256": "0" * 64,
        })
        manifest.write_text(json.dumps(drifted, indent=2) + "\n", encoding="utf-8")
        drift = pretooluse_decision(run_pretooluse_guard_hook(repo, event(repo, "src/feature.js")))
        if drift is None or drift.get("permissionDecision") != "deny":
            report(f"delegation-guard-binds: drifted authority did not fail closed: {drift}")
            return 1
        manifest.write_text(saved, encoding="utf-8")

        write_text(repo / "openspec/changes/demo/tasks.md", guard_task_fixture(checked=True))
        checked = pretooluse_decision(run_pretooluse_guard_hook(repo, event(repo, "src/feature.js")))
        if checked is None or checked.get("permissionDecision") != "deny":
            report(f"delegation-guard-binds: a checked task still admitted a delegate write: {checked}")
            return 1

    report("delegation-guard-binds scenario passed.")
    return 0


def validate_native_capability_scope_scenario() -> int:
    """A capability the target provides natively is not Keel's to build.

    The policy file already carried procedures serving this rule — do not cede
    a surface without a coverage report, do not integrate a host surface
    without recorded design authority — but never the rule itself. A procedure
    without its rule is followed where it was written and nowhere else.
    """

    spec = ROOT / "openspec/specs/keel-surface-evolution-policy/spec.md"
    if not spec.exists():
        report("native-capability-scope: the surface evolution policy is missing.")
        return 1
    text = re.sub(r"\s+", " ", spec.read_text(encoding="utf-8"))

    # M1 — the rule, its scope limit, and the duplicate-carrier refusal.
    for needle in (
        "MUST NOT implement, wrap, or re-specify a capability the target runtime already provides natively",
        "Keel's scope is limited to declaring policy about its use",
        "extends the projection it already publishes instead of introducing a second carrier",
    ):
        if re.sub(r"\s+", " ", needle) not in text:
            report(f"native-capability-scope: the policy omits: {needle}")
            return 1

    # M1 — a conflicting surface is refused outright, not resolved by wording.
    if re.sub(r"\s+", " ", "returns to authoring instead of being resolved by precedence wording") not in text:
        report("native-capability-scope: the policy does not refuse a conflicting surface.")
        return 1

    # M2 — the thinnest surviving layer is named rather than left implicit, so
    # the rule ships with the handle a later reader needs to apply it.
    if re.sub(r"\s+", " ", "the first candidate for removal when the argument stops holding") not in text:
        report("native-capability-scope: the policy does not name the thinnest layer.")
        return 1

    # M2 — and this change's own application is recorded in its design, so the
    # requirement ships with a worked example rather than as an abstraction.
    design = ROOT / "openspec/changes/declare-who-runs-the-task/design.md"
    archived = sorted(
        ROOT.glob("openspec/changes/archive/*declare-who-runs-the-task/design.md")
    )
    if not design.exists() and archived:
        design = archived[-1]
    if not design.exists():
        report("native-capability-scope: this change's design is missing.")
        return 1
    design_text = re.sub(r"\s+", " ", design.read_text(encoding="utf-8"))
    for needle in (
        "is not a Keel design goal",
        "No separate write-capable brief contract module is built",
    ):
        if re.sub(r"\s+", " ", needle) not in design_text:
            report(f"native-capability-scope: the design omits its own application: {needle}")
            return 1

    report("native-capability-scope scenario passed.")
    return 0


def validate_review_checks_content_scenario() -> int:
    """Both checks concern content a gate can only shape-check.

    Asserted by the phrases that carry the distinguishing content. "Durable
    owner" or "diagnostic" appearing somewhere would satisfy a keyword check
    while stating neither what to look at nor when.
    """

    required = [
        # The URL owner check, and the timing that makes it useful.
        "already carry the content",
        "when it is cited",
        # The message check, and the structure that triggers it.
        "name the actual cause",
        "two distinct failures",
        # Neither belongs in a gate.
        "not a deterministic gate check",
    ]
    canonical = ROOT / "src/skills/review-checklist/SKILL.md"
    distributed = ROOT / PLUGIN_ROOT / "skills/review-checklist/SKILL.md"

    for label, path in (("canonical", canonical), ("distributed", distributed)):
        if not path.is_file():
            report(f"review-checks-content: missing {label} skill: {path}")
            return 1
        content = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
        for phrase in required:
            if phrase not in content:
                report(f"review-checks-content: {label} skill omits: {phrase}")
                return 1

    if canonical.read_bytes() != portable_projection_bytes(distributed):
        report("review-checks-content: the canonical and distributed skills diverged.")
        return 1

    report("review-checks-content scenario passed.")
    return 0


def validate_unattended_boundary_scenario() -> int:
    """The boundary must be readable where an unattended run will read it.

    Phrases, not keywords: "unattended" appearing somewhere would satisfy a
    keyword check while stating none of what a run may and may not do. The
    alignment skill points at the protocol's own statement instead of
    repeating it (keel-unattended-triage's "A secondary surface points
    instead of repeating" scenario), so only the protocol is held to the
    full phrase set; the skill copies are held to the pointer instead.
    """

    required = [
        # What a run may do, and the one thing it may not.
        "open a pull request",
        "may not merge",
        # Where the loop comes from.
        "Keel schedules nothing",
        # Stopping is the design, not a fault.
        "designed boundary rather than a failure",
        # Admission comes from a declaration, never from accumulated history.
        "never from a precedent",
    ]
    pointer_required = [
        "AGENTS.md",
        "Unattended runs",
        "states no separate copy",
    ]
    canonical = ROOT / "src/skills/align-expectations/SKILL.md"
    distributed = ROOT / PLUGIN_ROOT / "skills/align-expectations/SKILL.md"
    protocol = ROOT / "AGENTS.md"

    if not protocol.is_file():
        report(f"unattended-boundary: missing protocol: {protocol}")
        return 1
    # Collapse whitespace: these are multi-word phrases in hard-wrapped
    # prose, so raw matching would assert the line layout, not the wording.
    protocol_content = re.sub(r"\s+", " ", protocol.read_text(encoding="utf-8"))
    for phrase in required:
        if phrase not in protocol_content:
            report(f"unattended-boundary: protocol omits: {phrase}")
            return 1

    for label, path in (
        ("canonical skill", canonical),
        ("distributed skill", distributed),
    ):
        if not path.is_file():
            report(f"unattended-boundary: missing {label}: {path}")
            return 1
        content = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
        for phrase in pointer_required:
            if phrase not in content:
                report(f"unattended-boundary: {label} omits: {phrase}")
                return 1

    if canonical.read_bytes() != portable_projection_bytes(distributed):
        report("unattended-boundary: the canonical and distributed skills diverged.")
        return 1

    report("unattended-boundary scenario passed.")
    return 0


def validate_triage_admits_only_a_start_scenario() -> int:
    """Admission answers "may this begin". It answers nothing after that.

    Same two-repository shape as the standing-authorization and precedent
    inertness scenarios, and for the same reason: a comparison that passes when
    two repositories agree also passes when the declaration silently failed to
    load, so the difference is asserted before it is asserted to be inert.
    """

    complete_task = (
        "- [ ] 1.1 Behavior\n"
        "  - Covers:\n"
        "    - E1: public behavior\n"
        "  - Touch:\n"
        "    - src/feature.js\n"
        "  - Verify:\n"
        "    - Strategy: evidence-first\n"
        "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "    - M1: node test.js proves the public behavior\n"
        "  - Evidence:\n"
        "    - Contract: pending\n"
        "    - M1: node test.js printed ok\n"
        "    - Review:\n"
        "      - Status: pass\n"
        "      - Acceptance check: reviewed\n"
        "      - Scope check: reviewed\n"
        "      - Findings: none\n"
        "    - Blocker: none\n"
    )
    missing_evidence_task = complete_task.replace(
        "    - M1: node test.js printed ok\n", "    - M1: pending\n"
    )

    def gate_result(repo: Path, stage: str) -> dict | None:
        result = run_keel(
            repo, "gate", stage, "--change", "demo", "--task", "1.1", "--json"
        )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            return None
        return {
            "status": payload.get("status"),
            "problems": sorted(
                (problem.get("code", ""), problem.get("message", ""))
                for problem in payload.get("problems") or []
            ),
        }

    with tempfile.TemporaryDirectory(prefix="keel-triage-inert-") as raw_tmp:
        root = Path(raw_tmp)

        def pair(name: str, tasks: str) -> tuple[Path, Path]:
            declaring = root / f"{name}-declaring"
            declaring.mkdir()
            write_gate_fixture(declaring, tasks)
            (declaring / "keel").mkdir(parents=True, exist_ok=True)
            (declaring / "keel" / "config.yaml").write_text(
                "triage:\n  - auto\n", encoding="utf-8"
            )
            silent = root / f"{name}-silent"
            silent.mkdir()
            write_gate_fixture(silent, tasks)
            # Positive control: the two repositories must actually differ on the
            # triage surface, or every comparison below is trivially true.
            live = run_keel(declaring, "--doctor").stdout
            inert = run_keel(silent, "--doctor").stdout
            if "triage: ok" not in live:
                report(
                    f"triage-inert: the {name} declaring fixture never loaded a "
                    "triage policy; the comparisons below would be vacuous."
                )
                raise AssertionError("declaring fixture is not declaring")
            if "triage: none" not in inert:
                report(f"triage-inert: the {name} silent fixture declared a policy.")
                raise AssertionError("silent fixture is not silent")
            return declaring, silent

        # M1 — every gate stage agrees across the pair.
        declaring, silent = pair("complete", complete_task)
        for stage in ("task-start", "task-complete"):
            live = gate_result(declaring, stage)
            inert = gate_result(silent, stage)
            if live is None or inert is None:
                report(f"triage-inert: {stage} produced no JSON.")
                return 1
            if live != inert:
                report(
                    f"triage-inert: a triage policy changed the {stage} result: "
                    f"{live} != {inert}"
                )
                return 1

        # M2 — missing evidence still fails, with unchanged failure text.
        declaring, silent = pair("missing", missing_evidence_task)
        for repo in (declaring, silent):
            if gate_result(repo, "task-start") is None:
                report("triage-inert: task-start produced no JSON.")
                return 1
        live = gate_result(declaring, "task-complete")
        inert = gate_result(silent, "task-complete")
        if live is None or inert is None:
            report("triage-inert: task-complete produced no JSON.")
            return 1
        if live.get("status") == "pass":
            report(
                "triage-inert: a declared triage policy let a task with missing "
                "evidence pass completion."
            )
            return 1
        if live != inert:
            report(
                f"triage-inert: a triage policy changed the failure text: "
                f"{live} != {inert}"
            )
            return 1

    report("triage-admits-only-a-start scenario passed.")
    return 0


def validate_precedent_rules_scenario() -> int:
    """The three rules the owner accepted must be in the skill, not in a chat.

    Each is asserted by the phrase that carries its distinguishing content, not
    by a keyword: "precedent" appearing somewhere would satisfy a keyword check
    while saying none of what was decided.
    """

    required = [
        # Citation: the trigger, and its negative half.
        "would otherwise have interrupted",
        "not cited",
        # Promotion: who does it, and what does not.
        "propose the promotion",
        "no usage count",
        # No reclassification, and the reason it is a fixed point.
        "never moves a decision out of",
        "recurrence",
        # Recording: the rationale is the load-bearing field.
        "reasoning transfers",
    ]
    canonical = ROOT / "src/skills/align-expectations/SKILL.md"
    distributed = ROOT / PLUGIN_ROOT / "skills/align-expectations/SKILL.md"

    for label, path in (("canonical", canonical), ("distributed", distributed)):
        if not path.is_file():
            report(f"precedent-rules: missing {label} skill: {path}")
            return 1
        # Collapse whitespace before matching. These are multi-word phrases and
        # the file is hard-wrapped, so matching raw text would assert the line
        # layout rather than the wording — and would fail on any later reflow
        # that changed nothing.
        content = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
        for phrase in required:
            if phrase not in content:
                report(f"precedent-rules: {label} skill omits: {phrase}")
                return 1

    if canonical.read_bytes() != portable_projection_bytes(distributed):
        report("precedent-rules: the canonical and distributed skills diverged.")
        return 1

    report("precedent-rules scenario passed.")
    return 0


def validate_precedent_projection_pointer_scenario() -> int:
    """SessionStart may say how big the store is. It may not say what is in it.

    The store grows monotonically while the precedents relevant to any one
    session are a small subset, and the hook pays its cost on every session
    including post-compaction reinjection. So the projection carries counts and
    freshness; bodies load when a decision is actually being made.
    """

    def projection(repo: Path) -> tuple[str, str]:
        result = run_session_start_hook(
            repo,
            {"hook_event_name": "SessionStart", "source": "startup"},
            keel_cli=f'node "{ROOT / "bin/keel.js"}"',
        )
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        return (
            payload["hookSpecificOutput"]["additionalContext"],
            payload.get("systemMessage", ""),
        )

    with tempfile.TemporaryDirectory(prefix="keel-precproj-") as raw_tmp:
        root = Path(raw_tmp)
        store = root / "store"
        # Text that must never reach the projection. If any of it appears, a
        # body leaked where only a pointer belongs.
        write_precedent(
            store,
            "leak-canary",
            status="authorized",
            decision="NEVERAPPEARSINPROJECTION-decision",
            rationale="NEVERAPPEARSINPROJECTION-rationale",
        )
        write_precedent(store, "second")

        # The hook is silent outside a Keel repository, so both fixtures need
        # an openspec tree before the projection exists at all.
        declaring = root / "declaring"
        declaring.mkdir()
        write_text(declaring / "openspec/changes/demo/tasks.md", task_contract_fixture())
        (declaring / "keel").mkdir(parents=True)
        (declaring / "keel" / "config.yaml").write_text(
            f"precedents: {str(store).replace(chr(92), '/')}\n", encoding="utf-8"
        )
        # Two ways to declare nothing, and they reach different branches: no
        # config file at all, and a config file that declares other things.
        silent = root / "silent"
        silent.mkdir()
        write_text(silent / "openspec/changes/demo/tasks.md", task_contract_fixture())
        other_keys = root / "other-keys"
        other_keys.mkdir()
        write_text(
            other_keys / "openspec/changes/demo/tasks.md", task_contract_fixture()
        )
        (other_keys / "keel").mkdir(parents=True)
        (other_keys / "keel" / "config.yaml").write_text(
            "fast_check: echo check\nauthorize:\n  - commit\n", encoding="utf-8"
        )

        # M1 — counts and freshness, never a body.
        context, message = projection(declaring)
        combined = f"{context}\n{message}"
        if "precedents: 2" not in combined or "1 authorized" not in combined:
            report(
                "precedent-projection: the projection does not state the "
                f"precedent counts: {combined!r}"
            )
            return 1
        if "last synced" not in combined:
            report("precedent-projection: the projection does not state store freshness.")
            report(combined)
            return 1
        if "NEVERAPPEARSINPROJECTION" in combined:
            report(
                "precedent-projection: a precedent body reached the projection; "
                "only a pointer belongs there."
            )
            report(combined)
            return 1

        # M2 — an undeclared store adds nothing at all, by either route.
        for repo, label in ((silent, "no config file"), (other_keys, "other keys only")):
            quiet_context, quiet_message = projection(repo)
            if "precedent" in f"{quiet_context}\n{quiet_message}".lower():
                report(
                    f"precedent-projection: with {label}, an undeclared store "
                    "still added text to the projection."
                )
                report(quiet_context)
                return 1

    report("precedent-projection-pointer scenario passed.")
    return 0


def validate_precedent_never_weakens_scenario() -> int:
    """A precedent informs a decision. It must not stand in for a proof.

    Same shape as the standing-authorization inertness scenario, and for the
    same reason: every check passes when two repositories agree, so a store
    that silently failed to load would make each comparison trivially true.
    The positive control asserts the difference exists before asserting it is
    inert.
    """

    complete_task = (
        "- [ ] 1.1 Behavior\n"
        "  - Covers:\n"
        "    - E1: public behavior\n"
        "  - Touch:\n"
        "    - src/feature.js\n"
        "  - Verify:\n"
        "    - Strategy: evidence-first\n"
        "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "    - M1: node test.js proves the public behavior\n"
        "  - Evidence:\n"
        "    - Contract: pending\n"
        "    - M1: node test.js printed ok\n"
        "    - Review:\n"
        "      - Status: pass\n"
        "      - Acceptance check: reviewed\n"
        "      - Scope check: reviewed\n"
        "      - Findings: none\n"
        "    - Blocker: none\n"
    )
    missing_evidence_task = complete_task.replace(
        "    - M1: node test.js printed ok\n", "    - M1: pending\n"
    )

    def gate_result(repo: Path, stage: str) -> dict | None:
        result = run_keel(
            repo, "gate", stage, "--change", "demo", "--task", "1.1", "--json"
        )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            return None
        return {
            "status": payload.get("status"),
            "problems": sorted(
                (problem.get("code", ""), problem.get("message", ""))
                for problem in payload.get("problems") or []
            ),
        }

    with tempfile.TemporaryDirectory(prefix="keel-precinert-") as raw_tmp:
        root = Path(raw_tmp)
        store = root / "store"
        for name in ("first", "second", "third"):
            write_precedent(store, name, status="authorized")

        def pair(name: str, tasks: str) -> tuple[Path, Path]:
            declaring = root / f"{name}-declaring"
            declaring.mkdir()
            write_gate_fixture(declaring, tasks)
            (declaring / "keel").mkdir(parents=True, exist_ok=True)
            (declaring / "keel" / "config.yaml").write_text(
                f"precedents: {str(store).replace(chr(92), '/')}\n", encoding="utf-8"
            )
            silent = root / f"{name}-silent"
            silent.mkdir()
            write_gate_fixture(silent, tasks)
            # Positive control: prove the two repositories actually differ
            # before proving the difference changes nothing.
            live = run_keel(declaring, "--doctor").stdout
            inert = run_keel(silent, "--doctor").stdout
            if "precedents: 3" not in live or "authorized: 3" not in live:
                report(
                    f"precedent-inert: the {name} declaring fixture never loaded "
                    "its store; every comparison below would be vacuous."
                )
                raise AssertionError("declaring fixture is not declaring")
            if "precedents: none" not in inert:
                report(f"precedent-inert: the {name} silent fixture declared a store.")
                raise AssertionError("silent fixture is not silent")
            return declaring, silent

        # M1 — every gate stage agrees across the pair.
        declaring, silent = pair("complete", complete_task)
        for stage in ("task-start", "task-complete"):
            live = gate_result(declaring, stage)
            inert = gate_result(silent, stage)
            if live is None or inert is None:
                report(f"precedent-inert: {stage} produced no JSON.")
                return 1
            if live != inert:
                report(
                    f"precedent-inert: a declared store changed the {stage} "
                    f"result: {live} != {inert}"
                )
                return 1

        # M2 — missing evidence still fails, with unchanged failure text.
        declaring, silent = pair("missing", missing_evidence_task)
        for repo in (declaring, silent):
            if gate_result(repo, "task-start") is None:
                report("precedent-inert: task-start produced no JSON.")
                return 1
        live = gate_result(declaring, "task-complete")
        inert = gate_result(silent, "task-complete")
        if live is None or inert is None:
            report("precedent-inert: task-complete produced no JSON.")
            return 1
        if live.get("status") == "pass":
            report(
                "precedent-inert: a store of authorized precedents let a task "
                "with missing evidence pass completion."
            )
            return 1
        if live != inert:
            report(
                "precedent-inert: a declared store changed the failure text: "
                f"{live} != {inert}"
            )
            return 1

    report("precedent-never-weakens scenario passed.")
    return 0


def validate_standing_authorization_never_weakens_scenario() -> int:
    """A declaration removes a confirmation. It must not remove a proof.

    Every check here compares an authorizing repository against an identical
    one that declares nothing. The declaration is proven inert on the gate
    result, on the failure text, and on continuity selection — the three places
    a reader might otherwise assume authorization had bought something.
    """

    complete_task = (
        "- [ ] 1.1 Behavior\n"
        "  - Covers:\n"
        "    - E1: public behavior\n"
        "  - Touch:\n"
        "    - src/feature.js\n"
        "  - Verify:\n"
        "    - Strategy: evidence-first\n"
        "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "    - M1: node test.js proves the public behavior\n"
        "  - Evidence:\n"
        "    - Contract: pending\n"
        "    - M1: node test.js printed ok\n"
        "    - Review:\n"
        "      - Status: pass\n"
        "      - Acceptance check: reviewed\n"
        "      - Scope check: reviewed\n"
        "      - Findings: none\n"
        "    - Blocker: none\n"
    )
    missing_evidence_task = complete_task.replace(
        "    - M1: node test.js printed ok\n", "    - M1: pending\n"
    )

    def gate_result(repo: Path, stage: str) -> dict | None:
        result = run_keel(
            repo, "gate", stage, "--change", "demo", "--task", "1.1", "--json"
        )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            return None
        return {
            "status": payload.get("status"),
            "problems": sorted(
                (problem.get("code", ""), problem.get("message", ""))
                for problem in payload.get("problems") or []
            ),
        }

    def pair(root: Path, name: str, tasks: str) -> tuple[Path, Path]:
        authorizing = root / f"{name}-authorizing"
        authorizing.mkdir()
        write_gate_fixture(authorizing, tasks)
        write_authorize_config(
            authorizing,
            "authorize:\n  - commit\n  - push\n  - release\n  - archive\n"
            "  - continuation\n",
        )
        silent = root / f"{name}-silent"
        silent.mkdir()
        write_gate_fixture(silent, tasks)
        # Positive control. Every check below compares these two repositories
        # and passes when they agree, so a declaration that silently failed to
        # reach the capsule would make each comparison trivially true and prove
        # nothing. Assert the difference exists before asserting it is inert.
        live = standing_authorization_autonomy(authorizing) or []
        inert = standing_authorization_autonomy(silent) or []
        if not any("keel/config.yaml" in entry for entry in live):
            report(
                f"standing-authorization-inert: the {name} authorizing fixture "
                f"never actually authorized anything: {live}"
            )
            raise AssertionError("authorizing fixture is not authorizing")
        if any("keel/config.yaml" in entry for entry in inert):
            report(
                f"standing-authorization-inert: the {name} silent fixture "
                f"declared something: {inert}"
            )
            raise AssertionError("silent fixture is not silent")
        return authorizing, silent

    with tempfile.TemporaryDirectory(prefix="keel-authinert-") as raw_tmp:
        root = Path(raw_tmp)

        # M1 — completion returns the same status and problem set either way.
        authorizing, silent = pair(root, "complete", complete_task)
        for repo in (authorizing, silent):
            if gate_result(repo, "task-start") is None:
                report("standing-authorization-inert: task-start produced no JSON.")
                return 1
        authorized_result = gate_result(authorizing, "task-complete")
        silent_result = gate_result(silent, "task-complete")
        if authorized_result is None or silent_result is None:
            report("standing-authorization-inert: task-complete produced no JSON.")
            return 1
        if authorized_result != silent_result:
            report(
                "standing-authorization-inert: a declaration changed the "
                f"completion gate result: {authorized_result} != {silent_result}"
            )
            return 1

        # M2 — a repo authorizing every action still fails for missing evidence,
        # with unchanged failure text.
        authorizing, silent = pair(root, "missing", missing_evidence_task)
        for repo in (authorizing, silent):
            if gate_result(repo, "task-start") is None:
                report("standing-authorization-inert: task-start produced no JSON.")
                return 1
        authorized_result = gate_result(authorizing, "task-complete")
        silent_result = gate_result(silent, "task-complete")
        if authorized_result is None or silent_result is None:
            report("standing-authorization-inert: task-complete produced no JSON.")
            return 1
        if authorized_result.get("status") == "pass":
            report(
                "standing-authorization-inert: authorizing every action let a "
                "task with missing evidence pass completion."
            )
            return 1
        if authorized_result != silent_result:
            report(
                "standing-authorization-inert: a declaration changed the failure "
                f"text: {authorized_result} != {silent_result}"
            )
            return 1

        # M3 — a declaration selects nothing and starts nothing.
        def continuity(repo: Path) -> dict | None:
            result = run_keel(repo, "context", "--json")
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError:
                return None
            return {
                "status": payload.get("status"),
                "selection": payload.get("selection"),
                "nextAction": payload.get("nextAction"),
            }

        authorizing, silent = pair(root, "context", complete_task)
        authorized_context = continuity(authorizing)
        silent_context = continuity(silent)
        if authorized_context is None or silent_context is None:
            report("standing-authorization-inert: keel context produced no JSON.")
            return 1
        if authorized_context != silent_context:
            report(
                "standing-authorization-inert: a declaration changed continuity "
                f"selection: {authorized_context} != {silent_context}"
            )
            return 1

    report("standing-authorization-never-weakens scenario passed.")
    return 0


def validate_continuation_authorization_scenario() -> int:
    """`continuation` gives the between-task approval a durable home (#94).

    The fifth vocabulary name has the same nature as the four before it:
    declared, it authorizes and an inheriting capsule names its source;
    undeclared, it authorizes nothing; and the declaration stays inert to
    every gate result and to continuity selection — it removes a
    confirmation, never a proof, and it never selects the next task itself.
    """
    label = "continuation-authorization"

    complete_task = (
        "- [ ] 1.1 Behavior\n"
        "  - Covers:\n"
        "    - E1: public behavior\n"
        "  - Touch:\n"
        "    - src/feature.js\n"
        "  - Verify:\n"
        "    - Strategy: evidence-first\n"
        "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "    - M1: node test.js proves the public behavior\n"
        "  - Evidence:\n"
        "    - Contract: pending\n"
        "    - M1: node test.js printed ok\n"
        "    - Review:\n"
        "      - Status: pass\n"
        "      - Acceptance check: reviewed\n"
        "      - Scope check: reviewed\n"
        "      - Findings: none\n"
        "    - Blocker: none\n"
    )

    def gate_result(repo: Path, stage: str) -> dict | None:
        result = run_keel(
            repo, "gate", stage, "--change", "demo", "--task", "1.1", "--json"
        )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            return None
        return {
            "status": payload.get("status"),
            "problems": sorted(
                (problem.get("code", ""), problem.get("message", ""))
                for problem in payload.get("problems") or []
            ),
        }

    with tempfile.TemporaryDirectory(prefix="keel-continuation-") as raw_tmp:
        root = Path(raw_tmp)

        # M1 — declared alone, `continuation` is authorized and no repository
        # action rides along with it: commit, push, release, and archive each
        # still require their own name.
        declared = root / "declared"
        declared.mkdir()
        write_authorize_config(declared, "authorize:\n  - continuation\n")
        result = run_keel(declared, "--doctor")
        if result.returncode != 0:
            report(f"{label}: a continuation-only declaration was refused.")
            report(result.stdout + result.stderr)
            return 1
        if "continuation: authorized" not in result.stdout:
            report(f"{label}: a declared continuation was not reported authorized.")
            report(result.stdout)
            return 1
        for needle in (
            "commit: not authorized",
            "push: not authorized",
            "release: not authorized",
            "archive: not authorized",
        ):
            if needle not in result.stdout:
                report(f"{label}: undeclared action not reported: {needle}")
                report(result.stdout)
                return 1

        # M1 — undeclared, it is reported beside the four exactly as any
        # unlisted action is.
        four = root / "four"
        four.mkdir()
        write_authorize_config(
            four, "authorize:\n  - commit\n  - push\n  - release\n  - archive\n"
        )
        out = run_keel(four, "--doctor").stdout
        if "continuation: not authorized" not in out:
            report(f"{label}: an undeclared continuation was not reported.")
            report(out)
            return 1

        # M1 — a task that authored no boundary inherits it, the capsule names
        # the declaration as its source, and undeclared actions keep the
        # hard-stop default.
        write_gate_fixture(declared, standing_authorization_task())
        autonomy = standing_authorization_autonomy(declared)
        if autonomy is None:
            report(f"{label}: task-start returned no capsule autonomy.")
            return 1
        inherited = [entry for entry in autonomy if "continuation" in entry]
        if not inherited:
            report(
                f"{label}: continuation did not reach the capsule autonomy: "
                f"{autonomy}"
            )
            return 1
        if not any("keel/config.yaml" in entry for entry in inherited):
            report(
                f"{label}: the inherited entry does not name its source: "
                f"{autonomy}"
            )
            return 1
        if not any(entry.startswith("Default: hard-stop") for entry in autonomy):
            report(
                f"{label}: undeclared actions lost the hard-stop default: "
                f"{autonomy}"
            )
            return 1

        # M1 — inert to gates and selection: against an otherwise identical
        # silent repository, gate results and continuity are equal. The
        # capsule check above is the positive control — the declaration
        # demonstrably reached the capsule, so equality is not trivially true.
        inert_declared = root / "inert-declared"
        inert_declared.mkdir()
        write_gate_fixture(inert_declared, complete_task)
        write_authorize_config(inert_declared, "authorize:\n  - continuation\n")
        inert_silent = root / "inert-silent"
        inert_silent.mkdir()
        write_gate_fixture(inert_silent, complete_task)
        if any(
            "keel/config.yaml" in entry
            for entry in standing_authorization_autonomy(inert_silent) or []
        ):
            report(f"{label}: the silent fixture declared something.")
            return 1
        for repo in (inert_declared, inert_silent):
            if gate_result(repo, "task-start") is None:
                report(f"{label}: task-start produced no JSON.")
                return 1
        declared_result = gate_result(inert_declared, "task-complete")
        silent_result = gate_result(inert_silent, "task-complete")
        if declared_result is None or silent_result is None:
            report(f"{label}: task-complete produced no JSON.")
            return 1
        if declared_result != silent_result:
            report(
                f"{label}: the declaration changed a gate result: "
                f"{declared_result} != {silent_result}"
            )
            return 1

        def continuity(repo: Path) -> dict | None:
            result = run_keel(repo, "context", "--json")
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError:
                return None
            return {
                "status": payload.get("status"),
                "selection": payload.get("selection"),
                "nextAction": payload.get("nextAction"),
            }

        declared_context = continuity(inert_declared)
        silent_context = continuity(inert_silent)
        if declared_context is None or silent_context is None:
            report(f"{label}: keel context produced no JSON.")
            return 1
        if declared_context != silent_context:
            report(
                f"{label}: the declaration changed continuity selection: "
                f"{declared_context} != {silent_context}"
            )
            return 1

    report("continuation-authorization scenario passed.")
    return 0


def validate_fast_check_config_scaffold_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-fastcfg-") as raw_tmp:
        repo = Path(raw_tmp)
        first = run_keel(repo, "--install")
        if first.returncode != 0:
            report("fast-check-config-scaffold: keel --install failed.")
            report((first.stderr or first.stdout).strip())
            return 1

        config_path = repo / "keel" / "config.yaml"
        if not config_path.is_file():
            report("fast-check-config-scaffold: install did not scaffold keel/config.yaml.")
            return 1
        scaffolded = config_path.read_text(encoding="utf-8")
        for needle in ("fast_check", "keel gate change-close", "--with-git-hooks"):
            if needle not in scaffolded:
                report(
                    "fast-check-config-scaffold: scaffolded keel/config.yaml lacks the "
                    f"fast_check guidance marker: {needle}"
                )
                return 1

        # A project's own edits to keel/config.yaml must survive re-install.
        edited = "fast_check: pytest -m 'not slow' -q\n"
        config_path.write_text(edited, encoding="utf-8")
        second = run_keel(repo, "--install")
        if second.returncode != 0:
            report("fast-check-config-scaffold: second keel --install failed.")
            report((second.stderr or second.stdout).strip())
            return 1
        if config_path.read_text(encoding="utf-8") != edited:
            report(
                "fast-check-config-scaffold: re-install overwrote an existing "
                "keel/config.yaml."
            )
            return 1

    report("fast-check-config-scaffold scenario passed.")
    return 0


def validate_fast_pre_push_hooks_scenario() -> int:
    def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True
        )

    def init_repo(root: Path, name: str) -> Path:
        repo = root / name
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "t@example.com")
        git(repo, "config", "user.name", "keel-test")
        return repo

    def declare_fast_check(repo: Path, command: str) -> None:
        (repo / "keel").mkdir(exist_ok=True)
        (repo / "keel" / "config.yaml").write_text(
            f"fast_check: {command}\n", encoding="utf-8"
        )

    def hooks_path(repo: Path) -> str | None:
        got = git(repo, "config", "--local", "--get", "core.hooksPath")
        return got.stdout.strip() if got.returncode == 0 else None

    with tempfile.TemporaryDirectory(prefix="keel-prepush-") as raw_tmp:
        root = Path(raw_tmp)

        # 1. A declared fast_check generates the hook and sets hooksPath.
        declared = init_repo(root, "declared")
        declare_fast_check(declared, "echo fast-check-ran")
        res = run_keel(declared, "--install", "--with-git-hooks")
        if res.returncode != 0:
            report("fast-pre-push-hooks: --with-git-hooks failed with a declared fast_check.")
            report((res.stderr or res.stdout).strip())
            return 1
        hook = declared / ".githooks" / "pre-push"
        if not hook.is_file():
            report("fast-pre-push-hooks: --with-git-hooks did not write .githooks/pre-push.")
            return 1
        hook_text = hook.read_text(encoding="utf-8")
        if not hook_text.startswith("#!/bin/sh") or "echo fast-check-ran" not in hook_text:
            report("fast-pre-push-hooks: pre-push does not run the declared fast_check under sh.")
            report(hook_text)
            return 1
        if hooks_path(declared) != ".githooks":
            report("fast-pre-push-hooks: --with-git-hooks did not set core.hooksPath to .githooks.")
            return 1

        # 2. A plain install touches neither the hook nor git config.
        plain = init_repo(root, "plain")
        declare_fast_check(plain, "echo plain")
        if run_keel(plain, "--install").returncode != 0:
            report("fast-pre-push-hooks: plain install failed.")
            return 1
        if (plain / ".githooks" / "pre-push").exists():
            report("fast-pre-push-hooks: plain install wrote a pre-push hook.")
            return 1
        if hooks_path(plain) is not None:
            report("fast-pre-push-hooks: plain install set core.hooksPath.")
            return 1

        # 3. Without a declared fast_check the flag refuses and writes nothing.
        undeclared = init_repo(root, "undeclared")
        res = run_keel(undeclared, "--install", "--with-git-hooks")
        if res.returncode == 0:
            report("fast-pre-push-hooks: --with-git-hooks did not refuse without a fast_check.")
            return 1
        if (undeclared / ".githooks" / "pre-push").exists():
            report("fast-pre-push-hooks: a refusal still wrote a pre-push hook.")
            return 1
        if hooks_path(undeclared) is not None:
            report("fast-pre-push-hooks: a refusal still set core.hooksPath.")
            return 1

        # 4a. Uninstall reverts a keel-set core.hooksPath.
        if run_keel(declared, "--uninstall").returncode != 0:
            report("fast-pre-push-hooks: uninstall failed.")
            return 1
        if hooks_path(declared) is not None:
            report("fast-pre-push-hooks: uninstall did not unset a keel-set core.hooksPath.")
            return 1

        # 4b. Uninstall leaves a non-.githooks core.hooksPath untouched.
        custom = init_repo(root, "custom")
        git(custom, "config", "--local", "core.hooksPath", ".customhooks")
        if run_keel(custom, "--uninstall").returncode != 0:
            report("fast-pre-push-hooks: uninstall failed on a custom hooksPath repo.")
            return 1
        if hooks_path(custom) != ".customhooks":
            report("fast-pre-push-hooks: uninstall clobbered a non-keel core.hooksPath.")
            return 1

    report("fast-pre-push-hooks scenario passed.")
    return 0


def validate_fast_pre_push_doctor_scenario() -> int:
    def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True
        )

    def init_repo(root: Path, name: str) -> Path:
        repo = root / name
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "t@example.com")
        git(repo, "config", "user.name", "keel-test")
        return repo

    with tempfile.TemporaryDirectory(prefix="keel-prepush-doc-") as raw_tmp:
        root = Path(raw_tmp)

        # Surface active: fast_check declared and --with-git-hooks applied.
        active = init_repo(root, "active")
        (active / "keel").mkdir()
        (active / "keel" / "config.yaml").write_text(
            "fast_check: echo doc-check\n", encoding="utf-8"
        )
        if run_keel(active, "--install", "--with-git-hooks").returncode != 0:
            report("fast-pre-push-doctor: install --with-git-hooks failed.")
            return 1
        before = git(active, "config", "--local", "--get", "core.hooksPath").stdout.strip()
        out = run_keel(active, "--doctor").stdout
        for needle in (
            "Fast pre-push surface:",
            "fast_check: ok",
            "echo doc-check",
            "pre-push hook: ok",
            "core.hooksPath: ok",
        ):
            if needle not in out:
                report(f"fast-pre-push-doctor: active-surface doctor output lacks: {needle}")
                report(out)
                return 1
        after = git(active, "config", "--local", "--get", "core.hooksPath").stdout.strip()
        if before != after:
            report("fast-pre-push-doctor: doctor mutated core.hooksPath.")
            return 1

        # Surface absent: plain install, no fast_check, no hook.
        absent = init_repo(root, "absent")
        if run_keel(absent, "--install").returncode != 0:
            report("fast-pre-push-doctor: plain install failed.")
            return 1
        out = run_keel(absent, "--doctor").stdout
        for needle in ("fast_check: none", "pre-push hook: none", "core.hooksPath: unset"):
            if needle not in out:
                report(f"fast-pre-push-doctor: absent-surface doctor output lacks: {needle}")
                report(out)
                return 1

    report("fast-pre-push-doctor scenario passed.")
    return 0


def run_pretooluse_guard_hook(
    repo: Path, event: dict
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["CLAUDE_PLUGIN_ROOT"] = str(ROOT / PLUGIN_ROOT)
    return subprocess.run(
        ["node", str(ROOT / PLUGIN_ROOT / "scripts/pretooluse-guard.js")],
        cwd=repo,
        env=env,
        input=json.dumps(event),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def pretooluse_decision(result: subprocess.CompletedProcess[str]) -> dict | None:
    if result.returncode != 0:
        return {"error": (result.stderr or result.stdout).strip()}
    if not result.stdout.strip():
        return None
    payload = json.loads(result.stdout)
    output = payload.get("hookSpecificOutput", {})
    if output.get("hookEventName") != "PreToolUse":
        return {"error": f"unexpected hook output: {result.stdout.strip()}"}
    return output


def edit_event(repo: Path, target: Path, tool: str = "Edit") -> dict:
    field = "notebook_path" if tool == "NotebookEdit" else "file_path"
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "tool_input": {field: str(target)},
        "cwd": str(repo),
    }


def expect_guard_deny(
    repo: Path, target: Path, needles: list[str], label: str, tool: str = "Edit"
) -> int:
    decision = pretooluse_decision(
        run_pretooluse_guard_hook(repo, edit_event(repo, target, tool))
    )
    if not decision or decision.get("permissionDecision") != "deny":
        report(f"{label}: expected deny for {target}, got {decision!r}")
        return 1
    reason = decision.get("permissionDecisionReason", "")
    for needle in needles:
        if needle not in reason:
            report(f"{label}: deny reason lacks {needle!r}: {reason!r}")
            return 1
    return 0


def expect_guard_allow(
    repo: Path, target: Path, label: str, tool: str = "Edit"
) -> int:
    decision = pretooluse_decision(
        run_pretooluse_guard_hook(repo, edit_event(repo, target, tool))
    )
    if decision is not None:
        report(f"{label}: expected silent allow for {target}, got {decision!r}")
        return 1
    return 0


RECORD_LAYER_SPEC = (
    "# demo-cap Specification\n\n"
    "## Purpose\n"
    "Fixture capability for the record-layer scenario.\n\n"
    "## Requirements\n"
    "### Requirement: Guarded behavior holds\n"
    "The guarded feature MUST keep its public behavior.\n\n"
    "#### Scenario: Guarded public behavior passes\n"
    "- **WHEN** the guarded feature runs\n"
    "- **THEN** it passes\n"
)


def record_layer_tasks(checked: bool = False, touch: str = "src/feature.js") -> str:
    box = "x" if checked else " "
    return (
        "# Tasks\n\n## Invalidates\n\n- None.\n\n"
        f"- [{box}] 1.1 Exercise guarded feature\n"
        "  - Covers:\n"
        "    - demo-cap / Guarded behavior holds / Guarded public behavior passes\n"
        "  - Touch:\n"
        f"    - {touch}\n"
        "  - Verify:\n"
        "    - Strategy: evidence-first\n"
        "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "    - M1: node test.js\n"
        "  - Evidence:\n"
        "    - M1: pending\n"
    )


def mode_fixture_tasks(mode: str, touch: str) -> str:
    return (
        "# Tasks\n\n## Invalidates\n\n- None.\n\n"
        "- [ ] 1.1 Establish the version baseline\n"
        f"  - Mode: {mode}\n"
        "  - Covers:\n"
        "    - E1: the repository carries its first commit\n"
        "  - Touch:\n"
        f"    - {touch}\n"
        "  - Verify:\n"
        "    - Strategy: evidence-first\n"
        "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "    - M1: git rev-parse HEAD resolves and git log reports one commit\n"
        "  - Evidence:\n"
        "    - Contract: pending\n"
        "    - M1: pending\n"
    )


def validate_repo_action_mode_scenario() -> int:
    """Issue #8 example 2: a repository action had no legal contract.

    A task whose whole effect is the repository's first commit writes no
    worktree file, so it has no concrete Touch; it is not diagnose-only,
    because it has real side effects needing evidence; and `Touch: none` was
    accepted for no other mode. The author was forced to name a path the task
    did not write, which then tripped the drift defect in example 1.
    """
    label = "repo-action-mode"

    def compile_task(repo: Path, mode: str, touch: str):
        write_text(repo / "openspec/changes/demo/tasks.md", mode_fixture_tasks(mode, touch))
        return run_keel(
            repo, "gate", "task-start",
            "--change", "demo", "--task", "1.1", "--no-guard", "--json",
        )

    with tempfile.TemporaryDirectory(prefix="keel-repo-action-") as raw:
        repo = Path(raw)

        started = compile_task(repo, "repo-action", "none")
        if started.returncode != 0:
            report(f"{label}: `Mode: repo-action` with `Touch: none` was rejected.")
            report((started.stderr or started.stdout).strip())
            return 1
        capsule = json.loads(started.stdout).get("contract", {}).get("capsule", {})
        prohibitions = capsule.get("prohibitions", [])
        if capsule.get("mode") != "repo-action":
            report(f"{label}: the capsule did not record the repo-action mode.")
            return 1
        if "must not write product files" not in prohibitions:
            report(
                f"{label}: repo-action must prohibit product writes; got "
                f"{prohibitions}."
            )
            return 1
        if "must not commit" in prohibitions:
            report(
                f"{label}: repo-action must be the mode that may commit; got "
                f"{prohibitions}."
            )
            return 1

        # Every other mode keeps the commit prohibition.
        for mode, touch in (
            ("implementation", "src/feature.js"),
            ("plan-first", "src/feature.js"),
            ("diagnose-only", "none"),
        ):
            other = compile_task(repo, mode, touch)
            if other.returncode != 0:
                report(f"{label}: `Mode: {mode}` regressed and no longer compiles.")
                report((other.stderr or other.stdout).strip())
                return 1
            other_capsule = (
                json.loads(other.stdout).get("contract", {}).get("capsule", {})
            )
            if "must not commit" not in other_capsule.get("prohibitions", []):
                report(f"{label}: `Mode: {mode}` lost the commit prohibition.")
                return 1
            product_write_prohibited = (
                "must not write product files"
                in other_capsule.get("prohibitions", [])
            )
            if product_write_prohibited != (mode == "diagnose-only"):
                report(
                    f"{label}: `Mode: {mode}` changed its product-write "
                    "prohibition."
                )
                return 1

        # repo-action means no worktree writes, so a concrete Touch contradicts it.
        with_touch = compile_task(repo, "repo-action", "src/feature.js")
        with_touch_problems = (
            json.loads(with_touch.stdout).get("problems", [])
            if with_touch.stdout
            else []
        )
        touch_message = " ".join(
            item.get("message", "")
            for item in with_touch_problems
            if item.get("code") == "invalid-touch"
        )
        if with_touch.returncode == 0 or "Touch: none" not in touch_message:
            report(
                f"{label}: repo-action with a concrete Touch must fail with a "
                "diagnostic naming the `Touch: none` it requires."
            )
            report((with_touch.stderr or with_touch.stdout).strip())
            return 1

        unsupported = compile_task(repo, "repo-actions", "none")
        unsupported_message = " ".join(
            item.get("message", "")
            for item in (
                json.loads(unsupported.stdout).get("problems", [])
                if unsupported.stdout
                else []
            )
            if item.get("code") == "unsupported-mode"
        )
        missing = [
            mode
            for mode in ("implementation", "diagnose-only", "plan-first", "repo-action")
            if mode not in unsupported_message
        ]
        if unsupported.returncode == 0 or missing:
            report(
                f"{label}: the unsupported-mode diagnostic must list every "
                f"supported mode; missing {missing}."
            )
            report((unsupported.stderr or unsupported.stdout).strip())
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_touch_guard_record_layer_scenario() -> int:
    """Issue #8: the guard denied what the completion gate already forgives.

    `scopeProblems` exempts the selected change's own `openspec/changes/<change>/`
    directory from outside-Touch attribution, but the guard denied writes there
    and treated the byte hash of that change's tasks.md as authority, so ticking
    a checkbox or appending Evidence locked the task out of its own bookkeeping.
    """
    label = "touch-guard-record-layer"
    with tempfile.TemporaryDirectory(prefix="keel-record-layer-") as raw:
        repo = Path(raw)
        tasks = repo / "openspec/changes/demo/tasks.md"
        spec = repo / "openspec/specs/demo-cap/spec.md"
        write_text(tasks, record_layer_tasks())
        write_text(spec, RECORD_LAYER_SPEC)
        write_text(repo / "openspec/changes/other/tasks.md", "# Tasks\n")
        write_text(repo / "keel/archive/follow-ups/note.md", "# Note\n")

        started = run_keel(
            repo, "guard", "start", "--change", "demo", "--task", "1.1", "--json"
        )
        if started.returncode != 0:
            report(f"{label}: guard start failed on the fixture.")
            report((started.stderr or started.stdout).strip())
            return 1
        manifest = json.loads(started.stdout).get("manifest", {})
        authority = [entry.get("path") for entry in manifest.get("authority", [])]
        if not any(item == "openspec/specs/demo-cap/spec.md" for item in authority):
            report(
                f"{label}: the fixture does not record an authority file outside "
                f"the change directory, so the negative case is untested: {authority}"
            )
            return 1

        # The record layer: writable although Touch never named it.
        if expect_guard_allow(repo, tasks, f"{label} record write"):
            return 1
        # A record write already made must not lock the task out of its product
        # writes — this is the drift half of the reported defect.
        write_text(tasks, record_layer_tasks().replace("M1: pending", "M1: done"))
        if expect_guard_allow(repo, repo / "src/feature.js", f"{label} after record write"):
            return 1

        # The layer is exactly this change's directory, nothing wider.
        if expect_guard_deny(
            repo,
            repo / "openspec/changes/other/tasks.md",
            ["outside Touch"],
            f"{label} other change",
        ):
            return 1
        if expect_guard_deny(
            repo,
            repo / "keel/archive/follow-ups/note.md",
            ["outside Touch"],
            f"{label} archive tree",
        ):
            return 1

        # Authority outside the change directory still hashes and still denies.
        write_text(spec, RECORD_LAYER_SPEC.replace("it passes", "it passes twice"))
        if expect_guard_deny(
            repo,
            repo / "src/feature.js",
            ["authority drift"],
            f"{label} real authority drift",
        ):
            return 1
        write_text(spec, RECORD_LAYER_SPEC)

        status = run_keel(repo, "guard", "status", "--json")
        status_payload = json.loads(status.stdout) if status.stdout else {}
        codes = [item.get("code") for item in status_payload.get("problems", [])]
        if status_payload.get("status") != "active" or codes:
            report(
                f"{label}: guard status reported {status_payload.get('status')!r} "
                f"with problems {codes} after a record write; a checkbox or "
                "Evidence write is not authority drift."
            )
            return 1

        # A real contract edit in the same file must still hard-stop, through the
        # fingerprint rather than through byte hashing.
        write_text(tasks, record_layer_tasks(touch="src/other.js"))
        drifted = run_keel(repo, "guard", "status", "--json")
        drifted_codes = [
            item.get("code")
            for item in (json.loads(drifted.stdout) if drifted.stdout else {}).get(
                "problems", []
            )
        ]
        if "fingerprint-drift" not in drifted_codes:
            report(
                f"{label}: editing the task's Touch line did not report "
                f"fingerprint drift; got {drifted_codes}."
            )
            return 1

        # Once checked, product writes stop but the task can still finish its
        # own records — the completion gate requires that Evidence.
        write_text(tasks, record_layer_tasks(checked=True))
        if expect_guard_deny(
            repo,
            repo / "src/feature.js",
            ["checked complete"],
            f"{label} completed product write",
        ):
            return 1
        if expect_guard_allow(repo, tasks, f"{label} completed record write"):
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_push_branch_guard_scenario() -> int:
    """Issue #257: with `push:<glob>` declared, the hook refuses other pushes.

    The real hook script receives `Bash` events with no task manifest. A push
    to a declared branch passes, one to `main` is refused by name, a bare
    `git push` resolves the branch's push destination, an undetermined target
    is refused naming the explicit form, a typo elsewhere does not lift the
    check, and a bare `push` declaration intercepts nothing.
    """
    label = "push-branch-guard:"
    hooks = json.loads((ROOT / PLUGIN_ROOT / "hooks/hooks.json").read_text(encoding="utf-8"))
    matchers = [entry.get("matcher", "") for entry in hooks.get("hooks", {}).get("PreToolUse", [])]
    if not any("Bash" in matcher.split("|") for matcher in matchers):
        report(f"{label} hooks.json does not register the guard for Bash: {matchers!r}")
        return 1
    with tempfile.TemporaryDirectory(prefix="keel-push-guard-") as raw:
        base = Path(raw)
        remote = base / "remote.git"
        repo = base / "repo"

        def git(*args: str, cwd: Path = repo) -> None:
            subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)

        git("init", "-q", "--bare", str(remote), cwd=base)
        git("init", "-q", "-b", "main", str(repo), cwd=base)
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "init")
        git("remote", "add", "origin", str(remote))
        git("push", "-q", "-u", "origin", "main")
        git("switch", "-q", "-c", "claude/fix")
        git("push", "-q", "-u", "origin", "claude/fix")

        def decide(command: str) -> dict | None:
            event = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(repo)}
            return pretooluse_decision(run_pretooluse_guard_hook(repo, event))

        def denied(decision: dict | None) -> bool:
            return bool(decision) and decision.get("permissionDecision") == "deny"

        write_authorize_config(repo, "authorize:\n  - commit\n  - push:claude/*\n")
        checks = [
            ("a push to the declared branch", "git add -A && git push -u origin claude/fix", False, None),
            ("a push to main", "git push origin HEAD:main", True, "main"),
            ("a bare push on a branch pushing to claude/fix", "git push", False, None),
            ("--all", "git push --all origin", True, "git push origin <branch>"),
            ("a shell variable", 'git push origin "$BRANCH"', True, "git push origin <branch>"),
        ]
        for what, command, want_deny, needle in checks:
            decision = decide(command)
            if decision and "error" in decision:
                report(f"{label} the hook failed on {what}: {decision['error']}")
                return 1
            if denied(decision) != want_deny:
                report(f"{label} {what} ({command!r}) was {'allowed' if want_deny else 'denied'}: {decision!r}")
                return 1
            if needle and needle not in decision.get("permissionDecisionReason", ""):
                report(f"{label} {what} was denied without naming {needle!r}: {decision!r}")
                return 1
        git("switch", "-q", "main")
        decision = decide("git push")
        if not denied(decision):
            report(f"{label} a bare push on a branch pushing to origin/main was allowed: {decision!r}")
            return 1
        if "main" not in decision.get("permissionDecisionReason", ""):
            report(f"{label} the bare push to main was denied without naming main: {decision!r}")
            return 1

        write_authorize_config(repo, "authorize:\n  - push:claude/*\n  - deploy\n")
        if not denied(decide("git push origin HEAD:main")):
            report(f"{label} a typo elsewhere in authorize: lifted the push check.")
            return 1
        write_authorize_config(repo, "authorize:\n  - push\n")
        if decide("git push origin HEAD:main") is not None:
            report(f"{label} a bare push declaration intercepted a push.")
            return 1
    report("push-branch-guard scenario passed.")
    return 0


def validate_push_guard_cd_before_push_scenario() -> int:
    """Issue #486: a `cd` before a push leaves its repository unknown, whatever the refspec.

    The guard reads the push scope of the session's repository. kaiwu-layout's
    `cd <export dir> && git push <url> main:main` was judged by kaiwu-ip's
    `push-protected:main@kaiwu-chief`, though it pushed another repository.
    The refusal now names `git -C <directory> push`, which is judged by the
    repository it names.
    """
    label = "push-guard-cd-before-push:"
    with tempfile.TemporaryDirectory(prefix="keel-push-cd-486-") as raw:
        base = Path(raw)
        repo = base / "repo"
        other = base / "export"

        def git(*args: str, cwd: Path) -> None:
            subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)

        for tree in (repo, other):
            git("init", "-q", "-b", "main", str(tree), cwd=base)
            git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "init", cwd=tree)
        (repo / "sub").mkdir()
        write_authorize_config(repo, "authorize:\n  - push:claude/*\n  - push-protected:main@chief\n")

        def decide(command: str) -> dict | None:
            event = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(repo)}
            return pretooluse_decision(run_pretooluse_guard_hook(repo, event))

        url = "https://example.invalid/acme/export.git"
        for what, command in (
            ("a push in another repository after cd", f"cd {other} && git push {url} main:main"),
            ("a push to a declared branch after cd", "cd sub && git push origin claude/fix"),
        ):
            decision = decide(command)
            if not decision or decision.get("permissionDecision") != "deny":
                report(f"{label} {what} ({command!r}) was not denied: {decision!r}")
                return 1
            reason = decision.get("permissionDecisionReason", "")
            if "git -C <directory> push" not in reason:
                report(f"{label} {what} was denied without naming `git -C <directory> push`: {reason!r}")
                return 1
            if "chief" in reason:
                report(f"{label} {what} was judged by the session repository's protected branch: {reason!r}")
                return 1
        decision = decide(f"git -C {other} push {url} main:main")
        if decision is not None:
            report(f"{label} `git -C` into a repository that declares nothing got a decision: {decision!r}")
            return 1
    if label.rstrip(":") not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report(f"{label.rstrip(':')} scenario passed.")
    return 0


def validate_authorize_role_scoped_scenario() -> int:
    """Issue #378: a scoped grant may name the roles it applies to.

    kaiwu-ip split its standing authorization by capability, one session per
    capability, and could only write the split as comments: every scoped grant
    but `push-protected` applied to every session. `@<role pattern>` limits an
    entry to matching roles; the push guard stays on for a role no entry names.
    """
    label = "authorize-role-scoped:"
    with tempfile.TemporaryDirectory(prefix="keel-authorize-378-") as raw:
        base = Path(raw)
        repo = mailbox_repository(base / "repo")
        rtl = chat_worktree(repo, base / "rtl")
        verify = chat_worktree(repo, base / "verify")
        env = chat_environment()
        run_keel(rtl, "chat", "role", "--set", "rtl", env=env)
        run_keel(verify, "chat", "role", "--set", "verify", env=env)
        entries = ["commit", "push:design-*@rtl", "push:review-*@ver*", "issue:acme/widgets@rtl",
                   "chat-reply:soc@verify", "push-protected:main@rt*"]
        for cwd in (rtl, verify):
            write_authorize_config(cwd, "authorize:\n" + "".join(f"  - {e}\n" for e in entries))

        def line(stdout: str, name: str) -> str:
            return next((l for l in stdout.splitlines() if l.strip().startswith(f"{name}:")), "")

        for cwd, role, granted, withheld in ((rtl, "rtl", "issue", "chat-reply"), (verify, "verify", "chat-reply", "issue")):
            doctor = run_keel(cwd, "--doctor", env=env)
            if not line(doctor.stdout, granted):
                report(f"{label} {role}'s doctor has no {granted} line: {doctor.stdout}")
                return 1
            if "not authorized" in line(doctor.stdout, granted):
                report(f"{label} {role}'s doctor does not report {granted} authorized: {doctor.stdout}")
                return 1
            if "not authorized" not in line(doctor.stdout, withheld):
                report(f"{label} {role}'s doctor reports {withheld}, another role's grant: {line(doctor.stdout, withheld)!r}")
                return 1
            roles = [l for l in doctor.stdout.splitlines() if l.startswith("roles:")]
            if not any("rtl" in l and "issue:acme/widgets@rtl" in l for l in roles):
                report(f"{label} {role}'s doctor lists no roles line for rtl's grants: {roles!r}")
                return 1
            if not any("verify" in l and "chat-reply:soc@verify" in l for l in roles):
                report(f"{label} {role}'s doctor lists no roles line for verify's grants: {roles!r}")
                return 1

        hook_env = {k: v for k, v in os.environ.items() if k not in ("KEEL_CHAT_ROLE", "KEEL_MAIL_ROLE")}
        hook_env["CLAUDE_PLUGIN_ROOT"] = str(ROOT / PLUGIN_ROOT)

        def decide(cwd: Path, command: str, role: str | None = None) -> dict:
            event = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd), "permission_mode": "default"}
            run_env = {**hook_env, **({"KEEL_CHAT_ROLE": role} if role else {})}
            result = subprocess.run(
                ["node", str(ROOT / PLUGIN_ROOT / "scripts/pretooluse-guard.js")],
                cwd=cwd, env=run_env, input=json.dumps(event), text=True, capture_output=True, check=False,
            )
            return pretooluse_decision(result) or {"permissionDecision": "pass"}

        if decide(rtl, "git push origin design-x").get("permissionDecision") != "pass":
            report(f"{label} rtl's own design branch was not allowed: {decide(rtl, 'git push origin design-x')!r}")
            return 1
        other = decide(verify, "git push origin design-x")
        if other.get("permissionDecision") != "deny":
            report(f"{label} verify pushing rtl's design branch was {other!r}, not deny.")
            return 1
        if "rtl" not in other.get("permissionDecisionReason", ""):
            report(f"{label} the refusal does not name the role that may push it: {other!r}")
            return 1
        if decide(verify, "git push origin review-x").get("permissionDecision") != "pass":
            report(f"{label} verify's review branch, granted by the ver* pattern, was not allowed.")
            return 1
        unnamed = decide(verify, "git push origin design-x", role="spec")
        if unnamed.get("permissionDecision") != "deny":
            report(f"{label} a role no entry names was left unlimited: {unnamed!r}")
            return 1
        if decide(rtl, "git push origin HEAD:main").get("permissionDecision") != "ask":
            report(f"{label} rtl, matching main@rt*, was not asked about main.")
            return 1
        if decide(verify, "git push origin HEAD:main").get("permissionDecision") != "deny":
            report(f"{label} verify's push to main@rt* was not refused.")
            return 1

        write_authorize_config(rtl, "authorize:\n  - issue:acme/widgets@Not A Role\n")
        bad = run_keel(rtl, "--doctor", env=env)
        if bad.returncode == 0:
            report(f"{label} a malformed role pattern was accepted: {bad.stdout}")
            return 1
        if "issue:acme/widgets@Not A Role" not in bad.stdout:
            report(f"{label} the refusal does not name the entry: {bad.stdout}")
            return 1
    if "authorize-role-scoped" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("authorize-role-scoped scenario passed.")
    return 0


def validate_push_protected_guard_scenario() -> int:
    """Issue #280: a protected push is asked, never stored, and role-limited.

    The real hook returns `ask` for the bound role in a mode that can ask,
    denies another role and a mode that cannot ask, and leaves `push:` and
    unlisted branches as they were.
    """
    label = "push-protected-guard:"
    with tempfile.TemporaryDirectory(prefix="keel-push-protected-guard-") as raw:
        base = Path(raw)
        repo = mailbox_repository(base / "repo")
        pm = chat_worktree(repo, base / "pm")
        rtl = chat_worktree(repo, base / "rtl")
        env = chat_environment()
        run_keel(pm, "chat", "role", "--set", "iecc-pm", env=env)
        run_keel(rtl, "chat", "role", "--set", "rtl", env=env)
        hook_env = {k: v for k, v in os.environ.items() if k not in ("KEEL_CHAT_ROLE", "KEEL_MAIL_ROLE")}
        hook_env["CLAUDE_PLUGIN_ROOT"] = str(ROOT / PLUGIN_ROOT)

        def declare(entries: list[str]) -> None:
            for cwd in (pm, rtl):
                write_authorize_config(cwd, "authorize:\n" + "".join(f"  - {e}\n" for e in entries))

        def decide(cwd: Path, command: str, mode: str = "default") -> dict:
            event = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd), "permission_mode": mode}
            result = subprocess.run(
                ["node", str(ROOT / PLUGIN_ROOT / "scripts/pretooluse-guard.js")],
                cwd=cwd, env=hook_env, input=json.dumps(event), text=True, capture_output=True, check=False,
            )
            return pretooluse_decision(result) or {"permissionDecision": "pass"}

        declare(["push:claude/*", "push-protected:main@iecc-pm"])
        store_before = chat_logs_snapshot(repo)
        for attempt in (1, 2):
            asked = decide(pm, "git push origin HEAD:main")
            if asked.get("permissionDecision") != "ask":
                report(f"{label} the coordinator's push to main (attempt {attempt}) was {asked!r}, not ask.")
                return 1
            if "main" not in asked.get("permissionDecisionReason", ""):
                report(f"{label} the ask does not name main: {asked!r}")
                return 1
        if chat_logs_snapshot(repo) != store_before:
            report(f"{label} asking wrote to the chat store.")
            return 1
        other = decide(rtl, "git push origin HEAD:main")
        if other.get("permissionDecision") != "deny":
            report(f"{label} another role's push to main was {other!r}, not deny.")
            return 1
        if "iecc-pm" not in other.get("permissionDecisionReason", ""):
            report(f"{label} the refusal does not name iecc-pm: {other!r}")
            return 1
        for mode in ("bypassPermissions", "dontAsk"):
            refused = decide(pm, "git push origin HEAD:main", mode)
            if refused.get("permissionDecision") != "deny":
                report(f"{label} the protected push in {mode} was {refused!r}, not deny.")
                return 1
            if mode not in refused.get("permissionDecisionReason", ""):
                report(f"{label} the {mode} refusal does not name the mode: {refused!r}")
                return 1
        if decide(rtl, "git push origin claude/fix").get("permissionDecision") != "pass":
            report(f"{label} a declared push: branch was intercepted.")
            return 1
        if decide(rtl, "git push origin release").get("permissionDecision") != "deny":
            report(f"{label} an unlisted branch was not denied.")
            return 1

        declare(["push-protected:main"])
        if decide(rtl, "git push origin release").get("permissionDecision") != "deny":
            report(f"{label} with only push-protected declared, an unlisted branch was not denied.")
            return 1
        if decide(rtl, "git push origin HEAD:main").get("permissionDecision") != "ask":
            report(f"{label} with no role limit, a push to main was not asked.")
            return 1
    report("push-protected-guard scenario passed.")
    return 0


def validate_push_guard_redirects_scenario() -> int:
    """Issue #286: a shell redirection is never read as a push target."""
    label = "push-guard-redirects:"
    with tempfile.TemporaryDirectory(prefix="keel-push-redirects-") as raw:
        repo = mailbox_repository(Path(raw) / "repo")
        write_authorize_config(repo, "authorize:\n  - push:flow-*\n")

        def decide(command: str) -> dict:
            event = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(repo)}
            return pretooluse_decision(run_pretooluse_guard_hook(repo, event)) or {"permissionDecision": "pass"}

        base = "git push --dry-run origin HEAD:refs/heads/flow-probe"
        for command in (f"{base} 2>&1 | tail -1", f"{base} 2>/dev/null", f"{base} &> out.log", f"{base} >&2"):
            decision = decide(command)
            if decision.get("permissionDecision") != "pass":
                report(f"{label} {command!r} was {decision!r}, not allowed.")
                return 1
        refused = decide("git push origin HEAD:main 2>&1 | tail -1")
        if refused.get("permissionDecision") != "deny":
            report(f"{label} an out-of-scope push with a redirection was {refused!r}, not denied.")
            return 1
        if "`main`" not in refused.get("permissionDecisionReason", ""):
            report(f"{label} the refusal does not name main: {refused!r}")
            return 1
    report("push-guard-redirects scenario passed.")
    return 0


def validate_push_guard_follow_tags_scenario() -> int:
    """Issue #327: a push that carries annotated tags is a tag push.

    The real hook denies `--follow-tags`, `push.followTags` from the repository
    config or `git -c`, and a `GIT_CONFIG*` assignment on a `push:` branch;
    turning tag carriage off restores the branch push; a protected branch is
    asked about with its tags; and nothing is checked without a push scope.
    """
    label = "push-guard-follow-tags:"
    with tempfile.TemporaryDirectory(prefix="keel-push-follow-tags-") as raw:
        base = Path(raw)
        repo = mailbox_repository(base / "repo")
        pm = chat_worktree(repo, base / "pm")
        rtl = chat_worktree(repo, base / "rtl")
        env = chat_environment()
        run_keel(pm, "chat", "role", "--set", "iecc-pm", env=env)
        run_keel(rtl, "chat", "role", "--set", "rtl", env=env)
        hook_env = {
            k: v for k, v in os.environ.items()
            if k not in ("KEEL_CHAT_ROLE", "KEEL_MAIL_ROLE") and not k.startswith("GIT_CONFIG")
        }
        hook_env["CLAUDE_PLUGIN_ROOT"] = str(ROOT / PLUGIN_ROOT)

        def declare(entries: list[str]) -> None:
            for cwd in (pm, rtl):
                write_authorize_config(cwd, "authorize:\n" + "".join(f"  - {e}\n" for e in entries))

        def decide(cwd: Path, command: str) -> dict:
            event = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd), "permission_mode": "default"}
            result = subprocess.run(
                ["node", str(ROOT / PLUGIN_ROOT / "scripts/pretooluse-guard.js")],
                cwd=cwd, env=hook_env, input=json.dumps(event), text=True, capture_output=True, check=False,
            )
            return pretooluse_decision(result) or {"permissionDecision": "pass"}

        def expect(what: str, cwd: Path, command: str, want: str, needles: tuple[str, ...] = ()) -> bool:
            decision = decide(cwd, command)
            if decision.get("permissionDecision") != want:
                verdict = "allowed" if decision.get("permissionDecision") == "pass" else decision.get("permissionDecision")
                report(f"{label} {what} was {verdict}, not {want} ({command!r}): {decision!r}")
                return False
            reason = decision.get("permissionDecisionReason", "")
            for needle in needles:
                if needle not in reason:
                    report(f"{label} {what} does not name {needle!r}: {reason!r}")
                    return False
            return True

        def set_follow_tags(value: str | None) -> None:
            args = ["config", "push.followTags", value] if value else ["config", "--unset", "push.followTags"]
            subprocess.run(["git", *args], cwd=rtl, check=False, capture_output=True)

        declare(["push:flow-*"])
        branch = "origin flow-release"
        if not expect("--follow-tags push to a granted branch", rtl, f"git push --follow-tags {branch}", "deny",
                      ("--follow-tags", "--no-follow-tags")):
            report(f"{label} --follow-tags push to a granted branch was allowed")
            return 1
        if not expect("--follow-tags undone by --no-follow-tags", rtl,
                      f"git push --follow-tags --no-follow-tags {branch}", "pass"):
            return 1
        if not expect("a plain push to a granted branch", rtl, f"git push {branch}", "pass"):
            return 1
        if not expect("git -c push.followTags=true", rtl, f"git -c push.followTags=true push {branch}", "deny",
                      ("push.followTags",)):
            return 1
        set_follow_tags("true")
        if not expect("a plain push under push.followTags=true", rtl, f"git push {branch}", "deny", ("push.followTags",)):
            return 1
        if not expect("git -c push.followTags=false over the config", rtl,
                      f"git -c push.followTags=false push {branch}", "pass"):
            return 1
        set_follow_tags(None)
        if not expect("a GIT_CONFIG_COUNT assignment", rtl,
                      f"GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=push.followTags GIT_CONFIG_VALUE_0=true git push {branch}",
                      "deny", ("GIT_CONFIG_COUNT",)):
            return 1

        if not expect("a GIT_CONFIG_COUNT assignment behind env", rtl,
                      f"env GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=push.followTags GIT_CONFIG_VALUE_0=true git push {branch}",
                      "deny", ("GIT_CONFIG_COUNT",)):
            return 1
        if not expect("a shell-expanded git -c", rtl, f'git -c "$CFG" push {branch}', "deny", ("expanded",)):
            return 1
        if not expect("a push to main behind `env FOO=1`", rtl, "env FOO=1 git push origin main", "deny", ("`main`",)):
            return 1

        declare(["push:flow-*", "push-protected:main@iecc-pm"])
        if not expect("the coordinator's --follow-tags push to main", pm, "git push --follow-tags origin main", "ask",
                      ("`main`", "annotated tags")):
            return 1
        if not expect("another role's --follow-tags push to main", rtl, "git push --follow-tags origin main", "deny",
                      ("iecc-pm",)):
            return 1
        if not expect("a --follow-tags push to a granted branch beside a protected one", pm,
                      f"git push --follow-tags {branch}", "deny", ("--no-follow-tags",)):
            return 1

        declare(["commit"])
        if not expect("a --follow-tags push with no push scope", rtl, f"git push --follow-tags {branch}", "pass"):
            return 1
    report("push-guard-follow-tags scenario passed.")
    return 0


def validate_touch_write_guard_scenario() -> int:
    with tempfile.TemporaryDirectory(
        prefix="keel-touch-guard-", ignore_cleanup_errors=True
    ) as raw_tmp:
        tmp = Path(raw_tmp)
        repo = tmp / "repo"
        repo.mkdir()
        write_text(repo / "openspec/changes/demo/tasks.md", guard_task_fixture())
        write_text(repo / "src/feature.js", "// fixture\n")
        write_text(repo / "README.md", "fixture\n")

        gate = run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
        )
        gate_payload = json.loads(gate.stdout)
        gate_fingerprint = gate_payload["contract"]["fingerprint"]["value"]

        manifest_path = repo / "keel/guard.json"
        if not manifest_path.is_file():
            report(
                "touch-write-guard: passing task-start did not write the guard "
                "manifest by default."
            )
            return 1
        default_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if default_manifest.get("fingerprint", {}).get("value") != gate_fingerprint:
            report(
                "touch-write-guard: default manifest fingerprint diverges from "
                "task-start."
            )
            return 1
        if gate_payload.get("guard", {}).get("status") != "started":
            report(
                "touch-write-guard: task-start result does not report the "
                "default guard start."
            )
            return 1

        optout_clear = run_keel(repo, "guard", "clear", "--json")
        if optout_clear.returncode != 0 or manifest_path.exists():
            report("touch-write-guard: could not clear the default manifest.")
            return 1
        optout = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--no-guard",
            "--json",
        )
        if optout.returncode != 0 or manifest_path.exists():
            report("touch-write-guard: --no-guard task-start wrote a manifest.")
            return 1
        codex_gate = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--target",
            "codex",
            "--json",
        )
        if codex_gate.returncode != 0 or manifest_path.exists():
            report("touch-write-guard: codex-target task-start wrote a manifest.")
            return 1

        started = run_keel(
            repo, "guard", "start", "--change", "demo", "--task", "1.1", "--json"
        )
        if started.returncode != 0:
            report("touch-write-guard: guard start did not exit 0.")
            report((started.stderr or started.stdout).strip())
            return 1
        payload = json.loads(started.stdout)
        if payload.get("status") != "started":
            report(f"touch-write-guard: guard start status {payload.get('status')!r}.")
            return 1
        manifest_path = repo / "keel/guard.json"
        if not manifest_path.is_file():
            report("touch-write-guard: guard start did not write keel/guard.json.")
            return 1
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schema") != "keel-write-guard/v1":
            report("touch-write-guard: manifest schema is wrong.")
            return 1
        if manifest.get("fingerprint", {}).get("value") != gate_fingerprint:
            report("touch-write-guard: manifest fingerprint diverges from task-start.")
            return 1

        before = snapshot_files(repo)
        if expect_guard_deny(
            repo,
            repo / "README.md",
            ["README.md", "demo", "1.1", "keel guard clear"],
            "touch-write-guard deny",
        ):
            return 1
        if snapshot_files(repo) != before:
            report("touch-write-guard: hook wrote repository state.")
            return 1
        if expect_guard_allow(
            repo, repo / "src/feature.js", "touch-write-guard in-touch", "Write"
        ):
            return 1
        if expect_guard_allow(
            repo, repo / "docs/new/page.md", "touch-write-guard glob"
        ):
            return 1
        if expect_guard_allow(
            repo, repo / "README.md", "touch-write-guard non-edit tool", "Bash"
        ):
            return 1
        if expect_guard_allow(
            repo, tmp / "outside.txt", "touch-write-guard external path"
        ):
            return 1

        status = run_keel(repo, "guard", "status", "--json")
        if status.returncode != 0 or json.loads(status.stdout).get("status") != "active":
            report("touch-write-guard: guard status is not active.")
            report((status.stderr or status.stdout).strip())
            return 1

        cleared = run_keel(repo, "guard", "clear", "--json")
        if cleared.returncode != 0 or manifest_path.exists():
            report("touch-write-guard: guard clear did not remove the manifest.")
            return 1
        if expect_guard_allow(
            repo, repo / "README.md", "touch-write-guard absent manifest"
        ):
            return 1
        recleared = run_keel(repo, "guard", "clear", "--json")
        if (
            recleared.returncode != 0
            or json.loads(recleared.stdout).get("status") != "absent"
        ):
            report("touch-write-guard: repeated clear is not a safe absent no-op.")
            return 1

        switch_repo = tmp / "switch"
        switch_repo.mkdir()
        switch_tasks = switch_repo / "openspec/changes/demo/tasks.md"
        second_task = (
            "\n- [ ] 1.2 Exercise second guarded feature\n"
            "  - Covers:\n"
            "    - E2: Second guarded behavior passes.\n"
            "  - Touch:\n"
            "    - src/other.js\n"
            "  - Verify:\n"
            "    - Strategy: evidence-first\n"
            "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
            "    - M1: node test.js\n"
            "  - Evidence:\n"
            "    - M1: pending\n"
        )
        write_text(switch_tasks, guard_task_fixture() + second_task)
        write_text(switch_repo / "src/feature.js", "// fixture\n")
        first_switch = run_keel(
            switch_repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
        )
        second_switch = run_keel(
            switch_repo, "gate", "task-start", "--change", "demo", "--task", "1.2", "--json"
        )
        switch_manifest_path = switch_repo / "keel/guard.json"
        if (
            first_switch.returncode != 0
            or second_switch.returncode != 0
            or not switch_manifest_path.is_file()
            or json.loads(switch_manifest_path.read_text(encoding="utf-8")).get("task")
            != "1.2"
        ):
            report("touch-write-guard: task switch did not replace the manifest.")
            return 1
        manifest_before_fail = switch_manifest_path.read_bytes()
        write_text(
            switch_tasks,
            switch_tasks.read_text(encoding="utf-8").replace(
                "src/other.js", "<path>"
            ),
        )
        failing_switch = run_keel(
            switch_repo, "gate", "task-start", "--change", "demo", "--task", "1.2", "--json"
        )
        if (
            failing_switch.returncode != 3
            or switch_manifest_path.read_bytes() != manifest_before_fail
        ):
            report(
                "touch-write-guard: failing task-start replaced or cleared the "
                "existing manifest."
            )
            return 1

        checked_repo = tmp / "checked"
        checked_repo.mkdir()
        write_text(
            checked_repo / "openspec/changes/demo/tasks.md",
            guard_task_fixture(checked=True),
        )
        refused = run_keel(
            checked_repo, "guard", "start", "--change", "demo", "--task", "1.1", "--json"
        )
        if refused.returncode != 3 or json.loads(refused.stdout).get("status") != "refused":
            report("touch-write-guard: completed task did not refuse guard start.")
            return 1

        broken_repo = tmp / "broken"
        broken_repo.mkdir()
        write_text(
            broken_repo / "openspec/changes/demo/tasks.md",
            guard_task_fixture()
            .replace("src/feature.js", "<path>")
            .replace("docs/**", "<more>"),
        )
        broken = run_keel(
            broken_repo, "guard", "start", "--change", "demo", "--task", "1.1", "--json"
        )
        if broken.returncode != 3:
            report("touch-write-guard: failing task-start compile did not refuse.")
            return 1
        broken_gate = run_keel(
            broken_repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
        )
        if broken_gate.returncode != 3 or (broken_repo / "keel/guard.json").exists():
            report("touch-write-guard: failing task-start wrote a guard manifest.")
            return 1

    report("touch-write-guard scenario passed.")
    return 0


def validate_touch_guard_surface_scenario() -> int:
    with tempfile.TemporaryDirectory(
        prefix="keel-guard-surface-", ignore_cleanup_errors=True
    ) as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()
        write_text(repo / "openspec/changes/demo/tasks.md", guard_task_fixture())
        write_text(repo / "src/feature.js", "// fixture\n")

        probe = run_keel(repo, "capabilities", "--target", "claude", "--json")
        if probe.returncode != 0:
            report("touch-guard-surface: claude capabilities probe failed.")
            return 1
        guard = json.loads(probe.stdout).get("guard", {})
        if guard.get("enforcement", {}).get("level") != "advisory":
            report(
                "touch-guard-surface: shipped claude guard enforcement must stay "
                f"advisory, got {guard.get('enforcement')!r}."
            )
            return 1
        boundary = guard.get("boundary", {}).get("evidence", "")
        if "file-edit" not in boundary or "Bash" not in boundary:
            report(
                "touch-guard-surface: guard boundary must document the "
                f"file-edit-tools-only limit and Bash: {boundary!r}."
            )
            return 1
        if "absent" not in guard.get("manifest", {}).get("evidence", ""):
            report("touch-guard-surface: manifest observation should report absent.")
            return 1

        started = run_keel(
            repo, "guard", "start", "--change", "demo", "--task", "1.1", "--json"
        )
        if started.returncode != 0:
            report("touch-guard-surface: guard start failed.")
            return 1
        active = run_keel(repo, "capabilities", "--target", "claude", "--json")
        active_guard = json.loads(active.stdout).get("guard", {})
        if "active" not in active_guard.get("manifest", {}).get("evidence", ""):
            report("touch-guard-surface: manifest observation should report active.")
            return 1

        rendered = run_keel(repo, "capabilities", "--target", "claude")
        if "guard enforcement: advisory - " not in rendered.stdout:
            report("touch-guard-surface: rendered capabilities lack guard lines.")
            return 1

        for target in ("codex", "opencode"):
            other = run_keel(repo, "capabilities", "--target", target, "--json")
            other_guard = json.loads(other.stdout).get("guard", {})
            if other_guard.get("enforcement", {}).get("level") != "manual":
                report(
                    f"touch-guard-surface: {target} guard enforcement must be "
                    f"manual, got {other_guard.get('enforcement')!r}."
                )
                return 1

        for name in ("README.md", "README.zh-CN.md"):
            readme = (ROOT / name).read_text(encoding="utf-8")
            for needle in ("keel guard start", "keel guard clear", "guard.json", "Bash"):
                if needle not in readme:
                    report(f"touch-guard-surface: {name} lacks guard guidance: {needle}.")
                    return 1
        bootstrap = (ROOT / "assets/bootstrap/AGENTS.md").read_text(encoding="utf-8")
        # The bootstrap must tell a consumer the guard exists and how to opt out;
        # it no longer spends bytes naming `keel guard clear`, which `keel --help`
        # and `keel guard status` carry. `--no-guard` is the flag it does name, so
        # that one stays literal and a rename of it still fails here.
        if "--no-guard" not in bootstrap or "guards it by default" not in bootstrap:
            report("touch-guard-surface: bootstrap does not mention the guard.")
            return 1
        registered = {name for name, _ in registry.SCENARIOS}
        for scenario in ("touch-write-guard", "touch-guard-drift", "touch-guard-surface"):
            if scenario not in registered:
                report(
                    f"touch-guard-surface: the scenario registry lacks {scenario}."
                )
                return 1

    report("touch-guard-surface scenario passed.")
    return 0


def validate_touch_guard_drift_scenario() -> int:
    with tempfile.TemporaryDirectory(
        prefix="keel-guard-drift-", ignore_cleanup_errors=True
    ) as raw_tmp:
        tmp = Path(raw_tmp)
        repo = tmp / "repo"
        repo.mkdir()
        tasks_path = repo / "openspec/changes/demo/tasks.md"
        write_text(tasks_path, guard_task_fixture())
        write_text(repo / "src/feature.js", "// fixture\n")

        started = run_keel(
            repo, "guard", "start", "--change", "demo", "--task", "1.1", "--json"
        )
        if started.returncode != 0:
            report("touch-guard-drift: initial guard start failed.")
            report((started.stderr or started.stdout).strip())
            return 1
        first = json.loads(started.stdout)["manifest"]["fingerprint"]["value"]

        write_text(
            tasks_path,
            tasks_path.read_text(encoding="utf-8").replace(
                "Exercise guarded feature", "Exercise guarded feature differently"
            ),
        )
        # A contract edit inside the guarded change's own directory is caught
        # where the capsule is compiled, not at the next write: the hook cannot
        # compile, so it cannot separate this from a checkbox or Evidence write
        # in the same file. It therefore allows the write and `guard status`
        # reports the drift. Authority *outside* that directory still denies at
        # write time — see the touch-guard-record-layer scenario.
        if expect_guard_allow(
            repo, repo / "src/feature.js", "touch-guard-drift contract edit"
        ):
            return 1
        status = run_keel(repo, "guard", "status", "--json")
        status_payload = json.loads(status.stdout) if status.stdout else {}
        if status.returncode != 3 or status_payload.get("status") != "drifted":
            report("touch-guard-drift: status did not report drifted.")
            report((status.stderr or status.stdout).strip())
            return 1
        if not any(
            item.get("code") == "fingerprint-drift"
            for item in status_payload.get("problems", [])
        ):
            report(
                "touch-guard-drift: the contract edit was not reported as "
                "fingerprint drift by the check that compiles the capsule."
            )
            report(status.stdout or "")
            return 1

        restarted = run_keel(
            repo, "guard", "start", "--change", "demo", "--task", "1.1", "--json"
        )
        if restarted.returncode != 0:
            report("touch-guard-drift: reauthorizing guard start failed.")
            return 1
        second = json.loads(restarted.stdout)["manifest"]["fingerprint"]["value"]
        if second == first:
            report("touch-guard-drift: authority edit did not change the fingerprint.")
            return 1
        if expect_guard_allow(
            repo, repo / "src/feature.js", "touch-guard-drift after restart"
        ):
            return 1

        # A fingerprint-neutral edit to the task's own file is a record write,
        # not drift. This used to fail closed, which is the defect issue #8
        # reports: appending Evidence blocked every following write.
        tasks_path.write_text(
            tasks_path.read_text(encoding="utf-8") + "\n", encoding="utf-8"
        )
        if expect_guard_allow(
            repo, repo / "src/feature.js", "touch-guard-drift cosmetic edit"
        ):
            return 1
        cosmetic = run_keel(repo, "guard", "status", "--json")
        cosmetic_payload = json.loads(cosmetic.stdout) if cosmetic.stdout else {}
        if cosmetic_payload.get("status") != "active" or cosmetic_payload.get(
            "problems"
        ):
            report(
                "touch-guard-drift: a fingerprint-neutral edit to the task's "
                "own file was reported as a guard problem."
            )
            report(cosmetic.stdout or "")
            return 1
        restarted_cosmetic = run_keel(
            repo, "guard", "start", "--change", "demo", "--task", "1.1",
            "--force", "--json",
        )
        if restarted_cosmetic.returncode != 0:
            report("touch-guard-drift: cosmetic restart failed.")
            report((restarted_cosmetic.stderr or restarted_cosmetic.stdout).strip())
            return 1
        third = json.loads(restarted_cosmetic.stdout)["manifest"]["fingerprint"][
            "value"
        ]
        if third != second:
            report("touch-guard-drift: cosmetic edit drifted the capsule fingerprint.")
            return 1

        write_text(
            tasks_path,
            tasks_path.read_text(encoding="utf-8").replace("- [ ] 1.1", "- [x] 1.1"),
        )
        if expect_guard_deny(
            repo,
            repo / "src/feature.js",
            ["keel guard clear"],
            "touch-guard-drift completed task",
        ):
            return 1
        completed = run_keel(repo, "guard", "status", "--json")
        if (
            completed.returncode != 3
            or json.loads(completed.stdout).get("status") != "completed"
        ):
            report("touch-guard-drift: status did not report completed.")
            return 1

        (repo / "keel/guard.json").write_text("not json", encoding="utf-8")
        if expect_guard_deny(
            repo,
            repo / "src/feature.js",
            ["invalid", "keel guard clear"],
            "touch-guard-drift invalid manifest",
        ):
            return 1
        invalid = run_keel(repo, "guard", "status", "--json")
        if invalid.returncode != 3 or json.loads(invalid.stdout).get("status") != "invalid":
            report("touch-guard-drift: status did not report invalid.")
            return 1
        cleared = run_keel(repo, "guard", "clear", "--json")
        if cleared.returncode != 0 or (repo / "keel/guard.json").exists():
            report("touch-guard-drift: clear did not recover from invalid manifest.")
            return 1

    report("touch-guard-drift scenario passed.")
    return 0


def validate_guard_stale_manifest_scenario() -> int:
    """A manifest whose change is gone says so, instead of enumerating Touch.

    `taskIsChecked` reads `openspec/changes/<change>/tasks.md`. After the change
    is archived that path is gone, the read throws, the miss is read as "not
    checked", and control reaches the Touch comparison — which denies the write
    while naming a task inside an archived change and telling the reader to
    reauthorize it. That instruction cannot be followed. `keel guard status`
    already classifies the same manifest as drifted; the hook enforcing it did
    not, and the two states it conflates are genuinely different: a task id
    missing from a live `tasks.md` is a parse miss the guard must not guess
    about, while a directory that is not there is a fact.

    Measured at the start of this change: the first write of a new change was
    refused against `the-name-is-not-the-thing#2.1`, archived one commit earlier.
    """
    with tempfile.TemporaryDirectory(
        prefix="keel-guard-stale-", ignore_cleanup_errors=True
    ) as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()
        change_dir = repo / "openspec/changes/demo"
        write_text(change_dir / "tasks.md", guard_task_fixture())
        write_text(repo / "src/feature.js", "// fixture\n")

        started = run_keel(
            repo, "guard", "start", "--change", "demo", "--task", "1.1", "--json"
        )
        if started.returncode != 0:
            report("guard-stale-manifest: guard start failed.")
            report((started.stderr or started.stdout).strip())
            return 1

        # The directory is relocated to the path `openspec archive` moves it to.
        # What is under test is the guard's answer once the change is gone, not
        # the archiver's behavior; making this depend on a complete change plus
        # the OpenSpec CLI would couple a guard test to a program it never
        # exercises. That archive relocates rather than marking in place was
        # verified directly against this repository — see design.md A2.
        archived_dir = repo / "openspec/changes/archive/2026-08-02-demo"
        archived_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(change_dir), str(archived_dir))

        decision = pretooluse_decision(
            run_pretooluse_guard_hook(
                repo, edit_event(repo, repo / "src/feature.js", "Edit")
            )
        )
        if decision is None:
            report(
                "guard-stale-manifest: M1 archiving the change made the guard "
                "allow a write silently. A stale manifest must fail closed, or "
                "`openspec archive` quietly disables the guard."
            )
            return 1
        if decision.get("permissionDecision") != "deny":
            report(
                "guard-stale-manifest: M1 expected deny once the change was "
                f"archived, got {decision.get('permissionDecision')!r}."
            )
            return 1
        reason = decision.get("permissionDecisionReason", "")
        for needle in ("stale", "keel guard clear", "openspec/changes/demo"):
            if needle not in reason:
                report(
                    "guard-stale-manifest: M1 the refusal must report the "
                    f"manifest as stale and name what resolves it; {needle!r} "
                    f"is missing from: {reason!r}"
                )
                return 1

        # M2 — the advice that could not be followed must be gone. The old
        # denial enumerated Touch for a task in an archived change and told the
        # reader to reauthorize it.
        for forbidden in ("update the task authority", "Touch allows:"):
            if forbidden in reason:
                report(
                    "guard-stale-manifest: M2 the refusal still tells the "
                    f"reader to do something impossible; {forbidden!r} is in: "
                    f"{reason!r}"
                )
                return 1

        # M3 — a live change whose task id is absent is a parse miss, and the
        # guard's answer there is unchanged.
        shutil.move(str(archived_dir), str(change_dir))
        write_text(
            change_dir / "tasks.md",
            guard_task_fixture().replace("1.1", "9.9"),
        )
        miss = pretooluse_decision(
            run_pretooluse_guard_hook(
                repo, edit_event(repo, repo / "src/outside.js", "Edit")
            )
        )
        if miss is None or miss.get("permissionDecision") != "deny":
            report(
                "guard-stale-manifest: M3 a write outside Touch must still be "
                f"denied when the task id is absent from a live tasks.md; got "
                f"{miss!r}"
            )
            return 1
        miss_reason = miss.get("permissionDecisionReason", "")
        if "Touch allows:" not in miss_reason:
            report(
                "guard-stale-manifest: M3 the parse-miss path must still deny "
                f"by enumerating Touch. Got: {miss_reason!r}"
            )
            return 1
        if "stale" in miss_reason:
            report(
                "guard-stale-manifest: M3 a live change with an unmatched task "
                f"id was reported as a stale manifest. Got: {miss_reason!r}"
            )
            return 1

    if "guard-stale-manifest" not in {name for name, _ in registry.SCENARIOS}:
        report("guard-stale-manifest: the scenario registry does not include it.")
        return 1
    report("guard-stale-manifest scenario passed.")
    return 0


# The message a reader is given when the state cannot be reauthorized.
#
# 5.26.0 recorded verbatim, so the parse-miss cell compares against the text as
# it shipped rather than against whatever the code happens to produce.
PARSE_MISS_PROBLEM = (
    "Guarded task demo#1.1 no longer resolves; reauthorize through "
    "`keel gate task-start` and `keel guard start`."
)


def guard_status_payload(repo: Path, cell: str) -> tuple[dict, str]:
    """Return `guard status --json` as a payload plus its first problem message.

    A run that produced nothing readable is reported here rather than handed
    back as an empty payload. Otherwise one condition downstream would guard two
    unrelated failures — the command did not run, and the status was wrong — and
    every caller would report the second, sending the reader to a state that was
    never observed. Returning `None` for the payload is what makes the two
    distinguishable at the call site instead of at the reader.
    """
    result = run_keel(repo, "guard", "status", "--json")
    if not result.stdout.strip():
        report(
            f"guard-status-stale-manifest: {cell} `guard status --json` "
            f"produced no output (exit {result.returncode}). "
            f"{(result.stderr or '').strip()!r}"
        )
        return None, ""
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        report(
            f"guard-status-stale-manifest: {cell} `guard status --json` "
            f"produced output that is not JSON ({error}): {result.stdout!r}"
        )
        return None, ""
    problems = payload.get("problems", [])
    return payload, (problems[0].get("message", "") if problems else "")


def validate_guard_status_stale_manifest_scenario() -> int:
    """`keel guard status` says which of two states the manifest is in.

    `loadTaskContract` returns `null` when the tasks file is absent and when the
    task id is not in it. `guardStatus` had one branch for both, so a manifest
    whose change had been archived and a manifest whose task id was merely
    renumbered produced byte-identical output — and the shared message told the
    reader to reauthorize, which for the archived change is impossible:
    `keel gate task-start` reports a missing tasks file and `keel guard start`
    reports that the task does not exist. Neither names `keel guard clear`,
    which is the only action that resolves it.

    The write guard hook drew this line in 5.12.0 by testing the change
    directory. This is the same test on the surface that describes the manifest
    rather than the one that refuses a write. Measured at the start of this
    change: both states returned `Guarded task demo#1.1 no longer resolves`.
    """
    with tempfile.TemporaryDirectory(
        prefix="keel-guard-status-stale-", ignore_cleanup_errors=True
    ) as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()
        change_dir = repo / "openspec/changes/demo"
        write_text(change_dir / "tasks.md", guard_task_fixture())
        write_text(repo / "src/feature.js", "// fixture\n")

        started = run_keel(
            repo, "guard", "start", "--change", "demo", "--task", "1.1", "--json"
        )
        if started.returncode != 0:
            report("guard-status-stale-manifest: guard start failed.")
            report((started.stderr or started.stdout).strip())
            return 1

        # Relocated to where `openspec archive` moves it, for the reason the
        # guard-stale-manifest scenario records: what is under test is the
        # answer once the change is gone, not the archiver.
        archived_dir = repo / "openspec/changes/archive/2026-08-04-demo"
        archived_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(change_dir), str(archived_dir))

        # M1 — the archived state names the directory that is gone and the
        # action that resolves it.
        stale, stale_message = guard_status_payload(repo, "M1")
        if stale is None:
            return 1
        if stale.get("status") != "drifted":
            report(
                "guard-status-stale-manifest: M1 expected the archived state to "
                f"stay classified as drifted, got {stale.get('status')!r}."
            )
            return 1
        stale_codes = [item.get("code") for item in stale.get("problems", [])]
        if "stale-manifest" not in stale_codes:
            report(
                "guard-status-stale-manifest: M1 an archived change was not "
                "reported under its own problem code, so a --json reader cannot "
                f"tell it from a parse miss. Codes: {stale_codes!r}"
            )
            return 1
        for needle in ("stale", "openspec/changes/demo", "keel guard clear"):
            if needle not in stale_message:
                report(
                    "guard-status-stale-manifest: M1 the message must report the "
                    f"manifest as stale and name what resolves it; {needle!r} is "
                    f"missing from: {stale_message!r}"
                )
                return 1
        # The advice that could not be followed. `keel gate task-start` may
        # still be named for the task the reader is actually starting — what
        # must be gone is the instruction to reauthorize the vanished one.
        for forbidden in ("reauthorize through", "keel guard start"):
            if forbidden in stale_message:
                report(
                    "guard-status-stale-manifest: M1 the message still sends the "
                    f"reader to reauthorize a change that is not there; "
                    f"{forbidden!r} is in: {stale_message!r}"
                )
                return 1

        # M3 — the parse miss is untouched. A live change whose task id is
        # absent is not a fact about the repository, it is a read the guard
        # must not guess about, and its answer is the 5.26.0 answer verbatim.
        change_dir.mkdir(parents=True, exist_ok=True)
        write_text(
            change_dir / "tasks.md",
            guard_task_fixture().replace("1.1", "9.9"),
        )
        miss, miss_message = guard_status_payload(repo, "M3")
        if miss is None:
            return 1
        if miss.get("status") != "drifted":
            report(
                "guard-status-stale-manifest: M3 the parse miss changed status "
                f"from drifted to {miss.get('status')!r}."
            )
            return 1
        miss_codes = [item.get("code") for item in miss.get("problems", [])]
        if miss_codes != ["authority-drift"]:
            report(
                "guard-status-stale-manifest: M3 the parse miss changed problem "
                f"code. Expected ['authority-drift'], got {miss_codes!r}"
            )
            return 1
        if miss_message != PARSE_MISS_PROBLEM:
            report(
                "guard-status-stale-manifest: M3 the parse-miss message changed "
                f"from the 5.26.0 text.\nwas:  {PARSE_MISS_PROBLEM!r}\nnow:  "
                f"{miss_message!r}"
            )
            return 1

        # M2 — the two states no longer answer the same. Asserted on both the
        # code and the message: a repair that reworded one branch while leaving
        # one code for two states would pass a message comparison alone.
        if stale_codes == miss_codes:
            report(
                "guard-status-stale-manifest: M2 an archived change and a task "
                "id absent from a live tasks.md still share a problem code "
                f"({stale_codes!r}), so they are separable only by prose."
            )
            return 1
        if stale_message == miss_message:
            report(
                "guard-status-stale-manifest: M2 the two states still produce "
                f"one message: {stale_message!r}"
            )
            return 1

        # D4 — a third state: the change directory is there and its tasks file
        # is not. That is a live change mid-authoring, where reauthorizing after
        # writing the tasks file is genuinely the way out, so it keeps the
        # parse-miss message. This is what testing the directory rather than the
        # tasks file buys, and it is the cell that fails if the two are swapped.
        (change_dir / "tasks.md").unlink()
        authoring, authoring_message = guard_status_payload(repo, "D4")
        if authoring is None:
            return 1
        if authoring_message != PARSE_MISS_PROBLEM:
            report(
                "guard-status-stale-manifest: D4 a live change whose tasks.md "
                "is absent was reported as a stale manifest; the change is "
                f"still there and can be reauthorized. Got: {authoring_message!r}"
            )
            return 1

    if "guard-status-stale-manifest" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "guard-status-stale-manifest: the scenario registry does not "
            "include it."
        )
        return 1
    report("guard-status-stale-manifest scenario passed.")
    return 0


def validate_an_authorization_names_its_repository_scenario() -> int:
    """Issue #136: the vocabulary had no name for a tracker write.

    `change-close` routes an unresolved follow-up to a durable owner and accepts
    an absolute https reference, which in practice is a tracker issue — while the
    standing-authorization vocabulary had no way to say the agent may create one.
    The entry added for it is the first whose credential reaches further than the
    checkout the declaration sits in: `gh` is account-wide, so a bare `issue`
    would be the widest entry in a file whose other entries the checkout bounds.
    It therefore names the repository it reaches, and the bare form is refused.
    """
    label = "an-authorization-names-its-repository"

    with tempfile.TemporaryDirectory(prefix="keel-issue-scope-") as raw:
        root = Path(raw)

        def fixture(name: str, body: str) -> Path:
            repo = root / name
            repo.mkdir()
            write_authorize_config(repo, body)
            return repo

        # M1 — the scoped form is accepted, beside an ordinary entry so the
        # assertion is about this entry and not about the block parsing at all.
        scoped = fixture(
            "scoped", "authorize:\n  - commit\n  - issue:acme/widgets\n"
        )
        out = run_keel(scoped, "--doctor").stdout
        if "authorize: ok" not in out or "issue:acme/widgets" not in out:
            report(
                f"{label}: a scoped tracker entry was refused. `gh` is "
                "account-wide, so this is the one entry that has to name its "
                "repository, and it is the one the vocabulary rejects."
            )
            report(out)
            return 1
        if "commit: authorized" not in out:
            report(
                f"{label}: the entry beside the scoped one lost its "
                "authorization, so the scoped entry voided the declaration "
                "rather than joining it."
            )
            report(out)
            return 1

        # The per-action line, which is the half a reader looks at. Without it
        # the same screen lists the entry as declared and reports the action as
        # unauthorized.
        if "issue: authorized" not in out or "acme/widgets" not in out.split(
            "issue: authorized", 1
        )[-1].split("\n", 1)[0]:
            report(
                f"{label}: the per-action line does not report the scoped entry "
                "as authorized and name its scope."
            )
            report(out)
            return 1
        if "issue: not authorized" in out:
            report(
                f"{label}: the doctor lists the entry as declared and reports "
                "`issue: not authorized` on the same screen, so the diagnostic "
                "contradicts itself."
            )
            report(out)
            return 1
        # D2 is unfixable by mechanism, so it is owed to wording: a reader must
        # not take the scope for a sandbox.
        if "does not enforce" not in out:
            report(
                f"{label}: the output does not say Keel carries the scope "
                "without enforcing it, so a reader can take it for a fence."
            )
            report(out)
            return 1

        # M2 — the bare form is refused, and the refusal carries the form it
        # needs. The refusal alone is not the assertion: a bare `issue` was
        # already refused before this existed, by not being a name at all.
        bare = fixture("bare", "authorize:\n  - commit\n  - issue\n")
        out = run_keel(bare, "--doctor").stdout
        if "authorize: failed" not in out:
            report(f"{label}: a bare tracker entry was granted.")
            report(out)
            return 1
        if "issue:<owner>/<repo>" not in out:
            report(
                f"{label}: the bare-entry refusal does not name the form it "
                "requires, so a reader is told `issue` is not a name rather "
                "than that it is a name needing a scope."
            )
            report(out)
            return 1

        # M3 — the shape is checked, on both sides of correct.
        for name, body in (
            ("short", "authorize:\n  - issue:acme\n"),
            ("long", "authorize:\n  - issue:acme/widgets/extra\n"),
            ("empty-owner", "authorize:\n  - issue:/widgets\n"),
            ("empty-repo", "authorize:\n  - issue:acme/\n"),
        ):
            repo = fixture(name, body)
            out = run_keel(repo, "--doctor").stdout
            if "authorize: failed" not in out:
                report(
                    f"{label}: a malformed scope ({name}) was accepted; a shape "
                    "check that passes everything checks nothing."
                )
                report(out)
                return 1
            declared_entry = body.strip().splitlines()[-1].strip("- ")
            if declared_entry not in out:
                report(
                    f"{label}: the refusal for {name} does not name the "
                    f"offending entry {declared_entry!r}."
                )
                report(out)
                return 1

        # M3 — and fail-closed is unchanged by the new form: a valid scoped
        # entry beside an unrecognized one authorizes nothing.
        mixed = fixture(
            "mixed", "authorize:\n  - issue:acme/widgets\n  - deploy\n"
        )
        out = run_keel(mixed, "--doctor").stdout
        if "authorize: failed" not in out or "deploy" not in out:
            report(f"{label}: an unrecognized entry beside a scoped one did not fail closed.")
            report(out)
            return 1
        if "issue: authorized" in out:
            report(
                f"{label}: the scoped entry stayed authorized beside an "
                "unrecognized one, so the declaration did not fail closed."
            )
            report(out)
            return 1


        # M3 — the new rendering did not turn an undeclared action into a
        # declared one.
        only_commit = fixture("only-commit", "authorize:\n  - commit\n")
        out = run_keel(only_commit, "--doctor").stdout
        for action in ("push", "release", "archive", "continuation", "issue"):
            if f"{action}: not authorized" not in out:
                report(
                    f"{label}: {action} is not reported as unauthorized in a "
                    "repository that declared only commit."
                )
                report(out)
                return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


EXTERNAL_AGENT_FACT_FIELDS = {
    "name", "source", "executable", "resolved", "allowed",
    "command", "sandbox", "ownSandbox", "sendsTo", "pitfalls",
}


def _external_agents_env(base: Path) -> tuple[dict[str, str], Path]:
    """An environment whose Keel home and PATH belong to the fixture.

    The stub `codex` stands in for the real one so resolution is checked against
    a path the scenario controls; it records any invocation, because a catalog
    or a brief that launched the agent would be the one thing Keel promised not
    to do.
    """
    home = base / "home"
    home.mkdir()
    stub_bin = base / "bin"
    stub_bin.mkdir()
    calls = base / "calls.log"
    for name in ("codex", "dsh"):
        stub = stub_bin / name
        stub.write_text(f"#!/bin/sh\necho {name} \"$@\" >> '{calls}'\n", encoding="utf-8")
        stub.chmod(0o755)
    env = dict(os.environ)
    env["KEEL_HOME"] = str(home)
    env["PATH"] = f"{stub_bin}{os.pathsep}{env.get('PATH', '')}"
    return env, calls


def validate_external_agent_catalog_scenario() -> int:
    """The catalog records facts, merges the machine file, and stays on demand.

    #219: an external model CLI writes outside the host's write guard and sends
    the repository to another provider. What Keel offers about one is facts a
    reader can check — template, sandboxes, destination, dated pitfalls — and
    never a judgement of what it is good at, because a judgement resident in the
    session steers the agent that reads it (owner, 2026-10-04).
    """
    label = "external-agent-catalog:"
    with tempfile.TemporaryDirectory(prefix="keel-agents-") as raw:
        base = Path(raw)
        env, calls = _external_agents_env(base)
        repo = base / "repo"
        repo.mkdir()
        write_gate_fixture(repo, standing_authorization_task())
        write_authorize_config(repo, "external_agents:\n  allow:\n    - codex\n")

        def listing() -> dict | None:
            result = run_keel(repo, "agents", "--json", env=env)
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                report(f"{label} `keel agents --json` printed no JSON: "
                       f"{(result.stdout + result.stderr).strip()[:400]}")
                return None

        payload = listing()
        if payload is None:
            return 1
        agents = {item.get("name"): item for item in payload.get("agents") or []}
        for name in ("codex", "dsh"):
            if agents.get(name, {}).get("source") != "bundled":
                report(f"{label} {name} is not listed as a bundled entry: {agents.get(name)}")
                return 1
        stub = str(base / "bin" / "codex")
        if agents["codex"].get("resolved") != stub:
            report(f"{label} codex resolved to {agents['codex'].get('resolved')!r}, not the stub on PATH.")
            return 1
        dsh_path = agents["dsh"].get("executable")
        expected = dsh_path if dsh_path and Path(dsh_path).exists() else None
        if agents["dsh"].get("resolved") != expected:
            report(f"{label} dsh resolution {agents['dsh'].get('resolved')!r} disagrees with "
                   f"whether {dsh_path!r} exists.")
            return 1
        if agents["codex"].get("allowed") is not True or agents["dsh"].get("allowed") is not False:
            report(f"{label} allowance is not read from external_agents: allow: "
                   f"codex={agents['codex'].get('allowed')!r} dsh={agents['dsh'].get('allowed')!r}")
            return 1
        for name, item in agents.items():
            extra = set(item) - EXTERNAL_AGENT_FACT_FIELDS
            if extra:
                report(f"{label} {name} carries fields outside the fact fields: {sorted(extra)}. "
                       "The catalog records facts, not a judgement of what an agent suits.")
                return 1
            pitfalls = item.get("pitfalls") or []
            if not pitfalls:
                report(f"{label} {name} records no pitfall.")
                return 1
            for pitfall in pitfalls:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(pitfall.get("date", ""))) \
                        or not str(pitfall.get("source", "")).strip():
                    report(f"{label} {name} has a pitfall without a date and a source: {pitfall}")
                    return 1

        shown = run_keel(repo, "agents", "codex", env=env)
        text = shown.stdout
        codex = agents["codex"]
        for needle in (codex.get("command"), "read-only", "workspace-write", codex.get("sendsTo"),
                       *[p["text"] for p in codex["pitfalls"]],
                       *[p["date"] for p in codex["pitfalls"]]):
            if not needle:
                report(f"{label} the codex entry has an empty command, destination, or pitfall.")
                return 1
            if needle not in text:
                report(f"{label} `keel agents codex` does not print {needle!r}.")
                return 1

        # Issue #259: dsh's headless profile has a sandbox of its own, as measured.
        dsh_text = run_keel(repo, "agents", "dsh", env=env).stdout
        sandbox_line = next((line for line in dsh_text.splitlines() if line.startswith("Sandbox:")), "")
        if "workspace-write" not in sandbox_line:
            report(f"{label} `keel agents dsh` does not describe its own sandbox: {sandbox_line!r}")
            return 1
        for needle in ("/dev/stdout", "PYTHONPYCACHEPREFIX"):
            if needle not in dsh_text:
                report(f"{label} `keel agents dsh` has no pitfall naming {needle!r}.")
                return 1
        if "reads and writes wherever it is started" in dsh_text:
            report(f"{label} `keel agents dsh` still says it reads and writes wherever it is started.")
            return 1

        # A machine entry declaring one field overrides that field only.
        custom = base / "bin" / "dsh"
        (base / "home" / "agents.json").write_text(
            json.dumps({"agents": {"dsh": {"executable": str(custom)}}}), encoding="utf-8")
        payload = listing()
        if payload is None:
            return 1
        dsh = {item.get("name"): item for item in payload.get("agents") or []}.get("dsh") or {}
        if dsh.get("source") != "machine" or dsh.get("executable") != str(custom):
            report(f"{label} the machine entry did not override dsh: {dsh}")
            return 1
        if dsh.get("command") != agents["dsh"].get("command"):
            report(f"{label} a machine entry declaring only an executable replaced the bundled template.")
            return 1

        # A malformed machine file is named and none of it is used.
        (base / "home" / "agents.json").write_text("{not json", encoding="utf-8")
        payload = listing()
        if payload is None:
            return 1
        problems = " ".join(payload.get("problems") or [])
        if "agents.json" not in problems:
            report(f"{label} a malformed agents.json was not reported: {payload.get('problems')}")
            return 1
        sources = {item.get("source") for item in payload.get("agents") or []}
        if sources != {"bundled"}:
            report(f"{label} a malformed agents.json still contributed entries: {sources}")
            return 1

        # Session start carries no catalog.
        context = run_keel(repo, "context", env=env)
        for needle in ("dsh", "DeepSeek", "/dev/null", "workspace-write"):
            if needle in context.stdout:
                report(f"{label} `keel context` carries catalog text {needle!r}.")
                return 1
        if calls.exists():
            report(f"{label} an agent was launched: {calls.read_text(encoding='utf-8').strip()}")
            return 1

    report("external-agent-catalog scenario passed.")
    return 0


def external_agent_brief_task() -> str:
    return (
        "- [ ] 1.1 Speed up the parser\n"
        "  - Covers:\n"
        "    - E1: public behavior\n"
        "  - Read:\n"
        "    - docs/spec.md\n"
        "    - secrets/vendor.key\n"
        "  - Touch:\n"
        "    - src/feature.js\n"
        "  - Verify:\n"
        "    - Strategy: evidence-first\n"
        "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "    - M1: node test.js proves the parser is faster\n"
        "  - Evidence:\n"
        "    - Contract: pending\n"
        "    - M1: pending\n"
        "    - Review:\n"
        "      - Status: pending\n"
        "      - Acceptance check: pending\n"
        "      - Scope check: pending\n"
        "      - Findings: pending\n"
        "    - Blocker: none\n"
    )


def validate_external_agent_brief_scenario() -> int:
    """The brief is the delegation brief, checked for egress and write boundary.

    #219: Keel compiles what the external agent is handed and prints the command;
    the session runs it. The brief refuses what the project has not allowed, a
    path the project said must not leave, and any write into the session's own
    checkout, because the host's write guard never sees an external process.
    """
    label = "external-agent-brief:"
    with tempfile.TemporaryDirectory(prefix="keel-agent-brief-") as raw:
        base = Path(raw)
        env, calls = _external_agents_env(base)
        repo = base / "repo"
        repo.mkdir()
        write_gate_fixture(repo, external_agent_brief_task())
        write_text(repo / "docs/spec.md", "spec\n")
        write_text(repo / "secrets/vendor.key", "key\n")
        write_text(repo / "src/feature.js", "// feature\n")
        for command in (["init", "-q"], ["add", "-A"],
                        ["-c", "user.email=k@example.com", "-c", "user.name=k",
                         "commit", "-q", "-m", "fixture"]):
            subprocess.run(["git", *command], cwd=repo, check=True, capture_output=True)
        prompt = base / "brief.md"

        def brief(name: str, mode: str, directory: Path) -> tuple[dict, str]:
            if prompt.exists():
                prompt.unlink()
            result = run_keel(repo, "agents", "brief", name, "--mode", mode,
                              "--dir", str(directory), "--out", str(prompt),
                              "--change", "demo", "--task", "1.1", "--json", env=env)
            try:
                return json.loads(result.stdout), result.stdout + result.stderr
            except json.JSONDecodeError:
                return {}, result.stdout + result.stderr

        def refused(payload: dict, output: str, *needles: str, what: str) -> bool:
            reasons = " ".join(payload.get("reasons") or [])
            if payload.get("status") != "blocked":
                report(f"{label} {what} was not refused: {output.strip()[:400]}")
                return False
            for needle in needles:
                if needle not in reasons:
                    report(f"{label} {what} was refused without naming {needle!r}: {reasons}")
                    return False
            if prompt.exists():
                report(f"{label} {what} was refused but still wrote a prompt file.")
                return False
            return True

        # Absent declaration allows nothing, and says how to declare.
        payload, out = brief("codex", "helper", repo)
        if not refused(payload, out, "external_agents:", "allow:", what="an undeclared project"):
            return 1
        # An agent outside allow.
        write_authorize_config(repo, "external_agents:\n  allow:\n    - codex\n")
        payload, out = brief("dsh", "helper", repo)
        if not refused(payload, out, "dsh", "codex", what="an agent outside allow"):
            return 1
        # A deny entry without a reason refuses every brief.
        write_authorize_config(repo, "external_agents:\n  allow:\n    - codex\n"
                                     "  egress_deny:\n    - secrets/**\n")
        payload, out = brief("codex", "helper", repo)
        if not refused(payload, out, "secrets/**", what="a deny entry without a reason"):
            return 1
        # A denied Read path refuses, naming path, pattern and reason.
        write_authorize_config(repo, "external_agents:\n  allow: [codex, dsh]\n"
                                     "  egress_deny:\n    - secrets/**: vendor NDA keys\n")
        payload, out = brief("codex", "helper", repo)
        if not refused(payload, out, "secrets/vendor.key", "secrets/**", "vendor NDA keys",
                       what="a denied Read path"):
            return 1
        # A clean helper brief.
        write_authorize_config(repo, "external_agents:\n  allow: [codex, dsh]\n"
                                     "  egress_deny:\n    - private/**: customer data\n")
        payload, out = brief("codex", "helper", repo)
        if payload.get("status") != "ready":
            report(f"{label} a clean helper brief was refused: {out.strip()[:600]}")
            return 1
        if not prompt.exists():
            report(f"{label} a clean helper brief reported ready but wrote no prompt file.")
            return 1
        text = prompt.read_text(encoding="utf-8")
        for needle in ("Speed up the parser", "docs/spec.md", "secrets/vendor.key",
                       "M1: node test.js", "commit", "push", "OpenSpec"):
            if needle not in text:
                report(f"{label} the prompt file does not carry {needle!r}.")
                return 1
        command = payload.get("run") or ""
        for needle in ("read-only", str(repo), str(prompt)):
            if needle not in command:
                report(f"{label} the printed command does not name {needle!r}: {command}")
                return 1
        if "cannot observe" not in " ".join(payload.get("warnings") or []):
            report(f"{label} the brief does not say Keel cannot observe what the agent reads.")
            return 1
        # A helper with no sandbox over the session's own checkout.
        payload, out = brief("dsh", "helper", repo)
        if not refused(payload, out, "sandbox", "worktree", what="a dsh helper over the checkout"):
            return 1
        # Implementation with no guard is refused, naming the guard: the host's
        # guard never sees an external process, so this is its only check.
        payload, out = brief("codex", "implementation", repo)
        if not refused(payload, out, "requires an active write guard", what="an unguarded implementation"):
            return 1
        started = run_keel(repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
                           "--record", "--json", env=env)
        if json.loads(started.stdout).get("status") != "pass":
            report(f"{label} the fixture task did not start: {started.stdout[:400]}")
            return 1
        payload, out = brief("codex", "implementation", repo)
        if not refused(payload, out, "worktree", what="an implementation over the checkout"):
            return 1
        worktree = base / "agent-wt"
        subprocess.run(["git", "worktree", "add", "-q", "--detach", str(worktree)],
                       cwd=repo, check=True, capture_output=True)
        payload, out = brief("codex", "implementation", worktree)
        if payload.get("status") != "ready":
            report(f"{label} an implementation brief over a separate worktree was refused: "
                   f"{out.strip()[:600]}")
            return 1
        if not prompt.exists():
            report(f"{label} an implementation brief reported ready but wrote no prompt file.")
            return 1
        command = payload.get("run") or ""
        for needle in ("workspace-write", str(worktree)):
            if needle not in command:
                report(f"{label} the implementation command does not name {needle!r}: {command}")
                return 1
        # Issue #262: a helper worktree beside the session's, under .claude/worktrees/.
        session_tree = repo / ".claude" / "worktrees" / "review"
        helper_tree = repo / ".claude" / "worktrees" / "dsh_review"
        # A real project commits its external_agents: declaration, so worktrees carry it.
        for command in (["add", "-A"], ["-c", "user.email=k@example.com", "-c", "user.name=k",
                                        "commit", "-q", "-m", "declare external agents"]):
            subprocess.run(["git", *command], cwd=repo, check=True, capture_output=True)
        for tree in (session_tree, helper_tree):
            subprocess.run(["git", "worktree", "add", "-q", "--detach", str(tree)],
                           cwd=repo, check=True, capture_output=True)

        def helper_brief(cwd: Path) -> tuple[dict, str]:
            if prompt.exists():
                prompt.unlink()
            result = run_keel(cwd, "agents", "brief", "dsh", "--mode", "helper",
                              "--dir", str(helper_tree), "--out", str(prompt),
                              "--change", "demo", "--task", "1.1", "--json", env=env)
            try:
                return json.loads(result.stdout), result.stdout + result.stderr
            except json.JSONDecodeError:
                return {}, result.stdout + result.stderr

        payload, out = helper_brief(session_tree)
        if payload.get("status") != "ready":
            report(f"{label} a helper worktree under .claude/worktrees/ was refused from a sibling worktree: "
                   f"{out.strip()[:600]}")
            return 1
        # Issue #259: a dsh brief keeps temporary files in tmp/ beside the brief.
        tmp = prompt.parent / "tmp"
        if not tmp.is_dir():
            report(f"{label} the dsh brief did not create {tmp} beside --out.")
            return 1
        if str(tmp) not in prompt.read_text(encoding="utf-8"):
            report(f"{label} the dsh brief does not name its temporary directory {tmp}.")
            return 1
        command = payload.get("run") or ""
        for needle in (f"TMPDIR={tmp}", f"PYTHONPYCACHEPREFIX={tmp}/pycache"):
            if needle not in command:
                report(f"{label} the dsh command does not set {needle!r}: {command}")
                return 1
        payload, out = helper_brief(helper_tree)
        if not refused(payload, out, str(helper_tree.resolve()), "current directory", "--repo",
                       what="a helper brief run from inside its own --dir"):
            return 1
        if calls.exists():
            report(f"{label} an agent was launched: {calls.read_text(encoding='utf-8').strip()}")
            return 1

    report("external-agent-brief scenario passed.")
    return 0


def validate_external_agent_exit_status_scenario() -> int:
    """The printed command records the agent's exit status (#221).

    Of nine codex runs read in rtl_ppa_prj, one recorded its exit status; a run
    that finished with `exit=0` read as a failure because it left no result
    file. The status is the one signal that is not the agent's own report.
    """
    label = "external-agent-exit-status:"
    with tempfile.TemporaryDirectory(prefix="keel-agent-exit-") as raw:
        base = Path(raw).resolve()
        env, _calls = _external_agents_env(base)
        for name in ("codex", "dsh"):
            stub = base / "bin" / name
            stub.write_text("#!/bin/sh\ncat > /dev/null\nexit 3\n", encoding="utf-8")
            stub.chmod(0o755)
        (base / "home" / "agents.json").write_text(
            json.dumps({"agents": {"dsh": {"executable": str(base / "bin" / "dsh")}}}),
            encoding="utf-8")
        repo = base / "repo"
        repo.mkdir()
        write_gate_fixture(repo, external_agent_brief_task())
        write_text(repo / "src/feature.js", "// feature\n")
        write_authorize_config(repo, "external_agents:\n  allow: [codex, dsh]\n")
        for command in (["init", "-q"], ["add", "-A"],
                        ["-c", "user.email=k@example.com", "-c", "user.name=k",
                         "commit", "-q", "-m", "fixture"]):
            subprocess.run(["git", *command], cwd=repo, check=True, capture_output=True)
        worktree = base / "agent-wt"
        subprocess.run(["git", "worktree", "add", "-q", "--detach", str(worktree)],
                       cwd=repo, check=True, capture_output=True)

        for name, directory in (("codex", repo), ("dsh", worktree)):
            prompt = base / f"{name}-brief.md"
            result = run_keel(repo, "agents", "brief", name, "--mode", "helper",
                              "--dir", str(directory), "--out", str(prompt),
                              "--change", "demo", "--task", "1.1", "--json", env=env)
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError:
                report(f"{label} {name} brief printed no JSON: {(result.stdout + result.stderr)[:400]}")
                return 1
            if payload.get("status") != "ready":
                report(f"{label} {name} brief was refused: {payload.get('reasons')}")
                return 1
            exit_file = payload.get("exit")
            if not exit_file:
                report(f"{label} the {name} brief names no exit file.")
                return 1
            text = run_keel(repo, "agents", "brief", name, "--mode", "helper",
                            "--dir", str(directory), "--out", str(prompt),
                            "--change", "demo", "--task", "1.1", env=env).stdout
            if exit_file not in text:
                report(f"{label} the {name} text output does not name the exit file {exit_file}.")
                return 1
            ran = subprocess.run(["sh", "-c", f"{payload['run']}\npwd"], cwd=base, env=env,
                                 capture_output=True, text=True)
            if not Path(exit_file).exists():
                report(f"{label} running the {name} command wrote no exit file: {ran.stderr[:300]}")
                return 1
            status = Path(exit_file).read_text(encoding="utf-8").strip()
            if status != "3":
                report(f"{label} the {name} exit file holds {status!r}, not the stub's 3.")
                return 1
            if ran.stdout.strip().splitlines()[-1:] != [str(base)]:
                report(f"{label} running the {name} command moved the shell to {ran.stdout.strip()!r}.")
                return 1

        shown = run_keel(repo, "agents", "codex", env=env).stdout
        if not re.search(r"parallel[^\n]*quota", shown, re.I):
            report(f"{label} `keel agents codex` has no pitfall about parallel runs sharing one quota.")
            return 1

    report("external-agent-exit-status scenario passed.")
    return 0

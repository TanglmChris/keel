"""Keel validation: selfcheck (split from validate_plugin.py, #409)."""
from __future__ import annotations

import contextlib
import importlib
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
import types
import ast
import atexit
import signal
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from validation.common import (
    BOOTSTRAP_BLOCK_BYTE_BUDGET,
    ROOT,
    report,
    run_keel,
    run_scenario_processes,
    skip_scenario,
    validate_resident_blocks,
    validation_source_with,
    validation_sources,
    write_text,
)
from validation import registry


def _goal_tasks_file(blocks: list[str]) -> str:
    return "# Tasks\n\n## Invalidates\n\n- None.\n\n" + "\n\n".join(blocks) + "\n"


def _goal_task_block(
    task_id: str = "1.1",
    title: str = "Deliver one bounded behavior",
    checked: bool = False,
    acceptance: tuple[str, ...] = ("Observable result is proven by M1.",),
    strategy: str | None = "evidence-first",
    filled: bool = False,
    blocker: str = "none",
    redgreen: bool = False,
) -> str:
    box = "x" if checked else " "
    lines = [
        "- [%s] %s %s" % (box, task_id, title),
        "  - Owner: keel-agent",
        "  - Mode: implementation",
        "  - Covers:",
        "    - E1: single-task goal",
        "  - Read:",
        "    - README.md",
        "  - Touch:",
        "    - src/feature.js",
    ]
    if strategy:
        lines.append("  - Verification Strategy: %s" % strategy)
        if strategy == "evidence-first":
            lines.append("  - Verification Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first")
    lines.append("  - Commands:")
    lines.append("    - M1: node test.js")
    lines.append("  - Acceptance:")
    for item in acceptance:
        lines.append("    - %s" % item)
    lines.extend(
        [
            "  - Autonomy boundary:",
            "    - Default: hard-stop",
            "  - Coupling: none",
            "  - Candidate Boundary:",
            "    - one candidate",
            "  - Stop Rules:",
            "    - stop on failure",
            "  - Evidence:",
            "    - Contract: pending",
        ]
    )
    if filled:
        lines.append("    - M1: node test.js passed with the expected output")
        if redgreen:
            lines.append("    - M1.red: the failing behavior fixture was reproduced exit 1")
            lines.append("    - M1.green: the behavior fixture passed exit 0")
        lines.extend(
            [
                "    - Review:",
                "      - Status: pass",
                "      - Acceptance check: acceptance demonstrated by M1",
                "      - Scope check: only src/feature.js changed within Touch",
                "      - Findings: none",
                "    - Blocker: %s" % blocker,
            ]
        )
    else:
        lines.extend(
            [
                "    - M1: pending",
                "    - Review:",
                "      - Status: pending",
                "      - Acceptance check: pending",
                "      - Scope check: pending",
                "      - Findings: pending",
                "    - Blocker: %s" % blocker,
            ]
        )
    lines.extend(
        [
            "  - Stop if:",
            "    - scope exceeds Touch",
            "  - Report:",
            "    - Summary",
        ]
    )
    return "\n".join(lines)


def validate_runner_skip_accounting_scenario() -> int:
    """Issue #10: the suite could not pass anywhere the native CLIs are absent.

    Two of seventy scenarios probe native runtimes and used to `return 1` when
    the CLI was missing, so no CI runner could ever go green. A skip must be
    reported and counted, never conflated with a pass or a failure.
    """
    label = "runner-skip-accounting"
    runner = str(ROOT / "scripts/validate_plugin.py")

    def run_registry(results: str) -> subprocess.CompletedProcess[str]:
        """Drive run_all over synthetic scenario results in a child process.

        run_all dispatches each scenario as its own subprocess, which reads the
        real registry from disk, so a substituted registry would be ignored.
        The accounting is the behavior under test, so the process fan-out is
        replaced with fixed (name, code, output) triples instead.
        """
        program = (
            "import sys\n"
            f"src = open({runner!r}, encoding='utf-8').read()\n"
            "ns = {'__name__': 'v', '__file__': %r}\n" % runner
            + "exec(compile(src, %r, 'exec'), ns)\n" % runner
            + f"results = {results}\n"
            "ns['SCENARIOS'] = tuple((n, None) for n, _, _ in results)\n"
            "ns['run_baseline'] = lambda: 0\n"
            "ns['run_scenario_processes'] = lambda names, jobs: results\n"
            "sys.exit(ns['run_all'](2))\n"
        )
        return subprocess.run(
            [sys.executable, "-c", program],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(ROOT),
        )

    # A skipping scenario must not fail the run, must be named, and must be
    # excluded from the verified count; a failing one must still fail it.
    both = run_registry(
        "[('fake-skip', 3, 'fake-skip scenario skipped: the frob CLI\\n'),"
        " ('fake-pass', 0, 'fake-pass scenario passed.\\n')]"
    )
    out = (both.stdout or "") + (both.stderr or "")
    if both.returncode != 0:
        report(f"{label}: a skipping scenario must not fail the run.")
        report(out.strip())
        return 1
    for needle in ("fake-skip", "skipped", "the frob CLI", "plus 1 scenario"):
        if needle not in out:
            report(f"{label}: the summary must report {needle!r}; got:\n{out.strip()}")
            return 1
    if "fake-pass" in out.split("passed:")[-1]:
        report(f"{label}: a passing scenario must not be listed as skipped.")
        report(out.strip())
        return 1

    mixed = run_registry(
        "[('fake-skip', 3, 'fake-skip scenario skipped: the frob CLI\\n'),"
        " ('fake-fail', 1, 'fake-fail scenario failed.\\n')]"
    )
    mixed_out = (mixed.stdout or "") + (mixed.stderr or "")
    if mixed.returncode == 0 or "failed for: fake-fail" not in mixed_out:
        report(
            f"{label}: a skip beside a failure must still fail the run and name "
            "the failure."
        )
        report(mixed_out.strip())
        return 1
    if "fake-skip" in mixed_out.split("failed for:")[-1]:
        report(f"{label}: a skipped scenario must not be named as a failure.")
        report(mixed_out.strip())
        return 1

    # The two real native-runtime scenarios must take the skip path, not fail,
    # when their CLI cannot be resolved.
    for name in ("native-plugin-marketplaces", "native-plugin-install-matrix"):
        blinded = subprocess.run(
            [sys.executable, runner, "--scenario", name],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(ROOT),
            env={**os.environ, "PATH": str(ROOT), "PATHEXT": ""},
        )
        blinded_out = (blinded.stdout or "") + (blinded.stderr or "")
        if blinded.returncode != 3 or "skipped" not in blinded_out:
            report(
                f"{label}: {name} must exit 3 with a reported skip when its CLI "
                f"cannot be resolved; got {blinded.returncode}."
            )
            report(blinded_out.strip())
            return 1
        if "codex" not in blinded_out:
            report(f"{label}: {name}'s skip does not name the runtime it needed.")
            report(blinded_out.strip())
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_self_checks_read_every_module_scenario() -> int:
    """Issue #409: a check that reads the runner's code reads every module of it.

    After the split, a scan that still read `scripts/*.py` alone would pass
    over every scenario that moved into `scripts/validation/` and report
    nothing, which reads exactly like having nothing to report.
    """
    label = "self-checks-read-every-module:"
    baseline = importlib.import_module("validation.baseline")
    with tempfile.TemporaryDirectory(prefix="keel-409-self-checks-") as raw:
        scratch = Path(raw)
        write_text(scratch / "scripts/validate_plugin.py", (ROOT / "scripts/validate_plugin.py").read_text(encoding="utf-8"))
        write_text(scratch / "scripts/validation/__init__.py", "")
        write_text(
            scratch / "scripts/validation/planted.py",
            "from validation.common import ROOT, run_keel\n"
            "import requests\n\n\n"
            "def validate_planted_scenario() -> int:\n"
            "    run_keel(ROOT, \"--install\", \"--target\", \"claude\")\n"
            "    return 0\n",
        )
        saved = baseline.ROOT
        baseline.ROOT = scratch
        try:
            path_errors: list[str] = []
            baseline.validate_paths(path_errors)
            import_errors: list[str] = []
            baseline.validate_scripts_use_stdlib(import_errors)
        finally:
            baseline.ROOT = saved

    planted = [e for e in path_errors if "scripts/validation/planted.py" in e]
    if not any("scripts/validation/planted.py:6:" in e and "mutating Keel command" in e for e in planted):
        report(f"{label} the path scan did not report the planted `run_keel(ROOT, \"--install\")` by module and line: {planted!r}")
        return 1
    planted = [e for e in import_errors if "scripts/validation/planted.py" in e]
    if not any("requests" in e for e in planted):
        report(f"{label} the standard-library check did not report the planted `import requests`: {import_errors!r}")
        return 1
    if any("validation" in e.split("modules:")[-1] for e in planted):
        report(f"{label} the standard-library check refused the runner's own `validation` package: {planted!r}")
        return 1

    # The unregistered-scenario check reads modules, not one namespace.
    module = types.ModuleType("validation.planted")

    def validate_planted_scenario() -> int:
        return 0

    validate_planted_scenario.__module__ = module.__name__
    module.validate_planted_scenario = validate_planted_scenario
    orphans = unregistered_scenario_functions([module], registry.SCENARIOS)
    if orphans != ["validation.planted.validate_planted_scenario"]:
        report(f"{label} the unregistered-scenario check did not name the planted scenario: {orphans!r}")
        return 1

    if "self-checks-read-every-module" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report("self-checks-read-every-module scenario passed.")
    return 0


def validate_runner_runs_one_group_scenario() -> int:
    """Issue #409: one module's scenarios run alone, with the full run's accounting.

    Driven like runner-skip-accounting: the entry point's source runs with a
    registry of synthetic scenarios from two modules and a stubbed process
    runner, so the selection, its order, and the summary are what is tested.
    """
    label = "runner-runs-one-group:"
    runner = str(ROOT / "scripts/validate_plugin.py")

    def run_group(results: str) -> subprocess.CompletedProcess[str]:
        program = (
            "import sys\n"
            f"src = open({runner!r}, encoding='utf-8').read()\n"
            "ns = {'__name__': 'v', '__file__': %r}\n" % runner
            + "exec(compile(src, %r, 'exec'), ns)\n" % runner
            + f"results = dict((n, (c, o)) for n, c, o in {results})\n"
            "def make(name, module):\n"
            "    def scenario():\n"
            "        return 0\n"
            "    scenario.__module__ = module\n"
            "    return (name, scenario)\n"
            "ns['SCENARIOS'] = (make('a-one', 'validation.alpha'), make('b-one', 'validation.beta'),\n"
            "                   make('a-two', 'validation.alpha'), make('a-three', 'validation.alpha'))\n"
            "def baseline():\n"
            "    raise SystemExit('the baseline ran')\n"
            "ns['run_baseline'] = baseline\n"
            "def processes(names, jobs):\n"
            "    print('handed: ' + ','.join(names))\n"
            "    return [(n, *results[n]) for n in names]\n"
            "ns['run_scenario_processes'] = processes\n"
            f"sys.argv = [{runner!r}, '--group', 'alpha', '--jobs', '2']\n"
            "sys.exit(ns['main']())\n"
        )
        return subprocess.run(
            [sys.executable, "-c", program],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(ROOT),
        )

    passing = run_group(
        "[('a-one', 0, 'a-one scenario passed.\\n'),"
        " ('a-two', 3, 'a-two scenario skipped: the frob CLI\\n'),"
        " ('a-three', 0, 'a-three scenario passed.\\n')]"
    )
    out = (passing.stdout or "") + (passing.stderr or "")
    if "handed: a-one,a-two,a-three" not in out:
        report(f"{label} --group alpha did not hand the runner exactly alpha's scenarios in registry order: {out!r}")
        return 1
    if "the baseline ran" in out:
        report(f"{label} --group ran the baseline: {out!r}")
        return 1
    if passing.returncode != 0:
        report(f"{label} a passing group exited {passing.returncode}: {out!r}")
        return 1
    if "validation --group alpha passed: 2 scenarios, 1 skipped: a-two" not in out:
        report(f"{label} the group's summary does not name the group, its verified count, and its skip: {out!r}")
        return 1

    failing = run_group(
        "[('a-one', 0, 'a-one scenario passed.\\n'),"
        " ('a-two', 1, 'a-two scenario failed.\\n'),"
        " ('a-three', 0, 'a-three scenario passed.\\n')]"
    )
    out = (failing.stdout or "") + (failing.stderr or "")
    if failing.returncode != 1:
        report(f"{label} a group with a failure exited {failing.returncode}, not 1: {out!r}")
        return 1
    if "validation --group alpha failed for: a-two" not in out:
        report(f"{label} a group with a failure does not name it: {out!r}")
        return 1

    unknown = subprocess.run(
        [sys.executable, runner, "--group", "no-such-group"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT),
    )
    out = (unknown.stdout or "") + (unknown.stderr or "")
    if unknown.returncode != 2:
        report(f"{label} an unknown group exited {unknown.returncode}, not 2: {out!r}")
        return 1
    for group in ("contract", "selfcheck"):
        if group not in out:
            report(f"{label} an unknown group's message does not name the group {group!r}: {out!r}")
            return 1

    if "runner-runs-one-group" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report("runner-runs-one-group scenario passed.")
    return 0


def validate_resident_topic_matching_scenario() -> int:
    """Issue #15 item 1: required entries were named topics, matched as prose.

    The bootstrap is under a line and byte budget, so its wording gets rewritten
    to fit — and every rewrite of a pinned sentence failed the check that was
    supposed to prove only that the topic was still covered.
    """
    label = "resident-topic-matching"
    source = (ROOT / "assets/bootstrap/AGENTS.md").read_text(encoding="utf-8")
    original = "Touch bounds product writes; the change's own dir is exempt."
    if original not in source:
        report(
            f"{label}: the fixture's anchor sentence is not in the bootstrap; "
            "update this scenario alongside the wording."
        )
        return 1

    def errors_for(text: str) -> list[str]:
        with tempfile.TemporaryDirectory(prefix="keel-resident-topic-") as raw:
            root = Path(raw)
            write_text(root / "assets/bootstrap/AGENTS.md", text)
            found: list[str] = []
            validate_resident_blocks(found, root)
            return found

    def touch_errors(text: str) -> list[str]:
        return [item for item in errors_for(text) if "Touch" in item or "bound" in item]

    baseline = errors_for(source)
    if baseline:
        report(f"{label}: the unmodified bootstrap must pass: {baseline}")
        return 1

    # A rewording that keeps both concepts in one statement must pass.
    reworded = source.replace(
        original, "Touch bounds product writes, not the task's own records;"
    )
    if touch_errors(reworded):
        report(
            f"{label}: a rewording that keeps the topic was rejected: "
            f"{touch_errors(reworded)}"
        )
        return 1

    # Deleting the statement must still fail.
    deleted = source.replace(original, "")
    if not touch_errors(deleted):
        report(f"{label}: deleting the boundary statement did not fail the check.")
        return 1

    # Mentioning only one of the topic's words must not satisfy it.
    partial = source.replace(original, "Touch the files you declared;")
    if not touch_errors(partial):
        report(
            f"{label}: a statement mentioning only Touch, with no boundary "
            "concept, satisfied the topic."
        )
        return 1

    # A renamed command must still fail, and be reported as a literal.
    renamed = source.replace("keel context", "keel status")
    literal_errors = [item for item in errors_for(renamed) if "keel context" in item]
    if not literal_errors:
        report(f"{label}: renaming a required command did not fail the check.")
        return 1
    if not any("literal" in item for item in literal_errors):
        report(
            f"{label}: a missing command must be reported as a missing literal, "
            f"distinguishably from a missing topic: {literal_errors}"
        )
        return 1
    if any("literal" in item for item in touch_errors(deleted)):
        report(
            f"{label}: a missing topic must not be reported as a missing "
            f"literal: {touch_errors(deleted)}"
        )
        return 1

    if (ROOT / "assets/bootstrap/AGENTS.md").read_text(encoding="utf-8") != source:
        report(f"{label}: the shipped bootstrap was left modified.")
        return 1
    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


# The one-message-many-failures shape, counted rather than forbidden.
#
# Issue #43 records it caught by `keel-review-checklist` in three consecutive
# changes, every time in this file: `if <the run did not work> or <the output
# lacks a specific thing>:` followed by one `report(...)` describing only the
# second operand. When the first fires the sentence is false, and it sends the
# reader to a place with no problem in it.
#
# This number bounds a SHAPE. It is not a count of defects: many of the sites
# it counts carry a message that genuinely covers every operand, and deciding
# whether a particular sentence misleads needs a model, so that judgment stays
# in `keel-review-checklist`. What the number does is make a *new* one visible
# when it is written, which is earlier than a review that only runs at a
# completion gate.
#
# A pass/fail lint was the obvious form and is unshippable: the shape was
# already present at this many sites when the count was introduced, and
# rewriting them all in the file every other correctness claim rests on is a
# large blind diff. A recorded count fails when the number rises and lists what
# it measured; it also fails when the number falls without this constant being
# lowered, because a number that only checks for rises becomes false the first
# time someone fixes a site — and a false number is what this whole change is
# about. Fixing sites is expected. Lowering this constant is one line.
#
# Raised 75 -> 80 by `change-verify-deferred-evidence` (issue #95): five sites,
# each `payload.get("status") != "fail" or "<code>" not in codes(payload)`
# guarding one `report(...)`, the same already-accepted gate-result-assertion
# shape as `regression-check-tag`'s own site above. The message covers both
# operands (the gate did not fail the way the fixture requires, whichever half
# was wrong), and every site prints the full problem payload alongside it, so
# a reader is never left with only the sentence.
OR_GUARDED_ASSERTION_SITES = 74


def or_guarded_assertion_sites(source: str) -> list[int]:
    """Line numbers of `if` statements where one message covers several failures.

    The counted shape, stated so the next reader can restate it exactly: a body
    of one or more `report(...)` calls followed by exactly one `return`, under
    an `or` test with at least one membership operand (`in` / `not in`) and at
    least one operand that is not.

    A heuristic rule keyed on `returncode`, `is None`, `len(` and
    `.get("status")` was measured first and found 68 sites against this rule's
    75; the simple one is used because a rule nobody can reproduce produces a
    number nobody can check.
    """

    def is_report_return(body: list) -> bool:
        reports = [
            node for node in body
            if isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "report"
        ]
        if not reports:
            return False
        returns = [node for node in body if isinstance(node, ast.Return)]
        if len(returns) != 1:
            return False
        return len(body) == len(reports) + len(returns)

    def is_membership(node) -> bool:
        if not isinstance(node, ast.Compare):
            return False
        return any(isinstance(op, (ast.In, ast.NotIn)) for op in node.ops)

    sites = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.If):
            continue
        if not is_report_return(node.body):
            continue
        test = node.test
        if not isinstance(test, ast.BoolOp):
            continue
        if not isinstance(test.op, ast.Or):
            continue
        operands = test.values
        if not any(is_membership(item) for item in operands):
            continue
        if all(is_membership(item) for item in operands):
            continue
        sites.append(node.lineno)
    return sorted(sites)


def assertion_site_drift(measured: list[int], recorded: int) -> str:
    """Empty when the measured sites match the recorded count.

    Both directions fail, and they fail differently, because they call for
    opposite actions: a rise means split the assertion you just wrote, and a
    fall means lower the constant.
    """
    if len(measured) > recorded:
        return (
            f"{len(measured)} assertion sites guard several distinct failures "
            f"behind one message, but {recorded} are recorded. One condition "
            "reporting two failures names the wrong cause whenever the other "
            "one fires. Split the `if` you just added so each failure carries "
            "its own message, or — if the message genuinely covers every "
            "operand — raise OR_GUARDED_ASSERTION_SITES and say why. This "
            "number bounds a shape and is not a count of defects. Measured at "
            f"lines: {', '.join(str(line) for line in measured)}."
        )
    if len(measured) < recorded:
        return (
            f"{recorded} assertion sites are recorded but only {len(measured)} "
            "are present, so the recorded number is stale. Lower "
            f"OR_GUARDED_ASSERTION_SITES to {len(measured)}. The count fails in "
            "this direction too because a number that only checks for rises "
            "stops being true the first time a site is fixed."
        )
    return ""


# Synthetic sources for the counter. They are strings rather than fixtures on
# disk because the rule is about syntax, and a fixture file would itself be
# counted when the suite measures this file's siblings.
COUNTED_ASSERTION_SOURCE = '''
def probe():
    if result.returncode != 0 or "Usage:" not in result.stdout:
        report("no Usage: line")
        return 1
    return 0
'''


SPLIT_ASSERTION_SOURCE = '''
def probe():
    if result.returncode != 0:
        report("the command failed to run")
        return 1
    if "Usage:" not in result.stdout:
        report("no Usage: line")
        return 1
    return 0
'''


ALL_MEMBERSHIP_ASSERTION_SOURCE = '''
def probe():
    if "alpha" not in text or "beta" not in text:
        report("the output names neither alpha nor beta")
        return 1
    return 0
'''


NO_REPORT_ASSERTION_SOURCE = '''
def probe():
    if result.returncode != 0 or "Usage:" not in result.stdout:
        cleanup()
        return 1
    return 0
'''


def validate_assertion_shape_count_scenario() -> int:
    """Issue #43: one condition guarding two failures, caught three times.

    `keel-review-checklist` catches it, but only at a completion gate and only
    because a human wrote a checklist entry pointing the model at it. This
    counts the shape so a new one is visible when it is written.
    """
    # M1 — the counter finds the shape, and stops finding it once it is split.
    counted = or_guarded_assertion_sites(COUNTED_ASSERTION_SOURCE)
    if counted != [3]:
        report(
            "assertion-shape-count: M1 the counter did not report the single "
            f"counted site at line 3 of the synthetic source; got {counted}."
        )
        return 1
    split = or_guarded_assertion_sites(SPLIT_ASSERTION_SOURCE)
    if split:
        report(
            "assertion-shape-count: M1 splitting the assertion so each failure "
            f"carries its own message must clear it; got {split}."
        )
        return 1

    # M2 — the two shapes that are deliberately not counted.
    all_membership = or_guarded_assertion_sites(ALL_MEMBERSHIP_ASSERTION_SOURCE)
    if all_membership:
        report(
            "assertion-shape-count: M2 an `or` whose operands are all "
            "membership tests is one claim about one subject and is not "
            f"counted; got {all_membership}."
        )
        return 1
    no_report = or_guarded_assertion_sites(NO_REPORT_ASSERTION_SOURCE)
    if no_report:
        report(
            "assertion-shape-count: M2 an `if` whose body is not a report "
            f"followed by a single return is not an assertion site; got "
            f"{no_report}."
        )
        return 1

    # M3 — the comparison fails in both directions, differently.
    risen = assertion_site_drift([10, 20, 30], 2)
    if not risen:
        report(
            "assertion-shape-count: M3 a measured count above the recorded one "
            "produced no failure."
        )
        return 1
    if "30" not in risen:
        report(
            "assertion-shape-count: M3 the rise must list the measured line "
            f"numbers so the added site can be located. Got: {risen}"
        )
        return 1
    fallen = assertion_site_drift([10], 2)
    if not fallen:
        report(
            "assertion-shape-count: M3 a measured count below the recorded one "
            "produced no failure, so the recorded number could go stale "
            "silently."
        )
        return 1
    if fallen == risen:
        report(
            "assertion-shape-count: M3 a rise and a fall call for opposite "
            "actions and must not share a message."
        )
        return 1
    if "stale" not in fallen:
        report(
            f"assertion-shape-count: M3 the fall must say the recorded number "
            f"is stale and name the new one. Got: {fallen}"
        )
        return 1
    if assertion_site_drift([10, 20], 2):
        report(
            "assertion-shape-count: M3 a measured count equal to the recorded "
            "one must pass."
        )
        return 1

    # M4 — the real files, and this scenario's own assertions. Every module of
    # the runner is counted and each site is named as file:line (#409).
    measured = []
    for path in validation_sources():
        relative = path.relative_to(ROOT).as_posix()
        measured.extend(
            f"{relative}:{line}"
            for line in or_guarded_assertion_sites(path.read_text(encoding="utf-8"))
        )
    drift = assertion_site_drift(measured, OR_GUARDED_ASSERTION_SITES)
    if drift:
        report(f"assertion-shape-count: M4 {drift}")
        return 1
    own_path, source, own_start = validation_source_with("def validate_assertion_shape_count_scenario")
    own_first_line = source[:own_start].count("\n") + 1
    own_end = own_start + source[own_start:].index("\n\n\ndef ")
    own_last_line = source[:own_end].count("\n") + 1
    own_relative = own_path.relative_to(ROOT).as_posix()
    inside = [
        site for site in measured
        if site.rsplit(":", 1)[0] == own_relative
        and own_first_line <= int(site.rsplit(":", 1)[1]) <= own_last_line
    ]
    if inside:
        report(
            "assertion-shape-count: M4 this scenario's own assertions are of "
            f"the shape it counts, at lines {inside}."
        )
        return 1

    # M5 — the wording says what the number is.
    if "bounds a shape and is not a count of defects" not in risen:
        report(
            "assertion-shape-count: M5 the failure must state that the count "
            f"bounds a shape rather than asserting each site is wrong. Got: "
            f"{risen}"
        )
        return 1

    if "assertion-shape-count" not in {name for name, _ in registry.SCENARIOS}:
        report("assertion-shape-count: the scenario registry does not include it.")
        return 1
    report(
        f"assertion-shape-count scenario passed: {len(measured)} sites, "
        "a bound on a shape and not a count of defects."
    )
    return 0


def unregistered_scenario_functions(modules, scenarios) -> list[str]:
    """Every `validate_*_scenario` function a module defines that the registry does not list.

    Read per module, since the scenarios live in several (#409); a function
    another module only imports is counted where it is defined.
    """
    registered = {(func.__module__, func.__name__) for _, func in scenarios}
    return sorted(
        f"{module.__name__}.{obj_name}"
        for module in modules
        for obj_name, obj in vars(module).items()
        if callable(obj)
        and obj_name.startswith("validate_")
        and obj_name.endswith("_scenario")
        and getattr(obj, "__module__", None) == module.__name__
        and (module.__name__, obj_name) not in registered
    )


def validation_modules() -> list:
    return [
        importlib.import_module(f"validation.{path.stem}")
        for path in validation_sources()
        if path.parent.name == "validation" and path.stem != "__init__"
    ]


def validate_validation_runner_scenario() -> int:
    if not getattr(registry, "SCENARIOS", None):
        report("validation-runner: the scenario registry is missing.")
        return 1
    names = [name for name, _ in registry.SCENARIOS]
    if len(names) != len(set(names)):
        report("validation-runner: registry names are not unique.")
        return 1
    orphans = unregistered_scenario_functions(validation_modules(), registry.SCENARIOS)
    if orphans:
        report(
            "validation-runner: scenario functions missing from the registry: "
            + ", ".join(orphans)
        )
        return 1

    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    test_script = package.get("scripts", {}).get("test", "")
    if (
        "--all" not in test_script
        or "--scenario" in test_script
        or "&&" in test_script
    ):
        report(
            "validation-runner: package.json test must be a single --all "
            "invocation, not a per-scenario chain."
        )
        return 1
    for name in ("README.md", "README.zh-CN.md"):
        readme = (ROOT / name).read_text(encoding="utf-8")
        if "--all" not in readme or "--jobs" not in readme:
            report(f"validation-runner: {name} does not document the parallel runner.")
            return 1

    # The full gate must actually run somewhere other than one author's machine:
    # a workflow drives the same single entry point on push and pull request,
    # and the release workflow keeps its own tag guard rather than becoming the
    # suite's only runner.
    workflow_path = ROOT / ".github/workflows/test.yml"
    if not workflow_path.is_file():
        report(
            "validation-runner: no .github/workflows/test.yml, so the full gate "
            "runs only in the local pre-push hook."
        )
        return 1
    workflow = workflow_path.read_text(encoding="utf-8")
    for needle in ("npm test", "npm ci", "pull_request", "push:", "ubuntu-latest"):
        if needle not in workflow:
            report(
                "validation-runner: the full-gate workflow does not declare "
                f"{needle!r}."
            )
            report(workflow)
            return 1
    publish = (ROOT / ".github/workflows/publish.yml").read_text(encoding="utf-8")
    if "does not match package.json version" not in publish:
        report(
            "validation-runner: the release workflow lost its tag/version guard."
        )
        return 1

    # Behavioral: the parallel machinery preserves registry order, keeps a
    # passing scenario's buffered output, and fails loudly on a bad entry.
    ordered = run_scenario_processes(
        ["version-alignment", "definitely-not-a-scenario"], 2
    )
    if [entry[0] for entry in ordered] != [
        "version-alignment",
        "definitely-not-a-scenario",
    ]:
        report("validation-runner: results are not returned in registry order.")
        return 1
    _, ok_code, ok_output = ordered[0]
    _, bad_code, bad_output = ordered[1]
    if ok_code != 0 or "version-alignment scenario passed" not in ok_output:
        report("validation-runner: parallel run lost a passing scenario's output.")
        return 1
    if bad_code == 0 or "unknown validation scenario" not in bad_output:
        report("validation-runner: an unknown scenario did not fail loudly.")
        return 1

    report("validation-runner scenario passed.")
    return 0


# `process.exit()` discards whatever Node has not flushed, and stdout to a pipe
# is asynchronous. Whether anything is lost depends only on whether the payload
# fit the pipe buffer — so at the 64KB default nothing is ever lost, and under
# the memory pressure that shrinks buffers to a page or two, output is lost
# silently. Waiting for that condition is not a test; this scenario creates it.
def validate_output_survives_the_pipe_scenario() -> int:
    label = "output-survives-the-pipe"
    F_SETPIPE_SZ = 1031
    try:
        import fcntl
        import time
    except ImportError:
        return skip_scenario(
            label,
            "fcntl is unavailable, so the pipe buffer cannot be shrunk and the "
            "truncation cannot be forced rather than waited for",
        )

    def goal_task(acceptance_padding: int) -> str:
        huge = ("Acceptance " + ("A" * acceptance_padding) + " is proven by M1.",)
        return _goal_tasks_file(
            [_goal_task_block(acceptance=huge, strategy="vertical-tdd")]
        )

    # A task-start result carries the whole compiled capsule, so a long
    # Acceptance makes it larger than the shrunken pipe. (It was `keel project
    # goal` until that command was removed in 5.173.0, #414.)
    goal_args = (
        "gate", "task-start",
        "--change", "sample-change", "--task", "1.1", "--json", "--no-guard",
    )

    with tempfile.TemporaryDirectory(prefix="keel-pipe-") as raw:
        root = Path(raw)
        repo = root / "repo"
        write_text(repo / "openspec/changes/sample-change/proposal.md", "# P\n")
        write_text(
            repo / "openspec/changes/sample-change/design.md",
            "## Context\n\nfixture\n",
        )
        write_text(
            repo / "openspec/changes/sample-change/specs/demo/spec.md",
            "## ADDED Requirements\n",
        )
        write_text(
            repo / "openspec/changes/sample-change/tasks.md", goal_task(4200)
        )

        # The reference length: the same invocation with nowhere to lose bytes.
        redirected = run_keel(repo, *goal_args)
        if redirected.returncode != 0:
            report(
                f"{label}: the fixture did not produce a task-start result to "
                f"measure against; keel exited {redirected.returncode}."
            )
            report((redirected.stderr or redirected.stdout).strip()[:400])
            return 1
        expected = redirected.stdout.encode("utf-8")
        if len(expected) <= 4096:
            report(
                f"{label}: the fixture projection is {len(expected)} bytes, "
                "which fits the shrunken pipe, so the condition this scenario "
                "exists to force would not arise."
            )
            return 1

        read_fd, write_fd = os.pipe()
        try:
            fcntl.fcntl(write_fd, F_SETPIPE_SZ, 4096)
        except OSError as error:
            os.close(read_fd)
            os.close(write_fd)
            return skip_scenario(
                label,
                "this platform refused F_SETPIPE_SZ "
                f"({error}), so the pipe buffer cannot be shrunk",
            )

        child = subprocess.Popen(
            ["node", str(ROOT / "bin" / "keel.js"), *goal_args],
            cwd=repo,
            stdout=write_fd,
            stderr=subprocess.DEVNULL,
        )
        os.close(write_fd)
        # Nothing is read for a moment, so the buffer fills and the rest of the
        # write is left pending. A child that discards its pending write on exit
        # is finished by now, having lost everything past the buffer; a child
        # that lets the event loop drain is blocked on the write and finishes
        # once the loop below starts reading. Reading immediately would drain
        # fast enough to let the broken form through, which is the race this
        # scenario exists to remove — so the pause is the forcing condition, and
        # the child is waited for after the read rather than before it.
        time.sleep(1.0)
        received = b""
        while True:
            chunk = os.read(read_fd, 65536)
            if not chunk:
                break
            received += chunk
        os.close(read_fd)
        child.wait(timeout=60)

        if received != expected:
            report(
                f"{label}: {len(received)} of {len(expected)} bytes survived a "
                "4096-byte pipe. Output written for a program to read is being "
                "discarded at process exit, with no error and no exit-code "
                "change — the consumer receives a valid prefix of an "
                "incomplete document."
            )
            return 1
        try:
            json.loads(received.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            report(f"{label}: the payload that survived does not parse: {error}.")
            return 1

        # D3: the one behavioral difference a reader would worry about.
        ok = run_keel(repo, "--version")
        if ok.returncode != 0:
            report(f"{label}: a successful command returned {ok.returncode}.")
            return 1
        refused = run_keel(
            repo, "gate", "task-start", "--change", "no-such-change", "--task", "1.1"
        )
        if refused.returncode != 1:
            report(
                f"{label}: a refused gate returned {refused.returncode}, not 1."
            )
            return 1
        invalid = run_keel(repo, "--not-a-flag")
        if invalid.returncode != 2:
            report(
                f"{label}: an invalid argument returned {invalid.returncode}, "
                "not 2."
            )
            return 1

    report(f"{label} scenario passed.")
    return 0


# A scenario name, as the registry spells one. Two registered names carry no
# hyphen — `cli` and `uninstall` — so requiring one would leave exactly those
# two unchecked, and allowing single words was measured to add no false
# positive.
AUTHORED_SCENARIO_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


# The two forms a scenario reference is read in. `--scenario` is the invocation
# itself and needs no context. The other is keyed on the *assertion* rather than
# on the token, because kebab-case is this project's spelling for gate stages,
# diagnostic codes, skills, capabilities, and hook events too: reading every
# such token as a scenario name flags 22 of the 55 in the archive. Keying on
# "stays green" flags one, and that one is a real unregistered name.
AUTHORED_SCENARIO_FLAG = re.compile(r"--scenario\s+`?([A-Za-z0-9][\w.-]*)`?")


AUTHORED_SCENARIO_STAYS_GREEN = re.compile(r"stays? green", re.IGNORECASE)


AUTHORED_CHECK_LINE = re.compile(r"^-\s*M\d+\b")


AUTHORED_VERIFY_BLOCK = re.compile(r"^-\s*(?:Verify|Commands):\s*$")


AUTHORED_CAPSULE_BLOCK = re.compile(r"^-\s*[A-Z][A-Za-z ]*:\s*$")


AUTHORED_INLINE_CODE = re.compile(r"`([^`\n]+)`")


AUTHORED_SCENARIO_FORMS = (
    "A scenario reference is read in two forms: a name after `--scenario`, and "
    "a backticked lowercase token in a `Verify` M<n> check asserting that "
    "something stays green. Other backticked vocabulary in a check is not read "
    "as a scenario name."
)


def unregistered_scenario_references(
    text: str, registered: set[str]
) -> list[tuple[int, str, str]]:
    """Scenario names a task contract declares that the registry does not hold.

    Returns `(line, name, form)` for each, 1-indexed, in file order. The `form`
    is which of the two recognized shapes matched, so a report can say why the
    token was read as a scenario name at all.
    """
    problems: list[tuple[int, str, str]] = []
    in_verify = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        # A capsule block heading ends the previous block, so `Evidence` and
        # `Stop Rules` leave the Verify block rather than extending it. Evidence
        # is written after the run, when execution has already answered the
        # question this check exists to answer earlier.
        if AUTHORED_CAPSULE_BLOCK.match(stripped):
            in_verify = bool(AUTHORED_VERIFY_BLOCK.match(stripped))
        for match in AUTHORED_SCENARIO_FLAG.finditer(line):
            name = match.group(1)
            if name not in registered:
                problems.append((line_number, name, "--scenario"))
        if not in_verify or not AUTHORED_CHECK_LINE.match(stripped):
            continue
        if not AUTHORED_SCENARIO_STAYS_GREEN.search(line):
            continue
        for token in AUTHORED_INLINE_CODE.findall(line):
            if not AUTHORED_SCENARIO_NAME.match(token):
                continue
            if token not in registered:
                problems.append((line_number, token, "stays green"))
    return problems


def active_change_tasks(repo: Path) -> list[Path]:
    """Every active change's tasks.md. Archived changes are deliberately absent.

    An archived task records what was true when it ran; a scenario renamed
    afterwards does not make that record wrong, and turning history red for it
    tells a reader nothing they can act on.
    """
    changes = repo / "openspec" / "changes"
    archive = changes / "archive"
    # The walk finds archived changes and the filter is what drops them, rather
    # than a glob depth that happens not to reach them. A depth that excludes by
    # accident passes every test aimed at the exclusion, including one aimed at
    # it on purpose.
    return sorted(
        path for path in changes.rglob("tasks.md") if archive not in path.parents
    )


def validate_authored_scenario_names_scenario() -> int:
    """Issue #51: a check whose scenario name is not registered cannot run.

    Three of the four authored contracts #51 records named something that did
    not exist, two of them scenario names, both written as an `M5 (regression)`
    check asserting that named scenarios stay green, and both found only when
    the check was executed. A fifth, unrecorded there, is
    `2026-08-01-the-name-is-not-the-thing/tasks.md:132`, which declares
    `tasks-template-validates` — a name `git log -S` finds at no commit — and
    records that check as passing.

    The assertions live on synthetic content with a known name set, because the
    live scan reads whatever the working tree holds and is normally empty: a
    change is archived when it closes. The temp-repository half is the positive
    control for the whole path, so a run that passes because the file selection
    silently found nothing is distinguishable from one that verified something.
    """
    registered = {name for name, _ in registry.SCENARIOS}
    known = {"core-gates", "cli"}
    authored = (
        "# Tasks\n"
        "\n"
        "- [ ] 1.1 Do the thing\n"
        "  - Touch:\n"
        "    - src/thing.js\n"
        "  - Verify:\n"
        "    - Strategy: vertical-tdd\n"
        "    - M1: `node scripts/run_python.js scripts/validate_plugin.py "
        "--scenario gate-diagnostics` passes\n"
        "    - M2 (regression): `core-gates` and `target-surface-doctor` stay "
        "green\n"
        "    - M3 (regression): `task-start`, `keel-review-checklist`, "
        "`contract-drift`, `subagent-stop`, and `keel-task-capsule` are "
        "unchanged\n"
        "    - M4: `cli` and "
        "`node scripts/run_python.js scripts/validate_plugin.py "
        "--scenario core-gates` stay green\n"
        "  - Evidence:\n"
        "    - M2: `target-surface-doctor` stays green\n"
    )
    found = unregistered_scenario_references(authored, known)
    expected = [
        (8, "gate-diagnostics", "--scenario"),
        (9, "target-surface-doctor", "stays green"),
    ]
    if found != expected:
        report(
            "authored-scenario-names-are-registered: the recognized forms did "
            f"not report what they must. expected {expected}, found {found}."
        )
        report(AUTHORED_SCENARIO_FORMS)
        return 1

    # Which files are read is a separate question from what is read out of
    # them, and it is the half that can silently resolve to nothing. The
    # planted reference is the positive control for the whole path: an
    # extractor that stopped reporting, or a selection that stopped finding,
    # both fail here rather than passing on an empty scan.
    with tempfile.TemporaryDirectory(prefix="keel-authored-names-") as raw:
        repo = Path(raw)
        write_text(repo / "openspec/changes/live/tasks.md", authored)
        write_text(repo / "openspec/changes/archive/old/tasks.md", authored)
        selected = active_change_tasks(repo)
        if selected != [repo / "openspec/changes/live/tasks.md"]:
            report(
                "authored-scenario-names-are-registered: the active change "
                "selection is wrong. An archived tasks.md must not be scanned "
                "and an active one must be. "
                f"selected {[str(path) for path in selected]}."
            )
            return 1
        control = [
            (path, unregistered_scenario_references(
                path.read_text(encoding="utf-8"), known
            ))
            for path in selected
        ]
        if [problems for _, problems in control] != [expected]:
            report(
                "authored-scenario-names-are-registered: a planted reference "
                "in an active change was not reported end to end, so a clean "
                "run over the real tree would prove nothing. "
                f"found {control}."
            )
            return 1

    for path in active_change_tasks(ROOT):
        problems = unregistered_scenario_references(
            path.read_text(encoding="utf-8"), registered
        )
        if not problems:
            continue
        relative = path.relative_to(ROOT).as_posix()
        for line_number, name, form in problems:
            report(
                f"authored-scenario-names-are-registered: {relative}:"
                f"{line_number} names `{name}` after {form}, and no scenario by "
                "that name is registered, so the check that names it cannot run."
            )
        report(AUTHORED_SCENARIO_FORMS)
        return 1

    if "authored-scenario-names-are-registered" not in {
        name for name, _ in registry.SCENARIOS
    }:
        report(
            "authored-scenario-names-are-registered: the scenario registry "
            "does not include it."
        )
        return 1
    report("authored-scenario-names-are-registered scenario passed.")
    return 0


def validate_the_routing_rule_reaches_the_decision_scenario() -> int:
    """Issue #131: routing is the one durable rule with nowhere to reach the agent.

    The block `keel --init` installs is five bullets and says nothing about Full
    or Lite; routing has no implementation at all, only four lines of prose in
    Keel's own README. So the first decision of every session is taken without
    the rule, and a project whose risk does not track diff size has no way to say
    so. The declaration is one-directional on purpose: it can raise the process
    floor and there is no key that lowers it.
    """
    label = "the-routing-rule-reaches-the-decision"
    declared = "results/experiments.jsonl"
    reason = "append-only; a one-field diff is not revertible"

    with tempfile.TemporaryDirectory(prefix="keel-routing-") as raw:
        root = Path(raw)

        def fixture(name: str, body: str | None) -> Path:
            repo = root / name
            repo.mkdir()
            if body is not None:
                (repo / "keel").mkdir()
                (repo / "keel" / "config.yaml").write_text(body, encoding="utf-8")
            return repo

        def context(repo: Path) -> str:
            return run_keel(repo, "context").stdout

        # M1 — a declared path is reported with the reason it carries, and the
        # projection is otherwise the one it would have printed anyway.
        plain = fixture("plain", "fast_check: echo plain\n")
        declaring = fixture(
            "declaring",
            f"fast_check: echo plain\nfull_mode_paths:\n  - {declared}: {reason}\n",
        )
        out = context(declaring)
        if declared not in out:
            report(
                f"{label}: no routing line — a repository that declared "
                f"{declared!r} is told nothing about it at the one moment the "
                "routing decision is made."
            )
            report(out)
            return 1
        if reason not in out:
            report(
                f"{label}: the declared path is reported without its reason, so "
                "the agent learns the file is special and not what makes it so."
            )
            report(out)
            return 1
        # D5 — the fixture creates no file at that path, on purpose.
        if (declaring / declared).exists():
            report(f"{label}: the fixture created the declared path; D5 is untested.")
            return 1
        baseline = [
            line
            for line in context(plain).splitlines()
            if line.startswith(("Keel context:", "Next action:"))
        ]
        moved = [
            line
            for line in out.splitlines()
            if line.startswith(("Keel context:", "Next action:"))
        ]
        if baseline != moved:
            report(
                f"{label}: the declaration moved the projection's status or next "
                f"action; {baseline!r} became {moved!r}."
            )
            return 1

        # M2 — an entry with no reason is not a declaration.
        bare = fixture(
            "bare", f"full_mode_paths:\n  - {declared}\n"
        )
        out = context(bare)
        # Behavior before message: what D2 forbids is the entry counting as a
        # declaration, and whether it is also reported well comes after that.
        routing_lines = [
            line for line in out.splitlines() if line.startswith("Routing:")
        ]
        if any(declared in line for line in routing_lines):
            report(
                f"{label}: the reason-less entry was read as a declaration; "
                f"{routing_lines!r}"
            )
            return 1
        if "full_mode_paths" not in out or declared not in out:
            report(
                f"{label}: an entry with no reason was dropped silently; the "
                "author is left believing they declared what they typed."
            )
            report(out)
            return 1
        if "<path>: <reason>" not in out:
            report(
                f"{label}: the refusal does not name the form the entry needs."
            )
            report(out)
            return 1

        # 1.2 — a declaration Keel cannot fully read raises the floor rather
        # than dropping it. `authorize:` and `triage:` fail closed and closed
        # means *less proceeds without a human*; for a declaration whose purpose
        # is to add process, the same principle is more Full mode, not less.
        mixed = fixture(
            "mixed",
            f"full_mode_paths:\n  - {declared}: {reason}\n  - src/lib.js\n",
        )
        out = context(mixed)
        routing_lines = [
            line for line in out.splitlines() if line.startswith("Routing:")
        ]
        if not any("every change" in line.lower() for line in routing_lines):
            report(
                f"{label}: routes only the entries it could read — a "
                "declaration Keel half-read was treated as the policy, so a "
                "typo silently lowers the process floor. {0!r}".format(
                    routing_lines
                )
            )
            report(out)
            return 1
        if any(declared in line for line in routing_lines):
            report(
                f"{label}: the readable entry was reported as the declared set "
                "beside an unreadable one, so half a declaration acted as a "
                f"whole one; {routing_lines!r}"
            )
            return 1
        if "src/lib.js" not in out:
            report(f"{label}: the unreadable entry is not named, so the state is not attributable.")
            report(out)
            return 1
        doctor = run_keel(mixed, "--doctor").stdout
        if "full_mode_paths: failed" not in doctor or "src/lib.js" not in doctor:
            report(
                f"{label}: the doctor does not report the declaration as failed "
                "and name the entry, so it reports health the projection "
                "contradicts."
            )
            report(doctor)
            return 1
        # The conservative branch is reached by an unreadable declaration, not
        # by any declaration at all.
        if "every change" in context(declaring).lower():
            report(
                f"{label}: a readable declaration reported the "
                "everything-routes-Full state."
            )
            return 1

        # M3 — the common case pays nothing.
        for name, body in (
            ("absent", None),
            ("blockless", "fast_check: echo blockless\n"),
            ("empty", "fast_check: echo empty\nfull_mode_paths:\n"),
        ):
            repo = fixture(name, body)
            out = context(repo)
            if "Routing:" in out or "full_mode_paths" in out:
                report(
                    f"{label}: the {name} repository was told about a routing "
                    "declaration it does not have."
                )
                report(out)
                return 1

    # 1.3 — the rule itself, in the artifact `keel --init` installs. Asserted on
    # the shipped block rather than on a fixture: this is the file a consuming
    # repository receives, and its two budgets are what keep it resident.
    bootstrap_path = ROOT / "assets/bootstrap/AGENTS.md"
    bootstrap = bootstrap_path.read_text(encoding="utf-8")
    for needle, why in (
        ("Full", "the block must name the complete flow"),
        ("Lite", "the block must name the local flow"),
        ("100 lines", "the block must carry the size heuristic it is correcting"),
        ("full_mode_paths", "the block must say a project can declare exceptions"),
    ):
        if needle not in bootstrap:
            report(
                f"{label}: bootstrap states no routing rule — {why}; "
                f"{needle!r} is absent. Routing is the first decision of a "
                "session and the block a consuming repository receives is "
                "where it has to arrive."
            )
            return 1
    # Both budgets. The line one runs the check the suite enforces rather than
    # counting here; the byte one is asserted at its raised value.
    budget_errors: list[str] = []
    validate_resident_blocks(budget_errors)
    if budget_errors:
        report(f"{label}: the routing line broke the resident block line budget.")
        for error in budget_errors:
            report(f"- {error}")
        return 1
    body = bootstrap.split("<!-- keel:start", 1)[1].split("<!-- keel:end -->", 1)[0]
    block_bytes = len(("<!-- keel:start" + body + "<!-- keel:end -->").encode())
    if block_bytes >= BOOTSTRAP_BLOCK_BYTE_BUDGET:
        report(
            f"{label}: the block is {block_bytes} bytes, over its "
            f"{BOOTSTRAP_BLOCK_BYTE_BUDGET}-byte budget."
        )
        return 1

    # The raise is only authorized because it is loud: a larger constant with no
    # argument beside it is exactly the quiet drift the cap was built to stop,
    # and it would pass every check above. So both assertions of the cap must
    # carry the reason it moved, not just the number.
    for marker in ("thin-native-install bootstrap block", "over its"):
        if validation_source_with(marker) is None:
            report(f"{label}: the byte-cap assertion {marker!r} is gone.")
            return 1
    # The rationale for a constant lives in the comment block above it, so that
    # is where it is read from — walking back over the contiguous comment lines
    # rather than guessing a window — in whichever module defines it (#409).
    defined = validation_source_with("\nBOOTSTRAP_BLOCK_BYTE_BUDGET =")
    if defined is None:
        report(f"{label}: no validation module defines BOOTSTRAP_BLOCK_BYTE_BUDGET.")
        return 1
    lines = defined[1].splitlines()
    at = next(
        i for i, line in enumerate(lines)
        if line.startswith("BOOTSTRAP_BLOCK_BYTE_BUDGET =")
    )
    top = at
    while top > 0 and lines[top - 1].startswith("#"):
        top -= 1
    rationale = "\n".join(lines[top:at + 1])
    for needle in ("routing", "not quietly"):
        if needle not in rationale:
            report(
                f"{label}: names the new cap without the reason it moved; "
                f"{needle!r} is absent from the constant's own rationale. A "
                "reader inheriting a larger number and no argument is the drift "
                "the cap exists to prevent."
            )
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0

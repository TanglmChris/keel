#!/usr/bin/env python3
"""Validate the Keel v4.1.0 package baseline."""

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

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from validation.common import (
    ROOT,
    SKIPPED,
    report,
    run_scenario_processes,
    validate_openspec_schema,
    validate_resident_blocks,
    validate_skill_docs,
    validate_skill_portability,
)
from validation.baseline import (
    validate_archive_overlay_hygiene,
    validate_install_honesty,
    validate_manifest,
    validate_npm_package,
    validate_openspec_invocable,
    validate_paths,
    validate_review_status_single_source,
    validate_scripts_use_stdlib,
    validate_templates,
)
from validation.registry import SCENARIOS
from validation import evidence


def run_baseline() -> int:
    errors: list[str] = []
    validate_manifest(errors)
    validate_npm_package(errors)
    validate_paths(errors)
    validate_resident_blocks(errors)
    validate_templates(errors)
    validate_openspec_schema(errors)
    validate_review_status_single_source(errors)
    validate_install_honesty(errors)
    validate_openspec_invocable(errors)
    validate_archive_overlay_hygiene(errors)
    validate_skill_docs(errors)
    validate_skill_portability(ROOT, errors)
    validate_scripts_use_stdlib(errors)

    if errors:
        report("Keel v4.1.0 baseline validation failed:")
        for error in errors:
            report(f"- {error}")
        return 1

    report("Keel v4.1.0 baseline validation passed.")
    return 0


def run_all(jobs: int) -> int:
    # Fail-loud, not fail-fast: baseline and every registered scenario run to
    # completion, buffered output is replayed in registry order, and every
    # failure is named in one summary.
    failures = []
    skipped = []
    if run_baseline() != 0:
        failures.append("baseline")
    ordered = run_scenario_processes([name for name, _ in SCENARIOS], jobs)
    for name, code, output in ordered:
        sys.stdout.write(output)
        if code == SKIPPED:
            skipped.append(name)
        elif code != 0:
            failures.append(name)
    if failures:
        report(f"validation --all failed for: {', '.join(failures)}")
        return 1
    # The verified count excludes skips, so the number that lands in evidence is
    # the number actually run, and every skip is named with the run.
    verified = len(SCENARIOS) - len(skipped)
    summary = (
        f"validation --all passed: baseline plus {verified} "
        f"scenario{'' if verified == 1 else 's'}"
    )
    if skipped:
        summary += f", {len(skipped)} skipped: {', '.join(skipped)}"
    report(f"{summary}.")
    report(evidence.evidence_line(evidence.classify(SCENARIOS), {name for name, _ in SCENARIOS} - set(skipped)))
    return 0


def run_group(group: str, jobs: int) -> int:
    """Run one module's registered scenarios, accounted as --all accounts them (#409).

    The group is the module under scripts/validation/ that defines the scenario
    function. The baseline is not part of any group.
    """
    module = f"validation.{group}"
    names = [name for name, func in SCENARIOS if func.__module__ == module]
    if not names:
        groups = sorted({func.__module__.split(".")[-1] for _, func in SCENARIOS})
        report(f"unknown validation group: {group}; the groups are {', '.join(groups)}")
        return 2
    failures = []
    skipped = []
    for name, code, output in run_scenario_processes(names, jobs):
        sys.stdout.write(output)
        if code == SKIPPED:
            skipped.append(name)
        elif code != 0:
            failures.append(name)
    if failures:
        report(f"validation --group {group} failed for: {', '.join(failures)}")
        return 1
    verified = len(names) - len(skipped)
    summary = (
        f"validation --group {group} passed: {verified} "
        f"scenario{'' if verified == 1 else 's'}"
    )
    if skipped:
        summary += f", {len(skipped)} skipped: {', '.join(skipped)}"
    report(f"{summary}.")
    report(evidence.evidence_line(evidence.classify(SCENARIOS), set(names) - set(skipped)))
    return 0


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--scenario":
        registry = dict(SCENARIOS)
        runner = registry.get(sys.argv[2])
        if runner is None:
            report(f"unknown validation scenario: {sys.argv[2]}")
            return 2
        return runner()

    if len(sys.argv) >= 2 and sys.argv[1] == "--all":
        jobs = os.cpu_count() or 2
        rest = sys.argv[2:]
        if rest and rest[0] == "--jobs" and len(rest) == 2 and rest[1].isdigit():
            jobs = int(rest[1])
        elif rest:
            report(f"usage: validate_plugin.py --all [--jobs N], got: {' '.join(rest)}")
            return 2
        return run_all(jobs)

    if len(sys.argv) >= 3 and sys.argv[1] == "--group":
        jobs = os.cpu_count() or 2
        rest = sys.argv[3:]
        if rest and rest[0] == "--jobs" and len(rest) == 2 and rest[1].isdigit():
            jobs = int(rest[1])
        elif rest:
            report(f"usage: validate_plugin.py --group NAME [--jobs N], got: {' '.join(rest)}")
            return 2
        return run_group(sys.argv[2], jobs)

    if sys.argv[1:2] == ["--evidence"]:
        rest = sys.argv[2:]
        if rest not in ([], ["--markdown"]):
            report(f"usage: validate_plugin.py --evidence [--markdown], got: {' '.join(rest)}")
            return 2
        classes = evidence.classify(SCENARIOS)
        print(evidence.render_markdown(classes) if rest else evidence.render(classes))
        return 0

    return run_baseline()


if __name__ == "__main__":
    sys.exit(main())

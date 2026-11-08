"""Keel validation: change-close and a declared skip of specs (#517)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from validation.common import report, run_keel, write_text


def closing_codes(repo: Path, env: dict[str, str], action: str) -> list[str] | None:
    result = run_keel(repo, "gate", "change-close", "--change", "demo", "--action", action, "--json", env=env)
    try:
        return [p.get("code") for p in json.loads(result.stdout).get("problems", [])]
    except json.JSONDecodeError:
        report(f"change-close-skip-specs: change-close printed no JSON: {result.stdout!r} {result.stderr!r}")
        return None


def validate_change_close_skip_specs_scenario() -> int:
    label = "change-close-skip-specs:"
    with tempfile.TemporaryDirectory(prefix="keel-skip-specs-") as raw:
        tmp = Path(raw).resolve()
        repo = tmp / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
        env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE", "KEEL_"))}
        env["CODEX_HOME"] = str(tmp / "codex-home")
        init = run_keel(repo, "--init", "--target", "claude", env=env)
        if init.returncode != 0:
            report(f"{label} init failed: {init.stderr or init.stdout}")
            return 1
        change = repo / "openspec/changes/demo"
        write_text(change / "proposal.md", "## Why\n\nfixture\n\n## What Changes\n\n- fixture\n")
        write_text(change / "tasks.md", "# Tasks\n\n- [x] 1.1 done\n")
        marker = change / ".openspec.yaml"

        def codes(action: str = "archive") -> list[str]:
            found = closing_codes(repo, env, action)
            return [] if found is None else found

        write_text(marker, "schema: keel-spec-driven\nskip_specs: true\n")
        for action in ("archive", "sync"):
            marked = codes(action)
            if "missing-delta-spec" in marked:
                report(f"{label} a marked change without specs still gets missing-delta-spec for {action}: {marked}")
                return 1
            if "skip-specs-with-specs" in marked:
                report(f"{label} a marked change without specs gets skip-specs-with-specs for {action}: {marked}")
                return 1

        write_text(change / "specs/demo/spec.md", "## ADDED Requirements\n")
        both = closing_codes(repo, env, "archive") or []
        if "skip-specs-with-specs" not in both:
            report(f"{label} a marker beside a spec file is not reported: {both}")
            return 1
        if "missing-delta-spec" in both:
            report(f"{label} a marker beside a spec file also reports missing-delta-spec: {both}")
            return 1
        gate = run_keel(repo, "gate", "change-close", "--change", "demo", "--action", "archive", "--json", env=env)
        if "specs/demo/spec.md" not in gate.stdout.replace("\\\\", "/"):
            report(f"{label} the contradiction does not name the file: {gate.stdout[:400]!r}")
            return 1
        shutil.rmtree(change / "specs")

        for text, why in (
            ("schema: keel-spec-driven\n", "no marker"),
            ("schema: keel-spec-driven\nskip_specs: false\n", "skip_specs: false"),
        ):
            write_text(marker, text)
            unmarked = codes()
            if "missing-delta-spec" not in unmarked:
                report(f"{label} with {why} the delta spec is no longer required: {unmarked}")
                return 1
        marker.unlink()
        marker.mkdir()
        unreadable = codes()
        if "missing-delta-spec" not in unreadable:
            report(f"{label} with an unreadable .openspec.yaml the delta spec is no longer required: {unreadable}")
            return 1
    report("change-close-skip-specs scenario passed.")
    return 0

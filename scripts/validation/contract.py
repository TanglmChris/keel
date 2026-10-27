"""Keel validation: contract (split from validate_plugin.py, #409)."""
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
    OPENSPEC_SCHEMA_NAME,
    OPENSPEC_SEARCH_ORDER,
    OPENSPEC_SURFACE_OVERLAY_START,
    PACKAGE_VERSION,
    PLUGIN_ROOT,
    ROOT,
    mailbox_repository,
    path_without_openspec,
    report,
    resident_session_start_section,
    run_keel,
    run_openspec,
    snapshot_files,
    task_capsule_compact_fixture,
    task_contract_fixture,
    tracker_owner_tasks,
    write_authorize_config,
    write_gate_fixture,
    write_text,
)
from validation import registry


def validate_expectation_slice_gates_scenario() -> int:
    protocol_snippets = [
        "Expectation alignment",
        "Expectation -> Slice -> Evidence",
        "Critical expectations",
        "Task Authoring Gate",
        "Slice Start Gate",
        "source expectations",
        "rough future slices",
    ]
    schema_snippets = [
        "Covers",
        "Task Authoring Gate",
        "Slice Start Gate",
        "source expectations",
        "Rough future slices",
        "cannot be selected for implementation or marked complete",
        "D<n>",
        "F<n>",
        "A<n>",
        "Q<n>",
        "basis",
        "resolution gate or durable owner",
    ]
    task_template_snippets = [
        "Covers:",
        "source expectation",
        "D<n>/F<n>/A<n>/Q<n>",
        # The rule is no longer "an unresolved Q<n> requires a fallback"
        # unconditionally: the identifier blocks only where it opens the entry,
        # so a resolved question can be cited beside the fact that closed it.
        "OPENS an entry",
        "requires an authorized fallback",
    ]
    design_template_snippets = [
        "D<n>",
        "F<n>",
        "A<n>",
        "Q<n>",
        "Basis",
        "Resolve by",
        "authorized fallback",
    ]
    overlay_snippets = [
        "Task Authoring Gate",
        "Slice Start Gate",
        "source expectations",
        "Rough future slices",
    ]

    checks: list[tuple[str, Path, list[str]]] = [
        ("root AGENTS.md", ROOT / "AGENTS.md", protocol_snippets),
        (
            "source keel-spec-driven schema",
            ROOT / "assets/openspec/schemas/keel-spec-driven/schema.yaml",
            schema_snippets,
        ),
        (
            "repo keel-spec-driven schema",
            ROOT / "openspec/schemas/keel-spec-driven/schema.yaml",
            schema_snippets,
        ),
        (
            "dist keel-spec-driven schema",
            ROOT / "assets/openspec/schemas/keel-spec-driven/schema.yaml",
            schema_snippets,
        ),
        (
            "source tasks template",
            ROOT / "assets/openspec/schemas/keel-spec-driven/templates/tasks.md",
            task_template_snippets,
        ),
        (
            "source design template",
            ROOT / "assets/openspec/schemas/keel-spec-driven/templates/design.md",
            design_template_snippets,
        ),
        (
            "repo design template",
            ROOT / "openspec/schemas/keel-spec-driven/templates/design.md",
            design_template_snippets,
        ),
        (
            "dist design template",
            ROOT / "assets/openspec/schemas/keel-spec-driven/templates/design.md",
            design_template_snippets,
        ),
        (
            "repo tasks template",
            ROOT / "openspec/schemas/keel-spec-driven/templates/tasks.md",
            task_template_snippets,
        ),
        (
            "dist tasks template",
            ROOT / "assets/openspec/schemas/keel-spec-driven/templates/tasks.md",
            task_template_snippets,
        ),
        ("OpenSpec apply overlay generator", ROOT / "bin/keel.js", overlay_snippets),
    ]

    for label, path, snippets in checks:
        if not path.is_file():
            report(f"expectation-slice-gates scenario missing {label}: {path}")
            return 1
        content = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in content:
                report(
                    f"expectation-slice-gates scenario {label} "
                    f"missing required text: {snippet}"
                )
                return 1

    with tempfile.TemporaryDirectory(prefix="keel-covers-") as raw_tmp:
        repo = Path(raw_tmp)
        write_text(
            repo / "openspec/changes/demo/specs/demo-capability/spec.md",
            "## ADDED Requirements\n\n"
            "### Requirement: Public behavior\n"
            "Keel MUST expose the public behavior.\n\n"
            "#### Scenario: Behavior succeeds\n"
            "- **WHEN** the public command runs\n"
            "- **THEN** the public output is ready\n"
            "- **AND THEN** source provenance remains visible\n",
        )
        scenario_task = task_capsule_compact_fixture().replace(
            "E1: Public behavior passes.",
            "demo-capability / Public behavior / Behavior succeeds",
        )
        write_text(repo / "openspec/changes/demo/tasks.md", scenario_task)
        resolved = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if resolved.returncode != 0:
            report("expectation-slice-gates rejected a unique scenario reference.")
            report((resolved.stderr or resolved.stdout).strip())
            return 1
        capsule = json.loads(resolved.stdout).get("contract", {}).get("capsule", {})
        authority = capsule.get("authority", [])
        if (
            len(authority) != 1
            or authority[0].get("kind") != "scenario"
            or not authority[0].get("source", "").endswith(
                "specs/demo-capability/spec.md#Scenario:Behavior succeeds"
            )
            or capsule.get("acceptance")
            != [
                "the public output is ready",
                "source provenance remains visible",
            ]
        ):
            report("expectation-slice-gates did not derive scenario provenance.")
            report(resolved.stdout.strip())
            return 1

        write_text(
            repo / "openspec/changes/demo/design.md",
            "## Decisions\n\n"
            "D1 — Keep one shared parser. Basis: fixture authority.\n\n"
            "## Hidden Knowledge / Assumptions\n\n"
            "A1 — Scenario headings are unique. Basis: fixture authority. "
            "Resolve by: task-start.\n",
        )
        critical_task = scenario_task.replace(
            "    - demo-capability / Public behavior / Behavior succeeds\n",
            "    - D1, A1\n"
            "    - demo-capability / Public behavior / Behavior succeeds\n",
        )
        write_text(repo / "openspec/changes/demo/tasks.md", critical_task)
        critical = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if critical.returncode != 0:
            report("expectation-slice-gates rejected critical design references.")
            report((critical.stderr or critical.stdout).strip())
            return 1
        critical_authority = (
            json.loads(critical.stdout)
            .get("contract", {})
            .get("capsule", {})
            .get("authority", [])
        )
        if (
            [item.get("reference") for item in critical_authority]
            != ["A1", "D1", "demo-capability / Public behavior / Behavior succeeds"]
            or any(
                item.get("kind") != "critical-statement"
                or not item.get("source", "").endswith(
                    f"design.md#{item.get('reference')}"
                )
                for item in critical_authority[:2]
            )
        ):
            report("expectation-slice-gates did not resolve critical statements.")
            report(critical.stdout.strip())
            return 1

        duplicate_task = scenario_task.replace(
            "    - demo-capability / Public behavior / Behavior succeeds\n",
            "    - demo-capability / Public behavior / Behavior succeeds\n"
            "    - demo-capability / Public behavior / Behavior succeeds\n",
        )
        write_text(repo / "openspec/changes/demo/tasks.md", duplicate_task)
        duplicate = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        duplicate_payload = json.loads(duplicate.stdout)
        if (
            duplicate.returncode != 3
            or not any(
                item.get("code") == "duplicate-covers"
                for item in duplicate_payload.get("problems", [])
            )
        ):
            report("expectation-slice-gates silently deduplicated Covers.")
            report((duplicate.stderr or duplicate.stdout).strip())
            return 1

        missing_task = scenario_task.replace(
            "Behavior succeeds",
            "Missing behavior",
        )
        write_text(repo / "openspec/changes/demo/tasks.md", missing_task)
        missing = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if (
            missing.returncode != 3
            or not any(
                item.get("code") == "unresolved-covers"
                for item in json.loads(missing.stdout).get("problems", [])
            )
        ):
            report("expectation-slice-gates accepted a missing scenario.")
            report((missing.stderr or missing.stdout).strip())
            return 1

        spec_path = repo / "openspec/changes/demo/specs/demo-capability/spec.md"
        write_text(
            spec_path,
            spec_path.read_text(encoding="utf-8")
            + "\n#### Scenario: Behavior succeeds\n"
            "- **WHEN** a duplicate scenario runs\n"
            "- **THEN** duplicate output appears\n",
        )
        write_text(repo / "openspec/changes/demo/tasks.md", scenario_task)
        ambiguous = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if (
            ambiguous.returncode != 3
            or not any(
                item.get("code") == "ambiguous-covers"
                for item in json.loads(ambiguous.stdout).get("problems", [])
            )
        ):
            report("expectation-slice-gates accepted a duplicated scenario.")
            report((ambiguous.stderr or ambiguous.stdout).strip())
            return 1

        write_text(
            repo / "openspec/changes/demo/design.md",
            "## Open Questions\n\n"
            "Q1 — Which implementation authority applies? Basis: fixture. "
            "Resolve by: user decision.\n",
        )
        question_task = task_capsule_compact_fixture().replace(
            "E1: Public behavior passes.",
            "Q1",
        )
        write_text(repo / "openspec/changes/demo/tasks.md", question_task)
        unauthorized = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if (
            unauthorized.returncode != 3
            or not any(
                item.get("code") == "unresolved-authority"
                for item in json.loads(unauthorized.stdout).get("problems", [])
            )
        ):
            report("expectation-slice-gates accepted unauthorized Q authority.")
            report((unauthorized.stderr or unauthorized.stdout).strip())
            return 1

    report("expectation-slice-gates scenario passed.")
    return 0


def validate_unparsed_covers_critical_statement_scenario() -> int:
    """Issue #49 item 1: a critical-statement Covers reference must be told apart
    as missing (the identifier never appears in design.md) from unparsed (the
    identifier appears but not in the exact resolvable shape), instead of both
    collapsing into the same "Missing" message.
    """
    task = task_capsule_compact_fixture().replace(
        "    - E1: Public behavior passes.\n",
        "    - D2\n",
    )

    def covers_message(repo: Path) -> tuple[int, str]:
        write_text(repo / "openspec/changes/demo/tasks.md", task)
        result = run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
        )
        problems = json.loads(result.stdout).get("problems", [])
        message = next(
            (
                item.get("message", "")
                for item in problems
                if item.get("code") == "unresolved-covers"
            ),
            "",
        )
        return result.returncode, message

    with tempfile.TemporaryDirectory(prefix="keel-unparsed-covers-missing-") as raw:
        repo = Path(raw)
        write_text(
            repo / "openspec/changes/demo/design.md",
            "## Decisions\n\nD1 — Unrelated decision. Basis: fixture authority.\n",
        )
        returncode, message = covers_message(repo)
        if returncode == 0 or not message.startswith(
            "Missing Covers critical statement: D2."
        ):
            report(
                "unparsed-covers-critical-statement: an identifier absent from "
                f"design.md must still report Missing, got: {message!r}"
            )
            return 1

    with tempfile.TemporaryDirectory(prefix="keel-unparsed-covers-unparsed-") as raw:
        repo = Path(raw)
        # A colon after the identifier stays outside the accepted shapes now
        # that bullet and bold wrapping resolve (issue #49, owner-decided).
        write_text(
            repo / "openspec/changes/demo/design.md",
            "## Decisions\n\n"
            "D2: Keep one shared parser. Basis: fixture authority.\n",
        )
        returncode, message = covers_message(repo)
        if returncode == 0:
            report(
                "unparsed-covers-critical-statement: a present-but-mis-shaped D2 "
                "must still fail task-start."
            )
            return 1
        if not message.startswith("Unparsed Covers critical statement: D2."):
            report(
                "unparsed-covers-critical-statement: a present-but-mis-shaped D2 "
                f"must report Unparsed, got: {message!r}"
            )
            return 1
        if "D2 — statement" not in message:
            report(
                "unparsed-covers-critical-statement: the Unparsed message must "
                f"name the required shape, got: {message!r}"
            )
            return 1

    with tempfile.TemporaryDirectory(prefix="keel-unparsed-covers-resolved-") as raw:
        repo = Path(raw)
        write_text(
            repo / "openspec/changes/demo/design.md",
            "## Decisions\n\nD2 — Keep one shared parser. Basis: fixture authority.\n",
        )
        write_text(repo / "openspec/changes/demo/tasks.md", task)
        result = run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
        )
        if result.returncode != 0:
            report(
                "unparsed-covers-critical-statement: a correctly-shaped D2 must "
                f"still resolve. {(result.stderr or result.stdout).strip()}"
            )
            return 1
        authority = (
            json.loads(result.stdout)
            .get("contract", {})
            .get("capsule", {})
            .get("authority", [])
        )
        if not any(
            item.get("reference") == "D2" and item.get("kind") == "critical-statement"
            for item in authority
        ):
            report(
                "unparsed-covers-critical-statement: correctly-shaped D2 did not "
                "resolve as critical-statement authority."
            )
            return 1

    if "unparsed-covers-critical-statement" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "unparsed-covers-critical-statement: the scenario registry does not "
            "include it."
        )
        return 1
    report("unparsed-covers-critical-statement scenario passed.")
    return 0


def validate_widened_critical_statement_shapes_scenario() -> int:
    """Issue #49 Section 1, owner-decided 2026-08-17: criticalAuthority() must
    resolve a design.md critical-statement line in the shapes authors actually
    write — bulleted, bold-wrapped, or both — not only the bare line shape,
    while a reference matching more than one line still fails as duplicated and
    a still-unaccepted shape reports Unparsed naming the accepted shapes.
    """
    task = task_capsule_compact_fixture().replace(
        "    - E1: Public behavior passes.\n",
        "    - D2\n",
    )

    def start(repo: Path) -> subprocess.CompletedProcess[str]:
        write_text(repo / "openspec/changes/demo/tasks.md", task)
        return run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
        )

    accepted_shapes = [
        "- D2 — Keep one shared parser.",
        "**D2** — Keep one shared parser.",
        "- **D2** — Keep one shared parser.",
        "* D2 — Keep one shared parser.",
        "+ D2 — Keep one shared parser.",
    ]
    for shape in accepted_shapes:
        with tempfile.TemporaryDirectory(prefix="keel-widened-shape-") as raw:
            repo = Path(raw)
            write_text(
                repo / "openspec/changes/demo/design.md",
                f"## Decisions\n\n{shape}\n",
            )
            result = start(repo)
            if result.returncode != 0:
                report(
                    f"widened-critical-statement-shapes: the shape {shape!r} "
                    f"must resolve, got exit {result.returncode}: "
                    f"{(result.stderr or result.stdout).strip()}"
                )
                return 1
            authority = (
                json.loads(result.stdout)
                .get("contract", {})
                .get("capsule", {})
                .get("authority", [])
            )
            if not any(
                item.get("reference") == "D2"
                and item.get("kind") == "critical-statement"
                and item.get("text") == "Keep one shared parser."
                for item in authority
            ):
                report(
                    f"widened-critical-statement-shapes: the shape {shape!r} "
                    "must resolve as critical-statement authority carrying the "
                    "statement text."
                )
                return 1

    with tempfile.TemporaryDirectory(prefix="keel-widened-duplicate-") as raw:
        repo = Path(raw)
        write_text(
            repo / "openspec/changes/demo/design.md",
            "## Decisions\n\nD2 — Keep one shared parser.\n\n"
            "- D2 — Keep one shared parser.\n",
        )
        result = start(repo)
        problems = json.loads(result.stdout).get("problems", [])
        if result.returncode == 0 or not any(
            item.get("code") == "ambiguous-covers"
            and item.get("message", "").startswith(
                "Duplicated Covers critical statement: D2."
            )
            for item in problems
        ):
            report(
                "widened-critical-statement-shapes: the same identifier in "
                "two accepted shapes must fail as duplicated."
            )
            return 1

    with tempfile.TemporaryDirectory(prefix="keel-widened-unparsed-") as raw:
        repo = Path(raw)
        write_text(
            repo / "openspec/changes/demo/design.md",
            "## Decisions\n\nD2: Keep one shared parser.\n",
        )
        result = start(repo)
        problems = json.loads(result.stdout).get("problems", [])
        message = next(
            (
                item.get("message", "")
                for item in problems
                if item.get("code") == "unresolved-covers"
            ),
            "",
        )
        if result.returncode == 0 or not message.startswith(
            "Unparsed Covers critical statement: D2."
        ):
            report(
                "widened-critical-statement-shapes: a colon line must still "
                f"report Unparsed, got: {message!r}"
            )
            return 1
        if "- D2 — " not in message or "**D2** — " not in message:
            report(
                "widened-critical-statement-shapes: the Unparsed message must "
                f"name the bulleted and bold shapes as accepted, got: {message!r}"
            )
            return 1

    if "widened-critical-statement-shapes" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "widened-critical-statement-shapes: the scenario registry does not "
            "include it."
        )
        return 1
    report("widened-critical-statement-shapes scenario passed.")
    return 0


def validate_whole_critical_statement_authority_scenario() -> int:
    """Issue #177: every owned line, but no sibling, binds cited authority."""
    task = task_capsule_compact_fixture().replace(
        "    - E1: Public behavior passes.\n", "    - D1\n"
    )
    base = (
        "## Decisions\n\n"
        "- D1 — Preserve semantics.\n"
        "  continuation alpha\n"
        "  - nested detail alpha\n\n"
        "- D2 — Peer decision.\n\n"
        "Independent paragraph.\n\n"
        "## Following heading\n"
    )

    with tempfile.TemporaryDirectory(prefix="keel-whole-critical-") as raw:
        repo = Path(raw)
        design_path = repo / "openspec/changes/demo/design.md"
        write_text(repo / "openspec/changes/demo/tasks.md", task)

        def start(design: str, *extra: str) -> tuple[int, dict]:
            write_text(design_path, design)
            result = run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
                *extra, "--json",
            )
            return result.returncode, json.loads(result.stdout)

        code, initial = start(base)
        if code != 0:
            report("whole-critical-statement-authority: accepted D1 did not compile.")
            report(str(initial))
            return 1
        authority = initial["contract"]["capsule"]["authority"]
        if authority[0]["text"] != (
            "Preserve semantics. continuation alpha - nested detail alpha"
        ):
            report(
                "whole-critical-statement-authority: the D1 authority omitted "
                f"an owned line: {authority[0]['text']!r}"
            )
            return 1
        fingerprint = initial["contract"]["fingerprint"]["value"]

        for old, new, label in (
            ("continuation alpha", "continuation beta", "continuation"),
            ("nested detail alpha", "nested detail beta", "nested bullet"),
        ):
            code, changed = start(base.replace(old, new))
            if code != 0:
                report(f"whole-critical-statement-authority: {label} edit failed to compile.")
                return 1
            if changed["contract"]["fingerprint"]["value"] == fingerprint:
                report(
                    f"whole-critical-statement-authority: {label} edit left "
                    "the cited contract fingerprint unchanged."
                )
                return 1

        for old, new, label in (
            ("Peer decision", "Changed peer", "peer bullet"),
            ("Independent paragraph", "Changed paragraph", "peer paragraph"),
            ("Following heading", "Changed heading", "heading"),
        ):
            code, changed = start(base.replace(old, new))
            if code != 0:
                report(f"whole-critical-statement-authority: {label} edit failed to compile.")
                return 1
            if changed["contract"]["fingerprint"]["value"] != fingerprint:
                report(
                    f"whole-critical-statement-authority: {label} edit "
                    "incorrectly changed D1 authority."
                )
                return 1

        # A `#` line nested inside the item is owned content (a code sample's
        # comment, a heading inside the list item), and an unindented line
        # with no blank before it continues the paragraph lazily. Neither may
        # cut the statement short; a blank-separated paragraph still ends it.
        for design, old, new, label in (
            (
                "## Decisions\n\n- D1 — Opener.\n  - detail one\n"
                "    # sample comment\n  - detail after hash\n",
                "detail after hash", "detail changed", "detail after a nested #",
            ),
            (
                "## Decisions\n\n- D1 — Opener wraps\nlazily onto this line.\n\n"
                "Separate paragraph.\n",
                "lazily onto", "lazily into", "lazy continuation",
            ),
        ):
            before_code, before = start(design)
            after_code, after = start(design.replace(old, new))
            if before_code != 0 or after_code != 0:
                report(f"whole-critical-statement-authority: {label} case failed to compile.")
                return 1
            if before["contract"]["fingerprint"]["value"] == after["contract"]["fingerprint"]["value"]:
                report(
                    f"whole-critical-statement-authority: {label} edit left "
                    "the cited contract fingerprint unchanged."
                )
                return 1
            if "Separate paragraph" not in design:
                continue
            _, peer = start(design.replace("Separate paragraph", "Changed paragraph"))
            if peer["contract"]["fingerprint"]["value"] != before["contract"]["fingerprint"]["value"]:
                report(
                    f"whole-critical-statement-authority: {label} case let a "
                    "blank-separated paragraph change D1 authority."
                )
                return 1

        # Consecutive unbulleted openers are one CommonMark paragraph, but
        # each is its own decision: a peer opener is never a lazy line.
        adjacent = "## Decisions\n\nD1 — First.\n**D2** — Second.\n"
        before_code, before = start(adjacent)
        after_code, after = start(adjacent.replace("Second", "Changed"))
        if before_code != 0 or after_code != 0:
            report("whole-critical-statement-authority: adjacent-opener case failed to compile.")
            return 1
        if before["contract"]["fingerprint"]["value"] != after["contract"]["fingerprint"]["value"]:
            report(
                "whole-critical-statement-authority: an adjacent unbulleted "
                "peer opener was absorbed into D1 authority."
            )
            return 1

        code, recorded = start(base, "--record", "--no-guard")
        if code != 0 or recorded.get("record", {}).get("status") != "recorded":
            report("whole-critical-statement-authority: could not record D1 anchor.")
            return 1
        write_text(design_path, base.replace("nested detail alpha", "nested detail beta"))
        completion = run_keel(
            repo, "gate", "task-complete", "--change", "demo", "--task", "1.1", "--json"
        )
        problems = json.loads(completion.stdout).get("problems", [])
        if not any(item.get("code") == "contract-drift" for item in problems):
            report(
                "whole-critical-statement-authority: task-complete missed "
                "drift after a nested detail changed."
            )
            report(completion.stdout.strip())
            return 1

        code, colon = start("## Decisions\n\n- D1: colon shape.\n")
        messages = [item.get("message", "") for item in colon.get("problems", [])]
        if code == 0 or not any(
            "Unparsed Covers critical statement: D1." in message
            and "D1 —" in message
            for message in messages
        ):
            report("whole-critical-statement-authority: colon shape lost its actionable refusal.")
            return 1

    if "whole-critical-statement-authority" not in {name for name, _ in registry.SCENARIOS}:
        report("whole-critical-statement-authority: scenario is not registered.")
        return 1
    report("whole-critical-statement-authority scenario passed.")
    return 0


def validate_unlinked_critical_covers_scenario() -> int:
    """Issue #177: critical citations must not silently become legacy prose."""
    design = (
        "## Decisions\n\n"
        "- D1 — First decision.\n"
        "- D2 — Second decision.\n"
    )
    with tempfile.TemporaryDirectory(prefix="keel-unlinked-critical-") as raw:
        repo = Path(raw)
        write_text(repo / "openspec/changes/demo/design.md", design)

        def start(covers: str) -> tuple[int, dict]:
            write_text(
                repo / "openspec/changes/demo/tasks.md",
                task_capsule_compact_fixture().replace(
                    "    - E1: Public behavior passes.\n", f"    - {covers}\n"
                ),
            )
            result = run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
            )
            return result.returncode, json.loads(result.stdout)

        for covers in (
            "D1、D2",
            "D1，D2",
            "D1 D2",
            "Implement both decisions（D1、D2）",
        ):
            code, payload = start(covers)
            messages = [item.get("message", "") for item in payload.get("problems", [])]
            if code == 0:
                report(f"unlinked-critical-covers: {covers!r} passed as unlinked prose.")
                return 1
            if not any(covers in message and "D1, D2" in message for message in messages):
                report(
                    f"unlinked-critical-covers: {covers!r} lacks a diagnostic "
                    "naming the entry and the supported list form."
                )
                report(str(messages))
                return 1

        for covers, expected in (
            ("D1", ["D1"]),
            ("D1, D2", ["D1", "D2"]),
            ("D1 — annotation", ["D1"]),
        ):
            code, payload = start(covers)
            if code != 0:
                report(f"unlinked-critical-covers: supported {covers!r} failed.")
                report(str(payload.get("problems", [])))
                return 1
            authority = payload["contract"]["capsule"]["authority"]
            actual = [item["reference"] for item in authority]
            if actual != expected or any(
                item["kind"] != "critical-statement" for item in authority
            ):
                report(
                    f"unlinked-critical-covers: supported {covers!r} lost "
                    f"linked authority: {authority!r}"
                )
                return 1

        for covers in (
            "F13 (Q1 resolved: the answer is recorded)",
            "D2: colon-form legacy description",
            "D2-compatible fixture text",
        ):
            code, payload = start(covers)
            if code != 0:
                report(f"unlinked-critical-covers: existing free text {covers!r} was rejected.")
                report(str(payload.get("problems", [])))
                return 1

    if "unlinked-critical-covers" not in {name for name, _ in registry.SCENARIOS}:
        report("unlinked-critical-covers: scenario is not registered.")
        return 1
    report("unlinked-critical-covers scenario passed.")
    return 0


def validate_record_derives_skeleton_scenario() -> int:
    """Issue #179: `--record` writes the record slots a capsule implies.

    Every slot it writes is a placeholder the gates still refuse as unfilled,
    so this changes who types the bookkeeping and not what completion needs.
    """
    label = "record-derives-skeleton:"
    fixture = task_capsule_compact_fixture()
    no_evidence = fixture.replace(
        "  - Evidence:\n    - Contract: pending\n    - M1: pending\n", ""
    )
    red_green = no_evidence.replace(
        "    - Strategy: evidence-first\n"
        "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "    - M1: node test.js\n",
        "    - Strategy: vertical-tdd\n"
        "    - M1: node test.js asserts the feature. Fails with: `boom`\n"
        "    - M2 (regression): node old.js stays green\n"
        "    - M3: node edge.js asserts the edge. Fails with: `edge` Detects: `drop the guard` -> `edge`\n",
    )
    if red_green == no_evidence:
        report(f"{label} the fixture's Verify block moved; update this scenario.")
        return 1
    expected_slots = [
        "    - M1: pending",
        "    - M1.red: pending",
        "    - M1.green: pending",
        "    - M2: pending",
        "    - M3: pending",
        "    - M3.red: pending",
        "    - M3.green: pending",
        "    - M3.detects: pending",
        "    - Review:",
        "      - Status: pending",
        "      - Acceptance check: pending",
        "      - Scope check: pending",
        "      - Findings: pending",
        "    - Blocker: none",
        "    - Reauthorizations: none",
    ]
    with tempfile.TemporaryDirectory(prefix="keel-skeleton-") as raw:
        repo = Path(raw)
        tasks = repo / "openspec/changes/demo/tasks.md"

        def record(*extra: str) -> tuple[int, dict]:
            result = run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
                *extra, "--json",
            )
            return result.returncode, json.loads(result.stdout)

        write_text(tasks, red_green)
        code, payload = record("--record", "--no-guard")
        if code != 0:
            report(f"{label} --record refused a valid task with no Evidence: {payload.get('problems')!r}")
            return 1
        if payload.get("record", {}).get("status") != "recorded":
            report(f"{label} the outcome was {payload.get('record')!r}, not recorded.")
            return 1
        fingerprint = payload["contract"]["fingerprint"]["value"]
        after = tasks.read_text(encoding="utf-8")
        before_lines, after_lines = red_green.splitlines(), after.splitlines()
        added = [line for line in after_lines if line not in before_lines]
        want = ["  - Evidence:", f"    - Contract: keel-task-capsule/v1 sha256:{fingerprint} (keel {PACKAGE_VERSION})", *expected_slots]
        if added != want:
            report(f"{label} --record added {added!r}, expected {want!r}.")
            return 1
        if [line for line in before_lines if line not in after_lines]:
            report(f"{label} --record removed or rewrote a line outside the Evidence it added.")
            return 1
        code, again = record("--record", "--no-guard")
        if code != 0 or tasks.read_text(encoding="utf-8") != after:
            report(f"{label} a second --record was not byte-identical.")
            return 1
        if again.get("record", {}).get("status") != "unchanged":
            report(f"{label} a second --record reported {again.get('record')!r}, not unchanged.")
            return 1
        completion = run_keel(repo, "gate", "task-complete", "--change", "demo", "--task", "1.1", "--json")
        if completion.returncode == 0:
            report(f"{label} task-complete accepted a task whose slots were only filled with pending.")
            return 1

        kept = red_green.replace(
            "  - Stop if:\n",
            "  - Evidence:\n    - M1: pass. node test.js printed ok.\n  - Stop if:\n",
        )
        write_text(tasks, kept)
        code, payload = record("--record", "--no-guard")
        text = tasks.read_text(encoding="utf-8")
        if code != 0:
            report(f"{label} --record refused a task with a partial Evidence block: {payload.get('problems')!r}")
            return 1
        if "    - M1: pass. node test.js printed ok." not in text:
            report(f"{label} --record rewrote an existing concrete M1 line.")
            return 1
        if "    - M1: pending" in text:
            report(f"{label} --record added a second M1 slot beside the kept one.")
            return 1
        if "    - M1.red: pending" not in text:
            report(f"{label} --record did not add the missing M1.red slot beside the kept M1.")
            return 1

        # Issue #236: added slots land in template order, not at the block's end.
        def evidence_lines(text: str) -> list[str]:
            lines = text.splitlines()
            start = lines.index("  - Evidence:") + 1
            end = next((i for i in range(start, len(lines)) if not lines[i].startswith("    ")), len(lines))
            return lines[start:end]

        logs_first = red_green.replace(
            "  - Stop if:\n",
            "  - Evidence:\n    - Contract: pending\n    - Blocker: none\n    - Reauthorizations: none\n  - Stop if:\n",
        )
        write_text(tasks, logs_first)
        code, payload = record("--record", "--no-guard")
        if code != 0:
            report(f"{label} --record refused a block holding Contract, Blocker and Reauthorizations: "
                   f"{payload.get('problems')!r}")
            return 1
        fingerprint = payload["contract"]["fingerprint"]["value"]
        got = evidence_lines(tasks.read_text(encoding="utf-8"))
        want = [f"    - Contract: keel-task-capsule/v1 sha256:{fingerprint} (keel {PACKAGE_VERSION})", *expected_slots]
        if got != want:
            report(f"{label} --record over Contract, Blocker and Reauthorizations left the block out of "
                   f"template order: {got!r}, expected {want!r}.")
            return 1
        before_review = red_green.replace(
            "  - Stop if:\n",
            "  - Evidence:\n    - M1: pass. node test.js printed ok.\n    - Review:\n      - Status: pending\n"
            "      - Acceptance check: pending\n      - Scope check: pending\n      - Findings: pending\n"
            "  - Stop if:\n",
        )
        write_text(tasks, before_review)
        code, payload = record("--record", "--no-guard")
        if code != 0:
            report(f"{label} --record refused a block holding M1 and Review: {payload.get('problems')!r}")
            return 1
        got = evidence_lines(tasks.read_text(encoding="utf-8"))
        at = got.index("    - M1: pass. node test.js printed ok.")
        if got[at + 1:at + 3] != ["    - M1.red: pending", "    - M1.green: pending"]:
            report(f"{label} --record did not place M1.red and M1.green directly after the kept M1: {got!r}")
            return 1

        write_text(tasks, no_evidence)
        code, payload = record("--record", "--no-guard")
        text = tasks.read_text(encoding="utf-8")
        if code != 0:
            report(f"{label} --record refused a valid evidence-first task: {payload.get('problems')!r}")
            return 1
        if ".red:" in text or ".green:" in text:
            report(f"{label} an evidence-first task was given .red/.green slots.")
            return 1

        broken = red_green.replace("    - Strategy: vertical-tdd\n", "")
        write_text(tasks, broken)
        code, payload = record("--record")
        if code == 0:
            report(f"{label} --record filled slots around a task with no Strategy.")
            return 1
        if tasks.read_text(encoding="utf-8") != broken:
            report(f"{label} a refused --record wrote to tasks.md.")
            return 1
        if (repo / "keel/guard.json").exists():
            report(f"{label} a refused --record wrote the guard manifest.")
            return 1

        write_text(tasks, fixture.replace("    - M1: pending\n", ""))
        code, payload = record()
        messages = [item.get("message", "") for item in payload.get("problems", [])]
        if code == 0:
            report(f"{label} task-start without --record accepted a missing M1 slot.")
            return 1
        if not any("--record" in message for message in messages):
            report(f"{label} the evidence-label-mismatch refusal does not name --record: {messages!r}")
            return 1

    if "record-derives-skeleton" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("record-derives-skeleton scenario passed.")
    return 0


def validate_review_checklist_defers_to_gate_scenario() -> int:
    """Issue #179: Review guidance keeps what no gate can judge, and only that.

    `task-complete` refuses a missing or drifted Contract anchor and missing
    `.red`/`.green` Evidence on its own, so asking the agent to confirm them
    again is reading cost without a criterion. What stays is the judgment.
    """
    label = "review-checklist-defers-to-gate:"
    for root in ("src/skills", f"{PLUGIN_ROOT}/skills"):
        text = (ROOT / root / "review-checklist" / "SKILL.md").read_text(encoding="utf-8")
        flat = " ".join(text.split())
        for restated in (
            "Evidence `Contract` line records the task-start capsule fingerprint",
            "confirm concrete per-label `.red` and `.green` Evidence exists",
        ):
            if restated in flat:
                report(f"{label} {root} review-checklist still restates a gate refusal: {restated!r}")
                return 1
        for kept in (
            "evidence-first tasks",
            "observable proof",
            "through the public interface",
            "not build-only or shape-only",
        ):
            if kept not in flat:
                report(f"{label} {root} review-checklist lost the judgment {kept!r}.")
                return 1
    if "review-checklist-defers-to-gate" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("review-checklist-defers-to-gate scenario passed.")
    return 0


def validate_covers_annotation_entry_scenario() -> int:
    """Issue #49 Section 1's fail-open half, owner-decided 2026-08-17: a Covers
    entry that opens with a critical-statement identifier and a dash
    (`D2 — note`) must resolve as that critical statement — failing loudly when
    the identifier is missing from design.md — instead of silently degrading to
    an unlinked legacy-task-reference, while colon-form entries and hyphenated
    free text stay free-text references.
    """
    design_with_d2 = "## Decisions\n\nD2 — Keep one shared parser.\n"

    def start_with_covers(
        repo: Path, covers_entry: str, design: str
    ) -> subprocess.CompletedProcess[str]:
        write_text(repo / "openspec/changes/demo/design.md", design)
        write_text(
            repo / "openspec/changes/demo/tasks.md",
            task_capsule_compact_fixture().replace(
                "    - E1: Public behavior passes.\n",
                f"    - {covers_entry}\n",
            ),
        )
        return run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
        )

    def authority_of(result: subprocess.CompletedProcess[str]) -> list:
        return (
            json.loads(result.stdout)
            .get("contract", {})
            .get("capsule", {})
            .get("authority", [])
        )

    with tempfile.TemporaryDirectory(prefix="keel-covers-annotation-") as raw:
        repo = Path(raw)
        result = start_with_covers(repo, "D2 — an annotation", design_with_d2)
        if result.returncode != 0:
            report(
                "covers-annotation-entry: `D2 — an annotation` with a resolvable "
                f"D2 must pass, got exit {result.returncode}: "
                f"{(result.stderr or result.stdout).strip()}"
            )
            return 1
        authority = authority_of(result)
        if not any(
            item.get("reference") == "D2"
            and item.get("kind") == "critical-statement"
            and item.get("text") == "Keep one shared parser."
            for item in authority
        ):
            report(
                "covers-annotation-entry: `D2 — an annotation` must resolve as "
                "critical-statement authority carrying the design.md statement "
                f"text, got: {authority!r}"
            )
            return 1
        if any("an annotation" in str(item.get("text", "")) for item in authority):
            report(
                "covers-annotation-entry: the annotation must not become "
                "authority text; design.md owns the statement."
            )
            return 1

    with tempfile.TemporaryDirectory(prefix="keel-covers-annotation-missing-") as raw:
        repo = Path(raw)
        result = start_with_covers(
            repo,
            "D2 — an annotation",
            "## Decisions\n\nD1 — Unrelated decision. Basis: fixture authority.\n",
        )
        problems = json.loads(result.stdout).get("problems", [])
        message = next(
            (
                item.get("message", "")
                for item in problems
                if item.get("code") == "unresolved-covers"
            ),
            "",
        )
        if result.returncode == 0 or not message.startswith(
            "Missing Covers critical statement: D2."
        ):
            report(
                "covers-annotation-entry: `D2 — an annotation` with no D2 in "
                "design.md must fail as Missing instead of passing as an "
                f"unlinked reference, got exit {result.returncode}: {message!r}"
            )
            return 1

    for covers_entry in ("E1: Public behavior passes.", "D2-compatible fixture text"):
        with tempfile.TemporaryDirectory(prefix="keel-covers-annotation-free-") as raw:
            repo = Path(raw)
            result = start_with_covers(repo, covers_entry, design_with_d2)
            if result.returncode != 0:
                report(
                    f"covers-annotation-entry: {covers_entry!r} must stay a "
                    "passing free-text reference, got exit "
                    f"{result.returncode}: "
                    f"{(result.stderr or result.stdout).strip()}"
                )
                return 1
            authority = authority_of(result)
            if not any(
                item.get("kind") == "legacy-task-reference" for item in authority
            ) or any(
                item.get("kind") == "critical-statement" for item in authority
            ):
                report(
                    f"covers-annotation-entry: {covers_entry!r} must remain a "
                    f"legacy-task-reference, got: {authority!r}"
                )
                return 1

    if "covers-annotation-entry" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "covers-annotation-entry: the scenario registry does not include it."
        )
        return 1
    report("covers-annotation-entry scenario passed.")
    return 0


def validate_expectation_completion_gates_scenario() -> int:
    protocol_snippets = [
        "Completion Gate",
        "critical expectation",
        "behavior evidence",
        "durable owner",
        "discard rationale",
        "keel gate task-complete",
        "Acceptance check",
        "Scope check",
        "Findings",
    ]
    review_snippets = [
        "critical expectation",
        "behavior evidence",
        "Resolved here:",
        "Durable owner:",
        "Discard reason:",
        "explicit discard reason",
        "thin Keel consistency gate",
        "evidence details",
        "deterministic structure",
        "`Status`",
        "`Acceptance check`",
        "`Scope check`",
        "`Findings`",
    ]
    task_template_review_snippets = [
        "- Review:",
        "- Status:",
        "- Acceptance check:",
        "- Scope check:",
        "- Findings:",
        "Discard rationale:",
    ]
    # The handoff skill is retired (#485); `keel --help` carries the format.
    handoff_skill_snippets = [
        "schema: keel-handoff/v1",
        "owner (a pointer into openspec/changes/",
        "change-close",
        "no other field",
    ]
    handoff_template_snippets = [
        "schema: keel-handoff/v1",
        "owner: openspec/changes/",
        "action:",
        "reason:",
    ]
    archive_overlay_snippets = [
        "keel gate change-close --action archive",
        "critical expectation",
        "behavior evidence",
        "durable follow-up owner",
        "explicit discard reason",
    ]

    checks: list[tuple[str, Path, list[str]]] = [
        ("root AGENTS.md", ROOT / "AGENTS.md", protocol_snippets),
        ("source review-checklist skill", ROOT / "src/skills/review-checklist/SKILL.md", review_snippets),
        (
            "source tasks Review template",
            ROOT / "assets/openspec/schemas/keel-spec-driven/templates/tasks.md",
            task_template_review_snippets,
        ),
        (
            "repo tasks Review template",
            ROOT / "openspec/schemas/keel-spec-driven/templates/tasks.md",
            task_template_review_snippets,
        ),
        (
            "dist tasks Review template",
            ROOT / "assets/openspec/schemas/keel-spec-driven/templates/tasks.md",
            task_template_review_snippets,
        ),
        ("keel --help HANDOFF format", ROOT / "bin/keel.js", handoff_skill_snippets),
        ("OpenSpec archive overlay generator", ROOT / "bin/keel.js", archive_overlay_snippets),
    ]

    for label, path, snippets in checks:
        if not path.is_file():
            report(f"expectation-completion-gates scenario missing {label}: {path}")
            return 1
        content = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in content:
                report(
                    f"expectation-completion-gates scenario {label} "
                    f"missing required text: {snippet}"
                )
                return 1

    report("expectation-completion-gates scenario passed.")
    return 0


def validate_authoring_continuity_scenario() -> int:
    protocol_snippets = [
        "align-expectations",
        "risk-triggered deep path",
        "hidden-knowledge risk",
        "domain lenses",
        "Missing authority returns to OpenSpec authoring",
    ]
    schema_snippets = [
        "risk-triggered deep",
        "hidden-knowledge assumptions",
        "domain lens",
    ]
    design_template_snippets = [
        "Hidden Knowledge / Assumptions",
        "compressed recovery context",
        "keel/HANDOFF.md",
    ]
    task_template_snippets = [
        "hidden-knowledge assumption",
        "domain lens",
    ]

    checks: list[tuple[str, Path, list[str]]] = [
        ("root AGENTS.md", ROOT / "AGENTS.md", protocol_snippets),
        (
            "source keel-spec-driven schema",
            ROOT / "assets/openspec/schemas/keel-spec-driven/schema.yaml",
            schema_snippets,
        ),
        (
            "repo keel-spec-driven schema",
            ROOT / "openspec/schemas/keel-spec-driven/schema.yaml",
            schema_snippets,
        ),
        (
            "dist keel-spec-driven schema",
            ROOT / "assets/openspec/schemas/keel-spec-driven/schema.yaml",
            schema_snippets,
        ),
        (
            "source design template",
            ROOT / "assets/openspec/schemas/keel-spec-driven/templates/design.md",
            design_template_snippets,
        ),
        (
            "repo design template",
            ROOT / "openspec/schemas/keel-spec-driven/templates/design.md",
            design_template_snippets,
        ),
        (
            "dist design template",
            ROOT / "assets/openspec/schemas/keel-spec-driven/templates/design.md",
            design_template_snippets,
        ),
        (
            "source tasks template",
            ROOT / "assets/openspec/schemas/keel-spec-driven/templates/tasks.md",
            task_template_snippets,
        ),
        (
            "repo tasks template",
            ROOT / "openspec/schemas/keel-spec-driven/templates/tasks.md",
            task_template_snippets,
        ),
        (
            "dist tasks template",
            ROOT / "assets/openspec/schemas/keel-spec-driven/templates/tasks.md",
            task_template_snippets,
        ),
    ]

    for label, path, snippets in checks:
        if not path.is_file():
            report(f"authoring-continuity scenario missing {label}: {path}")
            return 1
        content = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in content:
                report(
                    f"authoring-continuity scenario {label} "
                    f"missing required text: {snippet}"
                )
                return 1

    with tempfile.TemporaryDirectory(prefix="keel-authoring-state-") as raw_tmp:
        root = Path(raw_tmp)
        scaffold_repo = root / "scaffold"
        scaffold_repo.mkdir()
        write_text(
            scaffold_repo / "openspec/changes/draft/proposal.md",
            "# Proposal\n",
        )
        scaffold = run_keel(scaffold_repo, "context", "--json")
        scaffold_payload = json.loads(scaffold.stdout)
        if (
            scaffold.returncode != 0
            or scaffold_payload.get("status") != "ready"
            or scaffold_payload.get("selection")
            != {"source": "inferred", "change": "draft", "task": None}
            or scaffold_payload.get("nextAction", {}).get("kind") != "author"
        ):
            report(
                "authoring-continuity scenario did not keep an incomplete proposal actionable."
            )
            report((scaffold.stderr or scaffold.stdout).strip())
            return 1

        invalid_repo = root / "invalid"
        invalid_repo.mkdir()
        change_root = invalid_repo / "openspec/changes/authored-no-task"
        write_text(change_root / "proposal.md", "# Proposal\n")
        write_text(change_root / "design.md", "# Design\n")
        write_text(
            change_root / "specs/demo/spec.md",
            "## ADDED Requirements\n",
        )
        write_text(change_root / "tasks.md", "# Tasks\n\n## Invalidates\n\n- None.\n\n## Tasks\n")
        invalid = run_keel(invalid_repo, "context", "--json")
        invalid_payload = json.loads(invalid.stdout)
        if (
            invalid.returncode != 0
            or invalid_payload.get("status") != "blocked"
            or invalid_payload.get("selection") is not None
            or not any(
                "task" in reason.lower() and "invalid" in reason.lower()
                for reason in invalid_payload.get("reasons", [])
            )
        ):
            report(
                "authoring-continuity scenario let an authored no-task change disappear."
            )
            report((invalid.stderr or invalid.stdout).strip())
            return 1

    report("authoring-continuity scenario passed.")
    return 0


# task-start requires a change to declare what it invalidates, so every fixture
# that expects to start a task carries the cheapest legitimate answer. Scenarios
# exercising the declaration itself replace this block.
INVALIDATES_NONE = "## Invalidates\n\n- None.\n\n"


INVALIDATION_ENTRIES = (
    '- I1: "Touch is the write boundary" — assets/bootstrap/AGENTS.md.'
    " Updated by: 1.1\n"
    '- I2: "does not accept a GitHub issue URL" —'
    " keel/archive/follow-ups/note.md."
    " Discard reason: archive notes are historical evidence.\n"
    '- I3: "the suite is not portable" — README.md.'
    " Durable owner: https://example.invalid/issues/1\n"
)


def invalidation_repo(root: Path, name: str, section: str | None) -> Path:
    repo = root / name
    # A real Contract anchor, so the missing-section case can prove that a
    # failing authoring gate leaves the anchor untouched rather than merely
    # failing earlier for want of one.
    body = task_contract_fixture()
    body = body.replace(INVALIDATES_NONE, "" if section is None else section)
    write_text(repo / "openspec/changes/demo/tasks.md", body)
    return repo


def validate_task_start_invalidation_scenario() -> int:
    label = "task-start-invalidation"

    def gate(repo: Path, *extra: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = run_keel(
            repo, "gate", "task-start", ".",
            "--change", "demo", "--task", "1.1", "--json", *extra,
        )
        payload = json.loads(result.stdout) if result.stdout.strip() else {}
        return result, payload

    def codes(payload: dict) -> set[str]:
        return {item.get("code") for item in payload.get("problems", [])}

    def messages(payload: dict) -> str:
        return " ".join(item.get("message", "") for item in payload.get("problems", []))

    with tempfile.TemporaryDirectory(
        prefix="keel-invalidation-", ignore_cleanup_errors=True
    ) as raw:
        tmp = Path(raw)

        # A change that never answered the question cannot start, and the
        # refusal writes nothing — the guard manifest and the Contract anchor
        # are both withheld, so a failed authoring gate leaves no state behind.
        missing = invalidation_repo(tmp, "missing", None)
        tasks_before = (missing / "openspec/changes/demo/tasks.md").read_text(
            encoding="utf-8"
        )
        result, payload = gate(missing, "--record")
        if (
            payload.get("status") != "fail"
            or "invalidation-declaration" not in codes(payload)
        ):
            report(f"{label} accepted a change with no invalidation section.")
            report(repr(payload.get("problems")))
            return 1
        if (missing / "keel/guard.json").exists():
            report(f"{label} wrote a guard manifest for a failing authoring gate.")
            return 1
        if (missing / "openspec/changes/demo/tasks.md").read_text(
            encoding="utf-8"
        ) != tasks_before:
            report(f"{label} recorded a Contract anchor for a failing gate.")
            return 1

        none_repo = invalidation_repo(tmp, "none", INVALIDATES_NONE)
        _, none_payload = gate(none_repo, "--no-guard")
        if none_payload.get("status") != "pass":
            report(f"{label} refused a legitimate declaration of nothing.")
            report(repr(none_payload.get("problems")))
            return 1

        full_repo = invalidation_repo(
            tmp, "full", "## Invalidates\n\n" + INVALIDATION_ENTRIES + "\n"
        )
        _, full_payload = gate(full_repo, "--no-guard")
        if full_payload.get("status") != "pass":
            report(f"{label} refused well-formed entries covering all three closures.")
            report(repr(full_payload.get("problems")))
            return 1

        # The declaration is change-level bookkeeping, not task authority: two
        # changes whose tasks are byte-identical must compile the same capsule
        # however differently they answered this question.
        none_print = none_payload.get("contract", {}).get("fingerprint", {}).get("value")
        full_print = full_payload.get("contract", {}).get("fingerprint", {}).get("value")
        if not none_print or none_print != full_print:
            report(
                f"{label} let the invalidation section move the capsule "
                f"fingerprint: {none_print} vs {full_print}"
            )
            return 1

        # A location list only ever names files the author already recalled,
        # which is the failure this section exists to prevent, so an entry
        # without the searchable wording is refused.
        no_phrase = invalidation_repo(
            tmp,
            "no-phrase",
            "## Invalidates\n\n- I1: AGENTS.md and README.md. Updated by: 1.1\n\n",
        )
        _, no_phrase_payload = gate(no_phrase, "--no-guard")
        if (
            no_phrase_payload.get("status") != "fail"
            or "I1" not in messages(no_phrase_payload)
        ):
            report(f"{label} accepted an entry with no searchable phrase.")
            report(repr(no_phrase_payload.get("problems")))
            return 1

        unclosed = invalidation_repo(
            tmp,
            "unclosed",
            '## Invalidates\n\n- I1: "Touch is the write boundary" — AGENTS.md.\n\n',
        )
        _, unclosed_payload = gate(unclosed, "--no-guard")
        if (
            unclosed_payload.get("status") != "fail"
            or "I1" not in messages(unclosed_payload)
        ):
            report(f"{label} accepted an entry that never closed.")
            report(repr(unclosed_payload.get("problems")))
            return 1

        unknown_owner = invalidation_repo(
            tmp,
            "unknown-task",
            '## Invalidates\n\n- I1: "Touch is the write boundary" — AGENTS.md.'
            " Updated by: 9.9\n\n",
        )
        _, unknown_payload = gate(unknown_owner, "--no-guard")
        if unknown_payload.get("status") != "fail":
            report(f"{label} accepted an updater task that does not exist.")
            return 1

        if not codes(payload):
            report(f"{label} reported a failure with no problem code.")
            return 1

    report(f"{label} scenario passed.")
    return 0


# A task for the section-boundary fixtures. Two shapes matter and nothing else
# does: `covers` puts `- E<n>:` lines inside a task body, which a section that
# ran over the task list read as its own entries, and `repo_action` gives the
# task a `Touch` of a bare `- none`, which such a section read as its `- None.`
# and closed itself with. Every other field is the cheapest legitimate value.
def section_boundary_task(
    task_id: str,
    *,
    checked: bool,
    covers: tuple[str, ...] = ("E1: the task owns its file",),
    repo_action: bool = False,
) -> str:
    covers_lines = "".join(f"    - {item}\n" for item in covers)
    touch = "    - none\n" if repo_action else "    - src/example.js\n"
    mode = "repo-action" if repo_action else "implementation"
    return (
        f"- [{'x' if checked else ' '}] {task_id} Section boundary fixture\n"
        "  - Owner: claude\n"
        f"  - Mode: {mode}\n"
        "  - Covers:\n"
        f"{covers_lines}"
        "  - Read:\n"
        "    - README.md\n"
        "  - Touch:\n"
        f"{touch}"
        "  - Verify:\n"
        "    - Strategy: evidence-first\n"
        "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "    - M1: node test.js reports the public behavior passing\n"
        "  - Acceptance:\n"
        "    - Public behavior passes.\n"
        "  - Autonomy boundary:\n"
        "    - Default: hard-stop\n"
        "    - Pre-authorized fallback: none\n"
        "  - Stop Rules:\n"
        "    - Stop on failure.\n"
        "  - Evidence:\n"
        "    - Contract: pending\n"
        "    - M1: node test.js reported 4 passing and 0 failing\n"
        "    - Review:\n"
        "      - Status: pass\n"
        "      - Acceptance check: the public behavior was exercised\n"
        "      - Scope check: only the declared file changed\n"
        "      - Findings: none\n"
        "    - Blocker: none\n"
        "  - Stop if:\n"
        "    - Requires files outside Touch.\n"
    )


# The same file with the section above the task list and in the tail. Nothing
# else differs between the two, which is what makes the pair a measurement of
# position rather than of content.
def section_boundary_tasks_md(*, section: str, task: str, position: str) -> str:
    if position == "above":
        return "# Tasks\n\n" + section + "\n" + task
    return "# Tasks\n\n" + task + "\n" + section


def section_boundary_repo(root: Path, name: str, content: str) -> Path:
    repo = root / name
    change = repo / "openspec/changes/demo"
    write_text(change / "tasks.md", content)
    write_text(change / "proposal.md", "# Proposal\n")
    write_text(change / "design.md", "## Context\n\nfixture\n")
    write_text(change / "specs/demo/spec.md", "## ADDED Requirements\n")
    return repo


def validate_section_boundary_scenario() -> int:
    """A change-level section is bounded by the tasks, not only by headings.

    Regression for issue #71 and for the silent half the issue does not report.
    Both readers of a change-level section sliced to the next `## ` heading, so
    a section that was not the file's last one ran over the task list: the
    `- E<n>:` lines a task declares under `Covers` were judged as coverage
    entries and reported unclosed, and a `repo-action` task's `Touch` of a bare
    `- none` was read as the section's `- None.` and closed a declaration that
    closed nothing.

    Every cell is a pair — the identical section above the task list and in the
    tail — asserted both absolutely and against each other. The absolute half
    matters: a comparison alone passes when both positions are broken the same
    way.
    """
    label = "section-boundary"

    def problems_of(payload: dict) -> list[tuple[str, str]]:
        return sorted(
            (item.get("code", ""), item.get("message", ""))
            for item in payload.get("problems", [])
        )

    def closure_problems(payload: dict, code: str) -> list[str]:
        return [
            item.get("message", "")
            for item in payload.get("problems", [])
            if item.get("code") == code
        ]

    with tempfile.TemporaryDirectory(
        prefix="keel-section-boundary-", ignore_cleanup_errors=True
    ) as raw:
        tmp = Path(raw)

        # `None` and `{}` are kept apart on purpose. A fixture task-start
        # refused and a gate that printed nothing are different failures, and a
        # message naming one of them while the other happened sends the reader
        # to a place with no problem in it.
        def close(name: str, content: str) -> dict | None:
            repo = section_boundary_repo(tmp, name, content)
            # A checked task with no recorded anchor fails the close for a
            # reason that has nothing to do with this boundary, and that noise
            # would land in both halves of every pair.
            if not record_contract_anchor(repo, "demo", "1.1"):
                return None
            result = run_keel(
                repo, "gate", "change-close", ".",
                "--change", "demo", "--action", "archive", "--json",
            )
            return json.loads(result.stdout) if result.stdout.strip() else {}

        def start(name: str, content: str) -> dict:
            repo = section_boundary_repo(tmp, name, content)
            result = run_keel(
                repo, "gate", "task-start", ".",
                "--change", "demo", "--task", "1.1", "--no-guard", "--json",
            )
            return json.loads(result.stdout) if result.stdout.strip() else {}

        def readable(payload: dict | None, fixture: str, gate: str) -> bool:
            if payload is None:
                report(
                    f"{label} could not record a Contract anchor for {fixture}: "
                    "task-start refused the fixture, so change-close never ran "
                    "against it."
                )
                return False
            if not payload:
                report(
                    f"{label} got no JSON from {gate} for {fixture}, so there "
                    "was no verdict to read rather than a verdict that was "
                    "wrong."
                )
                return False
            return True

        # Cell 1: `## Expectation Coverage` closes every entry it declares, and
        # the task below it declares `- E1:`/`- E2:` under its own `Covers`.
        # Nothing here is unclosed in either position.
        closed_coverage = (
            "## Invalidates\n\n- None.\n\n"
            "## Expectation Coverage\n\n"
            "- E1: The task owns its file. Covered by: 1.1\n"
            "- E2: The task proves it. Covered by: 1.1\n"
        )
        closed_task = section_boundary_task(
            "1.1",
            checked=True,
            covers=("E1: The task owns its file.", "E2: The task proves it."),
        )
        closed = {
            position: close(
                f"coverage-closed-{position}",
                section_boundary_tasks_md(
                    section=closed_coverage, task=closed_task, position=position
                ),
            )
            for position in ("above", "tail")
        }
        for position, payload in closed.items():
            if not readable(payload, f"coverage-closed-{position}", "change-close"):
                return 1
            stray = closure_problems(payload, "expectation-closure")
            if stray:
                report(
                    f"{label} reported an expectation the section closes as "
                    f"unclosed, with the section {position} the task list. The "
                    "entries it judged are the task's own Covers lines."
                )
                report(repr(stray))
                return 1
        if problems_of(closed["above"]) != problems_of(closed["tail"]):
            report(
                f"{label} returned different problems for identical section "
                "content depending on where the section sits."
            )
            report(repr(problems_of(closed["above"])))
            report(repr(problems_of(closed["tail"])))
            return 1
        if closed["tail"].get("status") != "pass":
            report(
                f"{label} refused a fixture whose only expectations are closed; "
                "the pair comparison above would then be comparing two failures."
            )
            report(repr(closed["tail"].get("problems")))
            return 1

        # Cell 2: the silent half. The entry closes nothing, and the task below
        # is a `repo-action` whose `Touch` is a bare `- none`.
        open_coverage = (
            "## Invalidates\n\n- None.\n\n"
            "## Expectation Coverage\n\n"
            "- E3: Nothing closes this one.\n"
        )
        none_task = section_boundary_task("1.1", checked=True, repo_action=True)
        unclosed = {
            position: close(
                f"coverage-open-{position}",
                section_boundary_tasks_md(
                    section=open_coverage, task=none_task, position=position
                ),
            )
            for position in ("above", "tail")
        }
        for position, payload in unclosed.items():
            if not readable(payload, f"coverage-open-{position}", "change-close"):
                return 1
            named = [
                message
                for message in closure_problems(payload, "expectation-closure")
                if "E3" in message
            ]
            if not named:
                report(
                    f"{label} accepted an expectation that closes nothing, with "
                    f"the section {position} the task list. A task field of "
                    "`none` is not the section's `- None.`."
                )
                report(repr(payload.get("problems")))
                return 1
        if problems_of(unclosed["above"]) != problems_of(unclosed["tail"]):
            report(
                f"{label} returned different problems for an identical unclosed "
                "section depending on where the section sits."
            )
            report(repr(problems_of(unclosed["above"])))
            report(repr(problems_of(unclosed["tail"])))
            return 1

        # Cell 3: the other reader. `## Invalidates` is read by task-start, and
        # holds the character-identical slice.
        closed_invalidates = (
            "## Invalidates\n\n"
            '- I1: "the wording that is now wrong" — README.md. Updated by: 1.1\n'
        )
        start_task = section_boundary_task("1.1", checked=False)
        started = {
            position: start(
                f"invalidates-closed-{position}",
                section_boundary_tasks_md(
                    section=closed_invalidates, task=start_task, position=position
                ),
            )
            for position in ("above", "tail")
        }
        for position, payload in started.items():
            if not readable(payload, f"invalidates-closed-{position}", "task-start"):
                return 1
            if payload.get("status") != "pass":
                report(
                    f"{label} refused a closed invalidation declaration with "
                    f"the section {position} the task list."
                )
                report(repr(payload.get("problems")))
                return 1

        # Cell 4: the silent half of the other reader. This is the cell that
        # returned `pass` before the boundary gained its task half.
        open_invalidates = (
            "## Invalidates\n\n"
            '- I1: "the wording that is now wrong" — README.md.\n'
        )
        open_start_task = section_boundary_task(
            "1.1", checked=False, repo_action=True
        )
        unstarted = {
            position: start(
                f"invalidates-open-{position}",
                section_boundary_tasks_md(
                    section=open_invalidates, task=open_start_task, position=position
                ),
            )
            for position in ("above", "tail")
        }
        for position, payload in unstarted.items():
            if not readable(payload, f"invalidates-open-{position}", "task-start"):
                return 1
            named = [
                message
                for message in closure_problems(payload, "invalidation-closure")
                if "I1" in message
            ]
            if not named:
                report(
                    f"{label} accepted an invalidation that closes nothing, "
                    f"with the section {position} the task list. A task field "
                    "of `none` is not the section's `- None.`."
                )
                report(repr(payload.get("problems")))
                return 1
        if problems_of(unstarted["above"]) != problems_of(unstarted["tail"]):
            report(
                f"{label} returned different problems for an identical unclosed "
                "invalidation depending on where the section sits."
            )
            report(repr(problems_of(unstarted["above"])))
            report(repr(problems_of(unstarted["tail"])))
            return 1

        # Cells 5 and 6: the heading half of the boundary, in the tail, where
        # it is the only half that applies. An indented `##` line inside the
        # section's own body is not a heading, and the entry after it must still
        # be judged. The tolerant spelling `parseTasks()` uses for task bodies
        # ends the section there and drops that entry without a word — issue
        # #160, measured on the abandoned first attempt at #71 as `7bd6448`.
        # Both readers are covered because each slices its own section.
        indented = "  ## an indented line is not a heading\n"
        indented_invalidates = (
            "## Invalidates\n\n"
            '- I1: "the wording that is now wrong" — README.md. Updated by: 1.1\n'
            + indented
            + '- I2: "wording nothing updates" — README.md.\n'
        )
        payload = start(
            "invalidates-indented-tail",
            section_boundary_tasks_md(
                section=indented_invalidates, task=start_task, position="tail"
            ),
        )
        if not readable(payload, "invalidates-indented-tail", "task-start"):
            return 1
        if not [
            message
            for message in closure_problems(payload, "invalidation-closure")
            if "I2" in message
        ]:
            report(
                f"{label} accepted an invalidation that closes nothing because "
                "it follows an indented `##` line; the section ended at a line "
                "that is not a heading."
            )
            report(repr(payload.get("problems")))
            return 1

        indented_coverage = (
            "## Invalidates\n\n- None.\n\n"
            "## Expectation Coverage\n\n"
            "- E1: The task owns its file. Covered by: 1.1\n"
            + indented
            + "- E3: Nothing closes this one.\n"
        )
        payload = close(
            "coverage-indented-tail",
            section_boundary_tasks_md(
                section=indented_coverage,
                task=section_boundary_task("1.1", checked=True),
                position="tail",
            ),
        )
        if not readable(payload, "coverage-indented-tail", "change-close"):
            return 1
        if not [
            message
            for message in closure_problems(payload, "expectation-closure")
            if "E3" in message
        ]:
            report(
                f"{label} accepted an expectation that closes nothing because "
                "it follows an indented `##` line; the section ended at a line "
                "that is not a heading."
            )
            report(repr(payload.get("problems")))
            return 1

    report(f"{label} scenario passed.")
    return 0


SCHEMA_COPY_PAIRS = (
    (
        "openspec/schemas/keel-spec-driven/templates/tasks.md",
        "assets/openspec/schemas/keel-spec-driven/templates/tasks.md",
    ),
    (
        "openspec/schemas/keel-spec-driven/schema.yaml",
        "assets/openspec/schemas/keel-spec-driven/schema.yaml",
    ),
)


def validate_anchor_reverification_bound_scenario() -> int:
    label = "anchor-reverification-bound"

    # The fingerprint is described as recompiled and compared at resume,
    # projection, and completion, with no stated bound. It holds while the
    # change is live: the capsule records each authority's source as a path
    # under the change directory, and archiving renames that directory. An
    # unstated boundary reads as no boundary, so demonstrate where it is.
    with tempfile.TemporaryDirectory(prefix="keel-anchor-bound-") as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()
        live = repo / "openspec/changes/demo/tasks.md"
        write_text(live, task_contract_fixture())

        recorded = run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
            "--record", "--json",
        )
        payload = json.loads(recorded.stdout)
        if payload.get("status") != "pass":
            report(f"{label} could not record an anchor on a live change.")
            report(json.dumps(payload.get("problems", []), indent=2))
            return 1
        anchor = payload["contract"]["fingerprint"]["value"]

        # Live: recompiling reproduces the recorded value, which is the
        # guarantee the resident protocol states.
        again = json.loads(
            run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
            ).stdout
        )
        if again["contract"]["fingerprint"]["value"] != anchor:
            report(f"{label} a live anchor did not recompile to its recorded value.")
            return 1

        # Archived: the gate refuses to select the change at all, so the bound
        # is enforced rather than merely documented.
        archived = repo / "openspec/changes/archive/2026-07-28-demo/tasks.md"
        write_text(archived, live.read_text(encoding="utf-8"))
        refused = run_keel(
            repo, "gate", "task-start",
            "--change", "archive/2026-07-28-demo", "--task", "1.1",
        )
        if refused.returncode == 0 or "invalid change name" not in (
            refused.stderr + refused.stdout
        ):
            report(
                f"{label} the gate accepted an archived change; the bound this "
                "documents is supposed to be enforced, not advisory."
            )
            report((refused.stderr or refused.stdout).strip())
            return 1

        # And the reason the refusal is right: compiling the archived copy
        # directly yields a different fingerprint, because each authority's
        # `source` names the directory the task now lives in.
        probe = subprocess.run(
            [
                "node", "-e",
                "const {loadTaskContract}=require(process.argv[1]);"
                "const c=loadTaskContract(process.argv[2],'archive/2026-07-28-demo','1.1');"
                "process.stdout.write(c.contract.fingerprint.value);",
                str(ROOT / "src/core/task-contract.js"),
                str(repo),
            ],
            text=True, encoding="utf-8", capture_output=True, check=False,
        )
        if probe.returncode != 0:
            report(f"{label} could not compile the archived copy directly.")
            report((probe.stderr or probe.stdout).strip())
            return 1
        if probe.stdout.strip() == anchor:
            report(
                f"{label} the archived copy reproduced the anchor, so the "
                "documented bound no longer describes reality — revisit the "
                "protocol wording rather than relaxing this check."
            )
            return 1

    # And the resident protocol must say where the guarantee stops.
    resident = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    if "while its change is live" not in resident:
        report(
            f"{label} the resident protocol describes recompilation without "
            "stating that it holds while the change is live."
        )
        return 1

    report(f"{label} scenario passed.")
    return 0


def validate_authoring_surface_owner_and_tags_scenario() -> int:
    label = "authoring-surface-owner-and-tags"

    # Both rules this change adds widen what a gate accepts. An author only
    # benefits if the shipped surface says so, so the template, the artifact
    # instruction the CLI hands back, and the resident protocol each state them.
    template = (
        ROOT / "openspec/schemas/keel-spec-driven/templates/tasks.md"
    ).read_text(encoding="utf-8")
    resident = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    # Read the instruction the way an author receives it — through the CLI in a
    # repository Keel installed — rather than from the schema file it is
    # composed from, so a change that never reaches the author is a failure.
    with tempfile.TemporaryDirectory(prefix="keel-authoring-surface-") as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()
        install = run_keel(repo, "--install")
        if install.returncode != 0:
            report(f"{label} keel --install failed.")
            report((install.stderr or install.stdout).strip())
            return 1
        created = run_openspec(repo, "new", "change", "surface-probe")
        if created is None:
            report(
                f"{label} skipped: the openspec CLI could not be found. "
                "Searched " + ", then ".join(OPENSPEC_SEARCH_ORDER) + "."
            )
            return 3
        if created.returncode != 0:
            report(f"{label} could not scaffold a change to read the instruction.")
            report((created.stderr or created.stdout).strip())
            return 1
        instructions = run_openspec(
            repo, "instructions", "tasks", "--change", "surface-probe"
        )
        if instructions is None or instructions.returncode != 0:
            report(f"{label} could not read the tasks artifact instruction.")
            if instructions is not None:
                report((instructions.stderr or instructions.stdout).strip())
            return 1
        instruction = instructions.stdout

    for surface, text in (("tasks template", template), ("tasks instruction", instruction)):
        for needle in (
            "regression",
            "at least one check untagged",
        ):
            if needle not in text:
                report(f"{label} {surface} does not describe the tag: {needle}")
                return 1
        # D6 — the wording trap: red and green accompany the bare label.
        if "in addition to" not in text.lower():
            report(
                f"{label} {surface} still reads as though `.red`/`.green` "
                "replace the bare M<n> Evidence rather than accompanying it."
            )
            return 1
        if "repo-relative path that exists" not in text:
            report(
                f"{label} {surface} does not state the existing-path owner form."
            )
            return 1
        if "HANDOFF" not in text:
            report(f"{label} {surface} does not state that HANDOFF is refused.")
            return 1

    for needle in (
        "regression-only-strategy",
        "in addition to the bare",
        "any repo-relative path that exists",
    ):
        if needle not in resident:
            report(f"{label} resident protocol does not state: {needle}")
            return 1

    for local, packaged in SCHEMA_COPY_PAIRS:
        if (ROOT / local).read_text(encoding="utf-8") != (
            ROOT / packaged
        ).read_text(encoding="utf-8"):
            report(f"{label} schema copies diverge: {local} vs {packaged}")
            return 1

    report(f"{label} scenario passed.")
    return 0


def validate_an_invalidates_phrase_may_wrap_scenario() -> int:
    """Issue #108: the quoted phrase had to fit on one line.

    An `## Invalidates` entry carries a quotation, a location, and a closure,
    and wraps as often as it needs to. The phrase test was
    `/"[^"\\n]{3,}"/`, so a quotation that ran past the end of a line was
    reported as `names where to look but not what to look for` — when it named
    exactly that, and the only repair was to reflow the text.

    The corpus looked clean for the wrong reason: 42 of this repository's 194
    archived entries span more than one line and none carries a wrapped
    quotation, because the gate refused every one that did. Five entries in a
    single session were shortened to fit.

    The bound is the entry, set by the section parser, so a quotation cannot
    reach past its own entry — asserted below by refusing a second, unquoted
    entry while the wrapped one is accepted.
    """
    label = "an-invalidates-phrase-may-wrap"

    with tempfile.TemporaryDirectory(prefix="keel-wrapped-phrase-") as raw:
        repo = Path(raw) / "repo"
        repo.mkdir()
        tasks_path = repo / "openspec/changes/demo/tasks.md"
        write_text(repo / "openspec/changes/demo/proposal.md", "# Proposal\n")
        write_text(repo / "openspec/changes/demo/design.md", "## Context\n\nfixture\n")
        write_text(
            repo / "openspec/changes/demo/specs/demo/spec.md",
            "## ADDED Requirements\n",
        )

        def start(section: str) -> dict:
            write_text(
                tasks_path,
                task_contract_fixture().replace(
                    "## Invalidates\n\n- None.\n\n", section
                ),
            )
            result = run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
                "--json",
            )
            return json.loads(result.stdout)

        def problems(payload: dict) -> str:
            return " ".join(
                item.get("code", "") + ": " + item.get("message", "")
                for item in payload.get("problems", [])
            )

        wrapped = (
            '## Invalidates\n\n'
            '- I1: "the wording that is now wrong and runs on\n'
            '  past the end of this line" — somewhere in the repo.\n'
            '  Updated by: 1.1\n\n'
        )
        payload = start(wrapped)
        if payload.get("status") != "pass":
            report(
                f"{label}: an entry whose quotation wraps was refused. It named "
                "the wording a reader would search for; what it did not do was "
                "fit on one line, and reflowing text is not a repair."
            )
            report(json.dumps(payload.get("problems", []), indent=2))
            return 1

        # The requirement itself is unchanged: an entry with no quotation
        # anywhere in its body is still refused.
        unquoted = (
            '## Invalidates\n\n'
            '- I1: the wording that is now wrong and runs on\n'
            '  past the end of this line — somewhere in the repo.\n'
            '  Updated by: 1.1\n\n'
        )
        payload = start(unquoted)
        if payload.get("status") == "pass":
            report(
                f"{label}: an entry carrying no quotation at all was accepted. "
                "Reading the phrase across lines must widen where the quotation "
                "may sit, not remove the requirement to write one."
            )
            return 1
        if "invalidation-phrase" not in problems(payload):
            report(
                f"{label}: the unquoted entry was refused for some other reason, "
                "so this assertion proves nothing about the phrase check. Got: "
                + problems(payload)
            )
            return 1

        # The bound is the entry. A wrapped quotation in I1 must not satisfy an
        # unquoted I2 sitting below it.
        mixed = (
            '## Invalidates\n\n'
            '- I1: "the wording that is now wrong and runs on\n'
            '  past the end of this line" — somewhere in the repo.\n'
            '  Updated by: 1.1\n'
            '- I2: some other statement — elsewhere in the repo.\n'
            '  Updated by: 1.1\n\n'
        )
        payload = start(mixed)
        text = problems(payload)
        if payload.get("status") == "pass":
            report(
                f"{label}: an unquoted entry below a wrapped one was accepted. "
                "The quotation is bounded by its own entry; if it reaches the "
                "next one, every entry after a quoted one passes for free."
            )
            return 1
        if "I2" not in text:
            report(
                f"{label}: the run failed, but not for I2 — so this assertion "
                "proves nothing about the entry bound. The unquoted entry is "
                "the one that must be named. Got: " + text
            )
            return 1
        if "I1" in text:
            report(
                f"{label}: the wrapped entry was reported alongside the unquoted "
                "one. It carries its quotation and must not be named."
            )
            report(text)
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_a_path_is_what_the_value_declares_scenario() -> int:
    """Issue #113: the extractor answered with a path the value did not declare.

    Two shapes, measured across five consuming repositories — 624 path-shaped
    declarations, 34 of them extracting something else.

    A sentence supplies no whitespace. `openspec/FOLLOWUP.md。②接着说别的`
    extracted whole, because the run is bounded by whitespace and Chinese prose
    puts none after a path. That half refuses loudly, naming a path nobody
    wrote.

    A citation outranked the declaration. The backtick branch ran first and
    searched the whole value, so a `Durable owner:` that named its owner and
    then quoted another file resolved to the quotation. That half is worse: the
    quoted file usually exists, so the gate accepts and checks a file the
    author never declared.
    """
    label = "a-path-is-what-the-value-declares"

    with tempfile.TemporaryDirectory(prefix="keel-declared-path-") as raw:
        repo = Path(raw) / "repo"
        repo.mkdir()
        tasks_path = repo / "openspec/changes/demo/tasks.md"
        write_text(repo / "openspec/changes/demo/proposal.md", "# Proposal\n")
        write_text(repo / "openspec/changes/demo/design.md", "## Context\n\nfixture\n")
        write_text(
            repo / "openspec/changes/demo/specs/demo/spec.md",
            "## ADDED Requirements\n",
        )
        for name in (
            "docs/owner.md",
            "docs/cited.md",
            "docs/\u7b2c\u4e00\u7ae0/\u603b\u8bba.md",
            "AGENTS.md",
        ):
            write_text(repo / name, "x\n")
        write_text(repo / "docs/a b.md", "x\n")

        def completion(findings: str) -> dict:
            write_text(
                tasks_path,
                task_contract_fixture(evidence=("M1: check exercised.",))
                .replace("- [ ] 1.1", "- [x] 1.1")
                .replace("      - Status: pending\n", "      - Status: pass\n")
                .replace(
                    "      - Acceptance check: pending\n",
                    "      - Acceptance check: behavior proven through the public CLI.\n",
                )
                .replace(
                    "      - Scope check: pending\n",
                    "      - Scope check: writes stayed inside Touch.\n",
                )
                .replace("      - Findings: pending\n", f"      - Findings: {findings}\n")
            )
            record_contract_anchor(repo, "demo")
            result = run_keel(
                repo, "gate", "task-complete", "--change", "demo", "--task", "1.1",
                "--json",
            )
            return json.loads(result.stdout)

        def messages(payload: dict) -> str:
            return " ".join(
                item.get("message", "") for item in payload.get("problems", [])
            )

        # --- the citation must not outrank the declaration ---------------
        cited = "\u5224\u636e\u89c1 `docs/cited.md`"
        payload = completion(f"still open. Durable owner: docs/owner.md\uff0c{cited}")
        if payload.get("status") != "pass":
            report(
                f"{label}: a value naming an existing owner and then citing "
                "another existing file was refused."
            )
            report(json.dumps(payload.get("problems", []), indent=2))
            return 1

        # Proven by removing the declared owner: the refusal must name it, not
        # the citation. Without this the assertion above passes either way,
        # because both files exist.
        (repo / "docs/owner.md").unlink()
        payload = completion(f"still open. Durable owner: docs/owner.md\uff0c{cited}")
        if payload.get("status") == "pass":
            report(
                f"{label}: with the declared owner deleted the value still "
                "passed, so the gate checked the cited file instead. A "
                "citation that outranks the declaration lets a finding be "
                "owned by a file the author never named."
            )
            return 1

        # Which path the gate looked for, asserted through the reader that
        # names one. `Findings` reports a single owner refusal for every
        # unusable owner and never names the path, so the naming half is
        # asserted where it is actually emitted.
        def invalidates(closure: str) -> dict:
            write_text(
                tasks_path,
                task_contract_fixture().replace(
                    "## Invalidates\n\n- None.\n\n",
                    '## Invalidates\n\n- I1: "the wording that is now wrong" '
                    f"\u2014 somewhere in the repo. {closure}\n\n",
                ),
            )
            result = run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
                "--json",
            )
            return json.loads(result.stdout)

        payload = invalidates(f"Durable owner: docs/owner.md\uff0c{cited}")
        text = messages(payload)
        if payload.get("status") == "pass":
            report(
                f"{label}: an invalidation entry whose declared owner is "
                "missing passed, so the gate resolved the citation."
            )
            return 1
        if "docs/cited.md" in text or "docs/owner.md" not in text:
            report(
                f"{label}: the refusal named the citation rather than the "
                f"declared path. Got: {text or '(none)'}"
            )
            return 1
        write_text(repo / "docs/owner.md", "x\n")

        payload = invalidates(f"Durable owner: docs/owner.md\uff0c{cited}")
        if payload.get("status") != "pass":
            report(
                f"{label}: with the declared owner restored the invalidation "
                "entry was still refused."
            )
            report(json.dumps(payload.get("problems", []), indent=2))
            return 1

        # --- a bare run ends where the sentence does ---------------------
        accepted = (
            (
                "a path followed by a CJK terminator and more prose",
                "still open. Durable owner: docs/owner.md\u3002\u2461\u63a5\u7740\u8bf4\u522b\u7684",
            ),
            (
                "a path followed by a CJK comma",
                "still open. Durable owner: docs/owner.md\uff0c\u968f\u540e\u8bf4\u660e",
            ),
            (
                "a path whose own segments are CJK words",
                "still open. Durable owner: docs/\u7b2c\u4e00\u7ae0/\u603b\u8bba.md\u3002\u540e\u6587",
            ),
            (
                "a backticked path containing a space, opening the value",
                "still open. Durable owner: `docs/a b.md` \u8bf4\u660e",
            ),
            (
                "a backticked path with nothing declared before it",
                "still open. Durable owner: \u89c1 `docs/cited.md`",
            ),
            ("a repository-root file", "still open. Durable owner: AGENTS.md"),
            ("the same file with a leading dot-slash", "still open. Durable owner: ./AGENTS.md"),
            (
                "an ASCII path ending a sentence",
                "still open. Durable owner: docs/owner.md. Then more text",
            ),
        )
        for description, findings in accepted:
            payload = completion(findings)
            if payload.get("status") != "pass":
                report(f"{label}: {description} was refused.")
                report(json.dumps(payload.get("problems", []), indent=2))
                return 1

        # --- the boundary: a non-path stays unrecognized ------------------
        for description, findings in (
            ("a bare word", "still open. Durable owner: pending"),
            ("a version string", "still open. Durable owner: 5.44.0"),
            (
                "a separator between two adjacent inline code spans",
                "still open. Durable owner: \u9996\u7248\u53ea\u88c5 `networkx`/`PyYAML`",
            ),
        ):
            payload = completion(findings)
            text = messages(payload)
            if payload.get("status") == "pass":
                report(f"{label}: {description} was accepted as a durable owner.")
                return 1
            if "does not exist" in text:
                report(
                    f"{label}: {description} was reported as a missing file. "
                    "Got: " + text
                )
                return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_a_root_file_is_a_path_scenario() -> int:
    """Issue #107: a file at the repository root had no separator to find.

    `declaredPath()` located a path by finding a run of non-whitespace holding
    a path separator. Nine files sit at this repository's root and every one of
    them is a legitimate owner, so `Durable owner: AGENTS.md` was refused with
    `it names neither a check nor a path` — for a path whose file exists. The
    way past it was `./AGENTS.md`, which is a concession to the extractor
    rather than a path anyone meant.

    The boundary is what keeps this from becoming worse than the defect: a bare
    word must stay unrecognized, or `Durable owner: pending` would be reported
    as a file that does not exist and send the author to create one.
    """
    label = "a-root-file-is-a-path"

    with tempfile.TemporaryDirectory(prefix="keel-root-file-") as raw:
        repo = Path(raw) / "repo"
        repo.mkdir()
        tasks_path = repo / "openspec/changes/demo/tasks.md"
        write_text(repo / "openspec/changes/demo/proposal.md", "# Proposal\n")
        write_text(repo / "openspec/changes/demo/design.md", "## Context\n\nfixture\n")
        write_text(
            repo / "openspec/changes/demo/specs/demo/spec.md",
            "## ADDED Requirements\n",
        )
        write_text(repo / "AGENTS.md", "# Agents\n")

        def completion(findings: str) -> dict:
            write_text(
                tasks_path,
                task_contract_fixture(evidence=("M1: check exercised.",))
                .replace("- [ ] 1.1", "- [x] 1.1")
                .replace("      - Status: pending\n", "      - Status: pass\n")
                .replace(
                    "      - Acceptance check: pending\n",
                    "      - Acceptance check: behavior proven through the public CLI.\n",
                )
                .replace(
                    "      - Scope check: pending\n",
                    "      - Scope check: writes stayed inside Touch.\n",
                )
                .replace("      - Findings: pending\n", f"      - Findings: {findings}\n")
            )
            record_contract_anchor(repo, "demo")
            result = run_keel(
                repo, "gate", "task-complete", "--change", "demo", "--task", "1.1",
                "--json",
            )
            return json.loads(result.stdout)

        def messages(payload: dict) -> str:
            return " ".join(
                item.get("message", "") for item in payload.get("problems", [])
            )

        accepted = (
            ("a root file as a durable owner", "still open. Durable owner: AGENTS.md"),
            ("a root file as resolution evidence", "repaired. Resolved here: AGENTS.md"),
            ("the same file spelled with ./", "still open. Durable owner: ./AGENTS.md"),
            (
                "a root file ending a sentence",
                "still open. Durable owner: AGENTS.md.",
            ),
        )
        for description, findings in accepted:
            payload = completion(findings)
            if payload.get("status") != "pass":
                report(
                    f"{label}: {description} was refused. The file exists at the "
                    "repository root; requiring a separator refuses a path the "
                    "author may name and leaves them only a notation to change."
                )
                report(json.dumps(payload.get("problems", []), indent=2))
                return 1

        # Existence still decides.
        payload = completion("still open. Durable owner: NOT-THERE.md")
        if payload.get("status") == "pass":
            report(f"{label}: a root file that does not exist was accepted.")
            return 1

        # And where the gate names a missing path, it names a root file the
        # same way. `Findings` reports the generic owner refusal for every
        # unusable owner and always has; `## Invalidates` is the reader that
        # names the file, so the naming is asserted there rather than claimed
        # of a reader that never did it.
        def invalidates(closure: str) -> dict:
            write_text(
                tasks_path,
                task_contract_fixture().replace(
                    "## Invalidates\n\n- None.\n\n",
                    '## Invalidates\n\n- I1: "the wording that is now wrong" '
                    f"— somewhere in the repo. {closure}\n\n",
                ),
            )
            result = run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
                "--json",
            )
            return json.loads(result.stdout)

        payload = invalidates("Durable owner: AGENTS.md")
        if payload.get("status") != "pass":
            report(
                f"{label}: a root file was refused as an invalidation owner. "
                "One extractor serves every reader, so a form accepted in one "
                "must be accepted in all."
            )
            report(json.dumps(payload.get("problems", []), indent=2))
            return 1

        payload = invalidates("Durable owner: NOT-THERE.md")
        text = messages(payload)
        if payload.get("status") == "pass":
            report(f"{label}: a missing root file closed an invalidation entry.")
            return 1
        if "NOT-THERE.md" not in text:
            report(
                f"{label}: the refusal for a missing root file did not name it. "
                "A path is the one form a gate can check, and naming what it "
                f"looked for is what makes the refusal repairable. Got: {text}"
            )
            return 1

        # The boundary: a value with no path shape stays unrecognized, so the
        # author is not sent to create a file named `pending`.
        for description, findings in (
            ("a bare word", "still open. Durable owner: pending"),
            ("a version string", "still open. Durable owner: 5.44.0"),
        ):
            payload = completion(findings)
            text = messages(payload)
            if payload.get("status") == "pass":
                report(f"{label}: {description} was accepted as a durable owner.")
                return 1
            if "does not exist" in text:
                report(
                    f"{label}: {description} was reported as a file that does "
                    "not exist. It is not a path, and saying it is missing "
                    "sends the author to create it. Got: " + text
                )
                return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_an_owner_outlives_the_change_scenario() -> int:
    """Issue #100: the existence check expires at archive.

    `openspec archive` moves `openspec/changes/<name>/` under
    `openspec/changes/archive/`, so a `Durable owner:` naming the change's own
    `design.md` is true when the gate reads it and false one workflow step
    later. Measured in this repository: 10 declarations name a path inside a
    live change directory, all 10 are dead, and all 10 point at the change that
    wrote them. A pointer that must break is worse than none — the Review reads
    as closed while the trail ends halfway.

    A path into a *different* live change stays accepted: the protocol names a
    new OpenSpec change as a legitimate owner of deferred work, and no measured
    pointer has that shape.
    """
    label = "an-owner-outlives-the-change"

    with tempfile.TemporaryDirectory(prefix="keel-owner-outlives-") as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()
        tasks_path = repo / "openspec/changes/demo/tasks.md"
        write_text(repo / "openspec/changes/demo/proposal.md", "# Proposal\n")
        write_text(repo / "openspec/changes/demo/design.md", "## Context\n\nfixture\n")
        write_text(
            repo / "openspec/changes/demo/specs/demo/spec.md",
            "## ADDED Requirements\n",
        )
        # The other live change, and an archived path. Both exist; only one of
        # them is the directory the selected change is about to move.
        write_text(repo / "openspec/changes/other/design.md", "## Context\n\nother\n")
        write_text(repo / "keel/archive/notes/2026-09-05-example.md", "note\n")

        SELF = "openspec/changes/demo/design.md"
        OTHER = "openspec/changes/other/design.md"
        ARCHIVED = "keel/archive/notes/2026-09-05-example.md"
        TRACKER = "https://github.com/TanglmChris/keel/issues/100"

        def start(section: str) -> dict:
            fixture = task_contract_fixture()
            if section.startswith("## Invalidates"):
                fixture = fixture.replace("## Invalidates\n\n- None.\n\n", section)
            else:
                fixture = fixture + "\n" + section
            write_text(tasks_path, fixture)
            result = run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
                "--json",
            )
            return json.loads(result.stdout)

        def invalidates(closure: str) -> dict:
            return start(
                '## Invalidates\n\n- I1: "the wording that is now wrong" '
                f"— somewhere in the repo. {closure}\n\n"
            )

        # `## Expectation Coverage` is read by change-close, not task-start, so
        # this fixture closes the change rather than starting a task. Mirrors
        # the `durable-owner-vocabulary` scenario's own closing fixture.
        def expectation(closure: str) -> dict:
            write_text(
                tasks_path,
                task_contract_fixture(evidence=("M1: check exercised.",))
                .replace("- [ ] 1.1", "- [x] 1.1")
                .replace("      - Status: pending\n", "      - Status: pass\n")
                .replace(
                    "      - Acceptance check: pending\n",
                    "      - Acceptance check: proven.\n",
                )
                .replace(
                    "      - Scope check: pending\n",
                    "      - Scope check: inside Touch.\n",
                )
                .replace("      - Findings: pending\n", "      - Findings: none\n")
                + f"\n## Expectation Coverage\n\n- E1: the expectation. {closure}\n",
            )
            record_contract_anchor(repo, "demo")
            result = run_keel(
                repo, "gate", "change-close", "--change", "demo", "--action",
                "sync", "--json",
            )
            return json.loads(result.stdout)

        def completion(findings: str) -> dict:
            fixture = (
                task_contract_fixture(evidence=("M1: check exercised.",))
                .replace("- [ ] 1.1", "- [x] 1.1")
                .replace("      - Status: pending\n", "      - Status: pass\n")
                .replace(
                    "      - Acceptance check: pending\n",
                    "      - Acceptance check: behavior proven through the public CLI.\n",
                )
                .replace(
                    "      - Scope check: pending\n",
                    "      - Scope check: writes stayed inside Touch.\n",
                )
                .replace("      - Findings: pending\n", f"      - Findings: {findings}\n")
            )
            write_text(tasks_path, fixture)
            record_contract_anchor(repo, "demo")
            result = run_keel(
                repo, "gate", "task-complete", "--change", "demo", "--task", "1.1",
                "--json",
            )
            return json.loads(result.stdout)

        def messages(payload: dict) -> str:
            return " ".join(
                item.get("message", "") for item in payload.get("problems", [])
            )

        # The self-pointer is refused wherever an owner closes an entry, and
        # the refusal says why rather than reporting a spelling problem.
        refusals = (
            ("an Invalidates entry", invalidates(f"Durable owner: {SELF}")),
            ("an Expectation Coverage entry", expectation(f"Durable owner: {SELF}")),
            (
                "a Review finding",
                completion(f"the rule needs a second look. Durable owner: {SELF}"),
            ),
            (
                "a Resolved here claim",
                completion(f"the rule was repaired. Resolved here: {SELF}"),
            ),
        )
        for description, payload in refusals:
            if payload.get("status") == "pass":
                report(
                    f"{label}: a path inside the selected change's own directory "
                    f"closed {description}. That directory moves when the change "
                    "is archived, so the check was true only until the next step "
                    "of the workflow that accepted it."
                )
                return 1
            text = messages(payload)
            if "archiv" not in text.lower():
                report(
                    f"{label}: the refusal for {description} does not say the "
                    "directory moves when the change is archived, so it reads as "
                    "a spelling problem the author cannot repair. Got: "
                    f"{text or '(none)'}"
                )
                return 1

        # A different live change is a legitimate owner and stays one, as do
        # the forms that already worked.
        accepted = (
            ("another live change closing an Invalidates entry",
             invalidates(f"Durable owner: {OTHER}")),
            ("another live change closing an Expectation Coverage entry",
             expectation(f"Durable owner: {OTHER}")),
            ("another live change owning a finding",
             completion(f"still open. Durable owner: {OTHER}")),
            ("resolution evidence in another live change",
             completion(f"repaired. Resolved here: {OTHER}")),
            ("an archived path owning a finding",
             completion(f"still open. Durable owner: {ARCHIVED}")),
            ("a tracker reference owning a finding",
             completion(f"still open. Durable owner: {TRACKER}")),
        )
        for description, payload in accepted:
            if payload.get("status") != "pass":
                report(
                    f"{label}: {description} was refused. The rule is about the "
                    "directory this change is about to move, not about change "
                    "directories in general."
                )
                report(json.dumps(payload.get("problems", []), indent=2))
                return 1

        # Every refusal that lists the forms says what checking each is worth.
        for description, payload in (
            ("an Invalidates refusal", invalidates("no closure at all")),
            ("an Expectation Coverage refusal", expectation("no closure at all")),
            ("a Findings refusal", completion("a narrative finding with no marker")),
        ):
            text = messages(payload)
            for expected in (
                "checked for existence when it is cited",
                "never fetches",
            ):
                if expected not in text:
                    report(
                        f"{label}: {description} does not say what the accepted "
                        f"forms are worth — missing: {expected}. An author who "
                        "cannot see what was checked infers that it was."
                    )
                    report(text or "(none)")
                    return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_durable_owner_vocabulary_scenario() -> int:
    label = "durable-owner-vocabulary"

    # The accepted owner forms are shape checks: a gate cannot resolve a URL or
    # confirm an archive path is the right one. A repo-relative path is the one
    # form it can actually check, so refusing it drew the line in the least
    # defensible place.
    with tempfile.TemporaryDirectory(prefix="keel-owner-vocab-") as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()
        tasks_path = repo / "openspec/changes/demo/tasks.md"
        write_text(repo / "openspec/FOLLOWUP.md", "# Follow-ups\n")
        write_text(repo / "keel/HANDOFF.md", "pointer\n")
        write_text(repo / "keel/archive/notes/2026-07-28-example.md", "note\n")

        def invalidation_start(closure: str) -> dict:
            write_text(
                tasks_path,
                task_contract_fixture().replace(
                    "## Invalidates\n\n- None.\n\n",
                    '## Invalidates\n\n- I1: "the wording that is now wrong" '
                    f"— somewhere in the repo. {closure}\n\n",
                ),
            )
            result = run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
            )
            return json.loads(result.stdout)

        def completion(findings: str) -> dict:
            fixture = (
                task_contract_fixture(evidence=("M1: check exercised.",))
                .replace("- [ ] 1.1", "- [x] 1.1")
                .replace("      - Status: pending\n", "      - Status: pass\n")
                .replace(
                    "      - Acceptance check: pending\n",
                    "      - Acceptance check: behavior proven through the public CLI.\n",
                )
                .replace(
                    "      - Scope check: pending\n",
                    "      - Scope check: writes stayed inside Touch.\n",
                )
                .replace(
                    "      - Findings: pending\n", f"      - Findings: {findings}\n"
                )
            )
            write_text(tasks_path, fixture)
            record_contract_anchor(repo, "demo")
            result = run_keel(
                repo, "gate", "task-complete", "--change", "demo", "--task", "1.1", "--json"
            )
            return json.loads(result.stdout)

        def close(closure: str) -> dict:
            write_text(
                tasks_path,
                task_contract_fixture(evidence=("M1: check exercised.",))
                .replace("- [ ] 1.1", "- [x] 1.1")
                .replace("      - Status: pending\n", "      - Status: pass\n")
                .replace(
                    "      - Acceptance check: pending\n",
                    "      - Acceptance check: proven.\n",
                )
                .replace("      - Scope check: pending\n", "      - Scope check: inside Touch.\n")
                .replace("      - Findings: pending\n", "      - Findings: none\n")
                + f"\n## Expectation Coverage\n\n- E1: the expectation. {closure}\n",
            )
            write_text(repo / "openspec/changes/demo/proposal.md", "# Proposal\n")
            write_text(repo / "openspec/changes/demo/design.md", "## Context\n\nfixture\n")
            write_text(
                repo / "openspec/changes/demo/specs/demo/spec.md",
                "## ADDED Requirements\n",
            )
            result = run_keel(
                repo, "gate", "change-close", "--change", "demo", "--action", "sync", "--json"
            )
            return json.loads(result.stdout)

        # M1 — an existing repo path closes an entry in all three shared places.
        ledger = "Durable owner: openspec/FOLLOWUP.md"
        payload = invalidation_start(ledger)
        if payload.get("status") != "pass":
            report(f"{label} refused a repo ledger as an invalidation owner.")
            report(json.dumps(payload.get("problems", []), indent=2))
            return 1

        payload = completion(f"the IDE shell contract gap. {ledger}")
        if payload.get("status") != "pass":
            report(f"{label} refused a repo ledger as a Findings owner.")
            report(json.dumps(payload.get("problems", []), indent=2))
            return 1

        payload = close(ledger)
        if any(
            item.get("code") == "expectation-closure"
            for item in payload.get("problems", [])
        ):
            report(f"{label} refused a repo ledger as an Expectation Coverage owner.")
            report(json.dumps(payload.get("problems", []), indent=2))
            return 1

        # And a path with no file behind it is refused, distinguishably.
        payload = invalidation_start("Durable owner: openspec/NOT-THERE.md")
        codes = {item.get("code") for item in payload.get("problems", [])}
        messages = " ".join(
            item.get("message", "") for item in payload.get("problems", [])
        )
        if (
            payload.get("status") != "fail"
            or "invalidation-owner-missing" not in codes
            or "openspec/NOT-THERE.md" not in messages
        ):
            report(f"{label} accepted a durable owner with no file behind it.")
            report(json.dumps(payload.get("problems", []), indent=2))
            return 1

        # M2 — the pointer override is still not an owner, although it exists.
        payload = invalidation_start("Durable owner: keel/HANDOFF.md")
        messages = " ".join(
            item.get("message", "") for item in payload.get("problems", [])
        )
        if payload.get("status") != "fail" or "HANDOFF" not in messages:
            report(f"{label} accepted keel/HANDOFF.md as a durable owner.")
            report(json.dumps(payload.get("problems", []), indent=2))
            return 1

        # A refusal names the forms it accepts, including the new one.
        payload = invalidation_start("no closure at all")
        messages = " ".join(
            item.get("message", "") for item in payload.get("problems", [])
        )
        for expected in ("Durable owner:", "repo-relative path that exists", "Discard reason:"):
            if expected not in messages:
                report(f"{label} refusal does not name the accepted form: {expected}")
                report(messages)
                return 1

        # M3 — every previously accepted form still closes. The change artifact
        # names another live change: a path inside `demo`'s own directory is
        # refused now, because that directory moves when `demo` is archived.
        for closure in (
            "Durable owner: openspec/changes/other-change/proposal.md",
            "Durable owner: keel/archive/notes/2026-07-28-example.md",
            "Durable owner: https://github.com/TanglmChris/keel/issues/20",
            "Discard reason: it stands as written.",
        ):
            write_text(
                repo / "openspec/changes/other-change/proposal.md", "# Proposal\n"
            )
            payload = invalidation_start(closure)
            if payload.get("status") != "pass":
                report(f"{label} dropped a previously accepted form: {closure}")
                report(json.dumps(payload.get("problems", []), indent=2))
                return 1

    report(f"{label} scenario passed.")
    return 0


def regression_tag_fixture(
    commands: tuple[str, ...],
    evidence: tuple[str, ...],
    *,
    strategy: str = "vertical-tdd",
) -> str:
    return (
        task_contract_fixture(commands=commands, evidence=evidence)
        .replace(
            "  - Commands:\n",
            f"  - Verification Strategy: {strategy}\n  - Commands:\n",
        )
        .replace("      - Status: pending\n", "      - Status: pass\n")
        .replace(
            "      - Acceptance check: pending\n",
            "      - Acceptance check: behavior proven through the public CLI.\n",
        )
        .replace(
            "      - Scope check: pending\n",
            "      - Scope check: writes stayed inside Touch.\n",
        )
        .replace("      - Findings: pending\n", "      - Findings: none\n")
    )


def validate_regression_check_tag_scenario() -> int:
    label = "regression-check-tag"

    # A regression check asserts that something already green is still green, so
    # it has no honest red. Requiring one leaves an author fabricating evidence
    # or folding the guard into the behavior check; the tag is the third option.
    with tempfile.TemporaryDirectory(prefix="keel-regression-tag-") as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()
        tasks_path = repo / "openspec/changes/demo/tasks.md"

        def complete(fixture: str) -> dict:
            write_text(tasks_path, fixture)
            record_contract_anchor(repo, "demo")
            result = run_keel(
                repo, "gate", "task-complete", "--change", "demo", "--task", "1.1", "--json"
            )
            return json.loads(result.stdout)

        def start(fixture: str) -> dict:
            write_text(tasks_path, fixture)
            result = run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
            )
            return json.loads(result.stdout)

        mixed_commands = (
            "M1: behavior reaches the public interface",
            "M2 (regression): the existing suite stays green",
        )

        # M1 — a tagged check completes without red/green, and the untagged one
        # still needs both.
        payload = complete(
            regression_tag_fixture(
                mixed_commands,
                (
                    "M1: behavior exercised.",
                    "M1.red: failed before the implementation.",
                    "M1.green: passed after.",
                    "M2: existing suite still green.",
                ),
            )
        )
        if payload.get("status") != "pass":
            report(f"{label} refused a tagged regression check that needs no red.")
            report(json.dumps(payload.get("problems", []), indent=2))
            return 1

        # D5 — the exemption is from red-green, not from evidence.
        payload = complete(
            regression_tag_fixture(
                mixed_commands,
                (
                    "M1: behavior exercised.",
                    "M1.red: failed before the implementation.",
                    "M1.green: passed after.",
                    "M2: pending",
                ),
            )
        )
        if payload.get("status") != "fail" or not any(
            "M2" in item.get("message", "")
            for item in payload.get("problems", [])
        ):
            report(f"{label} completed a tagged check with no evidence at all.")
            report(json.dumps(payload, indent=2))
            return 1

        # M2 — the strategy cannot be emptied out by tagging every check.
        payload = start(
            regression_tag_fixture(
                (
                    "M1 (regression): the existing suite stays green",
                    "M2 (regression): the golden files stay byte-identical",
                ),
                ("M1: pending", "M2: pending"),
            )
        )
        codes = {item.get("code") for item in payload.get("problems", [])}
        if payload.get("status") != "fail" or "regression-only-strategy" not in codes:
            report(
                f"{label} accepted a red-green strategy whose every check is tagged."
            )
            report(json.dumps(payload, indent=2))
            return 1

        # M3 — an untagged check emits no tag key, so its capsule and fingerprint
        # are byte-identical to what they were before the tag existed.
        payload = start(
            regression_tag_fixture(
                ("M1: behavior reaches the public interface",),
                ("M1: pending",),
            )
        )
        entries = (
            payload.get("contract", {})
            .get("capsule", {})
            .get("verification", {})
            .get("commands", [])
        )
        if payload.get("status") != "pass" or [sorted(entry) for entry in entries] != [
            ["check", "label"]
        ]:
            report(
                f"{label} changed the compiled shape of an untagged check, which "
                "moves every recorded contract fingerprint."
            )
            report(json.dumps(entries, indent=2))
            return 1

        # And a tagged check does declare itself in the capsule, so the exemption
        # is a visible term of the contract rather than a silent skip.
        payload = start(
            regression_tag_fixture(mixed_commands, ("M1: pending", "M2: pending"))
        )
        tagged = next(
            (
                entry
                for entry in payload.get("contract", {})
                .get("capsule", {})
                .get("verification", {})
                .get("commands", [])
                if entry.get("label") == "M2"
            ),
            None,
        )
        if not tagged or tagged.get("regression") is not True:
            report(f"{label} did not record the regression tag in the capsule.")
            report(json.dumps(payload.get("contract", {}), indent=2))
            return 1

    report(f"{label} scenario passed.")
    return 0


def change_verify_task(
    task_id: str,
    *,
    checked: bool,
    commands: tuple[str, ...],
    evidence: tuple[str, ...],
) -> str:
    command_lines = "".join(f"    - {item}\n" for item in commands)
    evidence_lines = "".join(f"    - {item}\n" for item in evidence)
    return (
        f"- [{'x' if checked else ' '}] {task_id} Change verify fixture\n"
        "  - Owner: claude\n"
        "  - Mode: implementation\n"
        "  - Covers:\n"
        "    - E1: the task proves its own behavior\n"
        "  - Read:\n"
        "    - README.md\n"
        "  - Touch:\n"
        "    - src/example.js\n"
        "  - Verify:\n"
        "    - Strategy: vertical-tdd\n"
        f"{command_lines}"
        "  - Acceptance:\n"
        "    - Public behavior passes.\n"
        "  - Autonomy boundary:\n"
        "    - Default: hard-stop\n"
        "    - Pre-authorized fallback: none\n"
        "  - Stop Rules:\n"
        "    - Stop on failure.\n"
        "  - Evidence:\n"
        "    - Contract: pending\n"
        f"{evidence_lines}"
        "    - Review:\n"
        "      - Status: pass\n"
        "      - Acceptance check: behavior proven.\n"
        "      - Scope check: writes stayed inside Touch.\n"
        "      - Findings: none\n"
        "    - Blocker: none\n"
        "  - Stop if:\n"
        "    - Requires files outside Touch.\n"
    )


def change_verify_deferred_evidence_repo(root: Path, name: str) -> Path:
    repo = root / name
    write_text(repo / "openspec/changes/demo/proposal.md", "# Proposal\n")
    write_text(repo / "openspec/changes/demo/design.md", "## Context\n\nfixture\n")
    write_text(repo / "openspec/changes/demo/specs/demo/spec.md", "## ADDED Requirements\n")
    return repo


def validate_change_verify_deferred_evidence_scenario() -> int:
    """A `(regression)`-tagged check may defer its bare Evidence to a
    change-level `C<n>` check, run once for the whole change instead of once
    per task. Issue #95: a full regression suite that only needs to run once
    had no place to live in `tasks.md`, so authors either paid to repeat it on
    every task or gave the middle tasks no safety net at all.
    """
    label = "change-verify-deferred-evidence"

    change_verify_c1 = (
        "## Change Verify\n\n"
        "- Strategy: regression-first\n"
        "- C1: the full three-layer suite is 0 failed\n\n"
    )
    change_evidence_c1_pending = "## Change Evidence\n\n- C1: pending\n\n"
    change_evidence_c1_pass = (
        "## Change Evidence\n\n- C1: pass. Full suite ran clean at 142/142.\n\n"
    )
    tagged_commands = (
        "M1: behavior reaches the public interface",
        "M2 (regression): the full suite stays green",
    )
    deferred_evidence = (
        "M1: behavior exercised.",
        "M1.red: failed before the implementation.",
        "M1.green: passed after.",
        "M2: deferred to C1",
    )

    def tasks_md(
        *,
        change_verify: str = "",
        change_evidence: str = "",
        commands: tuple[str, ...] = tagged_commands,
        evidence: tuple[str, ...],
        checked: bool = True,
    ) -> str:
        sections = (
            "## Invalidates\n\n- None.\n\n"
            "## Expectation Coverage\n\n"
            "- E1: the task proves its own behavior. Covered by: 1.1\n\n"
            + change_verify
            + change_evidence
        )
        return "# Tasks\n\n" + sections + change_verify_task(
            "1.1", checked=checked, commands=commands, evidence=evidence
        )

    with tempfile.TemporaryDirectory(
        prefix="keel-change-verify-", ignore_cleanup_errors=True
    ) as raw:
        tmp = Path(raw)
        repo = change_verify_deferred_evidence_repo(tmp, "repo")
        tasks_path = repo / "openspec/changes/demo/tasks.md"

        def codes(payload: dict) -> set[str]:
            return {item.get("code") for item in payload.get("problems", [])}

        def complete(fixture: str) -> dict:
            write_text(tasks_path, fixture)
            record_contract_anchor(repo, "demo")
            result = run_keel(
                repo, "gate", "task-complete", "--change", "demo", "--task", "1.1", "--json"
            )
            return json.loads(result.stdout)

        def close(fixture: str) -> dict:
            write_text(tasks_path, fixture)
            record_contract_anchor(repo, "demo")
            result = run_keel(
                repo, "gate", "change-close", "--change", "demo", "--action", "sync", "--json"
            )
            return json.loads(result.stdout)

        # (a) A `(regression)`-tagged check deferring to a declared C1 passes
        # task-complete with no C1 result required yet — the change has not
        # closed, so the deferred check may legitimately not have run.
        payload = complete(tasks_md(change_verify=change_verify_c1, evidence=deferred_evidence))
        if payload.get("status") != "pass":
            report(f"{label} refused a regression check deferring to a declared change-level check.")
            report(json.dumps(payload.get("problems", []), indent=2))
            return 1

        # (b) An untagged check deferring to C1 fails: only a
        # `(regression)`-tagged check may defer.
        payload = complete(
            tasks_md(
                change_verify=change_verify_c1,
                commands=(
                    "M1: behavior reaches the public interface",
                    "M2: the full suite stays green",
                ),
                evidence=(
                    "M1: behavior exercised.",
                    "M1.red: failed before the implementation.",
                    "M1.green: passed after.",
                    "M2: deferred to C1",
                    "M2.red: n/a",
                    "M2.green: n/a",
                ),
            )
        )
        if (
            payload.get("status") != "fail"
            or "deferred-evidence-not-regression" not in codes(payload)
        ):
            report(f"{label} let an untagged check defer to a change-level check.")
            report(json.dumps(payload, indent=2))
            return 1

        # (c) A `(regression)`-tagged check deferring to an undeclared C9
        # fails: the reference must resolve.
        payload = complete(
            tasks_md(
                change_verify=change_verify_c1,
                evidence=(
                    "M1: behavior exercised.",
                    "M1.red: failed before the implementation.",
                    "M1.green: passed after.",
                    "M2: deferred to C9",
                ),
            )
        )
        if payload.get("status") != "fail" or "deferred-check-unresolved" not in codes(payload):
            report(f"{label} accepted a deferral to a change-level check that was never declared.")
            report(json.dumps(payload, indent=2))
            return 1

        # (d) change-close fails the same way when a task defers but
        # `## Change Verify` does not exist at all.
        payload = close(tasks_md(evidence=deferred_evidence))
        if payload.get("status") != "fail" or "deferred-check-unresolved" not in codes(payload):
            report(f"{label} closed a change whose deferred check has no Change Verify section.")
            report(json.dumps(payload, indent=2))
            return 1

        # (e) change-close fails when C1 is declared but Change Evidence has
        # no concrete entry for it — the check has to actually run once.
        payload = close(
            tasks_md(
                change_verify=change_verify_c1,
                change_evidence=change_evidence_c1_pending,
                evidence=deferred_evidence,
            )
        )
        if payload.get("status") != "fail" or "change-evidence-missing" not in codes(payload):
            report(f"{label} closed a change whose declared C1 has no concrete Change Evidence.")
            report(json.dumps(payload, indent=2))
            return 1

        # (f) change-close passes once Change Evidence carries concrete
        # evidence for every declared C<n>.
        payload = close(
            tasks_md(
                change_verify=change_verify_c1,
                change_evidence=change_evidence_c1_pass,
                evidence=deferred_evidence,
            )
        )
        if payload.get("status") != "pass":
            report(f"{label} refused a fully resolved deferred change-level check at close.")
            report(json.dumps(payload.get("problems", []), indent=2))
            return 1

        # (g) A change no task defers in reports nothing about either
        # section, whether present or absent — the feature costs nothing to a
        # change that never uses it, and a declared-but-unused section is
        # still held to its own shape.
        undeferred_evidence = (
            "M1: behavior exercised.",
            "M1.red: failed before the implementation.",
            "M1.green: passed after.",
            "M2: existing suite still green.",
        )
        without_sections = close(tasks_md(evidence=undeferred_evidence))
        with_unused_sections = close(
            tasks_md(
                change_verify=change_verify_c1,
                change_evidence=change_evidence_c1_pass,
                evidence=undeferred_evidence,
            )
        )
        for payload in (without_sections, with_unused_sections):
            stray = [
                item
                for item in payload.get("problems", [])
                if item.get("code", "").startswith("change-verify")
                or item.get("code", "").startswith("change-evidence")
                or item.get("code", "").startswith("deferred-")
            ]
            if stray:
                report(
                    f"{label} reported a Change Verify/Evidence problem for a "
                    "change nothing defers to."
                )
                report(json.dumps(stray, indent=2))
                return 1

        # (h) Non-contiguous C<n> labels fail change-close: the section is
        # held to the same label discipline `M<n>` already is.
        broken_change_verify = (
            "## Change Verify\n\n"
            "- Strategy: regression-first\n"
            "- C1: the full three-layer suite is 0 failed\n"
            "- C3: the byte baseline stays identical\n\n"
        )
        payload = close(
            tasks_md(
                change_verify=broken_change_verify,
                change_evidence="## Change Evidence\n\n- C1: pass.\n- C3: pass.\n\n",
                evidence=deferred_evidence,
            )
        )
        if payload.get("status") != "fail" or "change-verify-shape" not in codes(payload):
            report(f"{label} accepted non-contiguous Change Verify labels.")
            report(json.dumps(payload, indent=2))
            return 1

    report(f"{label} scenario passed.")
    return 0


def validate_invalidation_authoring_surface_scenario() -> int:
    label = "invalidation-authoring-surface"

    # The two schema copies are the repo-local one OpenSpec resolves and the
    # packaged one `keel --init` writes. This is the only check that asserts they
    # agree: compact-task-authoring used to imply it through a projection loop
    # rooted at trees that no longer exist, so it compared nothing and has since
    # been removed.
    for local, packaged in SCHEMA_COPY_PAIRS:
        local_text = (ROOT / local).read_text(encoding="utf-8")
        packaged_text = (ROOT / packaged).read_text(encoding="utf-8")
        if local_text != packaged_text:
            report(f"{label} schema copies diverge: {local} vs {packaged}")
            return 1

    template = (
        ROOT / "openspec/schemas/keel-spec-driven/templates/tasks.md"
    ).read_text(encoding="utf-8")
    for marker in ("## Invalidates", "- None.", "- I1:"):
        if marker not in template:
            report(f"{label} tasks template lacks the invalidation section: {marker}")
            return 1

    schema = (
        ROOT / "openspec/schemas/keel-spec-driven/schema.yaml"
    ).read_text(encoding="utf-8")
    for marker in ("## Invalidates", "Updated by:", "Discard reason:"):
        if marker not in schema:
            report(
                f"{label} authoring instruction does not describe the "
                f"invalidation section: {marker}"
            )
            return 1

    resident = resident_session_start_section(ROOT / "AGENTS.md")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    if resident is None:
        report(f"{label} resident AGENTS.md has no Session Start section.")
        return 1
    for marker in ("## Invalidates", "## Expectation Coverage"):
        if marker not in agents:
            report(f"{label} resident protocol does not name {marker}.")
            return 1

    # An author who scaffolds and fills in the tasks must not additionally have
    # to discover this section, so the template's own answer has to satisfy the
    # gate. Placeholders are filled generically; the assertion is narrow on
    # purpose — no invalidation problem may survive.
    filled = re.sub(r"<!--[\s\S]*?-->", "", template)
    filled = filled.replace("<strategy>", "evidence-first")
    filled = re.sub(r"<[^<>\n]+>", "concrete authored value", filled)
    with tempfile.TemporaryDirectory(
        prefix="keel-invalidation-surface-", ignore_cleanup_errors=True
    ) as raw:
        repo = Path(raw) / "scaffold"
        write_text(repo / "openspec/changes/demo/tasks.md", filled)
        started = run_keel(
            repo, "gate", "task-start", ".",
            "--change", "demo", "--task", "1.1", "--json", "--no-guard",
        )
        payload = json.loads(started.stdout) if started.stdout.strip() else {}
        offenders = [
            item for item in payload.get("problems", [])
            if str(item.get("code", "")).startswith("invalidation-")
        ]
        if offenders:
            report(
                f"{label} a filled-in scaffold still fails the invalidation "
                "gate, so the template's own answer is not usable."
            )
            report(repr(offenders))
            return 1

    report(f"{label} scenario passed.")
    return 0


def validate_task_contract_core_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-task-contract-") as raw_tmp:
        repo = Path(raw_tmp)
        tasks_path = repo / "openspec/changes/demo/tasks.md"
        write_text(
            tasks_path,
            task_contract_fixture(mode="diagnose-only", touch=("none",)),
        )
        diagnose_only = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if (
            diagnose_only.returncode != 0
            or json.loads(diagnose_only.stdout).get("status") != "pass"
        ):
            report("task-contract-core rejected diagnose-only Touch: none.")
            report((diagnose_only.stderr or diagnose_only.stdout).strip())
            return 1

        write_text(
            tasks_path,
            task_contract_fixture(mode="build-mode"),
        )
        unsupported_mode = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        unsupported_payload = json.loads(unsupported_mode.stdout)
        if (
            unsupported_mode.returncode != 3
            or unsupported_payload.get("status") != "fail"
            or not any(
                item.get("code") == "unsupported-mode"
                and "build-mode" in item.get("message", "")
                for item in unsupported_payload.get("problems", [])
            )
        ):
            report("task-contract-core accepted an unsupported Mode value.")
            report((unsupported_mode.stderr or unsupported_mode.stdout).strip())
            return 1

        write_text(
            tasks_path,
            task_contract_fixture(touch=()),
        )
        missing_touch = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        missing_touch_payload = json.loads(missing_touch.stdout)
        if (
            missing_touch.returncode != 3
            or not any(
                item.get("code") == "invalid-touch"
                for item in missing_touch_payload.get("problems", [])
            )
        ):
            report("task-contract-core accepted implementation without Touch.")
            report((missing_touch.stderr or missing_touch.stdout).strip())
            return 1

        write_text(
            tasks_path,
            task_contract_fixture(
                commands=("X1: node test.js",),
                evidence=("X1: pending",),
            ),
        )
        malformed_label = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        malformed_payload = json.loads(malformed_label.stdout)
        if (
            malformed_label.returncode != 3
            or not any(
                item.get("code") == "invalid-command-label"
                for item in malformed_payload.get("problems", [])
            )
        ):
            report("task-contract-core accepted a malformed M label.")
            report((malformed_label.stderr or malformed_label.stdout).strip())
            return 1

        inline_malformed_task = task_contract_fixture(
            commands=(),
            evidence=("X1: pending",),
        ).replace(
            "  - Commands:\n",
            "  - Commands: X1: node test.js\n",
        )
        write_text(tasks_path, inline_malformed_task)
        inline_malformed = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        inline_malformed_payload = json.loads(inline_malformed.stdout)
        if (
            inline_malformed.returncode != 3
            or not any(
                item.get("code") == "invalid-command-label"
                for item in inline_malformed_payload.get("problems", [])
            )
        ):
            report("task-contract-core accepted an inline malformed M label.")
            report((inline_malformed.stderr or inline_malformed.stdout).strip())
            return 1

        write_text(
            tasks_path,
            task_contract_fixture(
                commands=("M1: node first.js", "M1: node second.js"),
            ),
        )
        duplicate_label = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        duplicate_payload = json.loads(duplicate_label.stdout)
        if (
            duplicate_label.returncode != 3
            or not any(
                item.get("code") == "duplicate-command-label"
                and "M1" in item.get("message", "")
                for item in duplicate_payload.get("problems", [])
            )
        ):
            report("task-contract-core accepted a duplicate M label.")
            report((duplicate_label.stderr or duplicate_label.stdout).strip())
            return 1

        write_text(
            tasks_path,
            task_contract_fixture(
                commands=("M1: node first.js", "M3: node third.js"),
                evidence=("M1: pending", "M3: pending"),
            ),
        )
        noncontiguous_label = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        noncontiguous_payload = json.loads(noncontiguous_label.stdout)
        if (
            noncontiguous_label.returncode != 3
            or not any(
                item.get("code") == "noncontiguous-command-label"
                for item in noncontiguous_payload.get("problems", [])
            )
        ):
            report("task-contract-core accepted non-contiguous M labels.")
            report((noncontiguous_label.stderr or noncontiguous_label.stdout).strip())
            return 1

        write_text(
            tasks_path,
            task_contract_fixture(evidence=("M2: pending",)),
        )
        disconnected_evidence = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        disconnected_payload = json.loads(disconnected_evidence.stdout)
        if (
            disconnected_evidence.returncode != 3
            or not any(
                item.get("code") == "evidence-label-mismatch"
                and "M1" in item.get("message", "")
                and "M2" in item.get("message", "")
                for item in disconnected_payload.get("problems", [])
            )
        ):
            report("task-contract-core accepted disconnected Evidence labels.")
            report(
                (disconnected_evidence.stderr or disconnected_evidence.stdout).strip()
            )
            return 1

    report("task-contract-core scenario passed.")
    return 0


def task_capsule_expanded_fixture() -> str:
    # No `Owner:`: since #413 the capsule carries an owner only when a task
    # authors one, so writing the old default is no longer the same as omitting it.
    return task_contract_fixture().replace("  - Owner: keel-agent\n", "", 1).replace(
        "E1: public behavior",
        "E1: Public behavior passes.",
    ).replace(
        "  - Acceptance:\n",
        "  - Verification Strategy: evidence-first\n"
        "  - Verification Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "  - Acceptance:\n",
    )


def record_contract_anchor(repo: Path, change: str, task: str = "1.1") -> bool:
    """Run `task-start --record` so a fixture can reach completion.

    Completion refuses a task whose `Contract` anchor holds no compiled
    fingerprint (issue #30), so a scenario that only wanted to exercise
    task-complete still has to start the task first. That is the real loop, not
    a workaround: a task that was never started is not a task being completed.
    """
    result = run_keel(
        repo,
        "gate",
        "task-start",
        "--change",
        change,
        "--task",
        task,
        "--record",
        "--no-guard",
        "--json",
    )
    return result.returncode == 0


def validate_non_concrete_verify_diagnostic_scenario() -> int:
    """A compact v4 task whose Verify carries an unfilled token must be told so.

    Regression for issue #7 example 1: the compact/expanded decision reads
    isConcrete(Verify), so one unfilled token used to select the expanded v3
    required-field set and report fields the author never declared.
    """
    v3_only_fields = (
        "Owner",
        "Read",
        "Commands",
        "Acceptance",
        "Candidate Boundary",
        "Report",
    )
    with tempfile.TemporaryDirectory(prefix="keel-non-concrete-verify-") as raw_tmp:
        repo = Path(raw_tmp)
        # A bare token in prose. The reporter's own case wrote it inside an
        # inline code span, which the inline-code-is-concrete scenario now
        # covers as legitimately filled; what must still be reported is a token
        # standing unfenced in the text.
        task = task_capsule_compact_fixture().replace(
            "    - M1: node test.js\n",
            "    - M1: node test.js writes ledger/scan-log/<date>.md\n",
        )
        write_text(repo / "openspec/changes/demo/tasks.md", task)
        started = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        payload = json.loads(started.stdout)
        problems = payload.get("problems", [])
        codes = {problem.get("code") for problem in problems}
        if "non-concrete-verify" not in codes:
            report(
                "non-concrete-verify-diagnostic: an unfilled token in Verify did "
                "not produce the non-concrete-verify diagnostic."
            )
            report(started.stdout.strip())
            return 1
        named = [
            problem
            for problem in problems
            if problem.get("code") == "non-concrete-verify"
            and "<date>" in problem.get("message", "")
        ]
        if not named:
            report(
                "non-concrete-verify-diagnostic: the diagnostic did not name the "
                "matched token."
            )
            report(started.stdout.strip())
            return 1
        leaked = sorted(
            field
            for problem in problems
            if problem.get("code") == "missing-field"
            for field in v3_only_fields
            if problem.get("message", "").startswith(f"{field} must be concrete")
        )
        if leaked:
            report(
                "non-concrete-verify-diagnostic: expanded v3 fields were still "
                f"reported as missing: {', '.join(leaked)}."
            )
            report(started.stdout.strip())
            return 1
        # A task with no Verify at all must not be reported as carrying a token
        # it never wrote. What it is reported as instead — one missing
        # verification form rather than the expanded v3 set — belongs to the
        # absent-verification-form-is-one-problem scenario.
        bare = task_capsule_compact_fixture()
        for block in (
            "  - Verify:\n    - Strategy: evidence-first\n    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n    - M1: node test.js\n",
        ):
            bare = bare.replace(block, "")
        write_text(repo / "openspec/changes/bare/tasks.md", bare)
        bare_started = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "bare",
            "--task",
            "1.1",
            "--json",
        )
        bare_payload = json.loads(bare_started.stdout)
        bare_codes = {
            problem.get("code") for problem in bare_payload.get("problems", [])
        }
        if "non-concrete-verify" in bare_codes:
            report(
                "non-concrete-verify-diagnostic: a task with no Verify was "
                "reported as carrying an unfilled token."
            )
            report(bare_started.stdout.strip())
            return 1
    if "non-concrete-verify-diagnostic" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "non-concrete-verify-diagnostic: the scenario registry does not "
            "include it."
        )
        return 1
    report("non-concrete-verify-diagnostic scenario passed.")
    return 0


def validate_inline_code_is_concrete_scenario() -> int:
    """Unfilled-token forms inside inline code spans are documented patterns.

    Regression for issue #7 example 1: the reporter's Verify wrote a filename
    pattern inside backticks and it was still judged unfilled. The exemption
    covers every token form, not only angle brackets, because prose naming the
    keywords is equally common — see
    keel/archive/follow-ups/2026-07-27-unfilled-token-keywords.md.
    """
    fenced_m1 = (
        "    - M1: node test.js writes `ledger/scan-log/<date>.md`, skips a "
        "`TODO` marker, and leaves `TBD` rows alone\n"
    )
    bare_m1 = "    - M1: node test.js writes ledger/scan-log/<date>.md\n"
    with tempfile.TemporaryDirectory(prefix="keel-inline-code-") as raw_tmp:
        repo = Path(raw_tmp)
        write_text(
            repo / "openspec/changes/fenced/tasks.md",
            task_capsule_compact_fixture().replace(
                "    - M1: node test.js\n", fenced_m1
            ),
        )
        fenced = run_keel(
            repo, "gate", "task-start", "--change", "fenced", "--task", "1.1", "--json"
        )
        if fenced.returncode != 0:
            report(
                "inline-code-is-concrete: token forms inside inline code spans "
                "were still judged unfilled."
            )
            report((fenced.stdout or fenced.stderr).strip())
            return 1
        # The same token outside inline code must still be caught, otherwise the
        # exemption has swallowed the check it is narrowing.
        write_text(
            repo / "openspec/changes/bare/tasks.md",
            task_capsule_compact_fixture().replace(
                "    - M1: node test.js\n", bare_m1
            ),
        )
        bare = run_keel(
            repo, "gate", "task-start", "--change", "bare", "--task", "1.1", "--json"
        )
        bare_codes = {
            problem.get("code")
            for problem in json.loads(bare.stdout).get("problems", [])
        }
        if "non-concrete-verify" not in bare_codes:
            report(
                "inline-code-is-concrete: a bare token outside inline code was "
                "no longer reported as unfilled."
            )
            report(bare.stdout.strip())
            return 1
        # Stripping runs after the emptiness test, so a field that is entirely
        # one code span must not read as empty.
        write_text(
            repo / "openspec/changes/whole/tasks.md",
            task_capsule_compact_fixture()
            .replace("    - M1: node test.js\n", "    - M1: `node test.js`\n")
            .replace("    - src/feature.js\n", "    - `src/feature.js`\n"),
        )
        whole = run_keel(
            repo, "gate", "task-start", "--change", "whole", "--task", "1.1", "--json"
        )
        if whole.returncode != 0:
            report(
                "inline-code-is-concrete: a field whose whole value is one "
                "inline code span was judged empty."
            )
            report((whole.stdout or whole.stderr).strip())
            return 1
    if "inline-code-is-concrete" not in {name for name, _ in registry.SCENARIOS}:
        report("inline-code-is-concrete: the scenario registry does not include it.")
        return 1
    report("inline-code-is-concrete scenario passed.")
    return 0


def validate_marker_words_in_capitals_scenario() -> int:
    """Issue #271: a marker word reads as a slot only in capitals.

    `task-complete` refused Evidence reading "post and todo" because the
    unfilled-slot test matched its marker words in any case, so the name of a
    `keel chat` record kind read as an unfilled slot. Lowercase prose is
    concrete; `TODO`, `PLACEHOLDER` and `<value>` outside inline code are not.
    """
    def start(repo: Path, change: str, m1: str):
        write_text(
            repo / f"openspec/changes/{change}/tasks.md",
            task_capsule_compact_fixture().replace(
                "    - M1: node test.js\n", f"    - M1: {m1}\n"
            ),
        )
        return run_keel(
            repo, "gate", "task-start", "--change", change, "--task", "1.1", "--json"
        )

    with tempfile.TemporaryDirectory(prefix="keel-marker-words-") as raw_tmp:
        repo = Path(raw_tmp)
        prose = start(repo, "prose", "node test.js lists each todo and its placeholder text")
        if prose.returncode != 0:
            report(
                "marker-words-in-capitals: a check naming a todo and a "
                "placeholder in lowercase prose was judged unfilled."
            )
            report((prose.stdout or prose.stderr).strip())
            return 1

        # The reporter's shape: Evidence written after the task started.
        write_text(
            repo / "openspec/changes/evidence/tasks.md", task_capsule_compact_fixture()
        )
        if not record_contract_anchor(repo, "evidence"):
            report("marker-words-in-capitals: the fixture could not record its anchor.")
            return 1
        path = repo / "openspec/changes/evidence/tasks.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "    - M1: pending\n",
                "    - M1: pass. With `--ack` on post and todo, the record is acknowledged.\n",
            ),
            encoding="utf-8",
        )
        completed = run_keel(
            repo, "gate", "task-complete", "--change", "evidence", "--task", "1.1", "--json"
        )
        slots = [
            problem.get("message", "")
            for problem in json.loads(completed.stdout).get("problems", [])
            if "unfilled" in problem.get("message", "")
        ]
        if slots:
            report(
                "marker-words-in-capitals: Evidence reading 'post and todo' was "
                f"refused as an unfilled slot: {slots}"
            )
            return 1

        for change, m1, token in (
            ("todo", "node test.js TODO", "TODO"),
            ("upper", "node test.js PLACEHOLDER", "PLACEHOLDER"),
            ("angle", "node test.js <value>", "<value>"),
        ):
            result = start(repo, change, m1)
            problems = json.loads(result.stdout).get("problems", [])
            named = [
                problem
                for problem in problems
                if problem.get("code") == "non-concrete-verify"
                and f"`{token}`" in problem.get("message", "")
            ]
            if not named:
                report(
                    f"marker-words-in-capitals: a bare {token} was not reported "
                    "as non-concrete-verify naming it."
                )
                report(result.stdout.strip())
                return 1
    if "marker-words-in-capitals" not in {name for name, _ in registry.SCENARIOS}:
        report("marker-words-in-capitals: the scenario registry does not include it.")
        return 1
    report("marker-words-in-capitals scenario passed.")
    return 0


def validate_covers_separator_collision_scenario() -> int:
    """Issue #7 example 2: a requirement name containing the hierarchy separator.

    Both spellings the reporter tried must fail loudly and say why. Keeping the
    slash over-segments the reference, which used to compile to an unlinked
    legacy-task-reference and PASS; removing it resolves nothing and used to
    give a generic message.
    """
    collide = "Continue or downgrade or switch/window criteria"

    def spec(requirement: str) -> str:
        return (
            "# cap\n\n## Purpose\nDemo.\n\n"
            f"### Requirement: {requirement}\nText.\n\n"
            "#### Scenario: Criteria cover three outcomes\n"
            "- **WHEN** a thing\n- **THEN** another\n"
        )

    def tasks(reference: str) -> str:
        return task_capsule_compact_fixture().replace(
            "    - E1: Public behavior passes.\n", f"    - {reference}\n"
        )

    with tempfile.TemporaryDirectory(prefix="keel-covers-collision-") as raw_tmp:
        repo = Path(raw_tmp)
        write_text(repo / "openspec/specs/collide-cap/spec.md", spec(collide))
        write_text(repo / "openspec/specs/clean-cap/spec.md", spec("Plain name"))

        def start(change: str, reference: str):
            write_text(repo / f"openspec/changes/{change}/tasks.md", tasks(reference))
            result = run_keel(
                repo, "gate", "task-start", "--change", change, "--task", "1.1",
                "--json",
            )
            return json.loads(result.stdout)

        # The reporter's correct spelling: over-segmented, capability is real.
        kept = start(
            "kept",
            f"collide-cap / {collide} / Criteria cover three outcomes",
        )
        kept_messages = " ".join(
            problem.get("message", "") for problem in kept.get("problems", [])
        )
        kept_kinds = {
            entry.get("kind")
            for entry in kept.get("contract", {})
            .get("capsule", {})
            .get("authority", [])
        }
        if kept.get("status") != "fail" or "legacy-task-reference" in kept_kinds:
            report(
                "covers-separator-collision: an over-segmented reference to a "
                "real capability still degraded to a free-text reference."
            )
            report(json.dumps(kept.get("problems"), ensure_ascii=False))
            return 1
        if collide not in kept_messages or "separator" not in kept_messages:
            report(
                "covers-separator-collision: the over-segmented diagnostic did "
                "not name the colliding requirement."
            )
            report(kept_messages)
            return 1
        # The reporter's fallback spelling: resolves to nothing.
        trimmed = start(
            "trimmed",
            "collide-cap / Continue or downgrade or switchwindow criteria"
            " / Criteria cover three outcomes",
        )
        trimmed_messages = " ".join(
            problem.get("message", "") for problem in trimmed.get("problems", [])
        )
        if collide not in trimmed_messages:
            report(
                "covers-separator-collision: the unresolved diagnostic did not "
                "name the colliding requirement."
            )
            report(trimmed_messages)
            return 1
        # A capability with no colliding name receives no separator hint. It
        # still gets the unresolved diagnostic, which since 5.21.0 names what
        # the spec holds instead; what is asserted here is only that the
        # separator explanation stays with the capability that has one.
        plain = start(
            "plain", "clean-cap / No such requirement / No such scenario"
        )
        plain_messages = " ".join(
            problem.get("message", "") for problem in plain.get("problems", [])
        )
        if "separator" in plain_messages:
            report(
                "covers-separator-collision: a capability with no colliding "
                "name still received the separator hint."
            )
            report(plain_messages)
            return 1
        # Free text that merely contains slashes is not a spec reference.
        free = start("free", "E1: writes a/b/c and passes")
        free_kinds = {
            entry.get("kind")
            for entry in free.get("contract", {})
            .get("capsule", {})
            .get("authority", [])
        }
        if free.get("status") != "pass" or free_kinds != {"legacy-task-reference"}:
            report(
                "covers-separator-collision: free text containing slashes was "
                "no longer accepted as a legacy reference."
            )
            report(json.dumps(free.get("problems"), ensure_ascii=False))
            return 1
    if "covers-separator-collision" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "covers-separator-collision: the scenario registry does not include it."
        )
        return 1
    report("covers-separator-collision scenario passed.")
    return 0


def validate_unresolved_covers_names_what_failed_scenario() -> int:
    """Issue #49, 2026-08-02 supplement: an unresolved reference said only that.

    A two-segment `Covers` reference whose second segment is a Scenario name is
    the most common way to write the notation wrong — the shipped task template
    taught it — and the spec being read holds that exact name one heading level
    down. The refusal reported the reference back and nothing else, while the
    hierarchy sentence sat thirty lines above in the same function, reachable
    only by over-segmenting. Every case below still fails; only what it says
    changes, and the last case asserts that.
    """
    spec = (
        "# demo-cap\n\n## Purpose\nDemo.\n\n"
        "### Requirement: The store validates itself\n"
        "Keel MUST validate the published store.\n\n"
        "#### Scenario: A published store passes the pinned validator\n"
        "- **WHEN** the pinned validator runs\n"
        "- **THEN** the published store passes\n"
        "- **AND THEN** the pin is reported\n\n"
        "#### Scenario: A shared scenario name\n"
        "- **WHEN** a thing\n- **THEN** another\n\n"
        "### Requirement: Another requirement\n"
        "Keel MUST do the other thing.\n\n"
        "#### Scenario: A shared scenario name\n"
        "- **WHEN** a thing\n- **THEN** another\n"
    )

    with tempfile.TemporaryDirectory(prefix="keel-covers-what-failed-") as raw:
        repo = Path(raw)
        write_text(repo / "openspec/specs/demo-cap/spec.md", spec)

        def start(change: str, reference: str) -> dict:
            write_text(
                repo / f"openspec/changes/{change}/tasks.md",
                task_capsule_compact_fixture().replace(
                    "    - E1: Public behavior passes.\n", f"    - {reference}\n"
                ),
            )
            result = run_keel(
                repo, "gate", "task-start", "--change", change, "--task", "1.1",
                "--json",
            )
            return json.loads(result.stdout)

        def refusal(change: str, reference: str) -> tuple[dict, str]:
            payload = start(change, reference)
            message = " ".join(
                problem.get("message", "")
                for problem in payload.get("problems", [])
            )
            return payload, message

        # The reported case: the Scenario name written where a Requirement goes.
        scenario_ref = "demo-cap / A published store passes the pinned validator"
        offered, offered_message = refusal("offered", scenario_ref)
        corrected = (
            "demo-cap / The store validates itself"
            " / A published store passes the pinned validator"
        )
        if offered.get("status") != "fail":
            report(
                "unresolved-covers-names-what-failed: a Scenario named as a "
                "Requirement stopped being refused."
            )
            report(json.dumps(offered.get("problems"), ensure_ascii=False))
            return 1
        if not any(
            problem.get("code") == "unresolved-covers"
            for problem in offered.get("problems", [])
        ):
            report(
                "unresolved-covers-names-what-failed: the refusal no longer "
                "carries the unresolved-covers code."
            )
            report(json.dumps(offered.get("problems"), ensure_ascii=False))
            return 1
        if (
            "The store validates itself" not in offered_message
            or "Scenario" not in offered_message
            or corrected not in offered_message
        ):
            report(
                "unresolved-covers-names-what-failed: the diagnostic did not "
                "name the Requirement the Scenario belongs to, did not call it "
                "a Scenario, or did not spell the corrected reference."
            )
            report(offered_message)
            return 1

        # A name the capability declares nowhere: say the spec was read.
        absent, absent_message = refusal("absent", "demo-cap / No such name")
        if absent.get("status") != "fail":
            report(
                "unresolved-covers-names-what-failed: a name the capability does "
                "not declare stopped being refused."
            )
            report(json.dumps(absent.get("problems"), ensure_ascii=False))
            return 1
        if (
            "No such name" not in absent_message
            or "hierarchy is capability / requirement" not in absent_message
        ):
            report(
                "unresolved-covers-names-what-failed: a name the spec does not "
                "declare was not reported as read, or the hierarchy was withheld."
            )
            report(absent_message)
            return 1

        # A capability with no spec at all is a different failure.
        nospec, nospec_message = refusal("nospec", "nosuch-cap / Whatever")
        if nospec.get("status") != "fail":
            report(
                "unresolved-covers-names-what-failed: a capability with no spec "
                "stopped being refused."
            )
            report(json.dumps(nospec.get("problems"), ensure_ascii=False))
            return 1
        if (
            "nosuch-cap" not in nospec_message
            or "no spec" not in nospec_message.lower()
        ):
            report(
                "unresolved-covers-names-what-failed: a capability with no spec "
                "was not distinguished from a name the spec lacks."
            )
            report(nospec_message)
            return 1

        # Ambiguous: the same Scenario name under two Requirements has no single
        # correction, so none is offered.
        shared, shared_message = refusal("shared", "demo-cap / A shared scenario name")
        if shared.get("status") != "fail":
            report(
                "unresolved-covers-names-what-failed: an ambiguous Scenario name "
                "stopped being refused."
            )
            report(json.dumps(shared.get("problems"), ensure_ascii=False))
            return 1
        if (
            "The store validates itself" not in shared_message
            or "Another requirement" not in shared_message
        ):
            report(
                "unresolved-covers-names-what-failed: an ambiguous Scenario name "
                "did not name the Requirements it appears under."
            )
            report(shared_message)
            return 1
        if "Write it as" in shared_message:
            report(
                "unresolved-covers-names-what-failed: a corrected reference was "
                "offered for a Scenario name that has more than one parent."
            )
            report(shared_message)
            return 1

        # What resolves is unchanged. This is the assertion that must not be
        # dropped: reading more of the spec on the failure path is the direction
        # in which a refusal could accidentally become a resolution.
        resolves = start("resolves", "demo-cap / The store validates itself")
        capsule = resolves.get("contract", {}).get("capsule", {})
        authority = capsule.get("authority", [])
        if (
            resolves.get("status") != "pass"
            or resolves.get("problems")
            or len(authority) != 1
            or authority[0].get("kind") != "requirement"
            or not authority[0]
            .get("source", "")
            .endswith("specs/demo-cap/spec.md#Requirement:The store validates itself")
        ):
            report(
                "unresolved-covers-names-what-failed: a reference that resolves "
                "no longer compiles to the same authority."
            )
            report(json.dumps(resolves, ensure_ascii=False)[:2000])
            return 1

    if "unresolved-covers-names-what-failed" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "unresolved-covers-names-what-failed: the scenario registry does not "
            "include it."
        )
        return 1
    report("unresolved-covers-names-what-failed scenario passed.")
    return 0


def validate_unresolved_authority_names_field_scenario() -> int:
    """Issue #7 example 3: the diagnostic must name what it actually reads.

    The check reads only the task's `Pre-authorized fallback:` line. The old
    wording said "documented design authority", which sent authors to design.md
    where the answer usually already was.
    """
    with tempfile.TemporaryDirectory(prefix="keel-unresolved-authority-") as raw:
        repo = Path(raw)
        # design.md documents Q1 and an authorized fallback in prose, which is
        # exactly the state the reporter was in when the message misdirected.
        write_text(
            repo / "openspec/changes/demo/design.md",
            "## Questions\n\nQ1 — Should the widget retry on timeout?\n\n"
            "Authorized fallback: retry twice with backoff, then stop.\n",
        )
        without = task_capsule_compact_fixture().replace(
            "    - E1: Public behavior passes.\n", "    - Q1\n"
        )
        write_text(repo / "openspec/changes/demo/tasks.md", without)
        result = run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
        )
        payload = json.loads(result.stdout)
        messages = [
            problem.get("message", "")
            for problem in payload.get("problems", [])
            if problem.get("code") == "unresolved-authority"
        ]
        if not messages:
            report(
                "unresolved-authority-names-field: a Q reference with no "
                "authorized fallback produced no unresolved-authority diagnostic."
            )
            report(result.stdout.strip())
            return 1
        message = messages[0]
        required = ("Autonomy boundary:", "Pre-authorized fallback:", "design.md")
        missing = [needle for needle in required if needle not in message]
        if missing:
            report(
                "unresolved-authority-names-field: the diagnostic omitted "
                f"{', '.join(missing)}."
            )
            report(message)
            return 1
        if "documented design authority" in message:
            report(
                "unresolved-authority-names-field: the diagnostic still points "
                "at design.md as the thing to add."
            )
            report(message)
            return 1
        # Doing literally what the message asks must clear it.
        with_fallback = without.replace(
            "    - Pre-authorized fallback: none\n",
            "    - Pre-authorized fallback: retry twice with backoff then stop;"
            " evidence is the retry log\n",
        )
        write_text(repo / "openspec/changes/fixed/tasks.md", with_fallback)
        write_text(
            repo / "openspec/changes/fixed/design.md",
            "## Questions\n\nQ1 — Should the widget retry on timeout?\n",
        )
        fixed = run_keel(
            repo, "gate", "task-start", "--change", "fixed", "--task", "1.1", "--json"
        )
        if fixed.returncode != 0:
            report(
                "unresolved-authority-names-field: following the diagnostic did "
                "not clear it."
            )
            report((fixed.stdout or fixed.stderr).strip())
            return 1
    if "unresolved-authority-names-field" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "unresolved-authority-names-field: the scenario registry does not "
            "include it."
        )
        return 1
    report("unresolved-authority-names-field scenario passed.")
    return 0


TASK_SHAPE_TEMPLATE = """## 1. Work

- [ ] 1.1 First half
  - Covers:
    - E1: behavior
  - Touch:
{touch_one}
  - Verify:
    - Strategy: {strategy_one}
    - M1: the first half is observable through the public interface
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

- [ ] 1.2 Second half
  - Covers:
    - E2: behavior
  - Touch:
{touch_two}
  - Verify:
    - Strategy: {strategy_two}
    - M1: the second half is observable through the public interface
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Invalidates

- None.

## Expectation Coverage

- E1: behavior. Covered by: 1.1
- E2: behavior. Covered by: 1.2
"""


def task_shape_tasks(
    touch_one: list[str],
    touch_two: list[str],
    strategy_one: str = "vertical-tdd",
    strategy_two: str = "vertical-tdd",
) -> str:
    def block(entries: list[str]) -> str:
        return "\n".join(f"    - {entry}" for entry in entries)

    return TASK_SHAPE_TEMPLATE.format(
        touch_one=block(touch_one),
        touch_two=block(touch_two),
        strategy_one=strategy_one,
        strategy_two=strategy_two,
    )


def validate_task_shape_warning_scenario() -> int:
    """Issue #41: authoring cannot tell when two tasks are one behavior.

    `the-runtime-says-which-version-it-is` was authored with tasks 1.1 and 1.2
    declaring an identical Touch and the same red-green strategy. Both passed
    `task-start` and the Slice Start Gate, and the split was not executable:
    implementing 1.1 alone broke a shipping scenario, and once it was right two
    of 1.2's three checks were already green, leaving no honest red. They were
    merged mid-execution, at the cost of a reauthorization cycle the Slice
    Start Gate exists to make unnecessary.

    A warning rather than a verdict. A genuine vertical split can share files,
    the judgment is semantic, and there is no way to acknowledge a
    `needs-review` — turning the signal into a refusal would leave a legitimate
    split unstartable, which is worse than the problem.
    """
    label = "task-shape-warning"
    shared = ["src/feature.js", "scripts/validate_plugin.py"]

    with tempfile.TemporaryDirectory(prefix="keel-task-shape-") as raw:
        repo = Path(raw).resolve()
        tasks = repo / "openspec/changes/demo/tasks.md"
        write_text(repo / "openspec/changes/demo/proposal.md", "# Proposal\n")

        def start(content: str):
            write_text(tasks, content)
            return run_keel(
                repo, "gate", "task-start",
                "--change", "demo", "--task", "1.1", "--json", "--no-guard",
            )

        def warnings_of(result) -> list[str]:
            payload = json.loads(result.stdout) if result.stdout else {}
            return [str(item) for item in payload.get("warnings", [])]

        # M1 — the shape that produced the merge.
        matched = start(task_shape_tasks(shared, list(shared)))
        matched_warnings = warnings_of(matched)
        shape_warnings = [w for w in matched_warnings if "1.2" in w]
        if not shape_warnings:
            report(
                f"{label} M1 two tasks with an identical Touch set under a "
                "red-green strategy produced no warning naming the other task. "
                f"Warnings were: {matched_warnings}"
            )
            return 1

        # M2 — a signal, not a verdict.
        payload = json.loads(matched.stdout) if matched.stdout else {}
        if payload.get("status") != "pass":
            report(
                f"{label} M2 the task-shape signal changed the gate's status to "
                f"{payload.get('status')!r}; it must stay a warning."
            )
            return 1
        if matched.returncode != 0:
            report(
                f"{label} M2 the task-shape signal changed the exit code to "
                f"{matched.returncode}; it must stay 0 so the task starts."
            )
            return 1

        # M3 — the two cases that must stay silent.
        differing = start(
            task_shape_tasks(shared, ["src/other.js", "docs/notes.md"])
        )
        if [w for w in warnings_of(differing) if "1.2" in w]:
            report(
                f"{label} M3 a task whose Touch set differs from every other "
                f"task was warned about: {warnings_of(differing)}"
            )
            return 1
        not_red_green = start(
            task_shape_tasks(
                shared, list(shared),
                strategy_one="evidence-first", strategy_two="evidence-first",
            )
        )
        if [w for w in warnings_of(not_red_green) if "1.2" in w]:
            report(
                f"{label} M3 a matching Touch set under a strategy that is not "
                f"red-green was warned about: {warnings_of(not_red_green)}"
            )
            return 1

    # M4 — the same question at completion, in both copies.
    canonical = ROOT / "src/skills/review-checklist/SKILL.md"
    projected = ROOT / "plugins/keel/skills/review-checklist/SKILL.md"
    if canonical.read_bytes() != portable_projection_bytes(projected):
        report(
            f"{label} M4 the portable checklist and its plugin projection are "
            "not byte-identical."
        )
        return 1
    checklist = canonical.read_text(encoding="utf-8")
    if "one behavior" not in checklist:
        report(
            f"{label} M4 review-checklist does not ask whether two tasks "
            "turned out to be one behavior."
        )
        return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_completion_requires_a_recorded_anchor_scenario() -> int:
    """Issue #30: an unrecorded anchor made the drift guarantee conditional.

    `anchoredFingerprint` returns null for a non-digest value and completion
    then skipped the comparison entirely, so a task with `Contract: pending`
    passed with zero problems. It could be implemented against one contract,
    have its Touch or Verify rewritten mid-flight, and complete clean — purely
    by never running `task-start --record`. 5.3.7 closed the inference path;
    this closes the explicitly named one.
    """
    header = "# Tasks\n\n## Invalidates\n\n- None.\n\n"

    def task(contract: str) -> str:
        return (
            "- [ ] 1.1 Exercise task contract\n"
            "  - Covers:\n"
            "    - E1: Public behavior passes.\n"
            "  - Touch:\n"
            "    - src/feature.js\n"
            "  - Verify:\n"
            "    - Strategy: evidence-first\n"
            "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
            "    - M1: node test.js asserts the recorded feed status\n"
            "  - Evidence:\n"
            f"    - Contract: {contract}\n"
            "    - M1: the suite passed\n"
            "    - Review:\n"
            "      - Status: pass\n"
            "      - Acceptance check: behavior asserted at the interface\n"
            "      - Scope check: only Touch files changed\n"
            "      - Findings: none\n"
            "    - Blocker: none\n"
        )

    with tempfile.TemporaryDirectory(prefix="keel-anchor-required-") as raw:
        repo = Path(raw)
        write_text(repo / "openspec/changes/unrecorded/tasks.md", header + task("pending"))

        def gate(change: str, stage: str) -> dict:
            return json.loads(
                run_keel(
                    repo,
                    "gate",
                    stage,
                    "--change",
                    change,
                    "--task",
                    "1.1",
                    "--json",
                ).stdout
            )

        payload = gate("unrecorded", "task-complete")
        if payload.get("status") == "pass":
            report(
                "completion-requires-a-recorded-anchor: an explicitly named task "
                "with `Contract: pending` passed task-complete, so the "
                "fingerprint comparison still compares nothing."
            )
            return 1
        named = [
            problem.get("message", "")
            for problem in payload.get("problems", [])
            if problem.get("code") == "missing-contract-anchor"
        ]
        if not named:
            report(
                "completion-requires-a-recorded-anchor: the task did not pass, "
                "but no missing-contract-anchor diagnostic explained why."
            )
            for problem in payload.get("problems", []):
                report(f"  {problem.get('code')}: {problem.get('message')}")
            return 1
        for needle in ("Contract", "--record"):
            if needle not in named[0]:
                report(
                    "completion-requires-a-recorded-anchor: the diagnostic did "
                    f"not name {needle}."
                )
                report(named[0])
                return 1
        # Doing what the diagnostic asks must clear it — and the anchor has to be
        # the one this change compiles to. Until 5.10.0 this fixture recorded
        # against `unrecorded` and anchored `recorded`, two different change
        # directories, and passed anyway: a compiled capsule names its own source
        # paths, so those values were never equal. That it passed is direct
        # evidence the comparison it claims to exercise did not exist (issue
        # #37). Both halves are asserted below.
        started = gate("unrecorded", "task-start")
        fingerprint = started.get("contract", {}).get("fingerprint", {}).get("value")
        if not fingerprint:
            report(
                "completion-requires-a-recorded-anchor: task-start returned no "
                "fingerprint to record."
            )
            return 1
        if any(
            problem.get("code") == "missing-contract-anchor"
            for problem in started.get("problems", [])
        ):
            report(
                "completion-requires-a-recorded-anchor: task-start reported the "
                "missing anchor, but it runs before one can exist."
            )
            return 1
        write_text(repo / "openspec/changes/recorded/tasks.md", header + task("pending"))
        own = (
            gate("recorded", "task-start")
            .get("contract", {})
            .get("fingerprint", {})
            .get("value")
        )
        if not own:
            report(
                "completion-requires-a-recorded-anchor: task-start returned no "
                "fingerprint for the change being completed."
            )
            return 1
        if own == fingerprint:
            report(
                "completion-requires-a-recorded-anchor: two changes with "
                "identical task text compiled to the same fingerprint, so the "
                "foreign-anchor half of this scenario cannot bite."
            )
            return 1
        write_text(
            repo / "openspec/changes/recorded/tasks.md",
            header + task(f"keel-task-capsule/v1 sha256:{fingerprint}"),
        )
        foreign = gate("recorded", "task-complete")
        if foreign.get("status") == "pass":
            report(
                "completion-requires-a-recorded-anchor: a well-formed digest "
                "compiled from a different change passed task-complete, so the "
                "anchor is being checked for shape rather than compared."
            )
            return 1
        write_text(
            repo / "openspec/changes/recorded/tasks.md",
            header + task(f"keel-task-capsule/v1 sha256:{own}"),
        )
        recorded = gate("recorded", "task-complete")
        if recorded.get("status") != "pass":
            report(
                "completion-requires-a-recorded-anchor: recording the anchor did "
                "not clear the refusal."
            )
            for problem in recorded.get("problems", []):
                report(f"  {problem.get('code')}: {problem.get('message')}")
            return 1
    if "completion-requires-a-recorded-anchor" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "completion-requires-a-recorded-anchor: the scenario registry does "
            "not include it."
        )
        return 1
    report("completion-requires-a-recorded-anchor scenario passed.")
    return 0


def _anchor_fixture(
    *,
    contract: str,
    touch: str = "src/feature.js",
    checked: bool = False,
) -> str:
    """One change document that both completion and the close can be run against.

    It carries a delta-spec-shaped `## Expectation Coverage` and a single task so
    that `change-close --action sync` reaches the anchor checks instead of
    stopping on an unrelated structural problem.
    """
    box = "x" if checked else " "
    return (
        "# Tasks\n\n## Invalidates\n\n- None.\n\n"
        f"- [{box}] 1.1 Exercise task contract\n"
        "  - Covers:\n"
        "    - E1: Public behavior passes.\n"
        "  - Touch:\n"
        f"    - {touch}\n"
        "  - Verify:\n"
        "    - Strategy: evidence-first\n"
        "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "    - M1: node test.js asserts the recorded feed status\n"
        "  - Evidence:\n"
        f"    - Contract: {contract}\n"
        "    - M1: the suite passed\n"
        "    - Review:\n"
        "      - Status: pass\n"
        "      - Acceptance check: behavior asserted at the interface\n"
        "      - Scope check: only Touch files changed\n"
        "      - Findings: none\n"
        "    - Blocker: none\n"
        "\n## Expectation Coverage\n\n"
        "- E1: Public behavior passes. Covered by: 1.1\n"
    )


def validate_contract_drift_diagnosis_scenario() -> int:
    """Issue #342: drift names its cause when Git ties the anchor to a commit.

    Measured on rtl_ppa_prj: one upgrade-time drift was a compiler change
    (5.81.0), the other a `keel/config.yaml` edit. Every case here commits real
    gate output in a real repository and asks the real CLI what moved.
    """
    label = "contract-drift-diagnosis:"
    version = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]
    with tempfile.TemporaryDirectory(prefix="keel-drift-342-") as raw:
        repo = mailbox_repository(Path(raw) / "repo")

        def git(*args: str) -> str:
            return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()

        def commit(message: str) -> str:
            git("add", "-A")
            git("commit", "-q", "-m", message)
            return git("rev-parse", "HEAD")

        def change(name: str, doc: str) -> Path:
            path = repo / "openspec/changes" / name / "tasks.md"
            write_text(path, doc)
            write_text(
                repo / "openspec/changes" / name / "specs/demo/spec.md",
                "## ADDED Requirements\n\n"
                "### Requirement: Demo\nKeel MUST demo.\n\n"
                "#### Scenario: demo\n- **WHEN** a\n- **THEN** b\n",
            )
            return path

        def gate(name: str, stage: str, *extra: str) -> dict:
            return json.loads(run_keel(repo, "gate", stage, "--change", name, *extra, "--json").stdout)

        def record(name: str) -> dict:
            return gate(name, "task-start", "--task", "1.1", "--record", "--no-guard")

        def drift_message(payload: dict) -> str:
            found = [p.get("message", "") for p in payload.get("problems", []) if p.get("code") == "contract-drift"]
            return found[0] if found else ""

        def rewrite_anchor(path: Path, digest: str, keel: str) -> None:
            text = path.read_text(encoding="utf-8")
            text = re.sub(r"- Contract: .*", f"- Contract: keel-task-capsule/v1 sha256:{digest} (keel {keel})", text, count=1)
            write_text(path, text)

        write_authorize_config(repo, "authorize:\n  - commit\n  - push:main\n")

        # A compiler change: the committed sources compile to today's
        # fingerprint, and the anchor holds another digest from another version.
        comp = change("comp", _anchor_fixture(contract=f"keel-task-capsule/v1 sha256:{'a' * 64} (keel 5.0.0)"))
        sha = commit("comp recorded under an older compiler")
        message = drift_message(gate("comp", "task-complete", "--task", "1.1"))
        if "compiler" not in message:
            report(f"{label} the drift message does not name a compiler change: {message!r}")
            return 1
        for needle in (sha[:12], "5.0.0", version, "no `--keep-evidence` is needed"):
            if needle not in message:
                report(f"{label} the compiler-change message does not name {needle!r}: {message!r}")
                return 1
        rerecord = record("comp")
        warned = " ".join(rerecord.get("warnings", []))
        if "evidence stands" not in warned or sha[:12] not in warned:
            report(f"{label} the compiler-only re-record does not say the evidence stands at {sha[:12]}: {warned!r}")
            return 1
        if "stale" in warned:
            report(f"{label} the compiler-only re-record still calls evidence stale: {warned!r}")
            return 1
        # The anchor carries the version that recorded it.
        if f"(keel {version})" not in comp.read_text(encoding="utf-8"):
            report(f"{label} the recorded anchor does not carry (keel {version}): "
                   f"{re.search(r'- Contract: .*', comp.read_text(encoding='utf-8')).group(0)!r}")
            return 1

        # An anchor nothing explains claims nothing.
        same = change("same", _anchor_fixture(contract="pending"))
        record("same")
        rewrite_anchor(same, "b" * 64, version)
        commit("same: an anchor its sources do not compile to")
        message = drift_message(gate("same", "task-complete", "--task", "1.1"))
        if not message:
            report(f"{label} an unexplained anchor reported no contract drift.")
            return 1
        if "compiler" in message or "changed since" in message:
            report(f"{label} an unexplained anchor was given a cause: {message!r}")
            return 1

        # An edit is named by the field it changed.
        edit = change("edit", _anchor_fixture(contract="pending"))
        record("edit")
        sha = commit("edit recorded")
        write_text(edit, edit.read_text(encoding="utf-8").replace("src/feature.js", "src/DRIFTED.js"))
        message = drift_message(gate("edit", "task-complete", "--task", "1.1"))
        if "`touch`" not in message or sha[:12] not in message:
            report(f"{label} the edit drift does not name `touch` and {sha[:12]}: {message!r}")
            return 1
        context = run_keel(repo, "context", "--change", "edit", "--task", "1.1")
        if "`touch`" not in context.stdout:
            report(f"{label} keel context does not name the changed field: {context.stdout!r}")
            return 1
        write_text(edit, edit.read_text(encoding="utf-8").replace("src/DRIFTED.js", "src/feature.js"))

        # A standing-authorization change does not drift a completed task.
        done = change("auth", _anchor_fixture(contract="pending", checked=True))
        write_text(done.parent / "proposal.md", "## Why\n\nA fixture.\n")
        write_text(done.parent / "design.md", "## Context\n\nA fixture.\n")
        record("auth")
        going = change("auth2", _anchor_fixture(contract="pending"))
        record("auth2")
        commit("auth recorded under push:main")
        if gate("auth", "change-close", "--action", "archive").get("status") != "pass":
            report(f"{label} the authorization fixture does not close before the change: "
                   f"{gate('auth', 'change-close', '--action', 'archive')!r}")
            return 1
        write_authorize_config(repo, "authorize:\n  - commit\n  - push-protected:main\n")
        commit("push:main becomes push-protected:main")
        closed = gate("auth", "change-close", "--action", "archive")
        if closed.get("status") != "pass":
            report(f"{label} a standing-authorization change drifted a completed task at the close: "
                   f"{[p.get('message') for p in closed.get('problems', [])]!r}")
            return 1
        warned = " ".join(closed.get("warnings", []))
        if "1.1" not in warned or "standing authorization" not in warned:
            report(f"{label} the close does not warn naming 1.1 and the standing authorization: {warned!r}")
            return 1
        if not drift_message(gate("auth2", "task-complete", "--task", "1.1")):
            report(f"{label} an unchecked task inheriting the changed authorization was not drift.")
            return 1
    report("contract-drift-diagnosis scenario passed.")
    return 0


def validate_contract_anchor_is_compared_scenario() -> int:
    """Issue #37: completion checked that an anchor existed, never that it matched.

    `hasRecordedAnchor` parsed the digest, validated its shape, and discarded the
    value. A task could be implemented against one contract, have its Touch
    rewritten mid-flight, and still complete clean while the gate's own payload
    printed the recompiled fingerprint beside the recorded one. `change-close`
    was blind in the same way, which left the whole window between the last
    checkbox and the archive unguarded.

    Two shipped requirements already asserted the comparison — the write-guard
    spec's contract-drift scenario and the core-gates anchor scenario — so this
    makes existing text true rather than adding a promise.
    """
    label = "contract-anchor-is-compared"
    zeros = "0" * 64
    with tempfile.TemporaryDirectory(prefix="keel-anchor-compared-") as raw:
        repo = Path(raw)

        def change(name: str, doc: str) -> Path:
            path = repo / "openspec/changes" / name / "tasks.md"
            write_text(path, doc)
            write_text(
                repo / "openspec/changes" / name / "specs/demo/spec.md",
                "## ADDED Requirements\n\n"
                "### Requirement: Demo\nKeel MUST demo.\n\n"
                "#### Scenario: demo\n- **WHEN** a\n- **THEN** b\n",
            )
            return path

        def gate(name: str, stage: str, *extra: str) -> dict:
            return json.loads(
                run_keel(repo, "gate", stage, "--change", name, *extra, "--json").stdout
            )

        def record(name: str) -> str:
            payload = gate(
                name, "task-start", "--task", "1.1", "--record", "--no-guard"
            )
            return payload.get("contract", {}).get("fingerprint", {}).get("value", "")

        def codes(payload: dict) -> list[str]:
            return [problem.get("code", "") for problem in payload.get("problems", [])]

        def messages(payload: dict, code: str) -> list[str]:
            return [
                problem.get("message", "")
                for problem in payload.get("problems", [])
                if problem.get("code") == code
            ]

        def dump(check: str, payload: dict) -> None:
            report(f"  {check}: status={payload.get('status')}")
            for problem in payload.get("problems", []):
                report(f"    {problem.get('code')}: {problem.get('message')}")

        # M1 — a contract edited after recording is refused, and the refusal
        # carries everything the reader needs to act.
        drift_path = change("drift", _anchor_fixture(contract="pending"))
        recorded = record("drift")
        if not re.fullmatch(r"[0-9a-f]{64}", recorded):
            report(f"{label} M1 could not record an anchor to drift from.")
            return 1
        write_text(
            drift_path,
            drift_path.read_text(encoding="utf-8").replace(
                "src/feature.js", "src/DRIFTED.js"
            ),
        )
        payload = gate("drift", "task-complete", "--task", "1.1")
        recompiled = (
            payload.get("contract", {}).get("fingerprint", {}).get("value", "")
        )
        if recompiled == recorded:
            report(
                f"{label} M1 rewrote the task's Touch and the capsule compiled to "
                "the same fingerprint, so the fixture never produced the drift it "
                "is meant to catch."
            )
            return 1
        if "contract-drift" not in codes(payload):
            report(
                f"{label} M1 a task whose Touch was rewritten after recording "
                "reported no contract-drift problem, so the recorded anchor is "
                "still being counted rather than compared."
            )
            dump("M1", payload)
            return 1
        if payload.get("status") != "fail":
            report(
                f"{label} M1 reported contract drift but did not fail the gate; "
                f"status was {payload.get('status')!r}. Drift returns the task to "
                "authoring, so it cannot be a warning or a needs-review."
            )
            dump("M1", payload)
            return 1
        drift_message = messages(payload, "contract-drift")[0]
        for needle, why in (
            (recorded, "the recorded fingerprint"),
            (recompiled, "the fingerprint the task now compiles to"),
            ("task-start", "the command that reauthorizes the task"),
            ("stale", "that evidence recorded under the previous contract is stale"),
        ):
            if needle not in drift_message:
                report(f"{label} M1 the drift message does not name {why}.")
                report(f"  {drift_message}")
                return 1

        # M2 — a well-formed digest the task does not compile to is refused on
        # its value. This is the issue's own reproduction.
        change("forged", _anchor_fixture(contract=f"keel-task-capsule/v1 sha256:{zeros}"))
        payload = gate("forged", "task-complete", "--task", "1.1")
        if "contract-drift" not in codes(payload):
            report(
                f"{label} M2 an anchor of sixty-four zeros produced no "
                "contract-drift problem, so a well-formed digest this task never "
                "compiled to is still accepted on its shape."
            )
            dump("M2", payload)
            return 1
        if payload.get("status") != "fail":
            report(
                f"{label} M2 reported contract drift on a forged anchor without "
                f"failing the gate; status was {payload.get('status')!r}."
            )
            dump("M2", payload)
            return 1

        # M3 — correct work is not newly blocked, in either accepted anchor form.
        change("aligned", _anchor_fixture(contract="pending"))
        if not record("aligned"):
            report(f"{label} M3 could not record an anchor on the aligned change.")
            return 1
        payload = gate("aligned", "task-complete", "--task", "1.1")
        if payload.get("status") != "pass":
            report(
                f"{label} M3 a task whose anchor matches its recompiled "
                "fingerprint no longer completes, so the comparison refuses "
                "correct work."
            )
            dump("M3", payload)
            return 1
        bare_path = change("bare", _anchor_fixture(contract="pending"))
        bare = record("bare")
        write_text(
            bare_path,
            bare_path.read_text(encoding="utf-8").replace(
                f"keel-task-capsule/v1 sha256:{bare}", f"sha256:{bare}"
            ),
        )
        if "keel-task-capsule/v1" in bare_path.read_text(encoding="utf-8"):
            report(
                f"{label} M3 the fixture failed to strip the capsule schema "
                "prefix, so the bare-anchor case was never exercised."
            )
            return 1
        payload = gate("bare", "task-complete", "--task", "1.1")
        if payload.get("status") != "pass":
            report(
                f"{label} M3 a matching anchor written without the "
                "`keel-task-capsule/v1` prefix was refused. The prefix is "
                "diagnostic detail; a digest that matches could only have come "
                "from the schema that produced it."
            )
            dump("M3", payload)
            return 1

        # M4 — the close is not blind either: drift introduced after the last
        # checkbox, and a checked task carrying no anchor at all.
        close_path = change("close-drift", _anchor_fixture(contract="pending"))
        closed = record("close-drift")
        write_text(
            close_path,
            close_path.read_text(encoding="utf-8")
            .replace("- [ ] 1.1", "- [x] 1.1")
            .replace("src/feature.js", "src/DRIFTED.js"),
        )
        payload = gate("close-drift", "change-close", "--action", "sync")
        if "contract-drift" not in codes(payload):
            report(
                f"{label} M4 change-close reported no contract drift for a "
                "checked task whose contract was edited after its anchor was "
                f"recorded as sha256:{closed}, so the window between completion "
                "and the archive is unguarded."
            )
            dump("M4 drift", payload)
            return 1
        if payload.get("status") != "fail":
            report(
                f"{label} M4 change-close reported contract drift without "
                f"failing; status was {payload.get('status')!r}."
            )
            dump("M4 drift", payload)
            return 1
        if "1.1" not in messages(payload, "contract-drift")[0]:
            report(f"{label} M4 the close diagnostic does not name the drifted task.")
            report(f"  {messages(payload, 'contract-drift')[0]}")
            return 1
        change(
            "close-unrecorded", _anchor_fixture(contract="pending", checked=True)
        )
        payload = gate("close-unrecorded", "change-close", "--action", "sync")
        if "missing-contract-anchor" not in codes(payload):
            report(
                f"{label} M4 change-close named no missing anchor for a checked "
                "task that records no compiled fingerprint, so completion cannot "
                "be verified at the gate that closes it."
            )
            dump("M4 unrecorded", payload)
            return 1
        if payload.get("status") != "fail":
            report(
                f"{label} M4 change-close named the missing anchor without "
                f"failing; status was {payload.get('status')!r}."
            )
            dump("M4 unrecorded", payload)
            return 1
        close_missing = messages(payload, "missing-contract-anchor")[0]
        if "then complete it" in close_missing:
            report(
                f"{label} M4 the close diagnostic tells the reader to complete a "
                "task that is already checked, sending them to a place with no "
                "problem in it."
            )
            report(f"  {close_missing}")
            return 1

        # M5 — a change whose anchors all match still closes.
        clean_path = change("close-clean", _anchor_fixture(contract="pending"))
        if not record("close-clean"):
            report(f"{label} M5 could not record an anchor on the clean change.")
            return 1
        write_text(
            clean_path,
            clean_path.read_text(encoding="utf-8").replace("- [ ] 1.1", "- [x] 1.1"),
        )
        payload = gate("close-clean", "change-close", "--action", "sync")
        if payload.get("status") != "pass":
            report(
                f"{label} M5 a change whose every anchor matches no longer "
                "closes, so the comparison blocks correct work at the close."
            )
            dump("M5", payload)
            return 1
    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_task_body_ends_at_heading_scenario() -> int:
    """Issue #29: a change-level section was read as the last task's Evidence.

    parseTasks gave a task every line up to the next task or EOF, and a `##`
    heading did not stop it, so `## Invalidates` and `## Expectation Coverage`
    landed in whichever field was open last. That made the two checks look
    contradictory: `invalidation-phrase` requires the searchable wording in
    double quotes, while the concreteness test rejects an angle-bracket slot
    outside inline code, so an entry quoting wording that carries one could
    satisfy neither. They were never in conflict — the parser only made them
    appear so.
    """
    slot = "<" + "n" + ">"
    header = "# Tasks\n\n"

    def task(number: str, contract: str) -> str:
        return (
            f"- [ ] {number} Exercise task contract\n"
            "  - Covers:\n"
            "    - E1: Public behavior passes.\n"
            "  - Touch:\n"
            "    - src/feature.js\n"
            "  - Verify:\n"
            "    - Strategy: evidence-first\n"
            "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
            "    - M1: node test.js asserts the recorded feed status\n"
            "  - Evidence:\n"
            f"    - Contract: {contract}\n"
            "    - M1: the suite passed\n"
            "    - Review:\n"
            "      - Status: pass\n"
            "      - Acceptance check: behavior asserted at the interface\n"
            "      - Scope check: only Touch files changed\n"
            "      - Findings: none\n"
            "    - Blocker: none\n"
        )

    # The entry quotes stale wording carrying an unfilled slot, which is exactly
    # what issue #16 asks an invalidation to quote. A stray Contract line sits
    # in the trailing section to prove the anchor search stops at the heading.
    sections = (
        "\n## Invalidates\n\n"
        f'- I1: "an unresolved Q{slot} without an authorized fallback blocks '
        'implementation" — the schema prose. Updated by: 1.1\n'
        "    - Contract: keel-task-capsule/v1 sha256:" + "b" * 64 + "\n"
        "\n## Expectation Coverage\n\n"
        f"- E1: Every Q{slot} reference resolves Covered by: 1.1\n"
    )
    body = header + task("1.1", "pending") + "\n## 2. Second group\n\n" + task(
        "2.1", "pending"
    )

    with tempfile.TemporaryDirectory(prefix="keel-task-extent-") as raw:
        repo = Path(raw)
        write_text(repo / "openspec/changes/demo/tasks.md", body + sections)
        started = run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "2.1", "--json"
        )
        payload = json.loads(started.stdout)
        problems = payload.get("problems", [])
        if payload.get("status") != "pass":
            report(
                "task-body-ends-at-heading: the last task did not pass task-start "
                "with a trailing section quoting an unfilled slot."
            )
            for problem in problems:
                report(f"  {problem.get('code')}: {problem.get('message')}")
            return 1
        # The same run proves the phrase check is satisfied: an entry the phrase
        # check rejected would have produced invalidation-phrase above.
        malformed = body + (
            "\n## Invalidates\n\n"
            "- I1: the schema prose is stale. Updated by: 1.1\n"
        )
        write_text(repo / "openspec/changes/unquoted/tasks.md", malformed)
        unquoted = json.loads(
            run_keel(
                repo,
                "gate",
                "task-start",
                "--change",
                "unquoted",
                "--task",
                "2.1",
                "--json",
            ).stdout
        )
        if not any(
            problem.get("code") == "invalidation-phrase"
            for problem in unquoted.get("problems", [])
        ):
            report(
                "task-body-ends-at-heading: an unquoted invalidation entry was "
                "accepted, so the phrase check is no longer being satisfied by "
                "the quoted one."
            )
            return 1
        # A group heading must not be appended to the preceding task's field.
        first = json.loads(
            run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
            ).stdout
        )
        evidence = json.dumps(first)
        if "Second group" in evidence:
            report(
                "task-body-ends-at-heading: the group heading leaked into the "
                "preceding task's fields."
            )
            return 1
        # An indented `##` line is not a heading — issue #160. The tolerant
        # test ended the task there, and a field declared after it with a
        # documented default was replaced by that default without a word: the
        # stop rule below vanished and task-start still passed. The fields are
        # ordered so the dropped one is exactly such a field.
        write_text(
            repo / "openspec/changes/indented/tasks.md",
            header
            + "- [ ] 1.1 Exercise task contract\n"
            "  - Covers:\n"
            "    - E1: Public behavior passes.\n"
            "  - Touch:\n"
            "    - src/feature.js\n"
            "  - Verify:\n"
            "    - Strategy: evidence-first\n"
            "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
            "    - M1: node test.js asserts the recorded feed status\n"
            "  - Evidence:\n"
            "    - Contract: pending\n"
            "    - M1: pending\n"
            "  - Acceptance:\n"
            "    - Public behavior passes.\n"
            "    ## an indented line is not a heading\n"
            "  - Stop Rules:\n"
            "    - Stop on the rule declared after the indented line.\n"
            "\n## Invalidates\n\n- None.\n",
        )
        indented = json.loads(
            run_keel(
                repo, "gate", "task-start", "--change", "indented", "--task",
                "1.1", "--no-guard", "--json",
            ).stdout
        )
        if "Stop on the rule declared after the indented line." not in json.dumps(
            indented
        ):
            report(
                "task-body-ends-at-heading: task-start dropped the fields "
                "declared after an indented `##` line; the task ended at a line "
                f"that is not a heading (status {indented.get('status')!r})."
            )
            return 1
        # --record must anchor the last task's own Contract line, not the stray
        # one planted in the trailing section.
        recorded = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "2.1",
            "--record",
            "--json",
        )
        if recorded.returncode != 0:
            report("task-body-ends-at-heading: --record failed on the last task.")
            report((recorded.stdout or recorded.stderr).strip())
            return 1
        written = (repo / "openspec/changes/demo/tasks.md").read_text(
            encoding="utf-8"
        )
        after_heading = written.split("## Invalidates", 1)[1]
        if "b" * 64 not in after_heading:
            report(
                "task-body-ends-at-heading: --record overwrote the Contract line "
                "planted inside the trailing section."
            )
            return 1
        # The extent change must move no fingerprint: an anchor that shifted
        # would drift every live change in every consumer repo at once. Pinned
        # rather than merely measured, so a future extent change cannot move one
        # silently. A deliberate capsule-shape change will fail here too — that
        # is the point; it should be looked at, not absorbed.
        #
        # Moved once, deliberately, when `evidence-first` began requiring a
        # stated reason: this fixture gained a `Verification Reason:` field, so
        # its own capsule changed. What did not change is the capsule of a task
        # that states no reason — the `reason` key is emitted only when there is
        # one, and a vertical-tdd task compiles to the identical block and the
        # identical fingerprint before and after, measured both ways. So no
        # existing anchor drifted; this fixture is simply a different task now.
        #
        # Moved again, deliberately and for every anchor, in 5.175.0 (#413): the
        # capsule dropped three prohibitions and its default owner. The drift
        # diagnosis names that move a compiler change, measured with an anchor
        # recorded by 5.174.0, and the changelog tells each repository to
        # re-record once.
        pinned = {
            "1.1": "7149e77c287d08abd33aae1835e24ff4892771efdfb5d6755b791e2d78436319",
            "2.1": "bc2d69bcf8718e5825af8f2fb5f318518f74051ea021a61d549691b449ad5929",
        }
        plain = (
            "# Tasks\n\n"
            + task("1.1", "pending")
            + "\n## 2. Second group\n\n"
            + task("2.1", "pending")
            + '\n## Invalidates\n\n- I1: "the schema prose is stale here" — the '
            "schema. Updated by: 1.1\n\n## Expectation Coverage\n\n"
            "- E1: Covered by: 1.1\n"
        )
        write_text(repo / "openspec/changes/pinned/tasks.md", plain)
        for task_id, expected in pinned.items():
            payload = json.loads(
                run_keel(
                    repo,
                    "gate",
                    "task-start",
                    "--change",
                    "pinned",
                    "--task",
                    task_id,
                    "--json",
                ).stdout
            )
            actual = (
                payload.get("contract", {}).get("fingerprint", {}).get("value")
            )
            if actual != expected:
                report(
                    "task-body-ends-at-heading: the compiled fingerprint for "
                    f"task {task_id} moved. Expected {expected}, got {actual}. "
                    "An extent or capsule-shape change that moves an anchor "
                    "drifts every live change in every consumer repo."
                )
                return 1
    if "task-body-ends-at-heading" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "task-body-ends-at-heading: the scenario registry does not include it."
        )
        return 1
    report("task-body-ends-at-heading scenario passed.")
    return 0


def validate_task_complete_selection_requires_a_started_task_scenario() -> int:
    """Issue #28 item 6: the no-arg default reported another task's problems.

    The documented order is gate-then-checkbox, so first-unchecked is the right
    inference and stays. The hazard is narrower: inferring a task that never
    started, then printing its readiness problems under a selection heading the
    author reads as their own task's failure. A task that has started records a
    fingerprint in its Evidence `Contract` anchor, so that anchor is what makes
    the inference safe.
    """
    header = "# Tasks\n\n## Invalidates\n\n- None.\n\n"

    def task(number: str, checked: bool, contract: str) -> str:
        box = "x" if checked else " "
        return (
            f"- [{box}] {number} Exercise task contract\n"
            "  - Covers:\n"
            "    - E1: Public behavior passes.\n"
            "  - Touch:\n"
            "    - src/feature.js\n"
            "  - Verify:\n"
            "    - Strategy: evidence-first\n"
            "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
            "    - M1: node test.js\n"
            "  - Evidence:\n"
            f"    - Contract: {contract}\n"
            "    - M1: the suite passed\n"
            "    - Review:\n"
            "      - Status: pass\n"
            "      - Acceptance check: behavior asserted at the interface\n"
            "      - Scope check: only Touch files changed\n"
            "      - Findings: none\n"
            "    - Blocker: none\n"
        )

    digest = "a" * 64
    anchored = f"keel-task-capsule/v1 sha256:{digest}"
    with tempfile.TemporaryDirectory(prefix="keel-complete-selection-") as raw:
        repo = Path(raw)

        def gate(change: str, stage: str) -> dict:
            result = run_keel(
                repo, "gate", stage, "--change", change, "--json"
            )
            return json.loads(result.stdout)

        # 1.1 is finished; 1.2 has never started, so its anchor is still pending.
        write_text(
            repo / "openspec/changes/unstarted/tasks.md",
            header
            + task("1.1", True, anchored)
            + "\n"
            + task("1.2", False, "pending"),
        )
        payload = gate("unstarted", "task-complete")
        codes = {problem.get("code") for problem in payload.get("problems", [])}
        if "ambiguous-completion-selection" not in codes:
            report(
                "task-complete-selection-requires-a-started-task: no-arg "
                "task-complete did not refuse on selection for a task that "
                "records no start fingerprint."
            )
            report(json.dumps(payload.get("problems", []), indent=2))
            return 1
        message = next(
            problem.get("message", "")
            for problem in payload.get("problems", [])
            if problem.get("code") == "ambiguous-completion-selection"
        )
        for needle in ("1.2", "1.1", "--task"):
            if needle not in message:
                report(
                    "task-complete-selection-requires-a-started-task: the "
                    f"refusal did not name {needle}."
                )
                report(message)
                return 1
        # The same shape, once 1.2 has recorded its start fingerprint.
        write_text(
            repo / "openspec/changes/started/tasks.md",
            header
            + task("1.1", True, anchored)
            + "\n"
            + task("1.2", False, anchored),
        )
        started = gate("started", "task-complete")
        started_codes = {
            problem.get("code") for problem in started.get("problems", [])
        }
        if "ambiguous-completion-selection" in started_codes:
            report(
                "task-complete-selection-requires-a-started-task: a task that "
                "recorded its start fingerprint was still refused on selection."
            )
            return 1
        if started.get("selection", {}).get("tasks") != ["1.2"]:
            report(
                "task-complete-selection-requires-a-started-task: the started "
                "task was not the inferred selection."
            )
            report(json.dumps(started.get("selection", {}), indent=2))
            return 1
        # task-start keeps the plain first-unchecked default: selecting a task
        # that has not started is exactly its job.
        start = gate("unstarted", "task-start")
        if start.get("selection", {}).get("tasks") != ["1.2"]:
            report(
                "task-complete-selection-requires-a-started-task: no-arg "
                "task-start no longer selects the first unchecked task."
            )
            report(json.dumps(start.get("selection", {}), indent=2))
            return 1
        start_codes = {problem.get("code") for problem in start.get("problems", [])}
        if "ambiguous-completion-selection" in start_codes:
            report(
                "task-complete-selection-requires-a-started-task: the selection "
                "refusal leaked into task-start."
            )
            return 1
    if "task-complete-selection-requires-a-started-task" not in {
        name for name, _ in registry.SCENARIOS
    }:
        report(
            "task-complete-selection-requires-a-started-task: the scenario "
            "registry does not include it."
        )
        return 1
    report("task-complete-selection-requires-a-started-task scenario passed.")
    return 0


def validate_absent_verification_form_is_one_problem_scenario() -> int:
    """Issue #28 item 4: the cascade reported a schema the author never chose.

    Compact detection read only `isConcrete(Verify)`, so a task that simply had
    no verification field was reported as an expanded v3 task missing nine
    fields. Seven of them either resolve to a documented default, derive from
    other authority, are consumed nowhere, or belong to the coupling contract —
    leaving the one actionable line last.
    """
    defaulted = (
        "Owner",
        "Mode",
        "Read",
        "Acceptance",
        "Report",
        "Candidate Boundary",
        "Stop Rules",
    )
    header = "# Tasks\n\n## Invalidates\n\n- None.\n\n"
    body = (
        "- [ ] 1.1 Exercise task contract\n"
        "  - Covers:\n"
        "    - E1: Public behavior passes.\n"
        "  - Touch:\n"
        "    - src/feature.js\n"
    )
    evidence = "  - Evidence:\n    - M1: pending\n"
    commands = (
        "  - Verification Strategy: evidence-first\n"
        "  - Verification Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "  - Commands:\n    - M1: node test.js\n"
    )

    with tempfile.TemporaryDirectory(prefix="keel-absent-verification-") as raw:
        repo = Path(raw)

        def problems_for(change: str, content: str) -> list:
            write_text(repo / f"openspec/changes/{change}/tasks.md", content)
            result = run_keel(
                repo,
                "gate",
                "task-start",
                "--change",
                change,
                "--task",
                "1.1",
                "--json",
            )
            return json.loads(result.stdout).get("problems", [])

        # M1 — neither verification form declared.
        none_declared = problems_for("noform", header + body + evidence)
        naming = [
            problem
            for problem in none_declared
            if "Verify" in problem.get("message", "")
        ]
        if len(naming) != 1:
            report(
                "absent-verification-form-is-one-problem: expected exactly one "
                f"diagnostic naming Verify, found {len(naming)}."
            )
            for problem in none_declared:
                report(f"  {problem.get('code')}: {problem.get('message')}")
            return 1
        leaked = sorted(
            name
            for problem in none_declared
            if problem.get("code") == "missing-field"
            for name in defaulted
            if problem.get("message", "").startswith(f"{name} must be concrete")
        )
        if leaked:
            report(
                "absent-verification-form-is-one-problem: fields with documented "
                f"defaults were still required: {', '.join(leaked)}."
            )
            return 1

        # M2 — a genuine expanded v3 task that omits every defaulted field.
        expanded = problems_for("expanded", header + body + commands + evidence)
        if expanded:
            report(
                "absent-verification-form-is-one-problem: an expanded task "
                "declaring Commands, Covers, Touch and Evidence did not pass."
            )
            for problem in expanded:
                report(f"  {problem.get('code')}: {problem.get('message')}")
            return 1
        # Removing Commands from that same task must still fail.
        if not problems_for("expanded-no-commands", header + body + evidence):
            report(
                "absent-verification-form-is-one-problem: removing Commands "
                "from the expanded task left it passing."
            )
            return 1
        # Candidate Boundary is the coupling contract's to require.
        coupled = problems_for(
            "coupled",
            header
            + body
            + "  - Coupling: required\n"
            + commands
            + evidence,
        )
        if not any(
            "Candidate Boundary" in problem.get("message", "") for problem in coupled
        ):
            report(
                "absent-verification-form-is-one-problem: Coupling required did "
                "not require a Candidate Boundary."
            )
            for problem in coupled:
                report(f"  {problem.get('code')}: {problem.get('message')}")
            return 1
    if "absent-verification-form-is-one-problem" not in {
        name for name, _ in registry.SCENARIOS
    }:
        report(
            "absent-verification-form-is-one-problem: the scenario registry does "
            "not include it."
        )
        return 1
    report("absent-verification-form-is-one-problem scenario passed.")
    return 0


def validate_non_concrete_check_names_token_scenario() -> int:
    """Issue #28 item 5: the check diagnostic must name the slot it matched.

    `unfilledToken` already identifies the matched token and `Verify` already
    reports it. The per-check message said only that the check "must define a
    concrete public check", which describes the consequence rather than the
    cause, so the reporter had to guess which of several inline slots was the
    problem.
    """
    slot = "<" + "url" + ">"
    with tempfile.TemporaryDirectory(prefix="keel-check-token-") as raw:
        repo = Path(raw)
        base = task_capsule_compact_fixture().replace(
            "    - M1: node test.js\n",
            "    - M1: node test.js\n"
            f"    - M2: run the fetch script against {slot} and assert the "
            "recorded status\n",
        ).replace("    - M1: pending\n", "    - M1: pending\n    - M2: pending\n")
        write_text(repo / "openspec/changes/tokened/tasks.md", base)

        def check_messages(change: str) -> list:
            result = run_keel(
                repo,
                "gate",
                "task-start",
                "--change",
                change,
                "--task",
                "1.1",
                "--json",
            )
            payload = json.loads(result.stdout)
            return [
                problem.get("message", "")
                for problem in payload.get("problems", [])
                if problem.get("code") == "missing-command-check"
            ]

        tokened = check_messages("tokened")
        if not tokened:
            report(
                "non-concrete-check-names-token: a check carrying a bare "
                "unfilled slot produced no missing-command-check diagnostic."
            )
            return 1
        if slot not in tokened[0]:
            report(
                "non-concrete-check-names-token: the diagnostic did not name "
                f"the {slot} slot it matched."
            )
            report(tokened[0])
            return 1
        # Replacing exactly what the diagnostic names must clear it.
        fixed = base.replace(slot, "`https://example.test/feed`")
        write_text(repo / "openspec/changes/fixed/tasks.md", fixed)
        if check_messages("fixed"):
            report(
                "non-concrete-check-names-token: replacing the named slot did "
                "not clear the diagnostic."
            )
            return 1
        # An empty check has no token to name, so the unqualified wording is
        # still the honest one there.
        empty = base.replace(
            f"    - M2: run the fetch script against {slot} and assert the "
            "recorded status\n",
            "    - M2: pending\n",
        )
        write_text(repo / "openspec/changes/empty/tasks.md", empty)
        bare = check_messages("empty")
        if not bare:
            report(
                "non-concrete-check-names-token: a pending check produced no "
                "missing-command-check diagnostic."
            )
            return 1
        if "must define a concrete public check" not in bare[0]:
            report(
                "non-concrete-check-names-token: a pending check lost the "
                "unqualified wording."
            )
            report(bare[0])
            return 1
    if "non-concrete-check-names-token" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "non-concrete-check-names-token: the scenario registry does not "
            "include it."
        )
        return 1
    report("non-concrete-check-names-token scenario passed.")
    return 0


def validate_unusable_contract_names_only_its_cause_scenario() -> int:
    """Issue #52: the first problem named `Commands`, which compact tasks lack.

    Two defects compound. `missingFieldProblems` emitted a bare "must be
    concrete" while `unfilledToken` sat eight lines above it, and a contract
    carrying any diagnostic is discarded, after which `completionChecks` falls
    back to reading `Commands` — a field a compact task never declares. The
    derived problem sorts first and is the only one naming a field, so it is the
    one an author acts on, and it is about a schema they did not choose.

    What is deliberately *not* changed is which fields the gate accepts. A bare
    token in prose stays non-concrete; see the M3 regression on
    `inline-code-is-concrete` and the decision recorded in
    keel/archive/follow-ups/2026-07-27-unfilled-token-keywords.md.
    """
    less, greater = "<", ">"
    # The reporter's own shape: two bare brackets separated by half a sentence,
    # so the unbounded `<[^>]+>` swallows the span between them.
    prose = (
        f"pass — max ratio 0.001916 (bound {less}0.02), "
        f"min ratio 0.998107 (bound {greater}0.98)."
    )
    captured = f"{less}0.02), min ratio 0.998107 (bound {greater}"
    review = (
        "    - Review:\n"
        "      - Status: pass\n"
        "      - Acceptance check: reviewed\n"
        "      - Scope check: reviewed\n"
        "      - Findings: none\n"
    )
    with tempfile.TemporaryDirectory(prefix="keel-unusable-contract-") as raw:
        repo = Path(raw)
        clean = task_capsule_compact_fixture()
        write_text(repo / "openspec/changes/prose/tasks.md", clean)
        # The anchor has to be recorded while the Evidence is still concrete —
        # which is the real sequence, not a workaround. The token arrives when
        # the author writes up the result, after the task started.
        if not record_contract_anchor(repo, "prose"):
            report(
                "unusable-contract-names-only-its-cause: the clean fixture "
                "could not record a contract anchor."
            )
            return 1
        started = (repo / "openspec/changes/prose/tasks.md").read_text(
            encoding="utf-8"
        )
        write_text(
            repo / "openspec/changes/prose/tasks.md",
            started.replace(
                "    - M1: pending\n", f"    - M1: {prose}\n{review}"
            ),
        )
        completed = run_keel(
            repo,
            "gate",
            "task-complete",
            "--change",
            "prose",
            "--task",
            "1.1",
            "--json",
        )
        payload = json.loads(completed.stdout)
        problems = payload.get("problems", [])
        messages = [problem.get("message", "") for problem in problems]

        # 1. The derived problem is gone. It named a field compact tasks lack.
        derived = [text for text in messages if "must define at least one" in text]
        if derived:
            report(
                "unusable-contract-names-only-its-cause: an unusable contract "
                "still derived a verification-form problem from the other "
                "schema's field."
            )
            for text in derived:
                report(f"  {text}")
            return 1

        # 2. The remaining problem names the span that caused it, and the escape.
        named = [
            text
            for text in messages
            if captured in text and "inline code" in text
        ]
        if not named:
            report(
                "unusable-contract-names-only-its-cause: the Evidence "
                "diagnostic did not name the matched span and the inline-code "
                "escape."
            )
            for text in messages:
                report(f"  {text}")
            return 1

        # 3. Naming the cause did not stop the gate refusing. This is the
        #    assertion that must never be dropped: suppressing a problem is the
        #    direction that can wrongly make a gate pass.
        if payload.get("status") != "fail":
            report(
                "unusable-contract-names-only-its-cause: the gate returned "
                f"{payload.get('status')!r} for a task whose Evidence is not "
                "concrete."
            )
            return 1

        # 4. Fencing exactly what the message names clears it, so the offered
        #    repair is the one that works.
        fenced = started.replace(
            "    - M1: pending\n",
            f"    - M1: `{prose}`\n{review}",
        )
        write_text(repo / "openspec/changes/fenced/tasks.md", fenced)
        if not record_contract_anchor(repo, "fenced"):
            report(
                "unusable-contract-names-only-its-cause: fencing the named "
                "span did not make the Evidence concrete."
            )
            return 1

        # 5. An empty field has no token to name, so it keeps the plain wording.
        empty = clean.replace(
            "  - Covers:\n    - E1: Public behavior passes.\n", "  - Covers:\n"
        )
        write_text(repo / "openspec/changes/empty/tasks.md", empty)
        bare = run_keel(
            repo, "gate", "task-start", "--change", "empty", "--task", "1.1",
            "--json",
        )
        bare_messages = [
            problem.get("message", "")
            for problem in json.loads(bare.stdout).get("problems", [])
        ]
        if not any(
            text.startswith("Covers must be concrete") for text in bare_messages
        ):
            report(
                "unusable-contract-names-only-its-cause: an empty required "
                "field lost the unqualified wording."
            )
            for text in bare_messages:
                report(f"  {text}")
            return 1

        # 6. Suppression must not hide a task that genuinely declares no
        #    verification form. The refusal names the compact field to add.
        noform = clean.replace(
            "  - Verify:\n    - Strategy: evidence-first\n    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n    - M1: node test.js\n",
            "",
        )
        write_text(repo / "openspec/changes/noform/tasks.md", noform)
        absent = run_keel(
            repo, "gate", "task-complete", "--change", "noform", "--task", "1.1",
            "--json",
        )
        absent_payload = json.loads(absent.stdout)
        absent_messages = [
            problem.get("message", "")
            for problem in absent_payload.get("problems", [])
        ]
        if absent_payload.get("status") != "fail":
            report(
                "unusable-contract-names-only-its-cause: a task declaring no "
                "verification form was not refused."
            )
            return 1
        if not any("`Verify`" in text for text in absent_messages):
            report(
                "unusable-contract-names-only-its-cause: the refusal did not "
                "name `Verify` as the field to add."
            )
            for text in absent_messages:
                report(f"  {text}")
            return 1
        if any("must define at least one" in text for text in absent_messages):
            report(
                "unusable-contract-names-only-its-cause: a task declaring no "
                "verification form was told about `Commands`."
            )
            return 1
    if "unusable-contract-names-only-its-cause" not in {
        name for name, _ in registry.SCENARIOS
    }:
        report(
            "unusable-contract-names-only-its-cause: the scenario registry "
            "does not include it."
        )
        return 1
    report("unusable-contract-names-only-its-cause scenario passed.")
    return 0


def validate_covers_question_reference_scope_scenario() -> int:
    """Issue #28 item 9: citing a resolved question must not re-open it.

    The question scan used to run over the whole Covers field, so a task that
    named `Q1` beside the fact that closed it was told to declare a fallback for
    a question it does not carry. The reporter's only available fix was to
    delete the reference, which makes traceability worse.

    Both sides are asserted. A scenario that only checked the newly passing
    shape would also be satisfied by deleting the check outright.
    """
    with tempfile.TemporaryDirectory(prefix="keel-covers-question-") as raw:
        repo = Path(raw)
        base = task_capsule_compact_fixture()
        # Still in scope: the question is the subject of its entry.
        subject = base.replace(
            "    - E1: Public behavior passes.\n",
            "    - Q1: Should the widget retry on timeout?\n",
        )
        write_text(repo / "openspec/changes/subject/tasks.md", subject)
        # Out of scope: the entry's subject is the fact, and the resolved
        # question is named as the supporting detail that points at it.
        detail = base.replace(
            "    - E1: Public behavior passes.\n",
            "    - F13 (Q1 resolved: the widget retries twice, then stops)\n",
        )
        write_text(repo / "openspec/changes/detail/tasks.md", detail)

        def authority_messages(change: str) -> list:
            result = run_keel(
                repo,
                "gate",
                "task-start",
                "--change",
                change,
                "--task",
                "1.1",
                "--json",
            )
            payload = json.loads(result.stdout)
            return [
                problem.get("message", "")
                for problem in payload.get("problems", [])
                if problem.get("code") == "unresolved-authority"
            ]

        blocking = authority_messages("subject")
        if not blocking:
            report(
                "covers-question-reference-scope: a question that opens its "
                "Covers entry produced no unresolved-authority diagnostic, so "
                "the check no longer refuses anything."
            )
            return 1
        if "Q1" not in blocking[0]:
            report(
                "covers-question-reference-scope: the diagnostic did not name "
                "the question it read."
            )
            report(blocking[0])
            return 1
        citing = authority_messages("detail")
        if citing:
            report(
                "covers-question-reference-scope: naming a resolved question as "
                "supporting detail still demands a fallback for it."
            )
            report(citing[0])
            return 1
    if "covers-question-reference-scope" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "covers-question-reference-scope: the scenario registry does not "
            "include it."
        )
        return 1
    report("covers-question-reference-scope scenario passed.")
    return 0


TRACKER_OWNER = "https://github.com/TanglmChris/keel/issues/12"


def validate_tracker_durable_owner_scenario() -> int:
    """Issue #12: an issue tracker is a durable follow-up owner.

    The gate enumerated three repository-local forms, so a project whose
    declared follow-up owner is an issue tracker had to write a local note per
    finding whose only job was to be a shape the gate recognized. The tracker
    form is now accepted in both places a durable owner is required, and every
    previously accepted form still passes.
    """
    with tempfile.TemporaryDirectory(prefix="keel-tracker-owner-") as raw:
        repo = Path(raw)
        tasks = repo / "openspec/changes/demo/tasks.md"
        write_text(repo / "openspec/changes/demo/proposal.md", "# Proposal\n")
        write_text(
            repo / "openspec/changes/demo/specs/demo/spec.md",
            "## ADDED Requirements\n",
        )

        def complete(findings: str, closure: str = "Covered by: 1.1"):
            write_text(tasks, tracker_owner_tasks(findings, closure))
            record_contract_anchor(repo, "demo")
            return run_keel(
                repo, "gate", "task-complete",
                "--change", "demo", "--task", "1.1", "--json",
            )

        def close(closure: str):
            write_text(tasks, tracker_owner_tasks("none", closure))
            # The close compares each checked task's anchor, so the fixture
            # records the one its own contract compiles to rather than leaving
            # the task in a state completion would have refused.
            record_contract_anchor(repo, "demo")
            return run_keel(
                repo, "gate", "change-close",
                "--change", "demo", "--action", "sync", "--json",
            )

        tracker = complete(f"stale local note; owner {TRACKER_OWNER}")
        if tracker.returncode != 0:
            report(
                "tracker-durable-owner: a finding owned by an absolute tracker "
                "reference was still refused."
            )
            report((tracker.stderr or tracker.stdout).strip())
            return 1

        unowned = complete("stale local note that names no owner at all")
        unowned_payload = json.loads(unowned.stdout) if unowned.stdout else {}
        message = " ".join(
            problem.get("message", "")
            for problem in unowned_payload.get("problems", [])
            if problem.get("code") == "finding-owner"
        )
        if unowned.returncode != 3 or "http" not in message:
            report(
                "tracker-durable-owner: an unowned finding must still fail, and "
                "the error must list the tracker form among the accepted ones."
            )
            report((unowned.stderr or unowned.stdout).strip())
            return 1

        handoff = complete("stale local note; owner keel/HANDOFF.md")
        if handoff.returncode != 3:
            report(
                "tracker-durable-owner: keel/HANDOFF.md must still be refused "
                "as a finding owner."
            )
            report((handoff.stderr or handoff.stdout).strip())
            return 1

        # The archive path must now exist to own anything: a note nobody wrote
        # owns nothing, and a path is the one owner form a gate can check.
        write_text(repo / "keel/archive/follow-ups/x.md", "follow-up note\n")
        archived = complete("stale local note; owner keel/archive/follow-ups/x.md")
        if archived.returncode != 0:
            report(
                "tracker-durable-owner: the pre-existing keel/archive owner form "
                "regressed."
            )
            report((archived.stderr or archived.stdout).strip())
            return 1

        closed_by_tracker = close(f"Durable owner: {TRACKER_OWNER}")
        if closed_by_tracker.returncode != 0:
            report(
                "tracker-durable-owner: change-close refused an Expectation "
                "Coverage durable owner naming a tracker reference."
            )
            report((closed_by_tracker.stderr or closed_by_tracker.stdout).strip())
            return 1

        closed_by_task = close("Covered by: 1.1")
        if closed_by_task.returncode != 0:
            report(
                "tracker-durable-owner: the pre-existing Covered by closure "
                "regressed at change-close."
            )
            report((closed_by_task.stderr or closed_by_task.stdout).strip())
            return 1

        closed_unowned = close("pending")
        if closed_unowned.returncode != 3:
            report(
                "tracker-durable-owner: change-close must still reject an E1 "
                "with no coverage, owner, or discard reason."
            )
            report((closed_unowned.stderr or closed_unowned.stdout).strip())
            return 1

    if "tracker-durable-owner" not in {name for name, _ in registry.SCENARIOS}:
        report("tracker-durable-owner: the scenario registry does not include it.")
        return 1
    report("tracker-durable-owner scenario passed.")
    return 0


def validate_findings_resolved_here_scenario() -> int:
    """A finding fixed in its own task is recorded as fixed, not as discarded.

    The gate required a durable owner for every non-`none` Findings value, while
    the spec and `review-checklist` both scope that requirement to
    *unresolved* findings. A finding found and repaired inside one task had no
    accepted form, so the only text that passed was `Discard reason:` — which
    files a repair as a dismissal. `## Invalidates` has carried the same third
    slot since it shipped, where `Updated by:` names tasks of this change.
    """
    with tempfile.TemporaryDirectory(prefix="keel-resolved-here-") as raw:
        repo = Path(raw)
        tasks = repo / "openspec/changes/demo/tasks.md"
        write_text(repo / "openspec/changes/demo/proposal.md", "# Proposal\n")
        write_text(
            repo / "openspec/changes/demo/specs/demo/spec.md",
            "## ADDED Requirements\n",
        )

        def complete(findings: str):
            write_text(tasks, tracker_owner_tasks(findings, "Covered by: 1.1"))
            record_contract_anchor(repo, "demo")
            return run_keel(
                repo, "gate", "task-complete",
                "--change", "demo", "--task", "1.1", "--json",
            )

        def problems(result, code: str) -> str:
            payload = json.loads(result.stdout) if result.stdout else {}
            return " ".join(
                item.get("message", "")
                for item in payload.get("problems", [])
                if item.get("code") == code
            )

        # M1 — the disposition exists, and its evidence has to be real.
        resolved = complete(
            "the helper rewrote its own baseline path. Resolved here: M1"
        )
        if resolved.returncode != 0:
            report(
                "findings-resolved-here: M1 a finding recorded as resolved here "
                "and citing M1, a check this task declares, was still refused."
            )
            report((resolved.stderr or resolved.stdout).strip())
            return 1

        bare = complete("the helper rewrote its own baseline path. Resolved here:")
        bare_message = problems(bare, "finding-resolution-evidence")
        if bare.returncode != 3:
            report(
                "findings-resolved-here: M1 a resolved finding naming no "
                f"evidence exited {bare.returncode}, not 3."
            )
            report((bare.stderr or bare.stdout).strip())
            return 1
        if not bare_message:
            report(
                "findings-resolved-here: M1 a resolved finding naming no "
                "evidence produced no finding-resolution-evidence problem."
            )
            report((bare.stderr or bare.stdout).strip())
            return 1

        unknown = complete(
            "the helper rewrote its own baseline path. Resolved here: M7"
        )
        unknown_message = problems(unknown, "finding-resolution-evidence")
        if unknown.returncode != 3:
            report(
                "findings-resolved-here: M1 a resolved finding citing M7, which "
                f"this task does not declare, exited {unknown.returncode}, not 3."
            )
            report((unknown.stderr or unknown.stdout).strip())
            return 1
        if "M7" not in unknown_message:
            report(
                "findings-resolved-here: M1 the refusal must name the check it "
                f"could not find. Got: {unknown_message or '(no problem)'}"
            )
            return 1

        # M2 — a path is evidence when it exists; a tracker URL never is.
        write_text(repo / "src/feature.js", "// the fix\n")
        by_path = complete(
            "the helper rewrote its own baseline path. Resolved here: src/feature.js"
        )
        if by_path.returncode != 0:
            report(
                "findings-resolved-here: M2 resolution evidence naming an "
                "existing repo-relative path was refused."
            )
            report((by_path.stderr or by_path.stdout).strip())
            return 1

        missing = complete(
            "the helper rewrote its own baseline path. Resolved here: src/gone.js"
        )
        missing_message = problems(missing, "finding-resolution-evidence")
        if missing.returncode != 3:
            report(
                "findings-resolved-here: M2 resolution evidence naming a path "
                f"that does not exist exited {missing.returncode}, not 3."
            )
            report((missing.stderr or missing.stdout).strip())
            return 1
        if "src/gone.js" not in missing_message:
            report(
                "findings-resolved-here: M2 the refusal must name the path it "
                f"could not find. Got: {missing_message or '(no problem)'}"
            )
            return 1

        as_evidence = complete(
            f"the helper rewrote its own baseline path. Resolved here: {TRACKER_OWNER}"
        )
        tracker_message = problems(as_evidence, "finding-resolution-evidence")
        if as_evidence.returncode != 3:
            report(
                "findings-resolved-here: M2 a tracker reference is not evidence "
                "that a finding was fixed, but it was accepted as resolution "
                f"evidence (exit {as_evidence.returncode})."
            )
            report((as_evidence.stderr or as_evidence.stdout).strip())
            return 1
        if "Durable owner" not in tracker_message:
            report(
                "findings-resolved-here: M2 the refusal must send a tracker "
                f"reference to `Durable owner:`. Got: {tracker_message or '(none)'}"
            )
            return 1

        as_owner = complete(
            f"the helper rewrote its own baseline path. Durable owner: {TRACKER_OWNER}"
        )
        if as_owner.returncode != 0:
            report(
                "findings-resolved-here: M2 the same tracker reference must "
                "still pass as a durable owner."
            )
            report((as_owner.stderr or as_owner.stdout).strip())
            return 1

        # A Findings block normally holds several findings with different
        # dispositions, written as free prose on one line or wrapped across
        # several — `review-entry-extent` covers the wrapped shape. The
        # evidence taken from a marker is what follows *that* marker, not the
        # rest of the text — otherwise the first `Resolved here:` swallows
        # every disposition after it, and a block mixing a fix with a
        # tracker-owned follow-up is refused on the follow-up's URL. Measured
        # on this change's own task 1.3 before it was fixed.
        mixed = complete(
            "the counter's own line arithmetic was wrong. Resolved here: M1. "
            "Second, nothing warned that the CLI was four minors old. "
            f"Durable owner: {TRACKER_OWNER}"
        )
        if mixed.returncode != 0:
            report(
                "findings-resolved-here: M1 a block holding a resolved finding "
                "and a tracker-owned one was refused; the resolved marker must "
                "not reach past its own evidence."
            )
            report((mixed.stderr or mixed.stdout).strip())
            return 1

        second_bare = complete(
            "the first was fixed. Resolved here: M1. The second was too. "
            "Resolved here:"
        )
        if second_bare.returncode != 3:
            report(
                "findings-resolved-here: M2 every resolved marker must be "
                "checked, not only the first; a block whose second names no "
                f"evidence exited {second_bare.returncode}, not 3."
            )
            report((second_bare.stderr or second_bare.stdout).strip())
            return 1
        if not problems(second_bare, "finding-resolution-evidence"):
            report(
                "findings-resolved-here: M2 the second resolved marker was not "
                "reported as missing its evidence."
            )
            return 1

        # M3 — the general refusal has to name the form that now exists.
        unowned = complete("a finding with no disposition at all")
        owner_message = problems(unowned, "finding-owner")
        if unowned.returncode != 3:
            report(
                "findings-resolved-here: M3 a finding with no disposition "
                f"exited {unowned.returncode}, not 3."
            )
            report((unowned.stderr or unowned.stdout).strip())
            return 1
        for phrase in ("Resolved here", "M<n>", "Discard reason", "Durable owner"):
            if phrase not in owner_message:
                report(
                    "findings-resolved-here: M3 the accepted-forms message must "
                    f"name every disposition; {phrase!r} is missing from it."
                )
                report(owner_message or "(no finding-owner problem)")
                return 1

    # M4 — the criterion is stated where the author reads it, and the portable
    # skill and its projection do not disagree about it.
    canonical = ROOT / "src/skills/review-checklist/SKILL.md"
    projected = ROOT / "plugins/keel/skills/review-checklist/SKILL.md"
    if canonical.read_bytes() != portable_projection_bytes(projected):
        report(
            "findings-resolved-here: M4 the portable checklist and its plugin "
            "projection are not byte-identical."
        )
        return 1
    checklist = canonical.read_text(encoding="utf-8")
    for phrase in ("Resolved here:", "Durable owner:", "Discard reason:"):
        if phrase not in checklist:
            report(
                "findings-resolved-here: M4 review-checklist does not name "
                f"the {phrase!r} disposition."
            )
            return 1
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    if "Resolved here:" not in agents:
        report(
            "findings-resolved-here: M4 AGENTS.md does not name the "
            "`Resolved here:` disposition."
        )
        return 1

    if "findings-resolved-here" not in {name for name, _ in registry.SCENARIOS}:
        report("findings-resolved-here: the scenario registry does not include it.")
        return 1
    report("findings-resolved-here scenario passed.")
    return 0


# A task whose Review entries are supplied verbatim, so a fixture can wrap one
# across lines. Everything outside the Review block is the complete, checked
# shape `tracker_owner_tasks` uses; only the four entries and the sibling below
# them vary.
def review_extent_tasks(review: str, blocker: str = "none") -> str:
    return (
        "# Tasks\n\n## Invalidates\n\n- None.\n\n"
        "## Expectation Coverage\n\n"
        "- E1:\n"
        "  - Covered by: 1.1\n\n"
        "## 1. Work\n\n"
        "- [x] 1.1 Complete behavior\n"
        "  - Owner: keel-agent\n"
        "  - Mode: implementation\n"
        "  - Covers:\n"
        "    - E1: public behavior\n"
        "  - Read:\n"
        "    - README.md\n"
        "  - Touch:\n"
        "    - src/feature.js\n"
        "  - Verification Strategy: evidence-first\n"
        "  - Verification Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "  - Commands:\n"
        "    - M1: node test.js\n"
        "  - Acceptance:\n"
        "    - Public behavior passes.\n"
        "  - Autonomy boundary:\n"
        "    - Default: hard-stop\n"
        "    - Pre-authorized fallback: none\n"
        "  - Coupling: none\n"
        "  - Candidate Boundary:\n"
        "    - One candidate.\n"
        "  - Stop Rules:\n"
        "    - Stop on failure.\n"
        "  - Evidence:\n"
        "    - Contract: pending\n"
        "    - M1: passed\n"
        "    - Review:\n"
        f"{review}"
        f"    - Blocker: {blocker}\n"
        "  - Stop if:\n"
        "    - Scope expands.\n"
        "  - Report:\n"
        "    - Summary\n"
    )


def validate_review_entry_extent_scenario() -> int:
    """A Review entry is the text the author wrote under its label.

    Issue #49's first supplement. `reviewValue()` matched each Review entry
    with a line-anchored regex, so an entry that wrapped was judged by its
    first line and every continuation line was discarded before any check saw
    it. A `Findings` recording its `Durable owner:` on the fourth line was
    refused with the owner present, the path existing, and the form correct.

    The same truncation failed open, which #49 does not report: a `Findings`
    reading `none` on its first line and recording an unowned finding below it
    produced no problem at all, because the check tested `none` and never saw
    the rest.

    Both directions are driven through `keel gate task-complete` on real
    repositories, and the widened read is bounded at the sibling entry so that
    one entry cannot be satisfied by another's text.
    """
    label = "review-entry-extent"
    # Outside the selected change's own directory on purpose: a path under
    # `openspec/changes/demo/` is refused as a durable owner because that
    # directory moves at archive, and this scenario is about how far a wrapped
    # Findings entry extends, not about which owner forms are accepted.
    owner_path = "openspec/FOLLOWUP.md"

    with tempfile.TemporaryDirectory(
        prefix="keel-review-extent-", ignore_cleanup_errors=True
    ) as raw:
        repo = Path(raw)
        tasks = repo / "openspec/changes/demo/tasks.md"
        write_text(repo / "openspec/changes/demo/proposal.md", "# Proposal\n")
        write_text(repo / owner_path, "# Follow-ups\n")
        write_text(
            repo / "openspec/changes/demo/specs/demo/spec.md",
            "## ADDED Requirements\n",
        )

        def complete(review: str, blocker: str = "none") -> dict | None:
            write_text(tasks, review_extent_tasks(review, blocker))
            if not record_contract_anchor(repo, "demo"):
                return None
            result = run_keel(
                repo, "gate", "task-complete", ".",
                "--change", "demo", "--task", "1.1", "--json",
            )
            return json.loads(result.stdout) if result.stdout.strip() else {}

        def codes(payload: dict) -> list[str]:
            return sorted(
                item.get("code", "") for item in payload.get("problems", [])
            )

        def owner_problems(payload: dict) -> list[str]:
            return [
                item.get("message", "")
                for item in payload.get("problems", [])
                if item.get("code") == "finding-owner"
            ]

        def readable(payload: dict | None, fixture: str) -> bool:
            if payload is None:
                report(
                    f"{label} could not record a Contract anchor for {fixture}: "
                    "task-start refused the fixture, so task-complete never ran "
                    "against it."
                )
                return False
            if not payload:
                report(
                    f"{label} got no JSON from task-complete for {fixture}, so "
                    "there was no verdict to read rather than a verdict that "
                    "was wrong."
                )
                return False
            return True

        def review_block(findings: str, status: str = "pass") -> str:
            return (
                f"      - Status: {status}\n"
                "      - Acceptance check: reviewed\n"
                "      - Scope check: reviewed\n"
                f"{findings}"
            )

        # M1 — the reported defect. The same finding is written twice: wrapped
        # across four indented lines with the owner on the last, and joined
        # onto one line with no word changed. The pair is compared as well as
        # pinned absolutely, because a comparison alone passes when both forms
        # are refused identically.
        wrapped_owner = (
            "      - Findings: two behaviors of state sync turned up in "
            "measurement.\n"
            "        First, the watcher fires per property rather than once "
            "per object.\n"
            "        Second, a class-typed property does not update on the "
            "child side.\n"
            f"        Durable owner: {owner_path}\n"
        )
        joined_owner = (
            "      - Findings: two behaviors of state sync turned up in "
            "measurement. First, the watcher fires per property rather than "
            "once per object. Second, a class-typed property does not update "
            f"on the child side. Durable owner: {owner_path}\n"
        )
        forms = {
            "wrapped": complete(review_block(wrapped_owner)),
            "joined": complete(review_block(joined_owner)),
        }
        for form, payload in forms.items():
            if not readable(payload, f"owner-{form}"):
                return 1
            stray = owner_problems(payload)
            if stray:
                report(
                    f"{label} refused a durable owner the author recorded, with "
                    f"the finding written {form}. The owner is named after "
                    "`Durable owner:` and the path exists."
                )
                report(repr(stray))
                return 1
        if codes(forms["wrapped"]) != codes(forms["joined"]):
            report(
                f"{label} returned different problems for the same finding "
                "depending on whether it wrapped."
            )
            report(f"wrapped={codes(forms['wrapped'])} joined={codes(forms['joined'])}")
            return 1

        # M2 — the silent half. `none` on the first line, a real finding under
        # it. At 5.27.0 this produced no problem at all.
        below_none = complete(
            review_block(
                "      - Findings: none\n"
                "        Actually the retry path still drops the last error.\n"
                "        Nobody owns this and no reason is given for dropping "
                "it.\n"
            )
        )
        if not readable(below_none, "finding-below-none"):
            return 1
        if not owner_problems(below_none):
            report(
                f"{label} accepted a finding written below a `none` first "
                "line. The gate read the word `none` and not the finding under "
                "it."
            )
            report(repr(codes(below_none)))
            return 1

        # M3 — the sibling bound. The wrapped `Findings` carries no disposition
        # of its own; the `- Blocker:` entry below it does. Reading the entry
        # whole must not let the sibling's text satisfy it.
        absorbing = complete(
            review_block(
                "      - Findings: the helper rewrote its own baseline path.\n"
                "        Nothing here names who owns it.\n"
            ),
            blocker=f"none. Durable owner: {owner_path}",
        )
        if not readable(absorbing, "sibling-bound"):
            return 1
        if not owner_problems(absorbing):
            report(
                f"{label} let a `Findings` with no disposition be satisfied by "
                "the sibling entry below it. A widened read must still stop at "
                "its sibling."
            )
            report(repr(codes(absorbing)))
            return 1

        # M4 — the unwrapped shape, which is what all 640 archived Review
        # entries use. The expected message is written out rather than compared
        # against another run of the same build, so a change that altered the
        # text in both places would still fail here.
        unwrapped = complete(
            review_block("      - Findings: a finding with no disposition\n")
        )
        if not readable(unwrapped, "unwrapped"):
            return 1
        unwrapped_owner = owner_problems(unwrapped)
        if len(unwrapped_owner) != 1:
            report(
                f"{label} did not produce exactly one `finding-owner` problem "
                "for an unwrapped finding with no disposition."
            )
            report(repr(codes(unwrapped)))
            return 1
        for phrase in (
            "Review Findings must be `none` or carry a disposition — name a "
            "path after `Durable owner:`",
            "Resolved here:",
            "Durable owner:",
            "Discard reason:",
            "keel/HANDOFF.md",
        ):
            if phrase not in unwrapped_owner[0]:
                report(
                    f"{label} the unwrapped refusal's message changed; "
                    f"{phrase!r} is no longer in it. This change moves how much "
                    "text is read, not what the gate says."
                )
                report(unwrapped_owner[0])
                return 1
        passing = complete(
            review_block(f"      - Findings: still open. Durable owner: {owner_path}\n")
        )
        if not readable(passing, "unwrapped-owned"):
            return 1
        if owner_problems(passing):
            report(
                f"{label} refused an unwrapped finding that names an existing "
                "path after `Durable owner:`."
            )
            report(repr(owner_problems(passing)))
            return 1

    if "review-entry-extent" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


# A task whose Reauthorizations entry is supplied verbatim, so a fixture can
# leave it out entirely, wrap it, or plant an unfilled token on either the
# label line or a continuation line. Everything else is the complete, checked
# shape `review_extent_tasks` uses; only the Reauthorizations line (or its
# absence) and Blocker vary.
def reauthorizations_tasks(reauthorizations: str, blocker: str = "none") -> str:
    return (
        "# Tasks\n\n## Invalidates\n\n- None.\n\n"
        "## Expectation Coverage\n\n"
        "- E1:\n"
        "  - Covered by: 1.1\n\n"
        "## 1. Work\n\n"
        "- [x] 1.1 Complete behavior\n"
        "  - Owner: keel-agent\n"
        "  - Mode: implementation\n"
        "  - Covers:\n"
        "    - E1: public behavior\n"
        "  - Read:\n"
        "    - README.md\n"
        "  - Touch:\n"
        "    - src/feature.js\n"
        "  - Verification Strategy: evidence-first\n"
        "  - Verification Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "  - Commands:\n"
        "    - M1: node test.js\n"
        "  - Acceptance:\n"
        "    - Public behavior passes.\n"
        "  - Autonomy boundary:\n"
        "    - Default: hard-stop\n"
        "    - Pre-authorized fallback: none\n"
        "  - Coupling: none\n"
        "  - Candidate Boundary:\n"
        "    - One candidate.\n"
        "  - Stop Rules:\n"
        "    - Stop on failure.\n"
        "  - Evidence:\n"
        "    - Contract: pending\n"
        "    - M1: passed\n"
        "    - Review:\n"
        "      - Status: pass\n"
        "      - Acceptance check: reviewed\n"
        "      - Scope check: reviewed\n"
        "      - Findings: none\n"
        f"    - Blocker: {blocker}\n"
        f"{reauthorizations}"
        "  - Stop if:\n"
        "    - Scope expands.\n"
        "  - Report:\n"
        "    - Summary\n"
    )


def validate_reauthorizations_shape_scenario() -> int:
    """A rejection becomes a Reauthorizations entry the author writes (#70).

    The owner chose R2 over R3 on issue #70: the task author records what a
    gate rejected themselves, in a new `Reauthorizations` Evidence entry; the
    gate adds no write of its own and validates only the entry's shape. This
    drives that shape check through `keel gate task-complete` on real
    repositories: absence and `none` need nothing, a concrete record — wrapped
    or joined — is accepted, an unfilled `<slot>` token is refused even when it
    only appears on a continuation line the label line itself does not carry,
    and a concrete record never blocks completion the way a concrete `Blocker`
    does.
    """
    label = "reauthorizations-shape"
    baseline_reauthorizations = "    - Reauthorizations: none\n"
    baseline_blocker = "    - Blocker: none\n"

    with tempfile.TemporaryDirectory(
        prefix="keel-reauthorizations-shape-", ignore_cleanup_errors=True
    ) as raw:
        repo = Path(raw)
        tasks = repo / "openspec/changes/demo/tasks.md"
        write_text(repo / "openspec/changes/demo/proposal.md", "# Proposal\n")
        write_text(
            repo / "openspec/changes/demo/specs/demo/spec.md",
            "## ADDED Requirements\n",
        )

        # Started once, with clean Evidence, and every variant below edits
        # only the Reauthorizations/Blocker lines and calls task-complete
        # directly rather than restarting. Two things make restarting wrong
        # here: Evidence is not part of the compiled capsule that task-start
        # fingerprints, so editing only these lines cannot drift it; and
        # task-start separately enforces its own blanket "Evidence must be
        # concrete" check across the whole field regardless of which label an
        # unfilled `<slot>` sits under, so planting one for M1 and then
        # restarting would be refused there before task-complete's more
        # specific `reauthorizations-shape` ever saw it.
        write_text(tasks, reauthorizations_tasks(baseline_reauthorizations))
        if not record_contract_anchor(repo, "demo"):
            report(f"{label} could not record a Contract anchor for the baseline fixture.")
            return 1
        baseline = tasks.read_text(encoding="utf-8")
        if baseline_reauthorizations not in baseline or baseline_blocker not in baseline:
            report(
                f"{label} lost track of the baseline Reauthorizations/Blocker "
                "lines after task-start recorded the Contract anchor."
            )
            return 1

        def complete(reauthorizations: str, blocker: str = "none") -> dict:
            text = baseline.replace(baseline_reauthorizations, reauthorizations, 1)
            if blocker != "none":
                text = text.replace(baseline_blocker, f"    - Blocker: {blocker}\n", 1)
            write_text(tasks, text)
            result = run_keel(
                repo, "gate", "task-complete", ".",
                "--change", "demo", "--task", "1.1", "--json",
            )
            return json.loads(result.stdout) if result.stdout.strip() else {}

        def codes(payload: dict) -> list[str]:
            return sorted(
                item.get("code", "") for item in payload.get("problems", [])
            )

        def shape_problems(payload: dict) -> list[str]:
            return [
                item.get("message", "")
                for item in payload.get("problems", [])
                if item.get("code") == "reauthorizations-shape"
            ]

        def readable(payload: dict, fixture: str) -> bool:
            if not payload:
                report(
                    f"{label} got no JSON from task-complete for {fixture}, so "
                    "there was no verdict to read rather than a verdict that "
                    "was wrong."
                )
                return False
            return True

        # M1 — the core new behavior, in both places an unfilled token can
        # hide: on the label line itself, and on a continuation line a
        # first-line-only reader would never see.
        on_label_line = complete("    - Reauthorizations: <what was rejected>\n")
        if not readable(on_label_line, "unfilled-on-label-line"):
            return 1
        if not shape_problems(on_label_line):
            report(
                f"{label} accepted an unfilled `<slot>` token written on the "
                "Reauthorizations label line itself."
            )
            report(repr(codes(on_label_line)))
            return 1
        if "<what was rejected>" not in shape_problems(on_label_line)[0]:
            report(f"{label} refused the unfilled token but did not name it.")
            report(shape_problems(on_label_line)[0])
            return 1

        on_continuation = complete(
            "    - Reauthorizations:\n"
            "      - task-complete refused finding-owner on 2026-08-05; added\n"
            "        a Durable owner naming <the tracker issue>.\n"
        )
        if not readable(on_continuation, "unfilled-on-continuation-line"):
            return 1
        if not shape_problems(on_continuation):
            report(
                f"{label} accepted an unfilled `<slot>` token written on a "
                "continuation line below the Reauthorizations label. A reader "
                "that only looks at the first line would miss it."
            )
            report(repr(codes(on_continuation)))
            return 1
        if "<the tracker issue>" not in shape_problems(on_continuation)[0]:
            report(
                f"{label} refused the continuation-line token but did not "
                "name it."
            )
            report(shape_problems(on_continuation)[0])
            return 1

        # M2 (regression) — no false positives: absent, none, and a wrapped
        # concrete record all pass, and wrapped/joined forms of the same
        # concrete text agree.
        absent = complete("")
        if not readable(absent, "absent"):
            return 1
        if shape_problems(absent):
            report(
                f"{label} refused a task that declares no Reauthorizations "
                "entry at all."
            )
            report(repr(shape_problems(absent)))
            return 1

        bare_none = complete("    - Reauthorizations: none\n")
        if not readable(bare_none, "bare-none"):
            return 1
        if shape_problems(bare_none):
            report(f"{label} refused a bare `Reauthorizations: none`.")
            report(repr(shape_problems(bare_none)))
            return 1

        wrapped_concrete = complete(
            "    - Reauthorizations:\n"
            "      - task-complete refused outside-touch on src/helper.js on\n"
            "        2026-08-05; the file belonged to this task and Touch was\n"
            "        missing it, so it was added.\n"
        )
        joined_concrete = complete(
            "    - Reauthorizations: task-complete refused outside-touch on "
            "src/helper.js on 2026-08-05; the file belonged to this task and "
            "Touch was missing it, so it was added.\n"
        )
        if not readable(wrapped_concrete, "wrapped-concrete"):
            return 1
        if not readable(joined_concrete, "joined-concrete"):
            return 1
        if shape_problems(wrapped_concrete):
            report(f"{label} refused a concrete, wrapped Reauthorizations record.")
            report(repr(shape_problems(wrapped_concrete)))
            return 1
        if codes(wrapped_concrete) != codes(joined_concrete):
            report(
                f"{label} returned different problems for the same concrete "
                "record depending on whether it wrapped."
            )
            report(
                f"wrapped={codes(wrapped_concrete)} joined={codes(joined_concrete)}"
            )
            return 1

        # M3 (regression) — presence does not block completion, unlike
        # Blocker. Proven able to fail: a concrete Blocker on the same
        # repository does fail it, so the comparison is not vacuous.
        if codes(wrapped_concrete):
            report(
                f"{label} a concrete Reauthorizations record produced a "
                "problem — presence alone must not fail completion."
            )
            report(repr(codes(wrapped_concrete)))
            return 1
        concrete_blocker = complete("", blocker="a real blocker is recorded here")
        if not readable(concrete_blocker, "concrete-blocker"):
            return 1
        if "blocker" not in codes(concrete_blocker):
            report(
                f"{label} the comparison fixture proves nothing: a concrete "
                "Blocker on this repository did not fail completion either."
            )
            report(repr(codes(concrete_blocker)))
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_task_capsule_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-task-capsule-") as raw_tmp:
        repo = Path(raw_tmp)
        write_text(
            repo / "openspec/changes/demo/tasks.md",
            task_capsule_expanded_fixture(),
        )
        started = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if started.returncode != 0:
            report("task-capsule rejected a valid expanded task.")
            report((started.stderr or started.stdout).strip())
            return 1
        payload = json.loads(started.stdout)
        contract = payload.get("contract", {})
        capsule = contract.get("capsule", {})
        fingerprint = contract.get("fingerprint", {})
        if (
            contract.get("schema") != "keel-task-capsule/v1"
            or capsule.get("schema") != "keel-task-capsule/v1"
            or capsule.get("task", {}).get("id") != "1.1"
            or capsule.get("mode") != "implementation"
            or fingerprint.get("algorithm") != "sha256"
            or not re.fullmatch(r"[0-9a-f]{64}", fingerprint.get("value", ""))
            or hashlib.sha256(
                json.dumps(
                    capsule,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            != fingerprint.get("value")
        ):
            report("task-capsule task-start omitted its normalized contract.")
            report(started.stdout.strip())
            return 1

        human_start = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
        )
        if (
            human_start.returncode != 0
            or f"Fingerprint: sha256:{fingerprint.get('value')}" not in human_start.stdout
            or '"authority"' in human_start.stdout
        ):
            report("task-capsule human output omitted or dumped contract detail.")
            report((human_start.stderr or human_start.stdout).strip())
            return 1

        completion_task = (
            task_capsule_expanded_fixture()
            .replace("    - M1: pending\n", "    - M1: passed\n")
            .replace("      - Status: pending\n", "      - Status: pass\n")
            .replace(
                "      - Acceptance check: pending\n",
                "      - Acceptance check: public behavior reviewed\n",
            )
            .replace(
                "      - Scope check: pending\n",
                "      - Scope check: Touch reviewed\n",
            )
            .replace("      - Findings: pending\n", "      - Findings: none\n")
        )
        write_text(
            repo / "openspec/changes/demo/tasks.md",
            completion_task,
        )
        record_contract_anchor(repo, "demo")
        completed = run_keel(
            repo,
            "gate",
            "task-complete",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        completed_contract = json.loads(completed.stdout).get("contract", {})
        if (
            completed.returncode != 0
            or completed_contract.get("fingerprint") != fingerprint
        ):
            report("task-capsule task-complete did not reuse the start contract.")
            report((completed.stderr or completed.stdout).strip())
            return 1

        write_text(
            repo / "openspec/changes/demo/tasks.md",
            task_capsule_compact_fixture(),
        )
        compact = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if compact.returncode != 0:
            report("task-capsule rejected a compact equivalent task.")
            report((compact.stderr or compact.stdout).strip())
            return 1
        compact_contract = json.loads(compact.stdout).get("contract", {})
        if (
            compact_contract.get("capsule") != capsule
            or compact_contract.get("fingerprint") != fingerprint
        ):
            report("task-capsule compact and expanded authority diverged.")
            report(compact.stdout.strip())
            return 1

        conflicting_task = task_capsule_compact_fixture().replace(
            "  - Verify:\n",
            "  - Verification Strategy: vertical-tdd\n"
            "  - Commands:\n"
            "    - M1: node conflicting-test.js\n"
            "  - Verify:\n",
        )
        write_text(
            repo / "openspec/changes/demo/tasks.md",
            conflicting_task,
        )
        conflicting = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if (
            conflicting.returncode != 3
            or not any(
                item.get("code") == "legacy-field-conflict"
                for item in json.loads(conflicting.stdout).get("problems", [])
            )
        ):
            report("task-capsule silently preferred conflicting legacy fields.")
            report((conflicting.stderr or conflicting.stdout).strip())
            return 1

        contradictory_coupling = task_capsule_compact_fixture() + (
            "  - Coupling: none\n"
            "  - Candidate Boundary:\n"
            "    - Candidate A regenerates output.\n"
        )
        write_text(
            repo / "openspec/changes/demo/tasks.md",
            contradictory_coupling,
        )
        contradictory = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if (
            contradictory.returncode != 3
            or not any(
                item.get("code") == "contradictory-coupling-authority"
                for item in json.loads(contradictory.stdout).get("problems", [])
            )
        ):
            report("task-capsule accepted contradictory compact coupling fields.")
            report((contradictory.stderr or contradictory.stdout).strip())
            return 1

        minimal_compact = (
            task_capsule_compact_fixture()
            .replace(
                "  - Read:\n"
                "    - README.md\n",
                "",
            )
            .replace(
                "  - Autonomy boundary:\n"
                "    - Default: hard-stop\n"
                "    - Pre-authorized fallback: none\n",
                "",
            )
            .replace(
                "  - Stop Rules:\n"
                "    - Stop on failure.\n",
                "",
            )
            .replace(
                "  - Stop if:\n"
                "    - Requires files outside Touch.\n",
                "",
            )
        )
        write_text(
            repo / "openspec/changes/demo/tasks.md",
            minimal_compact,
        )
        minimal = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        minimal_capsule = (
            json.loads(minimal.stdout)
            .get("contract", {})
            .get("capsule", {})
        )
        expected_base_read = [
            "openspec/changes/demo/design.md",
            "openspec/changes/demo/proposal.md",
            "openspec/changes/demo/specs/**/*.md",
            "openspec/changes/demo/tasks.md",
        ]
        if (
            minimal.returncode != 0
            or minimal_capsule.get("read") != expected_base_read
            or minimal_capsule.get("boundaries", {}).get("autonomy")
            != ["Default: hard-stop", "Pre-authorized fallback: none"]
        ):
            report("task-capsule omitted compact Read or hard-stop defaults.")
            report((minimal.stderr or minimal.stdout).strip())
            return 1

        mutable_task = (
            task_capsule_compact_fixture()
            .replace(
                "- [ ] 1.1 Exercise task contract",
                "- [x] 1.1 Exercise   task contract <!-- presentation only -->",
            )
            .replace(
                "E1: Public behavior passes.",
                "E1: Public   behavior passes. <!-- presentation only -->",
            )
            .replace("M1: node test.js", "M1: node    test.js")
            .replace(
                "    - M1: pending\n",
                "    - M1: passed\n"
                "    - Review:\n"
                "      - Status: pass\n"
                "      - Acceptance check: reviewed\n"
                "      - Scope check: reviewed\n"
                "      - Findings: none\n",
            )
            + "  - Report:\n"
            "    - Mutable completion report\n"
        )
        write_text(
            repo / "openspec/changes/demo/tasks.md",
            mutable_task,
        )
        mutable = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        mutable_contract = json.loads(mutable.stdout).get("contract", {})
        if (
            mutable.returncode != 0
            or mutable_contract.get("fingerprint") != fingerprint
        ):
            report("task-capsule mutable completion data drifted the fingerprint.")
            report((mutable.stderr or mutable.stdout).strip())
            return 1

        write_text(
            repo / "openspec/changes/demo/design.md",
            "## Coupled Iteration Contract\n\n"
            "- Coupled artifacts: source and generated output\n"
            "- Invalidation triggers: source changes\n"
            "- Required regeneration: rebuild output\n"
            "- Final assertions: source and output agree\n"
            "- Conflict authority: source wins\n"
            "- Baseline policy: preserve existing bytes\n",
        )
        coupled_a = task_capsule_compact_fixture() + (
            "  - Coupling: required\n"
            "  - Candidate Boundary:\n"
            "    - Candidate A regenerates the output.\n"
        )
        write_text(repo / "openspec/changes/demo/tasks.md", coupled_a)
        coupled_a_result = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        coupled_a_contract = json.loads(coupled_a_result.stdout).get("contract", {})
        coupled_b = coupled_a.replace("Candidate A", "Candidate B")
        write_text(repo / "openspec/changes/demo/tasks.md", coupled_b)
        coupled_b_result = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        coupled_b_contract = json.loads(coupled_b_result.stdout).get("contract", {})
        if (
            coupled_a_result.returncode != 0
            or coupled_b_result.returncode != 0
            or coupled_a_contract.get("fingerprint")
            == coupled_b_contract.get("fingerprint")
        ):
            report("task-capsule omitted coupled candidate authority.")
            report(
                (coupled_b_result.stderr or coupled_b_result.stdout).strip()
            )
            return 1

        coupled_b_fingerprint = coupled_b_contract.get("fingerprint")
        write_text(
            repo / "openspec/changes/demo/design.md",
            (repo / "openspec/changes/demo/design.md")
            .read_text(encoding="utf-8")
            .replace(
                "Final assertions: source and output agree",
                "Final assertions: source, output, and snapshot agree",
            ),
        )
        write_text(repo / "openspec/changes/demo/tasks.md", coupled_b)
        coupled_design_result = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        coupled_design_contract = json.loads(coupled_design_result.stdout).get(
            "contract", {}
        )
        if (
            coupled_design_result.returncode != 0
            or coupled_design_contract.get("fingerprint") == coupled_b_fingerprint
        ):
            report("task-capsule omitted coupled design authority.")
            report(
                (coupled_design_result.stderr or coupled_design_result.stdout).strip()
            )
            return 1

        unordered_a = (
            task_capsule_compact_fixture()
            .replace(
                "    - E1: Public behavior passes.\n",
                "    - E1: Public behavior passes.\n"
                "    - E2: Secondary behavior passes.\n",
            )
            .replace(
                "    - README.md\n",
                "    - README.md\n"
                "    - docs/guide.md\n",
            )
            .replace(
                "    - src/feature.js\n",
                "    - src/feature.js\n"
                "    - tests/feature.test.js\n",
            )
        )
        unordered_b = (
            unordered_a
            .replace(
                "    - E1: Public behavior passes.\n"
                "    - E2: Secondary behavior passes.\n",
                "    - E2: Secondary behavior passes.\n"
                "    - E1: Public behavior passes.\n",
            )
            .replace(
                "    - README.md\n"
                "    - docs/guide.md\n",
                "    - docs/guide.md\n"
                "    - README.md\n",
            )
            .replace(
                "    - src/feature.js\n"
                "    - tests/feature.test.js\n",
                "    - tests/feature.test.js\n"
                "    - src/feature.js\n",
            )
        )
        unordered_contracts = []
        for task_text in (unordered_a, unordered_b):
            write_text(repo / "openspec/changes/demo/tasks.md", task_text)
            result = run_keel(
                repo,
                "gate",
                "task-start",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
            )
            if result.returncode != 0:
                report("task-capsule rejected unordered authority fixture.")
                report((result.stderr or result.stdout).strip())
                return 1
            unordered_contracts.append(json.loads(result.stdout).get("contract", {}))
        if (
            unordered_contracts[0].get("fingerprint")
            != unordered_contracts[1].get("fingerprint")
        ):
            report("task-capsule unordered presentation drifted the fingerprint.")
            return 1

        drift_variants = {
            "expectation": task_capsule_compact_fixture().replace(
                "Public behavior passes.", "Changed behavior passes."
            ),
            "mode": task_capsule_compact_fixture().replace(
                "  - Covers:\n", "  - Mode: plan-first\n  - Covers:\n"
            ),
            "scope": task_capsule_compact_fixture().replace(
                "src/feature.js", "src/changed-feature.js"
            ),
            "acceptance": task_capsule_compact_fixture().replace(
                "  - Verify:\n",
                "  - Acceptance:\n"
                "    - Additional observable boundary.\n"
                "  - Verify:\n",
            ),
            "verification": task_capsule_compact_fixture().replace(
                "node test.js", "node changed-test.js"
            ),
            "stop": task_capsule_compact_fixture().replace(
                "Stop on failure.", "Stop on any failed public check."
            ),
        }
        for dimension, task_text in drift_variants.items():
            write_text(repo / "openspec/changes/demo/tasks.md", task_text)
            drifted = run_keel(
                repo,
                "gate",
                "task-start",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
            )
            drifted_contract = json.loads(drifted.stdout).get("contract", {})
            if (
                drifted.returncode != 0
                or drifted_contract.get("fingerprint") == fingerprint
            ):
                report(f"task-capsule {dimension} authority did not drift.")
                report((drifted.stderr or drifted.stdout).strip())
                return 1

        if (
            capsule.get("defaultsVersion") != 1
            or capsule.get("prohibitions")
            != [
                "must not change Acceptance",
                "must not commit",
                "must not push",
                "must not sync or archive",
            ]
        ):
            report("task-capsule omitted default or prohibition authority.")
            return 1

        close_task = (
            completion_task
            .replace("# Tasks\n\n## Invalidates\n\n- None.\n\n", "# Tasks\n\n## Invalidates\n\n- None.\n\n## Expectation Coverage\n\n"
                     "- E1:\n  - Covered by: 1.1\n\n## 1. Work\n\n")
            .replace("- [ ] 1.1", "- [x] 1.1")
        )
        write_text(repo / "openspec/changes/demo/tasks.md", close_task)
        write_text(repo / "openspec/changes/demo/proposal.md", "# Proposal\n")
        write_text(
            repo / "openspec/changes/demo/specs/demo/spec.md",
            "## ADDED Requirements\n",
        )
        # `--record` as well as compile: the close compares each checked task's
        # anchor, so a fixture that only read the fingerprint would be closing a
        # change whose task never recorded the contract it completed under.
        close_start = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--record",
            "--no-guard",
            "--json",
        )
        close_fingerprint = (
            json.loads(close_start.stdout)
            .get("contract", {})
            .get("fingerprint")
        )
        close = run_keel(
            repo,
            "gate",
            "change-close",
            "--change",
            "demo",
            "--action",
            "sync",
            "--json",
        )
        close_payload = json.loads(close.stdout)
        close_contracts = close_payload.get("contracts", [])
        if (
            close.returncode != 0
            or len(close_contracts) != 1
            or close_contracts[0].get("task") != "1.1"
            or close_contracts[0].get("contract", {}).get("fingerprint")
            != close_fingerprint
        ):
            report("task-capsule change-close did not reuse task contracts.")
            report((close.stderr or close.stdout).strip())
            return 1

    report("task-capsule scenario passed.")
    return 0


def validate_core_gates_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-gates-") as raw_tmp:
        root = Path(raw_tmp)
        repo = root / "task-start"
        repo.mkdir()
        tasks_path = repo / "openspec/changes/demo/tasks.md"
        write_text(
            tasks_path,
            "# Tasks\n\n## Invalidates\n\n- None.\n\n"
            "- [ ] 1.1 Incomplete task\n"
            "  - Owner: keel-agent\n",
        )

        incomplete = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if incomplete.returncode != 3:
            report("core-gates scenario task-start did not use policy-fail exit 3.")
            report((incomplete.stderr or incomplete.stdout).strip())
            return 1
        incomplete_payload = json.loads(incomplete.stdout)
        if (
            incomplete_payload.get("schemaVersion") != 1
            or incomplete_payload.get("gate") != "task-start"
            or incomplete_payload.get("status") != "fail"
            or not any(
                "Covers" in problem.get("message", "")
                for problem in incomplete_payload.get("problems", [])
            )
        ):
            report("core-gates scenario task-start failure contract mismatch.")
            report(incomplete.stdout.strip())
            return 1

        write_text(
            tasks_path,
            "# Tasks\n\n## Invalidates\n\n- None.\n\n"
            "- [ ] 1.1 Complete executable task\n"
            "  - Owner: keel-agent\n"
            "  - Mode: implementation\n"
            "  - Covers:\n"
            "    - E1: public behavior\n"
            "  - Read:\n"
            "    - README.md\n"
            "  - Touch:\n"
            "    - src/feature.js\n"
            "    - openspec/changes/demo/tasks.md\n"
            "  - Verification Strategy: evidence-first\n"
            "  - Verification Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
            "  - Commands:\n"
            "    - M1: node test.js\n"
            "  - Acceptance:\n"
            "    - Public behavior passes.\n"
            "  - Autonomy boundary:\n"
            "    - Default: hard-stop\n"
            "    - Pre-authorized fallback: none\n"
            "  - Coupling: none\n"
            "  - Candidate Boundary:\n"
            "    - One complete candidate reaches M1.\n"
            "  - Stop Rules:\n"
            "    - Stop on final assertion failure.\n"
            "  - Evidence:\n"
            "    - M1: pending\n"
            "    - Review:\n"
            "      - Status: pending\n"
            "      - Acceptance check: pending\n"
            "      - Scope check: pending\n"
            "      - Findings: pending\n"
            "    - Blocker: none\n"
            "  - Stop if:\n"
            "    - Requires files outside Touch.\n"
            "  - Report:\n"
            "    - Summary\n",
        )
        before_gate = snapshot_files(repo)
        complete = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        after_gate = snapshot_files(repo)
        if complete.returncode != 0:
            report("core-gates scenario rejected a complete task-start contract.")
            report((complete.stderr or complete.stdout).strip())
            return 1
        complete_payload = json.loads(complete.stdout)
        if (
            complete_payload.get("status") != "pass"
            or complete_payload.get("selection")
            != {"change": "demo", "tasks": ["1.1"]}
        ):
            report("core-gates scenario task-start pass contract mismatch.")
            report(complete.stdout.strip())
            return 1
        inferred_start = run_keel(
            repo,
            "gate",
            "task-start",
            "--json",
        )
        if (
            inferred_start.returncode != 0
            or json.loads(inferred_start.stdout).get("selection")
            != {"change": "demo", "tasks": ["1.1"]}
        ):
            report("core-gates scenario did not conservatively infer a unique task.")
            report((inferred_start.stderr or inferred_start.stdout).strip())
            return 1
        added_paths = set(after_gate) - set(before_gate)
        if added_paths != {"keel/guard.json"} or any(
            before_gate[key] != after_gate[key] for key in before_gate
        ):
            report(
                "core-gates scenario passing task-start must write exactly the "
                "guard manifest and nothing else."
            )
            return 1

        executable_task = tasks_path.read_text(encoding="utf-8")
        unresolved_task = executable_task.replace(
            "E1: public behavior",
            "Q1: unresolved implementation authority",
        )
        write_text(tasks_path, unresolved_task)
        write_text(
            repo / "openspec/changes/demo/design.md",
            "# Design\n\n"
            "## Open Questions\n\n"
            "- Q1 — Which fallback is authorized?\n"
            "  - Basis: fixture uncertainty\n"
            "  - Resolve by: task start\n",
        )
        unresolved = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if (
            unresolved.returncode != 3
            or not any(
                problem.get("code") == "unresolved-authority"
                for problem in json.loads(unresolved.stdout).get("problems", [])
            )
        ):
            report("core-gates scenario allowed unresolved implementation authority.")
            report((unresolved.stderr or unresolved.stdout).strip())
            return 1
        authorized_task = unresolved_task.replace(
            "Pre-authorized fallback: none",
            "Pre-authorized fallback: use the reversible fixture and record M1",
        )
        write_text(tasks_path, authorized_task)
        authorized = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if authorized.returncode != 0:
            report("core-gates scenario rejected documented bounded authority.")
            report((authorized.stderr or authorized.stdout).strip())
            return 1
        write_text(tasks_path, executable_task)

        completion_repo = root / "task-complete"
        completion_repo.mkdir()
        completion_tasks = completion_repo / "openspec/changes/demo/tasks.md"

        def completion_task(
            evidence: str,
            review_status: str,
            findings: str = "none",
        ) -> str:
            return (
                "# Tasks\n\n## Invalidates\n\n- None.\n\n"
                "- [ ] 1.1 Complete behavior\n"
                "  - Owner: keel-agent\n"
                "  - Mode: implementation\n"
                "  - Covers:\n"
                "    - E1: public behavior\n"
                "  - Read:\n"
                "    - README.md\n"
                "  - Touch:\n"
                "    - src/feature.js\n"
                "    - openspec/changes/demo/tasks.md\n"
                "  - Verification Strategy: evidence-first\n"
                "  - Verification Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
                "  - Commands:\n"
                "    - M1: node test.js\n"
                "  - Acceptance:\n"
                "    - Public behavior passes.\n"
                "  - Autonomy boundary:\n"
                "    - Default: hard-stop\n"
                "    - Pre-authorized fallback: none\n"
                "  - Coupling: none\n"
                "  - Candidate Boundary:\n"
                "    - One complete candidate reaches M1.\n"
                "  - Stop Rules:\n"
                "    - Stop on final assertion failure.\n"
                "  - Evidence:\n"
                # Read at call time, so every variant below carries the anchor
                # recorded once for this fixture. Evidence is not in the capsule,
                # so one fingerprint is correct for all of them.
                f"    - Contract: {completion_anchor}\n"
                f"    - M1: {evidence}\n"
                "    - Review:\n"
                f"      - Status: {review_status}\n"
                "      - Acceptance check: public behavior reviewed\n"
                "      - Scope check: Touch reviewed semantically\n"
                f"      - Findings: {findings}\n"
                "    - Blocker: none\n"
                "  - Stop if:\n"
                "    - Requires files outside Touch.\n"
                "  - Report:\n"
                "    - Summary\n"
            )

        completion_anchor = "pending"
        write_text(completion_tasks, completion_task("pending", "pass"))
        if not record_contract_anchor(completion_repo, "demo"):
            report("core-gates scenario could not record the completion anchor.")
            return 1
        recorded_line = re.search(
            r"-\s*Contract:\s*(.+)", completion_tasks.read_text(encoding="utf-8")
        )
        if not recorded_line:
            report("core-gates scenario found no recorded Contract anchor.")
            return 1
        completion_anchor = recorded_line.group(1).strip()

        write_text(completion_tasks, completion_task("pending", "pass"))
        missing_evidence = run_keel(
            completion_repo,
            "gate",
            "task-complete",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if (
            missing_evidence.returncode != 3
            or json.loads(missing_evidence.stdout).get("status") != "fail"
        ):
            report("core-gates scenario missing command evidence did not fail.")
            report((missing_evidence.stderr or missing_evidence.stdout).strip())
            return 1

        write_text(completion_tasks, completion_task("passed", "pending"))
        missing_review = run_keel(
            completion_repo,
            "gate",
            "task-complete",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if (
            missing_review.returncode != 4
            or json.loads(missing_review.stdout).get("status") != "needs-review"
        ):
            report("core-gates scenario missing Review did not need review.")
            report((missing_review.stderr or missing_review.stdout).strip())
            return 1

        write_text(
            completion_tasks,
            completion_task("passed", "pass", "security issue; owner keel/HANDOFF.md"),
        )
        handoff_owner = run_keel(
            completion_repo,
            "gate",
            "task-complete",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        handoff_payload = json.loads(handoff_owner.stdout)
        finding_owner_message = " ".join(
            problem.get("message", "")
            for problem in handoff_payload.get("problems", [])
            if problem.get("code") == "finding-owner"
        )
        if (
            handoff_owner.returncode != 3
            or handoff_payload.get("status") != "fail"
            or "Discard reason" not in finding_owner_message
            or "keel/archive" not in finding_owner_message
            or "openspec/changes" not in finding_owner_message
        ):
            report(
                "core-gates scenario accepted HANDOFF as finding owner or the "
                "finding-owner error did not enumerate the accepted forms."
            )
            report((handoff_owner.stderr or handoff_owner.stdout).strip())
            return 1

        # The accepted-forms enumeration is a menu; the one actionable
        # instruction inside it (name a path after `Durable owner:`) must lead
        # the message, not close it, so a reader who forgot to name a path
        # reads what to do before reading the menu. Three single-cause checks,
        # not one compound condition — issue #43 exists to catch exactly that
        # shape.
        finding_owner_lower = finding_owner_message.lower()
        instruction_at = finding_owner_lower.find(
            "name a path after `durable owner:`"
        )
        if instruction_at < 0:
            report(
                "core-gates scenario: the finding-owner message dropped its "
                "actionable instruction (\"name a path after `Durable "
                "owner:`\")."
            )
            return 1
        resolved_here_at = finding_owner_lower.find("`resolved here:`")
        if resolved_here_at < 0:
            report(
                "core-gates scenario: the finding-owner message dropped its "
                "`Resolved here:` disposition form."
            )
            return 1
        if instruction_at > resolved_here_at:
            report(
                "core-gates scenario: the finding-owner message states its "
                "actionable instruction after the `Resolved here:` form "
                "instead of before it."
            )
            return 1

        write_text(
            completion_tasks,
            completion_task(
                "passed",
                "pass",
                "security issue; owner openspec/changes/follow-up/tasks.md#1.1",
            ),
        )
        write_text(
            completion_repo / "openspec/changes/follow-up/tasks.md",
            "# Tasks\n\n## Invalidates\n\n- None.\n\n- [ ] 1.1 Own the finding\n",
        )
        owned_finding = run_keel(
            completion_repo,
            "gate",
            "task-complete",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if owned_finding.returncode != 0:
            report("core-gates scenario rejected a durable finding owner.")
            report((owned_finding.stderr or owned_finding.stdout).strip())
            return 1

        write_text(completion_tasks, completion_task("passed", "done"))
        done_status = run_keel(
            completion_repo,
            "gate",
            "task-complete",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        if (
            done_status.returncode != 0
            or json.loads(done_status.stdout).get("status") != "pass"
        ):
            report("core-gates scenario rejected an accepted `done` Review Status.")
            report((done_status.stderr or done_status.stdout).strip())
            return 1

        write_text(completion_tasks, completion_task("passed", "reviewed"))
        bad_status = run_keel(
            completion_repo,
            "gate",
            "task-complete",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        bad_status_payload = json.loads(bad_status.stdout)
        bad_status_message = " ".join(
            problem.get("message", "")
            for problem in bad_status_payload.get("problems", [])
        )
        if (
            bad_status.returncode != 4
            or bad_status_payload.get("status") != "needs-review"
            or "Status" not in bad_status_message
            or "done" not in bad_status_message
        ):
            report(
                "core-gates scenario semantic-review did not name Status and list "
                "accepted tokens including done."
            )
            report((bad_status.stderr or bad_status.stdout).strip())
            return 1

        write_text(completion_tasks, completion_task("passed", "pass"))
        write_text(completion_repo / "src/outside.js", "outside\n")
        subprocess.run(
            ["git", "init", "--quiet"],
            cwd=completion_repo,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "keel@example.invalid"],
            cwd=completion_repo,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Keel Fixture"],
            cwd=completion_repo,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "add", "."],
            cwd=completion_repo,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "commit", "--quiet", "-m", "baseline"],
            cwd=completion_repo,
            check=True,
            capture_output=True,
            text=True,
        )
        write_text(completion_repo / "src/outside.js", "outside changed\n")
        before_complete_gate = {
            "tasks": completion_tasks.read_bytes(),
            "outside": (completion_repo / "src/outside.js").read_bytes(),
        }
        offline_env = dict(os.environ)
        offline_env.update(
            {
                "HTTP_PROXY": "http://127.0.0.1:1",
                "HTTPS_PROXY": "http://127.0.0.1:1",
                "OPENAI_API_KEY": "must-not-be-used",
            }
        )
        no_base = run_keel(
            completion_repo,
            "gate",
            "task-complete",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
            env=offline_env,
        )
        after_complete_gate = {
            "tasks": completion_tasks.read_bytes(),
            "outside": (completion_repo / "src/outside.js").read_bytes(),
        }
        no_base_payload = json.loads(no_base.stdout)
        if (
            no_base.returncode != 0
            or not any(
                "not attributed" in warning
                for warning in no_base_payload.get("warnings", [])
            )
        ):
            report("core-gates scenario dirty worktree without base was attributed.")
            report((no_base.stderr or no_base.stdout).strip())
            return 1
        if before_complete_gate != after_complete_gate:
            report("core-gates scenario task-complete mutated project artifacts.")
            return 1

        with_base = run_keel(
            completion_repo,
            "gate",
            "task-complete",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--base",
            "HEAD",
            "--json",
        )
        with_base_payload = json.loads(with_base.stdout)
        if (
            with_base.returncode != 3
            or with_base_payload.get("status") != "fail"
            or not any(
                "src/outside.js" in problem.get("message", "")
                for problem in with_base_payload.get("problems", [])
            )
        ):
            report("core-gates scenario explicit base missed out-of-Touch path.")
            report((with_base.stderr or with_base.stdout).strip())
            return 1

        write_text(completion_repo / "src/outside.js", "outside\n")
        write_text(
            completion_tasks,
            completion_task("passed", "pass").replace(
                "    - src/feature.js\n",
                "    - src/feature.js\n    - src/nested/**\n",
            ),
        )
        # Adding a path to Touch is a contract change, so the anchor is
        # reauthorized here exactly as an author would reauthorize it. Without
        # that step this glob check fails on contract drift and never reaches
        # the question it is asking.
        if not record_contract_anchor(completion_repo, "demo"):
            report("core-gates scenario could not reauthorize the glob contract.")
            return 1
        write_text(completion_repo / "src/nested/deep/file.js", "nested changed\n")
        nested_glob = run_keel(
            completion_repo,
            "gate",
            "task-complete",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--base",
            "HEAD",
            "--json",
        )
        if nested_glob.returncode != 0:
            report(
                "core-gates scenario double-star Touch glob produced a false "
                "outside-touch failure for a nested path."
            )
            report((nested_glob.stderr or nested_glob.stdout).strip())
            return 1

        # The gate's own guard manifest is never attributed outside Touch:
        # completion with an active manifest needs no prior guard clear.
        write_text(
            completion_repo / "keel/guard.json",
            '{"schema": "keel-write-guard/v1"}\n',
        )
        with_manifest = run_keel(
            completion_repo, "gate", "task-complete",
            "--change", "demo", "--task", "1.1",
            "--base", "HEAD", "--json",
        )
        if with_manifest.returncode != 0:
            report(
                "core-gates scenario attributed the gate's own guard manifest "
                "as outside Touch."
            )
            report((with_manifest.stderr or with_manifest.stdout).strip())
            return 1
        write_text(completion_repo / "src/other-outside.js", "outside\n")
        manifest_and_outside = run_keel(
            completion_repo, "gate", "task-complete",
            "--change", "demo", "--task", "1.1",
            "--base", "HEAD", "--json",
        )
        outside_messages = [
            problem.get("message", "")
            for problem in json.loads(manifest_and_outside.stdout).get("problems", [])
        ]
        if (
            manifest_and_outside.returncode != 3
            or not any("src/other-outside.js" in item for item in outside_messages)
            or any("keel/guard.json" in item for item in outside_messages)
        ):
            report(
                "core-gates scenario guard-manifest exemption did not stay "
                "exact: the other outside path must still fail and the "
                "manifest must never be cited."
            )
            report((manifest_and_outside.stderr or manifest_and_outside.stdout).strip())
            return 1
        (completion_repo / "keel/guard.json").unlink()
        (completion_repo / "src/other-outside.js").unlink()

        # The selected change's own authoring artifacts are never attributed
        # outside Touch: completion with dirty proposal/design files of the
        # selected change succeeds under an explicit base, while other
        # changes' directories and the specs tree still fail deterministically.
        write_text(
            completion_repo / "openspec/changes/demo/design.md",
            "## Context\n\nauthoring artifact changed\n",
        )
        with_own_authoring = run_keel(
            completion_repo, "gate", "task-complete",
            "--change", "demo", "--task", "1.1",
            "--base", "HEAD", "--json",
        )
        if with_own_authoring.returncode != 0:
            report(
                "core-gates scenario attributed the selected change's own "
                "authoring artifacts as outside Touch."
            )
            report((with_own_authoring.stderr or with_own_authoring.stdout).strip())
            return 1
        write_text(
            completion_repo / "openspec/changes/other/proposal.md",
            "## Why\n\nunrelated change\n",
        )
        write_text(
            completion_repo / "openspec/specs/demo-spec/spec.md",
            "## Purpose\n\nspec tree changed\n",
        )
        authoring_and_outside = run_keel(
            completion_repo, "gate", "task-complete",
            "--change", "demo", "--task", "1.1",
            "--base", "HEAD", "--json",
        )
        authoring_messages = [
            problem.get("message", "")
            for problem in json.loads(authoring_and_outside.stdout).get("problems", [])
        ]
        if (
            authoring_and_outside.returncode != 3
            or not any(
                "openspec/changes/other/proposal.md" in item
                for item in authoring_messages
            )
            or not any(
                "openspec/specs/demo-spec/spec.md" in item
                for item in authoring_messages
            )
            or any("openspec/changes/demo/" in item for item in authoring_messages)
        ):
            report(
                "core-gates scenario authoring-artifact exemption did not stay "
                "exact: other changes and the specs tree must still fail and "
                "the selected change's own directory must never be cited."
            )
            report(
                (authoring_and_outside.stderr or authoring_and_outside.stdout).strip()
            )
            return 1
        (completion_repo / "openspec/changes/demo/design.md").unlink()
        (completion_repo / "openspec/changes/other/proposal.md").unlink()
        (completion_repo / "openspec/specs/demo-spec/spec.md").unlink()

        # Explicit --record replaces the selected task's Contract anchor
        # whatever it currently holds, so reauthorizing a task whose authority
        # changed needs no manual edit; a no-op re-record writes nothing, only
        # a missing anchor refuses, and without the flag the gate stays
        # read-only.
        record_repo = root / "record-anchor"
        record_repo.mkdir()
        record_tasks = record_repo / "openspec/changes/demo/tasks.md"

        def record_task(anchor: str, extra_touch: bool = False) -> str:
            touch = "    - src/feature.js\n"
            if extra_touch:
                touch += "    - src/extra.js\n"
            return (
                "# Tasks\n\n## Invalidates\n\n- None.\n\n"
                "- [ ] 1.1 Record behavior\n"
                "  - Owner: keel-agent\n"
                "  - Mode: implementation\n"
                "  - Covers:\n"
                "    - E1: public behavior\n"
                "  - Read:\n"
                "    - README.md\n"
                "  - Touch:\n"
                + touch
                + "    - openspec/changes/demo/tasks.md\n"
                "  - Verification Strategy: evidence-first\n"
                "  - Verification Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
                "  - Commands:\n"
                "    - M1: node test.js\n"
                "  - Acceptance:\n"
                "    - Public behavior passes.\n"
                "  - Autonomy boundary:\n"
                "    - Default: hard-stop\n"
                "    - Pre-authorized fallback: none\n"
                "  - Candidate Boundary:\n"
                "    - One complete candidate reaches M1.\n"
                "  - Stop Rules:\n"
                "    - Stop on final assertion failure.\n"
                "  - Evidence:\n"
                f"    - Contract: {anchor}\n"
                "    - M1: pending\n"
                "    - Review:\n"
                "      - Status: pending\n"
                "      - Acceptance check: pending\n"
                "      - Scope check: pending\n"
                "      - Findings: pending\n"
                "    - Blocker: none\n"
                "    - Reauthorizations: none\n"
                "  - Report:\n"
                "    - Summary\n"
            )

        write_text(record_tasks, record_task("pending"))
        before_default = record_tasks.read_bytes()
        default_start = run_keel(
            record_repo, "gate", "task-start",
            "--change", "demo", "--task", "1.1", "--no-guard", "--json",
        )
        if (
            default_start.returncode != 0
            or record_tasks.read_bytes() != before_default
        ):
            report(
                "core-gates scenario task-start without --record must stay "
                "read-only over the pending anchor."
            )
            report((default_start.stderr or default_start.stdout).strip())
            return 1

        recorded = run_keel(
            record_repo, "gate", "task-start",
            "--change", "demo", "--task", "1.1", "--no-guard", "--record",
            "--json",
        )
        if recorded.returncode != 0:
            report("core-gates scenario --record on a pending anchor failed.")
            report((recorded.stderr or recorded.stdout).strip())
            return 1
        recorded_result = json.loads(recorded.stdout)
        if recorded_result.get("record", {}).get("status") != "recorded":
            report(
                "core-gates scenario --record over a pending anchor must "
                "report the outcome as recorded."
            )
            return 1
        fingerprint = (
            recorded_result
            .get("contract", {})
            .get("fingerprint", {})
            .get("value", "")
        )
        before_lines = record_task("pending").splitlines()
        after_lines = record_tasks.read_text(encoding="utf-8").splitlines()
        changed_lines = [
            (old, new)
            for old, new in zip(before_lines, after_lines)
            if old != new
        ]
        if (
            len(before_lines) != len(after_lines)
            or len(changed_lines) != 1
            or changed_lines[0][0] != "    - Contract: pending"
            or changed_lines[0][1]
            != f"    - Contract: keel-task-capsule/v1 sha256:{fingerprint} (keel {PACKAGE_VERSION})"
        ):
            report(
                "core-gates scenario --record must replace exactly the "
                "pending Contract line with the fingerprint line."
            )
            return 1
        restart = run_keel(
            record_repo, "gate", "task-start",
            "--change", "demo", "--task", "1.1", "--no-guard", "--json",
        )
        restart_value = (
            json.loads(restart.stdout)
            .get("contract", {})
            .get("fingerprint", {})
            .get("value", "")
        )
        if restart.returncode != 0 or restart_value != fingerprint:
            report(
                "core-gates scenario recorded anchor drifted the fingerprint; "
                "recording must not change the compiled capsule."
            )
            return 1

        before_noop = record_tasks.read_bytes()
        noop = run_keel(
            record_repo, "gate", "task-start",
            "--change", "demo", "--task", "1.1", "--no-guard", "--record",
            "--json",
        )
        noop_result = json.loads(noop.stdout) if noop.stdout else {}
        if (
            noop.returncode != 0
            or noop_result.get("record", {}).get("status") != "unchanged"
            or noop_result.get("warnings")
            or record_tasks.read_bytes() != before_noop
        ):
            report(
                "core-gates scenario --record over an anchor that already "
                "carries the compiled fingerprint must report unchanged, "
                "warn about nothing, and write nothing."
            )
            report((noop.stderr or noop.stdout).strip())
            return 1

        # Reauthorization: the task authority changes, so the recorded anchor
        # is now stale and --record must replace it rather than refuse.
        anchor_line = f"keel-task-capsule/v1 sha256:{fingerprint}"
        write_text(record_tasks, record_task(anchor_line, extra_touch=True))
        before_rerecord = record_tasks.read_text(encoding="utf-8").splitlines()
        rerecord = run_keel(
            record_repo, "gate", "task-start",
            "--change", "demo", "--task", "1.1", "--no-guard", "--record",
            "--json",
        )
        rerecord_result = json.loads(rerecord.stdout) if rerecord.stdout else {}
        new_fingerprint = (
            rerecord_result.get("contract", {}).get("fingerprint", {}).get("value", "")
        )
        after_rerecord = record_tasks.read_text(encoding="utf-8").splitlines()
        rerecord_changed = [
            (old, new)
            for old, new in zip(before_rerecord, after_rerecord)
            if old != new
        ]
        if (
            rerecord.returncode != 0
            or rerecord_result.get("record", {}).get("status") != "rerecorded"
            or fingerprint not in rerecord_result.get("record", {}).get("previous", "")
            or not new_fingerprint
            or new_fingerprint == fingerprint
            or len(before_rerecord) != len(after_rerecord)
            or len(rerecord_changed) != 1
            or rerecord_changed[0][1]
            != f"    - Contract: keel-task-capsule/v1 sha256:{new_fingerprint} (keel {PACKAGE_VERSION})"
            or not any(
                fingerprint in warning
                for warning in rerecord_result.get("warnings", [])
            )
        ):
            report(
                "core-gates scenario --record over a stale recorded anchor "
                "must replace exactly that line with the new fingerprint, "
                "report the outcome as rerecorded with the replaced value, "
                "and warn naming the fingerprint it replaced."
            )
            report((rerecord.stderr or rerecord.stdout).strip())
            return 1

        write_text(record_tasks, record_task("pending").replace(
            "    - Contract: pending\n", ""
        ))
        # Issue #179: a missing anchor is a missing record slot, which
        # `--record` now derives instead of refusing; refusal is kept for an
        # authoring error (see `record-derives-skeleton`).
        missing_anchor = run_keel(
            record_repo, "gate", "task-start",
            "--change", "demo", "--task", "1.1", "--record", "--no-guard", "--json",
        )
        if missing_anchor.returncode != 0:
            report(
                "core-gates scenario --record with a missing anchor must add "
                "the anchor and pass."
            )
            report((missing_anchor.stderr or missing_anchor.stdout).strip())
            return 1
        if "    - Contract: keel-task-capsule/v1 sha256:" not in record_tasks.read_text(encoding="utf-8"):
            report("core-gates scenario --record did not write the missing Contract anchor.")
            return 1

        invalid_base = run_keel(
            completion_repo,
            "gate",
            "task-complete",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--base",
            "missing-ref",
            "--json",
        )
        if (
            invalid_base.returncode != 1
            or "gate input error" not in invalid_base.stderr
        ):
            report("core-gates scenario invalid base was not operational failure.")
            report((invalid_base.stderr or invalid_base.stdout).strip())
            return 1

        close_repo = root / "change-close"
        close_repo.mkdir()
        close_tasks = close_repo / "openspec/changes/demo/tasks.md"

        def close_task(checked: bool, review_status: str = "pass") -> str:
            mark = "x" if checked else " "
            return (
                "# Tasks\n\n## Invalidates\n\n- None.\n\n"
                "## Expectation Coverage\n\n"
                "- E1:\n"
                "  - Covered by: 1.1\n\n"
                "## 1. Work\n\n"
                f"- [{mark}] 1.1 Complete behavior\n"
                "  - Owner: keel-agent\n"
                "  - Mode: implementation\n"
                "  - Covers:\n"
                "    - E1: public behavior\n"
                "  - Read:\n"
                "    - README.md\n"
                "  - Touch:\n"
                "    - src/feature.js\n"
                "  - Verification Strategy: evidence-first\n"
                "  - Verification Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
                "  - Commands:\n"
                "    - M1: node test.js\n"
                "  - Acceptance:\n"
                "    - Public behavior passes.\n"
                "  - Autonomy boundary:\n"
                "    - Default: hard-stop\n"
                "    - Pre-authorized fallback: none\n"
                "  - Coupling: none\n"
                "  - Candidate Boundary:\n"
                "    - One candidate.\n"
                "  - Stop Rules:\n"
                "    - Stop on failure.\n"
                "  - Evidence:\n"
                "    - Contract: pending\n"
                "    - M1: passed\n"
                "    - Review:\n"
                f"      - Status: {review_status}\n"
                "      - Acceptance check: reviewed\n"
                "      - Scope check: reviewed\n"
                "      - Findings: none\n"
                "    - Blocker: none\n"
                "  - Stop if:\n"
                "    - Scope expands.\n"
                "  - Report:\n"
                "    - Summary\n"
            )

        # A change reaching its close has tasks that completed, and completion
        # requires a recorded anchor. The close compares it, so every checked
        # fixture below carries the fingerprint its own contract compiles to.
        def write_close(doc: str) -> bool:
            write_text(close_tasks, doc)
            if not record_contract_anchor(close_repo, "demo"):
                report("core-gates scenario could not record the close anchor.")
                return False
            return True

        write_text(close_tasks, close_task(False))
        write_text(
            close_repo / "openspec/changes/demo/proposal.md",
            "# Proposal\n",
        )
        write_text(
            close_repo / "openspec/changes/demo/design.md",
            "# Design\n",
        )
        write_text(
            close_repo / "openspec/changes/demo/specs/demo/spec.md",
            "## ADDED Requirements\n",
        )
        incomplete_close = run_keel(
            close_repo,
            "gate",
            "change-close",
            "--change",
            "demo",
            "--action",
            "sync",
            "--json",
        )
        if (
            incomplete_close.returncode != 3
            or json.loads(incomplete_close.stdout).get("status") != "fail"
        ):
            report("core-gates scenario change-close accepted unchecked tasks.")
            report((incomplete_close.stderr or incomplete_close.stdout).strip())
            return 1

        if not write_close(close_task(True, "pending")):
            return 1
        close_needs_review = run_keel(
            close_repo,
            "gate",
            "change-close",
            "--change",
            "demo",
            "--action",
            "sync",
            "--json",
        )
        if (
            close_needs_review.returncode != 4
            or json.loads(close_needs_review.stdout).get("status") != "needs-review"
        ):
            report("core-gates scenario change-close missed semantic Review.")
            report((close_needs_review.stderr or close_needs_review.stdout).strip())
            return 1

        if not write_close(
            close_task(True).replace("  - Covered by: 1.1", "  - pending")
        ):
            return 1
        missing_closure = run_keel(
            close_repo,
            "gate",
            "change-close",
            "--change",
            "demo",
            "--action",
            "sync",
            "--json",
        )
        if (
            missing_closure.returncode != 3
            or not any(
                "E1" in problem.get("message", "")
                for problem in json.loads(missing_closure.stdout).get("problems", [])
            )
        ):
            report("core-gates scenario change-close missed expectation closure.")
            report((missing_closure.stderr or missing_closure.stdout).strip())
            return 1

        if not write_close(close_task(True)):
            return 1
        before_close = snapshot_files(close_repo)
        sync_close = run_keel(
            close_repo,
            "gate",
            "change-close",
            "--change",
            "demo",
            "--action",
            "sync",
            "--json",
        )
        archive_close = run_keel(
            close_repo,
            "gate",
            "change-close",
            "--change",
            "demo",
            "--action",
            "archive",
            "--json",
        )
        after_close = snapshot_files(close_repo)
        if sync_close.returncode != 0 or archive_close.returncode != 0:
            report("core-gates scenario rejected close-ready change.")
            report(
                (
                    sync_close.stderr
                    or sync_close.stdout
                    or archive_close.stderr
                    or archive_close.stdout
                ).strip()
            )
            return 1
        if before_close != after_close:
            report("core-gates scenario change-close mutated project artifacts.")
            return 1

    report("core-gates scenario passed.")
    return 0


def validate_scope_rename_attribution_scenario() -> int:
    rename_task = (
        "# Tasks\n\n## Invalidates\n\n- None.\n\n"
        "- [ ] 1.1 Complete behavior\n"
        "  - Owner: keel-agent\n"
        "  - Mode: implementation\n"
        "  - Covers:\n"
        "    - E1: public behavior\n"
        "  - Read:\n"
        "    - README.md\n"
        "  - Touch:\n"
        "    - src/renamed-from.js\n"
        "    - src/renamed-to.js\n"
        "    - openspec/changes/demo/tasks.md\n"
        "  - Verification Strategy: evidence-first\n"
        "  - Verification Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "  - Commands:\n"
        "    - M1: node test.js\n"
        "  - Acceptance:\n"
        "    - Public behavior passes.\n"
        "  - Autonomy boundary:\n"
        "    - Default: hard-stop\n"
        "    - Pre-authorized fallback: none\n"
        "  - Coupling: none\n"
        "  - Candidate Boundary:\n"
        "    - One complete candidate reaches M1.\n"
        "  - Stop Rules:\n"
        "    - Stop on final assertion failure.\n"
        "  - Evidence:\n"
        "    - Contract: pending\n"
        "    - M1: passed\n"
        "    - Review:\n"
        "      - Status: pass\n"
        "      - Acceptance check: public behavior reviewed\n"
        "      - Scope check: Touch reviewed semantically\n"
        "      - Findings: none\n"
        "    - Blocker: none\n"
        "  - Stop if:\n"
        "    - Requires files outside Touch.\n"
        "  - Report:\n"
        "    - Summary\n"
    )
    with tempfile.TemporaryDirectory(prefix="keel-scope-rename-") as raw_tmp:
        repo = Path(raw_tmp)
        write_text(repo / "openspec/changes/demo/tasks.md", rename_task)
        write_text(repo / "src/renamed-from.js", "module.exports = 1;\n")
        write_text(repo / "README.md", "readme\n")
        for args in (
            ["init", "--quiet"],
            ["config", "user.email", "keel@example.invalid"],
            ["config", "user.name", "Keel Fixture"],
            ["add", "."],
            ["commit", "--quiet", "-m", "baseline"],
        ):
            result = subprocess.run(
                ["git", *args], cwd=repo, capture_output=True, text=True
            )
            if result.returncode != 0:
                report("scope-rename scenario git setup failed:")
                report((result.stderr or result.stdout).strip())
                return 1
        # A staged rename whose old and new paths are both in Touch must not be a
        # false outside-Touch failure (git reports it as one `old -> new` entry).
        moved = subprocess.run(
            ["git", "mv", "src/renamed-from.js", "src/renamed-to.js"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        if moved.returncode != 0:
            report("scope-rename scenario git mv failed:")
            report((moved.stderr or moved.stdout).strip())
            return 1
        record_contract_anchor(repo, "demo")
        completed = run_keel(
            repo,
            "gate",
            "task-complete",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--base",
            "HEAD",
            "--json",
        )
        payload = json.loads(completed.stdout or "{}")
        outside = " ".join(
            problem.get("message", "") for problem in payload.get("problems", [])
        )
        if (
            completed.returncode != 0
            or payload.get("status") != "pass"
            or "outside" in outside.lower()
        ):
            report(
                "scope-rename scenario reported a false outside-touch failure for a "
                "git mv rename whose old and new paths are both in Touch."
            )
            report((completed.stderr or completed.stdout).strip())
            return 1
    report("scope-rename scenario passed.")
    return 0


SUPPORTED_VERIFICATION_STRATEGIES = (
    "vertical-tdd",
    "regression-first",
    "characterization",
    "snapshot-characterization",
    "rendered-behavior",
    "evidence-first",
)


def validate_expectation_alignment_skill_scenario() -> int:
    """Pin document structure and spec-traceable contract anchors only.

    Every retained exact phrase cites the keel-expectation-alignment (or
    named sibling) requirement or scenario that names it; editorial wording
    no durable authority names must stay rewritable without validator edits.
    """
    skill_path = ROOT / "src/skills/align-expectations/SKILL.md"
    if not skill_path.is_file():
        report("expectation-alignment-skill canonical SKILL.md is missing.")
        return 1
    skill = skill_path.read_text(encoding="utf-8")

    # Structure: Agent Skills frontmatter with trigger/non-trigger guidance.
    frontmatter = re.match(r"---\n([\s\S]*?)\n---\n", skill)
    if (
        frontmatter is None
        or "name: align-expectations" not in frontmatter.group(1)
        or "description:" not in frontmatter.group(1)
    ):
        report("expectation-alignment-skill lacks portable trigger metadata.")
        return 1
    description = frontmatter.group(1)
    if "Use when" not in description or "not" not in description:
        report(
            "expectation-alignment-skill description lacks trigger/non-trigger "
            "guidance."
        )
        return 1

    # Contract anchors, each traceable to a governing spec:
    contract_anchors = {
        # keel-expectation-alignment / Scenario: Complete request uses the
        # quick path; Scenario: Material ambiguity uses the deep path.
        "quick path": "risk-scaled routing",
        "deep path": "risk-scaled routing",
        # keel-expectation-alignment: "asks one decision at a time" and
        # "provides a recommended answer".
        "one material decision at a time": "deep-path pacing",
        "recommended answer": "deep-path pacing",
        # keel-expectation-alignment / Scenario: Material ambiguity uses the
        # deep path (WHEN clause materiality list).
        "user-visible behavior": "materiality trigger",
        "external interface": "materiality trigger",
        "generated equivalence": "materiality trigger",
        "irreversible cost": "materiality trigger",
        "protocol/state/timing/reset": "materiality trigger",
        # keel-expectation-alignment / Requirement: Repository facts are
        # inspected before user questions ("distinguish F<n> facts").
        "F<n>": "fact discipline",
        # keel-expectation-alignment / Requirement: Implicit expectations
        # remain proposals until authorized (silence is not authority).
        "Silence does not": "candidate discipline",
        # keel-expectation-alignment / Requirement: Accepted alignment
        # writes back to existing OpenSpec owners (named owners, D/F/A/Q,
        # no separate ledger, HANDOFF exclusion).
        "proposal.md": "write-back ownership",
        "design.md": "write-back ownership",
        "tasks.md": "write-back ownership",
        "D/F/A/Q": "write-back ownership",
        "no separate alignment ledger": "write-back ownership",
        "HANDOFF": "write-back ownership",
    }
    for anchor, contract in contract_anchors.items():
        if anchor not in skill:
            report(
                f"expectation-alignment-skill lost the {contract} contract "
                f"anchor: {anchor}"
            )
            return 1

    # Structure and behavior: the skill routes to user-authored keel/lenses/,
    # the shipped lens templates exist, and each template stays scoped to its
    # own domain (cross-file keyword pairs).
    if "keel/lenses/" not in skill:
        report("expectation-alignment-skill does not route to keel/lenses/")
        return 1
    for domain in ("web", "hardware", "hardware-dsl"):
        template_path = ROOT / "assets/lenses" / f"{domain}.md"
        if not template_path.is_file():
            report(f"expectation-alignment-skill lens template is missing: {domain}.md")
            return 1
    web_reference = (ROOT / "assets/lenses/web.md").read_text(encoding="utf-8")
    hardware_reference = (ROOT / "assets/lenses/hardware.md").read_text(
        encoding="utf-8"
    )
    dsl_reference = (ROOT / "assets/lenses/hardware-dsl.md").read_text(
        encoding="utf-8"
    )
    for content, expected, unexpected in (
        (web_reference, "accessibility", "valid-ready"),
        (hardware_reference, "valid-ready", "browser"),
        (dsl_reference, "golden", "browser"),
    ):
        if expected not in content or unexpected in content:
            report(
                "expectation-alignment-skill lens templates are not scoped to "
                "their own domain."
            )
            return 1

    report("expectation-alignment-skill scenario passed.")
    return 0


def validate_authoring_alignment_overlay_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-authoring-overlay-") as raw_tmp:
        tmp = Path(raw_tmp)

        claude_repo = tmp / "claude"
        claude_repo.mkdir()
        claude_init = run_keel(claude_repo, "--init", "--target", "claude")
        if claude_init.returncode != 0:
            report("authoring-alignment-overlay Claude init failed:")
            report((claude_init.stderr or claude_init.stdout).strip())
            return 1
        # Skills only since #406: Keel generates no `.claude/commands/opsx/`.
        claude_surfaces = (
            claude_repo / ".claude/skills/openspec-propose/SKILL.md",
        )
        for surface in claude_surfaces:
            content = surface.read_text(encoding="utf-8")
            if (
                content.count(OPENSPEC_SURFACE_OVERLAY_START) != 1
                or "Keel Authoring Overlay" not in content
                or "align-expectations" not in content
            ):
                report(
                    "authoring-alignment-overlay Claude propose surface lacks "
                    f"exactly one alignment overlay: {surface}"
                )
                return 1

        codex_repo = tmp / "codex"
        codex_repo.mkdir()
        codex_home = tmp / "codex-home"
        codex_env = os.environ.copy()
        codex_env["CODEX_HOME"] = str(codex_home)
        codex_init = run_keel(codex_repo, "--init", "--target", "codex", env=codex_env)
        if codex_init.returncode != 0:
            report("authoring-alignment-overlay Codex init failed:")
            report((codex_init.stderr or codex_init.stdout).strip())
            return 1
        codex_surfaces = (
            codex_repo / ".agents/skills/openspec-propose/SKILL.md",
        )
        for surface in codex_surfaces:
            content = surface.read_text(encoding="utf-8")
            if (
                content.count(OPENSPEC_SURFACE_OVERLAY_START) != 1
                or "Keel Authoring Overlay" not in content
                or "align-expectations" not in content
            ):
                report(
                    "authoring-alignment-overlay Codex propose surface lacks "
                    f"exactly one alignment overlay: {surface}"
                )
                return 1

        refreshed = run_keel(codex_repo, "--install", "--target", "codex", env=codex_env)
        if refreshed.returncode != 0:
            report("authoring-alignment-overlay Codex refresh failed.")
            return 1
        for surface in codex_surfaces:
            if surface.read_text(encoding="utf-8").count(
                OPENSPEC_SURFACE_OVERLAY_START
            ) != 1:
                report(
                    "authoring-alignment-overlay refresh duplicated the overlay: "
                    f"{surface}"
                )
                return 1

        apply_skill = (
            codex_repo / ".agents/skills/openspec-apply-change/SKILL.md"
        ).read_text(encoding="utf-8")
        if (
            "rerun `align-expectations`" not in apply_skill
            or "repository fact" not in apply_skill
        ):
            report(
                "authoring-alignment-overlay apply overlay does not return missing "
                "material authority to alignment."
            )
            return 1

        opencode_repo = tmp / "opencode"
        opencode_repo.mkdir()
        opencode_init = run_keel(opencode_repo, "--init", "--target", "opencode")
        if opencode_init.returncode != 0:
            report("authoring-alignment-overlay OpenCode init failed:")
            report((opencode_init.stderr or opencode_init.stdout).strip())
            return 1
        for surface in (
            opencode_repo / ".opencode/skills/openspec-propose/SKILL.md",
            opencode_repo / ".opencode/commands/opsx-propose.md",
        ):
            if surface.is_file() and "Keel Authoring Overlay" in surface.read_text(
                encoding="utf-8"
            ):
                report(
                    "authoring-alignment-overlay created an OpenCode authoring "
                    f"overlay: {surface}"
                )
                return 1

    report("authoring-alignment-overlay scenario passed.")
    return 0


def validate_expectation_alignment_real_tasks_scenario() -> int:
    evidence_path = (
        ROOT / "keel/archive/skill-evidence/keel-align-expectations-v1.md"
    )
    if not evidence_path.is_file():
        report("expectation-alignment-real-tasks evidence document is missing.")
        return 1
    evidence = evidence_path.read_text(encoding="utf-8")

    # Evaluation integrity: raw prompts, isolated helpers, no intended answers.
    for phrase in (
        "raw prompt",
        "read-only",
        "did not receive intended answers",
    ):
        if phrase not in evidence:
            report(
                "expectation-alignment-real-tasks evidence lacks evaluation "
                f"integrity statement: {phrase}"
            )
            return 1

    # Three positive domains plus at least two negative controls.
    positive_headings = re.findall(r"(?m)^## Positive case P\d+", evidence)
    negative_headings = re.findall(r"(?m)^## Negative control N\d+", evidence)
    if len(positive_headings) < 3 or len(negative_headings) < 2:
        report(
            "expectation-alignment-real-tasks evidence needs 3 positive cases "
            f"and 2 controls; found {len(positive_headings)} and "
            f"{len(negative_headings)}."
        )
        return 1
    for domain in ("generic software", "web/API", "hardware/generated"):
        if domain not in evidence:
            report(
                f"expectation-alignment-real-tasks evidence misses domain: {domain}"
            )
            return 1

    # Each positive case records the full rubric.
    positive_sections = re.split(r"(?m)^## Positive case ", evidence)[1:]
    for section in positive_sections:
        for field_name in (
            "Raw prompt:",
            "Triggered:",
            "Path:",
            "Question materiality:",
            "Facts vs product choices:",
            "Observable acceptance:",
            "Negative behavior:",
            "Durable write-back:",
            "Verdict:",
        ):
            if field_name not in section:
                report(
                    "expectation-alignment-real-tasks positive case misses "
                    f"rubric field: {field_name}"
                )
                return 1

    # Each control proves no interview and no artifact mutation happened.
    negative_sections = re.split(r"(?m)^## Negative control ", evidence)[1:]
    for section in negative_sections:
        for field_name in (
            "Raw prompt:",
            "Triggered:",
            "Interview avoided:",
            "Artifacts untouched:",
            "Verdict:",
        ):
            if field_name not in section:
                report(
                    "expectation-alignment-real-tasks control misses rubric "
                    f"field: {field_name}"
                )
                return 1

    # Unresolved failures must be owned, not hidden.
    if "Unresolved findings:" not in evidence:
        report("expectation-alignment-real-tasks evidence lacks findings section.")
        return 1

    report("expectation-alignment-real-tasks scenario passed.")
    return 0


def validate_compact_task_authoring_scenario() -> int:
    local_root = ROOT / "openspec" / "schemas" / OPENSPEC_SCHEMA_NAME

    which = run_openspec(ROOT, "schema", "which", OPENSPEC_SCHEMA_NAME, "--json")
    # Two distinct facts, kept apart. A CLI that was never found says nothing
    # about the schema, and reporting the schema as unresolvable sends the
    # reader to a subject with nothing wrong with it (issue #105).
    if which is None:
        report(
            "compact-task-authoring skipped: the openspec CLI could not be "
            "found. Searched " + ", then ".join(OPENSPEC_SEARCH_ORDER)
            + ". Run `npm install` to provide the declared dependency."
        )
        return 3
    if which.returncode != 0:
        report(
            "compact-task-authoring could not resolve the schema through "
            "OpenSpec. The CLI ran and refused:"
        )
        report((which.stderr or which.stdout).strip())
        return 1
    which_payload = json.loads(which.stdout[which.stdout.index("{"):])
    resolved = Path(which_payload.get("path", ""))
    if (
        which_payload.get("source") != "project"
        or resolved.resolve() != local_root.resolve()
    ):
        report("compact-task-authoring did not resolve the project-local schema.")
        report(which.stdout.strip())
        return 1

    template = (resolved / "templates" / "tasks.md").read_text(encoding="utf-8")
    for marker in (
        "keel-task-capsule/v1",
        "- Covers:",
        "- Touch:",
        "- Verify:",
        "- Strategy: <strategy>",
        "- M1:",
        "- Evidence:",
        "- Contract: pending",
        "- Review:",
        "- Blocker: none",
        "- Mode: diagnose-only",
    ):
        if marker not in template:
            report(
                "compact-task-authoring template resolved by OpenSpec is missing "
                f"compact language: {marker}"
            )
            return 1
    stripped_template = re.sub(r"<!--[\s\S]*?-->", "", template)
    for forbidden in (
        "Owner: keel-agent",
        "Mode: implementation",
        "- Read:",
        "- Commands:",
        "- Acceptance:",
        "- Autonomy boundary:",
        "- Coupling:",
        "- Candidate Boundary:",
        "- Stop Rules:",
        "- Stop if:",
        "- Report:",
    ):
        if forbidden in stripped_template:
            report(
                "compact-task-authoring template repeats an invariant default: "
                f"{forbidden}"
            )
            return 1

    # The projection loop that stood here compared against `src/assets` and
    # `dist`, both retired, so it iterated nothing. `invalidation-authoring-surface`
    # asserts the two copies that do exist are byte-identical.

    with tempfile.TemporaryDirectory(prefix="keel-compact-") as raw_tmp:
        repo = Path(raw_tmp) / "fixture"
        repo.mkdir()
        tasks_path = repo / "openspec/changes/demo/tasks.md"
        fingerprints = {}
        for label, fixture in (
            ("compact", task_capsule_compact_fixture()),
            ("expanded", task_capsule_expanded_fixture()),
        ):
            write_text(tasks_path, fixture)
            started = run_keel(
                repo,
                "gate",
                "task-start",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
            )
            payload = json.loads(started.stdout)
            fingerprints[label] = (
                payload.get("contract", {}).get("fingerprint", {}).get("value")
            )
            if started.returncode != 0 or payload.get("status") != "pass":
                report(f"compact-task-authoring {label} fixture did not compile.")
                report((started.stderr or started.stdout).strip())
                return 1
        if (
            not fingerprints["compact"]
            or fingerprints["compact"] != fingerprints["expanded"]
        ):
            report(
                "compact-task-authoring compact and expanded fixtures did not "
                "compile to the same fingerprint."
            )
            report(str(fingerprints))
            return 1

        write_text(
            tasks_path,
            task_capsule_compact_fixture().replace(
                "  - Evidence:\n",
                "  - Verification Strategy: vertical-tdd\n  - Evidence:\n",
            ),
        )
        conflicted = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        conflicted_payload = json.loads(conflicted.stdout)
        if (
            conflicted.returncode != 3
            or conflicted_payload.get("status") != "fail"
            or not any(
                item.get("code") == "legacy-field-conflict"
                for item in conflicted_payload.get("problems", [])
            )
        ):
            report(
                "compact-task-authoring contradictory legacy fields did not "
                "receive a migration diagnostic."
            )
            report((conflicted.stderr or conflicted.stdout).strip())
            return 1

    report("compact-task-authoring scenario passed.")
    return 0


def strategy_task_fixture(
    strategy: str | None,
    *,
    evidence: tuple[str, ...] = ("M1: pending",),
) -> str:
    fixture = task_contract_fixture(evidence=evidence)
    if strategy is None:
        return fixture
    return fixture.replace(
        "  - Commands:\n",
        f"  - Verification Strategy: {strategy}\n  - Commands:\n",
    )


def validate_task_verification_strategies_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-strategy-") as raw_tmp:
        root = Path(raw_tmp)
        repo = root / "strategies"
        repo.mkdir()
        tasks_path = repo / "openspec/changes/demo/tasks.md"

        write_text(tasks_path, strategy_task_fixture("build-only"))
        rejected = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--json",
        )
        rejected_payload = json.loads(rejected.stdout)
        if (
            rejected.returncode != 3
            or rejected_payload.get("status") != "fail"
            or not any(
                "strategy" in item.get("message", "").lower()
                and "build-only" in item.get("message", "")
                and "vertical-tdd" in item.get("message", "")
                for item in rejected_payload.get("problems", [])
            )
        ):
            report(
                "task-verification-strategies accepted an unsupported strategy at task-start."
            )
            report((rejected.stderr or rejected.stdout).strip())
            return 1

        for strategy in SUPPORTED_VERIFICATION_STRATEGIES:
            write_text(tasks_path, strategy_task_fixture(strategy))
            accepted = run_keel(
                repo,
                "gate",
                "task-start",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
            )
            accepted_payload = json.loads(accepted.stdout)
            normalized = (
                accepted_payload.get("contract", {})
                .get("capsule", {})
                .get("verification", {})
                .get("strategy")
            )
            if (
                accepted.returncode != 0
                or accepted_payload.get("status") != "pass"
                or normalized != strategy
            ):
                report(
                    f"task-verification-strategies did not normalize {strategy} "
                    "through task-start."
                )
                report((accepted.stderr or accepted.stdout).strip())
                return 1

        def completion_fixture(strategy: str | None, evidence: tuple[str, ...]) -> str:
            return (
                strategy_task_fixture(strategy, evidence=evidence)
                .replace("      - Status: pending\n", "      - Status: pass\n")
                .replace(
                    "      - Acceptance check: pending\n",
                    "      - Acceptance check: behavior proven through the public CLI.\n",
                )
                .replace(
                    "      - Scope check: pending\n",
                    "      - Scope check: writes stayed inside Touch.\n",
                )
                .replace("      - Findings: pending\n", "      - Findings: none\n")
            )

        def run_completion(fixture: str) -> subprocess.CompletedProcess[str]:
            write_text(tasks_path, fixture)
            record_contract_anchor(repo, "demo")
            return run_keel(
                repo,
                "gate",
                "task-complete",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
            )

        for strategy in ("vertical-tdd", "regression-first"):
            green_only = run_completion(
                completion_fixture(strategy, ("M1: behavior check exercised.",))
            )
            green_only_payload = json.loads(green_only.stdout)
            if (
                green_only.returncode != 3
                or green_only_payload.get("status") != "fail"
                or not any(
                    "M1.red" in item.get("message", "")
                    for item in green_only_payload.get("problems", [])
                )
            ):
                report(
                    f"task-verification-strategies let {strategy} complete without "
                    "red evidence."
                )
                report((green_only.stderr or green_only.stdout).strip())
                return 1

            pending_red = run_completion(
                completion_fixture(
                    strategy,
                    (
                        "M1: behavior check exercised.",
                        "M1.red: pending",
                        "M1.green: check passed after implementation.",
                    ),
                )
            )
            pending_red_payload = json.loads(pending_red.stdout)
            if (
                pending_red.returncode != 3
                or pending_red_payload.get("status") != "fail"
                or not any(
                    "M1.red" in item.get("message", "")
                    for item in pending_red_payload.get("problems", [])
                )
            ):
                report(
                    f"task-verification-strategies let {strategy} complete with "
                    "pending red evidence."
                )
                report((pending_red.stderr or pending_red.stdout).strip())
                return 1

            red_green = run_completion(
                completion_fixture(
                    strategy,
                    (
                        "M1: behavior check exercised red then green.",
                        "M1.red: check failed before implementation with the expected reason.",
                        "M1.green: same check passed after the minimal implementation.",
                    ),
                )
            )
            red_green_payload = json.loads(red_green.stdout)
            if (
                red_green.returncode != 0
                or red_green_payload.get("status") != "pass"
            ):
                report(
                    f"task-verification-strategies rejected complete {strategy} "
                    "red-green evidence."
                )
                report((red_green.stderr or red_green.stdout).strip())
                return 1

        evidence_first = run_completion(
            completion_fixture(None, ("M1: observable artifact verified.",))
        )
        evidence_first_payload = json.loads(evidence_first.stdout)
        if (
            evidence_first.returncode != 0
            or evidence_first_payload.get("status") != "pass"
        ):
            report(
                "task-verification-strategies required red-green records from "
                "an evidence-first task."
            )
            report((evidence_first.stderr or evidence_first.stdout).strip())
            return 1

    report("task-verification-strategies scenario passed.")
    return 0


def validate_verify_layer_tag_scenario() -> int:
    fixture = (
        "# Tasks\n\n## Invalidates\n\n- None.\n\n"
        "- [ ] 1.1 Exercise the verification-layer tag\n"
        "  - Covers:\n"
        "    - E1: Public behavior passes.\n"
        "  - Read:\n"
        "    - README.md\n"
        "  - Touch:\n"
        "    - src/feature.js\n"
        "  - Verify:\n"
        "    - Strategy: evidence-first\n"
        "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "    - M1 (fast): node fast.js\n"
        "    - M2: node full.js\n"
        "  - Autonomy boundary:\n"
        "    - Default: hard-stop\n"
        "    - Pre-authorized fallback: none\n"
        "  - Stop Rules:\n"
        "    - Stop on failure.\n"
        "  - Evidence:\n"
        "    - M1: pending\n"
        "    - M2: pending\n"
        "  - Stop if:\n"
        "    - Requires files outside Touch.\n"
    )
    with tempfile.TemporaryDirectory(prefix="keel-verify-layer-") as raw_tmp:
        repo = Path(raw_tmp)
        write_text(repo / "openspec/changes/demo/tasks.md", fixture)
        started = run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
        )
        if started.returncode != 0:
            report("verify-layer-tag: task-start rejected the tagged fixture.")
            report((started.stderr or started.stdout).strip())
            return 1
        capsule = json.loads(started.stdout).get("contract", {}).get("capsule", {})
        commands = capsule.get("verification", {}).get("commands", [])
        by_label = {c.get("label"): c for c in commands}
        if by_label.get("M1", {}).get("layer") != "fast":
            report("verify-layer-tag: the (fast)-tagged check did not compile with layer fast.")
            report(json.dumps(commands))
            return 1
        if "layer" in by_label.get("M2", {}):
            report(
                "verify-layer-tag: an untagged check emitted a layer field; full is "
                "the implicit default and must stay off the capsule."
            )
            report(json.dumps(commands))
            return 1
        if (
            by_label.get("M1", {}).get("check") != "node fast.js"
            or by_label.get("M2", {}).get("check") != "node full.js"
        ):
            report("verify-layer-tag: the layer tag altered the check text.")
            report(json.dumps(commands))
            return 1

    report("verify-layer-tag scenario passed.")
    return 0


def sibling_scope_tasks(sibling_checked: bool, sibling_touch: str) -> str:
    """Two tasks: 1.1 owns `shared.js`, 1.2 is the one being completed."""

    def task(task_id: str, title: str, checked: bool, touch: str) -> str:
        mark = "x" if checked else " "
        return (
            f"- [{mark}] {task_id} {title}\n"
            "  - Covers:\n"
            "    - E1: public behavior\n"
            "  - Touch:\n"
            + "".join(f"    - {entry}\n" for entry in touch.split(","))
            + "  - Verify:\n"
            "    - Strategy: evidence-first\n"
            "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
            "    - M1: node test.js\n"
            "  - Evidence:\n"
            "    - M1: verified\n"
            "    - Review:\n"
            "      - Status: pass\n"
            "      - Acceptance check: reviewed\n"
            "      - Scope check: reviewed\n"
            "      - Findings: none\n"
            "    - Blocker: none\n"
        )

    return (
        "# Tasks\n\n## Invalidates\n\n- None.\n\n"
        "## 1. Work\n\n"
        + task("1.1", "Own the shared file", sibling_checked, sibling_touch)
        + "\n"
        + task("1.2", "Own its own file", False, "src/mine.js")
        + "\n## Expectation Coverage\n\n- None.\n"
    )


def validate_completed_sibling_attribution_scenario() -> int:
    """Issue #13 item 2: a finished task's uncommitted work blamed the next one.

    `--base HEAD` cannot tell who wrote a path, so a sibling that already passed
    its own completion gate had its files attributed to whoever ran next. The
    workaround — commit per task — was correct but implicit, and the diagnostic
    named a file the author never touched.
    """
    label = "completed-sibling-attribution"

    def complete(sibling_checked: bool, sibling_touch: str = "src/shared.js"):
        with tempfile.TemporaryDirectory(prefix="keel-sibling-scope-") as raw:
            repo = Path(raw)
            for name in ("src/shared.js", "src/mine.js", "src/stray.js"):
                write_text(repo / name, "// base\n")
            write_text(
                repo / "openspec/changes/demo/tasks.md",
                sibling_scope_tasks(sibling_checked, sibling_touch),
            )
            for args in (
                ["init", "--quiet"],
                ["-c", "user.email=t@e", "-c", "user.name=t", "add", "-A"],
                [
                    "-c", "user.email=t@e", "-c", "user.name=t",
                    "commit", "--quiet", "-m", "base",
                ],
            ):
                done = subprocess.run(
                    ["git", *args], cwd=repo, capture_output=True, text=True
                )
                if done.returncode != 0:
                    report(f"{label}: git {args[0]} failed: {done.stderr}")
                    return None
            # The sibling's work and an undeclared stray, both uncommitted.
            write_text(repo / "src/shared.js", "// sibling's uncommitted work\n")
            write_text(repo / "src/stray.js", "// nobody declared this\n")
            result = run_keel(
                repo, "gate", "task-complete",
                "--change", "demo", "--task", "1.2", "--base", "HEAD", "--json",
            )
            return json.loads(result.stdout) if result.stdout else {}

    owned = complete(sibling_checked=True)
    if owned is None:
        return 1
    outside = [
        item.get("message", "")
        for item in owned.get("problems", [])
        if item.get("code") == "outside-touch"
    ]
    if any("src/shared.js" in message for message in outside):
        report(
            f"{label}: a completed sibling's declared file was still attributed "
            f"to the selected task: {outside}"
        )
        return 1
    if not any("src/stray.js" in message for message in outside):
        report(
            f"{label}: a path no task declares must still fail: {outside}"
        )
        return 1
    warnings = " ".join(owned.get("warnings", []))
    if "src/shared.js" not in warnings or "1.1" not in warnings:
        report(
            f"{label}: the exclusion must be reported, naming the path and the "
            f"completed task that declares it; got {owned.get('warnings')}"
        )
        return 1

    unchecked = complete(sibling_checked=False)
    if unchecked is None:
        return 1
    unchecked_outside = [
        item.get("message", "")
        for item in unchecked.get("problems", [])
        if item.get("code") == "outside-touch"
    ]
    if not any("src/shared.js" in message for message in unchecked_outside):
        report(
            f"{label}: an unchecked sibling's Touch must grant nothing: "
            f"{unchecked_outside}"
        )
        return 1

    no_touch = complete(sibling_checked=True, sibling_touch="none")
    if no_touch is None:
        return 1
    none_outside = [
        item.get("message", "")
        for item in no_touch.get("problems", [])
        if item.get("code") == "outside-touch"
    ]
    if not any("src/shared.js" in message for message in none_outside):
        report(
            f"{label}: a sibling whose Touch is none must contribute no claim: "
            f"{none_outside}"
        )
        return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_declared_paths_are_read_whole_scenario() -> int:
    """Issue #60: a durable owner under a Chinese directory was refused.

    `notes/note-006-转岗最难的不是流程/note.md` exists and `git ls-files` finds
    it, and `change-close` reported that `notes/note-006-` does not exist — a
    path nobody wrote. The extractor was `[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)+`,
    which answers "where does the path end" by assuming what a path is made of.

    Two more shapes fell out while reproducing it: a path whose *first* segment
    is not ASCII does not match at all, and a path containing a space truncates
    at the space. The last is why the backtick form matters — `Touch` already
    accepts it, so one authorship was spelled two ways depending on which
    reader would read it.

    Same class as #40, which fixed it in `gitPaths` for the worktree side. That
    fix did not generalize because it repaired one reader rather than how the
    repository extracts paths.
    """
    label = "declared-paths-are-read-whole"
    cjk_owner = "notes/note-006-转岗最难的不是流程/note.md"
    cjk_first = "文档/风格.md"
    spaced = "docs/has space.md"

    def git(repo, *args):
        return subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True
        )

    def tasks_doc(findings: str, coverage: str) -> str:
        return (
            "# Tasks\n\n"
            "- [x] 1.1 Exercise the declared-path readers\n"
            "  - Covers:\n    - E1: Public behavior passes.\n"
            "  - Touch:\n    - src/declared.js\n"
            "  - Verify:\n    - Strategy: evidence-first\n    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
            "    - M1: node test.js asserts the recorded feed status\n"
            "  - Evidence:\n"
            "    - Contract: keel-task-capsule/v1 sha256:"
            + ("0" * 64) + "\n"
            "    - M1: the suite passed\n"
            "    - Review:\n      - Status: pass\n"
            "      - Acceptance check: behavior asserted at the interface\n"
            "      - Scope check: only Touch files changed\n"
            f"      - Findings: {findings}\n"
            "    - Blocker: none\n\n"
            "## Invalidates\n\n- None.\n\n"
            "## Expectation Coverage\n\n"
            f"- E1: the behavior {coverage}\n"
        )

    with tempfile.TemporaryDirectory(prefix="keel-declared-paths-") as raw:
        repo = (Path(raw) / "repo").resolve()
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.email", "t@example.com")
        git(repo, "config", "user.name", "keel-test")
        for item in (cjk_owner, cjk_first, spaced):
            write_text(repo / item, "# owner\n")
        write_text(repo / "src/declared.js", "// product\n")
        tasks_path = repo / "openspec/changes/demo/tasks.md"

        def close(findings: str, coverage: str) -> dict:
            write_text(tasks_path, tasks_doc(findings, coverage))
            return json.loads(
                run_keel(
                    repo, "gate", "change-close", "--change", "demo",
                    "--action", "sync", "--json",
                ).stdout
            )

        def problems(payload: dict) -> list[str]:
            return [p.get("message", "") for p in payload.get("problems", [])]

        # M1 — the reported shape, on both readers that take a declared path.
        for where, findings, coverage in (
            ("Findings", f"one open. Durable owner: {cjk_owner}", "Covered by: 1.1"),
            ("Expectation Coverage", "none", f"Durable owner: {cjk_owner}"),
        ):
            payload = close(findings, coverage)
            truncated = [m for m in problems(payload) if "note-006-" in m]
            if truncated:
                report(
                    f"{label} M1 a {where} durable owner naming an existing "
                    "file under a non-ASCII directory was refused, and the "
                    "refusal names a path nobody wrote."
                )
                for message in truncated:
                    report(f"  {message}")
                return 1

        # M1 — a path whose first segment is not ASCII matched nothing at all,
        # which is a different failure from truncation and needs its own case.
        payload = close("none", f"Durable owner: {cjk_first}")
        rejected = [m for m in problems(payload) if "E1" in m and "owner" in m.lower()]
        if rejected:
            report(
                f"{label} M1 a durable owner whose first segment is not ASCII "
                "was not recognized as a path at all."
            )
            for message in rejected:
                report(f"  {message}")
            return 1

        # M1 — whitespace arrives in backticks, the form Touch already accepts.
        payload = close("none", f"Durable owner: `{spaced}`")
        rejected = [m for m in problems(payload) if "E1" in m and "owner" in m.lower()]
        if rejected:
            report(
                f"{label} M1 a backtick-wrapped path containing a space was "
                "not read whole, so Touch and Durable owner still disagree "
                "about how one path is written."
            )
            for message in rejected:
                report(f"  {message}")
            return 1

        # M1 — a path ending a sentence, in both punctuation families.
        for mark in ("。", ","):
            payload = close("none", f"Durable owner: {cjk_owner}{mark} 说明文字")
            rejected = [
                m for m in problems(payload) if "E1" in m and "owner" in m.lower()
            ]
            if rejected:
                report(
                    f"{label} M1 a path followed by {mark!r} was extended by "
                    "its punctuation, so the gate looked for a file that "
                    "cannot exist."
                )
                for message in rejected:
                    report(f"  {message}")
                return 1

        # M1 — the check itself must survive the widening. A path that does not
        # exist is still refused, and the refusal names the whole path.
        missing = "notes/不存在的目录/note.md"
        payload = close("none", f"Durable owner: {missing}")
        named = [m for m in problems(payload) if missing in m]
        if not named:
            report(
                f"{label} M1 a durable owner naming a file that does not exist "
                "was accepted, or was refused without naming the whole path. "
                "Widening the extractor must not weaken the existence check."
            )
            for message in problems(payload):
                report(f"  {message}")
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_decimal_runs_are_not_hash_shaped_scenario() -> int:
    """Issue #58: an eleven-digit fake phone number failed `keel state`.

    The criterion was a context word beside `[0-9a-f]{7,40}`, and eleven
    decimal digits are eleven characters of that class. So was a timestamp,
    an order number, a port, and any numeric fixture that happened to sit on a
    line with the word `commit` or `提交` — which in evidence prose is most of
    them.

    The cost is not the refusal, it is what the refusal asks for. Nothing is
    wrong with the line, so the only way past it is to write the evidence
    differently; the reporter changed the number to `138****0000`. Evidence
    reworded to satisfy a pattern is weaker than the evidence that was true,
    and a check that fails on correct work is one people learn to route
    around.

    Same class as #60, repaired one release earlier in the other direction:
    there the character class was too narrow. The rule was right both times.
    """
    label = "decimal-runs-are-not-hash-shaped"

    def tasks_doc(body: str) -> str:
        return (
            "# Tasks\n\n## Invalidates\n\n- None.\n\n"
            "## Tasks\n\n"
            "- [x] A1 implementation\n"
            f"{body}\n"
            "## Workflow Notes\n\n- None.\n"
        )

    # F2, measured at 5.18.0: each of these is refused by the pre-change
    # criterion, and none of them records anything git owns.
    accepted = (
        "- M1: pass —— 提交表单时手机号 13800138000 通过校验。\n",
        "- M2: pass —— 时间戳 1700000000 与 commit 记录对齐。\n",
        "- M3: pass —— 提交订单号 20260802123 落库。\n",
    )
    # The other half of the requirement: what the rule exists to refuse.
    refused_token = "- M4: pass —— 合入前的 commit a1b2c3d4e5f6 已验证。\n"
    # Wording alone, carrying no hash-shaped token at all. The line names 分支
    # because 提交 on its own is an ordinary verb and no longer refused (#103);
    # what this fixture is for is the absence of a token, not the absence of
    # context.
    refused_wording = "- M5: 该分支**未提交**，等待评审。\n"

    def state_of(check) -> str:
        if "keel state: ok" in check.stdout:
            return "ok"
        if "keel state: failed" in check.stdout:
            return "failed"
        return "unreported"

    with tempfile.TemporaryDirectory(prefix="keel-decimal-runs-") as raw:
        repo = (Path(raw) / "repo").resolve()
        repo.mkdir()
        install = run_keel(repo, "--install")
        if install.returncode != 0:
            report(f"{label}: keel --install failed while building the fixture.")
            report((install.stderr or install.stdout).strip())
            return 1

        tasks_path = repo / "openspec/changes/numbers-in-evidence/tasks.md"

        def check(body: str):
            write_text(tasks_path, tasks_doc(body))
            return run_keel(repo, "--check")

        # `keel state` reporting nothing at all is a different failure from it
        # reporting a refusal, and one condition covering both would send the
        # reader to a line that has no problem in it.
        def unreported(result, where: str) -> bool:
            if state_of(result) != "unreported":
                return False
            report(
                f"{label}: keel --check reported no state at all while {where}. "
                "This is not a verdict about the fixture — the check did not "
                "reach the point of having one."
            )
            report((result.stderr or result.stdout).strip()[:600])
            return True

        # M1 — the reported shape and its two siblings, each on its own line so
        # a failure names which one.
        for line in accepted:
            result = check(line)
            if unreported(result, "reading one ordinary number"):
                return 1
            if state_of(result) != "ok":
                report(
                    f"{label}: an ordinary number in evidence prose was refused "
                    "as a recorded identifier. Nothing on this line records "
                    "anything git owns, so the only way past the refusal is to "
                    "reword evidence that was true."
                )
                report(f"  line: {line.strip()}")
                for state_error in [
                    out for out in result.stdout.splitlines()
                    if out.startswith("state-error")
                ]:
                    report(f"  {state_error}")
                return 1

        # All three together, because the check reports per line and a
        # per-line pass says nothing about a file holding several.
        together = check("".join(accepted))
        if unreported(together, "reading three ordinary numbers in one file"):
            return 1
        if state_of(together) != "ok":
            report(f"{label}: three ordinary numbers in one file were refused.")
            report(together.stdout.strip()[:600])
            return 1

        # M1 negative — the narrowing must not have narrowed the rule.
        with_token = check("".join(accepted) + refused_token)
        if unreported(with_token, "reading a hexadecimal identifier"):
            return 1
        if state_of(with_token) != "failed":
            report(
                f"{label}: a hexadecimal identifier of that length beside a "
                "context word was accepted. Narrowing what counts as an "
                "identifier must not stop the check refusing one."
            )
            report(with_token.stdout.strip()[:600])
            return 1
        if with_token.returncode == 0:
            report(f"{label}: the refusal did not fail the check's exit status.")
            return 1
        named = [
            out for out in with_token.stdout.splitlines()
            if out.startswith("state-error") and "tasks.md:" in out
        ]
        if not named:
            report(
                f"{label}: the refusal named no line. An author cannot act on "
                "a refusal that does not say where."
            )
            report(with_token.stdout.strip()[:600])
            return 1

        # And the wording patterns, which never depended on a digit run.
        wording = check(refused_wording)
        if unreported(wording, "reading recorded work state written in words"):
            return 1
        if state_of(wording) != "failed":
            report(
                f"{label}: recorded work state written in words was accepted. "
                "That rule reads the wording and is untouched by any change to "
                "what counts as an identifier."
            )
            report(wording.stdout.strip()[:600])
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def _tasks_semantics_probe(raw: str):
    """Install into `raw` and return `check(body) -> (state, errors)`.

    Both scenarios below ask the same question of `keel --check` — which lines
    of one active `tasks.md` it refuses — so they share the fixture rather than
    each growing their own copy of it. The caller owns the temporary directory,
    so a failed install is reported by the caller and cleaned up by its `with`.
    """
    repo = (Path(raw) / "repo").resolve()
    repo.mkdir()
    install = run_keel(repo, "--install")
    if install.returncode != 0:
        return None, (install.stderr or install.stdout).strip()

    tasks_path = repo / "openspec/changes/reading-lines/tasks.md"

    def check(body: str):
        write_text(
            tasks_path,
            "# Tasks\n\n## Invalidates\n\n- None.\n\n"
            "## Tasks\n\n"
            f"{body}\n"
            "## Workflow Notes\n\n- None.\n",
        )
        result = run_keel(repo, "--check")
        if "keel state: ok" in result.stdout:
            state = "ok"
        elif "keel state: failed" in result.stdout:
            state = "failed"
        else:
            state = "unreported"
        errors = [
            out for out in result.stdout.splitlines() if out.startswith("state-error")
        ]
        return state, errors

    return check, None


def validate_a_context_word_is_a_word_scenario() -> int:
    """Issue #65 §1: `remaining` supplied the word `main`.

    The context words that turn a hash-shaped token into a recorded commit
    identifier were matched anywhere on the line, so `remaining`, `heading`,
    `domain`, and `maintains` each supplied one. Four lines in this
    repository's own history are refused this way, and every hex token on
    them is a `sha256:` contract anchor rather than a commit identifier.

    The boundary form is the owner's decision on #65 and keeps the inflections
    an author actually writes. Dropping `committed` and `hashes` would have
    been the quieter change and would have cost four real refusals.
    """
    label = "a-context-word-is-a-word"
    with tempfile.TemporaryDirectory(prefix="keel-context-word-") as raw:
        check, failure = _tasks_semantics_probe(raw)
        if failure is not None:
            report(f"{label}: keel --install failed while building the fixture.")
            report(failure)
            return 1

        # A word is not the words inside it. Each carries a hash-shaped token so
        # that the host word is the only thing under test.
        for host in ("remaining", "heading", "domain", "maintains"):
            state, errors = check(
                "- [x] A1 implementation\n"
                f"  - Evidence:\n"
                f"    - M1: pass — 0 anchors {host}, recorded at sha256:01b9e740ab.\n"
            )
            if state == "unreported":
                report(f"{label}: keel --check reported no state at all on `{host}`.")
                return 1
            if state != "ok":
                report(
                    f"{label}: `{host}` was read as a context word. It contains "
                    "one, which is not the same thing, and the token beside it "
                    "here is a contract anchor. The author's only repair is to "
                    "reword a line that was correct."
                )
                for error in errors:
                    report(f"  {error}")
                return 1

        # The control. A check that passes because nothing is refused any more
        # is indistinguishable from this one, so the inflections the owner
        # decided to keep are asserted in the same repository.
        for host in ("commit", "commits", "committed", "committing", "hashes"):
            state, errors = check(
                "- [x] A1 implementation\n"
                f"  - Evidence:\n"
                f"    - M1: pass — {host} a1b2c3d4e5f6 verified.\n"
            )
            if state == "unreported":
                report(f"{label}: keel --check reported no state at all on `{host}`.")
                return 1
            if state != "failed":
                report(
                    f"{label}: an identifier beside `{host}` was accepted. That "
                    "word names the act the rule exists to catch, and requiring "
                    "a boundary must not stop it counting."
                )
                return 1
            if not [error for error in errors if "tasks.md:" in error]:
                report(f"{label}: the refusal on `{host}` named no line.")
                return 1

        # The Chinese words carry no boundary, because none is definable
        # between two word characters. Asserted here rather than reasoned
        # about: `\b提交\b` matches none of these. What the absence buys is
        # the context supply below — each line holds a hash-shaped token and
        # no other context word, so the Chinese word is the only thing that
        # can make the token an identifier. The wording rule no longer rests
        # on this: 提交 alone is an ordinary verb and needs a git word of its
        # own, which `a-submission-is-not-a-commit` covers.
        for recorded in ("已提交", "未提交", "该任务尚未提交"):
            state, _ = check(
                "- [x] A1 implementation\n"
                "  - Evidence:\n"
                f"    - M1: {recorded} a1b2c3d4e5f6。\n"
            )
            if state == "unreported":
                report(
                    f"{label}: keel --check reported no state at all on "
                    f"`{recorded}`. This is not a verdict about the fixture — "
                    "the check did not reach the point of having one."
                )
                return 1
            if state != "failed":
                report(
                    f"{label}: an identifier beside `{recorded}` was accepted. "
                    "A word boundary around a Chinese context word disables it "
                    "silently, which is why it does not carry one."
                )
                return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_a_submission_is_not_a_commit_scenario() -> int:
    """Issue #103: a general Chinese verb was read as a git word.

    \u63d0\u4ea4 is an ordinary transitive verb — \u63d0\u4ea4\u8d44\u6599, \u63d0\u4ea4\u5ba1\u6838, \u63d0\u4ea4\u7533\u8bf7. Matched bare, it
    refused an Evidence line recording that a user had submitted paperwork to
    a third-party review queue, while the same fact written in English passed
    untouched. A check whose verdict depends on which language the author
    wrote in is not checking what it claims to.

    \u5408\u5165 is the other half and stays bare: it names the git act and has no
    ordinary-prose reading, so requiring context for it would buy nothing.
    """
    label = "a-submission-is-not-a-commit"

    with tempfile.TemporaryDirectory(prefix="keel-submission-") as raw:
        check, failure = _tasks_semantics_probe(raw)
        if failure is not None:
            report(f"{label}: keel --install failed while building the fixture.")
            report(failure)
            return 1

        def evidence(text: str) -> str:
            return (
                "- [x] A1 implementation\n"
                "  - Evidence:\n"
                f"    - M1: {text}\n"
            )

        # The report's own line, and its English translation. Neither says
        # anything about this repository's git state, and the check must not
        # split them.
        accepted = (
            (
                "the reported line",
                "\u6536\u5de5\u72b6\u6001\u4e00\u5e76\u767b\u8bb0\uff1a\u7528\u6237\u5f53\u5929**\u5df2\u63d0\u4ea4**\u80fd\u586b\u7684\u5546\u6237\u4e0e\u7ed3\u7b97\u8d44\u6599\u3002",
            ),
            (
                "its English translation",
                "the user has submitted the merchant paperwork for review.",
            ),
            (
                "a submission to a review queue",
                "\u8868\u5355**\u5df2\u63d0\u4ea4**\uff0c\u5f00\u53d1\u8005\u8d26\u6237\u5904\u4e8e\u5ba1\u6838\u4e2d\u3002",
            ),
        )
        for description, text in accepted:
            state, errors = check(evidence(text))
            if state == "unreported":
                report(
                    f"{label}: keel --check reported no state at all on "
                    f"{description}."
                )
                return 1
            if state != "ok":
                report(
                    f"{label}: {description} was refused as recorded commit "
                    "state. Nothing on that line names git, and the same "
                    "sentence in English is accepted — so what the check "
                    "measured was the language, not the claim."
                )
                for error in errors:
                    report(f"  {error}")
                return 1

        # What the rule exists to catch, kept refused. Each of these carries a
        # git word, so the subject of the verb is not in doubt.
        refused = (
            ("beside a branch name", "1.2 \u7684\u6539\u52a8**\u5df2\u63d0\u4ea4**\u5230 main\u3002"),
            ("beside \u5206\u652f", "\u8be5\u5206\u652f\u7684\u6539\u52a8**\u5c1a\u672a\u63d0\u4ea4**\uff0c\u7b49\u5f85\u8bc4\u5ba1\u3002"),
            ("beside \u4ee3\u7801", "\u4ee3\u7801**\u5df2\u63d0\u4ea4**\uff0c\u6587\u6863\u672a\u52a8\u3002"),
            ("\u5408\u5165 alone", "\u8fd9\u4e00\u6ce2**\u672a\u5408\u5165**\uff0c\u4e0b\u5468\u518d\u8bf4\u3002"),
            ("\u5df2\u5408\u5165 alone", "\u8be5\u6539\u52a8**\u5df2\u5408\u5165**\u3002"),
        )
        for description, text in refused:
            state, errors = check(evidence(text))
            if state == "unreported":
                report(
                    f"{label}: keel --check reported no state at all on a "
                    f"line {description}."
                )
                return 1
            if state != "failed":
                report(
                    f"{label}: recorded state {description} was accepted. "
                    "Requiring context must narrow which lines are read, not "
                    "which words the rule knows."
                )
                return 1
            if not [error for error in errors if "tasks.md:" in error]:
                report(f"{label}: the refusal {description} named no line.")
                return 1

        # The contextual-identifier rule is untouched: a Chinese state word
        # still supplies context to a hash-shaped token, with no other context
        # word on the line.
        state, _ = check(evidence("\u5df2\u63d0\u4ea4 a1b2c3d4e5f6 \u5f85\u9a8c\u3002"))
        if state != "failed":
            report(
                f"{label}: a hash-shaped token beside a Chinese state word "
                "was accepted. This change bounds the wording rule, not the "
                "contextual-identifier rule."
            )
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_a_quoted_span_is_not_a_claim_scenario() -> int:
    """Issue #65 §2 and §4: quoted material was read as an assertion.

    Evidence prose quotes what it is evidence of — the command that ran, the
    output it printed, the branch base it ran against, the name of the
    requirement under change. `withoutInlineCode()` in
    `src/core/task-contract.js` already settled that shape for the field
    reader; this check never had it, so a Scope check recording that it ran
    `git status --short` was refused for the word inside the backticks.

    The boundary matters as much as the exemption: quoting one token must not
    exempt the sentence around it, or the rule becomes optional.
    """
    label = "a-quoted-span-is-not-a-claim"

    with tempfile.TemporaryDirectory(prefix="keel-quoted-span-") as raw:
        check, failure = _tasks_semantics_probe(raw)
        if failure is not None:
            report(f"{label}: keel --install failed while building the fixture.")
            report(failure)
            return 1

        # Each of these carries its whole match inside a quoted span. Nothing
        # outside the quotes on any of these lines is a claim about this
        # repository's git state.
        quoted = (
            (
                "inline code holding quoted output",
                "- [x] A1 implementation\n"
                "  - Evidence:\n"
                "    - M1.red: fail, as required. The runner printed "
                "`fatal: you have uncommitted changes`.\n",
            ),
            (
                "inline code holding an identifier and its context word",
                "- [x] A1 implementation\n"
                "  - Evidence:\n"
                "    - M1: pass. The fixture repository reported "
                "`HEAD is at 3f2a9bc` before the run.\n",
            ),
            (
                "a fenced block holding output",
                "- [x] A1 implementation\n"
                "  - Evidence:\n"
                "    - M1: pass. The runner printed:\n"
                "      ```\n"
                "      HEAD is at 3f2a9bc, working tree uncommitted\n"
                "      ```\n",
            ),
            (
                "a quotation span holding a requirement name",
                "- [x] A1 implementation\n"
                "  - Evidence:\n"
                "    - M1: pass. This task renames \u201cA recorded commit "
                "hash is recognized by what makes it one\u201d.\n",
            ),
        )
        for description, body in quoted:
            state, errors = check(body)
            if state == "unreported":
                report(
                    f"{label}: keel --check reported no state at all on "
                    f"{description}. This is not a verdict about the fixture — "
                    "the check did not reach the point of having one."
                )
                return 1
            if state != "ok":
                report(
                    f"{label}: {description} was read as a claim. A quoted "
                    "span is content the author cites, and the only repair "
                    "open to them is to stop quoting it accurately."
                )
                for error in errors:
                    report(f"  {error}")
                return 1

        # The boundary. Quoting one token exempts that token and nothing else.
        state, errors = check(
            "- [x] A1 implementation\n"
            "  - Evidence:\n"
            "    - M1: verified against `3f2a9bc`, but the work is still "
            "uncommitted.\n"
        )
        if state != "failed":
            report(
                f"{label}: wording outside a quoted span was exempted. The "
                "span is what stops being read, not the line holding it."
            )
            return 1
        if not [error for error in errors if "tasks.md:" in error]:
            report(f"{label}: the refusal outside the span named no line.")
            return 1

        # An apostrophe is not a quotation delimiter. Treating it as one would
        # silence the remainder of any line carrying a contraction, which is
        # the failure mode that is invisible rather than wrong.
        state, errors = check(
            "- [x] A1 implementation\n"
            "  - Evidence:\n"
            "    - M1: the guard doesn't fire here, and the worktree is "
            "uncommitted.\n"
        )
        if state != "failed":
            report(
                f"{label}: a contraction opened a quotation span and silenced "
                "the rest of the line. The ASCII single quote is an "
                "apostrophe far more often than it is a quotation mark."
            )
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_a_task_field_cites_its_provenance_scenario() -> int:
    """Issue #213: a Review field naming its base failed `keel state`.

    The contextual-hash rule matched a context word and a hash-shaped token
    anywhere on one line, and the dirty rule matched the bare word. Inside a
    task field that reads cited provenance as recorded state: the base a Scope
    check compared against (which review-checklist asks it to name), the
    commit a result ran on, a cache buffer's `dirty groups`, and a negation
    about another checkout. Each accepted line below is one rtl_ppa_prj wrote,
    shortened; line 262's shape is an Acceptance criterion of a checked task,
    so rewording it would move a recorded fingerprint.
    """
    label = "a-task-field-cites-its-provenance"
    task = "- [x] A1 implementation\n"
    accepted = (
        ("a Scope check naming its base",
         "  - Evidence:\n    - Review:\n      - Scope check: git diff against task-start "
         "base 1f3a6b0 changes only the declared TB. Frozen input hashes identify "
         "actual 211dfb5 RTL.\n"),
        ("an Acceptance check naming the commit it ran on",
         "  - Evidence:\n    - Review:\n      - Acceptance check: P2 55/55 on dec4d6e. "
         "All 15 manifests match current source hashes.\n"),
        ("an Acceptance criterion bounding scope by a base",
         "  - Acceptance:\n    - Only declared files change after synchronized base "
         "dec4d6e. Capture shared HEAD and reject unexpected staged scope before commit.\n"),
        ("a domain term",
         "  - Evidence:\n    - M2: pass. All 24 resource traces end with no dirty groups.\n"),
        ("a negation about another checkout",
         "  - Evidence:\n    - Review:\n      - Scope check: no design edits were authored "
         "or copied from uncommitted Claude changes.\n"),
    )
    refused = (
        ("a commit recorded in a field",
         "  - Evidence:\n    - M1: pass, committed to main as a1b2c3d.\n"),
        ("HEAD recorded in a field", "  - Evidence:\n    - M1: HEAD is at a1b2c3d.\n"),
        ("a merge recorded in Chinese", "  - Evidence:\n    - M1: 已合入 a1b2c3d。\n"),
        ("work state stated in a field",
         "  - Evidence:\n    - M1: pass, but the work is still uncommitted.\n"),
        ("a Status value", "  - Evidence:\n    - Status: dirty\n"),
    )

    with tempfile.TemporaryDirectory(prefix="keel-task-field-") as raw:
        check, failure = _tasks_semantics_probe(raw)
        if failure is not None:
            report(f"{label}: keel --install failed while building the fixture.")
            report(failure)
            return 1
        for description, body in accepted:
            state, errors = check(task + body)
            if state == "unreported":
                report(f"{label}: keel --check reported no state at all on {description}.")
                return 1
            if state != "ok":
                report(f"{label}: {description} was refused as recorded state. A task "
                       "field cites its provenance, and the only repair open to the "
                       "author is to leave the evidence out.")
                for error in errors:
                    report(f"  {error}")
                return 1
        # The boundary: a bound claim inside a field, and any claim outside one.
        for description, body in (*refused, (
            "a title line carrying a context word and a hash apart",
            "- [x] A1 done on main, see a1b2c3d\n  - Touch:\n    - src/a.js\n",
        )):
            text = body if body.startswith("- [") else task + body
            state, errors = check(text)
            if state == "unreported":
                report(f"{label}: keel --check reported no state at all on {description}.")
                return 1
            if state != "failed":
                report(f"{label}: {description} was accepted. Binding the rule to a "
                       "claim must not stop it refusing the claim.")
                return 1
            if not [error for error in errors if "tasks.md:" in error]:
                report(f"{label}: the refusal of {description} named no line.")
                return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_a_covers_citation_is_not_a_record_scenario() -> int:
    """Issue #65 §4: the rule refused a tasks.md that cited it.

    A `Covers` entry names a requirement that must exist in a spec. When the
    requirement is about the state this check forbids — dirty worktrees,
    recorded identifiers — citing it by name reads to the check as recording
    it. The repair available to the author is to rename the requirement, which
    is what 5.19.0 did.

    Eleven lines across four changes in this repository's history sit in this
    shape, eight of them citing requirements published in `openspec/specs/`.
    """
    label = "a-covers-citation-is-not-a-record"
    # Two requirement names published in this repository today. Neither is
    # invented for the fixture; both are cited by archived changes.
    cited = (
        "keel-core-gates / Dirty-worktree attribution is conservative"
        " / A path already dirty at task start is not attributed",
        "keel-stateless-continuity / A recorded commit hash is recognized by"
        " what makes it one / A decimal run is not a hash",
    )

    with tempfile.TemporaryDirectory(prefix="keel-covers-citation-") as raw:
        check, failure = _tasks_semantics_probe(raw)
        if failure is not None:
            report(f"{label}: keel --install failed while building the fixture.")
            report(failure)
            return 1

        state, errors = check(
            "- [x] A1 implementation\n"
            "  - Covers:\n"
            + "".join(f"    - {entry}\n" for entry in cited)
            + "  - Touch:\n    - src/a.js\n"
        )
        if state == "unreported":
            report(f"{label}: keel --check reported no state at all on a citation.")
            return 1
        if state != "ok":
            report(
                f"{label}: a Covers citation was read as a record of the state "
                "it names. The entry is a reference to a requirement that has "
                "to exist elsewhere, and the only repair open to the author is "
                "to rename that requirement."
            )
            for error in errors:
                report(f"  {error}")
            return 1

        # The control, and the boundary. The same wording outside the field is
        # a statement, and is still refused — otherwise this scenario would
        # pass just as well against a check that had stopped running.
        state, errors = check(
            "- [x] A1 implementation\n"
            "  - Covers:\n"
            + "".join(f"    - {entry}\n" for entry in cited)
            + "  - Evidence:\n"
            "    - M1: pass — the worktree was dirty when the task started.\n"
        )
        if state == "unreported":
            report(
                f"{label}: keel --check reported no state at all while reading "
                "the wording outside the field."
            )
            return 1
        if state != "failed":
            report(
                f"{label}: the same wording in an Evidence line was accepted. "
                "The exemption is the Covers field, not the file that contains "
                "one."
            )
            return 1
        named = [error for error in errors if "tasks.md:" in error]
        if not named:
            report(f"{label}: the refusal outside the field named no line.")
            return 1
        # The citations are the two lines under the label, and each carries
        # wording this rule refuses; naming either of them means the exemption
        # did not hold while the Evidence line was being refused.
        if any(f"tasks.md:{cited_line}:" in error
               for error in named for cited_line in (11, 12)):
            report(
                f"{label}: the refusal named a citation line. The rule fired "
                "correctly on the Evidence line and wrongly on the field, so "
                "what is wrong is the field's bound."
            )
            for error in named:
                report(f"  {error}")
            return 1

        # The bound ends where the next field begins. A `Covers` field that
        # ran to the end of the task would swallow the Evidence line above and
        # make that control vacuous, so the end of the field is asserted from
        # the other side too.
        state, _ = check(
            "- [x] A1 implementation\n"
            "  - Covers:\n"
            f"    - {cited[0]}\n"
            "  - Verify:\n"
            "    - M1: the change is 已合入 and needs no further work.\n"
        )
        if state == "unreported":
            report(
                f"{label}: keel --check reported no state at all while reading "
                "the field that follows a Covers field."
            )
            return 1
        if state != "failed":
            report(
                f"{label}: a Verify line following a Covers field was exempted. "
                "The field ends at the next field label."
            )
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


# A helper the strategy scenarios share. The task body is written out rather
# than reusing `change_verify_task` because these scenarios need to omit fields
# that helper always emits.
def strategy_probe_task(
    *,
    strategy: str | None,
    reason: str | None = None,
    mode: str = "implementation",
    form: str = "Verify",
    commands: tuple[str, ...] = ("M1: node test.js asserts the public behavior",),
) -> str:
    lines = [
        "- [ ] 1.1 Strategy probe",
        "  - Owner: claude",
        f"  - Mode: {mode}",
        "  - Covers:",
        "    - E1: the task proves its own behavior",
        "  - Read:",
        "    - README.md",
        "  - Touch:",
        "    - src/example.js",
    ]
    # In the expanded v3 form the strategy and its reason are task-level fields
    # beside `Commands`, not entries inside it.
    if form != "Verify":
        if strategy is not None:
            lines.append(f"  - Verification Strategy: {strategy}")
        if reason is not None:
            lines.append(f"  - Verification Reason: {reason}")
    lines.append(f"  - {form}:")
    if form == "Verify":
        if strategy is not None:
            lines.append(f"    - Strategy: {strategy}")
        if reason is not None:
            lines.append(f"    - Reason: {reason}")
    lines.extend(f"    - {entry}" for entry in commands)
    lines.extend(
        [
            "  - Acceptance:",
            "    - Public behavior passes.",
            "  - Autonomy boundary:",
            "    - Default: hard-stop",
            "    - Pre-authorized fallback: none",
            "  - Stop Rules:",
            "    - Stop on failure.",
            "  - Evidence:",
            "    - Contract: pending",
        ]
    )
    lines.extend(
        f"    - {entry.split(':', 1)[0].split(' ')[0]}: pending" for entry in commands
    )
    lines.extend(
        [
            "    - Review:",
            "      - Status: pass",
            "      - Acceptance check: behavior proven.",
            "      - Scope check: writes stayed inside Touch.",
            "      - Findings: none",
            "    - Blocker: none",
            "  - Stop if:",
            "    - Requires files outside Touch.",
        ]
    )
    return "\n".join(lines) + "\n"


def strategy_probe_start(root: Path, name: str, task: str) -> dict:
    repo = root / name
    write_gate_fixture(repo, tasks=task)
    result = run_keel(
        repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "unparsed", "problems": [{"message": result.stdout[:400]}]}


def problem_text(payload: dict) -> str:
    return " ".join(
        str(entry.get("message", "")) for entry in (payload.get("problems") or [])
    )


def problem_codes(payload: dict) -> list[str]:
    return [str(entry.get("code", "")) for entry in (payload.get("problems") or [])]


# Red-green forces the expensive half — a check that fails before the
# implementation exists — and enforces that a `.red` line is present. Nothing
# checked that the red failed *because of the thing under test*. Issue #116
# measured two reds in one session that were shape-perfect and failed for an
# unrelated reason: one where the fixture had not cleared PATH so the check
# passed, one where the fixture contained no wording the checker would refuse.
# The declaration is what a gate can hold: written into the check, so it is in
# the fingerprint, and therefore written before the run rather than after it.
def validate_declared_literal_whitespace_scenario() -> int:
    """Issue #479 D1, D2: declared literals match recorded Evidence with whitespace runs as one space.

    Tool output aligns with runs of spaces; a literal copied from it must
    match the raw output it was copied from, while different characters are
    still refused and the refusal rules spacing out.
    """
    label = "declared-literal-whitespace"
    with tempfile.TemporaryDirectory(prefix="keel-literal-479-") as raw:
        repo = Path(raw) / "repo"

        def complete(check: str, evidence: list[str]) -> dict:
            task = "\n".join([
                "- [x] 1.1 Literal probe",
                "  - Owner: claude",
                "  - Mode: implementation",
                "  - Covers:",
                "    - E1: the task proves its own behavior",
                "  - Read:",
                "    - README.md",
                "  - Touch:",
                "    - src/example.js",
                "  - Verify:",
                "    - Strategy: vertical-tdd",
                f"    - M1: node test.js asserts the public behavior. {check}",
                "  - Evidence:",
                *evidence,
                "    - Review:",
                "      - Status: pass",
                "      - Acceptance check: the behavior is proven.",
                "      - Scope check: only Touch changed.",
                "      - Findings: none.",
                "    - Blocker: none",
                "    - Reauthorizations: none",
            ])
            write_gate_fixture(repo, tasks=task)
            started = run_keel(repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--record", "--json")
            try:
                json.loads(started.stdout)
            except json.JSONDecodeError:
                return {"status": "unstarted", "problems": [{"message": started.stdout[:300]}]}
            done = run_keel(repo, "gate", "task-complete", "--change", "demo", "--task", "1.1", "--json")
            try:
                return json.loads(done.stdout)
            except json.JSONDecodeError:
                return {"status": "unparsed", "problems": [{"message": done.stdout[:400]}]}

        cases = (
            ("an aligned failure signature", "Fails with: `FAIL  record reachable`",
             ["    - M1: pass.", "    - M1.red: fail. `FAIL  record reachable` (exit 1).", "    - M1.green: pass."]),
            ("an aligned injection failure", "Fails with: `boom` Detects: `drop the guard` -> `FAIL  guard missing`",
             ["    - M1: pass.", "    - M1.red: fail. `boom`.", "    - M1.green: pass.",
              "    - M1.detects: fail. `FAIL   guard missing`."]),
            ("a spaced measurement", "Fails with: `boom` Measured: `took  12 s`",
             ["    - M1: pass. the run took 12 s.", "    - M1.red: fail. `boom`.", "    - M1.green: pass."]),
        )
        for name, check, evidence in cases:
            result = complete(check, evidence)
            if result.get("status") != "pass":
                report(f"{label}: {name} copied from the raw output was refused; {problem_codes(result)!r} {problem_text(result)!r}.")
                return 1
        wrong = complete("Fails with: `FAIL  record reachable`",
                         ["    - M1: pass.", "    - M1.red: fail. `FAIL record unreachable` (exit 1).", "    - M1.green: pass."])
        if "red-missing-declared-failure" not in problem_codes(wrong):
            report(f"{label}: a red with different characters was not refused as red-missing-declared-failure; {problem_codes(wrong)!r}.")
            return 1
        if "as one space" not in problem_text(wrong):
            report(f"{label}: the refusal does not say runs of whitespace are compared as one space; {problem_text(wrong)!r}.")
            return 1
    report(f"{label} scenario passed.")
    return 0


def validate_red_declares_what_it_proves_scenario() -> int:
    label = "a-red-declares-what-it-proves"
    signature = "openspec: not found"
    declared = (
        f"M1: node test.js asserts the public behavior. Fails with: `{signature}`",
    )
    plain = ("M1: node test.js asserts the public behavior",)
    with tempfile.TemporaryDirectory(prefix="keel-failswith-") as raw:
        root = Path(raw)

        def start(name: str, **kwargs) -> dict:
            return strategy_probe_start(
                root, name, strategy_probe_task(**kwargs)
            )

        def commands_of(payload: dict) -> list[dict]:
            contract = payload.get("contract") or {}
            capsule = contract.get("capsule") or {}
            return ((capsule.get("verification") or {}).get("commands") or [])

        def fingerprint_of(payload: dict) -> str:
            return str((payload.get("contract") or {}).get("fingerprint") or "")

        # A declared signature compiles and is carried as its own field, so the
        # gate can read it without re-parsing the author's prose.
        with_signature = start(
            "declared", strategy="vertical-tdd", commands=declared
        )
        if with_signature.get("status") != "pass":
            report(
                f"{label}: a check declaring a failure signature was refused; "
                f"got {with_signature.get('status')!r} "
                f"{problem_text(with_signature)!r}."
            )
            return 1
        compiled = commands_of(with_signature)
        if len(compiled) != 1 or compiled[0].get("failsWith") != signature:
            report(
                f"{label}: the compiled check does not carry the declared "
                f"failure signature; got {compiled!r}."
            )
            return 1
        # The clause is part of the check the author wrote, so it stays in
        # `check` as well; the field is what the gate reads, not a replacement
        # for the text.
        if "Fails with:" not in str(compiled[0].get("check", "")):
            report(
                f"{label}: compiling the signature stripped it out of the "
                f"check text the author wrote; got {compiled[0]!r}."
            )
            return 1

        # In the fingerprint for free, which is what makes the declaration a
        # prediction rather than a transcription: it cannot be retrofitted to
        # whatever the run happened to print without the anchor moving.
        edited = start(
            "edited",
            strategy="vertical-tdd",
            commands=(
                "M1: node test.js asserts the public behavior. "
                "Fails with: `a different failure entirely`",
            ),
        )
        without = start("without", strategy="vertical-tdd", commands=plain)
        prints = {
            "declared": fingerprint_of(with_signature),
            "edited": fingerprint_of(edited),
            "without": fingerprint_of(without),
        }
        if not all(prints.values()):
            report(f"{label}: a probe reported no fingerprint; got {prints!r}.")
            return 1
        if prints["declared"] == prints["edited"]:
            report(
                f"{label}: editing only the declared failure signature left "
                f"the fingerprint unmoved at {prints['declared']!r}, so a "
                "signature could be rewritten after the red was recorded."
            )
            return 1
        if prints["declared"] == prints["without"]:
            report(
                f"{label}: declaring a signature left the fingerprint "
                f"unmoved at {prints['without']!r}."
            )
            return 1

        # A declaration that can produce no red is refused rather than left to
        # sit in the contract doing nothing, which reads to its author as a
        # check being enforced.
        for name, kwargs in (
            (
                "regression",
                dict(
                    strategy="vertical-tdd",
                    commands=(
                        "M1: node test.js asserts the public behavior",
                        "M2 (regression): the suite stays green. "
                        f"Fails with: `{signature}`",
                    ),
                ),
            ),
            (
                "no-red-strategy",
                dict(
                    strategy="evidence-first",
                    reason="the artifact is inspected after it is written.",
                    commands=declared,
                ),
            ),
        ):
            payload = start(name, **kwargs)
            if payload.get("status") != "fail":
                report(
                    f"{label}: a failure signature on a check with no red "
                    f"({name}) was accepted; got {payload.get('status')!r}."
                )
                return 1
            text = problem_text(payload)
            expected_label = "M2" if name == "regression" else "M1"
            if expected_label not in text or "red" not in text:
                report(
                    f"{label}: the refusal for {name} does not name the check "
                    f"and say it records no red; got {text!r}."
                )
                return 1
            if "signature-without-red" not in problem_codes(payload):
                report(
                    f"{label}: the refusal for {name} carries no "
                    f"signature-without-red code; got "
                    f"{problem_codes(payload)!r}."
                )
                return 1

        # A marker that names no literal is the shape of a typo. Ignoring it
        # leaves the author believing a signature is enforced when none parsed.
        for name, check in (
            ("bare", "M1: node test.js asserts the behavior. Fails with:"),
            (
                "unquoted",
                "M1: node test.js asserts the behavior. Fails with: not found",
            ),
            (
                "not-closing",
                "M1: node test.js asserts it. Fails with: `not found` "
                "and then keeps going.",
            ),
        ):
            payload = start(name, strategy="vertical-tdd", commands=(check,))
            if payload.get("status") != "fail":
                report(
                    f"{label}: a malformed signature marker ({name}) compiled "
                    f"as if nothing were declared; got "
                    f"{payload.get('status')!r}."
                )
                return 1
            if "malformed-failure-signature" not in problem_codes(payload):
                report(
                    f"{label}: the refusal for {name} carries no "
                    f"malformed-failure-signature code; got "
                    f"{problem_codes(payload)!r}."
                )
                return 1

        # The escape is the one this repository already established for quoted
        # material: a check that describes this rule has to be able to name it.
        quoted = start(
            "quoted",
            strategy="vertical-tdd",
            commands=(
                "M1: a `Fails with:` marker with no literal is refused by name",
            ),
        )
        if quoted.get("status") != "pass":
            report(
                f"{label}: a marker written inside inline code was read as a "
                f"declaration; got {quoted.get('status')!r} "
                f"{problem_text(quoted)!r}."
            )
            return 1
        if commands_of(quoted)[0].get("failsWith") is not None:
            report(
                f"{label}: a marker inside inline code compiled to a failure "
                f"signature; got {commands_of(quoted)!r}."
            )
            return 1

        # The obligation is stated where the author is deciding — before the
        # failing check is written — rather than discovered once it has run.
        warnings = " ".join(str(w) for w in (with_signature.get("warnings") or []))
        if signature not in warnings or "M1" not in warnings:
            report(
                f"{label}: the task-start obligation does not name which "
                f"checks declared a failure signature; got {warnings!r}."
            )
            return 1
        undeclared = " ".join(str(w) for w in (without.get("warnings") or []))
        if "declared no failure signature" not in undeclared:
            report(
                f"{label}: the obligation does not say that a check owing a "
                f"red declared no signature; got {undeclared!r}."
            )
            return 1

        # Completion is where the declaration becomes a criterion.
        repo = root / "completion"
        tasks_path = repo / "openspec/changes/demo/tasks.md"

        def complete(check: str, red: str) -> dict:
            write_gate_fixture(
                repo,
                tasks=strategy_probe_task(
                    strategy="vertical-tdd", commands=(check,)
                ).replace(
                    "    - M1: pending\n",
                    f"    - M1: the check ran.\n"
                    f"    - M1.red: {red}\n"
                    "    - M1.green: it passed after the implementation.\n",
                ),
            )
            record_contract_anchor(repo, "demo")
            result = run_keel(
                repo,
                "gate",
                "task-complete",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
            )
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {
                    "status": "unparsed",
                    "problems": [{"message": result.stdout[:400]}],
                }

        declared_check = declared[0]
        mismatched = complete(
            declared_check, "it failed before the implementation existed."
        )
        if mismatched.get("status") != "fail":
            report(
                f"{label}: task-complete accepted a red that does not show "
                f"the declared failure; got {mismatched.get('status')!r}."
            )
            return 1
        text = problem_text(mismatched)
        if "M1" not in text or signature not in text:
            report(
                f"{label}: the refusal names neither the check nor the string "
                f"it did not find; got {text!r}."
            )
            return 1
        if "red-missing-declared-failure" not in problem_codes(mismatched):
            report(
                f"{label}: the refusal carries no "
                f"red-missing-declared-failure code; got "
                f"{problem_codes(mismatched)!r}."
            )
            return 1

        matched = complete(
            declared_check,
            f"it failed with `{signature}` before the implementation existed.",
        )
        if matched.get("status") != "pass":
            report(
                f"{label}: a red showing the declared failure was refused; "
                f"got {matched.get('status')!r} {problem_text(matched)!r}."
            )
            return 1

        # D3: the undeclared case is unchanged, asserted against the same
        # fixture with the clause removed and the same weak red that the
        # declared check was refused for.
        undeclared_task = complete(
            plain[0], "it failed before the implementation existed."
        )
        if undeclared_task.get("status") != "pass":
            report(
                f"{label}: a red-green task declaring no signature stopped "
                f"completing; got {undeclared_task.get('status')!r} "
                f"{problem_text(undeclared_task)!r}."
            )
            return 1

    report(f"{label} scenario passed.")
    return 0


# The strategy was the one capsule field the compiler supplied from a value no
# spec documents as a default — and it supplied the weakest of the six, so
# omitting the line was how a task opted out of red-green.
def validate_strategy_is_declared_scenario() -> int:
    label = "a-strategy-is-declared"
    with tempfile.TemporaryDirectory(prefix="keel-strategy-") as raw:
        root = Path(raw)

        missing = strategy_probe_start(
            root, "missing", strategy_probe_task(strategy=None)
        )
        if missing.get("status") != "fail":
            report(
                f"{label}: a task declaring Verify with no Strategy was not "
                f"refused; task-start returned {missing.get('status')!r}."
            )
            return 1
        text = problem_text(missing)
        for needed in ("vertical-tdd", "evidence-first", "strategy"):
            if needed not in text:
                report(
                    f"{label}: the refusal for a missing strategy omits "
                    f"{needed!r}; got {text!r}."
                )
                return 1
        # The failure this change exists to remove: reporting the task as using
        # a strategy it never named.
        if "unsupported" in text:
            report(
                f"{label}: a missing strategy was reported as an unsupported "
                f"one, which sends the reader looking for a typo; got {text!r}."
            )
            return 1
        if "missing-verification-strategy" not in problem_codes(missing):
            report(
                f"{label}: the refusal for a missing strategy carries no "
                f"missing-verification-strategy code; got "
                f"{problem_codes(missing)!r}."
            )
            return 1

        legacy = strategy_probe_start(
            root,
            "legacy",
            strategy_probe_task(strategy=None, form="Commands"),
        )
        if legacy.get("status") != "fail":
            report(
                f"{label}: an expanded v3 task declaring Commands with no "
                "Verification Strategy was not refused; task-start returned "
                f"{legacy.get('status')!r}."
            )
            return 1

        for strategy in (
            "vertical-tdd",
            "regression-first",
            "characterization",
            "snapshot-characterization",
            "rendered-behavior",
        ):
            declared = strategy_probe_start(
                root, f"ok-{strategy}", strategy_probe_task(strategy=strategy)
            )
            if declared.get("status") != "pass":
                report(
                    f"{label}: a task declaring {strategy} was refused; "
                    f"{problem_text(declared)!r}."
                )
                return 1

        unsupported = strategy_probe_start(
            root, "unsupported", strategy_probe_task(strategy="made-up-thing")
        )
        if unsupported.get("status") != "fail":
            report(
                f"{label}: an unsupported strategy was not refused; task-start "
                f"returned {unsupported.get('status')!r}."
            )
            return 1
        if "unsupported" not in problem_text(unsupported):
            report(
                f"{label}: an unsupported strategy lost its own diagnostic; "
                f"got {problem_text(unsupported)!r}."
            )
            return 1

        # A task declaring no verification form at all is already reported once,
        # as the one field it is missing. Restating it as a missing strategy is
        # the cascade this repository has removed before.
        formless = strategy_probe_start(
            root,
            "formless",
            strategy_probe_task(strategy=None).replace("  - Verify:\n", ""),
        )
        codes = problem_codes(formless)
        if "missing-verification-strategy" in codes:
            report(
                f"{label}: a task declaring no verification form was also told "
                f"its strategy is missing; codes {codes!r}."
            )
            return 1
        if codes != ["missing-verification-form"]:
            report(
                f"{label}: a task declaring no verification form should be "
                f"reported once, as that; got codes {codes!r}."
            )
            return 1

    report(f"{label} scenario passed.")
    return 0


# `evidence-first` is scoped by an absence — work that cannot use a meaningful
# red-green loop — and an absence is exactly the claim that has to be stated to
# be reviewable. The gate checks the reason is there and is a sentence; whether
# it is true belongs to the Review, the same contract `Discard reason:` has.
def validate_weakest_strategy_states_its_reason_scenario() -> int:
    label = "the-weakest-strategy-states-its-reason"
    with tempfile.TemporaryDirectory(prefix="keel-reason-") as raw:
        root = Path(raw)

        silent = strategy_probe_start(
            root, "silent", strategy_probe_task(strategy="evidence-first")
        )
        if silent.get("status") != "fail":
            report(
                f"{label}: an evidence-first task stating no reason was not "
                f"refused; task-start returned {silent.get('status')!r}."
            )
            return 1
        if "reason" not in problem_text(silent).lower():
            report(
                f"{label}: the refusal does not name the reason as what is "
                f"missing; got {problem_text(silent)!r}."
            )
            return 1

        for slot in ("TODO", "<why>"):
            empty = strategy_probe_start(
                root,
                f"slot-{slot.strip('<>')}",
                strategy_probe_task(strategy="evidence-first", reason=slot),
            )
            if empty.get("status") != "fail":
                report(
                    f"{label}: an evidence-first task whose reason is {slot!r} "
                    f"was accepted; task-start returned {empty.get('status')!r}."
                )
                return 1

        stated = strategy_probe_start(
            root,
            "stated",
            strategy_probe_task(
                strategy="evidence-first",
                reason="this task only moves documentation; there is no "
                "executable behavior that can fail first.",
            ),
        )
        if stated.get("status") != "pass":
            report(
                f"{label}: an evidence-first task stating a reason was refused; "
                f"{problem_text(stated)!r}."
            )
            return 1
        verification = (
            (stated.get("contract") or {})
            .get("capsule", {})
            .get("verification", {})
        )
        if "documentation" not in str(verification.get("reason", "")):
            report(
                f"{label}: the compiled capsule does not carry the stated "
                f"reason in its verification block; got {verification!r}."
            )
            return 1
        # D5: the reason is a field, not a check. A reason that took an M<n>
        # label would be a check the author never wrote.
        labels = [entry.get("label") for entry in verification.get("commands", [])]
        if labels != ["M1"]:
            report(
                f"{label}: the reason was parsed as a check; the compiled "
                f"checks are {labels!r}."
            )
            return 1

        # D3: no exemption. A mode the same author writes would be a second
        # escape hatch, and the first one is what this change closes.
        diagnostic = strategy_probe_start(
            root,
            "diagnose-only",
            strategy_probe_task(strategy="evidence-first", mode="diagnose-only"),
        )
        if diagnostic.get("status") != "fail":
            report(
                f"{label}: a diagnose-only task skipped the reason; task-start "
                f"returned {diagnostic.get('status')!r}."
            )
            return 1

        # D4: the requirement reaches only the strategy it is about.
        redgreen = strategy_probe_start(
            root, "redgreen", strategy_probe_task(strategy="vertical-tdd")
        )
        if redgreen.get("status") != "pass":
            report(
                f"{label}: a vertical-tdd task was asked for a reason; "
                f"{problem_text(redgreen)!r}."
            )
            return 1

    report(f"{label} scenario passed.")
    return 0


# A completed task fixture whose Review Findings the caller writes. Everything
# else is the shape `task-complete` needs so that the only thing under test is
# the Findings block.
def findings_fixture_repo(root: Path, name: str, findings: str) -> Path:
    repo = root / name
    task = strategy_probe_task(strategy="vertical-tdd")
    task = task.replace("- [ ] 1.1", "- [x] 1.1")
    task = task.replace(
        "    - M1: pending",
        "    - M1: pass. node test.js reported 3 passing.\n"
        "    - M1.red: fail, for the right reason. the assertion was absent.\n"
        "    - M1.green: pass. node test.js reported 3 passing.",
    )
    task = task.replace("      - Findings: none", f"      - Findings: {findings}")
    write_gate_fixture(repo, tasks=task)
    started = run_keel(
        repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--json"
    )
    fingerprint = json.loads(started.stdout)["contract"]["fingerprint"]["value"]
    tasks_path = repo / "openspec/changes/demo/tasks.md"
    tasks_path.write_text(
        tasks_path.read_text(encoding="utf-8").replace(
            "    - Contract: pending",
            f"    - Contract: keel-task-capsule/v1 sha256:{fingerprint}",
        ),
        encoding="utf-8",
    )
    return repo


def findings_completion(root: Path, name: str, findings: str) -> dict:
    repo = findings_fixture_repo(root, name, findings)
    result = run_keel(
        repo, "gate", "task-complete", "--change", "demo", "--task", "1.1", "--json"
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "unparsed", "problems": [{"message": result.stdout[:400]}]}


# `Findings` is free prose by design, and in a repository whose subject is the
# protocol that prose names the markers themselves. A quoted marker was read as
# a disposition — and because the resolution scan is global and stops at the
# first claim it cannot resolve, one mention eclipsed every real disposition
# beside it. 5.42.0 already decided that an inline-code span holds quoted
# material rather than an assertion; the rule had not reached this scan.
def validate_quoted_marker_is_not_a_disposition_scenario() -> int:
    label = "a-quoted-marker-is-not-a-disposition"
    tracker = "https://github.com/TanglmChris/keel/issues/114"
    with tempfile.TemporaryDirectory(prefix="keel-quoted-marker-") as raw:
        root = Path(raw)

        owned = findings_completion(
            root,
            "owned",
            "one, still open. The `Resolved here:` grammar is what this finding "
            f"is about. Durable owner: {tracker}",
        )
        if owned.get("status") != "pass":
            report(
                f"{label}: a quoted marker eclipsed a genuine tracker owner; "
                f"{problem_codes(owned)!r} {problem_text(owned)!r}."
            )
            return 1

        resolved = findings_completion(
            root,
            "resolved",
            "one, fixed here. The `Durable owner:` form is what this finding is "
            "about. Resolved here: M1",
        )
        if resolved.get("status") != "pass":
            report(
                f"{label}: a quoted marker eclipsed a genuine resolution; "
                f"{problem_codes(resolved)!r} {problem_text(resolved)!r}."
            )
            return 1

        # Every marker, not only the one that fired.
        for index, marker in enumerate(
            ("Resolved here:", "Durable owner:", "Discard reason:", "Discard rationale:")
        ):
            only = findings_completion(
                root,
                f"only-{index}",
                f"one. The `{marker}` marker is the topic of this finding, and "
                "nothing here disposes of it.",
            )
            codes = problem_codes(only)
            if only.get("status") != "fail":
                report(
                    f"{label}: a block whose only {marker!r} is quoted was "
                    "accepted, so the quotation created a disposition."
                )
                return 1
            if "finding-resolution-evidence" in codes:
                report(
                    f"{label}: a block whose only {marker!r} is quoted was "
                    "refused as a resolution with unusable evidence; it carries "
                    f"no disposition at all. Codes {codes!r}."
                )
                return 1
            if "finding-owner" not in codes:
                report(
                    f"{label}: a block whose only {marker!r} is quoted did not "
                    f"report the missing-disposition problem. Codes {codes!r}."
                )
                return 1

        # D5: the refusal names what it read.
        misread = findings_completion(
            root, "misread", "one. Resolved here: thoroughly, by rewriting it."
        )
        if misread.get("status") != "fail":
            report(f"{label}: a resolution naming no evidence was accepted.")
            return 1
        if "thoroughly" not in problem_text(misread):
            report(
                f"{label}: the refusal does not name the text it read as "
                f"evidence; got {problem_text(misread)!r}."
            )
            return 1

        # The verdicts that must not move.
        plain = findings_completion(root, "plain", "one, fixed. Resolved here: M1")
        if plain.get("status") != "pass":
            report(
                f"{label}: an ordinary resolution was refused; "
                f"{problem_text(plain)!r}."
            )
            return 1
        undeclared = findings_completion(
            root, "undeclared", "one, fixed. Resolved here: M9"
        )
        if undeclared.get("status") != "fail":
            report(
                f"{label}: a resolution naming a check the task does not "
                "declare was accepted."
            )
            return 1
        missing_path = findings_completion(
            root, "missing-path", "one, open. Durable owner: docs/nowhere.md"
        )
        if missing_path.get("status") != "fail":
            report(
                f"{label}: an owner naming a path that does not exist was "
                "accepted."
            )
            return 1

        # A disposition may legitimately wrap its value in backticks. The first
        # draft of the blanking removed whole code spans and destroyed exactly
        # these two forms; nothing in the suite noticed, which is why they are
        # asserted here rather than left to the reader who happens to ask.
        for name, findings in (
            ("backticked-owner", "one, open. Durable owner: `keel/archive/note.md`"),
            ("backticked-resolution", "one, fixed. Resolved here: `src/example.js`"),
        ):
            repo = findings_fixture_repo(root, name, findings)
            write_text(repo / "keel/archive/note.md", "note\n")
            write_text(repo / "src/example.js", "//\n")
            result = run_keel(
                repo, "gate", "task-complete", "--change", "demo", "--task",
                "1.1", "--json",
            )
            payload = json.loads(result.stdout)
            if payload.get("status") != "pass":
                report(
                    f"{label}: a disposition whose value is wrapped in "
                    f"backticks was refused ({name}); "
                    f"{problem_codes(payload)!r} {problem_text(payload)!r}."
                )
                return 1

    report(f"{label} scenario passed.")
    return 0


# A drift is a hard stop, so whatever the message says is what the author acts
# on. Saying only that a value moved produced a wrong record in this repository:
# the cause was recorded as a Review edit, which is measurably not covered by
# the fingerprint at all.
def validate_drift_names_where_to_look_scenario() -> int:
    label = "drift-names-where-to-look"

    def fixture(root: Path, name: str, anchor_value: str) -> Path:
        repo = root / name
        task = strategy_probe_task(strategy="vertical-tdd")
        # Cite a design statement so the capsule holds two distinct sources.
        task = task.replace(
            "    - E1: the task proves its own behavior",
            "    - E1: the task proves its own behavior\n    - D1",
        )
        task = task.replace(
            "    - Contract: pending",
            f"    - Contract: keel-task-capsule/v1 sha256:{anchor_value}",
        )
        write_gate_fixture(
            repo,
            tasks=task,
            design=(
                "## Context\n\nfixture\n\n## Decisions\n\n"
                "- D1 — the public behavior is proven through the CLI. "
                "Basis: fixture.\n"
            ),
        )
        return repo

    with tempfile.TemporaryDirectory(prefix="keel-drift-") as raw:
        root = Path(raw)

        # The true anchor, so the matching case can be compared against it.
        settled = fixture(root, "settled", "0" * 64)
        started = run_keel(
            settled, "gate", "task-start", "--change", "demo", "--task", "1.1",
            "--json", "--no-guard",
        )
        true_value = json.loads(started.stdout)["contract"]["fingerprint"]["value"]

        drifted = fixture(root, "drifted", "0" * 64)
        result = run_keel(drifted, "context", "--change", "demo", "--json")
        payload = json.loads(result.stdout)
        if payload.get("status") != "blocked":
            report(
                f"{label}: a task whose anchor does not match was not blocked; "
                f"status {payload.get('status')!r}."
            )
            return 1
        reason = " ".join(str(x) for x in (payload.get("reasons") or []))

        for needed in ("0" * 8, true_value[:8]):
            if needed not in reason:
                report(
                    f"{label}: the drift reason no longer reports both "
                    f"fingerprints; {reason!r}."
                )
                return 1
        for source in (
            "openspec/changes/demo/tasks.md",
            "openspec/changes/demo/design.md",
        ):
            if source not in reason:
                report(
                    f"{label}: the drift reason does not name the authority "
                    f"source {source!r}; {reason!r}."
                )
                return 1
        # The list is the authority set, not the change directory.
        if "proposal.md" in reason:
            report(
                f"{label}: the drift reason names a file the capsule resolved "
                f"no authority text from; {reason!r}."
            )
            return 1
        lowered = reason.lower()
        for word in ("evidence", "review", "checkbox"):
            if word not in lowered:
                report(
                    f"{label}: the drift reason does not say that {word} is "
                    f"outside the fingerprint; {reason!r}."
                )
                return 1
        # D3: it names a search set, never a culprit.
        for guess in ("changed field", "the field that changed", "caused by"):
            if guess in lowered:
                report(
                    f"{label}: the drift reason claims which field moved, which "
                    f"it cannot know; {reason!r}."
                )
                return 1

        matching = fixture(root, "matching", true_value)
        ok = json.loads(
            run_keel(matching, "context", "--change", "demo", "--json").stdout
        )
        if ok.get("status") != "ready":
            report(
                f"{label}: a task whose anchor matches was not ready; "
                f"{ok.get('status')!r} {ok.get('reasons')!r}."
            )
            return 1
        ok_reason = " ".join(str(x) for x in (ok.get("reasons") or []))
        if "fingerprint" in ok_reason.lower():
            report(
                f"{label}: a matching anchor now reports drift wording; "
                f"{ok_reason!r}."
            )
            return 1

    report(f"{label} scenario passed.")
    return 0


# Issue #112's minimal reproduction. An unfilled slot in an `M<n>` declaration
# stopped the contract compiling, the completion path fell back to the expanded
# v3 `Commands` field a compact task never declares, and every reference to an
# `M<n>` was reported as naming a check the task does not declare — first, and
# as somebody else's fault. The reporter calls it the only diagnostic in 149
# invocations that made them edit the wrong file.

# `## Expectation Coverage` carries the protocol's one global assertion — every
# expectation has an owner — and 80% of its closures were the single form with
# nothing behind them. Issue #133 ran the set difference by hand over 24
# archived changes and found six wrong claims, all of them already past
# change-close and a semantic Review. The operation that finds them is between
# two identifier lists the author already declared, in one file.
def validate_coverage_claim_is_compared_scenario() -> int:
    label = "a-coverage-claim-is-compared"

    design = (
        "## Context\n\nfixture\n\n## Decisions\n\n"
        "- F1 — the first fact the fixture declares.\n"
        "- F2 — the second fact the fixture declares.\n"
        "- D1 — the decision no task of the fixture covers.\n"
    )

    def task(tid: str, covers: str) -> str:
        return "\n".join((
            f"- [x] {tid} Coverage probe",
            "  - Owner: claude",
            "  - Mode: implementation",
            "  - Covers:",
            f"    - {covers}",
            "  - Read:",
            "    - README.md",
            "  - Touch:",
            "    - src/example.js",
            "  - Verify:",
            "    - Strategy: evidence-first",
            "    - Reason: fixture; nothing here can fail first",
            "    - M1: the check asserts the public behavior",
            "  - Autonomy boundary:",
            "    - Default: hard-stop",
            "    - Pre-authorized fallback: none",
            "  - Stop Rules:",
            "    - Stop if the fixture needs a decision it cannot make.",
            "  - Evidence:",
            "    - Contract: pending",
            "    - M1: pass. ran it.",
            "    - Review:",
            "      - Status: pass",
            "      - Acceptance check: M1 asserts the behavior at its interface.",
            "      - Scope check: only src/example.js changed.",
            "      - Findings: none",
            "    - Blocker: none",
            "    - Reauthorizations: none",
            "",
        ))

    def fixture(root: Path, name: str, coverage: str) -> Path:
        repo = root / name
        write_gate_fixture(repo, tasks="", design=design)
        write_text(
            repo / "openspec/changes/demo/tasks.md",
            "# Tasks\n\n"
            + "## Work\n\n"
            + task("1.1", "F1")
            + "\n"
            + task("2.1", "F2")
            + "\n## Invalidates\n\n- None.\n\n"
            + "## Expectation Coverage\n\n"
            + coverage
            + "\n",
        )
        # Both anchors, in order: `Contract: pending` is replaced once per task,
        # first occurrence first, and a task's fingerprint covers only its own
        # authority text, so recording one does not move the other.
        tasks_path = repo / "openspec/changes/demo/tasks.md"
        for tid in ("1.1", "2.1"):
            started = run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", tid,
                "--json", "--no-guard",
            )
            try:
                payload = json.loads(started.stdout)
            except json.JSONDecodeError:
                report(
                    f"{label}: the fixture's task {tid} did not start, so no "
                    f"anchor could be recorded; "
                    f"{(started.stderr or started.stdout).strip()[:400]!r}."
                )
                raise SystemExit(1)
            value = (
                ((payload.get("contract") or {}).get("fingerprint") or {})
                .get("value") or "0" * 64
            )
            tasks_path.write_text(
                tasks_path.read_text(encoding="utf-8").replace(
                    "    - Contract: pending",
                    f"    - Contract: keel-task-capsule/v1 sha256:{value}",
                    1,
                ),
                encoding="utf-8",
            )
        return repo

    def close(repo: Path) -> dict:
        result = run_keel(
            repo, "gate", "change-close", "--change", "demo", "--action",
            "archive", "--json",
        )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"status": "unparsed", "problems": [
                {"code": "unparsed", "message": result.stdout[:300]}
            ]}

    def said(payload: dict) -> str:
        return " ".join(str(x) for x in (payload.get("warnings") or []))

    agree = "- E1: the first expectation (F1). Covered by: 1.1\n" \
            "- E2: the second expectation (F2). Covered by: 2.1\n"
    # The identifier is covered — by the other task.
    mismatch = "- E1: the first expectation (F2). Covered by: 1.1\n" \
               "- E2: the second expectation. Covered by: 2.1\n"
    # The identifier is covered by nothing.
    orphan = "- E1: the first expectation (D1). Covered by: 1.1\n" \
             "- E2: the second expectation. Covered by: 2.1\n"
    # Same entry as `mismatch` with the citation removed, and nothing else.
    prose = "- E1: the first expectation. Covered by: 1.1\n" \
            "- E2: the second expectation. Covered by: 2.1\n"
    # Issue #133's contradiction: one identifier claimed covered and deferred.
    contradiction = "- E1: the first expectation (F2). Covered by: 1.1\n" \
                    "- E2: the same identifier, deferred (F2). " \
                    "Durable owner: https://github.com/TanglmChris/keel/issues/133\n"

    with tempfile.TemporaryDirectory(prefix="keel-coverage-claim-") as raw:
        root = Path(raw)

        # The control comes first: without a fixture that closes, every later
        # refusal could be something else refusing.
        settled = close(fixture(root, "agree", agree))
        if settled.get("status") != "pass":
            report(
                f"{label}: the agreeing fixture does not close, so no later "
                f"refusal can be attributed; {problem_text(settled)!r}."
            )
            return 1
        wrong = close(fixture(root, "mismatch", mismatch))
        if wrong.get("status") != "fail":
            report(
                f"{label}: a claim that task 1.1 covers F2 was accepted while "
                f"1.1's Covers names only F1; change-close returned "
                f"Status: {wrong.get('status')}."
            )
            return 1
        text = problem_text(wrong)
        if "E1" not in text:
            report(f"{label}: the refusal does not name the entry; {text!r}.")
            return 1
        if "F2" not in text:
            report(
                f"{label}: the refusal does not name the identifier it could "
                f"not find; {text!r}."
            )
            return 1
        if "2.1" not in text:
            report(
                f"{label}: the refusal does not name the task whose Covers "
                f"does hold F2, so the author is told the claim is wrong and "
                f"must re-derive which of three shapes it is; {text!r}."
            )
            return 1

        nowhere = close(fixture(root, "orphan", orphan))
        if nowhere.get("status") != "fail":
            report(
                f"{label}: a claim naming an identifier no task covers was "
                f"accepted; change-close returned Status: {nowhere.get('status')}."
            )
            return 1
        text = problem_text(nowhere)
        if "D1" not in text:
            report(
                f"{label}: the refusal does not name the uncovered identifier; "
                f"{text!r}."
            )
            return 1
        # The distinction is which of the two halves the refusal chose, not
        # whether a task id appears at all — the entry's own claim names one.
        if "is covered by task" in text:
            report(
                f"{label}: the refusal points at a task as the place D1 is "
                f"covered, which sends the author to a capsule with nothing "
                f"wrong in it; {text!r}."
            )
            return 1
        if "No task of this change covers" not in text:
            report(
                f"{label}: the refusal does not say that no task covers it, so "
                f"the shape issue #133 measured as the serious one is not told "
                f"apart from a wrong task id; {text!r}."
            )
            return 1

        # Citing is optional, and the fixture proving it is the mismatch with
        # its one citation removed — so a rule that refused prose would have to
        # refuse this and nothing else about it changed.
        quiet = close(fixture(root, "prose", prose))
        if quiet.get("status") != "pass":
            report(
                f"{label}: an entry citing no identifier was refused; "
                f"{problem_text(quiet)!r}."
            )
            return 1
        # Issue #239: the warning names the identifiers that make an entry
        # compared, so a reader can tell how to make it count.
        if "D<n>, F<n>, A<n>, or Q<n>" not in said(quiet):
            report(
                f"{label}: the uncompared-entry warning does not name the "
                f"identifiers that count; {said(quiet)!r}."
            )
            return 1

        # D3: the report's second suggestion is unnecessary, because the
        # comparison already refuses the case it was aimed at.
        both = close(fixture(root, "contradiction", contradiction))
        if both.get("status") != "fail":
            report(
                f"{label}: the same identifier claimed covered by a task that "
                f"omits it and deferred to a tracker was accepted; "
                f"change-close returned Status: {both.get('status')}."
            )
            return 1
        text = problem_text(both)
        if "F2" not in text:
            report(
                f"{label}: the contradiction was refused for something other "
                f"than the identifier it is about; {text!r}."
            )
            return 1

        # How far the comparison reached, read off the control run above.
        spoken = said(settled)
        if "Expectation Coverage" not in spoken:
            report(
                f"{label}: the close does not report how much of the section "
                f"it compared, so a pass reads as a warrant it does not carry; "
                f"{spoken!r}."
            )
            return 1
        if "2" not in spoken:
            report(
                f"{label}: the report does not carry the compared count; "
                f"{spoken!r}."
            )
            return 1
        if "0" not in spoken:
            report(
                f"{label}: the report is suppressed when every entry was "
                f"compared, which teaches a reader that its absence means full "
                f"coverage; {spoken!r}."
            )
            return 1

    report(f"{label} scenario passed.")
    return 0


def validate_reference_outlives_its_declaration_scenario() -> int:
    label = "a-reference-outlives-its-declaration"

    def complete(root: Path, name: str, checks, findings, form="Verify"):
        repo = root / name
        task = strategy_probe_task(
            strategy="evidence-first",
            reason="fixture; nothing here can fail first",
            form=form,
            commands=checks,
        )
        task = task.replace("- [ ] 1.1", "- [x] 1.1")
        task = task.replace("      - Findings: none", f"      - Findings: {findings}")
        for entry in checks:
            lbl = entry.split(":", 1)[0].split(" ")[0]
            task = task.replace(f"    - {lbl}: pending", f"    - {lbl}: pass. ran it.")
        write_gate_fixture(repo, tasks=task)
        started = run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
            "--json", "--no-guard",
        )
        payload = json.loads(started.stdout)
        value = ((payload.get("contract") or {}).get("fingerprint") or {}).get(
            "value"
        ) or "0" * 64
        tasks_path = repo / "openspec/changes/demo/tasks.md"
        tasks_path.write_text(
            tasks_path.read_text(encoding="utf-8").replace(
                "    - Contract: pending",
                f"    - Contract: keel-task-capsule/v1 sha256:{value}",
            ),
            encoding="utf-8",
        )
        result = run_keel(
            repo, "gate", "task-complete", "--change", "demo", "--task", "1.1",
            "--json",
        )
        return json.loads(result.stdout)

    slotted = (
        "M1: the first check asserts the public behavior",
        "M2: the second check runs make sta RUN=<experiment_id> and succeeds",
    )
    clean = (
        "M1: the first check asserts the public behavior",
        "M2: the second check runs the suite and succeeds",
    )

    with tempfile.TemporaryDirectory(prefix="keel-reference-") as raw:
        root = Path(raw)

        reported = complete(root, "slotted", slotted, "one. Resolved here: M2")
        text = problem_text(reported)
        if "<experiment_id>" not in text:
            report(
                f"{label}: the unfilled slot is no longer reported; {text!r}."
            )
            return 1
        if "not a check this task declares" in text:
            report(
                f"{label}: a reference to M2 was reported as undeclared because "
                f"M2's own declaration failed to compile; {text!r}."
            )
            return 1

        settled = complete(root, "clean", clean, "one. Resolved here: M2")
        if settled.get("status") != "pass":
            report(
                f"{label}: the same task without the slot no longer passes; "
                f"{problem_text(settled)!r}."
            )
            return 1

        # The set narrowed to the truth, not to everything.
        absent = complete(root, "absent", clean, "one. Resolved here: M9")
        if "not a check this task declares" not in problem_text(absent):
            report(
                f"{label}: a reference to a check the task never declared was "
                f"accepted; {problem_text(absent)!r}."
            )
            return 1

        legacy = complete(
            root, "legacy", clean, "one. Resolved here: M2", form="Commands"
        )
        if legacy.get("status") != "pass":
            report(
                f"{label}: an expanded v3 task lost its declared labels; "
                f"{problem_text(legacy)!r}."
            )
            return 1

    report(f"{label} scenario passed.")
    return 0


# The red-green obligation is a static function of the strategy and the tags,
# and the `Verify` block is complete at task-start while the Evidence is all
# pending. Issue #112 hit it three times, this repository twice more: the rule
# was first heard after the capsule was written, the task implemented, the
# checks run, and the Evidence recorded.
def validate_obligation_is_stated_early_scenario() -> int:
    label = "the-obligation-is-stated-early"

    def start(root: Path, name: str, strategy: str, reason=None, checks=None):
        repo = root / name
        write_gate_fixture(
            repo,
            tasks=strategy_probe_task(
                strategy=strategy,
                reason=reason,
                commands=checks
                or (
                    "M1: the first check asserts the public behavior",
                    "M2 (regression): the second asserts something green stays green",
                ),
            ),
        )
        result = run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
            "--json", "--no-guard",
        )
        return json.loads(result.stdout)

    with tempfile.TemporaryDirectory(prefix="keel-obligation-") as raw:
        root = Path(raw)

        redgreen = start(root, "redgreen", "vertical-tdd")
        if redgreen.get("status") != "pass":
            report(
                f"{label}: stating the obligation changed the verdict; "
                f"{problem_text(redgreen)!r}."
            )
            return 1
        warnings = " ".join(str(x) for x in (redgreen.get("warnings") or []))
        if ".red" not in warnings or ".green" not in warnings:
            report(
                f"{label}: task-start did not state the red-green obligation; "
                f"{warnings!r}."
            )
            return 1
        obligation = next(
            (w for w in redgreen["warnings"] if ".red" in str(w)), ""
        )
        if "M1" not in obligation:
            report(
                f"{label}: the obligation does not name the check that owes it; "
                f"{obligation!r}."
            )
            return 1
        if "M2" not in obligation or "regression" not in obligation:
            report(
                f"{label}: the obligation does not name the exempt check; "
                f"{obligation!r}."
            )
            return 1

        quiet = start(
            root,
            "quiet",
            "evidence-first",
            reason="fixture; nothing here can fail first",
        )
        quiet_warnings = " ".join(str(x) for x in (quiet.get("warnings") or []))
        if ".red" in quiet_warnings:
            report(
                f"{label}: a strategy without red-green was told about it; "
                f"{quiet_warnings!r}."
            )
            return 1

        # A task that fails task-start for another reason still fails with its
        # own problem: the warning is not a verdict and cannot mask one.
        broken = start(root, "broken", "made-up-thing")
        if broken.get("status") != "fail":
            report(f"{label}: an unsupported strategy stopped failing.")
            return 1
        if "unsupported" not in problem_text(broken):
            report(
                f"{label}: an unsupported strategy lost its own diagnostic; "
                f"{problem_text(broken)!r}."
            )
            return 1

    report(f"{label} scenario passed.")
    return 0


# Measured on issue #112's own shape: a two-check vertical-tdd task with no
# red-green Evidence produced four problems in 827 characters, of which the
# same 84-character rule sentence was four copies. It scales with the number
# of checks, and the reporter estimates a third of failure output is this.
def validate_explanation_is_printed_once_scenario() -> int:
    label = "an-explanation-is-printed-once"
    shared = "Tag the check `(regression)` if it asserts that something already green stays green."
    with tempfile.TemporaryDirectory(prefix="keel-explanation-") as raw:
        root = Path(raw)
        repo = root / "repo"
        task = strategy_probe_task(
            strategy="vertical-tdd",
            commands=(
                "M1: the first check asserts the public behavior",
                "M2: the second check asserts the public behavior",
            ),
        )
        task = task.replace("- [ ] 1.1", "- [x] 1.1")
        for lbl in ("M1", "M2"):
            task = task.replace(f"    - {lbl}: pending", f"    - {lbl}: pass. ran it.")
        write_gate_fixture(repo, tasks=task)
        started = run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
            "--json", "--no-guard",
        )
        value = json.loads(started.stdout)["contract"]["fingerprint"]["value"]
        tasks_path = repo / "openspec/changes/demo/tasks.md"
        tasks_path.write_text(
            tasks_path.read_text(encoding="utf-8").replace(
                "    - Contract: pending",
                f"    - Contract: keel-task-capsule/v1 sha256:{value}",
            ),
            encoding="utf-8",
        )

        rendered = run_keel(
            repo, "gate", "task-complete", "--change", "demo", "--task", "1.1"
        ).stdout
        copies = rendered.count(shared)
        if copies != 1:
            report(
                f"{label}: the shared rule explanation appears {copies} times "
                "in the rendered text; it belongs once per run."
            )
            return 1
        problems = [
            line for line in rendered.splitlines() if line.startswith("Problem:")
        ]
        if len(problems) != 4:
            report(
                f"{label}: expected the four per-label problems, got "
                f"{len(problems)}: {problems!r}."
            )
            return 1
        for needed in ("M1.red", "M1.green", "M2.red", "M2.green"):
            if not any(needed in line for line in problems):
                report(
                    f"{label}: {needed} lost its own problem line; {problems!r}."
                )
                return 1
        if len(rendered) >= 827:
            report(
                f"{label}: the rendered failure is {len(rendered)} characters, "
                "no shorter than the 827 measured before deduplication."
            )
            return 1

        payload = json.loads(
            run_keel(
                repo, "gate", "task-complete", "--change", "demo", "--task",
                "1.1", "--json",
            ).stdout
        )
        carried = [
            entry for entry in (payload.get("problems") or [])
            if entry.get("code") == "missing-strategy-evidence"
        ]
        if len(carried) != 4:
            report(
                f"{label}: the JSON result no longer carries all four problems; "
                f"{len(carried)}."
            )
            return 1
        if not all(shared in json.dumps(entry, ensure_ascii=False) for entry in carried):
            report(
                f"{label}: the JSON result was deduplicated; a consumer reading "
                "problems individually would get a payload whose content "
                "depends on position."
            )
            return 1

    report(f"{label} scenario passed.")
    return 0


# Issue #112's most valuable finding: a change its owner had stopped kept being
# recommended, and the workaround was a paragraph in the project's CLAUDE.md
# telling future sessions to ignore keel's own primary output.
def validate_paused_change_is_not_the_next_action_scenario() -> int:
    label = "a-paused-change-is-not-the-next-action"

    def write_change(repo: Path, name: str, keel_block: str | None) -> None:
        task = strategy_probe_task(strategy="vertical-tdd")
        change = repo / "openspec" / "changes" / name
        write_text(
            change / "tasks.md",
            "# Tasks\n\n## Invalidates\n\n- None.\n\n## Expectation Coverage\n\n"
            "- E1:\n  - Covered by: 1.1\n\n## Tasks\n\n" + task,
        )
        write_text(change / "proposal.md", "# Proposal\n")
        write_text(change / "design.md", "## Context\n\nfixture\n")
        write_text(change / "specs/demo/spec.md", "## ADDED Requirements\n")
        write_text(
            change / ".openspec.yaml",
            "schema: keel-spec-driven\ncreated: 2026-09-08\n"
            + (keel_block or ""),
        )

    paused_block = (
        "keel:\n"
        "  status: paused\n"
        "  reason: 打分寻优要等赛题，当前优先级是不依赖工具的知识沉淀\n"
        "  since: 2026-09-05\n"
    )

    def context(repo: Path, *args):
        result = run_keel(repo, "context", "--json", *args)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"status": "unparsed", "reasons": [result.stdout[:300]]}

    def said(payload: dict) -> str:
        return " ".join(
            str(x) for x in
            (payload.get("reasons") or []) + (payload.get("warnings") or [])
        )

    with tempfile.TemporaryDirectory(prefix="keel-paused-") as raw:
        root = Path(raw)

        # Without the declaration the pair is ambiguous, so the skip is what
        # changes the answer rather than the fixture shape.
        both = root / "both"
        write_change(both, "alpha", None)
        write_change(both, "beta", None)
        if context(both).get("status") != "ambiguous":
            report(
                f"{label}: two unpaused changes were not ambiguous, so the "
                "fixture does not isolate what pausing changes."
            )
            return 1

        mixed = root / "mixed"
        write_change(mixed, "alpha", paused_block)
        write_change(mixed, "beta", None)
        picked = context(mixed)
        if picked.get("status") != "ready":
            report(
                f"{label}: inference did not pass over the paused change; "
                f"{picked.get('status')!r} {said(picked)!r}."
            )
            return 1
        if (picked.get("selection") or {}).get("change") != "beta":
            report(
                f"{label}: inference selected {picked.get('selection')!r} "
                "rather than the change that is not paused."
            )
            return 1
        spoken = said(picked)
        if "alpha" not in spoken or "打分寻优" not in spoken:
            report(
                f"{label}: the paused change was skipped silently or without "
                f"its reason; {spoken!r}."
            )
            return 1

        allpaused = root / "allpaused"
        write_change(allpaused, "alpha", paused_block)
        write_change(allpaused, "beta", paused_block)
        idle = context(allpaused)
        if idle.get("status") != "idle":
            report(
                f"{label}: a repository whose every change is paused reported "
                f"{idle.get('status')!r}."
            )
            return 1
        spoken = said(idle)
        for needed in ("alpha", "beta", "打分寻优"):
            if needed not in spoken:
                report(
                    f"{label}: the all-paused report omits {needed!r}; "
                    f"{spoken!r}."
                )
                return 1

        explicit = context(mixed, "--change", "alpha")
        if (explicit.get("selection") or {}).get("change") != "alpha":
            report(
                f"{label}: explicit selection no longer reaches a paused "
                f"change; {explicit.get('status')!r} {said(explicit)!r}."
            )
            return 1
        if "paused" not in said(explicit).lower():
            report(
                f"{label}: explicit selection did not report that the change "
                f"is paused; {said(explicit)!r}."
            )
            return 1

        # D6: a declaration Keel cannot read pauses nothing.
        broken = root / "broken"
        write_change(broken, "alpha", "keel:\n  status: perhaps-later\n")
        write_change(broken, "beta", None)
        unreadable = context(broken)
        if unreadable.get("status") != "ambiguous":
            report(
                f"{label}: an unreadable declaration removed a change from "
                f"inference; {unreadable.get('status')!r} {said(unreadable)!r}."
            )
            return 1
        if "perhaps-later" not in said(unreadable):
            report(
                f"{label}: an unreadable declaration was not reported; "
                f"{said(unreadable)!r}."
            )
            return 1

        # D4: pausing is not a gate.
        gated = run_keel(
            mixed, "gate", "task-start", "--change", "alpha", "--task", "1.1",
            "--json", "--no-guard",
        )
        ungated = run_keel(
            both, "gate", "task-start", "--change", "alpha", "--task", "1.1",
            "--json", "--no-guard",
        )
        if json.loads(gated.stdout).get("status") != json.loads(
            ungated.stdout
        ).get("status"):
            report(
                f"{label}: pausing changed a gate verdict — paused "
                f"{json.loads(gated.stdout).get('status')!r} against unpaused "
                f"{json.loads(ungated.stdout).get('status')!r}."
            )
            return 1

    report(f"{label} scenario passed.")
    return 0


# Issue #112 recorded four re-verifications in one session from contract
# changes that could not affect evidence — renaming `M2:` to `M2 (regression):`
# among them, with the assertion unchanged by a character. One of the four meant
# breaking a testbench, re-running, and restoring it. The gate genuinely cannot
# judge which evidence survives; what it could do is stop saying "all of it".
def validate_evidence_survives_what_did_not_change_scenario() -> int:
    label = "evidence-survives-what-did-not-change"

    def fixture(root: Path, name: str, strategy: str = "evidence-first") -> Path:
        repo = root / name
        task = strategy_probe_task(
            strategy=strategy,
            reason="fixture; nothing here can fail first",
            commands=(
                "M1: the first check asserts the public behavior",
                "M2: the second check asserts the public behavior",
                "M3: the third check asserts the public behavior",
            ),
        )
        # A recorded anchor that is not the compiled one, so --record re-records.
        task = task.replace(
            "    - Contract: pending",
            "    - Contract: keel-task-capsule/v1 sha256:" + "0" * 64,
        )
        write_gate_fixture(repo, tasks=task)
        return repo

    def start(repo: Path, *args):
        result = run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
            "--json", "--no-guard", *args,
        )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"status": "unparsed", "problems": [{"message": result.stdout[:300]}]}

    def said(payload: dict) -> str:
        return " ".join(str(x) for x in (payload.get("warnings") or []))

    with tempfile.TemporaryDirectory(prefix="keel-keep-evidence-") as raw:
        root = Path(raw)

        # Control: without a declaration the report covers every check.
        blanket = start(fixture(root, "blanket"), "--record")
        if blanket.get("status") != "pass":
            report(
                f"{label}: the re-record fixture did not pass; "
                f"{problem_text(blanket)!r}."
            )
            return 1
        if "stale" not in said(blanket):
            report(
                f"{label}: the fixture did not produce a stale-evidence "
                f"report to narrow; {said(blanket)!r}."
            )
            return 1

        narrowed = start(
            fixture(root, "narrowed"), "--record", "--keep-evidence", "M1,M3"
        )
        if narrowed.get("status") != "pass":
            report(
                f"{label}: a declaration refused a valid re-record; "
                f"{problem_text(narrowed)!r}."
            )
            return 1
        spoken = said(narrowed)
        stale_line = next(
            (w for w in narrowed["warnings"] if "stale" in str(w)), ""
        )
        if "M2" not in stale_line:
            report(
                f"{label}: the narrowed report does not name the check that is "
                f"still stale; {stale_line!r}."
            )
            return 1
        for kept in ("M1", "M3"):
            if kept not in stale_line:
                report(
                    f"{label}: the narrowed report does not name {kept} as "
                    f"declared unaffected; {stale_line!r}."
                )
                return 1
        if "declar" not in stale_line.lower():
            report(
                f"{label}: the narrowed report does not attribute the "
                f"narrowing to the declaration; {stale_line!r}."
            )
            return 1

        unknown = start(
            fixture(root, "unknown"), "--record", "--keep-evidence", "M9"
        )
        if unknown.get("status") != "fail":
            report(
                f"{label}: a declaration naming a check the contract does not "
                "declare was accepted; task-start returned "
                f"{unknown.get('status')!r}."
            )
            return 1
        if "M9" not in problem_text(unknown):
            report(
                f"{label}: the refusal does not name the label it could not "
                f"resolve; {problem_text(unknown)!r}."
            )
            return 1

        stray = start(fixture(root, "stray"), "--keep-evidence", "M1")
        if stray.get("status") != "fail":
            report(
                f"{label}: --keep-evidence without --record was accepted, so "
                "an author could believe they declared something nothing read."
            )
            return 1

        # Completion is unchanged: the declaration is about the past.
        completing = fixture(root, "completing", strategy="vertical-tdd")
        start(completing, "--record", "--keep-evidence", "M1,M2,M3")
        tasks_path = completing / "openspec/changes/demo/tasks.md"
        tasks_path.write_text(
            tasks_path.read_text(encoding="utf-8")
            .replace("- [ ] 1.1", "- [x] 1.1")
            .replace("    - M1: pending", "    - M1: pass. ran it.")
            .replace("    - M2: pending", "    - M2: pass. ran it.")
            .replace("    - M3: pending", "    - M3: pass. ran it."),
            encoding="utf-8",
        )
        done = json.loads(
            run_keel(
                completing, "gate", "task-complete", "--change", "demo",
                "--task", "1.1", "--json",
            ).stdout
        )
        if done.get("status") != "fail":
            report(
                f"{label}: a declaration let a red-green task complete without "
                "its .red/.green Evidence."
            )
            return 1
        if "missing-strategy-evidence" not in problem_codes(done):
            report(
                f"{label}: completion stopped requiring red-green Evidence; "
                f"{problem_codes(done)!r}."
            )
            return 1

    report(f"{label} scenario passed.")
    return 0


# 5.55.0 built the way out of a blanket "all of it is stale" and signed it
# nowhere a reader would look: issue #134 grepped the installed package and
# found `--keep-evidence` only in its own two refusals, so the population told
# it exists is exactly the population already using it. One use in 67 task
# capsules, against a median re-verification of 256 s. Every exit that tells an
# author their evidence is stale now names it — and none of them names which
# checks it would apply to, because the gate keeps only the previous
# fingerprint and cannot know.
def validate_staleness_report_names_its_exception_scenario() -> int:
    label = "a-staleness-report-names-its-exception"
    flag = "--keep-evidence"

    def fixture(root: Path, name: str) -> Path:
        repo = root / name
        task = strategy_probe_task(
            strategy="evidence-first",
            reason="fixture; nothing here can fail first",
            commands=(
                "M1: the first check asserts the public behavior",
                "M2: the second check asserts the public behavior",
                "M3: the third check asserts the public behavior",
            ),
        )
        # A recorded anchor that is not the compiled one, so every exit fires.
        task = task.replace(
            "    - Contract: pending",
            "    - Contract: keel-task-capsule/v1 sha256:" + "0" * 64,
        )
        write_gate_fixture(repo, tasks=task)
        return repo

    def keel_json(repo: Path, *args) -> dict:
        result = run_keel(repo, *args)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"status": "unparsed", "problems": [
                {"code": "unparsed", "message": result.stdout[:300]}
            ]}

    def message_for(payload: dict, code: str) -> str:
        for entry in payload.get("problems") or []:
            if str(entry.get("code", "")) == code:
                return str(entry.get("message", ""))
        return ""

    # The suggestion has to carry the flag's own contract, not just its name:
    # when it applies, and that the claim is the author's to defend.
    def states_the_condition(text: str) -> bool:
        return "assertion" in text.lower()

    def sends_the_reason_home(text: str) -> bool:
        return "Reauthorizations" in text

    def names_a_check(text: str) -> str:
        return next((m for m in ("M1", "M2", "M3") if m in text), "")

    with tempfile.TemporaryDirectory(prefix="keel-names-exception-") as raw:
        root = Path(raw)

        # Exit 1 of 3 — `task-start --record` with no declaration. This is the
        # branch issue #134 names, and the only one whose reader is mid-record.
        blanket = keel_json(
            fixture(root, "blanket"), "gate", "task-start", "--change", "demo",
            "--task", "1.1", "--json", "--no-guard", "--record",
        )
        if blanket.get("status") != "pass":
            report(
                f"{label}: the re-record fixture did not pass, so no "
                f"stale-evidence report was produced; {problem_text(blanket)!r}."
            )
            return 1
        warned = " ".join(str(x) for x in (blanket.get("warnings") or []))
        if flag not in warned:
            report(
                f"{label}: the blanket stale-evidence report does not name "
                f"{flag}, so an author who has not already used it re-verifies "
                f"everything; {warned!r}."
            )
            return 1
        if not states_the_condition(warned):
            report(
                f"{label}: the blanket report names {flag} without saying when "
                f"it applies — that the check's assertion did not move; "
                f"{warned!r}."
            )
            return 1
        if not sends_the_reason_home(warned):
            report(
                f"{label}: the blanket report names {flag} without saying the "
                f"reason belongs in Reauthorizations, where it can be "
                f"disagreed with; {warned!r}."
            )
            return 1
        named = names_a_check(warned)
        if named:
            report(
                f"{label}: the blanket report names {named} while suggesting "
                f"{flag}. The gate keeps only the previous fingerprint and "
                f"cannot know which checks are unaffected; {warned!r}."
            )
            return 1

        # Exit 2 of 3 — `task-complete`'s contract-drift refusal, which already
        # prints the command the flag belongs to.
        completing = fixture(root, "completing")
        done = keel_json(
            completing, "gate", "task-complete", "--change", "demo",
            "--task", "1.1", "--json",
        )
        drift = message_for(done, "contract-drift")
        if not drift:
            report(
                f"{label}: the drifted fixture did not produce a "
                f"contract-drift refusal; {problem_codes(done)!r}."
            )
            return 1
        if "keel gate task-start --record" not in drift:
            report(
                f"{label}: the contract-drift refusal stopped naming the "
                f"reauthorization command, which is what makes the flag "
                f"belong in it; {drift!r}."
            )
            return 1
        if flag not in drift:
            report(
                f"{label}: the contract-drift refusal does not name {flag} "
                f"even though it names the command that accepts it; {drift!r}."
            )
            return 1
        if not states_the_condition(drift):
            report(
                f"{label}: the contract-drift refusal names {flag} without "
                f"saying when it applies; {drift!r}."
            )
            return 1
        named = names_a_check(drift)
        if named:
            report(
                f"{label}: the contract-drift refusal names {named} while "
                f"suggesting {flag}; {drift!r}."
            )
            return 1

        # Exit 3 of 3 — the context drift hard-stop, which already says to
        # re-run task-start and record the new anchor.
        blocked = keel_json(fixture(root, "blocked"), "context", "--json")
        reasons = " ".join(str(x) for x in (blocked.get("reasons") or []))
        if blocked.get("status") != "blocked":
            report(
                f"{label}: the drifted fixture did not block context, so the "
                f"drift hard-stop did not fire; {blocked.get('status')!r}."
            )
            return 1
        if "drift" not in reasons.lower():
            report(
                f"{label}: context blocked for something other than the "
                f"contract drift this fixture builds; {reasons!r}."
            )
            return 1
        if flag not in reasons:
            report(
                f"{label}: the context drift hard-stop does not name {flag} "
                f"even though it tells the reader to re-record the anchor; "
                f"{reasons!r}."
            )
            return 1
        if not states_the_condition(reasons):
            report(
                f"{label}: the context drift hard-stop names {flag} without "
                f"saying when it applies; {reasons!r}."
            )
            return 1
        named = names_a_check(reasons)
        if named:
            report(
                f"{label}: the context drift hard-stop names {named} while "
                f"suggesting {flag}; {reasons!r}."
            )
            return 1

        # The already-narrowed report does not repeat the suggestion. Absence
        # is also what a broken narrowing produces, so the positive control
        # runs first: the branch has to be alive before its silence means
        # anything.
        narrowed = keel_json(
            fixture(root, "narrowed"), "gate", "task-start", "--change", "demo",
            "--task", "1.1", "--json", "--no-guard", "--record",
            "--keep-evidence", "M1,M3",
        )
        narrowed_said = " ".join(str(x) for x in (narrowed.get("warnings") or []))
        if "declared unaffected" not in narrowed_said:
            report(
                f"{label}: the narrowed branch did not report a declaration, "
                f"so its silence about {flag} proves nothing; "
                f"{narrowed_said!r}."
            )
            return 1
        if flag in narrowed_said:
            report(
                f"{label}: the narrowed report suggests {flag} to a reader who "
                f"just used it; {narrowed_said!r}."
            )
            return 1

    report(f"{label} scenario passed.")
    return 0


# `keel context` exists to answer "what now" and answered with a noun. Issue
# #112: `Next action: change-close` followed by `keel gate change-close
# --change x` failing on the argument that stage requires — a wrong attempt
# Keel had everything in the same result to prevent.
def validate_next_action_is_a_command_scenario() -> int:
    label = "the-next-action-is-a-command"

    def repo_with(root: Path, name: str, *, checked: bool, evidence: bool):
        repo = root / name
        task = strategy_probe_task(
            strategy="evidence-first",
            reason="fixture; nothing here can fail first",
        )
        if checked:
            task = task.replace("- [ ] 1.1", "- [x] 1.1")
        if evidence:
            task = task.replace("    - M1: pending", "    - M1: pass. ran it.")
        write_gate_fixture(repo, tasks=task)
        started = run_keel(
            repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
            "--json", "--no-guard",
        )
        value = json.loads(started.stdout)["contract"]["fingerprint"]["value"]
        tasks_path = repo / "openspec/changes/demo/tasks.md"
        tasks_path.write_text(
            tasks_path.read_text(encoding="utf-8").replace(
                "    - Contract: pending",
                f"    - Contract: keel-task-capsule/v1 sha256:{value}",
            ),
            encoding="utf-8",
        )
        return repo

    def context(repo: Path):
        text = run_keel(repo, "context", "--change", "demo").stdout
        payload = json.loads(
            run_keel(repo, "context", "--change", "demo", "--json").stdout
        )
        return text, payload

    with tempfile.TemporaryDirectory(prefix="keel-next-command-") as raw:
        root = Path(raw)

        pending = repo_with(root, "pending", checked=False, evidence=False)
        text, payload = context(pending)
        command = (payload.get("nextAction") or {}).get("command")
        if not command:
            report(
                f"{label}: the next action carries no command; "
                f"{payload.get('nextAction')!r}."
            )
            return 1
        for needed in ("task-start", "--change demo", "--task 1.1"):
            if needed not in command:
                report(
                    f"{label}: the reported command omits {needed!r}; "
                    f"{command!r}."
                )
                return 1
        if command not in text:
            report(
                f"{label}: the text surface does not carry the same command as "
                f"--json; {command!r} not in {text!r}."
            )
            return 1

        done = repo_with(root, "done", checked=False, evidence=True)
        _, payload = context(done)
        if "task-complete" not in str((payload.get("nextAction") or {}).get("command")):
            report(
                f"{label}: a task with completion evidence did not report the "
                f"task-complete invocation; {payload.get('nextAction')!r}."
            )
            return 1

        closing = repo_with(root, "closing", checked=True, evidence=True)
        _, payload = context(closing)
        close_command = str((payload.get("nextAction") or {}).get("command") or "")
        if "change-close" not in close_command:
            report(
                f"{label}: a change whose tasks are complete did not report the "
                f"change-close invocation; {payload.get('nextAction')!r}."
            )
            return 1
        if "--action" not in close_command:
            report(
                f"{label}: the change-close command omits the argument that "
                f"stage requires; {close_command!r}."
            )
            return 1
        # Running exactly what was printed must not hit the input error the
        # report describes.
        printed = close_command.split()
        if printed and printed[0] == "keel":
            printed = printed[1:]
        ran = run_keel(closing, *printed)
        if "requires --action" in (ran.stdout + ran.stderr):
            report(
                f"{label}: the reported command still fails on the argument it "
                f"was supposed to supply; {(ran.stdout + ran.stderr)[:200]!r}."
            )
            return 1

        idle = root / "idle"
        write_text(idle / "README.md", "# fixture\n")
        payload = json.loads(run_keel(idle, "context", "--json").stdout)
        if (payload.get("nextAction") or {}).get("command"):
            report(
                f"{label}: an action with nothing to run reported a command; "
                f"{payload.get('nextAction')!r}."
            )
            return 1

    report(f"{label} scenario passed.")
    return 0


def validate_a_filter_drops_only_what_it_named_scenario() -> int:
    """Issue #137: a PATH built to exclude one tool removed a whole directory.

    Both scenarios that need "no openspec on PATH" dropped every directory that
    held an `openspec`. On the ordinary Homebrew plus `npm install -g` layout one
    directory holds `openspec` and `node`, so the filter took the interpreter the
    openspec shim needs, and the diagnostic named `openspec` — a tool that was
    installed and working.

    The defect is a layout, so the fixture builds the layout instead of relying on
    this host having it: a directory carrying both binaries, on a PATH between two
    that carry neither. Asserted from both sides — that the runtime survived is the
    regression guard, that the tool is gone is the positive control, because a
    mirror that produced an empty directory would satisfy the second alone.
    """
    label = "a-filter-drops-only-what-it-named"

    def write_executable(path: Path, body: str) -> None:
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    with tempfile.TemporaryDirectory(prefix="keel-shared-bin-") as raw:
        root = Path(raw)
        before = root / "before"
        shared = root / "shared"
        after = root / "after"
        for directory in (before, shared, after):
            directory.mkdir()
        write_executable(before / "tool-a", "#!/bin/sh\necho a\n")
        write_executable(after / "tool-b", "#!/bin/sh\necho b\n")
        # The layout under test: the interpreter and the tool in one directory,
        # plus a neighbour that belongs to neither and must survive with it.
        write_executable(shared / "node", "#!/bin/sh\necho node\n")
        write_executable(shared / "openspec", "#!/bin/sh\necho 1.12.0\n")
        write_executable(shared / "openspec.cmd", "#!/bin/sh\necho 1.12.0\n")
        write_executable(shared / "unrelated", "#!/bin/sh\necho unrelated\n")

        source = os.pathsep.join(str(entry) for entry in (before, shared, after))
        with path_without_openspec(source) as sanitized:
            entries = sanitized.split(os.pathsep)

            # Behavior before shape: what the defect destroys is the ability to
            # run the interpreter, and an entry count is only its symptom.
            node = shutil.which("node", path=sanitized)
            if node is None:
                report(
                    f"{label}: node did not survive a filter that was removing "
                    f"openspec. The interpreter shares a directory with the "
                    f"tool, and the whole directory went. sanitized PATH "
                    f"{sanitized!r}"
                )
                return 1
            if shutil.which("unrelated", path=sanitized) is None:
                report(
                    f"{label}: an executable unrelated to openspec was removed "
                    f"along with it."
                )
                return 1

            # The positive control. Without it, an empty mirror passes.
            for name in ("openspec", "openspec.cmd"):
                found = shutil.which(name, path=sanitized)
                if found is not None:
                    report(
                        f"{label}: {name} still resolves on a PATH built to "
                        f"exclude it, at {found!r}."
                    )
                    return 1

            if len(entries) != 3:
                report(
                    f"{label}: the sanitized PATH has {len(entries)} entries, "
                    f"not the 3 it was given, so search order did not survive. "
                    f"got {sanitized!r}"
                )
                return 1
            if Path(node).parent != Path(entries[1]):
                report(
                    f"{label}: node survived but moved search position; it "
                    f"resolved from {str(Path(node).parent)!r}, not from PATH "
                    f"entry 1 {entries[1]!r}."
                )
                return 1

            # M2: an entry that does not hold the tool is passed through, not
            # mirrored — the cost and the blast radius stay on the directories
            # that carry it.
            for index, original in ((0, before), (2, after)):
                if entries[index] != str(original):
                    report(
                        f"{label}: a PATH entry holding no openspec was "
                        f"rewritten; expected {str(original)!r}, got "
                        f"{entries[index]!r}."
                    )
                    return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_a_claim_names_what_would_falsify_it_scenario() -> int:
    """Issue #132: an honest red does not mean the check can catch the defect.

    A consistency check whose red was real, whose signature predicted it, and
    whose green was real stayed green through a 1000x unit error — the one thing
    it existed to catch — because `pytest.approx` carries a default absolute
    tolerance. `.red` proves the check failed before the implementation existed
    and `Fails with:` predicts the red of an *absent* feature; neither says
    anything about the red of a *broken* one. `Detects:` declares the injection
    that answers the third question, in the same shape: inside the check text, so
    it enters the fingerprint, and enforced by requiring its literal in Evidence.
    """
    label = "a-claim-names-what-would-falsify-it"
    mutation = "sed -i s/0.0005/0.5/ run_sta.py"
    failure = "assert 5e-16 == 5e-13"

    with tempfile.TemporaryDirectory(prefix="keel-detects-") as raw:
        root = Path(raw)

        def start(name: str, **kwargs) -> dict:
            return strategy_probe_start(root, name, strategy_probe_task(**kwargs))

        def commands_of(payload: dict) -> list[dict]:
            contract = payload.get("contract") or {}
            capsule = contract.get("capsule") or {}
            return ((capsule.get("verification") or {}).get("commands") or [])

        # M1 — two clauses on one check, both parsed. The failure signature comes
        # first, so this is also the assertion that a signature no longer has to
        # be the final clause.
        chained = (
            "M1: node test.js asserts the public behavior. "
            f"Fails with: `boom` Detects: `{mutation}` -> `{failure}`",
        )
        payload = start("chained", strategy="vertical-tdd", commands=chained)
        if payload.get("status") != "pass":
            report(
                f"{label}: Detects: is not parsed — a check carrying a failure "
                "signature followed by an injection clause was refused; got "
                f"{payload.get('status')!r} {problem_text(payload)!r}."
            )
            return 1
        compiled = commands_of(payload)
        if len(compiled) != 1:
            report(f"{label}: the chained check did not compile to one check; {compiled!r}")
            return 1
        entry = compiled[0]
        if entry.get("failsWith") != "boom":
            report(
                f"{label}: Detects: is not parsed — the failure signature was "
                f"lost when a clause followed it; got {entry!r}."
            )
            return 1
        detects = entry.get("detects") or {}
        if detects.get("mutation") != mutation or detects.get("failure") != failure:
            report(
                f"{label}: Detects: is not parsed — the compiled check does not "
                f"carry the declared injection; got {entry!r}."
            )
            return 1
        # The clause is inside the check text, so it is inside the fingerprint.
        # Without this, an injection edited after the run would be invisible.
        other = start(
            "chained-edited",
            strategy="vertical-tdd",
            commands=(
                "M1: node test.js asserts the public behavior. "
                f"Fails with: `boom` Detects: `{mutation}` -> `assert 1 == 2`",
            ),
        )
        first = str((payload.get("contract") or {}).get("fingerprint") or "")
        second = str((other.get("contract") or {}).get("fingerprint") or "")
        if not first or first == second:
            report(
                f"{label}: editing the declared injection did not move the "
                f"fingerprint; {first!r} vs {second!r}."
            )
            return 1

        # M1, second half — the declaration is enforced at completion, against a
        # `.detects` Evidence entry for the same check. The clause is a claim Keel
        # records: it never runs the mutation, so what completion holds is that
        # the declared failure appears in what the author recorded.
        def complete(name: str, detects_evidence: str | None) -> dict:
            repo = root / name
            evidence = [
                "    - Contract: pending",
                "    - M1: pass. node test.js reported the behavior.",
                "    - M1.red: fail. `boom` as predicted.",
                "    - M1.green: pass.",
            ]
            if detects_evidence is not None:
                evidence.append(f"    - M1.detects: {detects_evidence}")
            task = "\n".join(
                [
                    "- [x] 1.1 Injection probe",
                    "  - Owner: claude",
                    "  - Mode: implementation",
                    "  - Covers:",
                    "    - E1: the task proves its own behavior",
                    "  - Read:",
                    "    - README.md",
                    "  - Touch:",
                    "    - src/example.js",
                    "  - Verify:",
                    "    - Strategy: vertical-tdd",
                    "    - M1: node test.js asserts the public behavior. "
                    f"Fails with: `boom` Detects: `{mutation}` -> `{failure}`",
                    "  - Evidence:",
                    *evidence,
                    "    - Review:",
                    "      - Status: pass",
                    "      - Acceptance check: the behavior is proven.",
                    "      - Scope check: only Touch changed.",
                    "      - Findings: none.",
                    "    - Blocker: none",
                    "    - Reauthorizations: none",
                ]
            )
            write_gate_fixture(repo, tasks=task)
            started = run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
                "--record", "--json",
            )
            try:
                anchor_value = str(
                    (json.loads(started.stdout).get("contract") or {}).get(
                        "fingerprint"
                    )
                    or ""
                )
            except json.JSONDecodeError:
                anchor_value = ""
            if not anchor_value:
                return {"status": "unstarted", "problems": [{"message": started.stdout[:300]}]}
            done = run_keel(
                repo, "gate", "task-complete", "--change", "demo", "--task", "1.1",
                "--json",
            )
            try:
                return json.loads(done.stdout)
            except json.JSONDecodeError:
                return {"status": "unparsed", "problems": [{"message": done.stdout[:400]}]}

        absent = complete("no-detects", None)
        if absent.get("status") == "pass":
            report(
                f"{label}: Detects: is not enforced — a declared injection with "
                "no `.detects` Evidence completed cleanly."
            )
            return 1
        if "missing-injection-evidence" not in problem_codes(absent):
            report(
                f"{label}: Detects: is not enforced — an absent `.detects` was "
                f"refused under another diagnostic; {problem_codes(absent)!r} "
                f"{problem_text(absent)!r}."
            )
            return 1
        wrong = complete("wrong-detects", "ran the mutation; it still passed.")
        if wrong.get("status") == "pass":
            report(
                f"{label}: Detects: is not enforced — a `.detects` recording "
                "something other than the declared failure completed cleanly."
            )
            return 1
        if "injection-missing-declared-failure" not in problem_codes(wrong):
            report(
                f"{label}: a `.detects` lacking the declared failure was "
                f"refused under another diagnostic; {problem_codes(wrong)!r} "
                f"{problem_text(wrong)!r}."
            )
            return 1
        right = complete("good-detects", f"fail, as declared: `{failure}`.")
        if right.get("status") != "pass":
            report(
                f"{label}: a `.detects` carrying the declared failure was still "
                f"refused; {problem_codes(right)!r} {problem_text(right)!r}."
            )
            return 1

        # M2 — a (regression) check may declare one. It has no honest red by
        # construction and is exempt from .red/.green, so an injection is the
        # only mechanism that can show it is not vacuous: this is where the
        # clause is worth most, which is why the report's suggested refusal here
        # was narrowed rather than adopted.
        regression = start(
            "regression",
            strategy="vertical-tdd",
            commands=(
                "M1: node test.js asserts the new behavior. Fails with: `boom`",
                f"M2 (regression): node all.js stays green. Detects: `{mutation}` -> `{failure}`",
            ),
        )
        if regression.get("status") != "pass":
            report(
                f"{label}: regression check may not declare an injection; got "
                f"{regression.get('status')!r} {problem_text(regression)!r}."
            )
            return 1
        second_entry = next(
            (e for e in commands_of(regression) if e.get("label") == "M2"), {}
        )
        if not (second_entry.get("detects") or {}).get("failure"):
            report(
                f"{label}: regression check may not declare an injection — the "
                f"clause was dropped; got {second_entry!r}."
            )
            return 1

        # M3 — a malformed clause is named, not ignored. Both shapes: one literal
        # with no arrow, and an arrow with nothing after it.
        for name, clause in (
            ("one-literal", f"Detects: `{mutation}`"),
            ("no-target", f"Detects: `{mutation}` ->"),
        ):
            bad = start(
                name,
                strategy="vertical-tdd",
                commands=(f"M1: node test.js asserts the behavior. {clause}",),
            )
            if bad.get("status") == "pass":
                report(
                    f"{label}: a malformed injection clause ({name}) was "
                    "silently ignored, which leaves the author believing an "
                    "injection is enforced when none was parsed."
                )
                return 1
            if "malformed-injection" not in problem_codes(bad):
                report(
                    f"{label}: a malformed injection clause ({name}) was "
                    "silently ignored under another diagnostic; got "
                    f"{problem_codes(bad)!r} {problem_text(bad)!r}."
                )
                return 1
        # A marker inside inline code is quoted material, not a declaration —
        # which is what lets this repository's own tasks write about the clause.
        quoted = start(
            "quoted",
            strategy="vertical-tdd",
            commands=(
                "M1: node test.js asserts that a check may close with "
                "`Detects:` and two literals. Fails with: `boom`",
            ),
        )
        if quoted.get("status") != "pass":
            report(
                f"{label}: a clause named inside inline code was silently "
                f"ignored as a declaration; got {problem_text(quoted)!r}."
            )
            return 1

        # 1.2 — `Measured:` binds a literal to the check's own recorded output.
        # The failure class it answers is a number that reads like a measurement
        # and is an estimate or a recollection; the one instance of it that was
        # caught in the reporting session was caught exactly this way, by sitting
        # in a clause the gate held against recorded output.
        measured_literal = "1799.9"

        def complete_measured(name: str, m1_evidence: str, clause: str) -> dict:
            repo = root / name
            task = "\n".join(
                [
                    "- [x] 1.1 Measurement probe",
                    "  - Owner: claude",
                    "  - Mode: implementation",
                    "  - Covers:",
                    "    - E1: the task proves its own behavior",
                    "  - Read:",
                    "    - README.md",
                    "  - Touch:",
                    "    - src/example.js",
                    "  - Verify:",
                    "    - Strategy: vertical-tdd",
                    f"    - M1: node test.js reports the fanout load.{clause}",
                    "  - Evidence:",
                    "    - Contract: pending",
                    f"    - M1: {m1_evidence}",
                    "    - M1.red: fail. the reader did not exist.",
                    "    - M1.green: pass.",
                    "    - Review:",
                    "      - Status: pass",
                    "      - Acceptance check: the behavior is proven.",
                    "      - Scope check: only Touch changed.",
                    "      - Findings: none.",
                    "    - Blocker: none",
                    "    - Reauthorizations: none",
                ]
            )
            write_gate_fixture(repo, tasks=task)
            run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
                "--record", "--json",
            )
            done = run_keel(
                repo, "gate", "task-complete", "--change", "demo", "--task", "1.1",
                "--json",
            )
            try:
                return json.loads(done.stdout)
            except json.JSONDecodeError:
                return {"status": "unparsed", "problems": [{"message": done.stdout[:400]}]}

        estimated = complete_measured(
            "measured-absent",
            "pass. node test.js reported a fanout load of 1200 fF.",
            f" Measured: `{measured_literal}`",
        )
        if estimated.get("status") == "pass":
            report(
                f"{label}: Measured: is not enforced — a declared literal absent "
                "from the check's own recorded output completed cleanly, which is "
                "an estimate presented as a measurement."
            )
            return 1
        if "measurement-missing-from-evidence" not in problem_codes(estimated):
            report(
                f"{label}: a declared measurement absent from the output was "
                f"refused under another diagnostic; {problem_codes(estimated)!r} "
                f"{problem_text(estimated)!r}."
            )
            return 1
        real = complete_measured(
            "measured-present",
            f"pass. node test.js reported a fanout load of {measured_literal} fF.",
            f" Measured: `{measured_literal}`",
        )
        if real.get("status") != "pass":
            report(
                f"{label}: a declared measurement present in the output was "
                f"refused; {problem_codes(real)!r} {problem_text(real)!r}."
            )
            return 1
        # D4 — opt-in. A number in Evidence that no check declared is required
        # nowhere: the universal rule was declined on measurement, because in this
        # repository's own archive it would reach 847 inline-code spans, most of
        # them version strings, computed counts, and quoted references.
        undeclared = complete_measured(
            "measured-undeclared",
            "pass. node test.js reported `1200` fF across `2433` fanout pins.",
            "",
        )
        if undeclared.get("status") != "pass":
            report(
                f"{label}: numbers in Evidence with no `Measured:` clause were "
                f"refused, so the opt-in boundary did not hold; "
                f"{problem_codes(undeclared)!r} {problem_text(undeclared)!r}."
            )
            return 1

    # 1.3 — the clauses are documented where the first one is documented. A
    # vocabulary an author cannot discover is a vocabulary nobody declares.
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for needle, why in (
        ("Detects:", "the injection clause must be named"),
        ("Measured:", "the measurement clause must be named"),
    ):
        if needle not in readme:
            report(
                f"{label}: README does not name {needle} — {why}, and a clause "
                "an author cannot find is a clause nobody declares."
            )
            return 1
        if needle not in agents:
            report(
                f"{label}: the protocol's verification discipline does not name "
                f"{needle} — {why}."
            )
            return 1
    flat_readme = re.sub(r"\s+", " ", readme)
    for needle, why in (
        ("records the claim", "the README must say Keel does not judge the injection"),
        ("does not run", "the README must say Keel does not run the mutation"),
    ):
        if needle not in flat_readme:
            report(f"{label}: README does not name Detects: honestly — {why}.")
            return 1
    # The chaining is taught by the example rather than by prose about it: a
    # reader copies the example, and an example showing one clause teaches that
    # one clause is all there is.
    chained_example = re.search(
        r"Fails with: `[^`]+` Detects: `[^`]+` -> `[^`]+`", readme
    )
    if not chained_example:
        report(
            f"{label}: README does not name Detects: in a worked example beside "
            "a failure signature, so a reader learns the clauses are mutually "
            "exclusive from the only example they have."
        )
        return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_archive_keeps_tracked_evidence_scenario() -> int:
    """Issue #352: archiving a change whose own .gitignore ignores tracked
    evidence dropped that evidence from version control.

    The archive is a filesystem move; tracked files survive an ignore rule
    only at the path they were added at, so at the archived path they read as
    deleted-and-ignored and the archive commit removed them.
    `keel openspec archive` re-adds them, and `change-close --action archive`
    warns about them before any move.
    """
    label = "archive-keeps-tracked-evidence:"
    with tempfile.TemporaryDirectory(prefix="keel-archive-352-") as raw:
        tmp = Path(raw)
        repo = tmp / "repo"
        repo.mkdir()

        def git(*args: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=False)

        git("init", "-q")
        git("config", "user.email", "t@example.com")
        git("config", "user.name", "t")
        env = dict(os.environ)
        env["CODEX_HOME"] = str(tmp / "codex-home")
        init = run_keel(repo, "--init", "--target", "claude", env=env)
        if init.returncode:
            report(f"{label} init failed: {init.stderr or init.stdout}")
            return 1
        change = repo / "openspec/changes/demo"
        write_text(change / "proposal.md", "## Why\n\nfixture\n\n## What Changes\n\n- fixture\n")
        write_text(change / "tasks.md", "# Tasks\n\n- [x] 1.1 done\n")
        write_text(change / ".gitignore", "evidence/**\n")
        write_text(change / "evidence/run.log", "measured\n")
        git("add", "-A")
        git("add", "-f", "openspec/changes/demo/evidence/run.log")
        git("commit", "-q", "-m", "fixture")
        if "openspec/changes/demo/evidence/run.log" not in git("ls-files").stdout:
            report(f"{label} the fixture's evidence is not tracked.")
            return 1

        # The gate sees it before any move.
        closing = run_keel(repo, "gate", "change-close", "--change", "demo", "--action", "archive", "--json", env=env)
        try:
            warnings = json.loads(closing.stdout).get("warnings", [])
        except json.JSONDecodeError:
            report(f"{label} change-close printed no JSON: {closing.stdout!r} {closing.stderr!r}")
            return 1
        warned = next((w for w in warnings if "evidence/run.log" in w), "")
        if not warned:
            report(f"{label} change-close --action archive does not warn about tracked evidence the change ignores: {warnings!r}")
            return 1
        if "keel openspec archive" not in warned:
            report(f"{label} the warning does not name the archive that keeps it: {warned!r}")
            return 1

        archived = run_keel(repo, "openspec", "archive", "demo", "--yes", "--skip-specs", env=env)
        if archived.returncode:
            report(f"{label} keel openspec archive failed: {archived.stdout!r} {archived.stderr!r}")
            return 1
        moved = sorted((repo / "openspec/changes/archive").glob("*demo/evidence/run.log"))
        if len(moved) != 1:
            report(f"{label} the archive did not move the evidence: {sorted((repo / 'openspec/changes/archive').rglob('*'))!r}")
            return 1
        relative = moved[0].relative_to(repo).as_posix()
        if relative not in git("ls-files").stdout:
            report(f"{label} the archived evidence {relative} dropped out of version control: {archived.stdout!r}")
            return 1
        if "re-added 1" not in archived.stdout:
            report(f"{label} the archive does not say it re-added the tracked evidence: {archived.stdout!r}")
            return 1
    if "archive-keeps-tracked-evidence" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("archive-keeps-tracked-evidence scenario passed.")
    return 0


def validate_a_listed_marker_opens_its_clause_scenario() -> int:
    """Issue #362: a disposition written as a sub-list item was read as prose.

    A `Findings` value whose marker sits on its own `- ` line under the label
    reached the marker scan as a line break, indentation and `- `; the opening
    rule allowed only indentation after a break, so `Resolved here: M1` read as
    a mid-sentence mention and the entry was refused `finding-owner`, while the
    same text on the label's own line passed.
    """
    label = "a-listed-marker-opens-its-clause"

    def findings_task(findings: list[str]) -> str:
        return "\n".join(
            [
                "- [x] 1.1 Findings probe",
                "  - Owner: claude",
                "  - Mode: implementation",
                "  - Covers:",
                "    - E1: the task proves its own behavior",
                "  - Read:",
                "    - README.md",
                "  - Touch:",
                "    - src/example.js",
                "  - Verify:",
                "    - Strategy: vertical-tdd",
                "    - M1: node test.js asserts the public behavior",
                "  - Evidence:",
                "    - Contract: pending",
                "    - M1: pass. node test.js reported the behavior.",
                "    - M1.red: fail. the behavior did not exist.",
                "    - M1.green: pass.",
                "    - Review:",
                "      - Status: pass",
                "      - Acceptance check: the behavior is proven.",
                "      - Scope check: only Touch changed.",
                "      - Findings:",
                *[f"        - {item}" for item in findings],
                "    - Blocker: none",
                "    - Reauthorizations: none",
            ]
        )

    with tempfile.TemporaryDirectory(prefix="keel-listed-marker-") as raw:
        root = Path(raw)

        def complete(name: str, *findings: str) -> dict:
            repo = root / name
            write_gate_fixture(repo, tasks=findings_task(list(findings)))
            write_text(repo / "flow/Makefile", "all:\n")
            run_keel(repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--record", "--json")
            done = run_keel(repo, "gate", "task-complete", "--change", "demo", "--task", "1.1", "--json")
            try:
                return json.loads(done.stdout)
            except json.JSONDecodeError:
                return {"status": "unparsed", "problems": [{"message": done.stdout[:400]}]}

        # The forms #362 reported refused, each as a sub-list item.
        for name, items in (
            ("check", ["Resolved here: M1"]),
            ("path", ["Resolved here: flow/Makefile"]),
            ("path-then-cjk-sentence", ["Resolved here: flow/Makefile。规则已改为按点名运行。"]),
            ("two-items", ["Resolved here: M1", "Discard reason: out of scope."]),
        ):
            payload = complete(name, *items)
            if payload.get("status") != "pass":
                report(f"{label}: a sub-list {items!r} is not read as a disposition ({name}); "
                       f"{problem_codes(payload)!r} {problem_text(payload)!r}.")
                return 1

        # The control: a listed claim is held to the evidence rule, not waved through.
        payload = complete("unknown-check", "Resolved here: M9")
        if "M9" not in problem_text(payload):
            report(f"{label}: a sub-list `Resolved here: M9` naming an undeclared check was not refused "
                   f"for that check; {problem_codes(payload)!r} {problem_text(payload)!r}.")
            return 1

        # A negation on a listed line is still a negation (#144).
        payload = complete("negated", "Not resolved here: a different module. Durable owner: https://example.com/issues/1")
        if payload.get("status") != "pass":
            report(f"{label}: a listed negation was refused; "
                   f"{problem_codes(payload)!r} {problem_text(payload)!r}.")
            return 1

    if "a-listed-marker-opens-its-clause" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: scenario is not registered.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_a_negation_is_not_a_marker_scenario() -> int:
    """Issue #144: `Not resolved here:` was read as `Resolved here:`.

    The marker scan's `\\b` sits at the space inside the negation, so a finding
    that said in as many words it was *not* resolved here had the next word read
    as its resolution evidence — a dismissal read as a repair, then refused for
    lacking repair evidence. 5.42.0 established that a quoted marker is a
    quotation; a negated one is the same class and was not covered.
    """
    label = "a-negation-is-not-a-marker"

    def findings_task(findings: str) -> str:
        return "\n".join(
            [
                "- [x] 1.1 Findings probe",
                "  - Owner: claude",
                "  - Mode: implementation",
                "  - Covers:",
                "    - E1: the task proves its own behavior",
                "  - Read:",
                "    - README.md",
                "  - Touch:",
                "    - src/example.js",
                "  - Verify:",
                "    - Strategy: vertical-tdd",
                "    - M1: node test.js asserts the public behavior",
                "  - Evidence:",
                "    - Contract: pending",
                "    - M1: pass. node test.js reported the behavior.",
                "    - M1.red: fail. the behavior did not exist.",
                "    - M1.green: pass.",
                "    - Review:",
                "      - Status: pass",
                "      - Acceptance check: the behavior is proven.",
                "      - Scope check: only Touch changed.",
                f"      - Findings: {findings}",
                "    - Blocker: none",
                "    - Reauthorizations: none",
            ]
        )

    with tempfile.TemporaryDirectory(prefix="keel-negation-") as raw:
        root = Path(raw)

        def complete(name: str, findings: str) -> dict:
            repo = root / name
            write_gate_fixture(repo, tasks=findings_task(findings))
            run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
                "--record", "--json",
            )
            done = run_keel(
                repo, "gate", "task-complete", "--change", "demo", "--task", "1.1",
                "--json",
            )
            try:
                return json.loads(done.stdout)
            except json.JSONDecodeError:
                return {"status": "unparsed", "problems": [{"message": done.stdout[:400]}]}

        # M1 — the text that produced #144, verbatim in shape.
        negated = complete(
            "negated",
            "one, still open. The count is derivable from the declarations the "
            "module reads. Not resolved here: it is a different module and would "
            "be scope expansion. Durable owner: https://example.com/issues/1",
        )
        if negated.get("status") != "pass":
            report(
                f"{label}: names neither a check nor a path — a finding saying it "
                "was *not* resolved here, closing with a durable owner, was "
                f"refused; {problem_codes(negated)!r} {problem_text(negated)!r}."
            )
            return 1
        if "resolution evidence" in problem_text(negated).lower():
            report(
                f"{label}: the negated phrase still produced a resolution-evidence "
                f"diagnostic; {problem_text(negated)!r}."
            )
            return 1

        # M2 — the positive control, in all three opening positions. Without it
        # the narrowing could pass by recognizing no marker anywhere.
        for name, findings in (
            ("opens-value", "Resolved here: M9"),
            ("after-break", "one, and it was fixed.\n        Resolved here: M9"),
            ("after-stop", "one, and it was fixed. Resolved here: M9"),
        ):
            payload = complete(name, findings)
            if payload.get("status") == "pass":
                report(
                    f"{label}: stopped recognizing a real marker ({name}) — a "
                    "`Resolved here:` naming a check this task does not declare "
                    "completed cleanly."
                )
                return 1
            if "M9" not in problem_text(payload):
                report(
                    f"{label}: stopped recognizing a real marker ({name}) — the "
                    f"refusal does not name the cited check; {problem_text(payload)!r}."
                )
                return 1

        # M3 — a marker that opens no clause is refused, not ignored, and the
        # refusal names the rule so the author is not told to add what they wrote.
        swallowed = complete(
            "swallowed", "one, and the fix was Resolved here: M1 in passing"
        )
        if swallowed.get("status") == "pass":
            report(
                f"{label}: a finding whose only marker opens no clause completed "
                "cleanly, so it carried no disposition and nothing said so."
            )
            return 1
        # Asserted on the whole phrase, not the word: `opens` alone matches
        # inside `openspec`, which the same diagnostic already prints, and the
        # assertion was vacuous until this was tightened.
        if "opens its clause" not in problem_text(swallowed).lower():
            report(
                f"{label}: does not name the opening requirement — an author "
                "whose sentence visibly contains a marker is told to add a "
                f"disposition; {problem_text(swallowed)!r}."
            )
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def equivalence_task(
    *,
    base: str | None = "HEAD~1",
    fields: str | None = "wns, tns, cell_count",
    covers: tuple[str, ...] = ("E1: the measured result does not move",),
    label: str = "1.1",
    title: str = "Move the attribute without moving the numbers",
) -> str:
    """One `equivalence` task, with either declaration omittable."""
    lines = [
        f"- [ ] {label} {title}",
        "  - Covers:",
    ]
    lines.extend(f"    - {entry}" for entry in covers)
    lines.extend(
        [
            "  - Read:",
            "    - README.md",
            "  - Touch:",
            "    - src/example.js",
            "  - Verify:",
            "    - Strategy: equivalence",
        ]
    )
    if base is not None:
        lines.append(f"    - Base: {base}")
    if fields is not None:
        lines.append(f"    - Fields: {fields}")
    lines.extend(
        [
            "    - M1: node compare.js --base --head reports every field equal",
            "  - Autonomy boundary:",
            "    - Default: hard-stop",
            "    - Pre-authorized fallback: none",
            "  - Stop Rules:",
            "    - Stop on any field that differs.",
            "  - Evidence:",
            "    - Contract: pending",
            "    - M1: pending",
            "    - Review:",
            "      - Status: pass",
            "      - Acceptance check: every declared field agreed.",
            "      - Scope check: writes stayed inside Touch.",
            "      - Findings: none",
            "    - Blocker: none",
        ]
    )
    return "\n".join(lines) + "\n"


def validate_an_equivalence_claim_names_its_base_scenario() -> int:
    """Issue #142: the correct evidence for a refactor is zero difference.

    Red-green has no shape for it. The reporting repository re-recorded one
    task's contract twice to get past the shape — not because a criterion was
    wrong, but because the criterion had nowhere to live. An A/B against a base
    is *stronger* than red-green: it catches the change that also, incidentally,
    moved a result. What it needs is a place to say what it compares against and
    on which fields, plus a refusal for every way that shape can be complete and
    still compare nothing.
    """
    label = "an-equivalence-claim-names-its-base"

    def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True
        )

    with tempfile.TemporaryDirectory(prefix="keel-equivalence-") as raw:
        root = Path(raw)

        def fixture(name: str, task: str) -> Path:
            repo = (root / name).resolve()
            repo.mkdir()
            git(repo, "init", "-q")
            git(repo, "config", "user.email", "t@example.com")
            git(repo, "config", "user.name", "keel-test")
            write_gate_fixture(repo, tasks=task)
            write_text(repo / "src/example.js", "// product\n")
            git(repo, "add", "-A")
            git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "first")
            write_text(repo / "src/example.js", "// product, moved\n")
            git(repo, "add", "-A")
            git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "second")
            return repo

        def start(name: str, **kwargs) -> dict:
            repo = fixture(name, equivalence_task(**kwargs))
            result = run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
                "--no-guard", "--json",
            )
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {
                    "status": "unparsed",
                    "problems": [{"message": result.stdout[:400]}],
                }

        # M1 — the strategy is accepted, and it owes no red.
        payload = start("accepted")
        if payload.get("status") != "pass":
            report(
                f"{label}: unsupported verification strategy — a complete "
                "equivalence task was refused, so the one task class with the "
                "strongest criterion still has nowhere to declare it. "
                f"{problem_text(payload)}"
            )
            return 1
        capsule = (payload.get("contract") or {}).get("capsule") or {}
        verification = capsule.get("verification") or {}
        if verification.get("strategy", "").lower() != "equivalence":
            report(
                f"{label}: the compiled capsule does not carry the strategy; got "
                f"{verification.get('strategy')!r}."
            )
            return 1
        if not verification.get("base") or not verification.get("fields"):
            report(
                f"{label}: the capsule drops the declarations — base "
                f"{verification.get('base')!r}, fields "
                f"{verification.get('fields')!r}. A declaration absent from the "
                "capsule is absent from the fingerprint, so it could be edited "
                "after the run without moving the contract."
            )
            return 1
        warnings = " ".join(str(w) for w in (payload.get("warnings") or []))
        if ".red" in warnings or ".green" in warnings:
            report(
                f"{label}: equivalence was given a red-green obligation; the "
                f"criterion is agreement with a base, not a failing first run. "
                f"{warnings}"
            )
            return 1

        # M2 — every way the shape can be complete and still compare nothing,
        # each named for the declaration it is about. A diagnostic that named
        # the strategy would send the author to the line that is correct.
        for name, kwargs, code, expected in (
            ("no-base", {"base": None}, "missing-equivalence-base", "Base:"),
            ("no-fields", {"fields": None}, "missing-equivalence-fields", "Fields:"),
            ("empty-fields", {"fields": " , "}, "missing-equivalence-fields", "Fields:"),
            (
                "bad-base",
                {"base": "no-such-ref"},
                "unresolvable-equivalence-base",
                "no-such-ref",
            ),
        ):
            payload = start(name, **kwargs)
            if payload.get("status") == "pass":
                report(
                    f"{label}: accepted an equivalence task that compares "
                    f"nothing — the {name} fixture passed, so the declaration "
                    "is optional in practice."
                )
                return 1
            if code not in problem_codes(payload):
                report(
                    f"{label}: accepted an equivalence task that compares "
                    f"nothing — the {name} fixture was refused for another "
                    f"reason; expected {code}, got {problem_codes(payload)!r}."
                )
                return 1
            message = problem_text(payload)
            if expected not in message:
                report(
                    f"{label}: the {name} refusal does not name {expected!r}, so "
                    f"the author is sent to find which line is wrong; got "
                    f"{message!r}."
                )
                return 1
        # Absent and empty are the same state to the comparison and different
        # states to the author, so the two are asserted to read differently.
        absent = problem_text(start("no-fields-message", fields=None))
        empty = problem_text(start("empty-fields-message", fields=" , "))
        if absent == empty:
            report(
                f"{label}: a missing `Fields:` and one that resolves to an empty "
                "set produce the same sentence, so an author who wrote the line "
                "is told they did not."
            )
            return 1

        # M1 of 1.2 — `equivalence` owes no red, which makes it the first thing
        # reached for by a task that should have one. A task covering a scenario
        # the change *adds* is claiming new behavior and unchanged behavior at
        # once, and one of the two claims has no proof anywhere.
        added_spec = (
            "## ADDED Requirements\n\n"
            "### Requirement: The moved attribute keeps its effect\n\n"
            "The attribute SHALL keep its effect after the move.\n\n"
            "#### Scenario: The effect survives the move\n\n"
            "- **WHEN** the attribute moves into the flow\n"
            "- **THEN** the effect is unchanged\n\n"
            # A second real scenario, so the mismatched-sibling control fails
            # because the guard refused it and not because its Covers entry
            # resolves to nothing. A first attempt pointed the sibling at an
            # invented scenario and passed for that unrelated reason.
            "#### Scenario: The flow reports the attribute\n\n"
            "- **WHEN** the flow runs\n"
            "- **THEN** it reports the attribute\n"
        )
        covered = (
            "demo / The moved attribute keeps its effect / The effect survives "
            "the move"
        )

        def escape_fixture(name: str, *, sibling: str | None) -> dict:
            repo = (root / name).resolve()
            repo.mkdir()
            git(repo, "init", "-q")
            git(repo, "config", "user.email", "t@example.com")
            git(repo, "config", "user.name", "keel-test")
            tasks = equivalence_task(covers=(covered,))
            if sibling is not None:
                tasks += (
                    "- [ ] 1.2 Add the behavior\n"
                    "  - Covers:\n"
                    f"    - {sibling}\n"
                    "  - Read:\n    - README.md\n"
                    "  - Touch:\n    - src/other.js\n"
                    "  - Verify:\n"
                    "    - Strategy: vertical-tdd\n"
                    "    - M1: node test.js asserts the new behavior\n"
                    "  - Autonomy boundary:\n"
                    "    - Default: hard-stop\n"
                    "    - Pre-authorized fallback: none\n"
                    "  - Stop Rules:\n    - Stop on failure.\n"
                    "  - Evidence:\n    - Contract: pending\n    - M1: pending\n"
                    "    - Review:\n      - Status: pass\n"
                    "      - Acceptance check: behavior asserted.\n"
                    "      - Scope check: inside Touch.\n"
                    "      - Findings: none\n"
                    "    - Blocker: none\n"
                )
            write_gate_fixture(repo, tasks=tasks)
            write_text(repo / "openspec/changes/demo/specs/demo/spec.md", added_spec)
            write_text(repo / "src/example.js", "// product\n")
            git(repo, "add", "-A")
            git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "first")
            write_text(repo / "src/example.js", "// moved\n")
            git(repo, "add", "-A")
            git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "second")
            result = run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
                "--no-guard", "--json",
            )
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {
                    "status": "unparsed",
                    "problems": [{"message": result.stdout[:400]}],
                }

        payload = escape_fixture("escape-alone", sibling=None)
        if payload.get("status") == "pass":
            report(
                f"{label}: accepted new behavior with no red anywhere — an "
                "equivalence task covering a scenario the change adds passed, so "
                "the strategy is a way to author a feature with no red in the "
                "whole change."
            )
            return 1
        if "equivalence-covers-added-behavior" not in problem_codes(payload):
            report(
                f"{label}: accepted new behavior with no red anywhere — refused "
                f"for another reason; got {problem_codes(payload)!r}."
            )
            return 1
        message = problem_text(payload)
        if "The effect survives the move" not in message:
            report(
                f"{label}: the refusal does not name the covered scenario, so "
                f"the author cannot tell which Covers entry is the problem; got "
                f"{message!r}."
            )
            return 1
        if "unchanged" not in message:
            report(
                f"{label}: the refusal does not say why the two claims conflict; "
                f"got {message!r}."
            )
            return 1

        # M2 of 1.2 — the guard is satisfied by coverage of the entry it
        # objected to, and not by a red-green task merely existing in the change.
        payload = escape_fixture("escape-sibling", sibling=covered)
        if payload.get("status") != "pass":
            report(
                f"{label}: a sibling task covering the same scenario under "
                f"vertical-tdd did not satisfy the guard. {problem_text(payload)}"
            )
            return 1
        payload = escape_fixture(
            "escape-other-sibling",
            sibling=(
                "demo / The moved attribute keeps its effect / The flow reports "
                "the attribute"
            ),
        )
        if payload.get("status") == "pass":
            report(
                f"{label}: any sibling satisfied the guard — a red-green task "
                "covering a different scenario was accepted as proof of this "
                "one, which makes the guard a check that a change contains at "
                "least one red-green task."
            )
            return 1
        if "equivalence-covers-added-behavior" not in problem_codes(payload):
            report(
                f"{label}: any sibling satisfied the guard — refused for another "
                f"reason; got {problem_codes(payload)!r}."
            )
            return 1

        # M3 of 1.2 — the guard fires on new behavior, not on the strategy. A
        # task covering only identifiers, or a requirement the change does not
        # add, is an ordinary equivalence task.
        plain = start("escape-plain")
        if plain.get("status") != "pass":
            report(
                f"{label}: an equivalence task covering no added scenario was "
                f"refused. {problem_text(plain)}"
            )
            return 1

        # M3 — the shape that is complete, resolvable, and still empty. This is
        # the refusal worth having: nothing about the task looks wrong, and the
        # check passes having compared a thing against itself.
        payload = start("base-is-head", base="HEAD")
        if payload.get("status") == "pass":
            report(
                f"{label}: accepted a base that is head — an A/B against itself "
                "always agrees, so the check proves nothing and looks complete "
                "doing it."
            )
            return 1
        if "equivalence-base-is-head" not in problem_codes(payload):
            report(
                f"{label}: accepted a base that is head — refused for another "
                f"reason; got {problem_codes(payload)!r}."
            )
            return 1
        message = problem_text(payload)
        head = subprocess.run(
            ["git", "-C", str((root / "base-is-head").resolve()), "rev-parse",
             "HEAD"],
            capture_output=True, text=True,
        ).stdout.strip()
        if head and head not in message:
            report(
                f"{label}: the refusal does not name the resolved commit, so the "
                "author cannot tell which ref collapsed onto HEAD; got "
                f"{message!r}."
            )
            return 1
        if "always agrees" not in message:
            report(
                f"{label}: the refusal does not say why a base that is HEAD is "
                f"empty rather than merely redundant; got {message!r}."
            )
            return 1

        # 1.3 — Evidence may point at the machine output instead of retelling
        # it. A 244-line tasks.md that is mostly transcribed test output is a
        # transcription that can be wrong and that nobody can re-check.
        def artifact_fixture(
            name: str,
            *,
            artifact_path: str = "openspec/changes/demo/evidence/compare.json",
            body: str = '{"wns": 0.0, "tns": 0.0}\n',
            recorded: str | None = None,
            write_at: str | None = None,
        ) -> dict:
            repo = (root / name).resolve()
            repo.mkdir()
            git(repo, "init", "-q")
            git(repo, "config", "user.email", "t@example.com")
            git(repo, "config", "user.name", "keel-test")
            digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
            evidence = recorded or f"artifact {artifact_path} sha256:{digest}"
            tasks = equivalence_task().replace(
                "    - M1: pending", f"    - M1: {evidence}"
            )
            write_gate_fixture(repo, tasks=tasks)
            if write_at is not None:
                write_text(repo / write_at, body)
            write_text(repo / "src/example.js", "// product\n")
            git(repo, "add", "-A")
            git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "first")
            write_text(repo / "src/example.js", "// moved\n")
            git(repo, "add", "-A")
            git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "second")
            run_keel(
                repo, "gate", "task-start", "--change", "demo", "--task", "1.1",
                "--record", "--no-guard",
            )
            result = run_keel(
                repo, "gate", "task-complete", "--change", "demo", "--task",
                "1.1", "--json",
            )
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {
                    "status": "unparsed",
                    "problems": [{"message": result.stdout[:400]}],
                }

        inside = "openspec/changes/demo/evidence/compare.json"
        payload = artifact_fixture("artifact-ok", write_at=inside)
        if payload.get("status") != "pass":
            report(
                f"{label}: an artifact reference was not verified — a reference "
                "to a file that is there, with a digest that matches, was "
                f"refused. {problem_text(payload)}"
            )
            return 1
        payload = artifact_fixture("artifact-absent", write_at=None)
        if payload.get("status") == "pass":
            report(
                f"{label}: an artifact reference was not verified — a reference "
                "to a file that does not exist was accepted, so the form is "
                "tolerated as prose rather than checked. Any sentence would "
                "have passed the same way."
            )
            return 1
        if "artifact-missing" not in problem_codes(payload):
            report(
                f"{label}: an artifact reference was not verified — refused for "
                f"another reason; got {problem_codes(payload)!r}."
            )
            return 1

        # M2 of 1.3 — the digest is what makes the pointer worth more than a
        # path. A file that moved after the digest was recorded is the case a
        # bare path cannot see, and it is the common one: the command gets
        # re-run.
        stale = hashlib.sha256(b"different\n").hexdigest()
        payload = artifact_fixture(
            "artifact-stale",
            recorded=f"artifact {inside} sha256:{stale}",
            write_at=inside,
        )
        if payload.get("status") == "pass":
            report(
                f"{label}: accepted a stale digest — the artifact's content does "
                "not hash to the recorded digest and the reference was accepted, "
                "so Review reads whatever the file says now."
            )
            return 1
        if "artifact-digest-mismatch" not in problem_codes(payload):
            report(
                f"{label}: accepted a stale digest — refused for another reason; "
                f"got {problem_codes(payload)!r}."
            )
            return 1
        message = problem_text(payload)
        for expected in (inside, stale[:12]):
            if expected not in message:
                report(
                    f"{label}: the refusal does not name {expected!r}, so a "
                    "reader cannot tell a stale record from a wrong path; got "
                    f"{message!r}."
                )
                return 1

        # M3 of 1.3 — the inverse of the `Durable owner:` rule, for the opposite
        # reason: a follow-up pointer must outlive the change, and an evidence
        # artifact must travel with it. `openspec archive` moves the change
        # directory, so a path outside it is one the archive leaves behind.
        outside = "evidence/compare.json"
        payload = artifact_fixture("artifact-outside", artifact_path=outside, write_at=outside)
        if payload.get("status") == "pass":
            report(
                f"{label}: accepted a path archiving would leave behind — an "
                f"artifact at {outside!r} was accepted although the archive "
                "moves only the change directory."
            )
            return 1
        if "artifact-outside-change" not in problem_codes(payload):
            report(
                f"{label}: accepted a path archiving would leave behind — "
                f"refused for another reason; got {problem_codes(payload)!r}."
            )
            return 1
        if "archiv" not in problem_text(payload):
            report(
                f"{label}: the refusal does not say that archiving is what "
                f"breaks the pointer; got {problem_text(payload)!r}."
            )
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0

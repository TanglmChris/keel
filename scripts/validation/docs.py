"""Keel validation: docs (split from validate_plugin.py, #409)."""
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
    OPENSPEC_SEARCH_ORDER,
    OPENSPEC_SURFACE_OVERLAY_END,
    OPENSPEC_SURFACE_OVERLAY_START,
    PLUGIN_ROOT,
    ROOT,
    config_header_paragraph,
    config_header_problem,
    extract_managed_block,
    report,
    run_keel,
    run_node_expression,
    run_openspec,
    task_capsule_compact_fixture,
    write_text,
)
from validation import registry


def validate_decisions_are_selectable_scenario() -> int:
    """Issue #174: an enumerable decision is offered as selectable options.

    The owner asked (2026-09-28) that a decision be something the user can
    pick, not type, wherever the host offers a structured choice. No gate can
    observe presentation, so this checks only that both carriers say so — the
    resident protocol and the alignment skill's deep path, in source and in
    the shipped copy — and that the portable skill names no host tool.
    """
    label = "decisions-are-selectable:"

    def section(text: str, heading: str) -> str:
        start = text.find(heading)
        if start < 0:
            return ""
        rest = text[start + len(heading):]
        end = rest.find("\n## ")
        return rest if end < 0 else rest[:end]

    def offers_choices(text: str) -> bool:
        lowered = " ".join(text.lower().split())
        return (
            "structured-choice surface" in lowered
            and "recommend" in lowered
            and "first" in lowered
            and "open question" in lowered
            and "prose" in lowered
        )

    block = extract_managed_block((ROOT / "AGENTS.md").read_text(encoding="utf-8")) or ""
    if not offers_choices(section(block, "## User-facing communication")):
        report(
            f"{label} AGENTS.md User-facing communication does not offer "
            "decisions as selectable options."
        )
        return 1
    for root in ("src/skills", f"{PLUGIN_ROOT}/skills"):
        path = ROOT / root / "align-expectations" / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        if not offers_choices(section(text, "## Deep path")):
            report(
                f"{label} {root} align-expectations Deep path does not "
                "offer decisions as selectable options."
            )
            return 1
        if "AskUserQuestion" in text:
            report(f"{label} {root} align-expectations names a host tool.")
            return 1
    if "decisions-are-selectable" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("decisions-are-selectable scenario passed.")
    return 0


def validate_chat_role_apps_are_documented_scenario() -> int:
    """Issue #187: the setup guides and READMEs describe shared bots.

    Both guides carry the bot section — `keel chat bot add`, the Keychain
    accounts named by bot, the `slack.bots` mapping, that one bot serves a role
    in each of several projects, and that such a bot takes no direct messages
    — and neither still ties a token to a role or equates the app limit with a
    machine count.
    """
    label = "chat-role-apps-are-documented:"
    guides = {
        "docs/chat-slack-setup.md": ("serve a role in each of several projects", "takes no direct messages"),
        "docs/chat-slack-setup.zh-CN.md": ("在多个项目里各当一个角色", "不接私聊"),
    }
    for relative, phrases in guides.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in ('"bots"', "keel chat bot add", "bot:<name>", "app:<name>", "chat:write.public", "im:history", *phrases):
            if needle not in text:
                report(f"{label} {relative} does not carry {needle!r}.")
                return 1
        for stale in ("bot:<role>", "which means 10 machines", "也就是最多 10 台电脑"):
            if stale in text:
                report(f"{label} {relative} still says {stale!r}.")
                return 1
    readmes = {"README.md": "one bot can serve several projects", "README.zh-CN.md": "一个 bot 可以服务多个项目"}
    for relative, needle in readmes.items():
        if needle not in (ROOT / relative).read_text(encoding="utf-8"):
            report(f"{label} {relative} does not say {needle!r}.")
            return 1
    if "chat-role-apps-are-documented" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("chat-role-apps-are-documented scenario passed.")
    return 0


def validate_guidance_names_openspec_skills_scenario() -> int:
    """Issue #406: guidance names no `/opsx:` command, since Keel generates none.

    With the workflows delivered as skills only, a sentence telling the reader
    to run `/opsx:sync` points at a command that does not exist.
    """
    label = "guidance-names-openspec-skills:"
    shipped = [ROOT / "README.md", ROOT / "README.zh-CN.md",
               ROOT / "assets/openspec/schemas/keel-spec-driven/schema.yaml",
               *sorted((ROOT / "src/skills").rglob("SKILL.md")),
               *sorted((ROOT / "plugins/keel/skills").rglob("SKILL.md"))]
    naming = [str(p.relative_to(ROOT)) for p in shipped if "/opsx:" in p.read_text(encoding="utf-8")]
    if naming:
        report(f"{label} shipped guidance still names `/opsx:` commands: {naming!r}")
        return 1
    block = extract_managed_block((ROOT / "AGENTS.md").read_text(encoding="utf-8")) or ""
    if not block:
        report(f"{label} AGENTS.md has no managed protocol block to read.")
        return 1
    for needle in ("/opsx:", "commands/opsx"):
        if needle in block:
            report(f"{label} the AGENTS.md protocol block still names {needle!r}.")
            return 1

    with tempfile.TemporaryDirectory(prefix="keel-406-guidance-") as raw_tmp:
        repo = Path(raw_tmp)
        init = run_keel(repo, "--init", "--target", "claude")
        if init.returncode != 0:
            report(f"{label} keel --init --target claude failed: {(init.stderr or init.stdout).strip()}")
            return 1
        archive = (repo / ".claude/skills/openspec-archive-change/SKILL.md").read_text(encoding="utf-8")
        overlay = archive[archive.find(OPENSPEC_SURFACE_OVERLAY_START):archive.find(OPENSPEC_SURFACE_OVERLAY_END)]
        if not overlay:
            report(f"{label} the archive skill carries no Keel overlay to read.")
            return 1
        if "/opsx:" in overlay:
            report(f"{label} the archive overlay still names an `/opsx:` command.")
            return 1
        if "openspec-sync-specs" not in overlay:
            report(f"{label} the archive overlay does not name `openspec-sync-specs`.")
            return 1

    if "guidance-names-openspec-skills" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("guidance-names-openspec-skills scenario passed.")
    return 0


def validate_the_spec_names_the_managed_set_scenario() -> int:
    """Issue #86: the spec's summary named two of the four actions it covers.

    `propose` and `sync` joined the managed set as new requirements appended to
    the overlay spec, and the `## Purpose` and the requirement that says which
    actions carry an overlay were never rewritten — so the top of the file
    disagreed with the requirements below it.

    The Purpose line survived issue #79's sweep for a structural reason:
    OpenSpec's delta operations are Requirement-scoped, so no change can carry
    a Purpose edit, and the line is written once when the capability is
    created. It is therefore the location most likely to drift and the one
    least likely to be noticed, which is why it is checked by name here.

    Two named locations, not a scan. Statements in the published specs name a
    proper subset of the managed set and are correct — the doctor's
    command-surface label, which excludes the authoring action on purpose, and
    `authoring/apply/archive/sync`, which spells `propose` as authoring. A
    check that refused those would cost more than the drift it catches.
    """
    label = "the-spec-names-the-managed-set"

    source = (ROOT / "bin" / "keel.js").read_text(encoding="utf-8")
    declaration = re.search(
        r"const OPENSPEC_OVERLAY_ACTIONS = \[([^\]]*)\];", source
    )
    if declaration is None:
        report(
            f"{label}: bin/keel.js declares no OPENSPEC_OVERLAY_ACTIONS, so the "
            "check has no managed set to compare against. Restating the set "
            "here would be the same defect one layer out."
        )
        return 1
    managed = re.findall(r'"([a-z]+)"', declaration.group(1))
    if not managed:
        report(f"{label}: OPENSPEC_OVERLAY_ACTIONS parsed to an empty set.")
        return 1

    spec_path = ROOT / "openspec/specs/keel-openspec-surface-overlay/spec.md"
    REQUIREMENT = "### Requirement: Keel overlays every action in the managed set"

    def locations(text: str) -> tuple[str, str] | None:
        purpose = re.search(r"^## Purpose\s*\n+(.+?)\n", text, re.M)
        if purpose is None:
            return None
        start = text.find(REQUIREMENT)
        if start < 0:
            return None
        end = text.find("\n### Requirement:", start + len(REQUIREMENT))
        body = text[start : end if end > 0 else len(text)]
        return purpose.group(1), body

    # Two distinct failures, kept apart on purpose: a location the check
    # cannot find is not a location that names the wrong thing, and reporting
    # the second when the first happened sends the reader to a paragraph with
    # nothing wrong in it.
    NOT_FOUND = "__not-found__"

    def missing(text: str) -> list[tuple[str, list[str]]]:
        found = locations(text)
        if found is None:
            return [(NOT_FOUND, list(managed))]
        purpose, body = found
        gaps = []
        for name, region in (("## Purpose", purpose), (REQUIREMENT, body)):
            absent = [
                action for action in managed
                if not re.search(rf"\b{action}\b", region)
            ]
            if absent:
                gaps.append((name, absent))
        return gaps

    published = spec_path.read_text(encoding="utf-8")
    gaps = missing(published)
    if gaps:
        for name, absent in gaps:
            if name == NOT_FOUND:
                report(
                    f"{label}: keel-openspec-surface-overlay has no `## Purpose` "
                    f"line or no `{REQUIREMENT}` heading, so this check found "
                    "nothing to compare against the managed set. Nothing about "
                    "the action names is being reported here — the location is "
                    "what is missing."
                )
                continue
            report(
                f"{label}: the `{name}` of keel-openspec-surface-overlay does "
                f"not name {', '.join(absent)}, which bin/keel.js manages an "
                "overlay for. The file's summary and the requirements under it "
                "disagree, and a reader takes the summary."
            )
        return 1

    # The check fails on a drifted copy, and names the location that drifted.
    drifted = published.replace(
        REQUIREMENT, "### Requirement: Keel overlays apply and archive surfaces", 1
    )
    if missing(drifted) == []:
        report(
            f"{label}: a copy whose requirement heading is gone was reported "
            "clean. A check that cannot find what it looks for must fail, not "
            "pass — a vacuous pass is how the drift got here."
        )
        return 1

    for action in managed:
        reduced = published
        found = locations(published)
        assert found is not None
        purpose_line = found[0]
        reduced = reduced.replace(
            purpose_line, re.sub(rf"\b{action}\b[,/ ]*", "", purpose_line), 1
        )
        gaps = missing(reduced)
        if not any(name == "## Purpose" and action in absent for name, absent in gaps):
            report(
                f"{label}: the Purpose line with `{action}` removed was not "
                "reported. Each managed action is checked on its own, so an "
                "action that joins the set later is not covered by the others."
            )
            return 1

    # The three subset spellings that are correct stay correct: the check is
    # two named locations in one file, not a scan for action words.
    diagnostics = (
        ROOT / "openspec/specs/keel-target-surface-diagnostics/spec.md"
    ).read_text(encoding="utf-8")
    for correct in (
        "apply/archive/sync overlay markers",
        "it names sync alongside apply and archive",
    ):
        if correct not in diagnostics:
            report(
                f"{label}: the diagnostics spec no longer carries the correct "
                f"subset spelling `{correct}`. This scenario asserts the check "
                "leaves it alone; if the wording moved, the assertion has to "
                "move with it rather than be dropped."
            )
            return 1
    # `sync/archive decisions` left the overlay spec with the ownership
    # requirements (#414); `authoring/apply/archive/sync` is the correct subset
    # spelling that remains in it.
    if "authoring/apply/archive/sync" not in published:
        report(
            f"{label}: the overlay spec no longer carries "
            "`authoring/apply/archive/sync`, the correct subset spelling this "
            "check must not refuse."
        )
        return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


SPEC_TEMPLATE_RELATIVE = "schemas/keel-spec-driven/templates/spec.md"


SLOT_FILLER = "the recorded feed status"


# The filler must be a strategy the generic task can use as written.
# `evidence-first` no longer is: it carries a `Reason:` the generic task
# has no slot for, and giving it one would put a line there that is wrong
# for every other strategy the slot can take.
SLOT_VOCABULARY = {"<strategy>": "vertical-tdd"}


def fill_template_slots(text: str) -> str:
    """Fill a shipped template's author-facing slots the way an author would.

    Deliberately mechanical, so a slot added to the template later is handled
    without touching the scenario: what is asserted is the template's structure
    rather than a hand-maintained copy of it.

    One rule for both templates. An own-line comment is an instruction to the
    author and goes; a comment with text before it on the line is that line's
    slot — a requirement name, a task title — and is filled, because stripping
    it would leave a heading the parser cannot read.

    The spec template used to take a mode that replaced every comment, and it
    stopped being correct the moment that template gained an own-line
    instruction (`ed1388d`, the change that fixed issue #28). The instruction
    became a bare paragraph of slot text above `The system SHALL …`, and
    `openspec validate` reported the requirement as lacking a modal verb —
    the fixture failing the template rather than the template failing.
    """
    text = re.sub(r"^[ \t]*<!--[\s\S]*?-->[ \t]*\r?\n", "", text, flags=re.M)
    text = re.sub(r"<!--[\s\S]*?-->", SLOT_FILLER, text)
    # A slot whose value comes from a fixed vocabulary needs a member of it, so
    # those are named. Everything else takes the generic filler.
    for slot, value in SLOT_VOCABULARY.items():
        text = text.replace(slot, value)
    # Innermost-first to a fixed point: a slot may quote an identifier shape such
    # as `Q<n>`, and the inner brackets would otherwise block the outer match and
    # leave the whole slot unfilled.
    while True:
        collapsed = re.sub(r"<[^<>\n]*>", SLOT_FILLER, text)
        if collapsed == text:
            return text
        text = collapsed


TASKS_TEMPLATE_RELATIVE = "schemas/keel-spec-driven/templates/tasks.md"


def validate_tasks_template_red_green_example_scenario() -> int:
    """Issue #28 items 2 and 3: the red-green shape was described, never shown.

    The template's prose has said since 5.3.4 that the `.red`/`.green` entries
    come in addition to the bare `M<n>` entry, but it showed only the flat form.
    The reporter tried annotated labels, was refused, landed on the flat form,
    and was refused again for the missing bare entry. One worked example closes
    both attempts — and it is asserted by gating it, so it cannot drift from the
    rule it illustrates.
    """
    shipped = ROOT / "openspec" / TASKS_TEMPLATE_RELATIVE
    packaged = ROOT / "assets" / "openspec" / TASKS_TEMPLATE_RELATIVE
    for path in (shipped, packaged):
        if not path.is_file():
            report(f"tasks-template-red-green-example: missing template {path}.")
            return 1
    if shipped.read_bytes() != packaged.read_bytes():
        report(
            "tasks-template-red-green-example: the two shipped copies of the "
            "tasks template have diverged."
        )
        return 1

    source = shipped.read_text(encoding="utf-8")
    red_green = [
        block
        for block in re.split(r"^## ", source, flags=re.MULTILINE)
        if re.search(r"^\s*-\s*Strategy:\s*(vertical-tdd|regression-first)", block, re.M)
    ]
    if not red_green:
        report(
            "tasks-template-red-green-example: the template defines no task "
            "group with a red-green strategy, so it still only describes one."
        )
        return 1
    group = red_green[0]
    untagged = re.findall(r"^\s*-\s*(M[1-9]\d*):\s*(?!pending)", group, re.M)
    tagged = re.findall(r"^\s*-\s*(M[1-9]\d*)\s*\([^)]*regression[^)]*\):", group, re.M)
    if not untagged:
        report(
            "tasks-template-red-green-example: the red-green group has no "
            "untagged check, which task-start refuses as regression-only."
        )
        return 1
    if not tagged:
        report(
            "tasks-template-red-green-example: the red-green group shows no "
            "(regression)-tagged check, so the exemption is still unillustrated."
        )
        return 1
    label = untagged[0]
    for suffix in ("", ".red", ".green"):
        if not re.search(rf"^\s*-\s*{label}{re.escape(suffix)}:", group, re.M):
            report(
                "tasks-template-red-green-example: the untagged check is missing "
                f"its `{label}{suffix}` Evidence entry."
            )
            return 1
    for suffix in (".red", ".green"):
        if re.search(rf"^\s*-\s*{tagged[0]}{re.escape(suffix)}:", group, re.M):
            report(
                "tasks-template-red-green-example: the (regression)-tagged check "
                f"carries a `{suffix}` entry it is exempt from."
            )
            return 1

    # Gating the filled template is what keeps the example from drifting from
    # the rule it illustrates.
    filled = fill_template_slots(source)
    with tempfile.TemporaryDirectory(prefix="keel-tasks-template-") as raw:
        repo = Path(raw)
        write_text(repo / "openspec/changes/from-template/tasks.md", filled)
        ids = re.findall(r"^\s*-\s*\[[ xX]\]\s+(\d+(?:\.\d+)+)\s", filled, re.M)
        if not ids:
            report(
                "tasks-template-red-green-example: the filled template defines "
                "no task the gate can read."
            )
            return 1
        for task_id in ids:
            result = run_keel(
                repo,
                "gate",
                "task-start",
                "--change",
                "from-template",
                "--task",
                task_id,
                "--json",
            )
            payload = json.loads(result.stdout)
            if payload.get("status") != "pass":
                report(
                    "tasks-template-red-green-example: task "
                    f"{task_id} written from the shipped template did not pass "
                    "task-start."
                )
                for problem in payload.get("problems", []):
                    report(f"  {problem.get('code')}: {problem.get('message')}")
                return 1
    if "tasks-template-red-green-example" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "tasks-template-red-green-example: the scenario registry does not "
            "include it."
        )
        return 1
    report("tasks-template-red-green-example scenario passed.")
    return 0


def validate_spec_template_validates_scenario() -> int:
    """Issue #28 item 7: following the spec template guaranteed a first failure.

    The template's requirement body is a comment with no modal verb, and
    `openspec validate` requires SHALL or MUST, so the reporter's 16 requirements
    produced 16 errors. Asserted by running the filled template through the
    validator rather than by matching the template's prose, because a template
    that only mentions the requirement in a comment would satisfy the latter.
    """
    shipped = ROOT / "openspec" / SPEC_TEMPLATE_RELATIVE
    packaged = ROOT / "assets" / "openspec" / SPEC_TEMPLATE_RELATIVE
    for path in (shipped, packaged):
        if not path.is_file():
            report(f"spec-template-validates: missing shipped template {path}.")
            return 1
    if shipped.read_bytes() != packaged.read_bytes():
        report(
            "spec-template-validates: the two shipped copies of the spec "
            "template have diverged."
        )
        return 1
    if run_openspec(ROOT, "--version") is None:
        report(
            "spec-template-validates skipped: the openspec CLI could not be "
            "found. Searched " + ", then ".join(OPENSPEC_SEARCH_ORDER) + "."
        )
        return 0

    filled = fill_template_slots(shipped.read_text(encoding="utf-8"))
    # A line that is slot text and nothing else is an author instruction the
    # filler treated as a slot. It reads as a requirement body with no modal
    # verb, so the fixture would be handing the validator something no author
    # would ever write and reporting the template for it.
    stray = [
        index + 1
        for index, line in enumerate(filled.splitlines())
        if line.strip() == SLOT_FILLER
    ]
    if stray:
        report(
            "spec-template-validates: the filled template has slot text alone "
            f"on line(s) {stray}, so an own-line author instruction was filled "
            "rather than stripped and the fixture is malforming the template."
        )
        return 1
    with tempfile.TemporaryDirectory(prefix="keel-spec-template-") as raw:
        repo = Path(raw)
        write_text(repo / "openspec/project.md", "# Project\n\nA fixture.\n")
        change = repo / "openspec/changes/from-template"
        write_text(
            change / "proposal.md",
            "# from-template\n\n## Why\n\nExercise the shipped spec template.\n"
            "\n## What Changes\n\n- One requirement written from the template.\n",
        )
        write_text(change / "specs/demo-capability/spec.md", filled)
        result = run_openspec(repo, "validate", "from-template")
        if result is None:
            report(
                "spec-template-validates skipped: the openspec CLI vanished "
                "mid-scenario."
            )
            return 0
        if result.returncode != 0:
            report(
                "spec-template-validates: a requirement written from the "
                "shipped template did not validate."
            )
            report((result.stdout or result.stderr).strip())
            return 1
    if "spec-template-validates" not in {name for name, _ in registry.SCENARIOS}:
        report("spec-template-validates: the scenario registry does not include it.")
        return 1
    report("spec-template-validates scenario passed.")
    return 0


def validate_verification_layering_docs_scenario() -> int:
    en = (ROOT / "README.md").read_text(encoding="utf-8")
    for needle in (
        "## Verification layering",
        "inner-loop",
        "Full gate",
        "pre-push",
        "change-close",
    ):
        if needle not in en:
            report(
                "verification-layering-docs: README.md lacks the fast/full "
                f"verification split marker: {needle}"
            )
            return 1

    zh = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
    for needle in ("## 验证分层", "快速内环", "全量门禁", "pre-push", "change-close"):
        if needle not in zh:
            report(
                "verification-layering-docs: README.zh-CN.md lacks the fast/full "
                f"verification split marker: {needle}"
            )
            return 1

    if "verification-layering-docs" not in {name for name, _ in registry.SCENARIOS}:
        report("verification-layering-docs: the scenario registry does not include it.")
        return 1

    report("verification-layering-docs scenario passed.")
    return 0


ACCEPTED_AUTHORIZE_NAMES = (
    "commit, push, push:<branch glob>[@<role>], release, archive, continuation, "
    "issue:<owner>/<repo>[@<role>], protocol-refresh, chat-reply:<group>[@<role>], "
    "issue-close:<owner>/<repo>[@<role>], cleanup:scratch[@<role>], push-protected:<branch glob>[@<role>], shift-restore, self-shift, "
    "delete-branch:merged[@<role>]"
)


def validate_continuation_docs_scenario() -> int:
    """Every text an agent reads at the between-task boundary names the word (#94).

    The README and the config comment are where an owner learns the
    vocabulary, and the resident protocol is what the agent holds in context.
    The goal skill's stop rule was the third reader until the skill was
    removed in 5.173.0 (#414).
    """
    label = "continuation-docs"

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    # Since #414 crossing the boundary needs no confirmation by default, and the
    # README says so where it names the word.
    for needle in (
        "next unchecked task of the same change",
        "needs no confirmation by default",
    ):
        if needle not in readme:
            report(f"{label}: README.md lacks: {needle}")
            return 1
    # The seventh name (#164). Each surface that spells the vocabulary out has
    # to spell all of it: a reader copies from the list they are shown.
    for needle in (
        f"accepted names: {ACCEPTED_AUTHORIZE_NAMES}",
        "The fourteen names above are the whole vocabulary.",
        "`protocol-refresh`, the seventh name",
    ):
        if needle not in readme:
            report(f"{label}: README.md lacks: protocol-refresh, as {needle!r}")
            return 1

    config_text = (ROOT / "keel/config.yaml").read_text(encoding="utf-8")
    if "commit, push, push:<branch glob>[@<role>],\n# release, archive, continuation, issue:<owner>/<repo>[@<role>], protocol-refresh,\n# chat-reply:<group>[@<role>], issue-close:<owner>/<repo>[@<role>], cleanup:scratch[@<role>],\n# push-protected:<branch glob>[@<role>], shift-restore, self-shift,\n# delete-branch:merged[@<role>]" not in config_text:
        report(
            f"{label}: keel/config.yaml's comment lacks: protocol-refresh in the "
            "seven-name vocabulary."
        )
        return 1

    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    # M2 — the rule an agent follows when `keel context` names a refresh. The
    # consumer bootstrap has no room for it (its byte budget is spent), and
    # needs none: it opens with `keel context`, whose `Protocol:` line states
    # the same rule in whichever state applies.
    session = agents.split("## Session Start", 1)[-1].split("\n## ", 1)[0]
    for needle in ("`protocol-refresh`", "write guard", "uncommitted"):
        if needle not in session:
            report(
                f"{label}: AGENTS.md Session Start does not carry the "
                f"protocol-refresh rule; it lacks {needle!r}."
            )
            return 1
    bootstrap = (ROOT / "assets/bootstrap/AGENTS.md").read_text(encoding="utf-8")
    if "Start every session with `keel context`" not in bootstrap:
        report(
            f"{label}: the bootstrap does not carry the protocol-refresh rule's "
            "route to a consumer: it no longer opens with `keel context`."
        )
        return 1
    parts = agents.split("## Execution boundary", 1)
    if len(parts) != 2:
        report(f"{label}: AGENTS.md lost its Execution boundary section.")
        return 1
    section = parts[1].split("\n## ", 1)[0]
    for needle in (
        "declared `continuation` is accepted and changes nothing",
        "next unchecked task of the same approved change needs no confirmation",
        "its own recorded fingerprint",
    ):
        if needle not in section:
            report(f"{label}: AGENTS.md Execution boundary lacks: {needle}")
            return 1

    report("continuation-docs scenario passed.")
    return 0


def validate_plan_funnel_guidance_scenario() -> int:
    # The funnel is a conditional check, read on demand since #411.
    skill_copies = (
        ROOT / "src/skills/review-checklist/conditional-checks.md",
        ROOT / PLUGIN_ROOT / "skills/review-checklist/conditional-checks.md",
    )
    for copy in skill_copies:
        text = copy.read_text(encoding="utf-8")
        for needle in (
            "Planning artifact funnel",
            "never execution authority",
            "returns to OpenSpec authoring",
        ):
            if needle not in text:
                report(
                    f"plan-funnel-guidance: {copy.name} in {copy.parent.parent.name} "
                    f"lacks the funnel check ({needle!r})."
                )
                return 1
    if skill_copies[0].read_bytes() != skill_copies[1].read_bytes():
        report(
            "plan-funnel-guidance: shipped review-checklist copy diverges "
            "from the canonical source."
        )
        return 1

    for name in ("README.md", "README.zh-CN.md"):
        readme = (ROOT / name).read_text(encoding="utf-8")
        if "plan mode" not in readme or "proposal/design/specs/tasks" not in readme:
            report(f"plan-funnel-guidance: {name} lacks the plan-mode funnel rule.")
            return 1

    if "plan-funnel-guidance" not in {name for name, _ in registry.SCENARIOS}:
        report("plan-funnel-guidance: the scenario registry does not include it.")
        return 1

    report("plan-funnel-guidance scenario passed.")
    return 0


def validate_published_specs_validate_strictly_scenario() -> int:
    """Issue #46: the store Keel publishes was validated by nothing.

    Every change's closing task runs `openspec validate <change> --strict`,
    which reads the change directory and stays green. The published store under
    `openspec/specs/` was read by no check at all — measured at 5.16.0,
    `--specs` appeared zero times in this file. Issue #46 found 8 of 21 specs
    failing strict validation, every one on `Requirement must contain SHALL or
    MUST keyword`, because the requirement opened with a context paragraph and
    the strict validator reads only the block under the heading. Those failures
    had never appeared in front of anyone.

    They are gone now, removed by spec rewrites made for other reasons. That is
    what makes this the moment to assert it absolutely rather than as the
    ratchet #46 proposed: at a count of 8 a ratchet was the honest shape, and at
    0 the same mechanism becomes a budget for failures to hide in.
    """
    label = "published-specs-validate-strictly"

    # The pinned binary, not whatever `openspec` PATH happens to offer. This is
    # not fussiness: measured here, PATH answers 1.4.1 and reports 8 failures
    # while the version this repository resolves answers 1.6.0 and reports
    # none. Issue #46 recorded those 8 failures as an openspec 1.6.0 result;
    # they are 1.4.1's, and the store has always passed under the version the
    # repository pins. A check that reads PATH would re-record the same
    # mistake, which is exactly what `keel-target-surface-diagnostics` means by
    # a suite that silently changes which program it runs reporting facts about
    # a different program.
    pinned = ROOT / "node_modules" / ".bin" / (
        "openspec.cmd" if os.name == "nt" else "openspec"
    )
    if not pinned.exists():
        report(
            f"{label}: the pinned openspec is not installed "
            "(node_modules/.bin/openspec); reporting the skip rather than "
            "falling back to PATH, which would answer for a different program."
        )
        return 0

    def pinned_openspec(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(pinned), *args],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )

    version = pinned_openspec("--version")
    exercised = re.search(r"\d+\.\d+\.\d+", version.stdout or "")
    result = pinned_openspec("validate", "--specs", "--strict")

    output = f"{result.stdout or ''}{result.stderr or ''}"
    # Two independent readings. The exit status alone would pass if the command
    # stopped validating; the per-spec lines alone would pass if it started
    # exiting non-zero for an unrelated reason. Neither is trusted on its own.
    failed = [
        line.strip()
        for line in output.splitlines()
        if line.strip().startswith("✗")
    ]
    totals = re.search(r"Totals:\s*(\d+) passed,\s*(\d+) failed", output)
    if not totals:
        report(
            f"{label} the validator produced no totals line, so the result "
            "cannot be read. The output shape it reports may have moved."
        )
        report(output.strip()[:600])
        return 1
    passed_count, failed_count = int(totals.group(1)), int(totals.group(2))

    if failed:
        report(
            f"{label} {len(failed)} published spec(s) fail strict validation "
            f"against openspec {exercised.group(0) if exercised else 'unknown'}. "
            "A published spec that the validator Keel ships refuses is one "
            "every consumer sees refused. The usual cause is a requirement "
            "whose modal verb sits below its first paragraph — the strict "
            "validator reads only the block directly under the heading."
        )
        for line in failed:
            report(f"  {line}")
        return 1
    if failed_count != 0:
        report(
            f"{label} the totals line reports {failed_count} failing spec(s) "
            "while no per-spec failure line was emitted. The two readings "
            "disagree, so the result is not trustworthy either way."
        )
        report(output.strip()[:600])
        return 1
    if result.returncode != 0:
        report(
            f"{label} the validator reported {passed_count} passed and 0 "
            f"failed but exited {result.returncode}. The verdict and the exit "
            "status disagree."
        )
        report(output.strip()[:600])
        return 1
    if passed_count == 0:
        report(
            f"{label} the validator reports zero specs. An empty store passes "
            "every assertion about it, which is the shape "
            "`A derived assertion set that collapses to empty fails instead of "
            "passing` exists to refuse."
        )
        return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(
        f"{label} scenario passed: {passed_count} published specs validate "
        f"strictly against openspec "
        f"{exercised.group(0) if exercised else 'unknown'}."
    )
    return 0


def validate_a_count_is_derived_from_what_it_counts_scenario() -> int:
    """Issue #143: the header assertion restated a set as an English numeral.

    It had been hand-bumped twice, and the second bump was discovered by a red
    suite run in a scenario whose name has nothing to do with what was changed.
    An assertion about a set belongs to the set: read it from the module that
    defines it, and name the member that is missing rather than a count.
    """
    label = "a-count-is-derived-from-what-it-counts"

    def declared_names(root: Path) -> list[str]:
        result = run_node_expression(
            root,
            "process.stdout.write("
            "require('./src/core/config.js').CONFIG_DECLARATIONS.join(','))",
        )
        return [name for name in result.strip().split(",") if name]

    names = declared_names(ROOT)
    if not names:
        report(
            f"{label}: the assertion is a literal — `src/core/config.js` exports "
            "no declaration list, so nothing the header is checked against comes "
            "from the code that reads it."
        )
        return 1
    for expected in (
        "fast_check",
        "authorize",
        "precedents",
        "triage",
        "full_mode_paths",
    ):
        if expected not in names:
            report(
                f"{label}: the exported declaration list omits {expected!r}, so "
                f"the header is not checked for it; got {names!r}."
            )
            return 1

    header = (ROOT / "keel/config.yaml").read_text(encoding="utf-8")
    flat_header = config_header_paragraph(header)
    for name in names:
        if name not in flat_header:
            report(
                f"{label}: keel/config.yaml's header does not name {name!r}, "
                "which is the declaration a new project would never learn it may "
                "write."
            )
            return 1

    # The derivation is proved by feeding the check a member the header cannot
    # contain. Without this the whole scenario is satisfied by a list that
    # happens to agree with a header nobody compared it to.
    missing = config_header_problem(names + ["invented_declaration"], header)
    if not missing:
        report(
            f"{label}: the assertion is a literal — a declaration absent from "
            "the header produced no failure, so the check is not reading the "
            "exported list."
        )
        return 1
    if "invented_declaration" not in missing:
        report(
            f"{label}: the failure does not name the missing declaration; got "
            f"{missing!r}."
        )
        return 1
    if re.search(r"\b(?:four|five|six|seven)\b", missing, re.IGNORECASE):
        report(
            f"{label}: still says six declarations — the failure reports a "
            f"count rather than the missing name; got {missing!r}."
        )
        return 1

    # The header is the opening paragraph, not the file. A declaration name that
    # appears only in the body — a comment elsewhere happening to use the word —
    # does not tell a new project it may write that key. Found when `merge` was
    # added in 5.71.0: the triage section's "never authorizes a merge" satisfied
    # the rule before the header said anything (#155).
    body_only = header.replace(
        "# delegation, which names who runs a task;",
        "# delegation, which names who runs a task;",
    ) + "\n# a body comment that mentions body_only_declaration in passing\n"
    if not config_header_problem(names + ["body_only_declaration"], body_only):
        report(
            f"{label}: a declaration named only in the file body was accepted as "
            "named in the header — the rule reads the whole file, so any common "
            "word used anywhere satisfies it."
        )
        return 1

    # A header naming every declaration while miscounting them in prose passes:
    # membership is the checkable property, and a count is a lossy restatement.
    # The numeral is located by shape, not by its current value. Pinning the
    # word here would reintroduce the literal this scenario exists to remove,
    # one level down: adding `executor_tier` moved the header to "Seven" and the
    # mutation stopped finding anything to vary.
    miscounted, varied = re.subn(
        r"\b\w+ independent declarations\b",
        "Zero independent declarations",
        header,
        count=1,
    )
    if not varied:
        report(f"{label}: the header's prose count could not be located to vary it.")
        return 1
    if config_header_problem(names, miscounted):
        report(
            f"{label}: still says six declarations — a header naming all of them "
            "while miscounting them in prose was refused."
        )
        return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_a_tier_declares_what_is_skipped_scenario() -> int:
    """Issue #135: which guidance an executor skips is a declaration, not a judgement.

    A strong executor gets no value from stepwise how-to prose and pays for it on
    every activation. The report's own argument against letting the executor
    decide is that "do I need this?" is the judgement it is worst at, so the skip
    is written down by the repository. The tier reaches guidance and nothing else:
    a reader who takes it for a relaxation of the gates is worse off than one who
    never saw it, which is why every surface that reports it says so.
    """
    label = "a-tier-declares-what-is-skipped"

    with tempfile.TemporaryDirectory(prefix="keel-tier-") as raw:
        root = Path(raw)

        def fixture(name: str, body: str) -> Path:
            repo = root / name
            repo.mkdir()
            (repo / "keel").mkdir()
            (repo / "keel" / "config.yaml").write_text(body, encoding="utf-8")
            return repo

        def context(repo: Path) -> str:
            return run_keel(repo, "context").stdout

        # M1 — the declared tier is reported, an absent one reports the default,
        # and both say guidance is all the tier reaches.
        for name, body, expected in (
            ("high", "fast_check: echo high\nexecutor_tier: high\n", "high"),
            ("absent", "fast_check: echo absent\n", "standard"),
        ):
            repo = fixture(name, body)
            out = context(repo)
            line = next(
                (l for l in out.splitlines() if l.startswith("Executor tier:")), None
            )
            if line is None:
                report(
                    f"{label}: no executor tier reported — the {name} repository "
                    "is told nothing about which guidance its skills load."
                )
                report(out)
                return 1
            if expected not in line:
                report(
                    f"{label}: the {name} repository reports {line!r} rather than "
                    f"the {expected!r} tier."
                )
                return 1
            if "guidance" not in line:
                report(
                    f"{label}: no executor tier reported as affecting guidance "
                    f"only; {line!r} leaves a reader free to take it for a "
                    "relaxation of the gates."
                )
                return 1

        # M2 — a value Keel cannot read fails closed to reading the guidance.
        # The author of a typo believes they declared what they typed, so a
        # misspelling must not silently buy the skip it asked for, and the
        # refusal names the value and the alternatives rather than the key.
        typo = fixture("typo", "fast_check: echo typo\nexecutor_tier: aggressive\n")
        out = context(typo)
        line = next(
            (l for l in out.splitlines() if l.startswith("Executor tier:")), None
        )
        if line is None:
            report(
                f"{label}: accepted a tier outside the set — the projection "
                "reported no tier at all for an unreadable value, so the "
                "fallback is invisible."
            )
            report(out)
            return 1
        if "standard" not in line:
            report(
                f"{label}: accepted a tier outside the set — an unreadable value "
                f"did not fall back to reading the guidance; got {line!r}."
            )
            report(out)
            return 1
        if "aggressive" not in out:
            report(
                f"{label}: the rejected value is not named, so the author is "
                "left believing they declared what they typed."
            )
            report(out)
            return 1
        if "high" not in out:
            report(
                f"{label}: the refusal does not name the accepted tiers, so the "
                "reader learns their value is wrong and not what is right."
            )
            report(out)
            return 1
        doctor = run_keel(typo, "--doctor").stdout
        if "executor_tier" not in doctor or "aggressive" not in doctor:
            report(
                f"{label}: the doctor does not report the declaration as failed "
                "and name the entry, so it reports health the projection "
                "contradicts."
            )
            report(doctor)
            return 1
        healthy = run_keel(fixture("ok", "executor_tier: high\n"), "--doctor").stdout
        if "executor_tier: high" not in healthy:
            report(
                f"{label}: the doctor does not report a readable declaration, so "
                "the only tier it ever mentions is a broken one."
            )
            report(healthy)
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


# The words Keel states a criterion in. A guidance file is asserted to contain
# none of them, which is what makes "the executor tier removes no criterion" a
# property of the repository rather than a promise in a design document: a tier
# can only skip a file that decides nothing.
CRITERION_VOCABULARY = ("MUST", "SHOULD", "refuses", "rejects", "hard-stops")


def guidance_criterion_problem(name: str, text: str) -> str | None:
    """Return the problem a guidance file's text has, or None.

    Takes the text rather than reading the path, so the rule can be exercised on
    a planted copy. A rule that could only ever see files already known to be
    clean would pass forever without anyone learning whether it fires.
    """
    for word in CRITERION_VOCABULARY:
        if word in text:
            return (
                f"{name}'s guidance.md states a criterion — it contains "
                f"{word!r}, and a criterion in the file the executor tier skips "
                "would let `executor_tier: high` relax a rule rather than skip "
                "an explanation. Move the sentence back into SKILL.md."
            )
    return None


def validate_guidance_is_referenced_and_carries_no_criterion_scenario() -> int:
    """Issue #135: stepwise guidance is referenced, and it decides nothing.

    Keel is not on the delivery path for a skill body — the host reads
    `plugins/keel/skills/*/SKILL.md` directly — so the only way the resident cost
    falls is for the body to be smaller. What leaves it is how-to prose; every
    criterion stays, and that is checked here by planting one rather than
    promised, because a tier that could remove a criterion would be a relaxation
    of the gates wearing a capability label.
    """
    label = "guidance-is-referenced-and-carries-no-criterion"
    skills_root = ROOT / "src/skills"
    guidance_files = sorted(skills_root.glob("*/guidance.md"))

    # Two skills carry one today (#135, #389). An empty glob would satisfy every loop
    # below without reading anything, so the count is asserted first.
    if not guidance_files:
        report(
            f"{label}: no skill has a guidance.md, so every assertion below is "
            "vacuous — the split this scenario checks did not happen."
        )
        return 1

    for guidance in guidance_files:
        skill = guidance.parent / "SKILL.md"
        body = skill.read_text(encoding="utf-8")
        text = guidance.read_text(encoding="utf-8")
        if "guidance.md" not in body:
            report(
                f"{label}: guidance file is not referenced — "
                f"{guidance.parent.name}'s SKILL.md never names guidance.md, so "
                "the prose that left the body is unreachable from it."
            )
            return 1
        if "executor_tier" not in body:
            report(
                f"{label}: {guidance.parent.name}'s SKILL.md names guidance.md "
                "without the condition under which it is read, which leaves the "
                "skip to the executor's own judgement — the judgement #135 says "
                "it gets most wrong."
            )
            return 1
        if "high" not in body:
            report(
                f"{label}: {guidance.parent.name}'s SKILL.md does not name the "
                "tier that skips the read, so the condition it states cannot be "
                "evaluated."
            )
            return 1
        # "Measurably smaller than before the split" is checkable only as a
        # property of what is on disk now: the guidance carries real content,
        # and that content is no longer duplicated in the body it left.
        if len(text) < 500:
            report(
                f"{label}: {guidance.parent.name}'s guidance.md holds "
                f"{len(text)} bytes, too few for the split to have moved "
                "anything; a pointer to an almost-empty file costs a read and "
                "saves nothing."
            )
            return 1
        criterion = guidance_criterion_problem(guidance.parent.name, text)
        if criterion:
            report(f"{label}: {criterion}")
            return 1
        for heading in [
            line for line in text.splitlines() if line.startswith("## ")
        ]:
            if heading in body:
                report(
                    f"{label}: {guidance.parent.name}'s body still carries "
                    f"{heading!r}, so the section was copied rather than moved "
                    "and the resident cost did not fall."
                )
                return 1

    # M2 — the property is held by the suite, not promised by the design. A
    # guidance file that stated a criterion would let the tier skip one, which
    # would make `executor_tier: high` a relaxation of the gates wearing a
    # capability label. Planting one is the only way to know the rule fires.
    sample = guidance_files[0]
    planted = (
        sample.read_text(encoding="utf-8")
        + "\nAn executor MUST record the fingerprint before implementing.\n"
    )
    problem = guidance_criterion_problem(sample.parent.name, planted)
    if not problem:
        report(
            f"{label}: states a criterion — a guidance file carrying `MUST` was "
            "accepted, so nothing stops a criterion from moving into the file "
            "the tier skips."
        )
        return 1
    if sample.parent.name not in problem:
        report(
            f"{label}: the refusal does not name the file that states the "
            f"criterion; got {problem!r}."
        )
        return 1
    if "MUST" not in problem:
        report(
            f"{label}: the refusal does not name the word it objected to, so the "
            f"author has to guess which sentence to move; got {problem!r}."
        )
        return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_native_projections_removed_scenario() -> int:
    """Issue #414: Keel projects no goal, helper, task view, or subagent brief.

    The owner removed the tooling built for the stance that subagents and native
    goals had to be shaped by Keel. Each surface is checked from the outside: the
    command a model would type, the doctor line it would read, and the plugin
    files a host would load. `keel project --event startup` is the control —
    a `keel project` that refused everything would pass the rest.
    """
    label = "native-projections-removed"
    with tempfile.TemporaryDirectory(prefix="keel-414-", ignore_cleanup_errors=True) as raw:
        repo = Path(raw)
        init = run_keel(repo, "--init", "--target", "claude")
        if init.returncode != 0:
            report(f"{label}: keel --init failed: {(init.stderr or init.stdout).strip()}")
            return 1
        for args in (
            ("project", "goal"),
            ("project", "tasks"),
            ("project", "helper"),
            ("project", "--event", "subagent-start"),
        ):
            result = run_keel(repo, *args)
            said = (result.stdout + result.stderr).lower()
            if result.returncode == 0:
                report(f"{label}: keel {' '.join(args)} exited 0.")
                return 1
            if "unknown" not in said and "unsupported" not in said:
                report(f"{label}: keel {' '.join(args)} was not refused as unknown: {(result.stdout or result.stderr).strip()[:120]!r}")
                return 1
        control = run_keel(repo, "project", "--event", "startup", "--target", "claude")
        if control.returncode != 0:
            report(f"{label}: keel project --event startup no longer works: {(control.stderr or control.stdout).strip()}")
            return 1
        doctor = run_keel(repo, "--doctor", "--target", "claude")
        for prefix in ("execution.goal", "execution.task-view", "delegation.", "helper "):
            hit = [line for line in doctor.stdout.splitlines() if line.strip().startswith(prefix)]
            if hit:
                report(f"{label}: doctor still prints {hit[0].strip()!r}.")
                return 1
    for gone in (
        ROOT / PLUGIN_ROOT / "skills/keel-run-single-task-goal",
        ROOT / "src/skills/keel-run-single-task-goal",
        ROOT / PLUGIN_ROOT / "agents",
    ):
        if gone.exists():
            report(f"{label}: {gone.relative_to(ROOT)} still ships.")
            return 1
    for manifest in (ROOT / ".claude-plugin/plugin.json", ROOT / PLUGIN_ROOT / ".codex-plugin/plugin.json"):
        if "agents" in json.loads(manifest.read_text(encoding="utf-8")):
            report(f"{label}: {manifest.relative_to(ROOT)} still names agents.")
            return 1
    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


NATIVE_CAPABILITY_SUPPRESSIONS = (
    "unbounded subagent",
    "bounded helpers return read-only",
    "Implementation delegation is refused",
    "Delegation is refused with no active guard",
    "Target-native subagent gate",
    "One agent owns decisions",
    "may help with bounded assessment",
    "goal/task-view projection requires explicit authorization",
    "small contiguous task group",
    "in the current agent conversation",
    "inside the current agent session",
    "never infer continuity",
    "never native memory",
    "at most 2 attempts",
    "Read only the documents needed",
    "minimal read list",
    "load only that one",
    "do not load unrelated lenses",
    "read only the returned paths",
)


NATIVE_SUBAGENT_SENTENCE = "the model's choice and is treated as the main agent is"


NATIVE_CONTINUATION_SENTENCE = "approved `tasks.md` in order"


def validate_native_capabilities_unrestricted_scenario() -> int:
    """Issue #414: Keel neither suppresses nor steers the host's native capabilities.

    The owner reviewed each sentence that told the model to stay in one session,
    take one task, keep subagents to a read-only role, read a minimal list, or
    stop after two attempts, and removed them. This holds every one of them out
    of every model-facing surface, and requires the two sentences that replaced
    the subagent and continuation rules where the agent reads them first.
    """
    label = "native-capabilities-unrestricted"
    surfaces = [
        ROOT / "AGENTS.md",
        ROOT / "assets/bootstrap/AGENTS.md",
        ROOT / "assets/openspec/schemas/keel-spec-driven/schema.yaml",
        ROOT / "openspec/schemas/keel-spec-driven/schema.yaml",
    ]
    for name in ("apply-change", "archive-change", "sync-specs", "propose"):
        surfaces.append(ROOT / f".claude/skills/openspec-{name}/SKILL.md")
        surfaces.append(ROOT / f".codex/skills/openspec-{name}/SKILL.md")
    surfaces.extend(sorted((ROOT / "src/skills").glob("*/SKILL.md")))
    surfaces.extend(sorted((ROOT / PLUGIN_ROOT / "skills").glob("*/SKILL.md")))
    for surface in surfaces:
        if not surface.is_file():
            report(f"{label}: {surface.relative_to(ROOT)} is missing, so it cannot be checked.")
            return 1
        text = surface.read_text(encoding="utf-8")
        for phrase in NATIVE_CAPABILITY_SUPPRESSIONS:
            if phrase in text:
                report(f"{label}: {surface.relative_to(ROOT)} still says {phrase!r}.")
                return 1
    for first_read in (
        ROOT / "AGENTS.md",
        ROOT / "assets/bootstrap/AGENTS.md",
        ROOT / ".claude/skills/openspec-apply-change/SKILL.md",
        ROOT / ".codex/skills/openspec-apply-change/SKILL.md",
    ):
        text = first_read.read_text(encoding="utf-8")
        if NATIVE_SUBAGENT_SENTENCE not in text:
            report(f"{label}: {first_read.relative_to(ROOT)} does not say a subagent is {NATIVE_SUBAGENT_SENTENCE!r}.")
            return 1
        if NATIVE_CONTINUATION_SENTENCE not in text:
            report(f"{label}: {first_read.relative_to(ROOT)} does not say the agent works through an {NATIVE_CONTINUATION_SENTENCE!r}.")
            return 1
    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


# Sentences the surfaces said after the code stopped saying them (#413).
STALE_SURFACE_SENTENCES = (
    "Owner is the current Keel agent",
    "retry counting",
    "Keel Hook completion gate",
    "unless Touch authorizes diagnostics",
    "explicitly allows it",
    "without explicit authorization",
    "Commands prove Acceptance",
    "Acceptance, Commands, and Stop/Autonomy",
    "not a failed attempt",
    "skills and agents after",
    "Invoke OpenSpec through",
    "Remote Control off, the wake task",
)


def validate_surfaces_agree_with_code_scenario() -> int:
    """Issue #413: what the model reads states what the code does.

    #414 removed the protocol's old stance and the capsule kept it: every
    task-start still printed "must not continue to another task". The other
    sentences here contradicted the code they describe — a diagnose-only task
    the parser refuses unless its Touch is `none`, a completion hook no plugin
    declares, an authorization list ten names long beside a code list of
    thirteen. The names are read from `src/core/config.js`, so a name added
    later without its spec line fails here.
    """
    label = "surfaces-agree-with-code:"
    with tempfile.TemporaryDirectory(prefix="keel-surfaces-413-") as raw:
        repo = Path(raw)
        write_text(repo / "openspec/changes/demo/tasks.md", task_capsule_compact_fixture())
        started = run_keel(repo, "gate", "task-start", "--change", "demo", "--task", "1.1", "--no-guard", "--json")
        if started.returncode != 0:
            report(f"{label} task-start refused the compact fixture.")
            report((started.stderr or started.stdout).strip())
            return 1
        capsule = json.loads(started.stdout).get("contract", {}).get("capsule", {})
        if "owner" in capsule:
            report(f"{label} a task that authors no Owner compiled to owner {capsule['owner']!r}.")
            return 1
        kept = ["must not change Acceptance", "must not commit", "must not push", "must not sync or archive"]
        if capsule.get("prohibitions") != kept:
            report(f"{label} the capsule prohibits {capsule.get('prohibitions')!r}, not {kept!r}.")
            return 1

    overlays = []
    for name in ("apply-change", "archive-change", "sync-specs"):
        overlays.append(ROOT / f".claude/skills/openspec-{name}/SKILL.md")
        overlays.append(ROOT / f".codex/skills/openspec-{name}/SKILL.md")
    schemas = [
        ROOT / "assets/openspec/schemas/keel-spec-driven",
        ROOT / "openspec/schemas/keel-spec-driven",
    ]
    required = {
        ROOT / "AGENTS.md": [
            "with `Touch: none` and no worktree writes",
            "a standing authorization in `keel/config.yaml` allows it",
            "`Verify` checks MUST verify",
        ],
        ROOT / "assets/bootstrap/AGENTS.md": [
            "No commit, push, sync, or archive unless the task, the owner, or `keel/config.yaml` authorizes it.",
        ],
        ROOT / "src/skills/debug-failure/SKILL.md": ["expected rather than a stop"],
        ROOT / PLUGIN_ROOT / "skills/debug-failure/SKILL.md": ["expected rather than a stop"],
        ROOT / "bin/keel.js": [],
        ROOT / "src/core/config.js": [],
    }
    for schema in schemas:
        required[schema / "schema.yaml"] = [
            "equivalence (which also declares `Base:` and `Fields:`)",
            "`Resolved here:`",
            "No hook gates completion",
        ]
        required[schema / "templates/tasks.md"] = ["equivalence", '"Resolved here:"']
    for overlay in overlays:
        required[overlay] = ["Invoke the OpenSpec CLI as `keel openspec"]
        if "apply" in overlay.as_posix():
            required[overlay].append("Verify checks prove Acceptance")
    for surface, sentences in required.items():
        if not surface.is_file():
            report(f"{label} {surface.relative_to(ROOT)} is missing, so it cannot be checked.")
            return 1
        text = surface.read_text(encoding="utf-8")
        for phrase in STALE_SURFACE_SENTENCES:
            if phrase in text:
                report(f"{label} {surface.relative_to(ROOT)} still says {phrase!r}.")
                return 1
        for sentence in sentences:
            if sentence not in text:
                report(f"{label} {surface.relative_to(ROOT)} does not say {sentence!r}.")
                return 1
        if surface in overlays and text.count("keel openspec …") != 1:
            report(f"{label} {surface.relative_to(ROOT)} tells the agent to use `keel openspec` {text.count('keel openspec …')} times, not once.")
            return 1

    help_text = run_keel(ROOT, "--help").stdout
    for command in ("keel patrol", "keel tick"):
        if command not in help_text:
            report(f"{label} keel --help does not name {command!r}.")
            return 1
    chat_help = run_keel(ROOT, "chat", "help").stdout
    if "post-tool-use" not in chat_help:
        report(f"{label} keel chat help does not name the post-tool-use hook.")
        return 1

    config = (ROOT / "src/core/config.js").read_text(encoding="utf-8")
    declared = re.search(r"const STANDING_AUTHORIZATION_ACTIONS = \[(.*?)\];", config, re.S)
    names = re.findall(r'^\s*"([a-z-]+)",', declared.group(1), re.M) if declared else []
    if len(names) < 13:
        report(f"{label} read {len(names)} standing-authorization names from config.js; expected at least 13.")
        return 1
    standing = (ROOT / "openspec/specs/keel-standing-authorization/spec.md").read_text(encoding="utf-8")
    vocabulary = re.search(r"(?s)### Requirement: A repository declares standing authorization in a closed vocabulary\n(.*?)\n#### ", standing)
    if not vocabulary:
        report(f"{label} keel-standing-authorization has no closed-vocabulary requirement to read.")
        return 1
    for name in names:
        if f"`{name}`" not in vocabulary.group(1):
            report(f"{label} keel-standing-authorization does not list `{name}` in its closed vocabulary.")
            return 1
    for spec, phrase in (
        ("keel-domain-lenses", "reads only the lens"),
        ("keel-domain-lenses", "no other lens is loaded"),
        ("keel-task-capsule", "current-agent ownership"),
    ):
        if phrase in (ROOT / f"openspec/specs/{spec}/spec.md").read_text(encoding="utf-8"):
            report(f"{label} {spec} still says {phrase!r}.")
            return 1
    if label.rstrip(":") not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report(f"{label.rstrip(':')} scenario passed.")
    return 0


COUNT_WORDS = {13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen"}


def readme_cli_problem(readme: Path, exit_label: str, count_phrase) -> str | None:
    """What a README fails to state about the CLI, or None (#413).

    Every list is read from the CLI or the code, so a command, flag, or
    authorization name added later without its README line fails here.
    """
    text = readme.read_text(encoding="utf-8")
    usage = run_keel(ROOT, "--help").stdout.split("Usage:", 1)[-1].split("\n\n", 1)[0]
    commands = sorted(set(re.findall(r"^\s*keel ([a-z][a-z-]*)", usage, re.M)))
    flags = sorted(set(re.findall(r"(?<![\w-])(--[a-z][a-z-]*)", usage)))
    if len(commands) < 16 or len(flags) < 30:
        return f"read {len(commands)} commands and {len(flags)} flags from keel --help; expected at least 16 and 30."
    for command in commands:
        if f"keel {command}" not in text:
            return f"{readme.name} does not name `keel {command}`."
    for flag in flags:
        if not re.search(r"(?<![\w-])" + re.escape(flag) + r"(?![\w-])", text):
            return f"{readme.name} does not name `{flag}`."
    config = (ROOT / "src/core/config.js").read_text(encoding="utf-8")
    declared = re.search(r"const STANDING_AUTHORIZATION_ACTIONS = \[(.*?)\];", config, re.S)
    names = re.findall(r'^\s*"([a-z-]+)",', declared.group(1), re.M) if declared else []
    if len(names) < 13:
        return f"read {len(names)} standing-authorization names from config.js; expected at least 13."
    for name in names:
        if not re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", text):
            return f"{readme.name} does not name the standing authorization `{name}`."
    phrase = count_phrase(len(names))
    if phrase not in text:
        return f"{readme.name} does not say {phrase!r}, the count of names config.js accepts."
    # The line that lists them, wherever else the word appears in prose.
    exit_lines = [line for line in text.splitlines() if exit_label in line]
    if not exit_lines:
        return f"{readme.name} has no line containing {exit_label!r}."
    listed = max(exit_lines, key=lambda line: sum(f"`{code}`" in line for code in range(5)))
    for code in range(5):
        if f"`{code}`" not in listed:
            return f"{readme.name} does not describe exit code {code} on its {exit_label!r} line."
    return None


README_STALE_SENTENCES = (
    "skills and agents follow",
    "The eleven names",
    "load only that one lens",
    "(pick one task)",
    "`keel --init` writes only",
    "--doctor | --uninstall  [--target <t>] [--dry-run]",
    "full command and workflow reference",
)


def validate_readme_states_the_cli_scenario() -> int:
    """Issue #413: the English README states what the CLI does."""
    label = "readme-states-the-cli:"
    readme = ROOT / "README.md"
    problem = readme_cli_problem(readme, "Exit codes", lambda n: f"{COUNT_WORDS.get(n, n)} names")
    if problem:
        report(f"{label} {problem}")
        return 1
    text = readme.read_text(encoding="utf-8")
    for phrase in README_STALE_SENTENCES:
        if phrase in text:
            report(f"{label} README.md still says {phrase!r}.")
            return 1
    if label.rstrip(":") not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report(f"{label.rstrip(':')} scenario passed.")
    return 0


def validate_readme_zh_matches_english_scenario() -> int:
    """Issue #413: the Chinese README is the English one's counterpart.

    It was 355 lines against 1000 and lacked thirteen sections, while the
    English README called it the full reference. The command and name checks
    are the English ones; section parity is a heading count, the one
    structural measure that needs no translation table.
    """
    label = "readme-zh-matches-english:"
    zh = ROOT / "README.zh-CN.md"
    problem = readme_cli_problem(zh, "退出码", lambda n: f"{n} 个名字")
    if problem:
        report(f"{label} {problem}")
        return 1
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    chinese = zh.read_text(encoding="utf-8")
    for level in ("## ", "### "):
        counts = [
            sum(1 for line in text.splitlines() if line.startswith(level))
            for text in (english, chinese)
        ]
        if counts[0] != counts[1]:
            report(f"{label} README.md has {counts[0]} `{level.strip()}` headings and README.zh-CN.md has {counts[1]}.")
            return 1
    if "装配时的 `keel --init`" in chinese:
        report(f"{label} README.zh-CN.md still names `keel --init` as the one setup command.")
        return 1
    if label.rstrip(":") not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report(f"{label.rstrip(':')} scenario passed.")
    return 0


def validate_config_documents_in_declaration_order_scenario() -> int:
    """Issue #413: the configuration file documents what it says it documents.

    `CONFIG_DECLARATIONS` is "in the order the file documents them", and the
    file had drifted: owner_language first, patrol twice, executor_tier never.
    The order is read from the code, so a declaration added there without its
    block, or a block written out of place, fails here.
    """
    label = "config-documents-in-declaration-order:"
    source = (ROOT / "src/core/config.js").read_text(encoding="utf-8")
    declared = re.search(r"const CONFIG_DECLARATIONS = \[(.*?)\];", source, re.S)
    names = re.findall(r'^\s*"([a-z_]+)",', declared.group(1), re.M) if declared else []
    if len(names) < 12:
        report(f"{label} read {len(names)} declarations from config.js; expected at least 12.")
        return 1
    config = (ROOT / "keel/config.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r"^# ([a-z_]+) \(optional\):", config, re.M)
    if blocks != names:
        report(f"{label} keel/config.yaml documents {blocks}, not {names} in that order.")
        return 1
    if "`chat-reply`, and `push-protected` are the names" not in config:
        report(f"{label} keel/config.yaml's scoped-name sentence does not name `push-protected`.")
        return 1
    updating = (ROOT / "docs/updating.md").read_text(encoding="utf-8")
    if "skills and agents" in updating.lower():
        report(f"{label} docs/updating.md still says Claude reloads skills and agents.")
        return 1
    for needle in ("config.toml", "E404"):
        if needle not in updating:
            report(f"{label} docs/updating.md does not mention {needle!r}.")
            return 1
    for name in ("README.md", "README.zh-CN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        for phrase in ("A clear there keeps no title", "noticed expiry"):
            if phrase in text:
                report(f"{label} {name} still says {phrase!r}.")
                return 1
        if "keel chat help" not in text:
            report(f"{label} {name} does not point to `keel chat help` for the full chat command list.")
            return 1
    if label.rstrip(":") not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report(f"{label.rstrip(':')} scenario passed.")
    return 0


def validate_docs_zh_match_english_scenario() -> int:
    """Issue #413: each Chinese doc follows its English page.

    `docs/shift-change.zh-CN.md` had five sections against eight and never
    mentioned `keel patrol` or `keel tick`. Every Chinese page that exists is
    checked, so a new one is held from the day it is written.
    """
    label = "docs-zh-match-english:"
    pages = sorted((ROOT / "docs").glob("*.zh-CN.md"))
    if not pages:
        report(f"{label} found no docs/*.zh-CN.md to check.")
        return 1
    for zh_path in pages:
        en_path = zh_path.with_name(zh_path.name.replace(".zh-CN.md", ".md"))
        if not en_path.is_file():
            report(f"{label} {zh_path.name} has no English page {en_path.name}.")
            return 1
        en = en_path.read_text(encoding="utf-8").splitlines()
        zh = zh_path.read_text(encoding="utf-8").splitlines()
        for what, prefix in (("headings", "#"), ("code fences", "```")):
            counts = [sum(1 for line in lines if line.startswith(prefix)) for lines in (en, zh)]
            if counts[0] != counts[1]:
                report(f"{label} {en_path.name} has {counts[0]} {what} and {zh_path.name} has {counts[1]}.")
                return 1
        zh_text = "\n".join(zh)
        for command in sorted(set(re.findall(r"keel [a-z][a-z-]*", "\n".join(en)))):
            if command not in zh_text:
                report(f"{label} {zh_path.name} does not name `{command}`, which {en_path.name} names.")
                return 1
    slack = (ROOT / "docs/chat-slack-setup.zh-CN.md").read_text(encoding="utf-8")
    if "编辑和删除" not in slack:
        report(f"{label} chat-slack-setup.zh-CN.md does not say edits and deletions carry over.")
        return 1
    if label.rstrip(":") not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report(f"{label.rstrip(':')} scenario passed.")
    return 0


def validate_tdd_strategy_guide_scenario() -> int:
    """Issue #389: the skill an executor loads to plan its checks says how to choose.

    The strategy list is read from the parser, not repeated here, so a strategy
    added later without a selection row fails this scenario instead of passing
    a list that was never updated. The clauses are the ones the completion gate
    enforces; before #389 the skill named two of them and `AGENTS.md` the rest.
    """
    label = "tdd-strategy-guide"
    skill_dir = ROOT / "src/skills/tdd-or-test-first"
    plugin_dir = ROOT / PLUGIN_ROOT / "skills/tdd-or-test-first"
    guidance = skill_dir / "guidance.md"
    if not guidance.is_file():
        report(f"{label}: tdd-or-test-first has no guidance.md beside its SKILL.md.")
        return 1
    contract = (ROOT / "src/core/task-contract.js").read_text(encoding="utf-8")
    declared = re.search(
        r"const SUPPORTED_VERIFICATION_STRATEGIES = \[(.*?)\];", contract, re.S
    )
    if not declared:
        report(f"{label}: SUPPORTED_VERIFICATION_STRATEGIES not found in task-contract.js.")
        return 1
    strategies = re.findall(r'^\s*"([a-z-]+)",', declared.group(1), re.M)
    if len(strategies) < 7:
        report(f"{label}: read {len(strategies)} strategies from the parser; expected at least 7.")
        return 1
    rows = [
        line for line in guidance.read_text(encoding="utf-8").splitlines()
        if line.startswith("|")
    ]
    for strategy in strategies:
        if not any(f"`{strategy}`" in row for row in rows):
            report(f"{label}: no selection row for {strategy} in the guidance table.")
            return 1
    body = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    for clause in (
        "Fails with:",
        "Detects:",
        "Measured:",
        "(regression)",
        "deferred to C",
        "artifact",
    ):
        if clause not in body:
            report(f"{label}: the skill body does not name {clause!r}.")
            return 1
    if "what would make" not in body:
        report(f"{label}: the skill body does not say a strategy is chosen by what would make the Acceptance false.")
        return 1
    for name in ("SKILL.md", "guidance.md"):
        shipped = plugin_dir / name
        if not shipped.is_file():
            report(f"{label}: the plugin has no tdd-or-test-first/{name}.")
            return 1
        if portable_projection_bytes(shipped) != (skill_dir / name).read_bytes():
            report(f"{label}: the plugin's tdd-or-test-first/{name} diverges from the canonical source.")
            return 1
    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_external_agents_are_documented_scenario() -> int:
    """The command reaches the protocol, the READMEs, and the privacy policy.

    #219: an agent that never reads the README must still learn that external
    model CLIs are delegates with a compiled brief, so the bootstrap block and
    this repository's protocol name it. The privacy policy lists what leaves the
    machine, and handing a repository to codex or dsh is now one of those ways.
    """
    label = "external-agents-are-documented:"

    def flat(path: Path) -> str:
        return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))

    protocol = flat(ROOT / "AGENTS.md")
    if "keel agents brief" not in protocol:
        report(f"{label} AGENTS.md does not name `keel agents brief`.")
        return 1
    if "launches nothing" not in protocol:
        report(f"{label} AGENTS.md does not say Keel launches nothing.")
        return 1
    # The installed bootstrap spends its byte budget only on rules every session
    # uses; `external_agents:` is inert until declared, as delegation is, so it
    # reaches an agent where it is declared instead (D9).
    if "keel agents" in flat(ROOT / "assets/bootstrap/AGENTS.md"):
        report(f"{label} the bootstrap block names `keel agents`, spending its budget on a "
               "declaration that is inert until a project makes it.")
        return 1
    for path in (ROOT / "README.md", ROOT / "README.zh-CN.md"):
        text = path.read_text(encoding="utf-8")
        blocks = re.findall(r"```bash\n(.*?)```", text, re.S)
        if not any("keel agents" in block for block in blocks):
            report(f"{label} {path.name} lists no `keel agents` in a command block.")
            return 1
        yaml_blocks = re.findall(r"```yaml\n(.*?)```", text, re.S)
        example = next((block for block in yaml_blocks if "external_agents:" in block), "")
        if not example:
            report(f"{label} {path.name} shows no `external_agents:` example.")
            return 1
        for key in ("allow:", "egress_deny:"):
            if key not in example:
                report(f"{label} {path.name}'s external_agents example has no {key}.")
                return 1
    privacy = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")
    leaves = privacy.split("## What leaves your machine", 1)[-1].split("\n## ", 1)[0]
    if "External model CLIs" not in leaves:
        report(f"{label} PRIVACY.md does not list external model CLIs under what leaves the machine.")
        return 1

    report("external-agents-are-documented scenario passed.")
    return 0


def validate_review_checklist_conditional_checks_scenario() -> int:
    """Issue #411 rows 7 and 8 (owner, 2026-10-21): a short base checklist, conditions on demand.

    Four review-checklist sections apply only under a condition — a coupled
    task, a matching lens, a new or expanded skill, a plan-mode artifact — yet
    every activation read them. They live in `conditional-checks.md`, read
    when a condition applies. The handoff skill tells its override apart from
    the shift note, which selects no task.
    """
    label = "review-checklist-conditional-checks:"
    skill_dir = ROOT / "src/skills/review-checklist"
    base = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    conditional_path = skill_dir / "conditional-checks.md"
    if "conditional-checks.md" not in base:
        report(f"{label} the review checklist does not name conditional-checks.md.")
        return 1
    for condition in ("Coupling: required", "lens", "skill", "plan-mode"):
        if condition not in base.split("## Conditional checks", 1)[-1]:
            report(f"{label} the checklist's conditional-checks section does not name the {condition!r} condition.")
            return 1
    for moved in ("## Skill change review", "## Planning artifact funnel"):
        if moved in base:
            report(f"{label} the base checklist still holds {moved!r}, which applies only under a condition.")
            return 1
    lines = len(base.splitlines())
    if lines >= 80:
        report(f"{label} the base checklist is {lines} lines, not under 80.")
        return 1
    if not conditional_path.is_file():
        report(f"{label} conditional-checks.md is missing beside the checklist.")
        return 1
    conditional = conditional_path.read_text(encoding="utf-8")
    for needle in ("## Skill change review", "## Planning artifact funnel", "Coupling: required", "Execution and review checks"):
        if needle not in conditional:
            report(f"{label} conditional-checks.md does not hold {needle!r}.")
            return 1
    handoff = (ROOT / "src/skills/handoff/SKILL.md").read_text(encoding="utf-8")
    if "keel shift ready" not in handoff:
        report(f"{label} the handoff skill does not name the shift note's `keel shift ready`.")
        return 1
    if "selects no task" not in handoff:
        report(f"{label} the handoff skill does not say the shift note selects no task.")
        return 1
    if label.rstrip(":") not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report(f"{label.rstrip(':')} scenario passed: the base checklist is {lines} lines.")
    return 0

"""Keel validation: common (split from validate_plugin.py, #409)."""
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


ROOT = Path(__file__).resolve().parents[2]


# No scenario may reach the developer's real Claude Code or Codex: `keel
# --update` drives both through their own CLIs (#204), and a scenario that ran
# it unguarded updated the real plugins of whoever ran the suite. A scenario
# that wants a host plants a fake and names it in its own environment.
os.environ["KEEL_UPDATE_CLAUDE"] = str(Path(tempfile.gettempdir()) / "keel-suite-has-no-claude")


os.environ["KEEL_UPDATE_CODEX"] = str(Path(tempfile.gettempdir()) / "keel-suite-has-no-codex")


PACKAGE_VERSION = "5.186.0"


PROTOCOL_VERSION = "5.186.0"


LEGACY_MANAGED_START = "<!-- keel:start version=2.1 -->"


OPENSPEC_SCHEMA_NAME = "keel-spec-driven"


OPENSPEC_CONFIG_PATH = Path("openspec/config.yaml")


OPENSPEC_SCHEMA_ROOT = Path("openspec/schemas") / OPENSPEC_SCHEMA_NAME


OPENSPEC_SURFACE_OVERLAY_START = (
    f"<!-- keel:openspec-surface-overlay version={PROTOCOL_VERSION} -->"
)


OPENSPEC_SURFACE_OVERLAY_END = "<!-- keel:openspec-surface-overlay:end -->"


SKILL_TARGETS = {"claude", "codex", "opencode"}


HOOK_TARGETS = {"claude"}


AGENT_TARGETS: set[str] = set()


ADAPTER_TARGETS = {"claude", "codex", "opencode"}


AGENT_PROTOCOL_TARGETS = {"codex", "opencode"}


LEGACY_PROFILE_SKILLS = (
    "keel-profile-web",
    "keel-profile-hardware",
    "keel-profile-hardware-dsl",
)


SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


PORTABLE_SKILL_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}


MANAGED_START = f"<!-- keel:start version={PROTOCOL_VERSION} -->"


MANAGED_START_RE = re.compile(r"<!--\s*keel:start(?:\s+[^>]*)?\s*-->")


MANAGED_END = "<!-- keel:end -->"


TEMPLATE_CHECKSUM_PREFIX = "<!-- keel:content-sha256 "


TEMPLATE_CHECKSUM_SUFFIX = " -->"


# The installed bootstrap block's byte budget, asserted by `thin-native-install`
# and `delegation-resident-text`. Raised from 1024 to 1400 in 5.63.0 to carry the
# Full/Lite routing rule (#131), deliberately and in a diff.
#
# The reason has to live here, because the cap's purpose is that the budget is
# **not quietly spent later** — the adjective is the whole specification. A cap
# phrased that way is not a claim that the number is right forever; it is a claim
# that nobody moves it without a reader noticing. So a documented raise satisfies
# it and a bare larger constant does not.
#
# Why routing earned it, when delegation did not: delegation is inert until a
# project declares it, so a repository declaring nothing was already served by the
# sentence in the block. Routing is never inert — every session routes, declared
# or not — and it was the one durable rule with no gate, no command, and no
# declaration carrying it to the agent. The rejected alternative was compressing
# the existing bullets to fit under 1024, which would have gone green while paying
# for routing out of gate-discipline prose that was already earning its place.
#
# 1400 rather than a round 1536: the headroom is "current content plus one short
# clause", so the next addition has to argue for itself the way this one did.
#
# Raised from 1400 to 1700 in 5.187.0 for the memory rule (#416). The owner put
# memory hygiene into the protocol on 2026-10-21, and memory argues the way
# routing did: it is never inert. Any session may write to memory whether or not
# a project declares anything, and the bootstrap is the only text that reaches a
# consuming repository. The headroom is again current content plus one short
# clause.
BOOTSTRAP_BLOCK_BYTE_BUDGET = 1700


RESIDENT_BLOCKS = [
    {
        "name": "Bootstrap resident block",
        "path": "assets/bootstrap/AGENTS.md",
        "max_lines": 12,
        "required": [
            "Keel Bootstrap",
            "keel context",
            "OpenSpec artifacts and Git",
            "keel gate task-start",
            "task capsule",
            "fingerprint",
            # Prose, not a command: this sentence is the one that has actually
            # been reworded under byte pressure, so it is matched as a topic —
            # Touch and a `bound…` word in one statement. The other prose
            # entries stay literal until one of them needs the same freedom.
            re.compile(r"Touch\b[^\n]*\bbound", re.IGNORECASE),
            # #414: subagents are the model's choice, treated as the main agent.
            "treated as the main agent is",
            # #416: what memory may hold and when it is rechecked, as topics so
            # the sentence can be reworded under the byte budget.
            re.compile(r"memory[^\n]*repository cannot answer", re.IGNORECASE),
            re.compile(r"memory[^\n]*shift change", re.IGNORECASE),
            "native plugin",
            "keel --init",
            # Routing is the one durable rule with no gate behind it, so the
            # block is the only place it reaches a consuming repository (#131).
            # Matched as a topic: both modes named in one statement.
            re.compile(r"\bFull\b[^\n]*\bLite\b", re.IGNORECASE),
            "full_mode_paths",
        ],
    },
]


RESIDENT_FORBIDDEN_SNIPPETS = [
    "## Goal",
    "## Acceptance Criteria",
    "## Files To Read Next Session",
    "dry-run",
    "dry run",
    "for example",
]


SKILL_DOC_REQUIREMENTS = [
    {
        "name": "review-checklist skill",
        "path": "src/skills/keel-review-checklist/SKILL.md",
        "required": [
            "completion gates",
            "openspec-apply-change",
            "openspec-sync-specs",
            "openspec-archive-change",
            "## Context to read",
            "keel gate task-start",
            "task-complete",
            "change-close",
            "deterministic structure",
            "## Semantic Review",
            "`Acceptance check`",
            "`Scope check`",
            "`Findings`",
            "Resolved here:",
            "Durable owner:",
            "Discard reason:",
            "HANDOFF",
            "return-to-work",
            "critical expectation",
            "behavior evidence",
            "explicit discard reason",
            "evidence details",
            "## Skill change review",
            "authoritative sources",
            "provenance and license",
            "positive and negative trigger cases",
            "real-task evidence",
            "portable `SKILL.md`",
            "target-native discovery",
        ],
    },
    {
        "name": "handoff skill",
        "path": "src/skills/keel-handoff/SKILL.md",
        "required": [
            "Lite mode does not create HANDOFF",
            "not a durable follow-up owner",
            "## Context to read",
            "openspec/changes",
            "discard reason",
            "keel-handoff/v1",
            "schema",
            "owner",
            "action",
            "reason",
            "`active-backlog`",
            "`head=...`",
            "expectation state",
            "evidence details",
            "byte-for-byte",
            "keel context --clear-handoff",
            "## Standalone use",
        ],
    },
    {
        # Contract anchors traceable to keel-expectation-alignment; the
        # expectation-alignment-skill scenario owns the full structural and
        # cross-file behavioral checks, so this entry stays anchor-level.
        "name": "align-expectations skill",
        "path": "src/skills/keel-align-expectations/SKILL.md",
        "required": [
            "quick path",
            "deep path",
            "one material decision at a time",
            "recommended answer",
            "Silence does not",
            "keel/lenses/",
            "Applies when",
            "keel lenses add",
            "no separate alignment ledger",
        ],
    },
    {
        "name": "tdd-or-test-first skill",
        "path": "src/skills/keel-tdd-or-test-first/SKILL.md",
        "required": [
            "selected OpenSpec task",
            "acceptance criteria",
            "## Context to read",
            "## Standalone use",
            "Coupled-task preflight",
            "do not infer the missing decision",
        ],
    },
    {
        "name": "debug-failure skill",
        "path": "src/skills/keel-debug-failure/SKILL.md",
        "required": [
            "Follow-ups are limited to directly observed blockers, risks, missing scope, or escalation needs",
            "Do not include roadmap suggestions, new feature suggestions, unrelated architecture critique, or opportunistic refactor suggestions",
            "There is no fixed attempt count",
            "## Context to read",
            "## Standalone use",
            "candidate completion gate",
            "provisional failure",
        ],
    },
    {
        # Structure only ("Applies when" self-describing header, "Material risk
        # surface", "Execution and review checks"); the expectation-alignment-skill
        # scenario owns domain-keyword scoping across these three lens templates,
        # so the per-domain keywords are not duplicated here.
        "name": "web lens template",
        "path": "assets/lenses/web.md",
        "required": [
            "Applies when",
            "Material risk surface",
            "Execution and review checks",
        ],
    },
    {
        "name": "hardware lens template",
        "path": "assets/lenses/hardware.md",
        "required": [
            "Applies when",
            "Material risk surface",
            "Execution and review checks",
        ],
    },
    {
        "name": "hardware-dsl lens template",
        "path": "assets/lenses/hardware-dsl.md",
        "required": [
            "Applies when",
            "Material risk surface",
            "Execution and review checks",
        ],
    },
]


FORBIDDEN_SKILL_SNIPPETS = [
    "Source placeholder",
    "Full v2.1 protocol behavior is refined by later implementation issues",
]


def report(message: str) -> None:
    print(message)


# The runner's own source: the entry point and every module it imports (#409).
# A check that reads the runner's code reads all of it, because a check that
# read one file would go quiet about whatever moved out of it.
def validation_sources() -> list[Path]:
    return [ROOT / "scripts/validate_plugin.py", *sorted((ROOT / "scripts/validation").glob("*.py"))]


def validation_source_with(marker: str) -> tuple[Path, str, int] | None:
    """The source file containing `marker`, its text, and the marker's offset."""
    for path in validation_sources():
        text = path.read_text(encoding="utf-8")
        start = text.find(marker)
        if start >= 0:
            return path, text, start
    return None


def extract_managed_block(content: str) -> str | None:
    start_match = MANAGED_START_RE.search(content)
    if start_match is None:
        return None
    end = content.find(MANAGED_END, start_match.end())
    if end == -1:
        return None
    return content[start_match.start() : end + len(MANAGED_END)]


def template_checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def install_template_payload(content: str) -> str:
    return (
        content
        + f"{TEMPLATE_CHECKSUM_PREFIX}{template_checksum(content)}"
        + TEMPLATE_CHECKSUM_SUFFIX
        + "\n"
    )


def strip_template_checksum(content: str) -> tuple[str, str | None]:
    lines = content.splitlines(keepends=True)
    checksum: str | None = None
    kept: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(TEMPLATE_CHECKSUM_PREFIX) and stripped.endswith(
            TEMPLATE_CHECKSUM_SUFFIX
        ):
            checksum = stripped[
                len(TEMPLATE_CHECKSUM_PREFIX) : -len(TEMPLATE_CHECKSUM_SUFFIX)
            ]
            continue
        kept.append(line)
    return "".join(kept), checksum


def validate_resident_blocks(errors: list[str], root: Path = ROOT) -> None:
    for block in RESIDENT_BLOCKS:
        path = root / block["path"]
        if not path.is_file():
            errors.append(f"{block['name']} is missing: {block['path']}")
            continue

        content = path.read_text(encoding="utf-8")
        managed_block = extract_managed_block(content)
        if managed_block is None:
            errors.append(
                f"{block['name']} must contain keel managed block markers"
            )
            continue
        if MANAGED_START not in managed_block:
            errors.append(
                f"{block['name']} must declare managed block version {PROTOCOL_VERSION}"
            )
            continue

        line_count = len(managed_block.splitlines())
        max_lines = int(block["max_lines"])
        if line_count > max_lines:
            errors.append(
                f"{block['name']} has {line_count} managed-block lines; "
                f"budget is {max_lines}"
            )

        # A required entry is one of two kinds, and they mean different things.
        # A literal names a command, marker, or identifier: if the block no
        # longer contains it exactly, it is telling a reader to run something
        # that does not exist, so the check must fail. A pattern states a topic
        # in prose: the concepts must remain, the wording may move — which it
        # must be free to, because this block is under a line and byte budget
        # and gets rewritten to fit.
        for required in block["required"]:
            if isinstance(required, str):
                if required not in managed_block:
                    errors.append(
                        f"{block['name']} missing required literal: {required}"
                    )
            elif not required.search(managed_block):
                errors.append(
                    f"{block['name']} missing required topic: "
                    f"{required.pattern}"
                )

        lowered = managed_block.lower()
        for forbidden in RESIDENT_FORBIDDEN_SNIPPETS:
            if forbidden.lower() in lowered:
                errors.append(
                    f"{block['name']} includes forbidden resident-block content: "
                    f"{forbidden}"
                )


def validate_openspec_schema(errors: list[str]) -> None:
    source_root = ROOT / "assets" / "openspec" / "schemas" / OPENSPEC_SCHEMA_NAME
    required_files = [
        "schema.yaml",
        "templates/proposal.md",
        "templates/spec.md",
        "templates/design.md",
        "templates/tasks.md",
    ]

    for relative in required_files:
        if not (source_root / relative).is_file():
            errors.append(
                "OpenSpec source schema missing file: "
                f"{source_root.relative_to(ROOT).as_posix()}/{relative}"
            )

    schema_path = source_root / "schema.yaml"
    tasks_template_path = source_root / "templates" / "tasks.md"
    if schema_path.is_file():
        schema = schema_path.read_text(encoding="utf-8")
        for required in (
            f"name: {OPENSPEC_SCHEMA_NAME}",
            "description: Keel OpenSpec workflow",
            "apply:",
            "openspec-apply-change",
            "keel-review-checklist",
            "Mode",
            "Covers",
            "Read",
            "Touch",
            "Commands",
            "Acceptance",
            "Coupling",
            "Candidate Boundary",
            "Stop Rules",
            "Evidence",
            "Stop if",
            "Report",
            "Execution recommendation",
            "Autonomy boundary",
            "A subagent is the model's choice and is treated as the main agent is",
            "approved `tasks.md` in order",
            "Modify only files listed under Touch",
            "reading does not expand write authority",
            "Out-of-scope Need",
            "unresolved follow-ups must be owned",
            "Task Authoring Gate",
            "Slice Start Gate",
            "source expectations",
            "Rough future slices",
            "new or materially expanded dedicated skill",
            "authoritative sources",
            "provenance and license",
            "positive and negative trigger cases",
            "real-task evidence",
            "one of pass, passed, complete, completed, ok, or done.",
            "## Expectation Coverage",
            "carry a disposition",
            "`Resolved here:`",
        ):
            if required not in schema:
                errors.append(f"OpenSpec schema.yaml missing required language: {required}")

    if tasks_template_path.is_file():
        tasks_template = tasks_template_path.read_text(encoding="utf-8")
        for required in (
            "- [ ]",
            "keel-task-capsule/v1",
            "Covers:",
            "Touch:",
            "Verify:",
            "Strategy:",
            "M1:",
            "Evidence:",
            "- Contract: pending",
            "Review:",
            "Status: pending",
            "Status: one of pass, passed, complete, completed, ok, done",
            "Blocker: none",
            "Mode: diagnose-only",
            "Requires modifying files outside Touch.",
            "## Expectation Coverage",
            "Discard reason:",
        ):
            if required not in tasks_template:
                errors.append(
                    f"OpenSpec tasks.md template missing required language: {required}"
                )
        stripped_template = re.sub(r"<!--[\s\S]*?-->", "", tasks_template)
        for forbidden in (
            "Owner: keel-agent",
            "Mode: implementation",
            "- Read:",
            "- Commands:",
            "- Acceptance:",
            "- Execution recommendation:",
            "- Rationale:",
            "- Autonomy boundary:",
            "- Coupling:",
            "- Candidate Boundary:",
            "- Stop Rules:",
            "- Stop if:",
            "- Report:",
        ):
            if forbidden in stripped_template:
                errors.append(
                    "OpenSpec tasks.md template repeats an invariant default: "
                    f"{forbidden}"
                )


    # A source-versus-dist comparison stood here, but `dist_root` was assigned
    # `source_root`, so it diffed a directory against itself and could not fail.
    # The pair that really needs comparing — this packaged copy against the
    # repo-local one OpenSpec resolves — is asserted by
    # `invalidation-authoring-surface`.


def validate_skill_docs(errors: list[str]) -> None:
    for path in sorted((ROOT / "src" / "skills").glob("*/SKILL.md")):
        content = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_SKILL_SNIPPETS:
            if forbidden in content:
                errors.append(
                    f"{path.relative_to(ROOT).as_posix()} contains placeholder language: {forbidden}"
                )

    for skill in SKILL_DOC_REQUIREMENTS:
        path = ROOT / skill["path"]
        if not path.is_file():
            errors.append(f"{skill['name']} is missing: {skill['path']}")
            continue

        content = path.read_text(encoding="utf-8")
        for required in skill["required"]:
            if required not in content:
                errors.append(f"{skill['name']} missing required language: {required}")


def parse_skill_frontmatter(path: Path, errors: list[str]) -> dict[str, str]:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    if not lines or lines[0] != "---":
        errors.append(f"{path.as_posix()} must start with YAML frontmatter")
        return {}
    try:
        end = lines.index("---", 1)
    except ValueError:
        errors.append(f"{path.as_posix()} has unterminated YAML frontmatter")
        return {}

    fields: dict[str, str] = {}
    block_key: str | None = None
    for line in lines[1:end]:
        if not line:
            continue
        if line.startswith((" ", "\t")):
            if block_key:
                fields[block_key] = f"{fields[block_key]} {line.strip()}".strip()
            continue
        if ":" not in line:
            errors.append(f"{path.as_posix()} has invalid frontmatter line: {line}")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        block_key = key if value in {"|", ">"} else None
        fields[key] = "" if block_key else value.strip("'\"")
    return fields


def validate_skill_portability(root: Path, errors: list[str]) -> None:
    source_root = root / "src" / "skills"
    plugin_root = root / "plugins" / "keel" / "skills"
    if not source_root.is_dir():
        errors.append("skill portability requires src/skills canonical authority")
        return

    source_names = {path.name for path in source_root.iterdir() if path.is_dir()}
    for name in sorted(source_names):
        skill_dir = source_root / name
        skill_path = skill_dir / "SKILL.md"
        if not skill_path.is_file():
            errors.append(f"missing canonical skill: {skill_path.as_posix()}")
            continue
        fields = parse_skill_frontmatter(skill_path, errors)
        field_name = fields.get("name", "")
        description = fields.get("description", "")
        if field_name != name or not SKILL_NAME_RE.fullmatch(field_name):
            errors.append(
                f"canonical skill name must match its portable directory: {name}"
            )
        if not description or len(description) > 1024:
            errors.append(
                f"canonical skill description must be 1-1024 characters: {name}"
            )
        trigger_markers = ("use when", "when ", "before ")
        if not any(marker in description.lower() for marker in trigger_markers):
            errors.append(
                f"canonical skill description must state when it applies: {name}"
            )
        unknown = sorted(set(fields) - PORTABLE_SKILL_FIELDS)
        if unknown:
            errors.append(
                f"canonical skill uses non-portable frontmatter fields: "
                f"{name}: {', '.join(unknown)}"
            )
        content = skill_path.read_text(encoding="utf-8")
        references = re.findall(
            r"(?:\]\(|`)((?:references|scripts|assets)/[A-Za-z0-9_./-]+)(?:\)|`)",
            content,
        )
        for reference in sorted(set(references)):
            resource_path = (skill_path.parent / Path(reference)).resolve()
            try:
                resource_path.relative_to(skill_path.parent.resolve())
            except ValueError:
                errors.append(
                    f"canonical skill reference escapes its skill directory: "
                    f"{name}: {reference}"
                )
                continue
            if not resource_path.is_file():
                errors.append(
                    f"canonical skill has missing referenced resource: "
                    f"{name}: {reference}"
                )

        projection = plugin_root / name
        if not projection.is_dir():
            errors.append(
                f"canonical skill has missing native plugin projection: {name}"
            )
            continue
        source_files = {
            path.relative_to(skill_dir).as_posix(): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(skill_dir.rglob("*"))
            if path.is_file()
        }
        projection_files = {
            path.relative_to(projection).as_posix(): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(projection.rglob("*"))
            if path.is_file()
        }
        if source_files != projection_files:
            errors.append(
                f"native plugin skill projection differs from canonical source: "
                f"{name}"
            )

    if plugin_root.is_dir():
        for plugin_skill in sorted(
            path for path in plugin_root.iterdir() if path.is_dir()
        ):
            if plugin_skill.name not in source_names:
                errors.append(
                    f"native plugin skill has no canonical source: "
                    f"{plugin_skill.name}"
                )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def snapshot_files(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            snapshot[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8")
    return snapshot


def packaged_openspec_schema_install_paths(root: Path | None = None) -> list[str]:
    # The root the installer itself reads (install_to_repo.openspec_schema_actions),
    # which raises on the same condition. A validator that answered `[]` here left
    # six install/uninstall/clear assertions iterating nothing and reporting pass.
    schema_root = root if root is not None else (
        ROOT / "assets" / "openspec" / "schemas" / OPENSPEC_SCHEMA_NAME
    )
    if not schema_root.is_dir():
        raise FileNotFoundError(
            f"packaged OpenSpec schema root is missing: {schema_root}"
        )

    return [
        (OPENSPEC_SCHEMA_ROOT / path.relative_to(schema_root)).as_posix()
        for path in sorted(schema_root.rglob("*"))
        if path.is_file()
    ]


def run_keel(
    cwd: Path,
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", str(ROOT / "bin" / "keel.js"), *args],
        cwd=cwd,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def mailbox_repository(root: Path) -> Path:
    """A committed scratch repository whose mailbox tests can add worktrees."""
    root.mkdir(parents=True, exist_ok=True)
    for args in (
        ["init", "-q", "-b", "main"],
        ["config", "user.email", "keel@example.invalid"],
        ["config", "user.name", "Keel Validation"],
        ["commit", "-q", "--allow-empty", "-m", "seed"],
    ):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
    return root


def mailbox_common_dir(repo: Path) -> Path:
    raw = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=repo, check=True, capture_output=True, text=True,
    ).stdout.strip()
    return Path(raw)


CHAT_ROLE_VARIABLES = ("KEEL_CHAT_ROLE", "KEEL_MAIL_ROLE")


# The desktop app's session markers (#319 D5): a run inside it must not change
# what shift scenarios see.
DESKTOP_HOST_VARIABLES = ("CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_HOST_SESSION_ID", "CLAUDE_CODE_SESSION_ID", "CLAUDE_PID")


def chat_environment(**extra: str) -> dict[str, str]:
    """The test process's environment without any inherited chat role or desktop host."""
    env = {
        key: value for key, value in os.environ.items()
        if key not in CHAT_ROLE_VARIABLES and key not in DESKTOP_HOST_VARIABLES
    }
    env.update(extra)
    return env


def chat_worktree(repo: Path, path: Path) -> Path:
    subprocess.run(
        ["git", "worktree", "add", "-q", "-b", path.name, str(path)],
        cwd=repo, check=True, capture_output=True,
    )
    return path


def chat_log(repo: Path, group: str) -> Path:
    return mailbox_common_dir(repo) / "keel-chat" / "groups" / group / "log"


def chat_json(result: subprocess.CompletedProcess[str]) -> dict:
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def chat_scratch_group(base: Path) -> tuple[Path, Path, dict[str, str]]:
    """A repository with `rtl` and a `verify` worktree sharing group `soc`."""
    rtl = mailbox_repository(base / "rtl")
    verify = chat_worktree(rtl, base / "verify")
    env = chat_environment()
    for cwd, role in ((rtl, "rtl"), (verify, "verify")):
        run_keel(cwd, "chat", "role", "--set", role, env=env)
    run_keel(rtl, "chat", "group", "create", "soc", "--member", "verify", env=env)
    return rtl, verify, env


def host_project_name(directory: Path) -> str:
    """The host's project directory name for a working directory (Claude Code's sanitizing)."""
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.realpath(directory))


def chat_session_start(cwd: Path, env: dict, session: str, pid: int, source: str = "startup",
                       transcript: Path | None = None) -> subprocess.CompletedProcess:
    payload = {"cwd": str(cwd), "hook_event_name": "SessionStart", "session_id": session, "source": source}
    if transcript is not None:
        payload["transcript_path"] = str(transcript)
    return subprocess.run(["node", str(ROOT / "bin" / "keel.js"), "chat", "hook", "session-start"], cwd=cwd, text=True,
                          capture_output=True, check=False, input=json.dumps(payload),
                          env={**env, "CLAUDE_CODE_ENTRYPOINT": "cli", "CLAUDE_CODE_SESSION_ID": session, "CLAUDE_PID": str(pid)})


def chat_logs_snapshot(repo: Path) -> dict:
    groups = mailbox_common_dir(repo) / "keel-chat" / "groups"
    return {str(p): p.read_bytes() for p in groups.rglob("*") if p.is_file()}


def chat_records_with(repo: Path, group: str, needle: str) -> list[str]:
    """Record files in `group` whose text contains `needle`."""
    log = chat_log(repo, group)
    if not log.is_dir():
        return []
    return [p.read_text(encoding="utf-8") for p in sorted(log.glob("*.md")) if needle in p.read_text(encoding="utf-8")]


def shift_scratch(base: Path) -> tuple[Path, Path, dict, Path]:
    """`rtl` and `verify` worktrees pushed to a bare remote, for shift scenarios."""
    rtl, verify, env = chat_scratch_group(base)
    remote = base / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=rtl, check=True, capture_output=True)
    for tree in (rtl, verify):
        subprocess.run(["git", "push", "-q", "-u", "origin", "HEAD"], cwd=tree, check=True, capture_output=True)
    return rtl, verify, env, remote


FAKE_CODEX = r"""#!/usr/bin/env node
const fs = require("fs");
let input = "";
try { input = fs.readFileSync(0, "utf8"); } catch {}
fs.appendFileSync(process.env.FAKE_CODEX_LOG, JSON.stringify({ argv: process.argv.slice(2), cwd: process.cwd(), stdin: input }) + "\n");
console.log(JSON.stringify({ type: "thread.started", thread_id: "thread-fake-1" }));
console.log(JSON.stringify({ type: "turn.completed" }));
"""


def chat_wake_scratch(base: Path) -> tuple[Path, Path, dict[str, str], Path]:
    """`rtl` and a `cx` worktree sharing `lab` and `other`; `cx` declares chat-reply:lab.

    Returns the two worktrees, an environment whose KEEL_HOME, launchctl,
    LaunchAgents directory, and Codex executable are scratch doubles, and the
    file the fake Codex appends one JSON line per turn to.
    """
    rtl = mailbox_repository(base / "rtl")
    cx = chat_worktree(rtl, base / "cx")
    write_text(cx / "keel" / "config.yaml", "authorize:\n  - chat-reply:lab\n")
    subprocess.run(["git", "add", "keel/config.yaml"], cwd=cx, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", "chat-reply"], cwd=cx, check=True, capture_output=True)
    calls = base / "codex-calls.jsonl"
    codex = base / "fake-codex"
    write_text(codex, FAKE_CODEX)
    codex.chmod(0o755)
    launchctl = base / "launchctl"
    write_text(launchctl, f'#!/bin/sh\necho "$@" >> "{base / "launchctl-calls"}"\nexit 0\n')
    launchctl.chmod(0o755)
    env = chat_environment(
        KEEL_HOME=str(base / "home"),
        KEEL_CHAT_CODEX=str(codex),
        FAKE_CODEX_LOG=str(calls),
        KEEL_CHAT_LAUNCHCTL=str(launchctl),
        KEEL_CHAT_LAUNCH_AGENTS_DIR=str(base / "agents"),
    )
    run_keel(rtl, "chat", "role", "--set", "rtl", env=env)
    run_keel(cx, "chat", "role", "--set", "cx", env=env)
    run_keel(rtl, "chat", "group", "create", "lab", "--member", "cx", env=env)
    run_keel(rtl, "chat", "group", "create", "other", "--member", "cx", env=env)
    return rtl, cx, env, calls


def gate_task(
    *,
    checked: bool,
    coupling: str,
    missing_field: str | None = None,
    evidence: str = (
        "    - M1: passed\n"
        "    - Review:\n"
        "      - Status: pass\n"
        "      - Acceptance check: reviewed\n"
        "      - Scope check: reviewed\n"
        "      - Findings: none\n"
        "    - Blocker: none"
    ),
) -> str:
    fields = {
        "Owner": "claude",
        "Mode": "implementation",
        "Covers": "\n    - E1: hook behavior",
        "Read": "\n    - openspec/changes/demo/proposal.md",
        "Touch": "\n    - src/example.js",
        "Verification Strategy": "evidence-first",
        "Verification Reason": "this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first",
        "Commands": "\n    - M1: npm test",
        "Acceptance": "the required command succeeds",
        "Execution recommendation": "Claude Code implementation note (advisory)",
        "Rationale": "bounded implementation work",
        "Autonomy boundary": "hard-stop",
        "Coupling": coupling,
        "Candidate Boundary": "one complete candidate; provisional failures are repaired before the completion gate",
        "Stop Rules": "stop the current candidate at a final assertion; stop the task immediately for scope breach",
        "Evidence": "\n" + evidence,
        "Stop if": "scope requires files outside Touch",
        "Report": "Summary and Tests Run",
    }
    if missing_field is not None:
        del fields[missing_field]
    checkbox = "x" if checked else " "
    lines = [f"- [{checkbox}] 1.1 Gate fixture task"]
    for name, value in fields.items():
        if value.startswith("\n"):
            lines.append(f"  - {name}:{value}")
        else:
            lines.append(f"  - {name}: {value}")
    return "\n".join(lines) + "\n"


def write_gate_fixture(repo: Path, tasks: str, design: str = "## Context\n\nfixture\n") -> None:
    change = repo / "openspec/changes/demo"
    write_text(
        change / "tasks.md",
        "# Tasks\n\n## Invalidates\n\n- None.\n\n"
        "## Invalidates\n\n"
        "- None.\n\n"
        "## Expectation Coverage\n\n"
        "- E1:\n"
        "  - Covered by: 1.1\n\n"
        "## Tasks\n\n"
        + tasks,
    )
    write_text(change / "proposal.md", "# Proposal\n")
    write_text(change / "design.md", design)
    write_text(change / "specs/demo/spec.md", "## ADDED Requirements\n")


def coupled_design_fixture() -> str:
    return """## Coupled Iteration Contract

- Coupled artifacts: source and generated output.
- Invalidation triggers: source changes.
- Required regeneration: regenerate output.
- Final assertions: required checks pass.
- Conflict authority: design.md.
- Baseline policy: baseline stays fixed.
"""


def task_contract_fixture(
    *,
    mode: str = "implementation",
    touch: tuple[str, ...] = ("src/feature.js",),
    commands: tuple[str, ...] = ("M1: node test.js",),
    evidence: tuple[str, ...] = ("M1: pending",),
    strategy: str | None = "evidence-first",
) -> str:
    touch_lines = "".join(f"    - {item}\n" for item in touch)
    command_lines = "".join(f"    - {item}\n" for item in commands)
    evidence_lines = "".join(f"    - {item}\n" for item in evidence)
    return (
        "# Tasks\n\n## Invalidates\n\n- None.\n\n"
        "- [ ] 1.1 Exercise task contract\n"
        "  - Owner: keel-agent\n"
        f"  - Mode: {mode}\n"
        "  - Covers:\n"
        "    - E1: public behavior\n"
        "  - Read:\n"
        "    - README.md\n"
        "  - Touch:\n"
        f"{touch_lines}"
        + (f"  - Verification Strategy: {strategy}\n" if strategy else "")
        + (f"  - Verification Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
           if strategy == "evidence-first" else "")
        + "  - Commands:\n"
        + f"{command_lines}"
        "  - Acceptance:\n"
        "    - Public behavior passes.\n"
        "  - Autonomy boundary:\n"
        "    - Default: hard-stop\n"
        "    - Pre-authorized fallback: none\n"
        "  - Coupling: none\n"
        "  - Candidate Boundary:\n"
        "    - Not applicable; Coupling is none.\n"
        "  - Stop Rules:\n"
        "    - Stop on failure.\n"
        "  - Evidence:\n"
        # Emitted unconditionally rather than through `evidence`, which callers
        # override to control the M-entries. Completion requires a recorded
        # fingerprint, and `--record` rewrites this line in place, so a caller
        # that customizes its evidence must not be able to drop the anchor.
        "    - Contract: pending\n"
        f"{evidence_lines}"
        "    - Review:\n"
        "      - Status: pending\n"
        "      - Acceptance check: pending\n"
        "      - Scope check: pending\n"
        "      - Findings: pending\n"
        "    - Blocker: none\n"
        "  - Stop if:\n"
        "    - Requires files outside Touch.\n"
        "  - Report:\n"
        "    - Summary\n"
    )


def task_capsule_compact_fixture() -> str:
    return (
        "# Tasks\n\n## Invalidates\n\n- None.\n\n"
        "- [ ] 1.1 Exercise task contract\n"
        "  - Covers:\n"
        "    - E1: Public behavior passes.\n"
        "  - Read:\n"
        "    - README.md\n"
        "  - Touch:\n"
        "    - src/feature.js\n"
        "  - Verify:\n"
        "    - Strategy: evidence-first\n"
        "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "    - M1: node test.js\n"
        "  - Autonomy boundary:\n"
        "    - Default: hard-stop\n"
        "    - Pre-authorized fallback: none\n"
        "  - Stop Rules:\n"
        "    - Stop on failure.\n"
        "  - Evidence:\n"
        # Completion requires a recorded fingerprint here, so the anchor line
        # must exist for `--record` to rewrite in place. See
        # record_contract_anchor.
        "    - Contract: pending\n"
        "    - M1: pending\n"
        "  - Stop if:\n"
        "    - Requires files outside Touch.\n"
    )


def tracker_owner_tasks(findings: str, closure: str) -> str:
    """One complete, checked task plus one Expectation Coverage closure line."""
    return (
        "# Tasks\n\n## Invalidates\n\n- None.\n\n"
        "## Expectation Coverage\n\n"
        "- E1:\n"
        f"  - {closure}\n\n"
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
        f"      - Findings: {findings}\n"
        "    - Blocker: none\n"
        "  - Stop if:\n"
        "    - Scope expands.\n"
        "  - Report:\n"
        "    - Summary\n"
    )


# `@fission-ai/openspec` is this package's own declared dependency, and
# `npm install` puts an executable at `node_modules/.bin/openspec`. npm scripts
# see that directory on PATH; a Python subprocess started by
# `node scripts/run_python.js` does not — so a checkout that had installed
# everything it declares reported `validation --all failed for:
# compact-task-authoring` while the schema it could supposedly not resolve
# resolved perfectly (issue #105).
#
# The declared dependency wins over PATH. It is the version this repository is
# tested against; a global install that happens to be on PATH is a different
# version answering for it.
OPENSPEC_SEARCH_ORDER = (
    "the package's own node_modules/.bin",
    "PATH",
)


@contextlib.contextmanager
def path_without_openspec(path: str | None = None):
    """Yield `path` with every `openspec` executable on it removed, and nothing else.

    Dropping a PATH *directory* because it holds an `openspec` also drops that
    directory's other contents. On the ordinary Homebrew plus `npm install -g`
    layout one directory holds both `openspec` and `node`, so the filter took the
    interpreter the openspec shim needs and the scenario built on it asserted that
    a shell without an interpreter fails — reported against `openspec`, which was
    installed and working (issue #137).

    So a directory that holds the tool is replaced in place, at the same index, by
    a mirror symlinking every one of its entries except the `openspec` ones; a
    directory that does not hold it is passed through untouched. Exclusion is by
    stem, so `openspec.cmd` and its siblings cannot survive a filter whose whole
    purpose is that the name does not resolve.

    The mirrors live for the duration of the context, so callers must hold it open
    across every child process they run against the PATH, not only across the call
    that built it.
    """
    original = os.environ.get("PATH", "") if path is None else path
    entries = [entry for entry in original.split(os.pathsep) if entry]
    with tempfile.TemporaryDirectory(prefix="keel-no-openspec-") as raw:
        mirrors = Path(raw)
        rebuilt: list[str] = []
        for index, entry in enumerate(entries):
            source = Path(entry)
            try:
                contents = sorted(source.iterdir())
            except OSError:
                # Unreadable or absent: it carried nothing resolvable either way.
                rebuilt.append(entry)
                continue
            if not any(item.stem == "openspec" for item in contents):
                rebuilt.append(entry)
                continue
            mirror = mirrors / str(index)
            try:
                mirror.mkdir()
                for item in contents:
                    if item.stem == "openspec":
                        continue
                    (mirror / item.name).symlink_to(item)
            except OSError:
                # Windows can refuse a symlink without the privilege. Fall back to
                # dropping the directory, which is what this replaces; the caller's
                # precondition check then reports the consequence by name instead
                # of attributing it to the tool.
                continue
            rebuilt.append(str(mirror))
        yield os.pathsep.join(rebuilt)


def resolve_openspec(env: dict[str, str] | None = None) -> str | None:
    local = ROOT / "node_modules" / ".bin" / "openspec"
    if local.is_file():
        return str(local)
    return shutil.which("openspec", path=(env or os.environ).get("PATH"))


def run_openspec(
    cwd: Path,
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str] | None:
    executable = resolve_openspec(env)
    if executable is None:
        return None
    return subprocess.run(
        [executable, *args],
        cwd=cwd,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def legacy_v3_web_profile_text() -> str:
    return (
        "---\n"
        "name: keel-profile-web\n"
        "description: Optional Keel profile for web frontend/backend work; use during OpenSpec authoring or verification when UI, API, routing, persistence, or integration behavior may hide product assumptions.\n"
        "---\n"
        "\n"
        "# keel-profile-web\n"
        "## Purpose\n"
        "\n"
        "Use this optional domain profile to make web hidden-knowledge risk explicit before executable Keel tasks are selected. This is profile guidance only; it does not change core Keel ownership, Touch boundaries, sync/archive rules, or handoff semantics.\n"
        "\n"
        "## Risk-triggered grill\n"
        "\n"
        "Invoke `keel-grill-open-questions` during OpenSpec authoring when the change touches UI-observable behavior, public interface contracts, routing, auth/session behavior, persistence, migrations, async state, loading/error states, accessibility expectations, browser compatibility, or backend integration boundaries.\n"
        "\n"
        "Ask only questions that materially affect Acceptance, Commands, Touch, specs, design decisions, or non-goals. Stop when the task contract can be written without guessing.\n"
        "\n"
        "## Durable placement\n"
        "\n"
        "Write accepted answers into durable OpenSpec artifacts:\n"
        "\n"
        "- specs for user-visible behavior, API behavior, error handling, and scenarios.\n"
        "- design.md for framework choices, data flow, migration notes, auth/session assumptions, and trade-offs.\n"
        "- tasks.md for Acceptance, Commands, Read, Touch, Stop if, and Autonomy boundary details.\n"
        "\n"
        "Do not leave product decisions only in chat or `keel/HANDOFF.md`.\n"
        "\n"
        "## Verification prompts\n"
        "\n"
        "Prefer public interface evidence:\n"
        "\n"
        "- UI behavior through a rendered page or component workflow, not self-mocked internals.\n"
        "- API behavior through route/client contract checks, including failure paths when they affect users.\n"
        "- Data changes through migration/integration evidence when persistence semantics change.\n"
        "- Accessibility or responsive behavior checks when the task Acceptance names them.\n"
        "\n"
        "## Standalone use\n"
        "\n"
        "When used alone, report the hidden-knowledge risks found, where each accepted answer should be captured, and the public-interface evidence expected.\n"
    )


PLUGIN_ROOT = Path("plugins/keel")


def run_session_start_hook(
    repo: Path,
    event: dict,
    *,
    keel_cli: str | None,
    timeout_ms: int | None = None,
    panel: str | None = None,
    plugin_root: Path | None = None,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    # The shipping plugin unless a fixture plants its own copy. A planted copy
    # is how the version the plugin reports about itself becomes something the
    # suite decides rather than something it inherits from this working tree.
    root = Path(plugin_root) if plugin_root is not None else ROOT / PLUGIN_ROOT
    env = dict(os.environ)
    # None leaves the hook to choose its own CLI, which is the only way to
    # observe that choice; every other caller pins one.
    env.pop("KEEL_CLI", None)
    if keel_cli is not None:
        env["KEEL_CLI"] = keel_cli
    env["CLAUDE_PLUGIN_ROOT"] = str(root)
    # The suite must decide the panel's state rather than inherit whatever the
    # developer running it has exported, or the default-off assertion would
    # pass or fail by accident of the shell.
    env.pop("KEEL_SESSION_PANEL", None)
    if panel is not None:
        env["KEEL_SESSION_PANEL"] = panel
    if timeout_ms is not None:
        env["KEEL_HOOK_TIMEOUT_MS"] = str(timeout_ms)
    if extra_env is not None:
        env.update(extra_env)
    return subprocess.run(
        ["node", str(root / "scripts/session-start.js")],
        cwd=repo,
        env=env,
        input=json.dumps(event),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def session_start_context(result: subprocess.CompletedProcess[str]) -> str | None:
    if not result.stdout.strip():
        return None
    payload = json.loads(result.stdout)
    output = payload.get("hookSpecificOutput", {})
    if output.get("hookEventName") != "SessionStart":
        raise ValueError(f"unexpected hook output shape: {result.stdout!r}")
    return output.get("additionalContext")


def resident_session_start_section(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"^## Session Start$(.*?)^## ", text, re.MULTILINE | re.DOTALL
    )
    return match.group(1) if match else None


# A hook stub that reports which copy ran, with what input. Used as the newer
# install's copy of a script so the scenario can tell a hand-off from the
# loaded script's own logic, which prints none of this.
HANDOFF_STUB = r"""const fs = require("fs");
const path = require("path");
let input = "";
try { input = fs.readFileSync(0, "utf8"); } catch {}
const manifest = path.join(__dirname, "..", ".claude-plugin", "plugin.json");
process.stdout.write(JSON.stringify({
  stub: JSON.parse(fs.readFileSync(manifest, "utf8")).version,
  script: path.basename(__filename),
  argv: process.argv.slice(2),
  input,
  forwarded: process.env.KEEL_HOOK_FORWARDED || null,
  root: process.env.CLAUDE_PLUGIN_ROOT || null,
}) + "\n");
const sleep = Number(process.env.HANDOFF_STUB_SLEEP_MS || 0);
if (sleep) Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, sleep);
process.exit(Number(process.env.HANDOFF_STUB_STATUS || 0));
"""


def plant_handoff_package(root: Path, version: str, *, stubs: tuple[str, ...] = ()) -> Path:
    """One cached Claude install: the package root with both manifests and the
    plugin's real hook scripts, of which `stubs` are replaced by HANDOFF_STUB."""
    manifest = json.dumps({"name": "keel", "version": version}, indent=2) + "\n"
    write_text(root / ".claude-plugin/plugin.json", manifest)
    write_text(root / "plugins/keel/.claude-plugin/plugin.json", manifest)
    write_text(
        root / "package.json",
        json.dumps({"name": "@christang/keel", "version": version}) + "\n",
    )
    scripts = ROOT / PLUGIN_ROOT / "scripts"
    for source in sorted(scripts.glob("*.js")):
        body = HANDOFF_STUB if source.name in stubs else source.read_text(encoding="utf-8")
        write_text(root / "plugins/keel/scripts" / source.name, body)
    return root


def write_install_record(plugins_dir: Path, install_path: Path | None) -> None:
    entries = {}
    if install_path is not None:
        entries["keel@m"] = [{"scope": "user", "installPath": str(install_path), "version": "x"}]
    write_text(
        plugins_dir / "installed_plugins.json",
        json.dumps({"version": 2, "plugins": entries}) + "\n",
    )


def run_hook_script(
    script: Path,
    args: list[str],
    stdin: str,
    cwd: Path,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    for name in ("KEEL_HOOK_FORWARDED", "HANDOFF_STUB_STATUS", "HANDOFF_STUB_SLEEP_MS",
                 "KEEL_HOOK_FORWARD_TIMEOUT_MS"):
        env.pop(name, None)
    env["CLAUDE_PLUGIN_ROOT"] = str(script.parents[1])
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["node", str(script), *args], cwd=cwd, env=env, input=stdin, text=True,
        encoding="utf-8", errors="replace", capture_output=True, check=False, timeout=60,
    )


def stub_output(result: subprocess.CompletedProcess[str]) -> dict | None:
    for line in result.stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "stub" in value:
            return value
    return None


def run_node_expression(root: Path, expression: str) -> str:
    """Evaluate a Node expression with `root` as the working directory.

    The declaration set is read from the module that defines it rather than by
    regexing its source: a regex over the source would be a second copy of the
    same literal the check exists to remove, one level down (issue #143).
    """
    result = subprocess.run(
        ["node", "-e", expression],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    return result.stdout


def config_header_paragraph(config_text: str) -> str:
    """The opening paragraph that lists the declarations, whitespace-collapsed.

    The header, not the file. Both callers used to pass the whole of
    `keel/config.yaml`, so a declaration name appearing anywhere in the body — a
    comment elsewhere that happened to use the word — satisfied "the header names
    it". `merge` did exactly that in 5.71.0, through the triage section's "never
    authorizes a merge", before the header said anything about it (#155).
    """
    lines = config_text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if "independent declarations live here" in line),
        None,
    )
    if start is None:
        return ""
    paragraph = []
    for line in lines[start:]:
        if not line.startswith("#") or line.strip() == "#":
            break
        paragraph.append(line.lstrip("#").strip())
    return re.sub(r"\s+", " ", " ".join(paragraph))


def config_header_problem(names: list, config_text: str) -> str:
    """The one rule for "the header names every declaration", or "" when it does.

    Returns the diagnostic naming the missing declaration. Deliberately reports
    no count: a count tells an author that two numbers differ, and the name tells
    them which line to write.
    """
    header = config_header_paragraph(config_text)
    if not header:
        return (
            "keel/config.yaml has no header paragraph listing its declarations "
            "(the one containing `independent declarations live here`), so "
            "nothing tells a project which keys it may write."
        )
    for name in names:
        if name not in header:
            return (
                f"keel/config.yaml's header does not name the `{name}` "
                "declaration, so a project reading it would never learn it may "
                "write one. Add it to the header's list."
            )
    return ""


def write_authorize_config(repo: Path, body: str) -> None:
    (repo / "keel").mkdir(parents=True, exist_ok=True)
    (repo / "keel" / "config.yaml").write_text(body, encoding="utf-8")


def guard_task_fixture(checked: bool = False) -> str:
    box = "x" if checked else " "
    return (
        "# Tasks\n\n## Invalidates\n\n- None.\n\n"
        f"- [{box}] 1.1 Exercise guarded feature\n"
        "  - Covers:\n"
        "    - E1: Guarded public behavior passes.\n"
        "  - Touch:\n"
        "    - src/feature.js\n"
        "    - docs/**\n"
        "  - Verify:\n"
        "    - Strategy: evidence-first\n"
        "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
        "    - M1: node test.js\n"
        "  - Evidence:\n"
        "    - M1: pending\n"
    )


# Exit code 3 means "this scenario did not run because an external runtime it
# probes is absent". 0 is pass, 1 is fail, 2 is an unknown scenario or a usage
# error, so conflating an unavailable runtime with either would hide both. The
# reason is narrow on purpose: an inconvenient assertion, a hard fixture, or a
# platform difference is a failure, never a skip.
SKIPPED = 3


def skip_scenario(label: str, reason: str) -> int:
    report(f"{label} scenario skipped: {reason}")
    return SKIPPED


def run_scenario_processes(names: list, jobs: int) -> list:
    """Run each named scenario as its own --scenario subprocess in parallel.

    Output is captured per scenario and the result list preserves the input
    order so a replay is deterministic regardless of completion timing.
    """
    # The entry point, which each scenario runs through (#409).
    script = str(ROOT / "scripts/validate_plugin.py")

    def run_one(name: str):
        proc = subprocess.run(
            [sys.executable, script, "--scenario", name],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")

    results = {}
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        futures = {pool.submit(run_one, name): name for name in names}
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return [(name, *results[name]) for name in names]

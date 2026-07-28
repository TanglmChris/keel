#!/usr/bin/env python3
"""Validate the Keel v4.1.0 package baseline."""

from __future__ import annotations

import json
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRECTORIES = [
    "bin",
    "src",
    "src/core",
    "src/skills",
    "scripts",
    "plugins/keel",
    "plugins/keel/skills",
    "assets/bootstrap",
    "assets/openspec",
]

REQUIRED_SCRIPTS = [
    "bin/keel.js",
    "scripts/install_to_repo.py",
    "scripts/run_python.js",
    "scripts/validate_plugin.py",
]

PACKAGE_VERSION = "5.3.4"
PROTOCOL_VERSION = "5.3.4"
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
TARGET_SKILL_ROOTS = {
    "claude": Path(".claude") / "skills",
    "codex": Path(".agents") / "skills",
    "opencode": Path(".opencode") / "skills",
}
CORE_KEEL_SKILLS = {
    "keel-align-expectations",
    "keel-debug-failure",
    "keel-handoff",
    "keel-review-checklist",
    "keel-run-single-task-goal",
    "keel-tdd-or-test-first",
}
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
            "read-only report/evidence",
            "native plugin",
            "keel --init",
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

TEMPLATE_REQUIREMENTS: list[dict] = []

SKILL_DOC_REQUIREMENTS = [
    {
        "name": "review-checklist skill",
        "path": "src/skills/keel-review-checklist/SKILL.md",
        "required": [
            "completion gates",
            "/opsx:apply",
            "/opsx:sync",
            "/opsx:archive",
            "## Context to read",
            "keel gate task-start",
            "task-complete",
            "change-close",
            "deterministic structure",
            "## Semantic Review",
            "`Acceptance check`",
            "`Scope check`",
            "`Findings`",
            "durable OpenSpec task/new change",
            "discard rationale",
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
            "same failure at most 2 attempts",
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


def validate_manifest(errors: list[str]) -> None:
    package_path = ROOT / "package.json"
    try:
        package_version = json.loads(
            package_path.read_text(encoding="utf-8")
        ).get("version")
    except (FileNotFoundError, json.JSONDecodeError):
        package_version = None

    if (ROOT / "plugin.json").exists():
        errors.append(
            "legacy custom plugin.json must be retired in the Keel 4.0.0 native "
            "plugin release"
        )

    for runtime in (".codex-plugin", ".claude-plugin"):
        manifest_path = ROOT / "plugins" / "keel" / runtime / "plugin.json"
        if not manifest_path.is_file():
            errors.append(
                f"missing native plugin manifest: plugins/keel/{runtime}/plugin.json"
            )
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(
                f"native plugin manifest is not valid JSON: {runtime}: {exc}"
            )
            continue
        if manifest.get("name") != "keel":
            errors.append(
                f"native plugin manifest {runtime} must declare name keel"
            )
        version = manifest.get("version")
        if package_version is not None and version != package_version:
            errors.append(
                f"native plugin manifest {runtime} version {version!r} must equal "
                f"package version {package_version!r}"
            )

    skills_root = ROOT / "plugins" / "keel" / "skills"
    if not skills_root.is_dir():
        errors.append("plugins/keel/skills must hold the canonical skill set")
        return
    packaged = {path.name for path in skills_root.iterdir() if path.is_dir()}
    missing = sorted(set(CORE_KEEL_SKILLS) - packaged)
    if missing:
        errors.append(
            "plugins/keel/skills missing canonical skills: " + ", ".join(missing)
        )
    for legacy_skill in LEGACY_PROFILE_SKILLS:
        if legacy_skill in packaged:
            errors.append(
                f"plugins/keel/skills must not package legacy profile skill "
                f"{legacy_skill!r}"
            )


def validate_npm_package(errors: list[str]) -> None:
    package_path = ROOT / "package.json"
    if not package_path.is_file():
        errors.append("missing package.json")
        return

    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"package.json is not valid JSON: {exc}")
        return

    if package.get("name") != "@christang/keel":
        errors.append("package.json must declare npm package name @christang/keel")
    if package.get("version") != PACKAGE_VERSION:
        errors.append(f"package.json must declare version {PACKAGE_VERSION}")

    bin_map = package.get("bin")
    if not isinstance(bin_map, dict) or bin_map.get("keel") != "bin/keel.js":
        errors.append("package.json must expose bin keel -> bin/keel.js")

    scripts = package.get("scripts")
    if not isinstance(scripts, dict):
        errors.append("package.json must declare npm scripts")
    else:
        for script_name in ("validate", "test"):
            script_value = scripts.get(script_name)
            if not isinstance(script_value, str):
                errors.append(f"package.json missing npm script: {script_name}")
                continue
            if "scripts/run_python.js" not in script_value:
                errors.append(
                    f"package.json script {script_name!r} must use scripts/run_python.js"
                )
            if "python scripts/" in script_value:
                errors.append(
                    f"package.json script {script_name!r} must not depend on bare python"
                )

    dependencies = package.get("dependencies")
    if (
        not isinstance(dependencies, dict)
        or dependencies.get("@fission-ai/openspec") != "^1.4.1"
    ):
        errors.append("package.json must depend on @fission-ai/openspec ^1.4.1")

    files = package.get("files")
    if not isinstance(files, list):
        errors.append("package.json must declare files for npm packaging")
    else:
        for required in ("bin/", "scripts/", "assets/", "README.md", "plugins/"):
            if required not in files:
                errors.append(f"package.json files missing packaged path: {required}")
        for forbidden in ("dist/", "plugin.json"):
            if forbidden in files:
                errors.append(
                    "package.json files must not ship retired custom distribution: "
                    f"{forbidden}"
                )

    cli_path = ROOT / "bin" / "keel.js"
    if not cli_path.is_file():
        errors.append("missing npm CLI entrypoint: bin/keel.js")
        return

    cli = cli_path.read_text(encoding="utf-8")
    for required in (
        "#!/usr/bin/env node",
        "--init",
        "--install",
        "--clear",
        "--uninstall",
        "--update",
        "--check",
        "--doctor",
        "capabilities",
        "gate",
        "lenses",
        "--profile",
        "--version",
        "--help",
        "--source",
        "global keel CLI",
        "DEFAULT_UPDATE_SOURCE",
        "KEEL_PYTHON",
        "findOpenSpecCommand",
    ):
        if required not in cli:
            errors.append(f"bin/keel.js missing required CLI support: {required}")


# Path expressions rooted at a tree the retirement check above requires to be
# absent. `src/core` and `src/skills` are live, so only the retired `src`
# children are listed.
RETIRED_PATH_EXPRESSIONS = (
    r'ROOT\s*/\s*"dist"',
    r'ROOT\s*/\s*"src"\s*/\s*"assets"',
    r'ROOT\s*/\s*"src"\s*/\s*"hooks"',
    r'ROOT\s*/\s*"src"\s*/\s*"adapters"',
)


def validate_paths(errors: list[str]) -> None:
    for directory in REQUIRED_DIRECTORIES:
        if not (ROOT / directory).is_dir():
            errors.append(f"missing directory: {directory}")

    for script in REQUIRED_SCRIPTS:
        if not (ROOT / script).is_file():
            errors.append(f"missing script entrypoint: {script}")

    for root_label, skills_root in (
        ("source", ROOT / "src" / "skills"),
        ("plugin", ROOT / "plugins" / "keel" / "skills"),
    ):
        if not skills_root.is_dir():
            continue
        for skill_doc in sorted(skills_root.glob("*/SKILL.md")):
            name = skill_doc.parent.name
            content = skill_doc.read_text(encoding="utf-8")
            if not re.search(
                rf"^name:\s*{re.escape(name)}\s*$", content, re.MULTILINE
            ):
                errors.append(
                    "skill frontmatter name must match folder key "
                    f"{name!r} ({root_label}): "
                    f"{skill_doc.relative_to(ROOT).as_posix()}"
                )

    for retired in ("dist", "plugin.json", "src/adapters", "src/hooks"):
        if (ROOT / retired).exists():
            errors.append(
                f"retired custom distribution path must be removed: {retired}"
            )

    # Every Keel marker that carries a version is a shipped claim about which
    # version this is. Derive the set from the markers that exist rather than a
    # fixed list, because a fixed list is the next thing to fall behind — which
    # is exactly how the `.codex/` overlays sat four versions back unnoticed.
    for marker_file in sorted(ROOT.rglob("*")):
        if not marker_file.is_file() or not marker_file.suffix in (".md", ".json"):
            continue
        relative = marker_file.relative_to(ROOT).as_posix()
        if relative.startswith(("node_modules/", "openspec/changes/archive/", "keel/archive/")):
            continue
        try:
            text = marker_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for found in re.findall(r"keel:[a-z-]+(?::end)?\s+version=([0-9][^\s>]*)", text):
            if found != PACKAGE_VERSION:
                errors.append(
                    "shipped version marker disagrees with the package version "
                    f"{PACKAGE_VERSION}: {relative} says {found}"
                )

    # Asserting the trees are gone is not enough: a check that still resolves a
    # path into one of them can only ever find nothing, and rglob over a missing
    # directory yields no error, so the check reports success forever. Naming a
    # retired tree in a string literal is fine — that is how the checks above
    # state what must not exist; building a Path into one is not.
    validator_source = (ROOT / "scripts" / "validate_plugin.py").read_text(
        encoding="utf-8"
    )
    for line_number, line in enumerate(validator_source.splitlines(), start=1):
        if any(re.search(pattern, line) for pattern in RETIRED_PATH_EXPRESSIONS):
            errors.append(
                "validator resolves a path under a retired distribution tree, "
                "so the check it feeds can only iterate nothing: "
                f"scripts/validate_plugin.py:{line_number}: {line.strip()}"
            )


def extract_managed_block(content: str) -> str | None:
    start_match = MANAGED_START_RE.search(content)
    if start_match is None:
        return None
    end = content.find(MANAGED_END, start_match.end())
    if end == -1:
        return None
    return content[start_match.start() : end + len(MANAGED_END)]


def has_managed_block(path: Path) -> bool:
    if not path.is_file():
        return False
    return extract_managed_block(path.read_text(encoding="utf-8")) is not None


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


def validate_templates(errors: list[str]) -> None:
    for template in TEMPLATE_REQUIREMENTS:
        path = ROOT / template["path"]
        if not path.is_file():
            errors.append(f"{template['name']} is missing: {template['path']}")
            continue

        content = path.read_text(encoding="utf-8")
        marker = template.get("marker")
        if marker is not None and marker not in content:
            errors.append(f"{template['name']} missing marker: {marker}")
        for required in template["required"]:
            if required not in content:
                errors.append(f"{template['name']} missing required section: {required}")
        for forbidden in template.get("forbidden", []):
            if forbidden in content:
                errors.append(
                    f"{template['name']} includes forbidden content: {forbidden}"
                )

    # What actually ships is whatever package.json declares, so derive the roots
    # from there rather than naming a tree that can retire out from under the
    # check the way `src/assets` and `dist` did.
    packaged_roots = [
        ROOT / entry
        for entry in json.loads(
            (ROOT / "package.json").read_text(encoding="utf-8")
        ).get("files", [])
        if (ROOT / entry).is_dir()
    ]

    active_task_placeholders = [
        path.relative_to(ROOT).as_posix()
        for base in packaged_roots
        for path in base.rglob("keel/TASK.md")
    ]
    if active_task_placeholders:
        errors.append(
            "package must not include an active keel/TASK.md placeholder: "
            + ", ".join(active_task_placeholders)
        )

    backlog_assets = [
        path.relative_to(ROOT).as_posix()
        for base in packaged_roots
        for path in base.rglob("keel/backlog/*")
    ]
    if backlog_assets:
        errors.append(
            "package must not include keel backlog assets: "
            + ", ".join(sorted(backlog_assets))
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
            "/opsx:apply",
            "keel-review-checklist",
            "Owner",
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
            "current Keel agent remains task owner and executor",
            "Do not hand Keel-managed execution to another agent",
            "Modify only files listed under Touch",
            "repository-wide read authority is read-only",
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
            "carry a durable owner",
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


def validate_scripts_use_stdlib(errors: list[str]) -> None:
    stdlib_modules = set(
        getattr(
            sys,
            "stdlib_module_names",
            {
                "argparse",
                "ast",
                "dataclasses",
                "hashlib",
                "json",
                "os",
                "pathlib",
                "re",
                "shutil",
                "subprocess",
                "sys",
                "tempfile",
            },
        )
    )
    allowed = stdlib_modules | {"__future__"}

    for script in sorted((ROOT / "scripts").glob("*.py")):
        tree = ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])

        external = sorted(import_name for import_name in imports if import_name not in allowed)
        if external:
            errors.append(
                f"{script.relative_to(ROOT).as_posix()} imports non-stdlib modules: "
                + ", ".join(external)
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


def run_install(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "install_to_repo.py"),
            str(repo),
            *args,
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


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


def create_skill_portability_fixture(root: Path) -> None:
    write_text(
        root / "src/skills/keel-example/SKILL.md",
        "---\n"
        "name: keel-example\n"
        "description: >\n"
        "  Validate portable skills. Use when testing skill packaging.\n"
        "---\n\n"
        "# Keel Example\n",
    )
    source = (root / "src/skills/keel-example/SKILL.md").read_text(encoding="utf-8")
    write_text(root / "plugins/keel/skills/keel-example/SKILL.md", source)


def validate_skill_portability_policy_scenario() -> int:
    repository_errors: list[str] = []
    validate_skill_portability(ROOT, repository_errors)
    if repository_errors:
        report("skill-portability-policy rejected the repository baseline:")
        for error in repository_errors:
            report(f"- {error}")
        return 1

    policy_errors: list[str] = []
    validate_resident_blocks(policy_errors)
    validate_openspec_schema(policy_errors)
    validate_skill_docs(policy_errors)
    for path in (ROOT / "AGENTS.md", ROOT / "README.zh-CN.md"):
        content = path.read_text(encoding="utf-8")
        for snippet in (
            "authoritative source",
            "positive and negative trigger cases"
            if path.name == "AGENTS.md"
            else "should-not-trigger",
            "real-task evidence" if path.name == "AGENTS.md" else "real task",
            "target-native",
        ):
            if snippet not in content:
                policy_errors.append(f"{path.name} missing skill policy: {snippet}")
    if policy_errors:
        report("skill-portability-policy source policy validation failed:")
        for error in policy_errors:
            report(f"- {error}")
        return 1

    with tempfile.TemporaryDirectory() as temp_dir:
        fixture = Path(temp_dir)
        create_skill_portability_fixture(fixture)
        fixture_errors: list[str] = []
        validate_skill_portability(fixture, fixture_errors)
        if fixture_errors:
            report("skill-portability-policy rejected valid folded metadata.")
            return 1

        write_text(
            fixture / "src/skills/keel-example/SKILL.md",
            "---\n"
            "name: Keel_Example\n"
            "---\n\n"
            "# Invalid metadata\n",
        )
        metadata_errors: list[str] = []
        validate_skill_portability(fixture, metadata_errors)
        if not any("canonical skill name" in error for error in metadata_errors):
            report("skill-portability-policy accepted an invalid skill name.")
            return 1
        if not any("description" in error for error in metadata_errors):
            report("skill-portability-policy accepted a missing description.")
            return 1

        create_skill_portability_fixture(fixture)
        skill_path = fixture / "src/skills/keel-example/SKILL.md"
        write_text(
            skill_path,
            skill_path.read_text(encoding="utf-8")
            + "\nRead [the missing guide](references/missing.md).\n",
        )
        reference_errors: list[str] = []
        validate_skill_portability(fixture, reference_errors)
        if not any("missing referenced resource" in error for error in reference_errors):
            report("skill-portability-policy accepted a broken skill reference.")
            return 1

        create_skill_portability_fixture(fixture)
        write_text(
            fixture / "plugins/keel/skills/keel-example/SKILL.md",
            "# Divergent plugin projection\n",
        )
        projection_errors: list[str] = []
        validate_skill_portability(fixture, projection_errors)
        if not any(
            "projection differs from canonical source" in error
            for error in projection_errors
        ):
            report("skill-portability-policy accepted a divergent plugin projection.")
            return 1

    report("skill-portability-policy scenario passed.")
    return 0


def posix_paths(text: str) -> str:
    """Fold path separators so an assertion does not encode the host's spelling.

    Keel prints these paths through the host's path joiner, so the same doctor
    line reads `.claude\\commands\\opsx` on Windows and `.claude/commands/opsx`
    on a POSIX runner. Assertions state the forward-slash form and normalize the
    captured output, rather than branching on the platform or accepting both.
    """
    return (text or "").replace("\\", "/")


def validate_target_surface_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-surface-") as raw_tmp:
        tmp = Path(raw_tmp)

        claude_repo = tmp / "claude"
        claude_repo.mkdir()
        claude_init = run_keel(claude_repo, "--init", "--target", "claude")
        if claude_init.returncode != 0:
            report("target-surface scenario Claude init failed:")
            report((claude_init.stderr or claude_init.stdout).strip())
            return 1
        claude_doctor = run_keel(claude_repo, "--doctor", "--target", "claude")
        if (
            claude_doctor.returncode != 0
            or "Target surface:" not in claude_doctor.stdout
            or "OpenSpec commands: ok" not in claude_doctor.stdout
            or ".claude/commands/opsx" not in posix_paths(claude_doctor.stdout)
            or "OpenSpec action skills: ok" not in claude_doctor.stdout
            or ".claude/skills" not in posix_paths(claude_doctor.stdout)
            or "bootstrap: ok" not in claude_doctor.stdout
            or "CLAUDE import: ok" not in claude_doctor.stdout
            or "native plugin runtime: manual" not in claude_doctor.stdout
            or "Target capabilities (claude):" not in claude_doctor.stdout
            or "gate.change-close: manual" not in claude_doctor.stdout
            or "execution.goal: manual" not in claude_doctor.stdout
            or "helper byteStability: enforced" not in claude_doctor.stdout
            or "helper nestedDelegationPrevention: enforced" not in claude_doctor.stdout
            or "helper execution: manual" not in claude_doctor.stdout
        ):
            report("target-surface scenario Claude doctor did not report full surface.")
            report((claude_doctor.stderr or claude_doctor.stdout).strip())
            return 1

        codex_repo = tmp / "codex"
        codex_repo.mkdir()
        codex_home = tmp / "codex-home"
        env = os.environ.copy()
        env["CODEX_HOME"] = str(codex_home)
        codex_init = run_keel(codex_repo, "--init", "--target", "codex", env=env)
        if codex_init.returncode != 0:
            report("target-surface scenario Codex init failed:")
            report((codex_init.stderr or codex_init.stdout).strip())
            return 1
        codex_doctor = run_keel(codex_repo, "--doctor", "--target", "codex", env=env)
        codex_prompt_dir = str(codex_home / "prompts")
        if (
            codex_doctor.returncode != 0
            or "OpenSpec commands: ok" not in codex_doctor.stdout
            or posix_paths(codex_prompt_dir) not in posix_paths(codex_doctor.stdout)
            or "OpenSpec action skills: ok" not in codex_doctor.stdout
            or ".codex/skills" not in posix_paths(codex_doctor.stdout)
            or "bootstrap: ok" not in codex_doctor.stdout
            or "native plugin runtime: manual" not in codex_doctor.stdout
            or "Target capabilities (codex):" not in codex_doctor.stdout
            or "gate.change-close: manual" not in codex_doctor.stdout
            or "execution.goal: manual" not in codex_doctor.stdout
            or "helper byteStability: enforced" not in codex_doctor.stdout
            or "helper nestedDelegationPrevention: enforced" not in codex_doctor.stdout
            or "helper execution: manual" not in codex_doctor.stdout
        ):
            report("target-surface scenario Codex doctor did not report full surface.")
            report((codex_doctor.stderr or codex_doctor.stdout).strip())
            return 1
        if (codex_repo / ".claude").exists():
            report("target-surface scenario Codex init created Claude-only paths.")
            return 1

        for prompt in (codex_home / "prompts").glob("opsx-*.md"):
            prompt.unlink()
        codex_missing = run_keel(codex_repo, "--doctor", "--target", "codex", env=env)
        if (
            codex_missing.returncode != 0
            or "OpenSpec commands: missing" not in codex_missing.stdout
            or "keel --init --target codex" not in codex_missing.stdout
            or "openspec update --force" not in codex_missing.stdout
        ):
            report("target-surface scenario Codex doctor did not report missing prompts.")
            report((codex_missing.stderr or codex_missing.stdout).strip())
            return 1

        opencode_repo = tmp / "opencode"
        opencode_repo.mkdir()
        opencode_init = run_keel(opencode_repo, "--init", "--target", "opencode")
        if opencode_init.returncode != 0:
            report("target-surface scenario OpenCode init failed:")
            report((opencode_init.stderr or opencode_init.stdout).strip())
            return 1
        opencode_doctor = run_keel(opencode_repo, "--doctor", "--target", "opencode")
        if (
            opencode_doctor.returncode != 0
            or "OpenSpec commands: ok" not in opencode_doctor.stdout
            or ".opencode/commands" not in posix_paths(opencode_doctor.stdout)
            or "OpenSpec action skills: ok" not in opencode_doctor.stdout
            or ".opencode/skills" not in posix_paths(opencode_doctor.stdout)
            or "bootstrap: ok" not in opencode_doctor.stdout
            or "native plugin: manual" not in opencode_doctor.stdout
            or "Target capabilities (opencode):" not in opencode_doctor.stdout
            or "gate.change-close: manual" not in opencode_doctor.stdout
        ):
            report("target-surface scenario OpenCode doctor did not report full surface.")
            report((opencode_doctor.stderr or opencode_doctor.stdout).strip())
            return 1
        if (opencode_repo / ".claude").exists():
            report("target-surface scenario OpenCode init created Claude-only paths.")
            return 1

    report("target-surface scenario passed.")
    return 0


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
        "unresolved Q<n>",
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
        "durable OpenSpec task/new change",
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
    handoff_skill_snippets = [
        "keel-handoff/v1",
        "expectation state",
        "evidence details",
        "durable OpenSpec",
    ]
    handoff_template_snippets = [
        "schema: keel-handoff/v1",
        "owner: openspec/changes/",
        "action:",
        "reason:",
    ]
    archive_overlay_snippets = [
        "owns final sync/archive decisions",
        "critical expectation",
        "behavior evidence",
        "durable follow-up owner",
        "explicit discard reason",
    ]

    checks: list[tuple[str, Path, list[str]]] = [
        ("root AGENTS.md", ROOT / "AGENTS.md", protocol_snippets),
        ("source review-checklist skill", ROOT / "src/skills/keel-review-checklist/SKILL.md", review_snippets),
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
        ("source handoff skill", ROOT / "src/skills/keel-handoff/SKILL.md", handoff_skill_snippets),
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
        "keel-align-expectations",
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
            or scaffold_payload.get("nextAction") != {"kind": "author"}
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


def validate_domain_lenses_scenario() -> int:
    plugin_skills_root = ROOT / PLUGIN_ROOT / "skills"
    if not (plugin_skills_root / "keel-align-expectations/SKILL.md").is_file():
        report("domain-lenses scenario plugin misses the alignment skill")
        return 1
    lenses_root = ROOT / "assets/lenses"
    for template in ("web.md", "hardware.md", "hardware-dsl.md"):
        if not (lenses_root / template).is_file():
            report(
                "domain-lenses scenario misses the shipped lens template: "
                f"{template}"
            )
            return 1
    for legacy_skill in LEGACY_PROFILE_SKILLS:
        if (plugin_skills_root / legacy_skill).exists():
            report(
                f"domain-lenses scenario plugin packages a legacy profile: {legacy_skill}"
            )
            return 1

    with tempfile.TemporaryDirectory(prefix="keel-profiles-") as raw_tmp:
        tmp = Path(raw_tmp)
        repo = tmp / "default"
        repo.mkdir()
        install = run_keel(repo, "--install", "--target", "codex")
        if install.returncode != 0:
            report("domain-lenses scenario default install failed:")
            report((install.stderr or install.stdout).strip())
            return 1
        if (repo / TARGET_SKILL_ROOTS["codex"]).exists():
            report(
                "domain-lenses scenario thin install copied Keel skill trees; "
                "skills are plugin-owned in v4."
            )
            return 1

        rejected = run_keel(repo, "--install", "--target", "codex", "--profile", "web")
        rejected_text = (rejected.stderr or "") + (rejected.stdout or "")
        if rejected.returncode == 0 or "keel/lenses" not in rejected_text:
            report("domain-lenses scenario still accepts --profile.")
            report(rejected_text.strip())
            return 1

        doctor = run_keel(repo, "--doctor", "--target", "codex")
        doctor_text = (doctor.stderr or "") + (doctor.stdout or "")
        if (
            doctor.returncode != 0
            or "native plugin runtime: manual" not in doctor_text
            or "Keel profiles" in doctor_text
        ):
            report(
                "domain-lenses scenario doctor still reports profile state or "
                "misses the native plugin surface."
            )
            report(doctor_text.strip())
            return 1

        uninstall = run_keel(repo, "--uninstall", "--target", "codex")
        agents_text = (
            (repo / "AGENTS.md").read_text(encoding="utf-8")
            if (repo / "AGENTS.md").exists()
            else ""
        )
        if uninstall.returncode != 0 or "keel:start" in agents_text:
            report("domain-lenses scenario uninstall left the managed bootstrap.")
            report((uninstall.stderr or uninstall.stdout).strip())
            return 1

    report("domain-lenses scenario passed.")
    return 0


def validate_version_alignment_scenario() -> int:
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    if package.get("version") != PACKAGE_VERSION:
        report(f"version-alignment scenario package.json expected {PACKAGE_VERSION}.")
        return 1

    for runtime in (".codex-plugin", ".claude-plugin"):
        manifest_path = ROOT / "plugins" / "keel" / runtime / "plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("version") != PACKAGE_VERSION:
            report(
                f"version-alignment scenario native manifest {runtime} expected "
                f"{PACKAGE_VERSION}."
            )
            return 1

    dependencies = package.get("dependencies")
    if (
        not isinstance(dependencies, dict)
        or dependencies.get("@fission-ai/openspec") != "^1.4.1"
    ):
        report("version-alignment scenario dependency versions changed.")
        return 1

    version_result = run_keel(ROOT, "--version")
    expected_version = f"keel {PACKAGE_VERSION}"
    if (
        version_result.returncode != 0
        or version_result.stdout.strip() != expected_version
    ):
        report(f"version-alignment scenario expected CLI version {expected_version}.")
        report((version_result.stderr or version_result.stdout).strip())
        return 1

    required_version_paths = [
        ROOT / "AGENTS.md",
        ROOT / "assets/bootstrap/AGENTS.md",
        ROOT / "keel/CHANGELOG.md",
    ]
    for path in required_version_paths:
        if not path.is_file():
            report(f"version-alignment scenario missing file: {path}")
            return 1
        if PROTOCOL_VERSION not in path.read_text(encoding="utf-8"):
            report(f"version-alignment scenario missing {PROTOCOL_VERSION}: {path}")
            return 1

    with tempfile.TemporaryDirectory(prefix="keel-version-") as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()
        init = run_keel(repo, "--init", "--target", "claude")
        if init.returncode != 0:
            report("version-alignment scenario keel init failed:")
            report((init.stderr or init.stdout).strip())
            return 1
        overlay = repo / ".claude/skills/openspec-apply-change/SKILL.md"
        if OPENSPEC_SURFACE_OVERLAY_START not in overlay.read_text(encoding="utf-8"):
            report("version-alignment scenario OpenSpec overlay marker is stale.")
            return 1

        canonical_marker = (
            (ROOT / "assets/bootstrap/AGENTS.md")
            .read_text(encoding="utf-8")
            .splitlines()[0]
            .strip()
        )
        for managed in ("AGENTS.md", "CLAUDE.md"):
            content = (repo / managed).read_text(encoding="utf-8")
            if canonical_marker not in content:
                report(
                    f"version-alignment scenario installed {managed} marker "
                    "diverges from the canonical bootstrap asset."
                )
                return 1

    installer_source = (ROOT / "scripts/install_to_repo.py").read_text(
        encoding="utf-8"
    )
    if "keel:start version=" in installer_source:
        report(
            "version-alignment scenario install_to_repo.py restates the managed "
            "marker literal instead of deriving it from the bootstrap asset."
        )
        return 1

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for retired in ("npm run build", "dist/", "src/hooks", "src/assets"):
        if retired in readme:
            report(
                f"version-alignment scenario README references the retired "
                f"surface {retired!r}."
            )
            return 1

    report("version-alignment scenario passed.")
    return 0


def openspec_overlay_files(
    repo: Path,
    target: str,
    codex_home: Path | None = None,
) -> dict[str, list[Path]]:
    if target == "claude":
        return {
            "apply": [
                repo / ".claude/skills/openspec-apply-change/SKILL.md",
                repo / ".claude/commands/opsx/apply.md",
            ],
            "archive": [
                repo / ".claude/skills/openspec-archive-change/SKILL.md",
                repo / ".claude/commands/opsx/archive.md",
            ],
        }
    if target == "codex":
        assert codex_home is not None
        return {
            "apply": [
                repo / ".codex/skills/openspec-apply-change/SKILL.md",
                codex_home / "prompts/opsx-apply.md",
            ],
            "archive": [
                repo / ".codex/skills/openspec-archive-change/SKILL.md",
                codex_home / "prompts/opsx-archive.md",
            ],
        }
    return {
        "apply": [
            repo / ".opencode/skills/openspec-apply-change/SKILL.md",
            repo / ".opencode/commands/opsx-apply.md",
        ],
        "archive": [
            repo / ".opencode/skills/openspec-archive-change/SKILL.md",
            repo / ".opencode/commands/opsx-archive.md",
        ],
    }


def strip_openspec_surface_overlay(content: str) -> str:
    return re.sub(
        r"<!--\s*keel:openspec-surface-overlay(?:\s+[^>]*)?\s*-->"
        r".*?"
        r"<!--\s*keel:openspec-surface-overlay:end\s*-->\s*",
        "",
        content,
        flags=re.DOTALL,
    )


def assert_openspec_overlay(path: Path, action: str) -> str | None:
    if not path.is_file():
        return f"missing overlay target: {path}"
    content = path.read_text(encoding="utf-8")
    if content.count(OPENSPEC_SURFACE_OVERLAY_START) != 1:
        return f"{path} must contain exactly one current Keel overlay start marker"
    if content.count(OPENSPEC_SURFACE_OVERLAY_END) != 1:
        return f"{path} must contain exactly one Keel overlay end marker"

    required = [
        "Keel rules below take precedence",
        "Target-native subagent gate",
        "current agent remains",
        "return report/evidence only",
        "Keel ownership",
    ]
    if action == "apply":
        required.extend(
            [
                "Keel task owner",
                "Task Authoring Gate",
                "Slice Start Gate",
                "source expectations",
                "Rough future slices",
                "cannot mark tasks complete",
            ]
        )
    else:
        required.extend(
            [
                "owns final sync/archive decisions",
                "critical expectation",
                "behavior evidence",
                "durable follow-up owner",
                "explicit discard reason",
                "cannot archive, sync, change acceptance, or bypass completion gates",
            ]
        )
    for snippet in required:
        if snippet not in content:
            return f"{path} overlay missing required text: {snippet}"
    return None


def assert_target_overlays(
    repo: Path,
    target: str,
    codex_home: Path | None = None,
) -> str | None:
    for action, paths in openspec_overlay_files(repo, target, codex_home).items():
        for path in paths:
            error = assert_openspec_overlay(path, action)
            if error:
                return error
    return None


def validate_openspec_surface_overlay_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-overlay-") as raw_tmp:
        tmp = Path(raw_tmp)

        claude_repo = tmp / "claude"
        claude_repo.mkdir()
        claude_init = run_keel(claude_repo, "--init", "--target", "claude")
        if claude_init.returncode != 0:
            report("openspec-surface-overlay scenario Claude init failed:")
            report((claude_init.stderr or claude_init.stdout).strip())
            return 1
        error = assert_target_overlays(claude_repo, "claude")
        if error:
            report(f"openspec-surface-overlay scenario Claude overlay failed: {error}")
            return 1
        claude_doctor = run_keel(claude_repo, "--doctor", "--target", "claude")
        if (
            claude_doctor.returncode != 0
            or "Keel apply/archive overlay: ok" not in claude_doctor.stdout
        ):
            report("openspec-surface-overlay scenario Claude doctor missed overlay health.")
            report((claude_doctor.stderr or claude_doctor.stdout).strip())
            return 1

        codex_repo = tmp / "codex"
        codex_repo.mkdir()
        codex_home = tmp / "codex-home"
        codex_env = os.environ.copy()
        codex_env["CODEX_HOME"] = str(codex_home)
        codex_init = run_keel(codex_repo, "--init", "--target", "codex", env=codex_env)
        if codex_init.returncode != 0:
            report("openspec-surface-overlay scenario Codex init failed:")
            report((codex_init.stderr or codex_init.stdout).strip())
            return 1
        error = assert_target_overlays(codex_repo, "codex", codex_home)
        if error:
            report(f"openspec-surface-overlay scenario Codex overlay failed: {error}")
            return 1
        codex_doctor = run_keel(codex_repo, "--doctor", "--target", "codex", env=codex_env)
        if (
            codex_doctor.returncode != 0
            or "Keel apply/archive overlay: ok" not in codex_doctor.stdout
            or str(codex_home / "prompts") not in codex_doctor.stdout
        ):
            report("openspec-surface-overlay scenario Codex doctor missed overlay health.")
            report((codex_doctor.stderr or codex_doctor.stdout).strip())
            return 1

        codex_apply_prompt = codex_home / "prompts/opsx-apply.md"
        original_prompt = codex_apply_prompt.read_text(encoding="utf-8")
        outdated_prompt = re.sub(
            r"<!--\s*keel:openspec-surface-overlay(?:\s+[^>]*)?\s*-->"
            r".*?"
            r"<!--\s*keel:openspec-surface-overlay:end\s*-->",
            "<!-- keel:openspec-surface-overlay version=0.0.0 -->\n"
            "old overlay\n"
            "<!-- keel:openspec-surface-overlay:end -->",
            original_prompt,
            flags=re.DOTALL,
        )
        write_text(codex_apply_prompt, outdated_prompt)
        codex_install = run_keel(codex_repo, "--install", "--target", "codex", env=codex_env)
        if codex_install.returncode != 0:
            report("openspec-surface-overlay scenario Codex install failed:")
            report((codex_install.stderr or codex_install.stdout).strip())
            return 1
        refreshed_prompt = codex_apply_prompt.read_text(encoding="utf-8")
        if (
            refreshed_prompt.count(OPENSPEC_SURFACE_OVERLAY_START) != 1
            or "old overlay" in refreshed_prompt
            or strip_openspec_surface_overlay(refreshed_prompt).strip() == ""
        ):
            report("openspec-surface-overlay scenario Codex install did not refresh overlay idempotently.")
            return 1

        opencode_repo = tmp / "opencode"
        opencode_repo.mkdir()
        opencode_init = run_keel(opencode_repo, "--init", "--target", "opencode")
        if opencode_init.returncode != 0:
            report("openspec-surface-overlay scenario OpenCode init failed:")
            report((opencode_init.stderr or opencode_init.stdout).strip())
            return 1
        error = assert_target_overlays(opencode_repo, "opencode")
        if error:
            report(f"openspec-surface-overlay scenario OpenCode overlay failed: {error}")
            return 1

        opencode_apply_command = opencode_repo / ".opencode/commands/opsx-apply.md"
        write_text(
            opencode_apply_command,
            strip_openspec_surface_overlay(
                opencode_apply_command.read_text(encoding="utf-8")
            ),
        )
        opencode_missing_doctor = run_keel(
            opencode_repo,
            "--doctor",
            "--target",
            "opencode",
        )
        if (
            opencode_missing_doctor.returncode != 0
            or "Keel apply/archive overlay: missing" not in opencode_missing_doctor.stdout
            or "keel --install --target opencode" not in opencode_missing_doctor.stdout
        ):
            report("openspec-surface-overlay scenario doctor did not report a missing overlay marker.")
            report((opencode_missing_doctor.stderr or opencode_missing_doctor.stdout).strip())
            return 1

        install_only_repo = tmp / "install-only"
        install_only_repo.mkdir()
        install_only = run_keel(install_only_repo, "--install", "--target", "opencode")
        if install_only.returncode != 0:
            report("openspec-surface-overlay scenario install-only target failed:")
            report((install_only.stderr or install_only.stdout).strip())
            return 1
        if (install_only_repo / ".opencode/commands/opsx-apply.md").exists():
            report("openspec-surface-overlay scenario install created placeholder OpenSpec command.")
            return 1
        install_only_doctor = run_keel(
            install_only_repo,
            "--doctor",
            "--target",
            "opencode",
        )
        if (
            install_only_doctor.returncode != 0
            or "Keel apply/archive overlay: missing" not in install_only_doctor.stdout
            or "keel --init --target opencode" not in install_only_doctor.stdout
        ):
            report("openspec-surface-overlay scenario install-only doctor missed remediation.")
            report((install_only_doctor.stderr or install_only_doctor.stdout).strip())
            return 1

    report("openspec-surface-overlay scenario passed.")
    return 0


def validate_uninstall_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-uninstall-") as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()

        install = run_install(repo)
        if install.returncode != 0:
            report("uninstall scenario could not install fixture repo.")
            report((install.stderr or install.stdout).strip())
            return 1

        claude_block = extract_managed_block((repo / "CLAUDE.md").read_text(encoding="utf-8"))
        handoff_content = "# HANDOFF\nlegacy user content\n"
        if claude_block is None:
            report("uninstall scenario fixture is missing root managed blocks.")
            return 1

        write_text(repo / "CLAUDE.md", f"claude before\n{claude_block}\nclaude after\n")
        write_text(repo / "keel/TASK.md", "active task must remain\n")
        write_text(repo / "keel/HANDOFF.md", handoff_content)
        write_text(repo / "keel/templates/TASK.lite.md", "user edited lite template\n")
        write_text(repo / "openspec/changes/real-change/proposal.md", "real change\n")
        write_text(repo / "openspec/specs/real-spec.md", "real spec\n")
        before_dry_run = snapshot_files(repo)
        dry_run = run_install(repo, "--uninstall", "--dry-run")
        after_dry_run = snapshot_files(repo)
        if dry_run.returncode != 0:
            report("uninstall scenario dry run failed:")
            report((dry_run.stderr or dry_run.stdout).strip())
            return 1

        for expected in (
            "remove-managed CLAUDE.md",
            "remove-managed AGENTS.md",
            f"rmdir {OPENSPEC_SCHEMA_ROOT.as_posix()}",
        ):
            if expected not in dry_run.stdout:
                report(f"uninstall scenario missing dry-run action: {expected}")
                report(dry_run.stdout.strip())
                return 1
        for schema_file in packaged_openspec_schema_install_paths():
            if f"remove {schema_file}" not in dry_run.stdout:
                report(f"uninstall scenario missing schema removal: {schema_file}")
                report(dry_run.stdout.strip())
                return 1
        if "remove keel/templates/TASK.lite.md" in dry_run.stdout:
            report("uninstall scenario planned to remove a user-edited template.")
            return 1
        if "remove keel/templates/TASK.full.md" in dry_run.stdout:
            report("uninstall scenario planned to remove a legacy Full TASK template.")
            return 1
        if "remove openspec/config.yaml" in dry_run.stdout:
            report("uninstall scenario planned to remove OpenSpec config.")
            return 1
        if before_dry_run != after_dry_run:
            report("uninstall scenario dry run modified the repo.")
            return 1

        uninstall = run_install(repo, "--uninstall")
        if uninstall.returncode != 0:
            report("uninstall scenario failed:")
            report((uninstall.stderr or uninstall.stdout).strip())
            return 1

        if extract_managed_block((repo / "CLAUDE.md").read_text(encoding="utf-8")):
            report("uninstall scenario left CLAUDE.md managed block behind.")
            return 1
        if (repo / "CLAUDE.md").read_text(encoding="utf-8") != "claude before\n\nclaude after\n":
            report("uninstall scenario did not preserve CLAUDE.md user content.")
            return 1
        if not (repo / "keel/TASK.md").is_file():
            report("uninstall scenario deleted active TASK.md.")
            return 1
        if (repo / "keel/HANDOFF.md").read_text(encoding="utf-8") != handoff_content:
            report("uninstall scenario changed user-edited HANDOFF.md.")
            return 1
        if not (repo / "keel/templates/TASK.lite.md").is_file():
            report("uninstall scenario deleted user-edited Lite TASK template.")
            return 1
        if (repo / ".claude/skills/keel-handoff/SKILL.md").exists():
            report("uninstall scenario did not remove packaged Claude skill.")
            return 1
        if (repo / ".claude/skills/keel-review-checklist/SKILL.md").exists():
            report("uninstall scenario did not remove packaged Claude review skill.")
            return 1
        if not (repo / OPENSPEC_CONFIG_PATH).is_file():
            report("uninstall scenario deleted OpenSpec config.")
            return 1
        for schema_file in packaged_openspec_schema_install_paths():
            if (repo / schema_file).exists():
                report(f"uninstall scenario did not remove packaged OpenSpec schema: {schema_file}")
                return 1
        if (repo / OPENSPEC_SCHEMA_ROOT).exists():
            report("uninstall scenario left empty OpenSpec schema directory behind.")
            return 1
        for removed_dir in (
            ".claude",
        ):
            if (repo / removed_dir).exists():
                report(f"uninstall scenario left empty directory behind: {removed_dir}")
                return 1
        for required in (
            "openspec/changes/real-change/proposal.md",
            "openspec/specs/real-spec.md",
        ):
            if not (repo / required).is_file():
                report(f"uninstall scenario deleted real OpenSpec content: {required}")
                return 1

    report("uninstall scenario passed.")
    return 0


def validate_update_pack_install_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-update-pack-") as raw_tmp:
        tmp = Path(raw_tmp)
        fake_bin = tmp / "bin"
        fake_bin.mkdir()
        call_log = tmp / "npm-calls.jsonl"
        fake_npm_py = tmp / "fake_npm.py"
        fake_npm_py.write_text(
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import json",
                    "import os",
                    "import sys",
                    "from pathlib import Path",
                    "",
                    "args = sys.argv[1:]",
                    "log_path = Path(os.environ['KEEL_FAKE_NPM_LOG'])",
                    "with log_path.open('a', encoding='utf-8') as handle:",
                    "    handle.write(json.dumps(args) + '\\n')",
                    "",
                    "if args and args[0] == 'pack':",
                    "    if '--pack-destination' not in args:",
                    "        print('missing --pack-destination', file=sys.stderr)",
                    "        sys.exit(40)",
                    "    destination = Path(args[args.index('--pack-destination') + 1])",
                    "    destination.mkdir(parents=True, exist_ok=True)",
                    "    tarball = destination / 'keel-packed.tgz'",
                    "    tarball.write_bytes(b'fake tarball')",
                    "    print(json.dumps([{'filename': tarball.name}]))",
                    "    sys.exit(0)",
                    "",
                    "if len(args) == 3 and args[0] == 'install' and args[1] == '-g':",
                    "    source = args[2]",
                    "    if source.startswith('github:'):",
                    "        print('direct github install would create a fragile git dependency install', file=sys.stderr)",
                    "        sys.exit(41)",
                    "    if not source.endswith('.tgz'):",
                    "        print('expected a packed tarball install source', file=sys.stderr)",
                    "        sys.exit(42)",
                    "    if not Path(source).is_file():",
                    "        print('packed tarball is missing', file=sys.stderr)",
                    "        sys.exit(43)",
                    "    sys.exit(0)",
                    "",
                    "print('unexpected npm call: ' + json.dumps(args), file=sys.stderr)",
                    "sys.exit(44)",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        if sys.platform == "win32":
            write_text(
                fake_bin / "npm.cmd",
                f'@echo off\r\n"{sys.executable}" "{fake_npm_py}" %*\r\n',
            )
        else:
            fake_npm = fake_bin / "npm"
            fake_npm.write_text(
                f"#!{sys.executable}\n"
                "import runpy\n"
                f"runpy.run_path({str(fake_npm_py)!r}, run_name='__main__')\n",
                encoding="utf-8",
            )
            fake_npm.chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
        env["KEEL_FAKE_NPM_LOG"] = str(call_log)

        result = run_keel(
            tmp,
            "--update",
            "--source",
            "github:TanglmChris/keel",
            env=env,
        )
        if result.returncode != 0:
            report("update-pack-install scenario keel --update failed:")
            report((result.stderr or result.stdout).strip())
            return 1

        calls = [
            json.loads(line)
            for line in call_log.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if len(calls) != 2:
            report("update-pack-install scenario expected exactly two npm calls.")
            report(json.dumps(calls, indent=2))
            return 1

        pack_call, install_call = calls
        expected_pack_prefix = ["pack", "github:TanglmChris/keel"]
        if pack_call[:2] != expected_pack_prefix:
            report("update-pack-install scenario did not pack the GitHub source first.")
            report(json.dumps(calls, indent=2))
            return 1
        if "--pack-destination" not in pack_call or "--json" not in pack_call:
            report("update-pack-install scenario pack call missed required flags.")
            report(json.dumps(calls, indent=2))
            return 1
        if install_call[:2] != ["install", "-g"] or len(install_call) != 3:
            report("update-pack-install scenario did not run npm install -g on one source.")
            report(json.dumps(calls, indent=2))
            return 1
        if install_call[2].startswith("github:") or not install_call[2].endswith(".tgz"):
            report("update-pack-install scenario installed a non-tarball source.")
            report(json.dumps(calls, indent=2))
            return 1

    report("update-pack-install scenario passed.")
    return 0


def validate_update_default_registry_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-update-default-") as raw_tmp:
        tmp = Path(raw_tmp)
        update = run_keel(tmp, "--update", "--dry-run")
        if update.returncode != 0:
            report("update-default-registry scenario keel --update --dry-run failed:")
            report((update.stderr or update.stdout).strip())
            return 1

        pack_plan = (
            "would run npm pack" in update.stdout
            or "would run npm.cmd pack" in update.stdout
        )
        if not pack_plan:
            report("update-default-registry scenario did not report a pack plan.")
            report(update.stdout.strip())
            return 1
        if "@christang/keel" not in update.stdout:
            report(
                "update-default-registry scenario default source is not the "
                "published registry package @christang/keel."
            )
            report(update.stdout.strip())
            return 1
        if "github:" in update.stdout:
            report(
                "update-default-registry scenario default source is a git-type "
                "spec; self-update must default to the registry package."
            )
            report(update.stdout.strip())
            return 1

    report("update-default-registry scenario passed.")
    return 0


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


def validate_cli_scenario() -> int:
    help_result = run_keel(ROOT, "--help")
    if help_result.returncode != 0 or "Usage:" not in help_result.stdout:
        report("cli scenario expected keel --help to print usage.")
        report((help_result.stderr or help_result.stdout).strip())
        return 1

    version_result = run_keel(ROOT, "--version")
    expected_version = f"keel {PACKAGE_VERSION}"
    if version_result.returncode != 0 or version_result.stdout.strip() != expected_version:
        report(f"cli scenario expected keel --version to print {expected_version}.")
        report((version_result.stderr or version_result.stdout).strip())
        return 1

    with tempfile.TemporaryDirectory(prefix="keel-cli-") as raw_tmp:
        tmp = Path(raw_tmp)
        repo = tmp / "repo"
        repo.mkdir()

        before_check = snapshot_files(repo)
        check_missing = run_keel(repo, "--check")
        after_check = snapshot_files(repo)
        if check_missing.returncode != 0:
            report("cli scenario keel --check failed on missing repo.")
            report((check_missing.stderr or check_missing.stdout).strip())
            return 1
        for expected in ("status: missing", "Dry-run install plan:", "create CLAUDE.md"):
            if expected not in check_missing.stdout:
                report(f"cli scenario keel --check missing output: {expected}")
                report(check_missing.stdout.strip())
                return 1
        if before_check != after_check:
            report("cli scenario keel --check modified the repo.")
            return 1

        install = run_keel(repo, "--install")
        if install.returncode != 0:
            report("cli scenario keel --install failed.")
            report((install.stderr or install.stdout).strip())
            return 1
        for expected_file in (
            "CLAUDE.md",
            "AGENTS.md",
            OPENSPEC_CONFIG_PATH.as_posix(),
            *packaged_openspec_schema_install_paths(),
        ):
            if not (repo / expected_file).is_file():
                report(f"cli scenario keel --install missed file: {expected_file}")
                return 1
        if "@AGENTS.md" not in (repo / "CLAUDE.md").read_text(encoding="utf-8"):
            report("cli scenario keel --install missed CLAUDE.md @AGENTS.md import.")
            return 1
        if not has_managed_block(repo / "AGENTS.md"):
            report("cli scenario keel --install missed AGENTS.md bootstrap block.")
            return 1

        check_installed = run_keel(repo, "--check")
        if check_installed.returncode != 0 or "status: installed" not in check_installed.stdout:
            report("cli scenario keel --check did not report installed.")
            report((check_installed.stderr or check_installed.stdout).strip())
            return 1

        doctor = run_keel(repo, "--doctor")
        if (
            doctor.returncode != 0
            or "keel doctor" not in doctor.stdout
            or "openspec:" not in doctor.stdout
        ):
            report("cli scenario keel --doctor did not report environment status.")
            report((doctor.stderr or doctor.stdout).strip())
            return 1

        write_text(
            repo / "openspec/changes/status-drift/tasks.md",
            "# Tasks\n\n## Invalidates\n\n- None.\n\n"
            "## Tasks\n\n"
            "- [x] A1 implementation **未提交**\n\n"
            "## Execution Status\n\n"
            "- 合入 master(a4ca804).\n\n"
            "## Current Completion\n\n"
            "- 1 / 1.\n",
        )
        tasks_drift_check = run_keel(repo, "--check")
        if (
            tasks_drift_check.returncode == 0
            or "keel state: failed" not in tasks_drift_check.stdout
            or "Execution Status" not in tasks_drift_check.stdout
            or "Current Completion" not in tasks_drift_check.stdout
            or "commit or merge state" not in tasks_drift_check.stdout
            or "contextual commit hash" not in tasks_drift_check.stdout
        ):
            report("cli scenario keel --check did not fail on tasks.md commit-status drift.")
            report((tasks_drift_check.stderr or tasks_drift_check.stdout).strip())
            return 1

        write_text(
            repo / "openspec/changes/status-drift/tasks.md",
            "# Tasks\n\n## Invalidates\n\n- None.\n\n"
            "> Boundary: tasks.md is the source for the current change's slice checklist and logical completion only. Completion state is only `[x]` / `[ ]`; progress and the default next slice are derived from the checklist. Do not record commit hashes, branch/merge state, dirty/uncommitted state, or manually computed completion counts. Durable work state belongs in OpenSpec; HANDOFF is only an explicit pointer override.\n\n"
            "## Tasks\n\n"
            "- [x] A1 implementation\n\n"
            "## Workflow Notes\n\n"
            "- None.\n",
        )
        tasks_clean_check = run_keel(repo, "--check")
        if (
            tasks_clean_check.returncode != 0
            or "keel state: ok" not in tasks_clean_check.stdout
        ):
            report("cli scenario keel --check did not accept cleaned tasks.md.")
            report((tasks_clean_check.stderr or tasks_clean_check.stdout).strip())
            return 1

        write_text(
            repo / "openspec/changes/archive/2026-07-09-finished/tasks.md",
            "# Tasks\n\n## Invalidates\n\n- None.\n\n"
            "- [x] A1 implementation\n\n"
            "## Evidence\n\n"
            "- Scope check: pre-existing dirty paths were not attributed to this task.\n",
        )
        archived_tasks_check = run_keel(repo, "--check")
        if (
            archived_tasks_check.returncode != 0
            or "keel state: ok" not in archived_tasks_check.stdout
        ):
            report("cli scenario keel --check rejected historical evidence in archived tasks.md.")
            report((archived_tasks_check.stderr or archived_tasks_check.stdout).strip())
            return 1

        legacy_handoff = "# HANDOFF\n\nactive-backlog: FU-25 (head=R3-A2)\n"
        write_text(
            repo / "keel/HANDOFF.md",
            legacy_handoff,
        )
        drift_check = run_keel(repo, "--check")
        if (
            drift_check.returncode != 0
            or "handoff: legacy" not in drift_check.stdout
            or (repo / "keel/HANDOFF.md").read_text(encoding="utf-8")
            != legacy_handoff
        ):
            report("cli scenario keel --check did not preserve and diagnose legacy HANDOFF.")
            report((drift_check.stderr or drift_check.stdout).strip())
            return 1

        update = run_keel(repo, "--update", "--dry-run")
        pack_plan = (
            "would run npm pack" in update.stdout
            or "would run npm.cmd pack" in update.stdout
        )
        install_plan = (
            'would run npm install -g "<packed-tarball>"' in update.stdout
            or 'would run npm.cmd install -g "<packed-tarball>"' in update.stdout
        )
        if (
            update.returncode != 0
            or not pack_plan
            or "@christang/keel" not in update.stdout
            or not install_plan
        ):
            report("cli scenario keel --update did not report global CLI update plan.")
            report((update.stderr or update.stdout).strip())
            return 1

        codex_repo = tmp / "codex-repo"
        codex_repo.mkdir()
        codex_install = run_keel(codex_repo, "--install", "--target", "codex")
        if codex_install.returncode != 0:
            report("cli scenario keel --install --target codex failed.")
            report((codex_install.stderr or codex_install.stdout).strip())
            return 1
        if not (codex_repo / "AGENTS.md").is_file():
            report("cli scenario codex install missed AGENTS.md.")
            return 1
        if not has_managed_block(codex_repo / "AGENTS.md"):
            report("cli scenario codex install missed AGENTS.md bootstrap block.")
            return 1
        if (codex_repo / ".claude").exists():
            report("cli scenario codex install created Claude-only paths.")
            return 1

        opencode_repo = tmp / "opencode-repo"
        opencode_repo.mkdir()
        opencode_install = run_keel(opencode_repo, "--install", "--target", "opencode")
        if opencode_install.returncode != 0:
            report("cli scenario keel --install --target opencode failed.")
            report((opencode_install.stderr or opencode_install.stdout).strip())
            return 1
        if not (opencode_repo / "AGENTS.md").is_file():
            report("cli scenario opencode install missed AGENTS.md.")
            return 1
        if not has_managed_block(opencode_repo / "AGENTS.md"):
            report("cli scenario opencode install missed AGENTS.md bootstrap block.")
            return 1

        codex_init_plan = run_keel(codex_repo, "--init", "--target", "codex", "--dry-run")
        if (
            codex_init_plan.returncode != 0
            or "--tools codex" not in codex_init_plan.stdout
        ):
            report("cli scenario codex init dry-run did not plan OpenSpec codex init.")
            report((codex_init_plan.stderr or codex_init_plan.stdout).strip())
            return 1

        before_uninstall_dry_run = snapshot_files(repo)
        uninstall_dry_run = run_keel(repo, "--uninstall", "--dry-run")
        after_uninstall_dry_run = snapshot_files(repo)
        if uninstall_dry_run.returncode != 0:
            report("cli scenario keel --uninstall --dry-run failed.")
            report((uninstall_dry_run.stderr or uninstall_dry_run.stdout).strip())
            return 1
        if "remove-managed CLAUDE.md" not in uninstall_dry_run.stdout:
            report("cli scenario uninstall dry run did not report managed removal.")
            report(uninstall_dry_run.stdout.strip())
            return 1
        if before_uninstall_dry_run != after_uninstall_dry_run:
            report("cli scenario uninstall dry run modified the repo.")
            return 1

        uninstall = run_keel(repo, "--uninstall")
        if uninstall.returncode != 0:
            report("cli scenario keel --uninstall failed.")
            report((uninstall.stderr or uninstall.stdout).strip())
            return 1
        if extract_managed_block((repo / "CLAUDE.md").read_text(encoding="utf-8")):
            report("cli scenario uninstall left CLAUDE.md managed block behind.")
            return 1
        if (repo / "keel/HANDOFF.md").read_text(encoding="utf-8") != legacy_handoff:
            report("cli scenario uninstall changed legacy HANDOFF.md.")
            return 1

        init = run_keel(repo, "--init")
        if init.returncode != 0:
            report("cli scenario keel --init failed.")
            report((init.stderr or init.stdout).strip())
            return 1
        if not has_managed_block(repo / "AGENTS.md"):
            report("cli scenario keel --init missed AGENTS.md bootstrap block.")
            return 1
        if "@AGENTS.md" not in (repo / "CLAUDE.md").read_text(encoding="utf-8"):
            report("cli scenario keel --init missed CLAUDE.md @AGENTS.md import.")
            return 1

        clear = run_keel(repo, "--clear")
        if clear.returncode != 0:
            report("cli scenario keel --clear failed.")
            report((clear.stderr or clear.stdout).strip())
            return 1
        remaining_schema = [
            p
            for p in packaged_openspec_schema_install_paths()
            if (repo / p).exists()
        ]
        if remaining_schema:
            report("cli scenario keel --clear left packaged schema behind.")
            report(", ".join(remaining_schema))
            return 1

    report("cli scenario passed.")
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
            "nextAction": {"kind": "task-start"},
        }
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
            or inferred_payload.get("nextAction") != {"kind": "task-start"}
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
            or recomputed_payload.get("nextAction") != {"kind": "change-close"}
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
            or evidence_payload.get("nextAction") != {"kind": "task-complete"}
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
            or handoff_payload.get("nextAction") != {"kind": "task-start"}
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
            or json.loads(discuss.stdout).get("nextAction") != {"kind": "discuss"}
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
            or json.loads(author.stdout).get("nextAction") != {"kind": "author"}
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
            or idle_payload.get("nextAction") != {"kind": "none"}
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
            or matching_payload.get("nextAction") != {"kind": "task-start"}
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
            or matching_handoff_payload.get("nextAction") != {"kind": "task-start"}
        ):
            report("stateless-continuity scenario did not resume a matching HANDOFF anchor.")
            report((matching_handoff.stderr or matching_handoff.stdout).strip())
            return 1

    report("stateless-continuity scenario passed.")
    return 0


def task_contract_fixture(
    *,
    mode: str = "implementation",
    touch: tuple[str, ...] = ("src/feature.js",),
    commands: tuple[str, ...] = ("M1: node test.js",),
    evidence: tuple[str, ...] = ("M1: pending",),
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
        "  - Commands:\n"
        f"{command_lines}"
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
    body = task_contract_fixture(evidence=("Contract: pending", "M1: pending"))
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
            report(f"{label} skipped: the openspec CLI is not on PATH.")
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

        # M3 — every previously accepted form still closes.
        for closure in (
            "Durable owner: openspec/changes/demo/proposal.md",
            "Durable owner: keel/archive/notes/2026-07-28-example.md",
            "Durable owner: https://github.com/TanglmChris/keel/issues/20",
            "Discard reason: it stands as written.",
        ):
            write_text(repo / "openspec/changes/demo/proposal.md", "# Proposal\n")
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


def validate_packaged_schema_derivation_scenario() -> int:
    label = "packaged-schema-derivation"

    # The helper derives the consumer-repo paths every install/uninstall/clear
    # assertion iterates. When its root stopped existing it returned an empty
    # list, so those loops compared nothing and reported success. Anchor it to
    # what the installer really writes, and make emptiness a failure here.
    try:
        packaged_openspec_schema_install_paths(ROOT / "no-such-packaged-root")
    except FileNotFoundError as error:
        if "no-such-packaged-root" not in str(error):
            report(f"{label} missing-root failure does not name the path it expected.")
            report(str(error))
            return 1
    else:
        report(
            f"{label} returned a set for a missing packaged root instead of failing; "
            "an absent root must not silently empty its callers' assertions."
        )
        return 1

    derived = packaged_openspec_schema_install_paths()
    if not derived:
        report(
            f"{label} derived no packaged schema paths, so every assertion that "
            "iterates them verifies nothing."
        )
        return 1

    with tempfile.TemporaryDirectory(prefix="keel-packaged-schema-") as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()
        install = run_keel(repo, "--install")
        if install.returncode != 0:
            report(f"{label} keel --install failed.")
            report((install.stderr or install.stdout).strip())
            return 1

        schema_root = repo / OPENSPEC_SCHEMA_ROOT
        installed = sorted(
            path.relative_to(repo).as_posix()
            for path in schema_root.rglob("*")
            if path.is_file()
        )
        if installed != sorted(derived):
            report(
                f"{label} derived paths do not match what keel --install wrote."
            )
            report(f"derived:   {sorted(derived)}")
            report(f"installed: {installed}")
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
    return task_contract_fixture().replace(
        "E1: public behavior",
        "E1: Public behavior passes.",
    ).replace(
        "  - Acceptance:\n",
        "  - Verification Strategy: evidence-first\n"
        "  - Acceptance:\n",
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
        "    - M1: node test.js\n"
        "  - Autonomy boundary:\n"
        "    - Default: hard-stop\n"
        "    - Pre-authorized fallback: none\n"
        "  - Stop Rules:\n"
        "    - Stop on failure.\n"
        "  - Evidence:\n"
        "    - M1: pending\n"
        "  - Stop if:\n"
        "    - Requires files outside Touch.\n"
    )


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
        # A task with no Verify at all is a genuine expanded v3 task and must
        # keep its existing required-field diagnostics.
        bare = task_capsule_compact_fixture()
        for block in (
            "  - Verify:\n    - Strategy: evidence-first\n    - M1: node test.js\n",
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
    if "non-concrete-verify-diagnostic" not in {name for name, _ in SCENARIOS}:
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
    if "inline-code-is-concrete" not in {name for name, _ in SCENARIOS}:
        report("inline-code-is-concrete: the scenario registry does not include it.")
        return 1
    report("inline-code-is-concrete scenario passed.")
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
        # A capability with no collision keeps the plain wording.
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
    if "covers-separator-collision" not in {name for name, _ in SCENARIOS}:
        report(
            "covers-separator-collision: the scenario registry does not include it."
        )
        return 1
    report("covers-separator-collision scenario passed.")
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
    if "unresolved-authority-names-field" not in {name for name, _ in SCENARIOS}:
        report(
            "unresolved-authority-names-field: the scenario registry does not "
            "include it."
        )
        return 1
    report("unresolved-authority-names-field scenario passed.")
    return 0


def validate_dev_only_plugin_source_scoping_scenario() -> int:
    """Issue #6: plugins/keel/ exists only in Keel's own repository.

    In a consuming project the source check is permanently `missing` and the
    next line told the author to install a plugin they had just installed.
    """
    with tempfile.TemporaryDirectory(prefix="keel-dev-only-scope-") as raw:
        consumer = Path(raw)
        init = run_keel(consumer, "--init", "--target", "claude")
        if init.returncode != 0:
            report("dev-only-plugin-source-scoping: keel --init failed.")
            report((init.stderr or init.stdout).strip())
            return 1
        doctor = run_keel(consumer, "--doctor")
        out = doctor.stdout or ""
        if "native plugin source" in out:
            report(
                "dev-only-plugin-source-scoping: a consuming project was still "
                "shown the development-only plugin source check."
            )
            report(out)
            return 1
        if "install the plugin if it is missing" in out:
            report(
                "dev-only-plugin-source-scoping: a consuming project was still "
                "told to install an already-installed plugin."
            )
            report(out)
            return 1
        if "plugin source" in out:
            report(
                "dev-only-plugin-source-scoping: the plugin source clause "
                "leaked into a consuming project's capability lines."
            )
            report(out)
            return 1
        # Keel's own repository must keep the check, which is where it means
        # something: the manifest and the CLI have to agree before release.
        own = run_keel(ROOT, "--doctor")
        if "native plugin source" not in (own.stdout or ""):
            report(
                "dev-only-plugin-source-scoping: Keel's own repository lost the "
                "plugin source check."
            )
            report((own.stdout or own.stderr).strip())
            return 1
    if "dev-only-plugin-source-scoping" not in {name for name, _ in SCENARIOS}:
        report(
            "dev-only-plugin-source-scoping: the scenario registry does not "
            "include it."
        )
        return 1
    report("dev-only-plugin-source-scoping scenario passed.")
    return 0


def validate_source_repo_bootstrap_skip_scenario() -> int:
    """Issue #9: `keel --install` must not overwrite Keel's own AGENTS.md.

    Keel's repository AGENTS.md carries the full protocol that four scenarios
    assert on; the packaged asset is the shorter consumer bootstrap. Writing it
    here drops those sections and turns the repository red.
    """
    managed = re.compile(
        r"<!--\s*keel:start.*?<!--\s*keel:end\s*-->", re.DOTALL
    )

    def block(path: Path) -> str:
        found = managed.search(path.read_text(encoding="utf-8"))
        return found.group(0) if found else ""

    own_agents = ROOT / "AGENTS.md"
    before = block(own_agents)
    if not before:
        report("source-repo-bootstrap-skip: Keel's AGENTS.md has no managed block.")
        return 1
    result = run_keel(ROOT, "--install", "--target", "claude")
    if result.returncode != 0:
        report("source-repo-bootstrap-skip: keel --install failed in Keel's repo.")
        report((result.stderr or result.stdout).strip())
        return 1
    if block(own_agents) != before:
        report(
            "source-repo-bootstrap-skip: keel --install rewrote Keel's own "
            "AGENTS.md managed block."
        )
        return 1
    if "skip AGENTS.md" not in (result.stdout or ""):
        report(
            "source-repo-bootstrap-skip: the skip was silent; it must be "
            "reported explicitly."
        )
        report((result.stdout or "").strip())
        return 1
    # A consuming project must still receive the bootstrap.
    with tempfile.TemporaryDirectory(prefix="keel-bootstrap-consumer-") as raw:
        consumer = Path(raw)
        installed = run_keel(consumer, "--install", "--target", "claude")
        if installed.returncode != 0:
            report(
                "source-repo-bootstrap-skip: keel --install failed in a "
                "consuming project."
            )
            report((installed.stderr or installed.stdout).strip())
            return 1
        asset_block = block(ROOT / "assets/bootstrap/AGENTS.md")
        if block(consumer / "AGENTS.md") != asset_block:
            report(
                "source-repo-bootstrap-skip: a consuming project did not "
                "receive the packaged bootstrap block."
            )
            return 1
    if "source-repo-bootstrap-skip" not in {name for name, _ in SCENARIOS}:
        report(
            "source-repo-bootstrap-skip: the scenario registry does not include it."
        )
        return 1
    report("source-repo-bootstrap-skip scenario passed.")
    return 0


TRACKER_OWNER = "https://github.com/TanglmChris/keel/issues/12"


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
            return run_keel(
                repo, "gate", "task-complete",
                "--change", "demo", "--task", "1.1", "--json",
            )

        def close(closure: str):
            write_text(tasks, tracker_owner_tasks("none", closure))
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

    if "tracker-durable-owner" not in {name for name, _ in SCENARIOS}:
        report("tracker-durable-owner: the scenario registry does not include it.")
        return 1
    report("tracker-durable-owner scenario passed.")
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
    if "guard-manifest-ignored" not in {name for name, _ in SCENARIOS}:
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
    if "guard-status-is-not-enforcement" not in {name for name, _ in SCENARIOS}:
        report(
            "guard-status-is-not-enforcement: the scenario registry does not "
            "include it."
        )
        return 1
    report("guard-status-is-not-enforcement scenario passed.")
    return 0


def validate_source_repo_cli_resolution_scenario() -> int:
    """Issue #13 item 3: a bare `keel` runs the installed package.

    When the repository under change *is* Keel, gate commands verify the
    installed CLI rather than the working tree, and the failure mode is a
    silently stale result rather than an error. One dogfood round was lost to
    two spurious problems reported by a stale global CLI.
    """
    own = run_keel(ROOT, "--doctor")
    out = own.stdout or ""
    if "node bin/keel.js" not in out:
        report(
            "source-repo-cli-resolution: Keel's own repository is not told to "
            "run gate commands through its own entry point."
        )
        report(out)
        return 1
    # The local entry point needs an explicit repository argument; an author
    # who copies the hint without it gets an unrelated failure.
    hint = next(
        (line for line in out.splitlines() if "node bin/keel.js" in line), ""
    )
    # The line must be advisory: it describes a hazard, not a repository
    # failure, so it must never push doctor toward a non-ok verdict.
    for needle in ("gate", ".", "advisory"):
        if needle not in hint:
            report(
                "source-repo-cli-resolution: the hint does not name a usable "
                f"invocation, or is not advisory; missing {needle!r} in: {hint}"
            )
            return 1
    with tempfile.TemporaryDirectory(prefix="keel-cli-resolution-") as raw:
        consumer = Path(raw)
        init = run_keel(consumer, "--init", "--target", "claude")
        if init.returncode != 0:
            report("source-repo-cli-resolution: keel --init failed.")
            report((init.stderr or init.stdout).strip())
            return 1
        consumer_doctor = run_keel(consumer, "--doctor")
        if "node bin/keel.js" in (consumer_doctor.stdout or ""):
            report(
                "source-repo-cli-resolution: a consuming project was shown a "
                "hazard that exists only in Keel's own repository."
            )
            report(consumer_doctor.stdout or "")
            return 1
    if "source-repo-cli-resolution" not in {name for name, _ in SCENARIOS}:
        report(
            "source-repo-cli-resolution: the scenario registry does not "
            "include it."
        )
        return 1
    report("source-repo-cli-resolution scenario passed.")
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
                "must not continue to another task",
                "must not mark tasks complete",
                "must not push",
                "must not sync or archive",
                "must not transfer Keel ownership",
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
        close_start = run_keel(
            repo,
            "gate",
            "task-start",
            "--change",
            "demo",
            "--task",
            "1.1",
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
            != f"    - Contract: keel-task-capsule/v1 sha256:{fingerprint}"
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
            != f"    - Contract: keel-task-capsule/v1 sha256:{new_fingerprint}"
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
        missing_anchor = run_keel(
            record_repo, "gate", "task-start",
            "--change", "demo", "--task", "1.1", "--record", "--json",
        )
        if (
            missing_anchor.returncode != 3
            or not any(
                problem.get("code") == "record-refused"
                for problem in json.loads(missing_anchor.stdout).get("problems", [])
            )
            or (record_repo / "keel/guard.json").exists()
        ):
            report(
                "core-gates scenario --record with a missing anchor must "
                "refuse and write nothing, not even the guard manifest."
            )
            report((missing_anchor.stderr or missing_anchor.stdout).strip())
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

        write_text(close_tasks, close_task(True, "pending"))
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

        write_text(
            close_tasks,
            close_task(True).replace("  - Covered by: 1.1", "  - pending"),
        )
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

        write_text(close_tasks, close_task(True))
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


def validate_target_capability_adapters_scenario() -> int:
    capability_keys = (
        "continuity.start",
        "continuity.reinject",
        "gate.task-start",
        "gate.task-complete",
        "gate.change-close",
        "execution.goal",
        "execution.task-view",
        "execution.worktree",
        "delegation.context",
        "delegation.return",
    )
    with tempfile.TemporaryDirectory(prefix="keel-capabilities-") as raw_tmp:
        root = Path(raw_tmp)
        for target in ("claude", "codex", "opencode"):
            repo = root / target
            repo.mkdir()
            env = dict(os.environ)
            if target == "codex":
                env["CODEX_HOME"] = str(root / "codex-home")

            install = run_keel(
                repo,
                "--install",
                "--target",
                target,
                env=env,
            )
            if install.returncode != 0:
                report(f"target-capability-adapters {target} install failed.")
                report((install.stderr or install.stdout).strip())
                return 1
            checked = run_keel(
                repo,
                "--check",
                "--target",
                target,
                env=env,
            )
            if checked.returncode != 0 or "status: installed" not in checked.stdout:
                report(f"target-capability-adapters {target} check missed adapter.")
                report((checked.stderr or checked.stdout).strip())
                return 1

            before_doctor = snapshot_files(repo)
            doctor = run_keel(
                repo,
                "--doctor",
                "--target",
                target,
                env=env,
            )
            after_doctor = snapshot_files(repo)
            if doctor.returncode != 0:
                report(f"target-capability-adapters {target} doctor failed.")
                report((doctor.stderr or doctor.stdout).strip())
                return 1
            if before_doctor != after_doctor:
                report(f"target-capability-adapters {target} doctor mutated config.")
                return 1
            for key in capability_keys:
                if f"{key}: manual" not in doctor.stdout:
                    report(
                        f"target-capability-adapters {target} did not conservatively "
                        f"report {key}."
                    )
                    report(doctor.stdout.strip())
                    return 1
            # Native target capabilities never claim enforced behavior without
            # runtime evidence; the deterministic Keel Core helper dimensions
            # (byte-stability, nested-delegation prevention) are a separate,
            # legitimately enforced surface reported on their own helper lines.
            native_surface = "\n".join(
                line
                for line in doctor.stdout.splitlines()
                if not line.startswith("helper ")
            )
            if "enforced" in native_surface:
                report(
                    f"target-capability-adapters {target} invented enforced behavior."
                )
                report(doctor.stdout.strip())
                return 1

            probe = run_keel(
                repo, "capabilities", "--target", target, "--json", env=env
            )
            if probe.returncode != 0:
                report(f"target-capability-adapters {target} capability probe failed.")
                report((probe.stderr or probe.stdout).strip())
                return 1
            probe_payload = json.loads(probe.stdout)
            if (
                probe_payload.get("schemaVersion") != 1
                or probe_payload.get("target") != target
                or set(probe_payload.get("capabilities", {})) != set(capability_keys)
            ):
                report(f"target-capability-adapters {target} probe contract mismatch.")
                report(adapter_probe.stdout.strip())
                return 1

            write_text(
                repo / "openspec/changes/demo/tasks.md",
                "# Tasks\n\n## Invalidates\n\n- None.\n\n- [ ] 1.1 Incomplete\n  - Owner: keel-agent\n",
            )
            gate = run_keel(
                repo,
                "gate",
                "task-start",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
                env=env,
            )
            if (
                gate.returncode != 3
                or json.loads(gate.stdout).get("gate") != "task-start"
                or json.loads(gate.stdout).get("status") != "fail"
            ):
                report(
                    f"target-capability-adapters {target} did not surface Core gate JSON."
                )
                report((gate.stderr or gate.stdout).strip())
                return 1

            if target == "codex":
                write_text(
                    Path(env["CODEX_HOME"]) / "hooks.json",
                    '{"unverified": true}\n',
                )
            elif target == "opencode":
                write_text(
                    repo / ".opencode/plugins/unverified.js",
                    "export default {}\n",
                )
            else:
                write_text(
                    repo / ".claude/trust-unverified",
                    "not authoritative\n",
                )
            unverified = run_keel(
                repo,
                "capabilities",
                "--target",
                target,
                "--json",
                env=env,
            )
            if (
                unverified.returncode != 0
                or any(
                    item.get("level") != "manual"
                    for item in json.loads(unverified.stdout)
                    .get("capabilities", {})
                    .values()
                )
            ):
                report(
                    f"target-capability-adapters {target} promoted unverified state."
                )
                report((unverified.stderr or unverified.stdout).strip())
                return 1

        adapter_script = ROOT / PLUGIN_ROOT / "scripts/session-start.js"
        if not adapter_script.is_file():
            report(
                "target-capability-adapters native plugin session-start script is "
                "missing."
            )
            return 1
        adapter_content = adapter_script.read_text(encoding="utf-8")
        for forbidden in ("parseTasks", "completionProblems", "compileTaskContract"):
            if forbidden in adapter_content:
                report(
                    "target-capability-adapters plugin script duplicated Core policy: "
                    f"{forbidden}"
                )
                return 1

    report("target-capability-adapters scenario passed.")
    return 0


SUPPORTED_VERIFICATION_STRATEGIES = (
    "vertical-tdd",
    "regression-first",
    "characterization",
    "snapshot-characterization",
    "rendered-behavior",
    "evidence-first",
)


def run_openspec(cwd: Path, *args: str) -> subprocess.CompletedProcess[str] | None:
    executable = shutil.which("openspec")
    if executable is None:
        return None
    return subprocess.run(
        [executable, *args],
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def validate_expectation_alignment_skill_scenario() -> int:
    """Pin document structure and spec-traceable contract anchors only.

    Every retained exact phrase cites the keel-expectation-alignment (or
    named sibling) requirement or scenario that names it; editorial wording
    no durable authority names must stay rewritable without validator edits.
    """
    skill_path = ROOT / "src/skills/keel-align-expectations/SKILL.md"
    if not skill_path.is_file():
        report("expectation-alignment-skill canonical SKILL.md is missing.")
        return 1
    skill = skill_path.read_text(encoding="utf-8")

    # Structure: Agent Skills frontmatter with trigger/non-trigger guidance.
    frontmatter = re.match(r"---\n([\s\S]*?)\n---\n", skill)
    if (
        frontmatter is None
        or "name: keel-align-expectations" not in frontmatter.group(1)
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
PLUGIN_SKILLS = (
    "keel-align-expectations",
    "keel-debug-failure",
    "keel-handoff",
    "keel-review-checklist",
    "keel-run-single-task-goal",
    "keel-tdd-or-test-first",
)


def strict_semver(version: str) -> bool:
    return bool(re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version or ""))


def validate_native_plugin_manifests_scenario() -> int:
    codex_manifest_path = ROOT / PLUGIN_ROOT / ".codex-plugin/plugin.json"
    claude_manifest_path = ROOT / PLUGIN_ROOT / ".claude-plugin/plugin.json"
    for manifest_path in (codex_manifest_path, claude_manifest_path):
        if not manifest_path.is_file():
            report(f"native-plugin-manifests missing manifest: {manifest_path}")
            return 1
    codex_manifest = json.loads(codex_manifest_path.read_text(encoding="utf-8"))
    claude_manifest = json.loads(claude_manifest_path.read_text(encoding="utf-8"))

    if codex_manifest.get("name") != "keel" or claude_manifest.get("name") != "keel":
        report("native-plugin-manifests manifests do not share the plugin name keel.")
        return 1
    package_version = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))[
        "version"
    ]
    for label, manifest in (("codex", codex_manifest), ("claude", claude_manifest)):
        version = manifest.get("version", "")
        if version.split("+")[0] != package_version or not strict_semver(version):
            report(
                f"native-plugin-manifests {label} version {version!r} is not the "
                f"strict release semver {package_version!r}."
            )
            return 1
        if not manifest.get("description") or not (
            manifest.get("author", {}).get("name")
        ):
            report(f"native-plugin-manifests {label} lacks description/author.name.")
            return 1

    if "hooks" in codex_manifest:
        report(
            "native-plugin-manifests codex manifest declares an unsupported hooks "
            "field; default discovery must load hooks/hooks.json."
        )
        return 1
    interface = codex_manifest.get("interface", {})
    if not interface.get("displayName"):
        report("native-plugin-manifests codex manifest lacks interface.displayName.")
        return 1

    for plugin_file in sorted((ROOT / PLUGIN_ROOT).rglob("*")):
        if plugin_file.is_file() and "[TODO" in plugin_file.read_text(
            encoding="utf-8", errors="replace"
        ):
            report(
                f"native-plugin-manifests unresolved scaffold marker in {plugin_file}"
            )
            return 1

    skills_root = ROOT / PLUGIN_ROOT / "skills"
    found_skills = sorted(
        entry.name for entry in skills_root.iterdir() if entry.is_dir()
    ) if skills_root.is_dir() else []
    if found_skills != sorted(PLUGIN_SKILLS):
        report(
            "native-plugin-manifests plugin skill inventory mismatch: "
            + ", ".join(found_skills)
        )
        return 1
    for skill_name in PLUGIN_SKILLS:
        plugin_skill = skills_root / skill_name / "SKILL.md"
        canonical_skill = ROOT / "src/skills" / skill_name / "SKILL.md"
        if plugin_skill.read_text(encoding="utf-8") != canonical_skill.read_text(
            encoding="utf-8"
        ):
            report(
                "native-plugin-manifests plugin skill diverges from canonical "
                f"source: {skill_name}"
            )
            return 1
    lenses_root = ROOT / "assets/lenses"
    for template in ("web.md", "hardware.md", "hardware-dsl.md"):
        if not (lenses_root / template).is_file():
            report(f"native-plugin-manifests misses lens template: {template}")
            return 1

    codex_market_path = ROOT / ".agents/plugins/marketplace.json"
    claude_market_path = ROOT / ".claude-plugin/marketplace.json"
    for market_path in (codex_market_path, claude_market_path):
        if not market_path.is_file():
            report(f"native-plugin-manifests missing marketplace: {market_path}")
            return 1
    codex_market = json.loads(codex_market_path.read_text(encoding="utf-8"))
    codex_entry = next(
        (
            entry
            for entry in codex_market.get("plugins", [])
            if entry.get("name") == "keel"
        ),
        None,
    )
    if (
        codex_entry is None
        or codex_entry.get("source", {}).get("source") != "local"
        or codex_entry.get("source", {}).get("path") != "./plugins/keel"
        or codex_entry.get("policy", {}).get("installation") not in (
            "AVAILABLE",
            "INSTALLED_BY_DEFAULT",
        )
        or not codex_entry.get("category")
    ):
        report("native-plugin-manifests codex marketplace entry is invalid.")
        return 1
    claude_market = json.loads(claude_market_path.read_text(encoding="utf-8"))
    claude_entry = next(
        (
            entry
            for entry in claude_market.get("plugins", [])
            if entry.get("name") == "keel"
        ),
        None,
    )
    if claude_entry is None or claude_entry.get("source") != "./plugins/keel":
        report("native-plugin-manifests claude marketplace entry is invalid.")
        return 1

    report("native-plugin-manifests scenario passed.")
    return 0


def run_session_start_hook(
    repo: Path,
    event: dict,
    *,
    keel_cli: str,
    timeout_ms: int | None = None,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["KEEL_CLI"] = keel_cli
    env["CLAUDE_PLUGIN_ROOT"] = str(ROOT / PLUGIN_ROOT)
    if timeout_ms is not None:
        env["KEEL_HOOK_TIMEOUT_MS"] = str(timeout_ms)
    return subprocess.run(
        ["node", str(ROOT / PLUGIN_ROOT / "scripts/session-start.js")],
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


# The projection is delivered through additionalContext, which the host injects
# into the agent and never renders for the human. Every branch must therefore
# carry the instruction to relay it, including — especially — the degraded ones,
# because a projection nobody sees is a projection nobody checks.
SESSION_START_DISCLOSURE = "to the user in your first reply"

# A host loads its plugins once per session, so the projection can be absent for
# reasons no repository check can see. The resident protocol is the carrier of
# last resort and must state the same obligation without trading away the
# continuity rules it already carried.
RESIDENT_SESSION_START_REQUIRED = (
    SESSION_START_DISCLOSURE,
    "keel context",
    "never infer continuity from native memory",
)


def resident_session_start_section(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r"^## Session Start$(.*?)^## ", text, re.MULTILINE | re.DOTALL
    )
    return match.group(1) if match else None


def validate_native_plugin_session_start_scenario() -> int:
    real_cli = f'node "{ROOT / "bin/keel.js"}"'
    codex_event = {"hook_event_name": "SessionStart", "source": "startup"}
    claude_event = {
        "hook_event_name": "SessionStart",
        "session_id": "fixture",
        "source": "startup",
    }

    with tempfile.TemporaryDirectory(
        prefix="keel-session-start-", ignore_cleanup_errors=True
    ) as raw_tmp:
        tmp = Path(raw_tmp)

        ready_repo = tmp / "ready"
        ready_repo.mkdir()
        write_text(
            ready_repo / "openspec/changes/demo/tasks.md",
            task_contract_fixture(),
        )
        before = snapshot_files(ready_repo)
        codex_result = run_session_start_hook(
            ready_repo, codex_event, keel_cli=real_cli
        )
        claude_result = run_session_start_hook(
            ready_repo, claude_event, keel_cli=real_cli
        )
        after = snapshot_files(ready_repo)
        if before != after:
            report("native-plugin-session-start hook wrote repository state.")
            return 1
        if codex_result.returncode != 0 or claude_result.returncode != 0:
            report("native-plugin-session-start ready projection did not exit 0.")
            report((codex_result.stderr or codex_result.stdout).strip())
            return 1
        codex_context = session_start_context(codex_result)
        claude_context = session_start_context(claude_result)
        if codex_context != claude_context:
            report(
                "native-plugin-session-start Codex and Claude projections diverge."
            )
            return 1
        if (
            not codex_context
            or "demo#1.1" not in codex_context
            or "task-start" not in codex_context
            or "disposable" not in codex_context
            or SESSION_START_DISCLOSURE not in codex_context
        ):
            report(
                "native-plugin-session-start ready projection lacks concise "
                "context: " + repr(codex_context)
            )
            return 1
        for forbidden in ("fingerprint recorded", "goal created"):
            if forbidden in (codex_context or ""):
                report("native-plugin-session-start projection overstepped.")
                return 1

        idle_repo = tmp / "idle"
        (idle_repo / "openspec/changes").mkdir(parents=True)
        idle_result = run_session_start_hook(
            idle_repo, codex_event, keel_cli=real_cli
        )
        idle_context = session_start_context(idle_result)
        if (
            idle_result.returncode != 0
            or not idle_context
            or "idle" not in idle_context
            or SESSION_START_DISCLOSURE not in idle_context
        ):
            report(
                "native-plugin-session-start idle projection did not disclose "
                "its status to the user: " + repr(idle_context)
            )
            return 1

        ambiguous_repo = tmp / "ambiguous"
        ambiguous_repo.mkdir()
        for change in ("alpha", "beta"):
            write_text(
                ambiguous_repo / f"openspec/changes/{change}/tasks.md",
                task_contract_fixture(),
            )
        ambiguous_result = run_session_start_hook(
            ambiguous_repo, codex_event, keel_cli=real_cli
        )
        ambiguous_context = session_start_context(ambiguous_result)
        if (
            ambiguous_result.returncode != 0
            or not ambiguous_context
            or "ambiguous" not in ambiguous_context
            or "keel context" not in ambiguous_context
            or SESSION_START_DISCLOSURE not in ambiguous_context
            or "alpha#1.1" in ambiguous_context
        ):
            report(
                "native-plugin-session-start ambiguous projection guessed or "
                "lacked the explicit next command: " + repr(ambiguous_context)
            )
            return 1

        outside_repo = tmp / "not-openspec"
        outside_repo.mkdir()
        outside_result = run_session_start_hook(
            outside_repo, codex_event, keel_cli=real_cli
        )
        if outside_result.returncode != 0 or outside_result.stdout.strip():
            report(
                "native-plugin-session-start emitted context outside an OpenSpec "
                "repository."
            )
            return 1

        missing_result = run_session_start_hook(
            ready_repo, codex_event, keel_cli="keel-definitely-missing-cli-xyz"
        )
        missing_context = session_start_context(missing_result)
        if (
            missing_result.returncode != 0
            or not missing_context
            or "missing or incompatible" not in missing_context
            or "keel context" not in missing_context
            or SESSION_START_DISCLOSURE not in missing_context
        ):
            report("native-plugin-session-start missing-CLI fallback failed.")
            report(repr(missing_context))
            return 1

        malformed_cli = tmp / "malformed.js"
        write_text(
            malformed_cli,
            "if (process.argv.includes('--version')) {\n"
            "  console.log('keel 3.0.0');\n"
            "} else {\n"
            "  process.stdout.write('this is not json');\n"
            "}\n",
        )
        malformed_result = run_session_start_hook(
            ready_repo, codex_event, keel_cli=f'node "{malformed_cli}"'
        )
        malformed_context = session_start_context(malformed_result)
        if (
            malformed_result.returncode != 0
            or not malformed_context
            or "malformed" not in malformed_context
            or SESSION_START_DISCLOSURE not in malformed_context
        ):
            report("native-plugin-session-start malformed-output fallback failed.")
            report(repr(malformed_context))
            return 1

        hang_cli = tmp / "hang.js"
        write_text(
            hang_cli,
            "if (process.argv.includes('--version')) {\n"
            "  console.log('keel 3.0.0');\n"
            "} else {\n"
            "  setTimeout(() => {}, 2500);\n"
            "}\n",
        )
        hang_result = run_session_start_hook(
            ready_repo,
            codex_event,
            keel_cli=f'node "{hang_cli}"',
            timeout_ms=700,
        )
        hang_context = session_start_context(hang_result)
        if (
            hang_result.returncode != 0
            or not hang_context
            or "failed or timed out" not in hang_context
            or SESSION_START_DISCLOSURE not in hang_context
        ):
            report("native-plugin-session-start timeout fallback failed.")
            report(repr(hang_context))
            return 1

    hooks_config = json.loads(
        (ROOT / PLUGIN_ROOT / "hooks/hooks.json").read_text(encoding="utf-8")
    )
    session_hooks = hooks_config.get("hooks", {}).get("SessionStart", [])
    if not session_hooks or "session-start.js" not in json.dumps(session_hooks):
        report("native-plugin-session-start hooks.json does not wire the script.")
        return 1
    declared_events = sorted(hooks_config.get("hooks", {}))
    if declared_events != ["PreToolUse", "SessionStart"]:
        report(
            "native-plugin-session-start hooks.json declares unexpected events: "
            + ", ".join(declared_events)
        )
        return 1

    resident = resident_session_start_section(ROOT / "AGENTS.md")
    if resident is None:
        report(
            "native-plugin-session-start resident AGENTS.md has no Session "
            "Start section."
        )
        return 1
    for needle in RESIDENT_SESSION_START_REQUIRED:
        if needle not in resident:
            report(
                "native-plugin-session-start resident Session Start section is "
                f"missing: {needle}"
            )
            return 1

    report("native-plugin-session-start scenario passed.")
    return 0


def claude_cli() -> str | None:
    candidates = [
        shutil.which("claude"),
        str(Path.home() / "AppData/Roaming/npm/claude.cmd"),
    ]
    for candidate in candidates:
        if not candidate or not Path(candidate).exists():
            continue
        probe = subprocess.run(
            [candidate, "--version"],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        if probe.returncode == 0:
            return candidate
    return None


def validate_native_plugin_marketplaces_scenario() -> int:
    codex = shutil.which("codex")
    claude = claude_cli()
    if codex is None or claude is None:
        return skip_scenario(
            "native-plugin-marketplaces",
            "requires the codex and claude CLIs, which are not installed; it "
            "probes native marketplace behavior no CI runner provides",
        )

    with tempfile.TemporaryDirectory(prefix="keel-native-market-") as raw_tmp:
        tmp = Path(raw_tmp)

        codex_home = tmp / "codex-home"
        codex_home.mkdir()
        codex_env = os.environ.copy()
        codex_env["CODEX_HOME"] = str(codex_home)

        def run_codex(*args: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [codex, *args],
                cwd=ROOT,
                env=codex_env,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )

        market_add = run_codex("plugin", "marketplace", "add", str(ROOT))
        if market_add.returncode != 0:
            report("native-plugin-marketplaces codex marketplace add failed:")
            report((market_add.stderr or market_add.stdout).strip())
            return 1
        market_name = json.loads(
            (ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8")
        )["name"]
        plugin_add = run_codex("plugin", "add", f"keel@{market_name}")
        if plugin_add.returncode != 0:
            report("native-plugin-marketplaces codex plugin add failed:")
            report((plugin_add.stderr or plugin_add.stdout).strip())
            return 1
        plugin_list = run_codex("plugin", "list")
        if plugin_list.returncode != 0 or "keel" not in plugin_list.stdout:
            report("native-plugin-marketplaces codex plugin list does not show keel.")
            report((plugin_list.stderr or plugin_list.stdout).strip())
            return 1
        plugin_remove = run_codex("plugin", "remove", f"keel@{market_name}")
        if plugin_remove.returncode != 0:
            report("native-plugin-marketplaces codex plugin remove failed:")
            report((plugin_remove.stderr or plugin_remove.stdout).strip())
            return 1

        claude_config = tmp / "claude-config"
        claude_config.mkdir()
        claude_env = os.environ.copy()
        claude_env["CLAUDE_CONFIG_DIR"] = str(claude_config)

        def run_claude(*args: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [claude, *args],
                cwd=ROOT,
                env=claude_env,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )

        validated = run_claude(
            "plugin", "validate", "--strict", str(ROOT / PLUGIN_ROOT)
        )
        if validated.returncode != 0:
            report("native-plugin-marketplaces claude plugin validate failed:")
            report((validated.stderr or validated.stdout).strip())
            return 1
        claude_market_add = run_claude("plugin", "marketplace", "add", str(ROOT))
        if claude_market_add.returncode != 0:
            report("native-plugin-marketplaces claude marketplace add failed:")
            report((claude_market_add.stderr or claude_market_add.stdout).strip())
            return 1
        claude_market_name = json.loads(
            (ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8")
        )["name"]
        claude_install = run_claude(
            "plugin", "install", f"keel@{claude_market_name}"
        )
        if claude_install.returncode != 0:
            report("native-plugin-marketplaces claude plugin install failed:")
            report((claude_install.stderr or claude_install.stdout).strip())
            return 1
        claude_uninstall = run_claude("plugin", "uninstall", "keel")
        if claude_uninstall.returncode != 0:
            report("native-plugin-marketplaces claude plugin uninstall failed:")
            report((claude_uninstall.stderr or claude_uninstall.stdout).strip())
            return 1

        personal_market = Path.home() / ".agents/plugins/marketplace.json"
        if personal_market.exists() and str(codex_home) not in str(personal_market):
            before_after_guard = personal_market.read_text(encoding="utf-8")
            if "keel-native-market" in before_after_guard:
                report(
                    "native-plugin-marketplaces wrote isolation paths into the "
                    "personal marketplace."
                )
                return 1

    report("native-plugin-marketplaces scenario passed.")
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
        claude_surfaces = (
            claude_repo / ".claude/skills/openspec-propose/SKILL.md",
            claude_repo / ".claude/commands/opsx/propose.md",
        )
        for surface in claude_surfaces:
            content = surface.read_text(encoding="utf-8")
            if (
                content.count(OPENSPEC_SURFACE_OVERLAY_START) != 1
                or "Keel Authoring Overlay" not in content
                or "keel-align-expectations" not in content
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
            codex_repo / ".codex/skills/openspec-propose/SKILL.md",
            codex_home / "prompts/opsx-propose.md",
        )
        for surface in codex_surfaces:
            content = surface.read_text(encoding="utf-8")
            if (
                content.count(OPENSPEC_SURFACE_OVERLAY_START) != 1
                or "Keel Authoring Overlay" not in content
                or "keel-align-expectations" not in content
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
            codex_repo / ".codex/skills/openspec-apply-change/SKILL.md"
        ).read_text(encoding="utf-8")
        if (
            "rerun `keel-align-expectations`" not in apply_skill
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
    if which is None or which.returncode != 0:
        report("compact-task-authoring could not resolve the schema through OpenSpec.")
        if which is not None:
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


def validate_native_runtime_projection_scenario() -> int:
    core_events = ("startup", "resume", "compaction")

    def projection_task(acceptance: str = "observable result") -> str:
        return (
            "# Tasks\n\n## Invalidates\n\n- None.\n\n"
            "- [ ] 1.1 Project selected behavior\n"
            "  - Owner: keel-agent\n"
            "  - Mode: implementation\n"
            "  - Covers:\n"
            "    - E1: native projection\n"
            "  - Read:\n"
            "    - README.md\n"
            "  - Touch:\n"
            "    - src/feature.js\n"
            "  - Commands:\n"
            "    - M1: node test.js\n"
            "  - Acceptance:\n"
            f"    - {acceptance}\n"
            "  - Autonomy boundary:\n"
            "    - Default: hard-stop\n"
            "  - Coupling: none\n"
            "  - Candidate Boundary:\n"
            "    - one candidate\n"
            "  - Stop Rules:\n"
            "    - stop on failure\n"
            "  - Evidence:\n"
            "    - M1: pending\n"
            "    - Review:\n"
            "      - Status: pending\n"
            "      - Acceptance check: pending\n"
            "      - Scope check: pending\n"
            "      - Findings: pending\n"
            "    - Blocker: none\n"
            "  - Stop if:\n"
            "    - scope exceeds Touch\n"
            "  - Report:\n"
            "    - Summary\n"
        )

    with tempfile.TemporaryDirectory(prefix="keel-projection-") as raw_tmp:
        root = Path(raw_tmp)
        for target in ("codex", "claude"):
            repo = root / target
            repo.mkdir()
            env = dict(os.environ)
            if target == "codex":
                env["CODEX_HOME"] = str(root / "codex-home")
            installed = run_keel(
                repo,
                "--install",
                "--target",
                target,
                env=env,
            )
            if installed.returncode != 0:
                report(f"native-runtime-projection {target} install failed.")
                return 1
            tasks_path = repo / "openspec/changes/demo/tasks.md"
            write_text(tasks_path, projection_task())
            write_text(
                repo / f".{target}/memory/native-state.md",
                "must not be authority\n",
            )
            write_text(
                repo / f".{target}/transcripts/session.json",
                '{"complete": true}\n',
            )
            for native_aid in (
                "checkpoints/rewind.json",
                "automations/schedule.json",
                "channels/current.json",
                "agent-view/team.json",
            ):
                write_text(
                    repo / f".{target}/{native_aid}",
                    '{"available": true}\n',
                )
            projections = []
            before_projection = snapshot_files(repo)
            for core_event in core_events:
                projected = run_keel(
                    repo,
                    "project",
                    "--target",
                    target,
                    "--event",
                    core_event,
                    "--change",
                    "demo",
                    "--task",
                    "1.1",
                    "--json",
                    env=env,
                )
                if projected.returncode != 0:
                    report(
                        f"native-runtime-projection {target} event "
                        f"{core_event} failed."
                    )
                    report((projected.stderr or projected.stdout).strip())
                    return 1
                payload = json.loads(projected.stdout)
                projections.append(payload)
                if (
                    payload.get("schemaVersion") != 1
                    or payload.get("status") != "ready"
                    or payload.get("target") != target
                    or payload.get("source", {}).get("owner")
                    != "openspec/changes/demo/tasks.md#1.1"
                    or payload.get("capability", {}).get("level") != "manual"
                    or payload.get("projection", {}).get("objective")
                    != "Project selected behavior"
                ):
                    report(
                        f"native-runtime-projection {target} projection mismatch."
                    )
                    report(projected.stdout.strip())
                    return 1
            after_projection = snapshot_files(repo)
            if before_projection != after_projection:
                report(f"native-runtime-projection {target} mutated project state.")
                return 1
            if [item.get("event") for item in projections] != [
                "startup",
                "resume",
                "compaction",
            ]:
                report(
                    f"native-runtime-projection {target} native mapping mismatch."
                )
                return 1

            gated = run_keel(
                repo,
                "gate",
                "task-start",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
                env=env,
            )
            gate_contract = json.loads(gated.stdout).get("contract", {})
            if gated.returncode != 0 or not gate_contract:
                report(
                    f"native-runtime-projection {target} could not compile gate contract."
                )
                return 1
            for payload in projections:
                projection = payload.get("projection", {})
                if (
                    payload.get("contract") != gate_contract
                    or projection.get("fingerprint")
                    != gate_contract.get("fingerprint")
                    or projection.get("helperAuthority")
                    != "read-only-evidence-only"
                    or projection.get("prohibitions")
                    != gate_contract.get("capsule", {}).get("prohibitions")
                ):
                    report(
                        f"native-runtime-projection {target} did not consume capsule."
                    )
                    report(json.dumps(payload, indent=2))
                    return 1

            unauthorized_goal = run_keel(
                repo,
                "project",
                "--target",
                target,
                "--event",
                "goal",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
                env=env,
            )
            if (
                unauthorized_goal.returncode != 0
                or json.loads(unauthorized_goal.stdout).get("status") != "blocked"
            ):
                report(f"native-runtime-projection {target} enabled goal implicitly.")
                return 1

            authorized_task_view = run_keel(
                repo,
                "project",
                "--target",
                target,
                "--event",
                "task-view",
                "--authorize",
                "task-view",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
                env=env,
            )
            if (
                authorized_task_view.returncode != 0
                or json.loads(authorized_task_view.stdout).get("status") != "ready"
                or "[ ] 1.1" not in tasks_path.read_text(encoding="utf-8")
            ):
                report(
                    f"native-runtime-projection {target} task view was not one-way."
                )
                return 1

            authorized_goal = run_keel(
                repo,
                "project",
                "--target",
                target,
                "--event",
                "goal",
                "--authorize",
                "goal",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--native-complete",
                "--json",
                env=env,
            )
            goal_payload = json.loads(authorized_goal.stdout)
            if (
                authorized_goal.returncode != 0
                or goal_payload.get("status") != "ready"
                or goal_payload.get("projection", {}).get("acceptance")
                != ["observable result"]
                or not goal_payload.get("projection", {}).get("stopBoundary")
                or not any(
                    "ignored" in warning.lower()
                    for warning in goal_payload.get("warnings", [])
                )
                or "[ ] 1.1" not in tasks_path.read_text(encoding="utf-8")
            ):
                report(
                    f"native-runtime-projection {target} authorized goal violated "
                    "one-way projection."
                )
                report((authorized_goal.stderr or authorized_goal.stdout).strip())
                return 1

            unauthorized_subagent = run_keel(
                repo,
                "project",
                "--target",
                target,
                "--event",
                "subagent-start",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
                env=env,
            )
            if json.loads(unauthorized_subagent.stdout).get("status") != "blocked":
                report(
                    f"native-runtime-projection {target} activated subagent implicitly."
                )
                return 1

            authorized_subagent = run_keel(
                repo,
                "project",
                "--target",
                target,
                "--event",
                "subagent-start",
                "--authorize",
                "subagent",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
                env=env,
            )
            subagent_payload = json.loads(authorized_subagent.stdout)
            bounded = subagent_payload.get("projection", {})
            if (
                authorized_subagent.returncode != 0
                or bounded.get("read")
                != subagent_payload.get("contract", {}).get("capsule", {}).get("read")
                or "README.md" not in bounded.get("read", [])
                or "openspec/changes/demo/tasks.md" not in bounded.get("read", [])
                or bounded.get("touch") != ["src/feature.js"]
                or "M1: node test.js" not in bounded.get("evidenceContract", [])
                or not any(
                    "must not mark tasks complete" in item
                    for item in bounded.get("prohibitions", [])
                )
            ):
                report(
                    f"native-runtime-projection {target} subagent context was unbounded."
                )
                report(
                    (authorized_subagent.stderr or authorized_subagent.stdout).strip()
                )
                return 1

            subagent_return = run_keel(
                repo,
                "project",
                "--target",
                target,
                "--event",
                "subagent-stop",
                "--authorize",
                "subagent",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--native-complete",
                "--json",
                env=env,
            )
            if (
                subagent_return.returncode != 0
                or json.loads(subagent_return.stdout)
                .get("projection", {})
                .get("returnAuthority")
                != "report-and-evidence-only"
                or "[ ] 1.1" not in tasks_path.read_text(encoding="utf-8")
            ):
                report(
                    f"native-runtime-projection {target} accepted subagent completion."
                )
                return 1
            completion_after_subagent = run_keel(
                repo,
                "gate",
                "task-complete",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
                env=env,
            )
            if (
                completion_after_subagent.returncode != 3
                or json.loads(completion_after_subagent.stdout).get("status")
                != "fail"
            ):
                report(
                    f"native-runtime-projection {target} subagent result satisfied "
                    "task-complete."
                )
                return 1

            write_text(tasks_path, projection_task("changed durable acceptance"))
            recomputed = run_keel(
                repo,
                "project",
                "--target",
                target,
                "--event",
                "resume",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
                env=env,
            )
            if (
                json.loads(recomputed.stdout).get("projection", {}).get("acceptance")
                != ["changed durable acceptance"]
            ):
                report(
                    f"native-runtime-projection {target} reused native memory state."
                )
                return 1

            anchor = gate_contract.get("fingerprint", {}).get("value", "")
            if not re.fullmatch(r"[0-9a-f]{64}", anchor):
                report(
                    f"native-runtime-projection {target} could not create a task anchor."
                )
                return 1
            anchored_task = projection_task().replace(
                "  - Evidence:\n",
                "  - Evidence:\n"
                f"    - Contract: keel-task-capsule/v1 sha256:{anchor}\n",
            )
            write_text(tasks_path, anchored_task)
            write_text(
                tasks_path,
                anchored_task.replace(
                    "observable result",
                    "drifted durable acceptance",
                ),
            )
            drifted_projection = run_keel(
                repo,
                "project",
                "--target",
                target,
                "--event",
                "resume",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
                env=env,
            )
            drifted_payload = json.loads(drifted_projection.stdout)
            if (
                drifted_payload.get("status") != "blocked"
                or drifted_payload.get("projection") is not None
                or not any(
                    "fingerprint" in reason.lower() or "drift" in reason.lower()
                    for reason in drifted_payload.get("reasons", [])
                )
            ):
                report(
                    f"native-runtime-projection {target} projected drifted authority."
                )
                report(
                    (drifted_projection.stderr or drifted_projection.stdout).strip()
                )
                return 1

            invalid_task = projection_task().replace(
                "E1: native projection",
                "missing-capability / Missing requirement / Missing scenario",
            )
            write_text(tasks_path, invalid_task)
            invalid_projection = run_keel(
                repo,
                "project",
                "--target",
                target,
                "--event",
                "resume",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
                env=env,
            )
            invalid_payload = json.loads(invalid_projection.stdout)
            if (
                invalid_payload.get("status") != "blocked"
                or invalid_payload.get("contract") is not None
                or invalid_payload.get("projection") is not None
            ):
                report(
                    f"native-runtime-projection {target} projected invalid authority."
                )
                report((invalid_projection.stderr or invalid_projection.stdout).strip())
                return 1

            malformed_task = projection_task().replace(
                "M1: node test.js",
                "X1: node test.js",
            )
            write_text(tasks_path, malformed_task)
            malformed_projection = run_keel(
                repo,
                "project",
                "--target",
                target,
                "--event",
                "resume",
                "--change",
                "demo",
                "--task",
                "1.1",
                "--json",
                env=env,
            )
            malformed_payload = json.loads(malformed_projection.stdout)
            if (
                malformed_payload.get("status") != "blocked"
                or malformed_payload.get("contract") is not None
                or malformed_payload.get("projection") is not None
                or "M<n>" not in " ".join(malformed_payload.get("reasons", []))
            ):
                report(
                    f"native-runtime-projection {target} accepted malformed verification."
                )
                report(
                    (malformed_projection.stderr or malformed_projection.stdout).strip()
                )
                return 1

        worktree_repo = root / "worktree-main"
        worktree_repo.mkdir()
        write_text(
            worktree_repo / "openspec/changes/demo/tasks.md",
            projection_task(),
        )
        for command in (
            ["git", "init", "--quiet"],
            ["git", "config", "user.email", "keel@example.invalid"],
            ["git", "config", "user.name", "Keel Fixture"],
            ["git", "add", "."],
            ["git", "commit", "--quiet", "-m", "projection baseline"],
        ):
            result = subprocess.run(
                command,
                cwd=worktree_repo,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                report("native-runtime-projection could not create worktree baseline.")
                report(result.stderr.strip())
                return 1
        worktree = root / "worktree-secondary"
        added = subprocess.run(
            ["git", "worktree", "add", "--quiet", "-b", "projection-secondary", str(worktree)],
            cwd=worktree_repo,
            text=True,
            capture_output=True,
            check=False,
        )
        if added.returncode != 0:
            report("native-runtime-projection could not create secondary worktree.")
            report(added.stderr.strip())
            return 1
        same_owner = run_keel(
            worktree,
            "project",
            "--target",
            "codex",
            "--event",
            "worktree",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--expected-owner",
            "openspec/changes/demo/tasks.md#1.1",
            "--json",
        )
        if (
            same_owner.returncode != 0
            or json.loads(same_owner.stdout).get("status") != "ready"
        ):
            report("native-runtime-projection did not preserve worktree owner.")
            report((same_owner.stderr or same_owner.stdout).strip())
            return 1
        (worktree / "openspec/changes/demo/tasks.md").unlink()
        divergent = run_keel(
            worktree,
            "project",
            "--target",
            "codex",
            "--event",
            "worktree",
            "--change",
            "demo",
            "--task",
            "1.1",
            "--expected-owner",
            "openspec/changes/demo/tasks.md#1.1",
            "--json",
        )
        if (
            divergent.returncode != 0
            or json.loads(divergent.stdout).get("status") != "blocked"
        ):
            report("native-runtime-projection did not block divergent worktree.")
            report((divergent.stderr or divergent.stdout).strip())
            return 1

    projection_source = (ROOT / "src/core/projection.js").read_text(encoding="utf-8")
    for forbidden in ("parseTasks", "field(task"):
        if forbidden in projection_source:
            report(
                "native-runtime-projection retained an independent task parser: "
                f"{forbidden}"
            )
            return 1

    report("native-runtime-projection scenario passed.")
    return 0


NATIVE_GOAL_VERSION = "keel-native-goal/v1"


def _goal_tasks_file(blocks: list[str]) -> str:
    return "# Tasks\n\n## Invalidates\n\n- None.\n\n" + "\n\n".join(blocks) + "\n"


def _goal_task_block(
    task_id: str = "1.1",
    title: str = "Deliver one bounded behavior",
    checked: bool = False,
    acceptance: tuple[str, ...] = ("Observable result is proven by M1.",),
    strategy: str | None = None,
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


def validate_native_goal_projection_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-native-goal-") as raw_tmp:
        root = Path(raw_tmp)
        goals: dict[str, dict] = {}
        for target in ("codex", "claude"):
            repo = root / target
            repo.mkdir()
            env = dict(os.environ)
            if target == "codex":
                env["CODEX_HOME"] = str(root / "codex-home")
            if run_keel(repo, "--install", "--target", target, env=env).returncode != 0:
                report("native-goal-projection %s install failed." % target)
                return 1
            write_text(
                repo / "openspec/changes/sample-change/tasks.md",
                _goal_tasks_file([_goal_task_block(strategy="vertical-tdd")]),
            )
            # A native "already complete" signal must never be treated as authority.
            write_text(
                repo / (".%s/transcripts/session.json" % target),
                '{"complete": true}\n',
            )
            before = snapshot_files(repo)
            projected = run_keel(
                repo, "project", "goal",
                "--target", target,
                "--change", "sample-change",
                "--task", "1.1",
                "--json",
                env=env,
            )
            if projected.returncode != 0:
                report("native-goal-projection %s did not compile a ready goal." % target)
                report((projected.stderr or projected.stdout).strip())
                return 1
            payload = json.loads(projected.stdout)
            goal = payload.get("goal") or {}
            gate = run_keel(
                repo, "gate", "task-start",
                "--change", "sample-change", "--task", "1.1", "--no-guard",
                "--json",
                env=env,
            )
            fingerprint = json.loads(gate.stdout).get("contract", {}).get("fingerprint", {})
            if gate.returncode != 0 or not fingerprint:
                report("native-goal-projection %s could not compile the gate fingerprint." % target)
                return 1
            if (
                payload.get("version") != NATIVE_GOAL_VERSION
                or payload.get("status") != "ready"
                or payload.get("target") != target
                or goal.get("version") != NATIVE_GOAL_VERSION
                or goal.get("change") != "sample-change"
                or goal.get("task") != "1.1"
                or goal.get("fingerprint") != fingerprint
                or goal.get("objective") != "Deliver one bounded behavior"
                or goal.get("acceptance") != ["Observable result is proven by M1."]
                or goal.get("commands") != ["M1: node test.js"]
                or goal.get("verificationStrategy") != "vertical-tdd"
                or goal.get("touch") != ["src/feature.js"]
                or goal.get("ownership") != "current-agent-sole-writer"
                or goal.get("terminalStates") != ["complete", "blocked", "paused"]
                or not goal.get("stopBoundary")
                or not goal.get("condition")
                or goal.get("authorizationEvidence", {}).get("fingerprint")
                != fingerprint.get("value")
            ):
                report("native-goal-projection %s payload was incomplete." % target)
                report(json.dumps(payload, indent=2))
                return 1
            if "task-complete passes" not in goal.get("condition", ""):
                report("native-goal-projection %s omitted the terminal completion condition." % target)
                return 1
            # The projection is disposable: no Keel-owned goal/cursor state is written.
            if before != snapshot_files(repo):
                report("native-goal-projection %s mutated durable state." % target)
                return 1
            if target == "claude" and goal.get("conditionLength", 0) > 4000:
                report("native-goal-projection claude exceeded the 4,000-character budget.")
                return 1
            goals[target] = goal

        # Codex and Claude normalize to the same semantic fields.
        def _semantic(goal: dict) -> dict:
            copy = dict(goal)
            copy.pop("target", None)
            copy.pop("authorizationEvidence", None)
            return copy

        if _semantic(goals["codex"]) != _semantic(goals["claude"]):
            report("native-goal-projection codex and claude diverged on semantic fields.")
            return 1

        # Rejections never write task, goal, or session state.
        repo = root / "codex"
        env = dict(os.environ)
        env["CODEX_HOME"] = str(root / "codex-home")

        def _reject(args: list[str], label: str) -> bool:
            before = snapshot_files(repo)
            result = run_keel(repo, "project", "goal", *args, "--json", env=env)
            if result.returncode == 0:
                report("native-goal-projection accepted %s." % label)
                return False
            payload = json.loads(result.stdout)
            if payload.get("status") != "blocked" or payload.get("goal") is not None:
                report("native-goal-projection %s was not a clean block." % label)
                return False
            if before != snapshot_files(repo):
                report("native-goal-projection %s mutated state." % label)
                return False
            return True

        # Unsupported OpenCode target.
        if not _reject(
            ["--target", "opencode", "--change", "sample-change", "--task", "1.1"],
            "opencode target",
        ):
            return 1
        # Missing explicit task selection.
        if not _reject(
            ["--target", "codex", "--change", "sample-change"],
            "missing task selection",
        ):
            return 1
        # Task-group / ambiguous selection (a section id, not one executable task).
        if not _reject(
            ["--target", "codex", "--change", "sample-change", "--task", "1"],
            "task-group selection",
        ):
            return 1

        # A completed task never re-activates.
        write_text(
            repo / "openspec/changes/sample-change/tasks.md",
            _goal_tasks_file(
                [
                    _goal_task_block(task_id="1.1", checked=True, filled=True),
                    _goal_task_block(task_id="1.2", title="Second bounded behavior"),
                ]
            ),
        )
        if not _reject(
            ["--target", "codex", "--change", "sample-change", "--task", "1.1"],
            "completed task",
        ):
            return 1

        # An invalid task-start contract never compiles a goal.
        write_text(
            repo / "openspec/changes/sample-change/tasks.md",
            _goal_tasks_file([_goal_task_block(strategy="teleport")]),
        )
        if not _reject(
            ["--target", "codex", "--change", "sample-change", "--task", "1.1"],
            "invalid task-start contract",
        ):
            return 1

        # A projection that could not fit executable authority on Claude is refused
        # rather than silently truncated; Codex, without the limit, still compiles.
        huge = ("Acceptance " + ("A" * 4200) + " is proven by M1.",)
        oversized = _goal_tasks_file([_goal_task_block(acceptance=huge, strategy="vertical-tdd")])
        write_text(repo / "openspec/changes/sample-change/tasks.md", oversized)
        write_text((root / "claude") / "openspec/changes/sample-change/tasks.md", oversized)
        claude_over = run_keel(
            root / "claude", "project", "goal",
            "--target", "claude",
            "--change", "sample-change", "--task", "1.1", "--json",
            env=dict(os.environ),
        )
        claude_payload = json.loads(claude_over.stdout)
        if claude_over.returncode == 0 or claude_payload.get("status") != "blocked":
            report("native-goal-projection claude accepted an oversized condition.")
            return 1
        if "4,000" not in " ".join(claude_payload.get("reasons", [])) and "4000" not in " ".join(
            claude_payload.get("reasons", [])
        ):
            report("native-goal-projection claude blocked without citing the character budget.")
            return 1
        codex_over = run_keel(
            repo, "project", "goal",
            "--target", "codex",
            "--change", "sample-change", "--task", "1.1", "--json",
            env=env,
        )
        if codex_over.returncode != 0 or json.loads(codex_over.stdout).get("status") != "ready":
            report("native-goal-projection codex rejected a valid oversized-for-claude condition.")
            return 1

    report("native-goal-projection scenario passed.")
    return 0


NATIVE_TASKS_VIEW_VERSION = "keel-native-tasks/v1"


def validate_native_tasks_view_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-native-tasks-") as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()
        write_text(
            repo / "openspec/changes/sample-change/tasks.md",
            _goal_tasks_file(
                [
                    _goal_task_block(
                        task_id="1.1", checked=True, filled=True,
                        strategy="vertical-tdd",
                    ),
                    _goal_task_block(
                        task_id="1.2", title="Second bounded behavior",
                        strategy="vertical-tdd",
                    ),
                ]
            ),
        )

        # E1: the view compiles the whole checklist without writing anything.
        before = snapshot_files(repo)
        compiled = run_keel(
            repo, "project", "tasks",
            "--target", "claude", "--change", "sample-change", "--json",
        )
        if compiled.returncode != 0:
            report("native-tasks-view did not compile a ready view.")
            report((compiled.stderr or compiled.stdout).strip())
            return 1
        payload = json.loads(compiled.stdout)
        view = payload.get("view") or {}
        gate = run_keel(
            repo, "gate", "task-start",
            "--change", "sample-change", "--task", "1.2", "--no-guard", "--json",
        )
        fingerprint = json.loads(gate.stdout).get("contract", {}).get("fingerprint", {})
        if gate.returncode != 0 or not fingerprint:
            report("native-tasks-view could not compile the gate fingerprint.")
            return 1
        if (
            payload.get("version") != NATIVE_TASKS_VIEW_VERSION
            or payload.get("status") != "ready"
            or payload.get("target") != "claude"
            or payload.get("source", {}).get("authority") != "OpenSpec"
            or view.get("version") != NATIVE_TASKS_VIEW_VERSION
            or view.get("change") != "sample-change"
            or view.get("tasks") != [
                {
                    "id": "1.1",
                    "title": "Deliver one bounded behavior",
                    "checked": True,
                },
                {
                    "id": "1.2",
                    "title": "Second bounded behavior",
                    "checked": False,
                },
            ]
            or view.get("defaultTask") != "1.2"
            or view.get("fingerprint") != fingerprint
            or view.get("mirroring") != "current-agent-manual"
        ):
            report("native-tasks-view payload was incomplete.")
            report(json.dumps(payload, indent=2))
            return 1
        if before != snapshot_files(repo):
            report("native-tasks-view mutated durable state.")
            return 1

        # Non-Claude targets are refused without writing anything.
        for target in ("codex", "opencode"):
            refused = run_keel(
                repo, "project", "tasks",
                "--target", target, "--change", "sample-change", "--json",
            )
            if refused.returncode == 0:
                report("native-tasks-view accepted the %s target." % target)
                return 1
            refusal = json.loads(refused.stdout)
            if refusal.get("status") != "blocked" or refusal.get("view") is not None:
                report("native-tasks-view %s refusal was not a clean block." % target)
                return 1
            if before != snapshot_files(repo):
                report("native-tasks-view %s refusal mutated state." % target)
                return 1

        # The view projects a change checklist, never one task selection.
        singled = run_keel(
            repo, "project", "tasks",
            "--target", "claude", "--change", "sample-change", "--task", "1.2",
        )
        if singled.returncode == 0:
            report("native-tasks-view accepted a --task selection.")
            return 1

    readme = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
    if "keel project tasks" not in readme:
        report("native-tasks-view: README lacks the tasks-view command.")
        return 1
    if "native-tasks-view" not in {name for name, _ in SCENARIOS}:
        report("native-tasks-view: the scenario registry does not include it.")
        return 1

    report("native-tasks-view scenario passed.")
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

    if "verification-layering-docs" not in {name for name, _ in SCENARIOS}:
        report("verification-layering-docs: the scenario registry does not include it.")
        return 1

    report("verification-layering-docs scenario passed.")
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


def validate_native_goal_gate_order_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-goal-order-") as raw_tmp:
        root = Path(raw_tmp)
        repo = root / "codex"
        repo.mkdir()
        env = dict(os.environ)
        env["CODEX_HOME"] = str(root / "codex-home")
        if run_keel(repo, "--install", "--target", "codex", env=env).returncode != 0:
            report("native-goal-gate-order install failed.")
            return 1
        tasks_path = repo / "openspec/changes/sample-change/tasks.md"
        write_text(tasks_path, _goal_tasks_file([_goal_task_block()]))
        # A native evaluator claiming success must never stand in for the gates.
        write_text(repo / ".codex/transcripts/session.json", '{"complete": true}\n')

        goal_result = run_keel(
            repo, "project", "goal",
            "--target", "codex",
            "--change", "sample-change", "--task", "1.1", "--json",
            env=env,
        )
        goal = json.loads(goal_result.stdout).get("goal") or {}
        presentation = goal.get("evidencePresentation") or []
        if (
            len(presentation) != 3
            or "Done only when: task-complete passes" not in goal.get("condition", "")
            or "durably checked" not in goal.get("condition", "")
        ):
            report("native-goal-gate-order goal did not encode the durable completion order.")
            report(json.dumps(goal, indent=2))
            return 1

        # 1. task-start passes and yields the fingerprint authorization.
        start = run_keel(
            repo, "gate", "task-start",
            "--change", "sample-change", "--task", "1.1", "--json",
            env=env,
        )
        if start.returncode != 0:
            report("native-goal-gate-order task-start failed.")
            return 1

        # 2. Premature completion is rejected before implementation/evidence exist,
        #    even with a native "complete" transcript present.
        before_tasks = tasks_path.read_text(encoding="utf-8")
        premature = run_keel(
            repo, "gate", "task-complete",
            "--change", "sample-change", "--task", "1.1", "--json",
            env=env,
        )
        if premature.returncode == 0:
            report("native-goal-gate-order allowed premature completion.")
            return 1

        # 3. Compiling the goal never checks the box; the current agent owns it.
        run_keel(
            repo, "project", "goal",
            "--target", "codex",
            "--change", "sample-change", "--task", "1.1", "--json",
            env=env,
        )
        if tasks_path.read_text(encoding="utf-8") != before_tasks:
            report("native-goal-gate-order goal projection mutated the task owner.")
            return 1

        # 4. With evidence and a passing Review recorded, task-complete passes.
        write_text(tasks_path, _goal_tasks_file([_goal_task_block(filled=True)]))
        completed = run_keel(
            repo, "gate", "task-complete",
            "--change", "sample-change", "--task", "1.1", "--json",
            env=env,
        )
        if completed.returncode != 0:
            report("native-goal-gate-order rejected a completed task after evidence and Review.")
            report((completed.stderr or completed.stdout).strip())
            return 1

        # 5. A blocked state never satisfies completion.
        write_text(
            tasks_path,
            _goal_tasks_file(
                [_goal_task_block(filled=True, blocker="native runtime lost the goal condition")]
            ),
        )
        blocked = run_keel(
            repo, "gate", "task-complete",
            "--change", "sample-change", "--task", "1.1", "--json",
            env=env,
        )
        if blocked.returncode == 0:
            report("native-goal-gate-order let a blocked task complete.")
            return 1

        # 6. After the current agent durably checks the box, the goal stops.
        write_text(tasks_path, _goal_tasks_file([_goal_task_block(checked=True, filled=True)]))
        stopped = run_keel(
            repo, "project", "goal",
            "--target", "codex",
            "--change", "sample-change", "--task", "1.1", "--json",
            env=env,
        )
        stopped_payload = json.loads(stopped.stdout)
        if stopped.returncode == 0 or stopped_payload.get("status") != "blocked":
            report("native-goal-gate-order did not stop after completion.")
            return 1

    report("native-goal-gate-order scenario passed.")
    return 0


def validate_native_goal_continuity_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-goal-continuity-") as raw_tmp:
        root = Path(raw_tmp)
        repo = root / "codex"
        repo.mkdir()
        env = dict(os.environ)
        env["CODEX_HOME"] = str(root / "codex-home")
        if run_keel(repo, "--install", "--target", "codex", env=env).returncode != 0:
            report("native-goal-continuity install failed.")
            return 1
        tasks_path = repo / "openspec/changes/sample-change/tasks.md"
        write_text(
            tasks_path,
            _goal_tasks_file(
                [
                    _goal_task_block(task_id="1.1"),
                    _goal_task_block(task_id="1.2", title="Second bounded behavior"),
                ]
            ),
        )
        owner = "openspec/changes/sample-change/tasks.md#1.1"

        def _goal(*args: str) -> subprocess.CompletedProcess[str]:
            return run_keel(
                repo, "project", "goal",
                "--target", "codex",
                "--change", "sample-change", "--task", "1.1",
                *args,
                "--json",
                env=env,
            )

        # Continuity is reconstructed from OpenSpec/Git, not a Keel cursor/cache.
        before = snapshot_files(repo)
        first = _goal()
        second = _goal()
        if before != snapshot_files(repo):
            report("native-goal-continuity wrote a Keel cursor or cache.")
            return 1
        first_goal = json.loads(first.stdout).get("goal") or {}
        second_goal = json.loads(second.stdout).get("goal") or {}
        if not first_goal or first_goal != second_goal:
            report("native-goal-continuity did not reconstruct an identical goal.")
            return 1
        recorded = first_goal.get("fingerprint", {}).get("value")

        # A matching authorized resume is accepted.
        resume = _goal("--expected-fingerprint", recorded, "--expected-owner", owner)
        if resume.returncode != 0 or json.loads(resume.stdout).get("status") != "ready":
            report("native-goal-continuity rejected a matching authorized resume.")
            return 1

        def _blocks(result: subprocess.CompletedProcess[str], label: str) -> bool:
            if result.returncode == 0:
                report("native-goal-continuity accepted %s." % label)
                return False
            payload = json.loads(result.stdout)
            if payload.get("status") != "blocked" or payload.get("goal") is not None:
                report("native-goal-continuity %s was not a clean block." % label)
                return False
            return True

        # Missing authorization (a resume with no explicit task) never auto-advances
        # to the proposed next task.
        missing = run_keel(
            repo, "project", "goal",
            "--target", "codex", "--change", "sample-change", "--json",
            env=env,
        )
        if not _blocks(missing, "missing authorization"):
            return 1

        # Checkout divergence: the recorded owner no longer matches.
        if not _blocks(
            _goal("--expected-owner", "openspec/changes/other/tasks.md#9.9"),
            "checkout divergence",
        ):
            return 1

        # Fingerprint drift: a real source change makes the recompiled capsule
        # diverge from the recorded authorization.
        write_text(
            tasks_path,
            _goal_tasks_file(
                [
                    _goal_task_block(
                        task_id="1.1",
                        acceptance=("A different observable result is proven by M1.",),
                    ),
                    _goal_task_block(task_id="1.2", title="Second bounded behavior"),
                ]
            ),
        )
        recompiled = json.loads(_goal().stdout).get("goal") or {}
        if recompiled.get("fingerprint", {}).get("value") == recorded:
            report("native-goal-continuity did not track the durable source change.")
            return 1
        if not _blocks(
            _goal("--expected-fingerprint", recorded),
            "fingerprint drift",
        ):
            return 1

        # Completed authorization stops; the next task is never auto-selected.
        write_text(
            tasks_path,
            _goal_tasks_file(
                [
                    _goal_task_block(task_id="1.1", checked=True, filled=True),
                    _goal_task_block(task_id="1.2", title="Second bounded behavior"),
                ]
            ),
        )
        if not _blocks(_goal(), "completed authorization"):
            return 1
        next_task = run_keel(
            repo, "project", "goal",
            "--target", "codex", "--change", "sample-change", "--json",
            env=env,
        )
        if not _blocks(next_task, "auto-advance to the next task"):
            return 1

    report("native-goal-continuity scenario passed.")
    return 0


def validate_native_helper_brief_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-helper-brief-") as raw_tmp:
        root = Path(raw_tmp)
        repo = root / "repo"
        (repo / "src").mkdir(parents=True)
        write_text(repo / "src/goal.js", "// sample\n")

        def _helper(*args: str) -> subprocess.CompletedProcess[str]:
            return run_keel(repo, "project", "helper", *args, "--json")

        # A bounded read-only question compiles a non-writing, non-delegating brief.
        before = snapshot_files(repo)
        question = _helper(
            "--target", "codex",
            "--brief", "Which function in src/goal.js renders the condition?",
            "--read", "src/goal.js",
        )
        payload = json.loads(question.stdout)
        brief = payload.get("brief") or {}
        if (
            question.returncode != 0
            or payload.get("version") != "keel-helper-brief/v1"
            or payload.get("status") != "ready"
            or brief.get("mode") != "question"
            or brief.get("authority") != "read-only-evidence-only"
            or brief.get("writesProducts") is not False
            or brief.get("delegates") is not False
            or brief.get("completionAuthority") is not False
            or brief.get("reads") != ["src/goal.js"]
            or not brief.get("reportSchema")
        ):
            report("native-helper-brief did not compile a bounded question brief.")
            report(json.dumps(payload, indent=2))
            return 1

        # An exact repository-byte-stable verification command is also accepted.
        command = _helper(
            "--target", "claude",
            "--command", "node scripts/run_python.js scripts/validate_plugin.py --scenario cli",
        )
        if (
            command.returncode != 0
            or json.loads(command.stdout).get("brief", {}).get("mode")
            != "verification-command"
        ):
            report("native-helper-brief rejected a byte-stable verification command.")
            return 1

        if before != snapshot_files(repo):
            report("native-helper-brief mutated the repository while compiling briefs.")
            return 1

        def _reject(args: list[str], label: str) -> bool:
            snap = snapshot_files(repo)
            result = _helper(*args)
            if result.returncode == 0:
                report("native-helper-brief accepted %s." % label)
                return False
            payload = json.loads(result.stdout)
            if payload.get("status") != "blocked" or payload.get("brief") is not None:
                report("native-helper-brief %s was not a clean block." % label)
                return False
            if snap != snapshot_files(repo):
                report("native-helper-brief %s mutated state." % label)
                return False
            return True

        checks = [
            (["--target", "codex", "--brief", "Implement the renderer in src/goal.js"],
             "implementation delegation"),
            (["--target", "codex", "--brief", "What is X? What is Y unrelated thing?"],
             "multiple unrelated questions"),
            (["--target", "codex", "--brief", "Ask a subagent to summarize src/goal.js"],
             "nested delegation"),
            (["--target", "codex", "--brief", "Please mark the task complete and sync"],
             "completion-authority request"),
            (["--target", "codex", "--command", "node build.js > dist/out.txt"],
             "artifact-generating command"),
            (["--target", "codex", "--command", "git commit -am done"],
             "commit command"),
            (["--target", "codex", "--command", "node test.js", "--external", "src/tmp.json"],
             "in-repo declared output"),
            (["--target", "opencode", "--brief", "Which file defines the gate?"],
             "opencode target"),
            (["--target", "codex"], "empty brief"),
        ]
        for args, label in checks:
            if not _reject(args, label):
                return 1

    report("native-helper-brief scenario passed.")
    return 0


def validate_native_helper_read_only_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-helper-ro-") as raw_tmp:
        root = Path(raw_tmp)
        repo = root / "repo"
        (repo / "src").mkdir(parents=True)
        write_text(repo / "src/a.txt", "alpha\n")
        write_text(repo / "src/b.txt", "beta\n")
        baseline = root / "baseline.json"

        def _capture(target_baseline: Path) -> subprocess.CompletedProcess[str]:
            return run_keel(
                repo, "project", "helper",
                "--target", "codex", "--capture-baseline",
                "--baseline", str(target_baseline), "--json",
            )

        def _verify() -> subprocess.CompletedProcess[str]:
            return run_keel(
                repo, "project", "helper",
                "--target", "codex", "--verify",
                "--baseline", str(baseline), "--json",
            )

        # A baseline must live outside the worktree.
        inside = _capture(repo / "baseline.json")
        if inside.returncode == 0:
            report("native-helper-read-only wrote a baseline inside the repository.")
            return 1

        # Pre-existing dirty bytes are captured into the baseline and never
        # attributed to the helper.
        write_text(repo / "src/pre-existing.txt", "already changed by the current agent\n")
        if _capture(baseline).returncode != 0:
            report("native-helper-read-only could not capture an external baseline.")
            return 1
        clean = _verify()
        if clean.returncode != 0 or json.loads(clean.stdout).get("status") != "verified":
            report("native-helper-read-only rejected an unchanged repository.")
            report((clean.stderr or clean.stdout).strip())
            return 1
        # The pre-existing file is preserved, not cleaned up or attributed.
        if not (repo / "src/pre-existing.txt").exists():
            report("native-helper-read-only removed a pre-existing path.")
            return 1

        def _expect_reject(mutation, label: str, expected: dict[str, str]) -> bool:
            mutation()
            result = _verify()
            payload = json.loads(result.stdout)
            if result.returncode == 0 or payload.get("status") != "rejected":
                report("native-helper-read-only accepted %s." % label)
                return False
            changes = {c["path"]: c["kind"] for c in payload.get("changes", [])}
            for path_key, kind in expected.items():
                if changes.get(path_key) != kind:
                    report(
                        "native-helper-read-only %s misreported changes: %s"
                        % (label, json.dumps(changes))
                    )
                    return False
            if payload.get("cleanup") != "none":
                report("native-helper-read-only %s attempted cleanup." % label)
                return False
            return True

        # modified
        if not _expect_reject(
            lambda: write_text(repo / "src/a.txt", "alpha-changed\n"),
            "a modified path",
            {"src/a.txt": "modified"},
        ):
            return 1
        # restore for isolation, re-baseline
        write_text(repo / "src/a.txt", "alpha\n")
        if _capture(baseline).returncode != 0:
            return 1
        # added
        if not _expect_reject(
            lambda: write_text(repo / "src/c.txt", "added\n"),
            "an added path",
            {"src/c.txt": "added"},
        ):
            return 1
        (repo / "src/c.txt").unlink()
        if _capture(baseline).returncode != 0:
            return 1
        # deleted
        if not _expect_reject(
            lambda: (repo / "src/b.txt").unlink(),
            "a deleted path",
            {"src/b.txt": "removed"},
        ):
            return 1
        write_text(repo / "src/b.txt", "beta\n")
        if _capture(baseline).returncode != 0:
            return 1
        # renamed -> reported as removed + added
        if not _expect_reject(
            lambda: (repo / "src/b.txt").rename(repo / "src/b-renamed.txt"),
            "a renamed path",
            {"src/b.txt": "removed", "src/b-renamed.txt": "added"},
        ):
            return 1

        # A command whose byte stability cannot be established remains current-agent
        # work rather than a silent pass.
        missing = run_keel(
            repo, "project", "helper",
            "--target", "codex", "--verify",
            "--baseline", str(root / "does-not-exist.json"), "--json",
        )
        if missing.returncode == 0 or json.loads(missing.stdout).get("status") != "unverifiable":
            report("native-helper-read-only accepted an unestablished baseline.")
            return 1

    report("native-helper-read-only scenario passed.")
    return 0


def validate_native_goal_capabilities_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-helper-caps-") as raw_tmp:
        root = Path(raw_tmp)
        for target in ("codex", "claude"):
            repo = root / target
            repo.mkdir()
            env = dict(os.environ)
            if target == "codex":
                env["CODEX_HOME"] = str(root / "codex-home")
            if run_keel(repo, "--install", "--target", target, env=env).returncode != 0:
                report("native-goal-capabilities %s install failed." % target)
                return 1
            probed = run_keel(repo, "capabilities", "--target", target, "--json", env=env)
            payload = json.loads(probed.stdout)
            helper = payload.get("helper") or {}
            dimensions = (
                "discovery",
                "toolRestriction",
                "nestedDelegationPrevention",
                "byteStability",
                "execution",
            )
            if any(dim not in helper for dim in dimensions):
                report("native-goal-capabilities %s omitted a helper dimension." % target)
                report(json.dumps(helper, indent=2))
                return 1
            levels = {helper[dim].get("level") for dim in dimensions}
            # enforced, advisory, and manual are reported separately.
            if not {"enforced", "advisory", "manual"}.issubset(levels):
                report("native-goal-capabilities %s did not separate enforcement levels." % target)
                return 1
            if (
                helper["nestedDelegationPrevention"].get("level") != "enforced"
                or helper["byteStability"].get("level") != "enforced"
                or helper["execution"].get("level") != "manual"
            ):
                report("native-goal-capabilities %s mislabeled a helper dimension." % target)
                return 1
            # Helper absence never disables current-agent goal execution.
            if payload.get("capabilities", {}).get("execution.goal", {}).get("level") != "manual":
                report("native-goal-capabilities %s dropped goal execution." % target)
                return 1
            if not any(
                "Helper absence never disables" in warning
                for warning in payload.get("warnings", [])
            ):
                report("native-goal-capabilities %s did not assert helper independence." % target)
                return 1

    report("native-goal-capabilities scenario passed.")
    return 0


SINGLE_TASK_GOAL_SKILL = "keel-run-single-task-goal"
OFFICIAL_GOAL_SOURCES = (
    "https://learn.chatgpt.com/use-cases/follow-goals",
    "https://developers.openai.com/codex/subagents",
    "https://code.claude.com/docs/en/goal",
    "https://code.claude.com/docs/en/sub-agents",
)


def validate_single_task_goal_skill_scenario() -> int:
    canonical = ROOT / "src/skills" / SINGLE_TASK_GOAL_SKILL / "SKILL.md"
    projection = ROOT / "plugins/keel/skills" / SINGLE_TASK_GOAL_SKILL / "SKILL.md"
    if not canonical.is_file() or not projection.is_file():
        report("single-task-goal-skill missing canonical skill or native projection.")
        return 1
    canonical_bytes = canonical.read_bytes()
    if canonical_bytes != projection.read_bytes():
        report("single-task-goal-skill projection is not byte-equal to the canonical source.")
        return 1
    text = canonical_bytes.decode("utf-8")

    # Authoritative official sources are linked, and provenance/license is recorded.
    for source in OFFICIAL_GOAL_SOURCES:
        if source not in text:
            report("single-task-goal-skill did not link official source: %s" % source)
            return 1
    lowered = text.lower()
    if (
        "provenance" not in lowered
        or "license note" not in lowered
        or "not copied" not in lowered
        or "paraphrase" not in lowered
    ):
        report("single-task-goal-skill did not record provenance/license and paraphrase intent.")
        return 1
    # Paraphrase, not bundle: no verbatim external doc dumped inside a fenced block.
    if "```" in text:
        report("single-task-goal-skill bundled a fenced external block instead of paraphrasing.")
        return 1

    # Positive triggers for explicit one-task automatic execution and resume.
    if not (
        "## When to activate" in text
        and "resume" in lowered
        and ("one task" in lowered or "one" in lowered)
        and "explicit" in lowered
    ):
        report("single-task-goal-skill lacks explicit one-task/resume positive triggers.")
        return 1
    # Negative triggers.
    negatives = ("/opsx:apply", "proposal", "ambiguous", "opencode", "deleg", "helper")
    if "## When NOT to activate" not in text or any(
        neg not in lowered for neg in negatives
    ):
        report("single-task-goal-skill lacks the required negative triggers.")
        return 1
    # Manual fallback and the exact copy/paste command.
    if "## Manual fallback" not in text or "keel project goal" not in text:
        report("single-task-goal-skill lacks a manual fallback with the exact command.")
        return 1

    # Thin activation adapters exist for both native targets and no others.
    agents_dir = ROOT / "plugins/keel/agents"
    agent_files = sorted(p.name for p in agents_dir.glob("*.md")) if agents_dir.is_dir() else []
    expected_agents = [
        "keel-single-task-goal-claude.md",
        "keel-single-task-goal-codex.md",
    ]
    if agent_files != expected_agents:
        report("single-task-goal-skill adapters are not exactly the codex and claude pair.")
        return 1
    for name, target in (
        ("keel-single-task-goal-codex.md", "codex"),
        ("keel-single-task-goal-claude.md", "claude"),
    ):
        adapter = (agents_dir / name).read_text(encoding="utf-8")
        if ("target: %s" % target) not in adapter or "read-only" not in adapter.lower():
            report("single-task-goal-skill %s adapter is missing target or read-only helper policy." % target)
            return 1

    report("single-task-goal-skill scenario passed.")
    return 0


def validate_single_task_goal_real_tasks_scenario() -> int:
    cases = (
        ("bug-fix", "vertical-tdd", True),
        ("generator", "characterization", False),
        ("rendered", "rendered-behavior", False),
    )
    with tempfile.TemporaryDirectory(prefix="keel-real-tasks-") as raw_tmp:
        root = Path(raw_tmp)
        for name, strategy, redgreen in cases:
            repo = root / name
            repo.mkdir()
            env = dict(os.environ)
            env["CODEX_HOME"] = str(root / ("codex-home-" + name))
            if run_keel(repo, "--install", "--target", "codex", env=env).returncode != 0:
                report("single-task-goal-real-tasks %s install failed." % name)
                return 1
            tasks_path = repo / "openspec/changes/sample-change/tasks.md"
            write_text(tasks_path, _goal_tasks_file([_goal_task_block(strategy=strategy)]))

            start = run_keel(
                repo, "gate", "task-start",
                "--change", "sample-change", "--task", "1.1", "--json", env=env,
            )
            if start.returncode != 0:
                report("single-task-goal-real-tasks %s task-start failed." % name)
                return 1
            goal = run_keel(
                repo, "project", "goal",
                "--target", "codex", "--change", "sample-change", "--task", "1.1",
                "--json", env=env,
            )
            gpayload = json.loads(goal.stdout).get("goal") or {}
            if goal.returncode != 0 or gpayload.get("verificationStrategy") != strategy:
                report("single-task-goal-real-tasks %s goal did not carry its strategy." % name)
                return 1

            # Complete the one task through its approved strategy evidence.
            write_text(
                tasks_path,
                _goal_tasks_file(
                    [_goal_task_block(strategy=strategy, filled=True, redgreen=redgreen)]
                ),
            )
            done = run_keel(
                repo, "gate", "task-complete",
                "--change", "sample-change", "--task", "1.1", "--json", env=env,
            )
            if done.returncode != 0:
                report("single-task-goal-real-tasks %s task-complete failed." % name)
                report((done.stderr or done.stdout).strip())
                return 1

            # Current agent checks the one box; the run then stops at that boundary.
            write_text(
                tasks_path,
                _goal_tasks_file(
                    [_goal_task_block(strategy=strategy, checked=True, filled=True, redgreen=redgreen)]
                ),
            )
            stopped = run_keel(
                repo, "project", "goal",
                "--target", "codex", "--change", "sample-change", "--task", "1.1",
                "--json", env=env,
            )
            if stopped.returncode == 0 or json.loads(stopped.stdout).get("status") != "blocked":
                report("single-task-goal-real-tasks %s did not stop after one task." % name)
                return 1
            # No next fixture task exists or was auto-created.
            if "1.2" in tasks_path.read_text(encoding="utf-8"):
                report("single-task-goal-real-tasks %s started a next task." % name)
                return 1

    report("single-task-goal-real-tasks scenario passed.")
    return 0


def _goal_target_surface(target: str) -> int:
    with tempfile.TemporaryDirectory(prefix="keel-goal-%s-" % target) as raw_tmp:
        root = Path(raw_tmp)
        repo = root / target
        repo.mkdir()
        env = dict(os.environ)
        if target == "codex":
            env["CODEX_HOME"] = str(root / "codex-home")
        if run_keel(repo, "--install", "--target", target, env=env).returncode != 0:
            report("native-goal-%s install failed." % target)
            return 1
        write_text(
            repo / "openspec/changes/sample-change/tasks.md",
            _goal_tasks_file([_goal_task_block(strategy="vertical-tdd")]),
        )

        # The plugin ships the portable skill and this target's activation adapter.
        adapter = ROOT / "plugins/keel/agents" / ("keel-single-task-goal-%s.md" % target)
        if not (ROOT / "plugins/keel/skills" / SINGLE_TASK_GOAL_SKILL).is_dir() or not adapter.is_file():
            report("native-goal-%s missing portable skill or activation adapter." % target)
            return 1

        # Explicit activation, resume, drift stop, and single-task termination.
        activated = run_keel(
            repo, "project", "goal", "--target", target,
            "--change", "sample-change", "--task", "1.1", "--json", env=env,
        )
        apayload = json.loads(activated.stdout)
        goal = apayload.get("goal") or {}
        if activated.returncode != 0 or apayload.get("status") != "ready":
            report("native-goal-%s did not activate one task." % target)
            return 1
        if target == "claude" and goal.get("conditionLength", 0) > 4000:
            report("native-goal-claude condition exceeded the 4,000-character budget.")
            return 1
        recorded = goal.get("fingerprint", {}).get("value")
        owner = "openspec/changes/sample-change/tasks.md#1.1"
        resume = run_keel(
            repo, "project", "goal", "--target", target,
            "--change", "sample-change", "--task", "1.1",
            "--expected-fingerprint", recorded, "--expected-owner", owner, "--json", env=env,
        )
        if resume.returncode != 0 or json.loads(resume.stdout).get("status") != "ready":
            report("native-goal-%s could not resume the authorized task." % target)
            return 1
        drift = run_keel(
            repo, "project", "goal", "--target", target,
            "--change", "sample-change", "--task", "1.1",
            "--expected-fingerprint", "deadbeef", "--json", env=env,
        )
        if drift.returncode == 0 or json.loads(drift.stdout).get("status") != "blocked":
            report("native-goal-%s did not stop on drift." % target)
            return 1

        # Capabilities surface the goal at manual with a copy/paste command fallback.
        caps = run_keel(repo, "capabilities", "--target", target, "--json", env=env)
        cpayload = json.loads(caps.stdout)
        goal_cap = cpayload.get("capabilities", {}).get("execution.goal", {})
        if goal_cap.get("level") != "manual" or not goal_cap.get("command"):
            report("native-goal-%s did not report an advisory goal command fallback." % target)
            return 1

        # The skill carries the target-specific fallback guidance.
        skill_text = (ROOT / "plugins/keel/skills" / SINGLE_TASK_GOAL_SKILL / "SKILL.md").read_text(
            encoding="utf-8"
        )
        if target == "claude" and "disabled hooks" not in skill_text.lower():
            report("native-goal-claude skill lacks the disabled-hooks fallback.")
            return 1
        if target == "codex" and "advisory" not in skill_text.lower():
            report("native-goal-codex skill lacks the advisory activation fallback.")
            return 1
    return 0


def validate_native_goal_codex_scenario() -> int:
    status = _goal_target_surface("codex")
    if status == 0:
        report("native-goal-codex scenario passed.")
    return status


def validate_native_goal_claude_scenario() -> int:
    status = _goal_target_surface("claude")
    if status == 0:
        report("native-goal-claude scenario passed.")
    return status


def validate_native_helper_targets_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-helper-targets-") as raw_tmp:
        root = Path(raw_tmp)
        for target in ("codex", "claude"):
            repo = root / target
            repo.mkdir()
            env = dict(os.environ)
            if target == "codex":
                env["CODEX_HOME"] = str(root / "codex-home")
            if run_keel(repo, "--install", "--target", target, env=env).returncode != 0:
                report("native-helper-targets %s install failed." % target)
                return 1
            caps = run_keel(repo, "capabilities", "--target", target, "--json", env=env)
            helper = json.loads(caps.stdout).get("helper") or {}
            # Write and delegation authority are removed where supported (enforced),
            # and dimensions downgrade independently (mixed levels).
            if (
                helper.get("nestedDelegationPrevention", {}).get("level") != "enforced"
                or helper.get("byteStability", {}).get("level") != "enforced"
                or helper.get("toolRestriction", {}).get("level") != "advisory"
                or helper.get("execution", {}).get("level") != "manual"
            ):
                report("native-helper-targets %s did not downgrade helper dimensions independently." % target)
                return 1
            # Only byte-stable read-only briefs are accepted.
            ok = run_keel(
                repo, "project", "helper", "--target", target,
                "--brief", "Which file defines the gate?", "--json", env=env,
            )
            if ok.returncode != 0 or json.loads(ok.stdout).get("status") != "ready":
                report("native-helper-targets %s rejected a bounded read-only brief." % target)
                return 1
            bad = run_keel(
                repo, "project", "helper", "--target", target,
                "--brief", "Delegate the fix to a subagent", "--json", env=env,
            )
            if bad.returncode == 0 or json.loads(bad.stdout).get("status") != "blocked":
                report("native-helper-targets %s accepted a delegating helper." % target)
                return 1

        # No agent team or OpenCode v4 artifact is introduced: the adapter set is
        # exactly the codex and claude pair.
        agents_dir = ROOT / "plugins/keel/agents"
        names = sorted(p.name for p in agents_dir.glob("*.md"))
        if names != ["keel-single-task-goal-claude.md", "keel-single-task-goal-codex.md"]:
            report("native-helper-targets adapter set is not exactly the codex and claude pair.")
            return 1
        # No global Stop hook is registered in either native manifest.
        for runtime in (".codex-plugin", ".claude-plugin"):
            manifest = json.loads(
                (ROOT / "plugins/keel" / runtime / "plugin.json").read_text(encoding="utf-8")
            )
            hooks = json.dumps(manifest.get("hooks", {})).lower()
            if "stop" in hooks:
                report("native-helper-targets registered a global Stop hook in %s." % runtime)
                return 1

    report("native-helper-targets scenario passed.")
    return 0


def _single_task_matrix_target(target: str, root: Path) -> int:
    repo = root / target
    repo.mkdir()
    env = dict(os.environ)
    if target == "codex":
        env["CODEX_HOME"] = str(root / ("codex-home-" + target))
    if run_keel(repo, "--install", "--target", target, env=env).returncode != 0:
        report("native-single-task-matrix %s install failed." % target)
        return 1
    tasks_path = repo / "openspec/changes/sample-change/tasks.md"

    def two_tasks(checked_first: bool = False, blocker: str = "none") -> str:
        return _goal_tasks_file(
            [
                _goal_task_block(
                    task_id="1.1", strategy="vertical-tdd",
                    checked=checked_first, filled=checked_first, redgreen=checked_first,
                    blocker=blocker,
                ),
                _goal_task_block(task_id="1.2", title="Second bounded behavior"),
            ]
        )

    write_text(tasks_path, two_tasks())
    # A native "already complete" transcript must never act as authority.
    write_text(repo / (".%s/transcripts/session.json" % target), '{"complete": true}\n')

    def goal(*args: str) -> subprocess.CompletedProcess[str]:
        return run_keel(
            repo, "project", "goal", "--target", target,
            "--change", "sample-change", "--task", "1.1", *args, "--json", env=env,
        )

    # Explicit one-task activation with the vertical strategy carried through.
    activated = json.loads(goal().stdout)
    if activated.get("status") != "ready" or activated["goal"]["verificationStrategy"] != "vertical-tdd":
        report("native-single-task-matrix %s did not activate one vertical task." % target)
        return 1
    recorded = activated["goal"]["fingerprint"]["value"]
    owner = "openspec/changes/sample-change/tasks.md#1.1"

    # Compaction reconstruction is identical and writes no Keel cursor/cache.
    before = snapshot_files(repo)
    if json.loads(goal().stdout)["goal"] != activated["goal"]:
        report("native-single-task-matrix %s reconstruction diverged." % target)
        return 1
    if before != snapshot_files(repo):
        report("native-single-task-matrix %s wrote Keel goal/cursor state." % target)
        return 1

    # Exact resume; drift and ambiguous checkout hard-stop; premature success ignored.
    if json.loads(goal("--expected-fingerprint", recorded, "--expected-owner", owner).stdout)["status"] != "ready":
        report("native-single-task-matrix %s rejected an exact resume." % target)
        return 1
    if json.loads(goal("--expected-fingerprint", "deadbeef").stdout)["status"] != "blocked":
        report("native-single-task-matrix %s did not stop on drift." % target)
        return 1
    if json.loads(goal("--expected-owner", "openspec/changes/other/tasks.md#9.9").stdout)["status"] != "blocked":
        report("native-single-task-matrix %s did not stop on ambiguous checkout." % target)
        return 1

    # Current-agent order: task-complete fails before evidence, passes after, and a
    # blocked task never completes; failure never rolls back or escalates.
    start = run_keel(repo, "gate", "task-start", "--change", "sample-change", "--task", "1.1", "--json", env=env)
    if start.returncode != 0:
        report("native-single-task-matrix %s task-start failed." % target)
        return 1
    pre = snapshot_files(repo)
    if run_keel(repo, "gate", "task-complete", "--change", "sample-change", "--task", "1.1", "--json", env=env).returncode == 0:
        report("native-single-task-matrix %s allowed premature completion." % target)
        return 1
    if pre != snapshot_files(repo):
        report("native-single-task-matrix %s failing gate mutated the tree." % target)
        return 1
    # A blocked task never completes, even with evidence and a passing Review.
    write_text(
        tasks_path,
        _goal_tasks_file(
            [
                _goal_task_block(
                    task_id="1.1", strategy="vertical-tdd", filled=True, redgreen=True,
                    blocker="native runtime lost the goal condition",
                ),
                _goal_task_block(task_id="1.2", title="Second bounded behavior"),
            ]
        ),
    )
    if run_keel(repo, "gate", "task-complete", "--change", "sample-change", "--task", "1.1", "--json", env=env).returncode == 0:
        report("native-single-task-matrix %s let a blocked task complete." % target)
        return 1

    # Helper success and helper write/delegation rejection.
    ok = run_keel(repo, "project", "helper", "--target", target, "--brief", "Which file defines the gate?", "--json", env=env)
    if json.loads(ok.stdout).get("status") != "ready":
        report("native-single-task-matrix %s rejected a bounded helper." % target)
        return 1
    bad = run_keel(repo, "project", "helper", "--target", target, "--brief", "Delegate the fix to a subagent", "--json", env=env)
    if json.loads(bad.stdout).get("status") != "blocked":
        report("native-single-task-matrix %s accepted a delegating helper." % target)
        return 1

    # Successful completion: evidence + Review, task-complete passes, current agent
    # checks the box, then the goal stops and never selects the next task.
    write_text(
        tasks_path,
        _goal_tasks_file(
            [
                _goal_task_block(task_id="1.1", strategy="vertical-tdd", filled=True, redgreen=True),
                _goal_task_block(task_id="1.2", title="Second bounded behavior"),
            ]
        ),
    )
    done = run_keel(repo, "gate", "task-complete", "--change", "sample-change", "--task", "1.1", "--json", env=env)
    if done.returncode != 0:
        report("native-single-task-matrix %s could not complete with evidence." % target)
        report((done.stderr or done.stdout).strip())
        return 1
    write_text(tasks_path, two_tasks(checked_first=True))
    if json.loads(goal().stdout)["status"] != "blocked":
        report("native-single-task-matrix %s did not stop after completion." % target)
        return 1
    no_task = run_keel(repo, "project", "goal", "--target", target, "--change", "sample-change", "--json", env=env)
    if json.loads(no_task.stdout)["status"] != "blocked":
        report("native-single-task-matrix %s auto-advanced to the next task." % target)
        return 1

    # No Keel cursor, goal id, scheduler, queue, or global Stop hook state exists.
    forbidden = (".keel", "keel-cursor.json", "goal-id.json", "scheduler.json", "queue.json")
    for name in forbidden:
        if list(repo.rglob(name)):
            report("native-single-task-matrix %s created forbidden Keel state: %s" % (target, name))
            return 1
    return 0


def validate_native_single_task_matrix_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-matrix-") as raw_tmp:
        root = Path(raw_tmp)
        for target in ("codex", "claude"):
            status = _single_task_matrix_target(target, root)
            if status != 0:
                return status
    report("native-single-task-matrix scenario passed.")
    return 0


def validate_thin_native_install_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-thin-install-") as raw_tmp:
        tmp = Path(raw_tmp)

        forbidden_copies = (
            ".claude/skills/keel-review-checklist",
            ".claude/skills/keel-align-expectations",
            ".claude/hooks/keel-gate",
            ".agents/skills/keel-review-checklist",
            "keel/adapters",
        )

        # --- Case A: clean install delivers only the thin v4 surface ---
        repo = tmp / "clean"
        repo.mkdir()
        install = run_keel(repo, "--install")
        if install.returncode != 0:
            report("thin-native-install clean install failed.")
            report((install.stderr or install.stdout).strip())
            return 1

        agents_path = repo / "AGENTS.md"
        if not has_managed_block(agents_path):
            report("thin-native-install missed the AGENTS.md bootstrap block.")
            return 1
        agents_text = agents_path.read_text(encoding="utf-8")
        if agents_text.count(MANAGED_END) != 1:
            report("thin-native-install wrote more than one AGENTS.md managed block.")
            return 1
        block = extract_managed_block(agents_text)
        block_bytes = len(block.encode("utf-8"))
        if block_bytes >= 1024:
            report(
                "thin-native-install bootstrap block is not sub-1KB: "
                f"{block_bytes} bytes"
            )
            return 1

        # The bootstrap is the whole resident protocol a consumer gets, and the
        # qualifier "for product files" left readers to infer what it excluded.
        # The inference actually made was that tasks.md belongs in Touch.
        if not re.search(r"Touch\b[^\n]*\bbound", block, re.IGNORECASE):
            report("thin-native-install bootstrap does not state what Touch bounds.")
            return 1
        if not re.search(r"change'?s own dir|own change dir", block, re.IGNORECASE):
            report(
                "thin-native-install bootstrap does not name the record-write "
                "exemption, so a consumer still infers that tasks.md belongs in "
                "Touch."
            )
            return 1

        claude_text = (repo / "CLAUDE.md").read_text(encoding="utf-8")
        if claude_text.count("@AGENTS.md") != 1:
            report(
                "thin-native-install did not install exactly one Claude @AGENTS.md "
                "import."
            )
            return 1

        for schema_file in packaged_openspec_schema_install_paths():
            if not (repo / schema_file).is_file():
                report(
                    f"thin-native-install missed OpenSpec schema file: {schema_file}"
                )
                return 1
        if not (repo / OPENSPEC_CONFIG_PATH).is_file():
            report("thin-native-install missed the OpenSpec config.")
            return 1

        leaked = [rel for rel in forbidden_copies if (repo / rel).exists()]
        if leaked:
            report(
                "thin-native-install copied Keel plugin components the CLI must "
                "leave to the native plugin."
            )
            report(", ".join(leaked))
            return 1

        # --- Case A': re-install is idempotent, no duplicate bootstrap/import ---
        before_reinstall = agents_path.read_text(encoding="utf-8")
        reinstall = run_keel(repo, "--install")
        if reinstall.returncode != 0:
            report("thin-native-install re-install failed.")
            report((reinstall.stderr or reinstall.stdout).strip())
            return 1
        if agents_path.read_text(encoding="utf-8") != before_reinstall:
            report("thin-native-install re-install drifted the AGENTS.md bootstrap.")
            return 1
        if (repo / "CLAUDE.md").read_text(encoding="utf-8").count("@AGENTS.md") != 1:
            report("thin-native-install re-install duplicated the @AGENTS.md import.")
            return 1

        # --- Case B: plain user content is byte-preserved and only extended ---
        user_repo = tmp / "user-content"
        user_repo.mkdir()
        user_agents = "# My Project\n\nCustom operator notes.\n"
        user_claude = "# House Guidelines\n\nReview twice.\n"
        write_text(user_repo / "AGENTS.md", user_agents)
        write_text(user_repo / "CLAUDE.md", user_claude)
        user_install = run_keel(user_repo, "--install")
        if user_install.returncode != 0:
            report("thin-native-install user-content install failed.")
            report((user_install.stderr or user_install.stdout).strip())
            return 1
        merged_agents = (user_repo / "AGENTS.md").read_text(encoding="utf-8")
        merged_claude = (user_repo / "CLAUDE.md").read_text(encoding="utf-8")
        if user_agents not in merged_agents or not has_managed_block(
            user_repo / "AGENTS.md"
        ):
            report(
                "thin-native-install did not preserve user AGENTS.md text while "
                "appending the bootstrap."
            )
            return 1
        if user_claude not in merged_claude or "@AGENTS.md" not in merged_claude:
            report(
                "thin-native-install did not preserve user CLAUDE.md text while "
                "appending the import."
            )
            return 1

        # --- Case C: a known v3 managed block migrates idempotently ---
        legacy_repo = tmp / "legacy-block"
        legacy_repo.mkdir()
        legacy_block = (
            "# Team AGENTS\n\n"
            "<!-- keel:start version=3.0.0 -->\n"
            "## Keel Legacy Protocol\n\n"
            "- Old resident protocol body that v4 replaces.\n"
            "<!-- keel:end -->\n"
        )
        write_text(legacy_repo / "AGENTS.md", legacy_block)
        legacy_install = run_keel(legacy_repo, "--install")
        if legacy_install.returncode != 0:
            report("thin-native-install legacy-block install failed.")
            report((legacy_install.stderr or legacy_install.stdout).strip())
            return 1
        migrated = (legacy_repo / "AGENTS.md").read_text(encoding="utf-8")
        if "Old resident protocol body" in migrated:
            report("thin-native-install did not migrate the legacy v3 managed block.")
            return 1
        if "# Team AGENTS" not in migrated or migrated.count(MANAGED_END) != 1:
            report(
                "thin-native-install migration dropped user text or left multiple "
                "managed blocks."
            )
            return 1
        legacy_reinstall = run_keel(legacy_repo, "--install")
        if legacy_reinstall.returncode != 0 or (
            legacy_repo / "AGENTS.md"
        ).read_text(encoding="utf-8") != migrated:
            report("thin-native-install legacy migration is not idempotent.")
            return 1

        # --- Case D: uncertain keel-looking content is preserved with a warning ---
        uncertain_repo = tmp / "uncertain"
        uncertain_repo.mkdir()
        uncertain_agents = (
            "# Local notes\n\n"
            "Always run keel gate task-start before implementing anything.\n"
        )
        write_text(uncertain_repo / "AGENTS.md", uncertain_agents)
        uncertain_install = run_keel(uncertain_repo, "--install")
        uncertain_text = (uncertain_install.stdout or "") + (
            uncertain_install.stderr or ""
        )
        if uncertain_install.returncode != 0:
            report("thin-native-install uncertain-content install failed.")
            report(uncertain_text.strip())
            return 1
        if (uncertain_repo / "AGENTS.md").read_text(
            encoding="utf-8"
        ) != uncertain_agents:
            report(
                "thin-native-install overwrote uncertain keel-looking AGENTS.md "
                "content instead of preserving it."
            )
            return 1
        if "preserve AGENTS.md" not in uncertain_text:
            report(
                "thin-native-install preserved uncertain content without a warning "
                "naming AGENTS.md."
            )
            report(uncertain_text.strip())
            return 1

        # --- Case E: doctor reports the native plugin runtime with remediation ---
        # These repos consume Keel, so the runtime line and its install
        # remediation must appear, while the plugin *source* check must not:
        # plugins/keel/ exists only in Keel's own repository and `keel --init`
        # never creates it, so reporting it here is a permanent unactionable
        # `missing`. See the dev-only-plugin-source-scoping scenario.
        doctor = run_keel(repo, "--doctor")
        doctor_text = (doctor.stdout or "") + (doctor.stderr or "")
        if (
            "native plugin runtime" not in doctor_text
            or "keel@<marketplace>" not in doctor_text
        ):
            report(
                "thin-native-install doctor does not report the native plugin "
                "surface with install remediation."
            )
            report(doctor_text.strip())
            return 1
        if "native plugin source" in doctor_text:
            report(
                "thin-native-install doctor reported the development-only "
                "plugin source check in a consuming project."
            )
            report(doctor_text.strip())
            return 1
        missing_repo = tmp / "no-plugin"
        missing_repo.mkdir()
        missing_doctor = run_keel(missing_repo, "--doctor")
        missing_text = (missing_doctor.stdout or "") + (missing_doctor.stderr or "")
        if "plugin source" in missing_text:
            report(
                "thin-native-install doctor diagnosed a plugin source outside "
                "Keel's own repository."
            )
            report(missing_text.strip())
            return 1

    report("thin-native-install scenario passed.")
    return 0


def validate_native_plugin_install_matrix_scenario() -> int:
    codex = shutil.which("codex")
    claude = claude_cli()
    if codex is None or claude is None:
        return skip_scenario(
            "native-plugin-install-matrix",
            "requires the codex and claude CLIs, which are not installed; it "
            "probes native install behavior no CI runner provides",
        )

    expected_version = json.loads(
        (ROOT / "package.json").read_text(encoding="utf-8")
    )["version"]

    # The plugin must expose exactly the SessionStart hook it ships from source.
    hooks_config = json.loads(
        (ROOT / PLUGIN_ROOT / "hooks/hooks.json").read_text(encoding="utf-8")
    )
    if "SessionStart" not in hooks_config.get("hooks", {}):
        report("native-plugin-install-matrix plugin does not ship a SessionStart hook.")
        return 1

    with tempfile.TemporaryDirectory(prefix="keel-install-matrix-") as raw_tmp:
        tmp = Path(raw_tmp)

        # --- Codex: clean install, discovery, remove, reinstall ---
        codex_home = tmp / "codex-home"
        codex_home.mkdir()
        codex_env = os.environ.copy()
        codex_env["CODEX_HOME"] = str(codex_home)

        def run_codex(*args: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [codex, *args],
                cwd=ROOT,
                env=codex_env,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )

        codex_market = json.loads(
            (ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8")
        )["name"]
        if run_codex("plugin", "marketplace", "add", str(ROOT)).returncode != 0:
            report("native-plugin-install-matrix codex marketplace add failed.")
            return 1
        if run_codex("plugin", "add", f"keel@{codex_market}").returncode != 0:
            report("native-plugin-install-matrix codex plugin add failed.")
            return 1
        listed = run_codex("plugin", "list")
        if (
            listed.returncode != 0
            or "keel" not in listed.stdout
            or "installed" not in listed.stdout
            or expected_version not in listed.stdout
        ):
            report(
                "native-plugin-install-matrix codex list did not show keel installed "
                f"at version {expected_version}."
            )
            report((listed.stderr or listed.stdout).strip())
            return 1
        if run_codex("plugin", "remove", f"keel@{codex_market}").returncode != 0:
            report("native-plugin-install-matrix codex plugin remove failed.")
            return 1
        if run_codex("plugin", "add", f"keel@{codex_market}").returncode != 0:
            report("native-plugin-install-matrix codex reinstall failed.")
            return 1
        run_codex("plugin", "remove", f"keel@{codex_market}")

        # --- Claude: validate, install, uninstall, reinstall ---
        claude_config = tmp / "claude-config"
        claude_config.mkdir()
        claude_env = os.environ.copy()
        claude_env["CLAUDE_CONFIG_DIR"] = str(claude_config)

        def run_claude(*args: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [claude, *args],
                cwd=ROOT,
                env=claude_env,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )

        if run_claude(
            "plugin", "validate", "--strict", str(ROOT / PLUGIN_ROOT)
        ).returncode != 0:
            report("native-plugin-install-matrix claude validate --strict failed.")
            return 1
        claude_market = json.loads(
            (ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8")
        )["name"]
        if run_claude("plugin", "marketplace", "add", str(ROOT)).returncode != 0:
            report("native-plugin-install-matrix claude marketplace add failed.")
            return 1
        if run_claude("plugin", "install", f"keel@{claude_market}").returncode != 0:
            report("native-plugin-install-matrix claude install failed.")
            return 1
        if run_claude("plugin", "uninstall", "keel").returncode != 0:
            report("native-plugin-install-matrix claude uninstall failed.")
            return 1
        if run_claude("plugin", "install", f"keel@{claude_market}").returncode != 0:
            report("native-plugin-install-matrix claude reinstall failed.")
            return 1
        run_claude("plugin", "uninstall", "keel")

        # --- Host CLI: OpenSpec schema/overlay flow and missing-plugin doctor ---
        host = tmp / "host"
        host.mkdir()
        host_install = run_keel(host, "--install")
        if host_install.returncode != 0:
            report("native-plugin-install-matrix host install failed.")
            report((host_install.stderr or host_install.stdout).strip())
            return 1
        for schema_file in packaged_openspec_schema_install_paths():
            if not (host / schema_file).is_file():
                report(
                    "native-plugin-install-matrix host install missed OpenSpec schema "
                    f"file: {schema_file}"
                )
                return 1
        if not (host / OPENSPEC_CONFIG_PATH).is_file():
            report("native-plugin-install-matrix host install missed OpenSpec config.")
            return 1
        doctor = run_keel(host, "--doctor")
        doctor_text = (doctor.stdout or "") + (doctor.stderr or "")
        if (
            "native plugin runtime" not in doctor_text
            or "keel@<marketplace>" not in doctor_text
        ):
            report(
                "native-plugin-install-matrix doctor did not report native plugin "
                "install remediation for a missing runtime."
            )
            report(doctor_text.strip())
            return 1

        personal_market = Path.home() / ".agents/plugins/marketplace.json"
        if personal_market.exists():
            guard = personal_market.read_text(encoding="utf-8")
            if "keel-install-matrix" in guard:
                report(
                    "native-plugin-install-matrix leaked isolation paths into the "
                    "personal marketplace."
                )
                return 1

    report("native-plugin-install-matrix scenario passed.")
    return 0


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
        "    - M1: node test.js\n"
        "  - Evidence:\n"
        "    - M1: pending\n"
    )


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
        "    - M1: git rev-parse HEAD resolves and git log reports one commit\n"
        "  - Evidence:\n"
        "    - Contract: pending\n"
        "    - M1: pending\n"
    )


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

    if label not in {name for name, _ in SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
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

    if label not in {name for name, _ in SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
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
    if label not in {name for name, _ in SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


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

    if label not in {name for name, _ in SCENARIOS}:
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

    if label not in {name for name, _ in SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
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


def compaction_task_fixture() -> str:
    return (
        "# Tasks\n\n## Invalidates\n\n- None.\n\n"
        "- [ ] 1.1 Exercise compaction continuity\n"
        "  - Covers:\n"
        "    - E1: Continuity survives compaction.\n"
        "  - Touch:\n"
        "    - src/feature.js\n"
        "  - Verify:\n"
        "    - Strategy: evidence-first\n"
        "    - M1: node test.js\n"
        "  - Evidence:\n"
        "    - Contract: sha256:"
        + ("ab" * 32)
        + " recorded by keel gate task-start\n"
        "    - M1: pending\n"
    )


def validate_plugin_compaction_continuity_scenario() -> int:
    real_cli = f'node "{ROOT / "bin/keel.js"}"'
    with tempfile.TemporaryDirectory(
        prefix="keel-compaction-", ignore_cleanup_errors=True
    ) as raw_tmp:
        tmp = Path(raw_tmp)
        repo = tmp / "repo"
        repo.mkdir()
        write_text(
            repo / "openspec/changes/demo/tasks.md", compaction_task_fixture()
        )

        before = snapshot_files(repo)
        compact = run_session_start_hook(
            repo,
            {"hook_event_name": "SessionStart", "source": "compact"},
            keel_cli=real_cli,
        )
        if snapshot_files(repo) != before:
            report("plugin-compaction-continuity: compact projection wrote state.")
            return 1
        if compact.returncode != 0:
            report("plugin-compaction-continuity: compact projection did not exit 0.")
            report((compact.stderr or compact.stdout).strip())
            return 1
        context = session_start_context(compact)
        if not context:
            report("plugin-compaction-continuity: compact projection is empty.")
            return 1
        for needle in (
            "post-compaction",
            "demo#1.1",
            "sha256:" + "ab" * 32,
            "recorded, not verified",
            "disposable",
        ):
            if needle not in context:
                report(
                    "plugin-compaction-continuity: compact projection lacks "
                    f"{needle!r}: {context!r}"
                )
                return 1
        if len(context.splitlines()) > 8:
            report("plugin-compaction-continuity: compact projection is not bounded.")
            return 1

        resume = run_session_start_hook(
            repo,
            {"hook_event_name": "SessionStart", "source": "resume"},
            keel_cli=real_cli,
        )
        resume_context = session_start_context(resume)
        if (
            resume.returncode != 0
            or not resume_context
            or "reinjection" not in resume_context
            or "demo#1.1" not in resume_context
        ):
            report("plugin-compaction-continuity: resume projection is wrong.")
            report(repr(resume_context))
            return 1

        for source in ("startup", "clear", "mystery", None):
            event = {"hook_event_name": "SessionStart"}
            if source is not None:
                event["source"] = source
            generic = run_session_start_hook(repo, event, keel_cli=real_cli)
            generic_context = session_start_context(generic)
            if (
                generic.returncode != 0
                or not generic_context
                or "run `keel gate task-start` before implementation" not in generic_context
                or "post-compaction" in generic_context
            ):
                report(
                    "plugin-compaction-continuity: generic fallback failed for "
                    f"source {source!r}: {generic_context!r}"
                )
                return 1

        ambiguous_repo = tmp / "ambiguous"
        ambiguous_repo.mkdir()
        write_text(
            ambiguous_repo / "openspec/changes/one/tasks.md",
            compaction_task_fixture(),
        )
        write_text(
            ambiguous_repo / "openspec/changes/two/tasks.md",
            compaction_task_fixture(),
        )
        ambiguous = run_session_start_hook(
            ambiguous_repo,
            {"hook_event_name": "SessionStart", "source": "compact"},
            keel_cli=real_cli,
        )
        ambiguous_context = session_start_context(ambiguous)
        if (
            ambiguous.returncode != 0
            or not ambiguous_context
            or "ambiguous" not in ambiguous_context
        ):
            report(
                "plugin-compaction-continuity: ambiguous compact fallback failed: "
                f"{ambiguous_context!r}"
            )
            return 1

    report("plugin-compaction-continuity scenario passed.")
    return 0


def validate_plan_funnel_guidance_scenario() -> int:
    skill_copies = (
        ROOT / "src/skills/keel-review-checklist/SKILL.md",
        ROOT / PLUGIN_ROOT / "skills/keel-review-checklist/SKILL.md",
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
            "plan-funnel-guidance: shipped keel-review-checklist copy diverges "
            "from the canonical source."
        )
        return 1

    readme = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
    if "plan mode" not in readme or "proposal/design/specs/tasks" not in readme:
        report("plan-funnel-guidance: README lacks the plan-mode funnel rule.")
        return 1

    if "plan-funnel-guidance" not in {name for name, _ in SCENARIOS}:
        report("plan-funnel-guidance: the scenario registry does not include it.")
        return 1

    report("plan-funnel-guidance scenario passed.")
    return 0


def validate_domain_execution_references_scenario() -> int:
    consuming_skills = (
        "keel-tdd-or-test-first",
        "keel-debug-failure",
        "keel-review-checklist",
    )
    templates = ("web.md", "hardware.md", "hardware-dsl.md")
    roots = (ROOT / "src/skills", ROOT / PLUGIN_ROOT / "skills")

    for root in roots:
        for skill in consuming_skills:
            text = (root / skill / "SKILL.md").read_text(encoding="utf-8")
            for needle in (
                "keel/lenses/",
                "Execution and review checks",
                "load only that one",
                "no lens matches",
            ):
                if needle not in text:
                    report(
                        f"domain-execution-references: {root.name}/{skill} lacks "
                        f"the on-demand lens consult step ({needle!r})."
                    )
                    return 1

    lenses_root = ROOT / "assets/lenses"
    for template in templates:
        ref_path = lenses_root / template
        if not ref_path.is_file():
            report(f"domain-execution-references: lens template is missing: {template}")
            return 1
        text = ref_path.read_text(encoding="utf-8")
        if "## Execution and review checks" not in text:
            report(
                f"domain-execution-references: {template} lacks the "
                "execution and review section."
            )
            return 1
        if "Applies when" not in text:
            report(
                f"domain-execution-references: {template} lacks the "
                "self-describing 'Applies when' header."
            )
            return 1
        size = ref_path.stat().st_size
        if size > 3072:
            report(
                f"domain-execution-references: {template} exceeds the 3072-"
                f"byte budget ({size} bytes); move depth to dedicated skills."
            )
            return 1

    for skill in consuming_skills:
        src_text = (roots[0] / skill / "SKILL.md").read_bytes()
        shipped_text = (roots[1] / skill / "SKILL.md").read_bytes()
        if src_text != shipped_text:
            report(
                f"domain-execution-references: shipped {skill} copy diverges "
                "from the canonical source."
            )
            return 1

    readme = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
    if "Execution and review checks" not in readme:
        report(
            "domain-execution-references: README does not describe the "
            "execution/review phase coverage."
        )
        return 1
    if "domain-execution-references" not in {name for name, _ in SCENARIOS}:
        report(
            "domain-execution-references: the scenario registry does not "
            "include it."
        )
        return 1

    report("domain-execution-references scenario passed.")
    return 0


def validate_domain_lens_scaffold_scenario() -> int:
    shipped = {"web", "hardware", "hardware-dsl"}
    lenses_root = ROOT / "assets/lenses"
    for name in shipped:
        if not (lenses_root / f"{name}.md").is_file():
            report(f"domain-lens-scaffold: shipped template is missing: {name}")
            return 1

    with tempfile.TemporaryDirectory(prefix="keel-lenses-") as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()

        listing = run_keel(repo, "lenses", "list")
        if listing.returncode != 0:
            report("domain-lens-scaffold: keel lenses list failed.")
            report((listing.stderr or listing.stdout).strip())
            return 1
        for name in shipped:
            if name not in listing.stdout:
                report(
                    f"domain-lens-scaffold: keel lenses list omitted the "
                    f"{name} template."
                )
                report(listing.stdout.strip())
                return 1
        if "keel/lenses/" not in listing.stdout:
            report(
                "domain-lens-scaffold: keel lenses list did not name the "
                "keel/lenses/ install location."
            )
            return 1

        add = run_keel(repo, "lenses", "add", "web")
        installed = repo / "keel/lenses/web.md"
        if add.returncode != 0 or not installed.is_file():
            report("domain-lens-scaffold: keel lenses add web did not scaffold.")
            report((add.stderr or add.stdout).strip())
            return 1
        if "Applies when:" not in installed.read_text(encoding="utf-8"):
            report(
                "domain-lens-scaffold: scaffolded lens lost its 'Applies when:' "
                "header."
            )
            return 1

        clobber = run_keel(repo, "lenses", "add", "web")
        if clobber.returncode == 0:
            report(
                "domain-lens-scaffold: a second keel lenses add web must refuse "
                "without --force."
            )
            return 1

        forced = run_keel(repo, "lenses", "add", "web", "--force")
        if forced.returncode != 0:
            report("domain-lens-scaffold: keel lenses add web --force failed.")
            report((forced.stderr or forced.stdout).strip())
            return 1

        after_add = run_keel(repo, "lenses", "list")
        if "web (installed)" not in after_add.stdout:
            report(
                "domain-lens-scaffold: keel lenses list did not mark web as "
                "installed after add."
            )
            report(after_add.stdout.strip())
            return 1

    report("domain-lens-scaffold scenario passed.")
    return 0


def validate_domain_lens_doctor_scenario() -> int:
    with tempfile.TemporaryDirectory(
        prefix="keel-lens-doctor-", ignore_cleanup_errors=True
    ) as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()

        doctor = run_keel(repo, "--doctor")
        out = doctor.stdout
        if "Domain lens surface:" not in out:
            report("domain-lens-doctor: --doctor lacks the Domain lens surface section.")
            report((doctor.stderr or out).strip())
            return 1
        for name in ("web", "hardware", "hardware-dsl"):
            if name not in out:
                report(f"domain-lens-doctor: --doctor did not report the {name} template.")
                report(out.strip())
                return 1
        if "lens templates: ok" not in out:
            report("domain-lens-doctor: --doctor did not report the shipped templates as ok.")
            report(out.strip())
            return 1

        legacy = repo / ".claude/skills/keel-profile-web/SKILL.md"
        legacy.parent.mkdir(parents=True)
        legacy.write_text("legacy profile bytes\n", encoding="utf-8")
        before = legacy.read_bytes()

        doctor2 = run_keel(repo, "--doctor")
        out2 = doctor2.stdout
        if "legacy profiles: migrate" not in out2 or "keel-profile-web" not in out2:
            report(
                "domain-lens-doctor: --doctor did not warn about the legacy "
                "keel-profile-web skill."
            )
            report(out2.strip())
            return 1
        if "not active state" not in out2:
            report(
                "domain-lens-doctor: the legacy warning must state it is not "
                "active state."
            )
            return 1
        if legacy.read_bytes() != before:
            report("domain-lens-doctor: --doctor modified the legacy skill bytes.")
            return 1

    report("domain-lens-doctor scenario passed.")
    return 0


def validate_precompact_probe_scenario() -> int:
    hooks_config = json.loads(
        (ROOT / PLUGIN_ROOT / "hooks/hooks.json").read_text(encoding="utf-8")
    )
    declared_events = sorted(hooks_config.get("hooks", {}))
    if "PreCompact" in declared_events:
        report(
            "precompact-probe: hooks.json registers a PreCompact hook without "
            "behavioral probe evidence."
        )
        return 1

    with tempfile.TemporaryDirectory(
        prefix="keel-precompact-", ignore_cleanup_errors=True
    ) as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()

        claude = run_keel(repo, "capabilities", "--target", "claude", "--json")
        if claude.returncode != 0:
            report("precompact-probe: claude capabilities probe failed.")
            return 1
        compaction = json.loads(claude.stdout).get("compaction", {})
        if compaction.get("preCompaction", {}).get("level") != "manual":
            report(
                "precompact-probe: unprobed pre-compaction must report manual, "
                f"got {compaction.get('preCompaction')!r}."
            )
            return 1
        if "probe" not in compaction.get("preCompaction", {}).get("evidence", ""):
            report("precompact-probe: pre-compaction evidence must cite probing.")
            return 1
        if compaction.get("postCompactReinjection", {}).get("level") != "advisory":
            report(
                "precompact-probe: shipped claude post-compact reinjection must "
                f"report advisory, got {compaction.get('postCompactReinjection')!r}."
            )
            return 1

        for target in ("codex", "opencode"):
            other = run_keel(repo, "capabilities", "--target", target, "--json")
            other_compaction = json.loads(other.stdout).get("compaction", {})
            reinjection = other_compaction.get("postCompactReinjection", {})
            if reinjection.get("level") != "manual":
                report(
                    f"precompact-probe: {target} compaction must be manual, got "
                    f"{reinjection!r}."
                )
                return 1
            if f"--target {target} --event compaction" not in reinjection.get(
                "evidence", ""
            ):
                report(
                    f"precompact-probe: {target} evidence must name the manual "
                    "compaction command."
                )
                return 1

        rendered = run_keel(repo, "capabilities", "--target", "claude")
        if "compaction preCompaction: manual - " not in rendered.stdout:
            report("precompact-probe: rendered capabilities lack compaction lines.")
            return 1

    readme = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
    if "--event compaction" not in readme:
        report("precompact-probe: README lacks the manual compaction command.")
        return 1
    registered = {name for name, _ in SCENARIOS}
    for scenario in ("plugin-compaction-continuity", "precompact-probe"):
        if scenario not in registered:
            report(f"precompact-probe: the scenario registry lacks {scenario}.")
            return 1

    report("precompact-probe scenario passed.")
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

        readme = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        for needle in ("keel guard start", "keel guard clear", "guard.json", "Bash"):
            if needle not in readme:
                report(f"touch-guard-surface: README lacks guard guidance: {needle}.")
                return 1
        bootstrap = (ROOT / "assets/bootstrap/AGENTS.md").read_text(encoding="utf-8")
        # The bootstrap must tell a consumer the guard exists and how to opt out;
        # it no longer spends bytes naming `keel guard clear`, which `keel --help`
        # and `keel guard status` carry. `--no-guard` is the flag it does name, so
        # that one stays literal and a rename of it still fails here.
        if "--no-guard" not in bootstrap or "guards it by default" not in bootstrap:
            report("touch-guard-surface: bootstrap does not mention the guard.")
            return 1
        registered = {name for name, _ in SCENARIOS}
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


def validate_validation_runner_scenario() -> int:
    if "SCENARIOS" not in globals():
        report("validation-runner: the scenario registry is missing.")
        return 1
    names = [name for name, _ in SCENARIOS]
    if len(names) != len(set(names)):
        report("validation-runner: registry names are not unique.")
        return 1
    defined = {
        obj_name
        for obj_name, obj in globals().items()
        if callable(obj)
        and obj_name.startswith("validate_")
        and obj_name.endswith("_scenario")
    }
    registered = {func.__name__ for _, func in SCENARIOS}
    orphans = sorted(defined - registered)
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
    readme = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
    if "--all" not in readme or "--jobs" not in readme:
        report("validation-runner: README does not document the parallel runner.")
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


# The one ordered scenario registry: --scenario dispatch, the --all runner,
# and registration assertions all read this list and nothing else.
def validate_doctor_openspec_honesty_scenario() -> int:
    cli = (ROOT / "bin/keel.js").read_text(encoding="utf-8")
    if "is not on PATH" not in cli:
        report(
            "doctor-openspec-honesty scenario: bin/keel.js is missing the "
            "openspec PATH-reachability warning branch."
        )
        return 1
    with tempfile.TemporaryDirectory(prefix="keel-doctor-openspec-") as raw:
        root = Path(raw)
        repo = root / "repo"
        repo.mkdir()
        stub_dir = root / "stub"
        stub_dir.mkdir()
        if os.name == "nt":
            (stub_dir / "openspec.cmd").write_text(
                "@echo off\necho 1.6.0\n", encoding="utf-8"
            )
        else:
            stub = stub_dir / "openspec"
            stub.write_text("#!/bin/sh\necho 1.6.0\n", encoding="utf-8")
            stub.chmod(0o755)
        env = dict(os.environ)
        env["PATH"] = str(stub_dir) + os.pathsep + env.get("PATH", "")
        on_path = run_keel(repo, "--doctor", env=env)
        openspec_line = next(
            (
                line
                for line in on_path.stdout.splitlines()
                if line.startswith("openspec:")
            ),
            "",
        )
        if not openspec_line.startswith("openspec: ok"):
            report(
                "doctor-openspec-honesty scenario: doctor did not report `ok` "
                "when a bare openspec is on PATH."
            )
            report(on_path.stdout.strip())
            return 1
    report("doctor-openspec-honesty scenario passed.")
    return 0


SCENARIOS: tuple = (
    ("stateless-continuity", validate_stateless_continuity_scenario),
    ("core-gates", validate_core_gates_scenario),
    ("scope-rename-attribution", validate_scope_rename_attribution_scenario),
    ("target-capability-adapters", validate_target_capability_adapters_scenario),
    ("native-runtime-projection", validate_native_runtime_projection_scenario),
    ("target-surface", validate_target_surface_scenario),
    ("thin-native-install", validate_thin_native_install_scenario),
    ("expectation-slice-gates", validate_expectation_slice_gates_scenario),
    ("expectation-completion-gates", validate_expectation_completion_gates_scenario),
    ("authoring-continuity", validate_authoring_continuity_scenario),
    ("domain-lenses", validate_domain_lenses_scenario),
    ("skill-portability-policy", validate_skill_portability_policy_scenario),
    ("version-alignment", validate_version_alignment_scenario),
    ("openspec-surface-overlay", validate_openspec_surface_overlay_scenario),
    ("uninstall", validate_uninstall_scenario),
    ("cli", validate_cli_scenario),
    ("doctor-openspec-honesty", validate_doctor_openspec_honesty_scenario),
    ("update-pack-install", validate_update_pack_install_scenario),
    ("update-default-registry", validate_update_default_registry_scenario),
    ("verification-layering-docs", validate_verification_layering_docs_scenario),
    ("fast-check-config-scaffold", validate_fast_check_config_scaffold_scenario),
    ("fast-pre-push-hooks", validate_fast_pre_push_hooks_scenario),
    ("fast-pre-push-doctor", validate_fast_pre_push_doctor_scenario),
    ("verify-layer-tag", validate_verify_layer_tag_scenario),
    (
        "non-concrete-verify-diagnostic",
        validate_non_concrete_verify_diagnostic_scenario,
    ),
    ("inline-code-is-concrete", validate_inline_code_is_concrete_scenario),
    ("covers-separator-collision", validate_covers_separator_collision_scenario),
    (
        "unresolved-authority-names-field",
        validate_unresolved_authority_names_field_scenario,
    ),
    (
        "dev-only-plugin-source-scoping",
        validate_dev_only_plugin_source_scoping_scenario,
    ),
    (
        "source-repo-bootstrap-skip",
        validate_source_repo_bootstrap_skip_scenario,
    ),
    ("tracker-durable-owner", validate_tracker_durable_owner_scenario),
    ("guard-manifest-ignored", validate_guard_manifest_ignored_scenario),
    (
        "guard-status-is-not-enforcement",
        validate_guard_status_is_not_enforcement_scenario,
    ),
    ("source-repo-cli-resolution", validate_source_repo_cli_resolution_scenario),
    ("task-contract-core", validate_task_contract_core_scenario),
    ("task-capsule", validate_task_capsule_scenario),
    ("task-verification-strategies", validate_task_verification_strategies_scenario),
    ("compact-task-authoring", validate_compact_task_authoring_scenario),
    ("expectation-alignment-skill", validate_expectation_alignment_skill_scenario),
    (
        "expectation-alignment-real-tasks",
        validate_expectation_alignment_real_tasks_scenario,
    ),
    ("authoring-alignment-overlay", validate_authoring_alignment_overlay_scenario),
    ("native-plugin-manifests", validate_native_plugin_manifests_scenario),
    ("native-plugin-session-start", validate_native_plugin_session_start_scenario),
    ("native-plugin-marketplaces", validate_native_plugin_marketplaces_scenario),
    ("native-plugin-install-matrix", validate_native_plugin_install_matrix_scenario),
    ("native-goal-projection", validate_native_goal_projection_scenario),
    ("native-goal-gate-order", validate_native_goal_gate_order_scenario),
    ("native-goal-continuity", validate_native_goal_continuity_scenario),
    ("native-helper-brief", validate_native_helper_brief_scenario),
    ("native-helper-read-only", validate_native_helper_read_only_scenario),
    ("native-goal-capabilities", validate_native_goal_capabilities_scenario),
    ("single-task-goal-skill", validate_single_task_goal_skill_scenario),
    ("single-task-goal-real-tasks", validate_single_task_goal_real_tasks_scenario),
    ("native-goal-codex", validate_native_goal_codex_scenario),
    ("native-goal-claude", validate_native_goal_claude_scenario),
    ("native-helper-targets", validate_native_helper_targets_scenario),
    ("native-single-task-matrix", validate_native_single_task_matrix_scenario),
    ("touch-write-guard", validate_touch_write_guard_scenario),
    ("touch-guard-record-layer", validate_touch_guard_record_layer_scenario),
    ("repo-action-mode", validate_repo_action_mode_scenario),
    ("runner-skip-accounting", validate_runner_skip_accounting_scenario),
    ("resident-topic-matching", validate_resident_topic_matching_scenario),
    ("task-start-invalidation", validate_task_start_invalidation_scenario),
    ("regression-check-tag", validate_regression_check_tag_scenario),
    ("durable-owner-vocabulary", validate_durable_owner_vocabulary_scenario),
    (
        "authoring-surface-owner-and-tags",
        validate_authoring_surface_owner_and_tags_scenario,
    ),
    (
        "packaged-schema-derivation",
        validate_packaged_schema_derivation_scenario,
    ),
    (
        "invalidation-authoring-surface",
        validate_invalidation_authoring_surface_scenario,
    ),
    (
        "completed-sibling-attribution",
        validate_completed_sibling_attribution_scenario,
    ),
    ("touch-guard-drift", validate_touch_guard_drift_scenario),
    ("touch-guard-surface", validate_touch_guard_surface_scenario),
    ("plugin-compaction-continuity", validate_plugin_compaction_continuity_scenario),
    ("precompact-probe", validate_precompact_probe_scenario),
    ("domain-execution-references", validate_domain_execution_references_scenario),
    ("domain-lens-scaffold", validate_domain_lens_scaffold_scenario),
    ("domain-lens-doctor", validate_domain_lens_doctor_scenario),
    ("plan-funnel-guidance", validate_plan_funnel_guidance_scenario),
    ("native-tasks-view", validate_native_tasks_view_scenario),
    ("validation-runner", validate_validation_runner_scenario),
)


def run_scenario_processes(names: list, jobs: int) -> list:
    """Run each named scenario as its own --scenario subprocess in parallel.

    Output is captured per scenario and the result list preserves the input
    order so a replay is deterministic regardless of completion timing.
    """
    script = str(Path(__file__).resolve())

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


def validate_review_status_single_source(errors: list[str]) -> None:
    contract = (ROOT / "src/core/task-contract.js").read_text(encoding="utf-8")
    if "ACCEPTED_REVIEW_STATUSES" not in contract:
        errors.append(
            "src/core/task-contract.js must define the shared "
            "ACCEPTED_REVIEW_STATUSES constant."
        )
    if '"done"' not in contract:
        errors.append(
            "ACCEPTED_REVIEW_STATUSES must include the `done` Review Status."
        )
    literal = "pass|passed|complete|completed|ok"
    for relative in ("src/core/gates.js", "src/core/context.js"):
        content = (ROOT / relative).read_text(encoding="utf-8")
        if "ACCEPTED_REVIEW_STATUSES" not in content:
            errors.append(
                f"{relative} must consume the shared ACCEPTED_REVIEW_STATUSES "
                "constant rather than an inline Review Status vocabulary."
            )
        if literal in content:
            errors.append(
                f"{relative} still hard-codes the Review Status vocabulary "
                f"`{literal}`; consume the shared constant instead."
            )


def validate_install_honesty(errors: list[str]) -> None:
    installer = (ROOT / "scripts/install_to_repo.py").read_text(encoding="utf-8")
    if "def skill_actions" in installer or "dist_asset(target_name, \"skills\")" in installer:
        errors.append(
            "install_to_repo.py must not carry the dead keel-* skill_actions "
            "path; keel-* skills are plugin-delivered."
        )
    cli = (ROOT / "bin/keel.js").read_text(encoding="utf-8")
    if "delivered by the installed Keel plugin" not in cli:
        errors.append(
            "keel --help/--doctor must state that keel-* skills are delivered "
            "by the installed Keel plugin, not installed by the CLI."
        )
    if ".claude/skills/keel-*." in cli:
        errors.append(
            "keel --help must not claim the CLI installs skills under "
            ".claude/skills/keel-*."
        )


def validate_openspec_invocable(errors: list[str]) -> None:
    cli = (ROOT / "bin/keel.js").read_text(encoding="utf-8")
    if 'options.action === "openspec"' not in cli:
        errors.append("bin/keel.js must implement the `keel openspec` passthrough.")
    if cli.count("Invoke OpenSpec through") < 2:
        errors.append(
            "the apply and archive overlays must direct agents to `keel openspec` "
            "in place of a bare openspec command."
        )


def validate_archive_overlay_hygiene(errors: list[str]) -> None:
    cli = (ROOT / "bin/keel.js").read_text(encoding="utf-8")
    if "--skip-specs" not in cli:
        errors.append(
            "the archive overlay must direct archive to pass --skip-specs "
            "after /opsx:sync has promoted the delta."
        )
    if "drop the change's guard manifest" not in cli:
        errors.append(
            "the archive overlay must remind the agent to run keel guard clear "
            "after archiving."
        )
    gates = (ROOT / "src/core/gates.js").read_text(encoding="utf-8")
    if "clearGuard" in gates:
        errors.append(
            "gates must stay read-only: gate code must not clear the guard "
            "manifest (guard clear is explicit via keel guard clear)."
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

    return run_baseline()


if __name__ == "__main__":
    sys.exit(main())

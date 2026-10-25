"""Keel validation: baseline (split from validate_plugin.py, #409)."""
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
    LEGACY_PROFILE_SKILLS,
    PACKAGE_VERSION,
    ROOT,
)


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


CORE_KEEL_SKILLS = {
    "align-expectations",
    "debug-failure",
    "handoff",
    "review-checklist",
    "tdd-or-test-first",
}


TEMPLATE_REQUIREMENTS: list[dict] = []


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
# Keel subcommands that write. A scenario may point read-only ones at the
# repository root; these need a fixture.
MUTATING_KEEL_COMMANDS = (
    "--install",
    "--init",
    "--uninstall",
    "--clear",
    "--update",
    "--with-git-hooks",
)


RETIRED_PATH_EXPRESSIONS = (
    r'ROOT\s*/\s*"dist"',
    r'ROOT\s*/\s*"src"\s*/\s*"assets"',
    r'ROOT\s*/\s*"src"\s*/\s*"hooks"',
    r'ROOT\s*/\s*"src"\s*/\s*"adapters"',
)


def runner_sources() -> list[Path]:
    """The runner's files under this module's ROOT: the entry point and every module (#409)."""
    return [ROOT / "scripts/validate_plugin.py", *sorted((ROOT / "scripts/validation").glob("*.py"))]


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

    # Every file of the runner — the entry point and each module under
    # scripts/validation/ — since a scan of one file would pass over whatever
    # moved out of it (#409).
    validator_sources = [
        (path.relative_to(ROOT).as_posix(), path.read_text(encoding="utf-8"))
        for path in runner_sources()
    ]

    # A scenario that writes to the repository it validates can satisfy the very
    # condition another check asserts, and a check whose input its own run
    # produces cannot fail. Reads against ROOT are fine and common; writes are
    # not. Keyed on the mutating subcommand rather than on ROOT itself, so
    # `--version`, `--doctor`, and the gates stay legal.
    for relative, validator_source in validator_sources:
        for line_number, line in enumerate(validator_source.splitlines(), start=1):
            invocation = re.search(r"run_(?:keel|install)\(\s*ROOT\s*,([^)]*)", line)
            if not invocation:
                continue
            if any(
                re.search(rf'"{command}"', invocation.group(1))
                for command in MUTATING_KEEL_COMMANDS
            ):
                errors.append(
                    "a scenario must not run a mutating Keel command against the "
                    "repository it validates; build a fixture instead: "
                    f"{relative}:{line_number}: {line.strip()}"
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
    for relative, validator_source in validator_sources:
        for line_number, line in enumerate(validator_source.splitlines(), start=1):
            if any(re.search(pattern, line) for pattern in RETIRED_PATH_EXPRESSIONS):
                errors.append(
                    "validator resolves a path under a retired distribution tree, "
                    "so the check it feeds can only iterate nothing: "
                    f"{relative}:{line_number}: {line.strip()}"
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
    # `validation` is the runner's own package under scripts/ (#409).
    allowed = stdlib_modules | {"__future__", "validation"}

    # The runner's modules under scripts/validation/ are scripts too (#409).
    for script in sorted({*(ROOT / "scripts").glob("*.py"), *runner_sources()}):
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
    # Once per overlay, in the header every action shares (#413).
    if cli.count("Invoke the OpenSpec CLI as `keel openspec") < 2:
        errors.append(
            "the apply, archive, and sync overlays must direct agents to `keel openspec` "
            "in place of a bare openspec command."
        )


def validate_archive_overlay_hygiene(errors: list[str]) -> None:
    cli = (ROOT / "bin/keel.js").read_text(encoding="utf-8")
    if "--skip-specs" not in cli:
        errors.append(
            "the archive overlay must direct archive to pass --skip-specs "
            "after the openspec-sync-specs skill has promoted the delta."
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

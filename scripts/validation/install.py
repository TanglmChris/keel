"""Keel validation: install (split from validate_plugin.py, #409)."""
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
    BOOTSTRAP_BLOCK_BYTE_BUDGET,
    LEGACY_PROFILE_SKILLS,
    MANAGED_END,
    OPENSPEC_CONFIG_PATH,
    OPENSPEC_SCHEMA_ROOT,
    OPENSPEC_SURFACE_OVERLAY_END,
    OPENSPEC_SURFACE_OVERLAY_START,
    PACKAGE_VERSION,
    PLUGIN_ROOT,
    ROOT,
    extract_managed_block,
    guard_task_fixture,
    packaged_openspec_schema_install_paths,
    path_without_openspec,
    report,
    run_keel,
    run_openspec,
    skip_scenario,
    snapshot_files,
    validate_openspec_schema,
    validate_resident_blocks,
    validate_skill_docs,
    validate_skill_portability,
    validation_source_with,
    write_text,
)
from validation import registry


# Mirrors KEEL_PACKAGE_NAME in scripts/install_to_repo.py, one of the two
# signals is_keel_source_repo reads.
KEEL_PACKAGE_NAME = "@christang/keel"


TARGET_SKILL_ROOTS = {
    "claude": Path(".claude") / "skills",
    "codex": Path(".agents") / "skills",
    "opencode": Path(".opencode") / "skills",
}


def has_managed_block(path: Path) -> bool:
    if not path.is_file():
        return False
    return extract_managed_block(path.read_text(encoding="utf-8")) is not None


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
    for path in (ROOT / "AGENTS.md", ROOT / "README.md", ROOT / "README.zh-CN.md"):
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
            or "skills only" not in claude_doctor.stdout
            or "OpenSpec action skills: ok" not in claude_doctor.stdout
            or ".claude/skills" not in posix_paths(claude_doctor.stdout)
            or "bootstrap: ok" not in claude_doctor.stdout
            or "CLAUDE import: ok" not in claude_doctor.stdout
            or "native plugin runtime: manual" not in claude_doctor.stdout
            or "Target capabilities (claude):" not in claude_doctor.stdout
            or "gate.change-close: manual" not in claude_doctor.stdout
            or "execution.worktree: manual" not in claude_doctor.stdout
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
        if (
            codex_doctor.returncode != 0
            or "OpenSpec commands: ok" not in codex_doctor.stdout
            or "OpenSpec 1.13 and later surface Codex's workflows" not in codex_doctor.stdout
            or "OpenSpec action skills: ok" not in codex_doctor.stdout
            or ".agents/skills" not in posix_paths(codex_doctor.stdout)
            or "bootstrap: ok" not in codex_doctor.stdout
            or "native plugin runtime: manual" not in codex_doctor.stdout
            or "Target capabilities (codex):" not in codex_doctor.stdout
            or "gate.change-close: manual" not in codex_doctor.stdout
            or "execution.worktree: manual" not in codex_doctor.stdout
        ):
            report("target-surface scenario Codex doctor did not report full surface.")
            report((codex_doctor.stderr or codex_doctor.stdout).strip())
            return 1
        if (codex_repo / ".claude").exists():
            report("target-surface scenario Codex init created Claude-only paths.")
            return 1

        # OpenSpec 1.13 writes Codex's workflows as skills only (#169), so the
        # surface that can go missing is a skill.
        shutil.rmtree(codex_repo / ".agents/skills/openspec-propose")
        codex_missing = run_keel(codex_repo, "--doctor", "--target", "codex", env=env)
        if (
            codex_missing.returncode != 0
            or "OpenSpec action skills: missing" not in codex_missing.stdout
        ):
            report("target-surface scenario Codex doctor did not report a missing skill.")
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
            or "skills only" not in opencode_doctor.stdout
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


def openspec_overlay_files(
    repo: Path,
    target: str,
    codex_home: Path | None = None,
) -> dict[str, list[Path]]:
    # Keel generates skills only (#406); a command file counts only while a
    # repository still holds one from an earlier `both` delivery.
    def held(*paths: Path) -> list[Path]:
        return [paths[0], *[p for p in paths[1:] if p.exists()]]

    if target == "claude":
        return {
            "apply": held(
                repo / ".claude/skills/openspec-apply-change/SKILL.md",
                repo / ".claude/commands/opsx/apply.md",
            ),
            "archive": held(
                repo / ".claude/skills/openspec-archive-change/SKILL.md",
                repo / ".claude/commands/opsx/archive.md",
            ),
        }
    if target == "codex":
        assert codex_home is not None
        # OpenSpec 1.13 and later, including the 1.14 Keel pins, write Codex's workflows as skills
        # under `.agents/skills` and no command files (#169).
        return {
            "apply": [repo / ".agents/skills/openspec-apply-change/SKILL.md"],
            "archive": [repo / ".agents/skills/openspec-archive-change/SKILL.md"],
        }
    return {
        "apply": held(
            repo / ".opencode/skills/openspec-apply-change/SKILL.md",
            repo / ".opencode/commands/opsx-apply.md",
        ),
        "archive": held(
            repo / ".opencode/skills/openspec-archive-change/SKILL.md",
            repo / ".opencode/commands/opsx-archive.md",
        ),
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

    # Since #414 the overlay says one neutral thing about subagents and assigns
    # no ownership; apply continues through an approved task list.
    required = [
        "Keel rules below take precedence",
        "A subagent is the model's choice and is treated as the main agent is",
    ]
    if action == "apply":
        required.extend(
            [
                "approved `tasks.md` in order",
                "Task Authoring Gate",
                "Slice Start Gate",
                "source expectations",
                "Rough future slices",
                # A confirmation the owner already declared is routed to the
                # declaration; one they did not declare is still asked for, and
                # neither case touches the proof.
                "standing-authorized action proceeds without",
                "undeclared action still requires",
                "never substitutes for a gate",
            ]
        )
    else:
        required.extend(
            [
                "keel gate change-close --action archive",
                "keel-review-checklist",
                "critical expectation",
                "behavior evidence",
                "durable follow-up owner",
                "explicit discard reason",
                "standing-authorizes `archive`",
                "completion gate and follow-up ownership checks still run",
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


OVERLAY_ACTION_SKILLS = {
    "propose": "openspec-propose",
    "apply": "openspec-apply-change",
    "archive": "openspec-archive-change",
    "sync": "openspec-sync-specs",
}


def expected_overlay_surfaces(
    repo: Path,
    target: str,
    codex_home: Path | None = None,
) -> list[Path]:
    """Every surface `openspecOverlaySurfacesForTarget` projects the overlay onto.

    Written out rather than discovered, so that a scan of the tree can be
    compared against it. A scan alone answers "the files that carry the
    marker", which is the same answer whether the CLI covered eight surfaces
    or none — and "none of them still carry it" is exactly what a broken
    surface list also reports.
    """
    surfaces: list[Path] = []
    for action, skill in OVERLAY_ACTION_SKILLS.items():
        if action == "propose" and target == "opencode":
            continue
        # Keel generates skills only (#406); a command file counts only while a
        # repository still holds one from an earlier `both` delivery.
        if target == "claude":
            surfaces.append(repo / f".claude/skills/{skill}/SKILL.md")
            command = repo / f".claude/commands/opsx/{action}.md"
        elif target == "codex":
            assert codex_home is not None
            surfaces.append(repo / f".agents/skills/{skill}/SKILL.md")
            command = None
        else:
            surfaces.append(repo / f".opencode/skills/{skill}/SKILL.md")
            command = repo / f".opencode/commands/opsx-{action}.md"
        if command is not None and command.exists():
            surfaces.append(command)
    return surfaces


def files_carrying_overlay(*roots: Path) -> set[Path]:
    found: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*.md"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if "keel:openspec-surface-overlay" in text:
                found.add(path)
    return found


def validate_uninstall_removes_the_overlay_scenario() -> int:
    """Uninstalling left Keel's instructions in files OpenSpec owns.

    The overlay block is written into the `opsx` command surfaces and the
    `openspec-*` skills, and every line of it is about Keel: the gate to run,
    the checklist to run, how to invoke OpenSpec, where standing authorization
    is declared. `keel --uninstall` removed the `keel:start` managed block from
    AGENTS.md and CLAUDE.md and left all of that behind.

    Measured 2026-08-03 at 5.22.0: Claude 8 of 8 surfaces, Codex 8 of 8 (four
    of them under `CODEX_HOME/prompts/`), OpenCode 6 of 6 still carried the
    marker after uninstall. Filed as
    https://github.com/TanglmChris/keel/issues/50.
    """
    label = "uninstall-removes-the-overlay"
    with tempfile.TemporaryDirectory(prefix="keel-uninstall-overlay-") as raw:
        tmp = Path(raw)

        for target in ("claude", "codex", "opencode"):
            repo = tmp / target
            repo.mkdir()
            env = None
            codex_home = None
            roots = [repo]
            if target == "codex":
                codex_home = tmp / "codex-home"
                env = os.environ.copy()
                env["CODEX_HOME"] = str(codex_home)
                roots.append(codex_home)

            init = run_keel(repo, "--init", "--target", target, env=env)
            if init.returncode != 0:
                report(f"{label} `keel --init --target {target}` failed.")
                report((init.stderr or init.stdout).strip())
                return 1

            # M1 positive control — the surfaces the CLI writes to are the ones
            # this scenario is about to check, asserted before the act. Without
            # it, a run whose surface list resolved to nothing reports the same
            # clean tree as a run that removed everything.
            expected = set(expected_overlay_surfaces(repo, target, codex_home))
            carrying = files_carrying_overlay(*roots)
            if carrying != expected:
                report(
                    f"{label} M1 the {target} surfaces carrying the overlay "
                    "after init are not the ones this scenario expects, so "
                    "nothing after this measures removal."
                )
                report(f"  only installed: {sorted(str(p) for p in carrying - expected)}")
                report(f"  only expected:  {sorted(str(p) for p in expected - carrying)}")
                return 1

            # M2 — what the file held before Keel's block, kept so the whole
            # file can be compared against it afterwards. Trailing newlines are
            # normalized to one because the separator the install side inserted
            # before the block goes with the block.
            bodies = {}
            for surface in expected:
                text = surface.read_text(encoding="utf-8")
                head = text[: text.index("<!-- keel:openspec-surface-overlay")]
                bodies[surface] = head.rstrip("\n") + "\n"

            uninstall = run_keel(repo, "--uninstall", "--target", target, env=env)
            if uninstall.returncode != 0:
                report(f"{label} M1 `keel --uninstall --target {target}` failed.")
                report((uninstall.stderr or uninstall.stdout).strip())
                return 1

            # M1 — nothing Keel wrote is left in a file OpenSpec owns.
            left = files_carrying_overlay(*roots)
            if left:
                report(
                    f"{label} M1 uninstalling {target} left the Keel overlay "
                    f"in {len(left)} of {len(expected)} surfaces, so the "
                    "uninstalled repository still instructs an agent to run "
                    "commands that were just removed."
                )
                for path in sorted(str(p) for p in left):
                    report(f"  {path}")
                return 1

            # M4 — the run says how many surfaces it cleaned. An uninstall that
            # silently does nothing and an uninstall that cleaned everything
            # produce the same tree on a repository that was never installed.
            if f"removed={len(expected)}" not in uninstall.stdout:
                report(
                    f"{label} M4 uninstalling {target} did not report the "
                    f"{len(expected)} overlays it removed."
                )
                report((uninstall.stderr or uninstall.stdout).strip())
                return 1

            # M2 — the block, and only the block. The file is OpenSpec's, so a
            # removal that took the marker and anything either side of it is a
            # worse defect than the one being fixed, and "the marker is gone"
            # cannot tell the two apart.
            for surface, body in bodies.items():
                if not surface.is_file():
                    report(
                        f"{label} M2 uninstalling {target} deleted {surface}, "
                        "which is OpenSpec's file. Removing Keel's block is "
                        "the whole obligation."
                    )
                    return 1
                after = surface.read_text(encoding="utf-8")
                if after != body:
                    report(
                        f"{label} M2 uninstalling {target} did not leave "
                        f"{surface} at the bytes that preceded the overlay."
                    )
                    report(f"  expected {len(body)} bytes ending {body[-40:]!r}")
                    report(f"  found    {len(after)} bytes ending {after[-40:]!r}")
                    return 1

        # M3 — a dry run plans the writes it would make. `--check` already had
        # to learn that a Node-side step the installer's plan cannot see makes
        # a dry run under-report a run that writes; the uninstall side has the
        # same shape.
        dry = tmp / "dry-run"
        dry.mkdir()
        dry_init = run_keel(dry, "--init", "--target", "claude")
        if dry_init.returncode != 0:
            report(f"{label} M3 dry-run fixture init failed.")
            report((dry_init.stderr or dry_init.stdout).strip())
            return 1
        dry_expected = set(expected_overlay_surfaces(dry, "claude"))
        dry_run = run_keel(dry, "--uninstall", "--target", "claude", "--dry-run")
        if dry_run.returncode != 0:
            report(f"{label} M3 `keel --uninstall --dry-run` failed.")
            report((dry_run.stderr or dry_run.stdout).strip())
            return 1
        unplanned = [
            str(surface)
            for surface in sorted(dry_expected)
            if str(surface) not in dry_run.stdout
        ]
        if unplanned:
            report(
                f"{label} M3 the dry run did not name {len(unplanned)} of "
                f"{len(dry_expected)} surfaces it would clean, so the plan "
                "under-reports a run that writes."
            )
            for surface in unplanned:
                report(f"  {surface}")
            return 1
        if files_carrying_overlay(dry) != dry_expected:
            report(
                f"{label} M3 the dry run removed overlays. A dry run reports "
                "what it would do and writes nothing."
            )
            return 1

        # M4 — uninstalling again, and uninstalling a repository that never
        # received the overlay, both succeed. Uninstall is something a user
        # reaches for when something is already wrong; failing on the second
        # attempt is the worst moment to fail.
        again = run_keel(tmp / "claude", "--uninstall", "--target", "claude")
        if again.returncode != 0:
            report(
                f"{label} M4 a second uninstall failed. Uninstall is reached "
                "when something is already wrong; failing on the second "
                "attempt is the worst moment to fail."
            )
            report((again.stderr or again.stdout).strip())
            return 1
        if "removed=0" not in again.stdout:
            report(
                f"{label} M4 a second uninstall did not report that it removed "
                "nothing, so a run that cleaned nothing reads like a run that "
                "cleaned everything."
            )
            report((again.stderr or again.stdout).strip())
            return 1

        bare = tmp / "install-only"
        bare.mkdir()
        bare_install = run_keel(bare, "--install", "--target", "claude")
        if bare_install.returncode != 0:
            report(f"{label} M4 install-only fixture failed.")
            report((bare_install.stderr or bare_install.stdout).strip())
            return 1
        bare_uninstall = run_keel(bare, "--uninstall", "--target", "claude")
        if bare_uninstall.returncode != 0:
            report(
                f"{label} M4 uninstalling a repository whose OpenSpec surfaces "
                "were never created failed. An absent surface is nothing to "
                "remove, not an error."
            )
            report((bare_uninstall.stderr or bare_uninstall.stdout).strip())
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_sync_surface_overlay_scenario() -> int:
    """The surface that performs a gated action never named its gate.

    AGENTS.md gates sync and archive identically — `keel gate change-close
    --action sync|archive` plus `keel-review-checklist`. Archive's command
    surface carries a Keel overlay saying so; sync's carried none, because
    `OPENSPEC_OVERLAY_ACTIONS` listed only propose, apply, and archive. An
    agent invoking `/opsx:sync` read generic upstream instructions and was told
    nothing about the gate that decides whether the sync may complete.

    Measured 2026-08-02: neither `.claude/commands/opsx/sync.md` nor
    `.claude/skills/openspec-sync-specs/SKILL.md` contained `change-close`,
    `keel gate`, or `keel openspec`.
    """
    label = "sync-surface-overlay"
    marker = "keel:openspec-surface-overlay"
    with tempfile.TemporaryDirectory(prefix="keel-sync-overlay-") as raw:
        tmp = Path(raw)

        surfaces = {
            # Skills only since #406: Keel generates no `.claude/commands/opsx/`.
            "claude": [
                ".claude/skills/openspec-sync-specs/SKILL.md",
            ],
            "codex": [
                ".agents/skills/openspec-sync-specs/SKILL.md",
            ],
        }

        for target, paths in surfaces.items():
            repo = tmp / target
            repo.mkdir()
            init = run_keel(repo, "--init", "--target", target)
            if init.returncode != 0:
                report(f"{label} M1 `keel --init --target {target}` failed.")
                report((init.stderr or init.stdout).strip())
                return 1

            # M1 — the marker lands on every sync surface the target has.
            for relative in paths:
                surface = repo / relative
                if not surface.is_file():
                    report(
                        f"{label} M1 {target} has no sync surface at "
                        f"{relative}, so the projection has nothing to cover."
                    )
                    return 1
                text = surface.read_text(encoding="utf-8")
                if marker not in text:
                    report(
                        f"{label} M1 {relative} carries no Keel overlay, so the "
                        "surface that performs a gated action never names its "
                        "gate."
                    )
                    return 1

                # M2 — and it says the things that change behavior.
                for needle, why in (
                    ("keel gate change-close --action sync", "the gate"),
                    ("keel-review-checklist", "the semantic review"),
                    ("keel openspec", "how to invoke OpenSpec off PATH"),
                    ("--skip-specs", "that a following archive must skip specs"),
                ):
                    if needle not in text:
                        report(
                            f"{label} M2 the sync overlay in {relative} does "
                            f"not name {why} ({needle!r})."
                        )
                        return 1

            # M4 — explore stays uncovered, deliberately.
            explore = repo / (
                ".claude/skills/openspec-explore/SKILL.md" if target == "claude"
                else ".agents/skills/openspec-explore/SKILL.md"
            )
            if explore.is_file() and marker in explore.read_text(encoding="utf-8"):
                report(
                    f"{label} M4 the explore surface received an overlay. It "
                    "reaches no gate and changes no state, so an overlay there "
                    "reads as governance where there is none."
                )
                return 1

            # M3 — the doctor names sync rather than a hardcoded pair.
            doctor = run_keel(repo, "--doctor", "--target", target)
            overlay_lines = [
                line for line in doctor.stdout.splitlines()
                if "overlay" in line and line.startswith("Keel ")
            ]
            if not overlay_lines:
                report(f"{label} M3 {target} `keel --doctor` printed no overlay line.")
                report((doctor.stderr or doctor.stdout).strip())
                return 1
            if not any("sync" in line for line in overlay_lines):
                report(
                    f"{label} M3 the {target} doctor overlay line does not name "
                    f"sync: {overlay_lines}"
                )
                return 1
            if not any(": ok" in line for line in overlay_lines):
                report(
                    f"{label} M3 the {target} doctor did not report the overlay "
                    f"healthy after a fresh install: {overlay_lines}"
                )
                return 1

            # Uninstall is asserted by `uninstall-removes-the-overlay`, which
            # covers every surface on every target rather than sync alone. It
            # stripped nothing from any surface when this scenario was written;
            # that was #50, and the assertion lives there because the contract
            # is about all four actions, not about this one.

    # M4 — covering the surface did not widen what may be standing-authorized.
    config_doc = (ROOT / "keel/config.yaml").read_text(encoding="utf-8")
    if re.search(r"^\s*-\s*sync\s*$", config_doc, re.MULTILINE):
        report(
            f"{label} M4 `sync` was added to the standing-authorization "
            "vocabulary. Naming the gate that governs an action and deciding "
            "whether a repository may authorize it once are separate."
        )
        return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def overlay_action_label(text: str, pattern: str) -> str | None:
    """The action list a summary line names, or None when the line is absent.

    `\\S*` rather than `\\S+` on purpose: a label that derived to nothing leaves
    two spaces where the actions belong, and matching it is what lets an empty
    label be reported as empty instead of as a missing line.
    """
    match = re.search(pattern, text)
    if match is None:
        return None
    return match.group(1)


def validate_update_restores_overlays_scenario() -> int:
    label = "update-restores-overlays:"
    with tempfile.TemporaryDirectory(prefix="keel-update-overlays-") as raw:
        tmp = Path(raw)
        repo = tmp / "mixed"
        repo.mkdir()
        env = os.environ.copy()
        env["CODEX_HOME"] = str(tmp / "codex-home")
        for target in ("claude", "codex"):
            result = run_keel(repo, "--init", "--target", target, env=env)
            if result.returncode:
                report(f"{label} init {target} failed: {result.stderr or result.stdout}")
                return 1
        # Diagnose a missing foreign target before the upstream rewrite.
        codex_paths = [p for paths in openspec_overlay_files(
            repo, "codex", tmp / "codex-home").values() for p in paths]
        for p in codex_paths:
            if p.exists():
                p.write_text(strip_openspec_surface_overlay(p.read_text()), encoding="utf-8")
        doctor = run_keel(repo, "--doctor", "--target", "claude", env=env)
        if not re.search(r"Codex.*overlay: (missing|partial)", doctor.stdout):
            report(f"{label} doctor hid missing Codex overlays while selecting Claude")
            return 1
        for iteration in range(2):
            result = run_keel(repo, "openspec", "update", env=env)
            if result.returncode:
                report(f"{label} update failed: {result.stderr or result.stdout}")
                return 1
            for target in ("claude", "codex"):
                error = assert_target_overlays(repo, target, tmp / "codex-home")
                if error:
                    report(f"{label} update {iteration}: {error}")
                    return 1
                for action, skill in OVERLAY_ACTION_SKILLS.items():
                    surface = repo / (".claude/skills" if target == "claude" else ".agents/skills") / skill / "SKILL.md"
                    content = surface.read_text()
                    if content.count(OPENSPEC_SURFACE_OVERLAY_START) != 1 or content.count(OPENSPEC_SURFACE_OVERLAY_END) != 1:
                        report(f"{label} managed action has missing or duplicate overlays: {surface}")
                        return 1
                    if not strip_openspec_surface_overlay(content).strip():
                        report(f"{label} upstream body removed: {surface}")
                        return 1
        legacy = tmp / "legacy"
        legacy.mkdir()
        result = run_keel(legacy, "--init", "--target", "claude", env=env)
        if result.returncode:
            report(f"{label} legacy fixture init failed")
            return 1
        for skill in OVERLAY_ACTION_SKILLS.values():
            write_text(legacy / ".codex/skills" / skill / "SKILL.md", "# Legacy OpenSpec workflow\n")
        doctor = run_keel(legacy, "--doctor", "--target", "claude", env=env)
        if not re.search(r"Codex.*overlay: (missing|partial)", doctor.stdout):
            report(f"{label} legacy Codex coverage was hidden")
            return 1
        # A single-target repository must stay isolated, even with global prompts.
        single = tmp / "single"
        single.mkdir()
        result = run_keel(single, "--init", "--target", "claude", env=env)
        if result.returncode:
            report(f"{label} single init failed")
            return 1
        result = run_keel(single, "openspec", "update", env=env)
        if result.returncode or (single / ".agents/skills").exists() or (single / ".codex/skills").exists():
            report(f"{label} single-target update failed or created Codex surfaces")
            return 1
        doctor = run_keel(single, "--doctor", "--target", "claude", env=env)
        if re.search(r"Codex.*overlay:", doctor.stdout):
            report(f"{label} global prompts enrolled an unrelated repository")
            return 1
        # Invalid options fail in real upstream OpenSpec; no recovery may write.
        surface = repo / ".agents/skills/openspec-apply-change/SKILL.md"
        surface.write_text(strip_openspec_surface_overlay(surface.read_text()), encoding="utf-8")
        files = {p: p.read_bytes() for p in repo.rglob("*.md")}
        upstream = subprocess.run(
            ["node", str(ROOT / "node_modules/.bin/openspec"), "update", "--keel-invalid-option"],
            cwd=repo, env=env, capture_output=True, text=True, check=False)
        failed = run_keel(repo, "openspec", "update", "--keel-invalid-option", env=env)
        if not failed.returncode or failed.returncode != upstream.returncode or any(p.read_bytes() != b for p, b in files.items()):
            report(f"{label} failed update was masked or changed surfaces")
            return 1
    report("update-restores-overlays scenario passed.")
    return 0


def validate_openspec_skills_only_scenario() -> int:
    """Issue #406: one copy of each OpenSpec workflow, whatever the global delivery.

    OpenSpec reads `delivery` only from the user's global configuration, which
    defaults to `both` and put every workflow on Claude twice — a skill and an
    `/opsx:` command. Keel runs OpenSpec with that configuration's `delivery`
    replaced by `skills`, and never writes the file itself.
    """
    label = "openspec-skills-only:"
    with tempfile.TemporaryDirectory(prefix="keel-406-") as raw_tmp:
        tmp = Path(raw_tmp)
        config = tmp / "xdg/openspec/config.json"
        write_text(config, json.dumps({
            "featureFlags": {}, "profile": "custom", "delivery": "both",
            "workflows": ["propose", "explore", "apply", "sync", "archive"],
        }, indent=2) + "\n")
        before = config.read_bytes()
        env = dict(os.environ)
        env["XDG_CONFIG_HOME"] = str(tmp / "xdg")
        stray = ".claude/commands/opsx/apply.md"
        upstream = "---\nname: OPSX: Apply\n---\n\nImplement tasks.\n"

        def keel(repo: Path, *args: str):
            result = run_keel(repo, *args, env=env)
            if result.returncode != 0:
                report(f"{label} `keel {' '.join(args)}` failed: {(result.stderr or result.stdout).strip()}")
            return result

        claude = tmp / "claude"
        claude.mkdir()
        if keel(claude, "--init", "--target", "claude").returncode != 0:
            return 1
        commands = sorted(p.name for p in (claude / ".claude/commands/opsx").glob("*")) \
            if (claude / ".claude/commands/opsx").is_dir() else []
        if commands:
            report(f"{label} with a global `delivery: both`, keel --init left command files: {commands!r}")
            return 1
        skills = [claude / f".claude/skills/{skill}/SKILL.md" for skill in ("openspec-propose", "openspec-explore", "openspec-apply-change",
                                                               "openspec-sync-specs", "openspec-archive-change")]
        absent = [str(p.relative_to(claude)) for p in skills if not p.is_file()]
        if absent:
            report(f"{label} keel --init did not generate the workflow skills: {absent!r}")
            return 1
        # OpenSpec's own text only: the Keel overlay's wording is
        # guidance-names-openspec-skills's to check.
        naming = [str(p.relative_to(claude)) for p in skills
                  if "/opsx:" in strip_openspec_surface_overlay(p.read_text(encoding="utf-8"))]
        if naming:
            report(f"{label} OpenSpec's generated skill text still names `/opsx:` commands: {naming!r}")
            return 1
        unmarked = [str(p.relative_to(claude)) for p in expected_overlay_surfaces(claude, "claude")
                    if OPENSPEC_SURFACE_OVERLAY_START not in p.read_text(encoding="utf-8")]
        if unmarked:
            report(f"{label} managed skills lack the Keel overlay: {unmarked!r}")
            return 1
        if config.read_bytes() != before:
            report(f"{label} keel --init rewrote the global OpenSpec configuration: {config.read_text()!r}")
            return 1

        doctor = keel(claude, "--doctor", "--target", "claude")
        commands_line = next((l for l in doctor.stdout.splitlines() if l.startswith("OpenSpec commands:")), "")
        overlay_line = next((l for l in doctor.stdout.splitlines() if l.startswith("Keel apply/archive/sync overlay:")), "")
        if not commands_line.startswith("OpenSpec commands: ok"):
            report(f"{label} doctor does not read a skills-only repository's commands as ok: {commands_line!r}")
            return 1
        if "skills only" not in commands_line:
            report(f"{label} doctor's commands line does not say the workflows are skills only: {commands_line!r}")
            return 1
        if not overlay_line.startswith("Keel apply/archive/sync overlay: ok"):
            report(f"{label} doctor does not read the skills-only overlay as ok: {overlay_line!r}")
            return 1
        if "4/4" not in overlay_line:
            report(f"{label} doctor's overlay line does not count 4/4 surfaces: {overlay_line!r}")
            return 1

        write_text(claude / stray, upstream)
        if keel(claude, "--install", "--target", "claude").returncode != 0:
            return 1
        if OPENSPEC_SURFACE_OVERLAY_START not in (claude / stray).read_text(encoding="utf-8"):
            report(f"{label} keel --install did not overlay a command file the repository still holds.")
            return 1
        doctor = keel(claude, "--doctor", "--target", "claude")
        commands_line = next((l for l in doctor.stdout.splitlines() if l.startswith("OpenSpec commands:")), "")
        if not commands_line.startswith("OpenSpec commands: duplicate"):
            report(f"{label} doctor does not read a leftover command file as duplicate: {commands_line!r}")
            return 1
        for needle in ("1 ", ".claude/commands/opsx", "keel --init --target claude"):
            if needle not in posix_paths(commands_line):
                report(f"{label} the duplicate line does not name {needle!r}: {commands_line!r}")
                return 1
        if keel(claude, "--init", "--target", "claude").returncode != 0:
            return 1
        if (claude / stray).exists():
            report(f"{label} keel --init did not remove a command file a `both` delivery left.")
            return 1

        passthrough = tmp / "passthrough"
        passthrough.mkdir()
        if keel(passthrough, "--init", "--target", "claude").returncode != 0:
            return 1
        write_text(passthrough / stray, upstream)
        if keel(passthrough, "openspec", "update", "--force").returncode != 0:
            return 1
        if (passthrough / stray).exists():
            report(f"{label} keel openspec update did not remove a command file a `both` delivery left.")
            return 1

        opencode = tmp / "opencode"
        opencode.mkdir()
        if keel(opencode, "--init", "--target", "opencode").returncode != 0:
            return 1
        left = sorted(p.name for p in (opencode / ".opencode/commands").glob("opsx-*.md")) \
            if (opencode / ".opencode/commands").is_dir() else []
        if left:
            report(f"{label} keel --init --target opencode left command files: {left!r}")
            return 1
        # Any OpenSpec command — doctor runs some — records OpenSpec's own
        # telemetry notice in the file it reads; everything else must stand.
        settled = {k: v for k, v in json.loads(config.read_text()).items() if k != "telemetry"}
        if settled != json.loads(before):
            report(f"{label} a later run changed the global OpenSpec configuration: {config.read_text()!r}")
            return 1
        # Last: OpenSpec itself may record its telemetry notice in the file it reads.
        listed = keel(passthrough, "openspec", "config", "list")
        if "delivery: both" not in listed.stdout:
            report(f"{label} keel openspec config list no longer reports the user's own delivery: {listed.stdout!r}")
            return 1

    if "openspec-skills-only" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("openspec-skills-only scenario passed.")
    return 0


def validate_own_surface_is_skills_only_scenario() -> int:
    """Issue #406: this repository carries the surface Keel now generates.

    Keel's own checkout held `.claude/commands/opsx/*` beside the skills, from
    OpenSpec 1.6 under `delivery: both`.
    """
    label = "own-surface-is-skills-only:"
    commands = ROOT / ".claude/commands/opsx"
    held = sorted(p.name for p in commands.glob("*")) if commands.is_dir() else []
    if held:
        report(f"{label} this repository still holds OpenSpec command files: {held!r}")
        return 1
    naming = [str(p.relative_to(ROOT)) for p in sorted((ROOT / ".claude/skills").glob("openspec-*/SKILL.md"))
              if "/opsx:" in p.read_text(encoding="utf-8")]
    if naming:
        report(f"{label} this repository's Claude skills still name `/opsx:` commands: {naming!r}")
        return 1
    doctor = run_keel(ROOT, "--doctor", "--target", "claude")
    lines = doctor.stdout.splitlines()
    commands_line = next((l for l in lines if l.startswith("OpenSpec commands:")), "")
    overlay_line = next((l for l in lines if l.startswith("Keel apply/archive/sync overlay:")), "")
    if not commands_line.startswith("OpenSpec commands: ok"):
        report(f"{label} doctor here does not read the commands line ok: {commands_line!r}")
        return 1
    if not overlay_line.startswith("Keel apply/archive/sync overlay: ok"):
        report(f"{label} doctor here does not read the overlay line ok: {overlay_line!r}")
        return 1
    if "own-surface-is-skills-only" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("own-surface-is-skills-only scenario passed.")
    return 0


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
            or "Keel apply/archive/sync overlay: ok" not in claude_doctor.stdout
        ):
            report("openspec-surface-overlay scenario Claude doctor missed overlay health.")
            report((claude_doctor.stderr or claude_doctor.stdout).strip())
            return 1

        # Every direction that reports the overlay names the actions it covers,
        # and all of them describe one surface list. They are compared against
        # each other rather than against a literal repeated here: the doctor
        # label is already pinned above, so an action joining the managed set
        # moves all three lines together or fails on this comparison. A third
        # copy of the string is what produced the defect this guards.
        #
        # The refresh line was the copy nobody was watching. Measured 2026-08-03
        # on one repository, back to back: `--init` reported `apply/archive`
        # while `--uninstall` reported `apply/archive/sync` (issue #75).
        #
        # Absence is checked before agreement, and separately, because two
        # labels that were never found also agree.
        claude_uninstall = run_keel(claude_repo, "--uninstall", "--target", "claude")
        if claude_uninstall.returncode != 0:
            report("openspec-surface-overlay scenario Claude uninstall failed:")
            report((claude_uninstall.stderr or claude_uninstall.stdout).strip())
            return 1
        summaries = {
            "refresh": overlay_action_label(
                claude_init.stdout, r"OpenSpec (\S*) overlay refreshed="
            ),
            "doctor": overlay_action_label(
                claude_doctor.stdout, r"Keel (\S*) overlay:"
            ),
            "removal": overlay_action_label(
                claude_uninstall.stdout, r"OpenSpec (\S*) overlay removed="
            ),
        }
        for direction, printed in summaries.items():
            if printed is None:
                report(
                    f"openspec-surface-overlay scenario found no {direction} "
                    "overlay summary at all, so there was no label to compare "
                    "rather than a label that disagreed."
                )
                return 1
            if not printed:
                report(
                    f"openspec-surface-overlay scenario read an empty action "
                    f"label from the {direction} summary; a label that derives "
                    "to nothing reports no actions at all."
                )
                return 1
        for direction in ("refresh", "removal"):
            if summaries[direction] != summaries["doctor"]:
                report(
                    "openspec-surface-overlay scenario overlay summaries "
                    f"disagree: {direction} names {summaries[direction]!r} and "
                    f"doctor names {summaries['doctor']!r}. They describe the "
                    "same managed surface list, so one of them is written "
                    "beside the action set instead of derived from it."
                )
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
            or "Keel apply/archive/sync overlay: ok" not in codex_doctor.stdout
        ):
            report("openspec-surface-overlay scenario Codex doctor missed overlay health.")
            report((codex_doctor.stderr or codex_doctor.stdout).strip())
            return 1

        codex_apply_prompt = codex_repo / ".agents/skills/openspec-apply-change/SKILL.md"
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

        # M6 — a repository set up under OpenSpec 1.6 keeps its layout: skills
        # under `.codex/skills` and commands as CODEX_HOME prompts (#169).
        legacy_repo = tmp / "codex-legacy"
        legacy_home = tmp / "codex-legacy-home"
        legacy_env = os.environ.copy()
        legacy_env["CODEX_HOME"] = str(legacy_home)
        legacy_surfaces = []
        for action, skill in OVERLAY_ACTION_SKILLS.items():
            for surface in (
                legacy_repo / f".codex/skills/{skill}/SKILL.md",
                legacy_home / f"prompts/opsx-{action}.md",
            ):
                write_text(surface, f"---\nname: {skill}\n---\n\n# {action}\n")
                legacy_surfaces.append(surface)
        run_keel(legacy_repo, "--install", "--target", "codex", env=legacy_env)
        lost = [
            str(surface)
            for surface in legacy_surfaces
            if surface.read_text(encoding="utf-8").count(OPENSPEC_SURFACE_OVERLAY_START) != 1
        ]
        if lost:
            report(
                "openspec-surface-overlay scenario 1.6-layout Codex surfaces lost "
                f"their overlay: {lost!r}"
            )
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

        # The skill, since Keel generates no command file (#406).
        opencode_apply_skill = opencode_repo / ".opencode/skills/openspec-apply-change/SKILL.md"
        write_text(
            opencode_apply_skill,
            strip_openspec_surface_overlay(
                opencode_apply_skill.read_text(encoding="utf-8")
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
            or "Keel apply/archive/sync overlay: missing" not in opencode_missing_doctor.stdout
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
            or "Keel apply/archive/sync overlay: missing" not in install_only_doctor.stdout
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


def validate_cli_scenario() -> int:
    help_result = run_keel(ROOT, "--help")
    if help_result.returncode != 0 or "Usage:" not in help_result.stdout:
        report("cli scenario expected keel --help to print usage.")
        report((help_result.stderr or help_result.stdout).strip())
        return 1

    usage_block = help_result.stdout.split("Usage:", 1)[1].split("\n\n", 1)[0]
    triage_lines = [line for line in usage_block.splitlines() if "keel triage" in line]
    if not triage_lines:
        report("cli scenario expected keel --help Usage: block to list a `keel triage` line.")
        report(usage_block.strip())
        return 1
    if "--labels" not in triage_lines[0]:
        report("cli scenario expected the keel --help `keel triage` line to name --labels.")
        report(triage_lines[0].strip())
        return 1
    if "--issue" not in triage_lines[0]:
        report("cli scenario expected the keel --help `keel triage` line to name --issue.")
        report(triage_lines[0].strip())
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


def validate_dry_run_overlay_accounting_scenario() -> int:
    label = "dry-run-overlay-accounting"

    # A dry run is relied on, so it is wrong in both directions: naming a write
    # that will not happen trains the reader to ignore it, and omitting one
    # breaks the promise the dry run exists to make. `--check` used to omit the
    # overlay step entirely while `--install --dry-run` claimed every surface.
    def overlay_lines(text: str) -> list[str]:
        return [line for line in text.splitlines() if "overlay" in line]

    def counts(text: str) -> str | None:
        found = re.search(r"refreshed=(\d+) current=(\d+) missing=(\d+)", text)
        return found.group(0) if found else None

    with tempfile.TemporaryDirectory(prefix="keel-dry-run-overlay-") as raw_tmp:
        repo = Path(raw_tmp) / "repo"
        repo.mkdir()
        # The overlay surfaces are files OpenSpec generates; install merges into
        # them and skips the ones that are absent. Create them so this scenario
        # exercises the classification rather than the missing branch.
        for relative in (
            ".claude/skills/openspec-propose/SKILL.md",
            ".claude/skills/openspec-apply-change/SKILL.md",
            ".claude/skills/openspec-archive-change/SKILL.md",
            ".claude/commands/opsx/propose.md",
            ".claude/commands/opsx/apply.md",
            ".claude/commands/opsx/archive.md",
        ):
            write_text(repo / relative, "# OpenSpec surface\n\nGenerated body.\n")
        if run_keel(repo, "--install", "--target", "claude").returncode != 0:
            report(f"{label} could not install a fixture repository.")
            return 1

        # Nothing stale: neither dry run may name a file.
        check = run_keel(repo, "--check", "--target", "claude")
        if any("would refresh OpenSpec" in line and ".md" in line
               for line in overlay_lines(check.stdout)):
            report(f"{label} named a surface that would not change.")
            report("\n".join(overlay_lines(check.stdout)))
            return 1

        # Make exactly one surface stale and require both dry runs to say so.
        stale = repo / ".claude/skills/openspec-apply-change/SKILL.md"
        if not stale.is_file():
            report(f"{label} fixture has no overlay surface to make stale.")
            return 1
        original = stale.read_text(encoding="utf-8")
        stale.write_text(
            re.sub(r"(keel:openspec-surface-overlay version=)[0-9.]+", r"\g<1>0.0.1",
                   original, count=1),
            encoding="utf-8",
        )

        check = run_keel(repo, "--check", "--target", "claude")
        dry = run_keel(repo, "--install", "--dry-run", "--target", "claude")
        named = [line for line in overlay_lines(check.stdout) if ".md" in line]
        if len(named) != 1 or "openspec-apply-change" not in named[0]:
            report(f"{label} --check did not name exactly the one stale surface.")
            report("\n".join(overlay_lines(check.stdout)) or "(no overlay output)")
            return 1
        if counts(check.stdout) != counts(dry.stdout):
            report(f"{label} the two dry-run entry points disagree.")
            report(f"--check: {counts(check.stdout)}  --install --dry-run: {counts(dry.stdout)}")
            return 1
        if "0.0.1" not in stale.read_text(encoding="utf-8"):
            report(f"{label} a dry run wrote to the surface it was describing.")
            return 1

        # And the real run reports what the dry run promised.
        real = run_keel(repo, "--install", "--target", "claude")
        if counts(real.stdout) != counts(check.stdout):
            report(f"{label} the real run's counts differ from the plan's.")
            report(f"plan: {counts(check.stdout)}  real: {counts(real.stdout)}")
            return 1
        if "0.0.1" in stale.read_text(encoding="utf-8"):
            report(f"{label} the real run did not refresh the stale surface.")
            return 1

    report(f"{label} scenario passed.")
    return 0


def validate_a_declared_dependency_is_resolved_scenario() -> int:
    """Issue #105: the suite looked for its own dependency only on PATH.

    `@fission-ai/openspec` is declared in `package.json` and lands at
    `node_modules/.bin/openspec`. npm scripts see that directory; a Python
    subprocess started by `node scripts/run_python.js` does not. So on a
    checkout that had only run `npm install`, `--all` reported
    `validation --all failed for: compact-task-authoring` while the schema it
    was said to be unable to resolve resolved perfectly.

    The second half is that scenario's own condition: an unresolvable CLI and a
    CLI that ran and refused shared one message, so the reader was sent to a
    subject with nothing wrong with it.
    """
    label = "a-declared-dependency-is-resolved"

    # `no openspec on PATH`, and nothing else removed — by file, not by
    # directory. Removing the directory would also remove `node`, and the
    # openspec shim needs it, so the scenario would be asserting that a shell
    # without an interpreter fails (issue #137).
    with path_without_openspec() as sanitized:
        without = dict(os.environ)
        without["PATH"] = sanitized
        if shutil.which("openspec", path=without["PATH"]) is not None:
            report(
                f"{label}: could not build a PATH without openspec on it, so the "
                "reproduction cannot be set up."
            )
            return 1
        # The scenario's own precondition, asserted before the behavior. A shim
        # with no interpreter exits 127, and calling that a fact about openspec
        # sends the reader to a tool with nothing wrong with it.
        if shutil.which("node", path=without["PATH"]) is None:
            return skip_scenario(
                label,
                "node does not resolve on the PATH this scenario built, so the "
                "openspec shim it resolves would have no interpreter. That is a "
                "broken fixture, not a fact about openspec.",
            )
        resolved = run_openspec(ROOT, "--version", env=without)
        if resolved is None:
            report(
                f"{label}: with no `openspec` on PATH the runner resolved "
                "nothing, but this package declares it as a dependency and "
                "installs it at node_modules/.bin. A tool the repository ships "
                "is not a tool the host has to provide."
            )
            return 1
        if resolved.returncode != 0 or not re.search(
            r"\d+\.\d+\.\d+", resolved.stdout
        ):
            report(
                f"{label}: the resolved openspec did not report a version. "
                f"exit={resolved.returncode} out={(resolved.stdout or '').strip()!r}"
            )
            return 1

    # And it is the declared one, not whatever a host happens to carry.
    declared = ROOT / "node_modules" / ".bin" / "openspec"
    if not declared.exists():
        report(
            f"{label}: {declared} is absent, so this scenario cannot tell a "
            "resolved dependency from a lucky PATH entry. Run `npm install`."
        )
        return 3

    # The two failures carry their own messages. Asserted on the emitted text
    # of the scenario that had them fused, not on the source.
    marker = 'label = "compact-task-authoring"'
    found = validation_source_with(marker)
    if found is None:
        report(f"{label}: compact-task-authoring is gone, so its branch cannot be read.")
        return 1
    _, fused, start = found
    body = fused[start : start + 3000]
    for needle, why in (
        ("could not be found", "the unresolvable branch must say the tool was not found"),
        ("searched", "the unresolvable branch must name where it looked"),
        ("return 3", "an unresolvable tool reports the skip contract, not a failure"),
    ):
        if needle not in body:
            report(f"{label}: {why}; `{needle}` is absent from its branch.")
            return 1
    if re.search(r"if which is None or which\.returncode", body):
        report(
            f"{label}: compact-task-authoring still guards two distinct "
            "failures behind one condition. A tool that was never found and a "
            "tool that ran and refused are different facts, and reporting the "
            "first message when the second happened names the wrong cause."
        )
        return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
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


def validate_doctor_reads_the_diagnosed_repository_scenario() -> int:
    """Issue #57: doctor named one repository and answered about another.

    The OpenSpec declaration was read from `PACKAGE_ROOT/package-lock.json` —
    the directory Keel is installed in — while the line above it says
    `keel doctor for <repo>`. The two coincide only when `node bin/keel.js`
    runs from Keel's own checkout, which is the one arrangement every existing
    scenario uses: `run_keel` always spawns `node <ROOT>/bin/keel.js`, so
    `PACKAGE_ROOT` is Keel's checkout no matter what `cwd` is. Driving the
    diagnosis at a repository that declares its own version is what separates
    the two roots without needing a second installation.
    """
    label = "doctor-reads-the-diagnosed-repository"

    def openspec_line(stdout: str) -> str:
        return next(
            (line for line in stdout.splitlines() if line.startswith("openspec:")),
            "",
        )

    # M1 first half — a repository that declares a version Keel's own tree does
    # not. The sentinel is deliberately one no published OpenSpec reports, so a
    # line carrying it cannot have come from the resolved binary either.
    declared = "0.0.1"
    with tempfile.TemporaryDirectory(prefix="keel-doctor-declares-") as raw:
        declares = Path(raw).resolve()
        write_text(
            declares / "package-lock.json",
            json.dumps(
                {
                    "name": "consumer",
                    "lockfileVersion": 3,
                    "packages": {
                        "node_modules/@fission-ai/openspec": {"version": declared}
                    },
                },
                indent=2,
            )
            + "\n",
        )
        doctor = run_keel(declares, "--doctor")
        line = openspec_line(doctor.stdout or "")
        if not line:
            report(f"{label} M1 `keel --doctor` emitted no openspec line.")
            report((doctor.stdout or doctor.stderr or "").strip())
            return 1
        own_lock = json.loads((ROOT / "npm-shrinkwrap.json").read_text(encoding="utf-8"))
        own_declared = None
        for name, entry in own_lock.get("packages", {}).items():
            if name.endswith("@fission-ai/openspec"):
                own_declared = entry.get("version")
        if not own_declared:
            report(f"{label} could not read Keel's own declared OpenSpec version.")
            return 1
        # The reader sees two versions on this line: the one the resolved binary
        # reports and the one the repository declares. Assert on the declared
        # POSITION, not on bare presence — the resolved binary's version may
        # legitimately equal Keel's own declared version, and a test that reads
        # any occurrence cannot tell the two apart.
        # Two distinct failures, two conditions. A line carrying the right
        # version with no attribution and a line attributing the wrong version
        # need different fixes, and one message covering both would send half
        # its readers to a place with no problem in it.
        if "repo pins" not in line:
            report(
                f"{label} M1 the openspec line does not attribute any declared "
                "version to the repository, so a reader seeing two versions "
                "cannot tell which one is theirs."
            )
            report(f"  {line}")
            return 1
        if f"repo pins {declared}" not in line:
            report(
                f"{label} M1 the openspec line attributes a declared version "
                f"to the repository, but not {declared}, which is what this "
                "repository declares. It is answering about some other "
                "repository."
            )
            report(f"  {line}")
            return 1
        if own_declared != declared and f"repo pins {own_declared}" in line:
            report(
                f"{label} M1 the openspec line reports {own_declared} as the "
                "declared version. That is what is declared where Keel is "
                "installed, not where it was pointed."
            )
            report(f"  {line}")
            return 1
        if not line.startswith("openspec: warning"):
            report(
                f"{label} M1 the resolved binary and the declared version "
                f"disagree ({declared} is declared and no release reports it), "
                "and the line does not state the disagreement."
            )
            report(f"  {line}")
            return 1

    # M1 second half — absence is a statement about the repository, not a read
    # failure, and not a disagreement. Most repositories do not depend on
    # OpenSpec at all, so warning here would train readers to ignore the line.
    with tempfile.TemporaryDirectory(prefix="keel-doctor-silent-") as raw:
        silent = Path(raw).resolve()
        write_text(silent / "README.md", "# consumer\n")
        doctor = run_keel(silent, "--doctor")
        line = openspec_line(doctor.stdout or "")
        if not line:
            report(f"{label} M1 `keel --doctor` emitted no openspec line.")
            report((doctor.stdout or doctor.stderr or "").strip())
            return 1
        if "declares no OpenSpec" not in line:
            report(
                f"{label} M1 a repository declaring no OpenSpec version is not "
                "reported as declaring none."
            )
            report(f"  {line}")
            return 1
        if "unreadable" in line:
            report(
                f"{label} M1 the absence of a declaration is reported as a "
                "failure to read one. The two are different facts and only one "
                "of them is true here."
            )
            report(f"  {line}")
            return 1
        if "answering from a different" in line:
            report(
                f"{label} M1 a repository declaring nothing is reported as "
                "disagreeing with the resolved binary. There is nothing for it "
                "to disagree with."
            )
            report(f"  {line}")
            return 1

    # M4 — two lockfiles, the precedence npm applies. A repository that
    # publishes itself carries `npm-shrinkwrap.json` (npm never publishes
    # `package-lock.json`), and where both exist npm installs from the
    # shrinkwrap, so that is the version the repository actually pins (#164).
    with tempfile.TemporaryDirectory(prefix="keel-doctor-shrinkwrap-") as raw:
        both = Path(raw).resolve()
        for name, version in (
            ("npm-shrinkwrap.json", "0.0.2"),
            ("package-lock.json", "0.0.1"),
        ):
            write_text(
                both / name,
                json.dumps(
                    {
                        "name": "consumer",
                        "lockfileVersion": 3,
                        "packages": {
                            "node_modules/@fission-ai/openspec": {"version": version}
                        },
                    },
                    indent=2,
                )
                + "\n",
            )
        doctor = run_keel(both, "--doctor")
        line = openspec_line(doctor.stdout or "")
        if "repo pins 0.0.2" not in line:
            report(
                f"{label} M4 doctor read package-lock.json over "
                "npm-shrinkwrap.json, while npm installs from the shrinkwrap "
                "when both exist."
            )
            report(f"  {line}")
            return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_context_names_its_keel_scenario() -> int:
    """The version comparison has to survive a runtime too old to contain it.

    Measured 2026-08-02: installed plugin 5.7.1, CLI 5.7.0, repository protocol
    5.14.0, and no session reported anything. The SessionStart version
    comparison shipped in 5.9.0, so the installed plugin does not carry it, and
    its silence is indistinguishable from three versions agreeing — which is
    exactly what 5.9.0 designed silence to mean.

    That is not fixable inside the plugin: an absent mechanism cannot announce
    itself. The repository is the one participant that cannot be stale, because
    the working tree is what every runtime reads. So the version rides on
    `keel context`, which the protocol already requires, and the resident
    protocol asks for it to be reported beside the version the repository
    declares.
    """
    label = "context-names-its-keel"
    version = json.loads(
        (ROOT / "package.json").read_text(encoding="utf-8")
    )["version"]

    with tempfile.TemporaryDirectory(prefix="keel-context-version-") as raw:
        repo = Path(raw).resolve()

        # M1 — every status carries it. A result that omits the version cannot
        # be compared against anything, so an idle or failed answer needs it as
        # much as a selected one does.
        idle = run_keel(repo, "context")
        if version not in idle.stdout:
            report(
                f"{label} M1 an idle `keel context` does not name the Keel "
                f"that produced it: {idle.stdout.strip()!r}"
            )
            return 1

        write_text(repo / "openspec/changes/demo/proposal.md", "# Proposal\n")
        write_text(repo / "openspec/changes/demo/tasks.md", guard_task_fixture())
        selected = run_keel(repo, "context")
        if version not in selected.stdout:
            report(
                f"{label} M1 a selected `keel context` does not name the Keel "
                f"that produced it: {selected.stdout.strip()!r}"
            )
            return 1

        write_text(repo / "openspec/changes/broken/tasks.md", "not a task file\n")
        failing = run_keel(repo, "context")
        if version not in failing.stdout:
            report(
                f"{label} M1 an ambiguous or failing `keel context` does not "
                f"name the Keel that produced it: {failing.stdout.strip()!r}"
            )
            return 1

        payload = run_keel(repo, "context", "--json")
        try:
            parsed = json.loads(payload.stdout)
        except json.JSONDecodeError:
            report(f"{label} M1 `keel context --json` did not emit JSON.")
            return 1
        if parsed.get("keel") != version:
            report(
                f"{label} M1 the JSON projection carries no `keel` version; got "
                f"{parsed.get('keel')!r}, expected {version!r}."
            )
            return 1

    # M2 — the protocol asks for the comparison, and says why it does not
    # depend on the hook. Without the second half a reader who sees the
    # SessionStart line assumes it is covered.
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for needle, why in (
        ("keel context", "the command whose output carries the version"),
        ("protocol version", "the version the repository declares"),
        ("SessionStart", "that the requirement does not depend on the hook"),
    ):
        if needle not in agents:
            report(f"{label} M2 the Session Start protocol does not name {why}.")
            return 1
    session_start = agents.split("## Full/Lite routing", 1)[0]
    if "SessionStart" not in session_start:
        report(
            f"{label} M2 the hook-independence statement is not in the Session "
            "Start section, where an agent deciding what to report reads it."
        )
        return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_interpreter_surfaces_agree_scenario() -> int:
    """`keel --doctor` called an interpreter ok that the runner refuses.

    Measured 2026-08-02: the doctor printed `python3: ok - python3` while
    `run_python.js` on the same machine printed "no Python 3.10 or newer was
    found — tried python3 (3.9.6)". Two Keel surfaces, one question, opposite
    verdicts, and the one a person runs deliberately to check their environment
    was the wrong one. The cause is two implementations: `bin/keel.js` carried
    its own `pythonCandidates` that asked only whether a command runs.

    The same duplication hid a second defect. The candidate list held `python3`
    and `python`, so on macOS — where `python3` is the system 3.9 — the runner
    refused while `python3.11` sat on PATH, telling a reader who had already
    installed one to install one.
    """
    label = "interpreter-surfaces-agree"
    runner = ROOT / "scripts/run_python.js"
    with tempfile.TemporaryDirectory(prefix="keel-interp-agree-") as raw:
        root = Path(raw).resolve()
        script = root / "target.py"
        write_text(script, "import sys\nsys.exit(7)\n")

        def shim(directory: Path, name: str, version: str) -> Path:
            path = directory / name
            write_text(
                path,
                "#!/bin/sh\n"
                f'if [ "$1" = "--version" ]; then echo "Python {version}"; '
                "exit 0; fi\nexit 7\n",
            )
            path.chmod(0o755)
            return path

        # The stub directory shadows every name Keel could look for, so the
        # result does not depend on what happens to be installed on the machine
        # running the suite. Without the versioned shims, a real python3.11 on
        # PATH would satisfy the search that M1 needs to fail.
        def stub_dir(mapping: dict[str, str]) -> Path:
            directory = root / f"bin-{len(list(root.glob('bin-*')))}"
            directory.mkdir()
            for name in ("python", "python3", "python3.10", "python3.11",
                         "python3.12", "python3.13"):
                shim(directory, name, mapping.get(name, "3.9.6"))
            return directory

        def env_with(directory: Path, keel_python: str | None = None):
            env = dict(os.environ)
            env.pop("KEEL_PYTHON", None)
            env["PATH"] = str(directory) + os.pathsep + env.get("PATH", "")
            if keel_python:
                env["KEEL_PYTHON"] = keel_python
            return env

        def run_runner(env) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["node", str(runner), str(script)],
                env=env, text=True, encoding="utf-8",
                errors="replace", capture_output=True, check=False,
            )

        def doctor_python_line(env) -> str:
            result = subprocess.run(
                ["node", str(ROOT / "bin" / "keel.js"), "--doctor"],
                cwd=str(root), env=env, text=True, encoding="utf-8",
                errors="replace", capture_output=True, check=False,
            )
            for line in result.stdout.splitlines():
                if line.startswith("python3:"):
                    return line
            return ""

        # M1 — nothing on PATH reaches the minimum. Both surfaces must say so.
        old_only = stub_dir({})
        old_env = env_with(old_only)
        line = doctor_python_line(old_env)
        if not line:
            report(f"{label} M1 `keel --doctor` printed no python3 line at all.")
            return 1
        if ": ok" in line:
            report(
                f"{label} M1 the doctor called an interpreter ok that the "
                f"runner refuses. Got: {line}"
            )
            return 1
        for needle, why in (("3.9.6", "the version it found"),
                            ("3.10", "the minimum required")):
            if needle not in line:
                report(f"{label} M1 the doctor line does not name {why}: {line}")
                return 1
        refused = run_runner(old_env)
        if refused.returncode == 0:
            report(
                f"{label} M1 the runner accepted an interpreter the doctor "
                "reported as a problem, so the two surfaces disagree."
            )
            return 1

        # M2 — a usable interpreter exists only under a versioned name.
        versioned = stub_dir({"python3.11": "3.11.9"})
        versioned_env = env_with(versioned)
        used = run_runner(versioned_env)
        if used.returncode != 7:
            report(
                f"{label} M2 a usable interpreter was on PATH as python3.11 and "
                f"the runner did not use it; exited {used.returncode} rather "
                "than the script's 7."
            )
            report(f"  {(used.stdout + used.stderr).strip()}")
            return 1
        versioned_line = doctor_python_line(versioned_env)
        if ": ok" not in versioned_line:
            report(
                f"{label} M2 the doctor did not report the versioned "
                f"interpreter as ok. Got: {versioned_line}"
            )
            return 1
        if "3.11.9" not in versioned_line:
            report(
                f"{label} M2 the doctor line names no version for the "
                f"interpreter it resolved. Got: {versioned_line}"
            )
            return 1

        # M3 — the refusal names every candidate with its version, and an
        # explicit interpreter is used without a search.
        combined = f"{refused.stdout}{refused.stderr}"
        for needle in ("python3", "python3.13", "3.9.6"):
            if needle not in combined:
                report(
                    f"{label} M3 the refusal does not name {needle!r} among the "
                    f"candidates it tried: {combined.strip()}"
                )
                return 1
        explicit = shim(root, "explicit-python", "3.12.1")
        chosen = run_runner(env_with(old_only, str(explicit)))
        if chosen.returncode != 7:
            report(
                f"{label} M3 KEEL_PYTHON naming a usable interpreter was not "
                f"used; exited {chosen.returncode} rather than the script's 7."
            )
            return 1

    # M4 — the versioned names are derived from the declared minimum.
    # KEEL_PYTHON is cleared because it short-circuits the search by design, so
    # a probe that inherited it would read an empty list and report the derived
    # names as missing — a true observation about the wrong question.
    probe_env = dict(os.environ)
    probe_env.pop("KEEL_PYTHON", None)
    probe = subprocess.run(
        ["node", "-e",
         "const m = require(process.argv[1]);"
         "process.stdout.write(JSON.stringify({"
         "minimum: m.MINIMUM_PYTHON,"
         "names: m.pythonCandidates().map((c) => c.command)}));",
         str(ROOT / "scripts/run_python.js")],
        env=probe_env,
        text=True, encoding="utf-8", capture_output=True, check=False,
    )
    if probe.returncode != 0:
        report(
            f"{label} M4 scripts/run_python.js does not export its minimum and "
            f"candidate list: {(probe.stdout + probe.stderr).strip()}"
        )
        return 1
    exported = json.loads(probe.stdout)
    minor = exported["minimum"][1]
    versioned_names = [
        name for name in exported["names"] if re.match(r"^python3\.\d+$", name)
    ]
    if not versioned_names:
        report(f"{label} M4 the candidate list holds no versioned names.")
        return 1
    below = [
        name for name in versioned_names
        if int(name.split(".")[1]) < minor
    ]
    if below:
        report(
            f"{label} M4 the candidate list names interpreters below the "
            f"declared minimum 3.{minor}, so the two are written separately "
            f"rather than derived: {below}"
        )
        return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
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
    if "dev-only-plugin-source-scoping" not in {name for name, _ in registry.SCENARIOS}:
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

    # `is_keel_source_repo` reads exactly two signals — the package name and a
    # plugins/keel directory — so a fixture carrying both exercises the same
    # branch. Running this against the real repository used to work and used to
    # rewrite the .claude/ overlay markers as a side effect, which is how the
    # marker check ended up green on that side for the wrong reason.
    if not (ROOT / "AGENTS.md").is_file() or not block(ROOT / "AGENTS.md"):
        report("source-repo-bootstrap-skip: Keel's AGENTS.md has no managed block.")
        return 1

    with tempfile.TemporaryDirectory(prefix="keel-source-repo-") as raw:
        fixture = Path(raw) / "keel"
        write_text(fixture / "package.json", json.dumps({"name": KEEL_PACKAGE_NAME}))
        write_text(fixture / "plugins/keel/.keep", "")
        own_agents = fixture / "AGENTS.md"
        write_text(own_agents, (ROOT / "AGENTS.md").read_text(encoding="utf-8"))
        before_tree = snapshot_files(fixture)
        before = block(own_agents)

        result = run_keel(fixture, "--install", "--target", "claude")
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
        # The original defect was the missing assertion, not only the wrong
        # repository: name what the install must not have rewritten.
        rewritten = [
            name
            for name, text in before_tree.items()
            if (fixture / name).is_file()
            and (fixture / name).read_text(encoding="utf-8") != text
        ]
        if rewritten:
            report(
                "source-repo-bootstrap-skip: keel --install rewrote files it "
                "did not announce: " + ", ".join(sorted(rewritten))
            )
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
    if "source-repo-bootstrap-skip" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "source-repo-bootstrap-skip: the scenario registry does not include it."
        )
        return 1
    report("source-repo-bootstrap-skip scenario passed.")
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
    if "source-repo-cli-resolution" not in {name for name, _ in registry.SCENARIOS}:
        report(
            "source-repo-cli-resolution: the scenario registry does not "
            "include it."
        )
        return 1
    report("source-repo-cli-resolution scenario passed.")
    return 0


def validate_target_capability_adapters_scenario() -> int:
    capability_keys = (
        "continuity.start",
        "continuity.reinject",
        "gate.task-start",
        "gate.task-complete",
        "gate.change-close",
        "execution.worktree",
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
            # runtime evidence.
            native_surface = doctor.stdout
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


# Issue #168: 5.74.0's shrinkwrap pinned OpenSpec 1.6.0 for every install, and
# `keel --init` ran `openspec update --force` over surfaces 1.13.2 had written,
# deleting ~1000 lines in a consumer while doctor said `openspec: ok`.
DOWNGRADE_LABEL = "init-never-downgrades-openspec"


DOWNGRADE_SENTINEL = "keel-downgrade-sentinel: this line exists only in the planted surface"


def _restamp_surfaces(repo: Path, version: str) -> Path:
    """Stamp every OpenSpec skill `generatedBy: version` and plant a sentinel."""
    skills = sorted((repo / ".claude/skills").glob("openspec-*/SKILL.md"))
    for skill in skills:
        text = skill.read_text(encoding="utf-8")
        skill.write_text(
            re.sub(r'generatedBy: "[^"]*"', f'generatedBy: "{version}"', text),
            encoding="utf-8",
        )
    target = repo / ".claude/skills/openspec-propose/SKILL.md"
    head, sep, body = target.read_text(encoding="utf-8").partition("\n---\n")
    target.write_text(head + sep + DOWNGRADE_SENTINEL + "\n" + body, encoding="utf-8")
    return target


def _downgrade_m1(tmp: Path) -> str | None:
    repo = tmp / "newer"
    repo.mkdir()
    run_keel(repo, "--init", "--target", "claude")
    planted = _restamp_surfaces(repo, "99.0.0")
    again = run_keel(repo, "--init", "--target", "claude")
    output = (again.stdout or "") + (again.stderr or "")
    if DOWNGRADE_SENTINEL not in planted.read_text(encoding="utf-8"):
        return (
            "M1 keel --init rewrote OpenSpec surfaces written by a newer OpenSpec "
            "(99.0.0): the planted sentinel is gone."
        )
    if "99.0.0" not in output or "skip" not in output.lower():
        return (
            "M1 keel --init kept the surfaces but did not say it skipped the rewrite "
            f"of OpenSpec surfaces written by a newer OpenSpec: {output[-600:]!r}"
        )
    return None


def _downgrade_m2(tmp: Path) -> str | None:
    repo = tmp / "doctor-newer"
    repo.mkdir()
    run_keel(repo, "--init", "--target", "claude")
    _restamp_surfaces(repo, "99.0.0")
    running = run_keel(repo, "openspec", "--version").stdout.strip()
    doctor = run_keel(repo, "--doctor").stdout or ""
    lines = [l for l in doctor.splitlines() if l.startswith("OpenSpec surfaces:")]
    if len(lines) != 1 or not lines[0].startswith("OpenSpec surfaces: warning"):
        return f"M2 doctor printed no OpenSpec surfaces warning for 99.0.0 surfaces: {lines!r}"
    for needle in ("99.0.0", running, "keel --install --target claude"):
        if needle not in lines[0]:
            return f"M2 doctor printed no OpenSpec surfaces warning carrying {needle!r}: {lines[0]!r}"
    return None


def _downgrade_m3(tmp: Path) -> str | None:
    repo = tmp / "older"
    repo.mkdir()
    run_keel(repo, "--init", "--target", "claude")
    planted = _restamp_surfaces(repo, "1.0.0")
    run_keel(repo, "--init", "--target", "claude")
    if DOWNGRADE_SENTINEL in planted.read_text(encoding="utf-8"):
        return (
            "M3 keel --init skipped the OpenSpec refresh for surfaces older than "
            "the OpenSpec it runs (1.0.0); only newer surfaces are protected."
        )
    return None


def _downgrade_m4(tmp: Path) -> str | None:
    repo = tmp / "git"
    repo.mkdir()
    git = ["git", "-c", "user.name=keel", "-c", "user.email=keel@example.invalid"]
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    run_keel(repo, "--install", "--target", "claude")

    def line() -> str:
        doctor = run_keel(repo, "--doctor", "--target", "claude").stdout or ""
        return next((l for l in doctor.splitlines() if l.startswith("plugin auto-update:")), "")

    untracked = line()
    if not untracked.startswith("plugin auto-update: warning") or "git add .claude/settings.json" not in untracked:
        return f"M4 doctor did not say .claude/settings.json is untracked: {untracked!r}"
    subprocess.run([*git, "add", ".claude/settings.json"], cwd=repo, check=True)
    subprocess.run([*git, "commit", "-q", "-m", "declare"], cwd=repo, check=True)
    tracked = line()
    if not tracked.startswith("plugin auto-update: ok"):
        return f"M4 doctor did not say .claude/settings.json is untracked only while it was: {tracked!r}"
    return None


def validate_init_never_downgrades_openspec_scenario() -> int:
    with tempfile.TemporaryDirectory(
        prefix="keel-downgrade-", ignore_cleanup_errors=True
    ) as raw:
        tmp = Path(raw)
        for check in (_downgrade_m1, _downgrade_m2, _downgrade_m3, _downgrade_m4):
            problem = check(tmp)
            if problem:
                report(f"{DOWNGRADE_LABEL} {problem}")
                return 1
    report(f"{DOWNGRADE_LABEL} scenario passed.")
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
        if block_bytes >= BOOTSTRAP_BLOCK_BYTE_BUDGET:
            report(
                "thin-native-install bootstrap block is over its "
                f"{BOOTSTRAP_BLOCK_BYTE_BUDGET}-byte budget: {block_bytes} bytes"
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
                "the lens whose `Applies when:` header matches",
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

    readme = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8") + (ROOT / "README.md").read_text(encoding="utf-8")
    if "Execution and review checks" not in readme:
        report(
            "domain-execution-references: README does not describe the "
            "execution/review phase coverage."
        )
        return 1
    if "domain-execution-references" not in {name for name, _ in registry.SCENARIOS}:
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


# The one ordered scenario registry: --scenario dispatch, the --all runner,
# and registration assertions all read this list and nothing else.

# 170 scenarios and every release gate ran green while `keel openspec` did not
# resolve on a plain `npm install` (issue #129). The cause is a layout, not a
# behavior: npm hoists, so the OpenSpec bin lands in the consumer project's
# `node_modules/.bin` while the lookup only searched Keel's own package root —
# which is where it sits in a checkout of this repository, and nowhere else.
# So the assertion has to build the other layout rather than test harder in this
# one. Built from the package's own files instead of the registry: what is under
# test is where a file sits, and a suite that reaches the network fails for
# reasons that have nothing to do with this code.
def validate_dependency_resolves_where_npm_put_it_scenario() -> int:
    label = "the-dependency-resolves-where-npm-put-it"

    def write_openspec_stub(bin_dir: Path, version: str) -> None:
        bin_dir.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            (bin_dir / "openspec.cmd").write_text(
                f"@echo off\necho {version}\n", encoding="utf-8"
            )
            return
        stub = bin_dir / "openspec"
        stub.write_text(f"#!/bin/sh\necho {version}\n", encoding="utf-8")
        stub.chmod(0o755)

    def install_keel(package_root: Path) -> None:
        # The published `files` set, copied rather than packed: the tarball's
        # contents are what npm unpacks, and `npm pack` would add a network-free
        # but slow round trip through tar for no additional assertion.
        package_root.mkdir(parents=True, exist_ok=True)
        for entry in ("bin", "scripts", "src", "assets", "plugins"):
            source = ROOT / entry
            if source.exists():
                shutil.copytree(source, package_root / entry, dirs_exist_ok=True)
        shutil.copy2(ROOT / "package.json", package_root / "package.json")

    # PATH without any openspec, so what resolves came from the layout and not
    # from the machine running the suite. Removed by file rather than by
    # directory: one directory holds `openspec` and `node` on the ordinary
    # Homebrew plus `npm install -g` layout, and the children below are run by
    # `node` (issue #137).
    def clean_env(extra_path: Path | None = None) -> dict[str, str]:
        env = dict(os.environ)
        entries = [entry for entry in sanitized_path.split(os.pathsep) if entry]
        if extra_path is not None:
            entries.insert(0, str(extra_path))
        env["PATH"] = os.pathsep.join(entries)
        return env

    def run_installed(
        package_root: Path, cwd: Path, *args: str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["node", str(package_root / "bin" / "keel.js"), *args],
            cwd=cwd,
            env=env if env is not None else clean_env(),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )

    def doctor_openspec_line(result: subprocess.CompletedProcess[str]) -> str:
        return next(
            (
                line
                for line in result.stdout.splitlines()
                if line.startswith("openspec:")
            ),
            "",
        )

    # The mirrors live for the duration of the context, so it stays open across
    # every child process below rather than only across the call that built it.
    with path_without_openspec() as sanitized_path, tempfile.TemporaryDirectory(
        prefix="keel-hoisted-"
    ) as raw:
        # The scenario's own precondition, asserted before the behavior: every
        # assertion below runs `node`, so a PATH without one is a broken fixture
        # and not a fact about where the dependency resolves.
        if shutil.which("node", path=sanitized_path) is None:
            return skip_scenario(
                label,
                "node does not resolve on the PATH this scenario built, and "
                "every assertion below runs the installed Keel through it. That "
                "is a broken fixture, not a fact about openspec.",
            )
        root = Path(raw)

        # The layout npm actually produces: Keel unpacked under the consumer's
        # node_modules with no node_modules of its own, the dependency's bin
        # hoisted beside it.
        project = root / "project"
        package_root = project / "node_modules/@christang/keel"
        install_keel(package_root)
        write_openspec_stub(project / "node_modules/.bin", "1.12.0")
        if (package_root / "node_modules").exists():
            report(
                f"{label}: the fixture gave Keel a node_modules of its own, "
                "which is the one layout the defect does not appear in."
            )
            return 1

        proxied = run_installed(package_root, project, "openspec", "--version")
        if proxied.returncode != 0:
            report(
                f"{label}: `keel openspec` failed against the hoisted "
                f"dependency; exit {proxied.returncode}, stderr "
                f"{proxied.stderr.strip()!r}."
            )
            return 1
        if "1.12.0" not in proxied.stdout:
            report(
                f"{label}: `keel openspec` exited 0 without running the "
                f"hoisted dependency; stdout {proxied.stdout.strip()!r}."
            )
            return 1

        hoisted_doctor = doctor_openspec_line(
            run_installed(package_root, project, "--doctor")
        )
        if hoisted_doctor.startswith("openspec: missing"):
            report(
                f"{label}: doctor reported an installed dependency as missing; "
                f"got {hoisted_doctor!r}."
            )
            return 1

        # Nearest wins, so a project pinning its own OpenSpec is honored over
        # one further up the tree.
        nested = root / "outer/project"
        nested_package = nested / "node_modules/@christang/keel"
        install_keel(nested_package)
        write_openspec_stub(root / "outer/node_modules/.bin", "9.9.9")
        write_openspec_stub(nested / "node_modules/.bin", "1.12.0")
        nearest = run_installed(nested_package, nested, "openspec", "--version")
        if "1.12.0" not in nearest.stdout:
            report(
                f"{label}: the farther OpenSpec won over the nearer one; got "
                f"{nearest.stdout.strip()!r}."
            )
            return 1

        # The one case where advising a reinstall is correct.
        bare = root / "bare"
        bare_package = bare / "node_modules/@christang/keel"
        install_keel(bare_package)
        absent = doctor_openspec_line(
            run_installed(bare_package, bare, "--doctor")
        )
        if not absent.startswith("openspec: missing"):
            report(
                f"{label}: doctor did not report a genuinely absent dependency "
                f"as missing; got {absent!r}."
            )
            return 1
        if "reinstall" not in absent:
            report(
                f"{label}: doctor stopped advising a reinstall in the one case "
                f"where it is the right advice; got {absent!r}."
            )
            return 1

        # Installed and unreachable: the package is where npm puts it, its bin
        # entry is not. Sending this reader to reinstall is what issue #129
        # measured, and it is the one action that cannot help.
        broken = root / "broken"
        broken_package = broken / "node_modules/@christang/keel"
        install_keel(broken_package)
        write_text(
            broken / "node_modules/@fission-ai/openspec/package.json",
            '{"name": "@fission-ai/openspec", "version": "1.12.0"}\n',
        )
        unreachable = doctor_openspec_line(
            run_installed(broken_package, broken, "--doctor")
        )
        if "reinstall" in unreachable and "will not change this" not in unreachable:
            report(
                f"{label}: doctor advised reinstalling for a dependency that "
                f"is already installed; got {unreachable!r}."
            )
            return 1
        if "installed" not in unreachable:
            report(
                f"{label}: doctor did not distinguish an installed but "
                f"unreachable dependency from an absent one; got "
                f"{unreachable!r}."
            )
            return 1

    report(f"{label} scenario passed.")
    return 0


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


# The marker's `version=` attribute is written by the installer and, before this
# scenario, read back by nothing that runs locally: both marker parsers match
# `keel:start(?:\s+[^>]*)?` and discard the attributes. The only reader was the
# plugin's SessionStart hook, whose activation doctor itself reports as manual.
def validate_marker_version_is_read_scenario() -> int:
    def doctor_protocol_line(repo: Path) -> tuple[str, int]:
        result = run_keel(repo, "--doctor")
        line = next(
            (
                entry
                for entry in result.stdout.splitlines()
                if entry.startswith("protocol:")
            ),
            "",
        )
        return line, result.returncode

    def write_repo(root: Path, name: str, marker: str | None) -> Path:
        repo = root / name
        repo.mkdir()
        body = "# Agents\n\nSession Start.\n"
        (repo / "AGENTS.md").write_text(
            f"{marker}\n{body}" if marker is not None else body,
            encoding="utf-8",
        )
        return repo

    with tempfile.TemporaryDirectory(prefix="keel-marker-version-") as raw:
        root = Path(raw)

        behind = write_repo(root, "behind", "<!-- keel:start version=5.14.0 -->")
        line, behind_code = doctor_protocol_line(behind)
        if not line.startswith("protocol: warning"):
            report(
                "the-marker-version-is-read scenario: a repository declaring an "
                f"older protocol did not warn; got {line!r}."
            )
            return 1
        # #168: `keel --init` also runs OpenSpec's `--force` rewrite, which is
        # what downgraded a consumer's surfaces. The protocol refresh is install.
        if "keel --init" in line:
            report(
                "the-marker-version-is-read scenario: a repository behind its "
                f"install was told to run keel --init; got {line!r}."
            )
            return 1
        for needed in ("5.14.0", PACKAGE_VERSION, "keel --install"):
            if needed not in line:
                report(
                    "the-marker-version-is-read scenario: the behind-repository "
                    f"warning omits {needed!r}; got {line!r}."
                )
                return 1
        if "repository" not in line:
            report(
                "the-marker-version-is-read scenario: the warning does not name "
                f"the repository as the term that is behind; got {line!r}."
            )
            return 1

        ahead = write_repo(root, "ahead", "<!-- keel:start version=9.99.0 -->")
        line, _ = doctor_protocol_line(ahead)
        if not line.startswith("protocol: warning"):
            report(
                "the-marker-version-is-read scenario: a repository declaring a "
                f"newer protocol did not warn; got {line!r}."
            )
            return 1
        for needed in ("9.99.0", PACKAGE_VERSION, "install"):
            if needed not in line:
                report(
                    "the-marker-version-is-read scenario: the ahead-repository "
                    f"warning omits {needed!r}; got {line!r}."
                )
                return 1
        if "keel --init" in line:
            report(
                "the-marker-version-is-read scenario: a repository ahead of its "
                f"install was told to re-run keel --init; got {line!r}."
            )
            return 1

        agreed = write_repo(
            root, "agreed", f"<!-- keel:start version={PACKAGE_VERSION} -->"
        )
        line, agreed_code = doctor_protocol_line(agreed)
        if not line.startswith("protocol: ok"):
            report(
                "the-marker-version-is-read scenario: agreeing versions did not "
                f"report ok; got {line!r}."
            )
            return 1
        if line.count(PACKAGE_VERSION) < 2:
            report(
                "the-marker-version-is-read scenario: the agreeing line does not "
                f"print both versions; got {line!r}."
            )
            return 1

        # D2: drift is a warning and nothing else. A line that could turn a
        # pipeline red on release day is a line users switch off.
        if behind_code != agreed_code:
            report(
                "the-marker-version-is-read scenario: drift changed doctor's "
                f"exit code ({behind_code} vs {agreed_code})."
            )
            return 1

        for name, marker in (
            ("undeclared", None),
            ("attributeless", "<!-- keel:start -->"),
        ):
            repo = write_repo(root, name, marker)
            line, _ = doctor_protocol_line(repo)
            if not line.startswith("protocol: not comparable"):
                report(
                    f"the-marker-version-is-read scenario: the {name} repository "
                    f"did not report `not comparable`; got {line!r}."
                )
                return 1
            if "declares" not in line:
                report(
                    f"the-marker-version-is-read scenario: the {name} repository "
                    f"was not told which term is missing; got {line!r}."
                )
                return 1

    report("the-marker-version-is-read scenario passed.")
    return 0


# `keel --init` writes OpenSpec's command and skill surfaces, whose text says
# `openspec new change "<name>"`. With only the Keel package installed globally
# a bare `openspec` is not on PATH, which `keel --doctor` reports and names the
# working invocation for. Those files belong to OpenSpec and Keel appends a
# block rather than editing their body — so the block is where Keel says it.
def validate_overlay_names_the_invocation_scenario() -> int:
    label = "the-overlay-names-the-invocation"
    start = "<!-- keel:openspec-surface-overlay"
    end = "<!-- keel:openspec-surface-overlay:end -->"
    with tempfile.TemporaryDirectory(prefix="keel-overlay-invocation-") as raw:
        repo = Path(raw)
        # The surfaces OpenSpec writes, as OpenSpec writes them: the overlay is
        # merged into files that already exist, and their body is the text this
        # scenario asserts Keel does not touch.
        upstream = 'Run `openspec new change "<name>"` to begin.\n'
        for action in ("propose", "apply", "sync", "archive"):
            write_text(repo / f".claude/commands/opsx/{action}.md", upstream)
        for skill in (
            "openspec-propose",
            "openspec-apply-change",
            "openspec-sync-specs",
            "openspec-archive-change",
        ):
            write_text(repo / f".claude/skills/{skill}/SKILL.md", upstream)
        installed = run_keel(repo, "--install", "--target", "claude")
        if installed.returncode != 0:
            report(
                f"{label}: the fixture install failed; "
                f"{(installed.stderr or installed.stdout).strip()[:300]}"
            )
            return 1

        carrying = [
            path
            for path in sorted(repo.rglob("*.md"))
            if start in path.read_text(encoding="utf-8", errors="replace")
        ]
        if not carrying:
            report(f"{label}: the install wrote no file carrying an overlay.")
            return 1
        for path in carrying:
            content = path.read_text(encoding="utf-8")
            block = content[content.index(start):content.index(end) + len(end)]
            for needed in ("keel openspec", "keel --doctor"):
                if needed not in block:
                    report(
                        f"{label}: the overlay in {path.name} does not name "
                        f"{needed!r}."
                    )
                    return 1
            # The boundary: everything outside the block is OpenSpec's.
            outside = (
                content[: content.index(start)]
                + content[content.index(end) + len(end):]
            )
            if start in outside or "keel openspec" in outside:
                report(
                    f"{label}: {path.name} carries Keel invocation text outside "
                    "the overlay block, so the OpenSpec-authored body was "
                    "edited."
                )
                return 1

    report(f"{label} scenario passed.")
    return 0

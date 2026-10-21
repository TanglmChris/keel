"""Keel validation: hosts (split from validate_plugin.py, #409)."""
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
    HANDOFF_STUB,
    OPENSPEC_CONFIG_PATH,
    OPENSPEC_SURFACE_OVERLAY_START,
    PACKAGE_VERSION,
    PLUGIN_ROOT,
    PROTOCOL_VERSION,
    ROOT,
    packaged_openspec_schema_install_paths,
    plant_handoff_package,
    report,
    resident_session_start_section,
    run_hook_script,
    run_keel,
    run_session_start_hook,
    session_start_context,
    skip_scenario,
    snapshot_files,
    stub_output,
    task_contract_fixture,
    write_install_record,
    write_text,
)
from validation import registry


# `bump_version.js` writes a stub section for the new release, and the convention
# is to fill it in. Writing the entry *above* it instead leaves an orphan, and
# the stub carries the `Version alignment:` line this scenario reads — so the
# section describing nothing was the section that passed (#151). It happened in
# 5.67.0 and 5.68.0, with the suite green both times.
#
# Takes the text rather than reading the file, so the rule can be exercised on a
# planted copy: a rule that could only ever see the changelog already known to be
# correct would pass forever without anyone learning whether it fires.
def release_description_problem(changelog: str, version: str) -> str | None:
    """Return the problem the released version's section has, or None.

    Scoped to the version being released. An older section is history a current
    author cannot act on, and a rule that swept the whole file would fail on the
    archive — which is how a check gets disabled rather than fixed. The file also
    legitimately quotes `TODO` when describing the rules that refuse it.
    """
    pattern = re.compile(
        r"^## " + re.escape(version) + r"\b[^\n]*$", re.M
    )
    headings = pattern.findall(changelog)
    if not headings:
        return (
            f"the changelog carries no `## {version}` section, so the release "
            "describes nothing at all."
        )
    if len(headings) > 1:
        return (
            f"the changelog describes {version} twice — {len(headings)} `## "
            f"{version}` headings: {', '.join(h.strip() for h in headings)}. A "
            "release entry written above the stub instead of into it leaves both."
        )
    for heading in headings:
        if "TODO" in heading:
            return (
                f"the changelog still carries the stub heading `{heading.strip()}`"
                f", so the {version} release was never described. Fill that "
                "section in rather than writing the entry above it."
            )
    # The section body, bounded by the next `## ` heading, so a `TODO` belonging
    # to an older release is not read as this one's.
    start = changelog.index(headings[0])
    rest = changelog[start + len(headings[0]):]
    end = rest.find("\n## ")
    body = rest if end < 0 else rest[:end]
    for line in body.splitlines():
        if re.match(r"^\s*-\s*TODO\b", line):
            return (
                f"the {version} section still carries the stub bullet "
                f"`{line.strip().lstrip('- ')}`, so the release is titled but "
                "not described."
            )
    return None


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

    # M5 — on Claude the plugin is the npm package: the root manifest carries
    # the version, and the marketplace entry names it and the package version
    # it installs, so all three are version markers, and the script that moves
    # every marker has to move them (#337).
    def claude_entry_versions(root: Path) -> dict:
        market = json.loads(
            (root / ".claude-plugin/marketplace.json").read_text(encoding="utf-8")
        )
        entry = next(
            (e for e in market.get("plugins", []) if e.get("name") == "keel"), {}
        )
        source = entry.get("source") if isinstance(entry.get("source"), dict) else {}
        return {
            "version": entry.get("version"),
            "source.version": source.get("version"),
        }

    def root_manifest_version(root: Path) -> str | None:
        manifest = root / ".claude-plugin/plugin.json"
        if not manifest.is_file():
            return None
        return json.loads(manifest.read_text(encoding="utf-8")).get("version")

    stale = {
        k: v for k, v in claude_entry_versions(ROOT).items() if v != PACKAGE_VERSION
    }
    if root_manifest_version(ROOT) != PACKAGE_VERSION:
        stale["root plugin manifest"] = root_manifest_version(ROOT)
    if stale:
        report(
            "version-alignment scenario claude marketplace entry version "
            f"expected {PACKAGE_VERSION}: {stale!r}"
        )
        return 1
    with tempfile.TemporaryDirectory(prefix="keel-bump-") as raw:
        scratch = Path(raw)
        for relative in (
            "package.json",
            "npm-shrinkwrap.json",
            ".claude-plugin/marketplace.json",
            ".claude-plugin/plugin.json",
            "plugins/keel/.claude-plugin/plugin.json",
            "plugins/keel/.codex-plugin/plugin.json",
            "scripts/bump_version.js",
            "scripts/validation/common.py",
            "AGENTS.md",
            "keel/CHANGELOG.md",
        ):
            (scratch / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, scratch / relative)
        bumped = subprocess.run(
            ["node", str(scratch / "scripts/bump_version.js"), "99.0.0"],
            cwd=scratch,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        if bumped.returncode != 0:
            report("version-alignment scenario: bump_version.js failed in a scratch copy.")
            report((bumped.stderr or bumped.stdout).strip())
            return 1
        if root_manifest_version(scratch) != "99.0.0":
            report(
                "version-alignment scenario root plugin manifest was not moved "
                f"by bump_version.js: {root_manifest_version(scratch)!r}"
            )
            return 1
        left = {
            k: v
            for k, v in claude_entry_versions(scratch).items()
            if v != "99.0.0"
        }
        if left:
            report(
                "version-alignment scenario claude marketplace entry version "
                f"was not moved by bump_version.js: {left!r}"
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

    # Presence is not alignment. A changelog announcing a release nothing else
    # claims satisfies every check above, because the *previous* version is
    # still somewhere in the file — which is exactly how 5.8.0 was written with
    # every manifest left at 5.7.1. The newest entry is the claim that matters.
    changelog = (ROOT / "keel/CHANGELOG.md").read_text(encoding="utf-8")
    headings = re.findall(r"^## (\d+\.\d+\.\d+)\b", changelog, re.M)
    if not headings:
        report("version-alignment scenario found no versioned changelog entry.")
        return 1
    if headings[0] != PACKAGE_VERSION:
        report(
            f"version-alignment scenario changelog announces {headings[0]} while "
            f"the package declares {PACKAGE_VERSION}; the newest entry is a "
            "release claim and must name the version everything else ships."
        )
        return 1

    # The released version's section has to say what the release did. Asserted on
    # planted copies first, so the rule is known to fire, and then on the
    # repository's own changelog.
    stub = (
        f"# Keel Changelog\n\n## {PACKAGE_VERSION} - TODO: summarize this "
        f"release\n\n- TODO: describe the change.\n- Version alignment: "
        f"shares Keel {PACKAGE_VERSION}.\n\n## 5.0.0 - older\n\n- Done.\n"
    )
    planted = release_description_problem(stub, PACKAGE_VERSION)
    if not planted:
        report(
            "version-alignment scenario: an unfilled stub was accepted — a "
            f"changelog whose {PACKAGE_VERSION} section is the stub "
            "`bump_version.js` writes produced no problem, so a release can "
            "ship describing nothing while this scenario passes."
        )
        return 1
    if "TODO: summarize this release" not in planted:
        report(
            "version-alignment scenario: the refusal does not name the offending "
            f"line, so an author is sent to read the whole changelog; got "
            f"{planted!r}."
        )
        return 1

    # Still M1 — the stub survives renaming its heading. The bullet is the other
    # half of what `bump_version.js` writes, and a section titled correctly while
    # its only content is `- TODO: describe the change.` describes nothing.
    renamed = (
        f"# Keel Changelog\n\n## {PACKAGE_VERSION} - a real sounding title\n\n"
        f"- TODO: describe the change.\n- Version alignment: shares Keel "
        f"{PACKAGE_VERSION}.\n"
    )
    bullet = release_description_problem(renamed, PACKAGE_VERSION)
    if not bullet:
        report(
            "version-alignment scenario: an unfilled stub was accepted — a "
            "section with a real heading whose content is still `- TODO: describe "
            "the change.` produced no problem, so renaming the stub is enough to "
            "ship an undescribed release."
        )
        return 1
    if "TODO: describe the change." not in bullet:
        report(
            "version-alignment scenario: the bullet refusal does not name the "
            f"line it found; got {bullet!r}."
        )
        return 1

    # M2 — two sections for one version. This is the shape the real defect had,
    # and neither TODO rule catches it once the stub's heading has been renamed:
    # the reader then sees two identical version headings, one of which describes
    # nothing.
    doubled = (
        f"# Keel Changelog\n\n## {PACKAGE_VERSION} - the real entry\n\n"
        f"- Did the thing.\n- Version alignment: shares Keel {PACKAGE_VERSION}."
        f"\n\n## {PACKAGE_VERSION} - summarized\n\n- Also this.\n"
    )
    problem_found = release_description_problem(doubled, PACKAGE_VERSION)
    if not problem_found:
        report(
            "version-alignment scenario: a version described twice was accepted "
            f"— two `## {PACKAGE_VERSION}` sections produced no problem, which is "
            "the shape the defect this rule exists for actually had."
        )
        return 1
    if "twice" not in problem_found:
        report(
            "version-alignment scenario: the duplicate-section refusal does not "
            f"say the version is described twice; got {problem_found!r}."
        )
        return 1

    # M3 — only the version being released is judged. An older section is history,
    # and this file legitimately quotes `TODO` when describing the rules that
    # refuse it, so a rule sweeping the whole file would fire on its own
    # documentation.
    older = (
        f"# Keel Changelog\n\n## {PACKAGE_VERSION} - the real entry\n\n"
        f"- Did the thing.\n- Version alignment: shares Keel {PACKAGE_VERSION}."
        "\n\n## 5.0.0 - TODO: summarize this release\n\n- TODO: describe it.\n"
    )
    if release_description_problem(older, PACKAGE_VERSION):
        report(
            "version-alignment scenario: an older section was refused — a `TODO` "
            "in a section for another version failed the current release, which "
            "is a check the archive can only be edited to satisfy."
        )
        return 1
    if release_description_problem(changelog, PACKAGE_VERSION):
        report(
            "version-alignment scenario: an older section was refused — the "
            "repository's own changelog does not satisfy the rule: "
            f"{release_description_problem(changelog, PACKAGE_VERSION)}"
        )
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


def validate_the_tarball_is_the_repository_scenario() -> int:
    """Issue #110: what ships depended on the packer's working tree.

    `files` names `scripts/`, and declaring a `files` array means `.gitignore`
    stops filtering inside it — while `__pycache__` is not on npm's default
    exclusion list. Packing one commit twice: 41 files on a clean checkout, 43
    after anyone has run the Python in `scripts/`.

    The assertion is that every packed file is tracked by Git. That states the
    requirement directly and cannot be satisfied by a machine's leftovers; a
    recomputed list of expected files would have to reimplement npm's inclusion
    rules and would drift from them.
    """
    label = "the-tarball-is-the-repository"

    npm = shutil.which("npm")
    if npm is None:
        report(f"{label} skipped: npm is not on PATH, and it is what packs.")
        return 3

    # Reproduce the state the issue reports before asserting anything, so the
    # check runs against a tree that has the residue rather than one that
    # happens not to.
    residue = ROOT / "scripts" / "__pycache__" / "keel-pack-probe.pyc"
    created_dir = not residue.parent.exists()
    residue.parent.mkdir(parents=True, exist_ok=True)
    residue.write_bytes(b"probe\n")
    try:
        packed = subprocess.run(
            [npm, "pack", "--dry-run", "--json"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        if packed.returncode != 0:
            report(f"{label}: npm pack --dry-run failed.")
            report((packed.stderr or packed.stdout).strip())
            return 1
        try:
            files = [item["path"] for item in json.loads(packed.stdout)[0]["files"]]
        except (ValueError, KeyError, IndexError):
            report(f"{label}: could not read the file list from npm pack --json.")
            report((packed.stdout or "").strip()[:400])
            return 1

        tracked = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        if tracked.returncode != 0:
            report(f"{label}: git ls-files failed, so tracked state is unknown.")
            return 1
        known = {
            name for name in tracked.stdout.decode("utf-8").split("\0") if name
        }

        untracked = sorted(path for path in files if path not in known)
        if untracked:
            report(
                f"{label}: {len(untracked)} packed file(s) are not tracked by "
                "Git, so what ships depends on the machine that packs it "
                "rather than on the repository:"
            )
            for path in untracked:
                report(f"  {path}")
            return 1
        if not files:
            report(f"{label}: npm pack reported no files, so nothing was checked.")
            return 1
    finally:
        residue.unlink(missing_ok=True)
        if created_dir:
            try:
                residue.parent.rmdir()
            except OSError:
                pass

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed: {len(files)} packed files, all tracked.")
    return 0


def validate_runtime_versions_are_checked_scenario() -> int:
    """Issue #36: the suite ran on whatever interpreter and OpenSpec answered.

    `run_python.js` accepted any candidate whose `--version` exited zero, so
    macOS system Python 3.9 ran a suite needing 3.10 and failed ten scenarios
    with messages naming ten unrelated features. `findOpenSpecCommand` prefers
    `node_modules/.bin/openspec` and otherwise falls back to PATH in silence,
    so this repository validated changes against openspec 1.4.1 while its
    lockfile resolves 1.6.0 — which is the whole of why `spec-template-
    validates` was green in CI and red in the worktree.
    """
    label = "runtime-versions-are-checked"
    runner = ROOT / "scripts/run_python.js"
    with tempfile.TemporaryDirectory(prefix="keel-runtime-versions-") as raw:
        root = Path(raw).resolve()
        script = root / "target.py"
        write_text(script, "import sys\nsys.exit(7)\n")

        def fake_python(name: str, version: str) -> Path:
            path = root / name
            write_text(
                path,
                "#!/bin/sh\n"
                f'if [ "$1" = "--version" ]; then echo "Python {version}"; '
                "exit 0; fi\nexit 7\n",
            )
            path.chmod(0o755)
            return path

        def run_runner(python: Path) -> subprocess.CompletedProcess[str]:
            env = dict(os.environ)
            env["KEEL_PYTHON"] = str(python)
            return subprocess.run(
                ["node", str(runner), str(script)],
                env=env, text=True, encoding="utf-8",
                errors="replace", capture_output=True, check=False,
            )

        # M1 — an interpreter below the minimum is refused by version, and the
        # refusal names it. The fake exits 7 for anything but `--version`, so a
        # runner that handed the script over anyway would exit 7, not non-zero
        # for the right reason — the message is what separates the two.
        old = fake_python("old-python", "3.9.6")
        result = run_runner(old)
        if result.returncode == 0:
            report(
                f"{label} M1 the runner accepted an interpreter reporting 3.9.6 "
                "and ran the suite on it."
            )
            return 1
        combined = f"{result.stdout}{result.stderr}"
        for needle, why in (
            ("3.9.6", "the version the interpreter reported"),
            ("old-python", "which interpreter it tried"),
            ("3.10", "the minimum the suite needs"),
        ):
            if needle not in combined:
                report(f"{label} M1 the refusal does not name {why}.")
                report(f"  {combined.strip()}")
                return 1
        if result.returncode == 7:
            report(
                f"{label} M1 the runner exited with the script's own status, so "
                "it ran the script rather than refusing the interpreter."
            )
            return 1

        # M2 — and an interpreter at the minimum is still used, with the
        # script's exit status passed through untouched.
        new = fake_python("new-python", "3.10.0")
        passed = run_runner(new)
        if passed.returncode != 7:
            report(
                f"{label} M2 an interpreter reporting 3.10.0 did not run the "
                f"script and pass its exit status through; got "
                f"{passed.returncode} rather than the script's 7."
            )
            report(f"  {(passed.stdout + passed.stderr).strip()}")
            return 1

    # M3/M4/M5 — the OpenSpec binary that actually answers, against the one the
    # lockfile resolves. Read from this repository, because the fact under test
    # is which program a developer's `keel` invokes here.
    locked = None
    lock = json.loads((ROOT / "npm-shrinkwrap.json").read_text(encoding="utf-8"))
    for name, entry in lock.get("packages", {}).items():
        if name.endswith("@fission-ai/openspec"):
            locked = entry.get("version")
    if not locked:
        report(f"{label} could not read the locked OpenSpec version.")
        return 1
    doctor = run_keel(ROOT, "--doctor")
    lines = [line for line in doctor.stdout.splitlines() if line.startswith("openspec:")]
    if len(lines) != 1:
        report(f"{label} M3 `keel doctor` did not emit exactly one openspec line.")
        return 1
    line = lines[0]
    if locked not in line:
        report(
            f"{label} M3 the openspec doctor line does not name the locked "
            f"version {locked}, so a reader cannot tell which program answered."
        )
        report(f"  {line}")
        return 1
    resolved = re.search(r"\b(\d+\.\d+\.\d+)\b", line)
    if not resolved:
        report(f"{label} M3 the openspec doctor line reports no resolved version.")
        report(f"  {line}")
        return 1
    if resolved.group(1) != locked and "warning" not in line:
        report(
            f"{label} M3 the resolved OpenSpec is {resolved.group(1)} and the "
            f"lockfile resolves {locked}, but the doctor line does not state "
            "the disagreement."
        )
        report(f"  {line}")
        return 1
    for banned in ("npm install", "npm ci", "keel --update"):
        if banned in line:
            report(
                f"{label} M5 the openspec doctor line names {banned!r} as a "
                "remedy. Keel reports which version answered and does not "
                "install or select one."
            )
            report(f"  {line}")
            return 1
    # M4 — the same fact, asserted by the suite rather than by a person who
    # thought to run doctor.
    probe = run_keel(ROOT, "openspec", "--version")
    running = re.search(r"\b(\d+\.\d+\.\d+)\b", probe.stdout or "")
    if not running:
        report(f"{label} M4 could not read the version of the OpenSpec in use.")
        return 1
    if running.group(1) != locked:
        report(
            f"{label} M4 validation is running against OpenSpec "
            f"{running.group(1)} while npm-shrinkwrap.json resolves {locked}. "
            "Results describe a different program: run `npm ci` so the pinned "
            "OpenSpec is the one `keel openspec` resolves."
        )
        return 1
    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


PLUGIN_SKILLS = (
    "keel-align-expectations",
    "keel-debug-failure",
    "keel-handoff",
    "keel-review-checklist",
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

    if codex_manifest.get("hooks") != "./hooks/codex.json":
        report(
            "native-plugin-manifests codex manifest must select its host-compatible "
            "hooks/codex.json configuration."
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
        # A referenced `guidance.md` travels with the body that names it. The
        # host reads the plugin copy directly, so a guidance file the parity
        # check ignored could drift from the criteria it was split out of, and
        # the drift would be invisible to everything except a reader.
        canonical_guidance = canonical_skill.parent / "guidance.md"
        plugin_guidance = plugin_skill.parent / "guidance.md"
        if canonical_guidance.is_file() and not plugin_guidance.is_file():
            report(
                "native-plugin-manifests guidance file diverges from canonical "
                f"source: {skill_name} has guidance.md that the plugin does not "
                "ship, so the body's reference resolves to nothing"
            )
            return 1
        if canonical_guidance.is_file() and plugin_guidance.read_text(
            encoding="utf-8"
        ) != canonical_guidance.read_text(encoding="utf-8"):
            report(
                "native-plugin-manifests guidance file diverges from canonical "
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
    # M1 — on Claude the plugin is the npm package's tree, and the manifest
    # at its root is the one Claude manifest, so a directory entry nobody here
    # controls only has to say where the repository is.
    root_manifest_path = ROOT / ".claude-plugin/plugin.json"
    if not root_manifest_path.is_file():
        report(
            "native-plugin-manifests has no root plugin manifest at "
            ".claude-plugin/plugin.json, so a git-sourced entry has nothing to "
            "read the skills, agent, and hooks from."
        )
        return 1
    root_manifest = json.loads(root_manifest_path.read_text(encoding="utf-8"))
    plugin_manifest = json.loads(
        (ROOT / PLUGIN_ROOT / ".claude-plugin/plugin.json").read_text(
            encoding="utf-8"
        )
    )
    differing = [
        key
        for key in ("name", "version", "description")
        if root_manifest.get(key) != plugin_manifest.get(key)
        or root_manifest.get(key) in (None, "")
    ]
    if differing or root_manifest.get("version") != package_version:
        report(
            "native-plugin-manifests root plugin manifest disagrees with "
            f"{PLUGIN_ROOT}/.claude-plugin/plugin.json or the package version "
            f"{package_version} on {differing or ['version']!r}"
        )
        return 1
    declared_paths = [
        *root_manifest.get("skills", []),
        *root_manifest.get("agents", []),
    ]
    unresolved = [
        path for path in declared_paths if not (ROOT / path).exists()
    ]
    if not declared_paths or unresolved:
        report(
            "native-plugin-manifests root plugin manifest's skills and agents "
            f"must resolve inside the repository; declared {declared_paths!r}, "
            f"unresolved {unresolved!r}"
        )
        return 1
    # The manifest states the hooks a second time, so it is held to the file
    # Codex discovers: the same events, matchers, scripts, and timeouts, with
    # each script path resolved from the repository root instead.
    plugin_hooks = json.loads(
        (ROOT / PLUGIN_ROOT / "hooks/hooks.json").read_text(encoding="utf-8")
    )["hooks"]
    expected_hooks = json.loads(
        json.dumps(plugin_hooks).replace(
            "${CLAUDE_PLUGIN_ROOT}/scripts/",
            "${CLAUDE_PLUGIN_ROOT}/plugins/keel/scripts/",
        )
    )
    # Plus the Claude-only chat hooks (#180, #187). They stay out of
    # hooks.json, which Codex loads too: FileChanged, `asyncRewake`, and the
    # SessionEnd presence hook are Claude Code's.
    def mail_hook(event: str, **extra: object) -> dict:
        return {
            "type": "command",
            "command": "node",
            "args": [
                "${CLAUDE_PLUGIN_ROOT}/plugins/keel/scripts/mail-hook.js",
                event,
            ],
            "timeout": 10,
            **extra,
        }

    expected_hooks["SessionStart"] = [
        *expected_hooks.get("SessionStart", []),
        {"hooks": [mail_hook("session-start")]},
    ]
    expected_hooks["UserPromptSubmit"] = [{"hooks": [mail_hook("user-prompt-submit")]}]
    expected_hooks["PostToolUse"] = [{"hooks": [mail_hook("post-tool-use")]}]
    expected_hooks["FileChanged"] = [
        {"hooks": [mail_hook("file-changed", asyncRewake=True)]}
    ]
    expected_hooks["SessionEnd"] = [{"hooks": [mail_hook("session-end")]}]
    if root_manifest.get("hooks") != expected_hooks:
        report(
            "native-plugin-manifests root plugin manifest hooks diverge "
            f"from {PLUGIN_ROOT}/hooks/hooks.json after resolving script paths "
            "from the repository root, plus the Claude-only chat hooks: "
            f"{root_manifest.get('hooks')!r}"
        )
        return 1
    if sorted(plugin_hooks) != ["PreToolUse", "SessionStart"]:
        report(
            f"native-plugin-manifests {PLUGIN_ROOT}/hooks/hooks.json, which Codex "
            f"also loads, declares events beyond SessionStart and PreToolUse: {sorted(plugin_hooks)!r}"
        )
        return 1
    if "asyncRewake" in json.dumps(plugin_hooks):
        report(
            f"native-plugin-manifests {PLUGIN_ROOT}/hooks/hooks.json carries the "
            "Claude-only asyncRewake field."
        )
        return 1

    # M2 — Keel's own entry installs the npm package the CLI comes from, at
    # exactly this release (#337). It restates no component, so the root
    # manifest stays the only place they are declared, and the package has to
    # ship that manifest or the installed plugin has no components at all.
    source = (claude_entry or {}).get("source")
    want_source = {
        "source": "npm",
        "package": "@christang/keel",
        "version": package_version,
    }
    restated = [
        key for key in ("skills", "agents", "hooks") if key in (claude_entry or {})
    ]
    if (
        source != want_source
        or (claude_entry or {}).get("version") != package_version
        or restated
    ):
        report(
            "native-plugin-manifests claude marketplace entry is not the "
            f"npm package at {package_version}: source {source!r}, "
            f"version {(claude_entry or {}).get('version')!r}, restated "
            f"components {restated!r}"
        )
        return 1

    # M3 — what the host needs from the package to run it as a plugin: a bare
    # `keel` in `bin/` it can put on PATH, and a lockfile npm actually
    # publishes so the pinned OpenSpec is installed beside it.
    npm = shutil.which("npm")
    if npm is not None:
        packed = subprocess.run(
            [npm, "pack", "--dry-run", "--json"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        try:
            modes = {
                item["path"]: item.get("mode", 0)
                for item in json.loads(packed.stdout)[0]["files"]
            }
        except (ValueError, KeyError, IndexError):
            report("native-plugin-manifests could not read npm pack --json.")
            report((packed.stderr or packed.stdout).strip()[:400])
            return 1
        lacking = [
            name
            for name, ok in (
                ("bin/keel", modes.get("bin/keel", 0) & 0o111),
                ("npm-shrinkwrap.json", "npm-shrinkwrap.json" in modes),
                (".claude-plugin/plugin.json", ".claude-plugin/plugin.json" in modes),
            )
            if not ok
        ]
        if lacking:
            report(
                "native-plugin-manifests packed set lacks what the host needs "
                f"to run the package as a plugin: {lacking!r} (bin/keel must "
                "be executable)"
            )
            return 1

    report("native-plugin-manifests scenario passed.")
    return 0


def session_start_message(result: subprocess.CompletedProcess[str]) -> str | None:
    """The human-visible half of the projection, carried on `systemMessage`."""
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout).get("systemMessage")


# Each branch pairs its human message with the tokens a person needs in order to
# act: what the state is, and which command moves it. The degraded branches are
# the load-bearing rows — a fallback nobody sees is the bug this pair of channels
# exists to close.
HUMAN_BRANCH_TOKENS = {
    "ready": ("demo#1.1",),
    "idle": ("idle", "keel context"),
    "ambiguous": ("ambiguous", "keel context"),
    "missing-CLI": ("missing or incompatible", "keel context"),
    "malformed": ("malformed", "keel context"),
    "timeout": ("failed or timed out", "keel context"),
}


HUMAN_AUTHORITY_TOKEN = "OpenSpec and Git"


# The mark is drawn only from the block-element range the host's own banner uses.
# That range is East-Asian-Ambiguous width, so a terminal under a CJK locale
# renders every one of these cells the same way it already renders the banner —
# which is the whole reason the charset is pinned rather than the shape.
MARK_RANGE = (0x2580, 0x259F)


MARK_ROWS = 3


BORDER_RANGE = (0x2500, 0x257F)


def panel_rows(message: str) -> list[str]:
    """The rendered panel: everything after the leading newline."""
    return message[1:].split("\n") if message.startswith("\n") else []


def is_mark_row(content: str) -> bool:
    """A mark row is non-empty and drawn only from blocks and inner spaces.

    The inner spaces are load-bearing shape - they are the owl's eye gaps - so
    the charset test admits them rather than stripping the row down to its
    glyphs and demanding every remaining cell be a block.
    """
    return bool(content.strip()) and all(
        c == " " or MARK_RANGE[0] <= ord(c) <= MARK_RANGE[1] for c in content
    )


def panel_problem(message: str) -> str | None:
    """The panel must close.

    A frame turns a one-cell width error from a cosmetic skew into visibly
    broken output, so every row is checked for equal width rather than trusted.
    The mark keeps its own charset check: the border draws from U+2500-U+257F
    and the mark from U+2580-U+259F, and mixing them is what would misalign
    under a locale that renders one range wide.
    """
    if not message.startswith("\n"):
        return "human message does not open with a newline before the panel"
    rows = panel_rows(message)
    if len(rows) < MARK_ROWS + 3:
        return f"panel has {len(rows)} rows, too few to frame the mark"
    if not (rows[0].startswith("╭") and rows[0].endswith("╮")):
        return f"panel top rule is not a rule: {rows[0]!r}"
    if "Keel" not in rows[0]:
        return "panel top rule carries no title"
    if not (rows[-1].startswith("╰") and rows[-1].endswith("╯")):
        return f"panel bottom rule is not a rule: {rows[-1]!r}"
    for row in rows[1:-1]:
        if not (row.startswith("│") and row.endswith("│")):
            return f"panel body row is not enclosed: {row!r}"
    widths = {len(row) for row in rows}
    if len(widths) != 1:
        return f"panel rows are ragged: widths {sorted(widths)}"
    marks = [row[2:-2] for row in rows[1:-1] if is_mark_row(row[2:-2])]
    if len(marks) != MARK_ROWS:
        return f"panel carries {len(marks)} mark rows, expected {MARK_ROWS}"
    return None


def panel_content(message: str) -> str:
    """The panel with its frame and mark taken away."""
    rows = panel_rows(message)
    kept = [row[2:-2] for row in rows[1:-1] if not is_mark_row(row[2:-2])]
    return " ".join(part.strip() for part in kept if part.strip())


# additionalContext is the agent's half of the projection; the human reads the
# systemMessage line asserted above. Every branch must still carry the
# instruction to relay it, including — especially — the degraded ones. The two
# checks are not redundant: one proves the state was shown, this one proves the
# agent was told to say which state it is working from, and only the second can
# expose the two disagreeing.
SESSION_START_DISCLOSURE = "to the user in your first reply"


# A host loads its plugins once per session, so the projection can be absent for
# reasons no repository check can see. The resident protocol is the carrier of
# last resort and must state the same obligation without trading away the
# continuity rules it already carried.
RESIDENT_SESSION_START_REQUIRED = (
    SESSION_START_DISCLOSURE,
    "keel context",
    # #414: memory and transcripts may inform; `keel context` still decides.
    "`keel context` decides the current task",
)


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

        # Every branch is exercised in both forms. The panel is opt-in, so the
        # default run is the one that ships; the enabled run only proves the
        # decoration still assembles when asked for. Both must carry the same
        # information, which is what keeps the switch from costing anything.
        branches = (
            ("ready", ready_repo, real_cli, None),
            ("idle", idle_repo, real_cli, None),
            ("ambiguous", ambiguous_repo, real_cli, None),
            ("missing-CLI", ready_repo, "keel-definitely-missing-cli-xyz", None),
            ("malformed", ready_repo, f'node "{malformed_cli}"', None),
            ("timeout", ready_repo, f'node "{hang_cli}"', 700),
        )
        for label, repo, cli, timeout_ms in branches:
            for panel_env in (None, "1"):
                result = run_session_start_hook(
                    repo, codex_event, keel_cli=cli,
                    timeout_ms=timeout_ms, panel=panel_env,
                )
                mode = "default" if panel_env is None else "panel"
                message = session_start_message(result)
                if not message:
                    report(
                        f"native-plugin-session-start {label}/{mode} branch "
                        "emitted no human-visible message, so that state "
                        "reaches only the agent and nobody can catch it being "
                        "wrong."
                    )
                    return 1
                if label == "ambiguous" and "alpha#1.1" in message:
                    report(
                        f"native-plugin-session-start {label}/{mode} human "
                        "message named a guessed owner."
                    )
                    return 1
                if panel_env is None:
                    decoration = [
                        c for c in message
                        if MARK_RANGE[0] <= ord(c) <= MARK_RANGE[1]
                        or BORDER_RANGE[0] <= ord(c) <= BORDER_RANGE[1]
                    ]
                    if decoration:
                        report(
                            f"native-plugin-session-start {label} draws the "
                            f"panel without being asked: {decoration[:6]!r}"
                        )
                        return 1
                    if "\n" in message:
                        report(
                            f"native-plugin-session-start {label} default "
                            f"message is not a single line: {message!r}"
                        )
                        return 1
                    carried = message
                else:
                    problem = panel_problem(message)
                    if problem:
                        report(
                            f"native-plugin-session-start {label} {problem}"
                        )
                        return 1
                    # Neither frame nor mark may be load-bearing: take both
                    # away and the message still has to say what the state is
                    # and which command moves it.
                    carried = panel_content(message)
                absent = [
                    token
                    for token in (
                        *HUMAN_BRANCH_TOKENS[label], HUMAN_AUTHORITY_TOKEN
                    )
                    if token not in carried
                ]
                if absent:
                    report(
                        f"native-plugin-session-start {label}/{mode} message "
                        f"omits {absent}: {carried!r}"
                    )
                    return 1

        # A value outside the allowlist must leave the default in place, so a
        # typo cannot silently switch the decoration on.
        typo = session_start_message(
            run_session_start_hook(
                idle_repo, codex_event, keel_cli=real_cli, panel="yeah"
            )
        ) or ""
        if "\n" in typo or "╭" in typo:
            report(
                "native-plugin-session-start enabled the panel for a value "
                f"outside the allowlist: {typo!r}"
            )
            return 1

        # The panel sizes to its content. A change name longer than every other
        # row must widen the frame rather than be cut, because the identifier
        # is the thing the reader came for.
        long_name = "a-deliberately-long-change-name-that-exceeds-the-panel-default"
        wide_repo = tmp / "wide"
        write_text(
            wide_repo / f"openspec/changes/{long_name}/tasks.md",
            task_contract_fixture(),
        )
        wide_message = session_start_message(
            run_session_start_hook(wide_repo, codex_event, keel_cli=real_cli, panel="1")
        ) or ""
        problem = panel_problem(wide_message)
        if problem:
            report(f"native-plugin-session-start wide panel {problem}")
            return 1
        if long_name not in panel_content(wide_message):
            report(
                "native-plugin-session-start truncated the change name to fit "
                f"the panel: {panel_content(wide_message)!r}"
            )
            return 1
        narrow_message = session_start_message(
            run_session_start_hook(
                idle_repo, codex_event, keel_cli=real_cli, panel="1"
            )
        ) or ""
        wide = len(panel_rows(wide_message)[0])
        narrow = len(panel_rows(narrow_message)[0])
        if wide <= narrow:
            report(
                "native-plugin-session-start panel width is fixed, not derived "
                f"from content: wide={wide} narrow={narrow}"
            )
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


# Three versions are comparable in any repository, and the fixture drives each
# one independently: the plugin's by planting a manifest beside a copy of the
# shipping hook, the CLI's by what the fake CLI prints, and the repository's by
# the managed block in its AGENTS.md.
VERSION_DRIFT_STATEMENT = "runtime versions disagree"


# How an update applies: the hooks are fixed when the plugin loads, and the
# host's `/reload-plugins` reloads it in the running session (#164). A restart
# is one way to reach the next load, not the only one, so "only after
# restarting" sends a reader to the expensive remedy and is refused by name.
VERSION_DRIFT_APPLY_TOKENS = ("fixed when it loads the plugin", "/reload-plugins")


VERSION_DRIFT_RETIRED_WORDING = "only after restarting"


def plant_session_start_plugin(
    dest: Path, version: str | None, *, manifest: str = ".claude-plugin"
) -> Path:
    """A copy of the shipping hook with a manifest the suite controls."""
    write_text(
        dest / "scripts/session-start.js",
        (ROOT / PLUGIN_ROOT / "scripts/session-start.js").read_text(
            encoding="utf-8"
        ),
    )
    if version is not None:
        write_text(
            dest / manifest / "plugin.json",
            json.dumps({"name": "keel", "version": version}, indent=2) + "\n",
        )
    return dest


def fake_keel_cli(path: Path, version: str, *, change: str = "demo") -> str:
    """A CLI that reports the version the suite chose and answers `context`."""
    context = json.dumps(
        {
            "schemaVersion": 1,
            "status": "ready",
            "selection": {"source": "inferred", "change": change, "task": "1.1"},
            "nextAction": {"kind": "task-start"},
            "read": [f"openspec/changes/{change}/tasks.md"],
            "reasons": [],
            "warnings": [],
        }
    )
    write_text(
        path,
        "if (process.argv.includes('--version')) {\n"
        f"  console.log('keel {version}');\n"
        "} else {\n"
        f"  console.log({json.dumps(context)});\n"
        "}\n",
    )
    return f'node "{path}"'


def plant_spawn_recorder(path: Path) -> str:
    """A preload that records every subprocess the hook starts.

    Patching `child_process` inside the hook's own process sees a spawn however
    it is reached, where a PATH shim only sees the commands it was told to
    expect. The boundary is that process: a spawn made by something the hook
    spawned is not recorded, which is the right scope, because what is being
    asserted is what the hook does and not what the CLI does afterwards.

    The two `keel` invocations the hook already makes are its own positive
    control - a recorder that stopped working leaves an empty log, and that is
    reported as the recorder failing rather than as the hook behaving.
    """
    write_text(
        path,
        "const cp = require('child_process');\n"
        "const fs = require('fs');\n"
        "const log = process.env.KEEL_FIXTURE_SPAWN_LOG;\n"
        "for (const name of ['spawn', 'spawnSync', 'exec', 'execSync',\n"
        "  'execFile', 'execFileSync', 'fork']) {\n"
        "  const original = cp[name];\n"
        "  cp[name] = function (...args) {\n"
        "    fs.appendFileSync(log, name + ' ' + String(args[0]) + '\\n');\n"
        "    return original.apply(this, args);\n"
        "  };\n"
        "}\n",
    )
    return f"--require {path}"


def validate_runtime_version_drift_scenario() -> int:
    codex_event = {"hook_event_name": "SessionStart", "source": "startup"}

    with tempfile.TemporaryDirectory(
        prefix="keel-version-drift-", ignore_cleanup_errors=True
    ) as raw_tmp:
        tmp = Path(raw_tmp)

        # The drift this change exists to have caught, reproduced exactly: the
        # plugin and CLI five minor versions behind the protocol the repository
        # declares, with every gate and projection still reporting normally.
        repo = tmp / "repo"
        write_text(repo / "openspec/changes/demo/tasks.md", task_contract_fixture())
        write_text(
            repo / "AGENTS.md",
            "# Keel v5.7.1 Agent Protocol\n\n"
            "<!-- keel:start version=5.7.1 -->\n## Session Start\n"
            "<!-- keel:end -->\n",
        )
        stale_plugin = plant_session_start_plugin(tmp / "stale-plugin", "5.2.1")
        stale_cli = fake_keel_cli(tmp / "stale-cli.js", "5.2.1")

        drifted = run_session_start_hook(
            repo, codex_event, keel_cli=stale_cli, plugin_root=stale_plugin
        )
        if drifted.returncode != 0:
            report("runtime-version-drift hook did not exit 0 on a mismatch.")
            report((drifted.stderr or drifted.stdout).strip())
            return 1
        channels = {
            "additionalContext": session_start_context(drifted) or "",
            "systemMessage": session_start_message(drifted) or "",
        }
        for channel, text in channels.items():
            lowered = text.lower()
            if VERSION_DRIFT_STATEMENT not in lowered:
                report(
                    f"runtime-version-drift {channel} does not state that the "
                    f"versions disagree: {text!r}"
                )
                return 1
            absent = [
                version
                for version in ("5.2.1", "5.7.1")
                if version not in text
            ]
            if absent:
                report(
                    f"runtime-version-drift {channel} omits the discovered "
                    f"versions {absent}: {text!r}"
                )
                return 1
            missing = [
                token
                for token in VERSION_DRIFT_APPLY_TOKENS
                if token not in lowered
            ]
            if missing:
                report(
                    f"runtime-version-drift {channel} omits how an update applies "
                    f"{missing}, so a reader who updates the plugin and sees no "
                    f"change concludes the check is broken: {text!r}"
                )
                return 1
            if VERSION_DRIFT_RETIRED_WORDING in lowered:
                report(
                    f"runtime-version-drift {channel} omits how an update applies "
                    f"and still says it applies {VERSION_DRIFT_RETIRED_WORDING!r}, "
                    f"which sends the reader to a restart when a reload would "
                    f"do: {text!r}"
                )
                return 1

        # The remedy belongs to what lags (#240): plugin and CLI behind the
        # protocol name the plugin update, and a protocol behind them names the
        # protocol refresh, never the plugin update that would change nothing.
        if "claude plugin update" not in channels["additionalContext"]:
            report(
                "runtime-version-drift a plugin behind the protocol does not name "
                f"the plugin update: {channels['additionalContext']!r}"
            )
            return 1
        lagging = tmp / "lagging-protocol"
        write_text(lagging / "openspec/changes/demo/tasks.md", task_contract_fixture())
        write_text(
            lagging / "CLAUDE.md",
            "<!-- keel:start version=5.2.0 -->\n## Session Start\n<!-- keel:end -->\n",
        )
        behind = run_session_start_hook(
            lagging, codex_event, keel_cli=stale_cli, plugin_root=stale_plugin
        )
        behind_text = session_start_context(behind) or ""
        if "keel --install --target claude" not in behind_text:
            report(
                "runtime-version-drift a protocol behind the plugin and CLI does not "
                f"name the protocol refresh: {behind_text!r}"
            )
            return 1
        if "claude plugin update" in behind_text:
            report(
                "runtime-version-drift a protocol behind the plugin and CLI still "
                f"names the plugin update, which changes nothing: {behind_text!r}"
            )
            return 1

        # Silence when aligned, and silence that costs nothing else. The drift
        # sentence is lifted off the mismatched payload and the remainder must
        # be byte-identical to the aligned one: that is the comparison disabled
        # on the same run, and it proves the capability's whole effect is the
        # one line rather than a reshaped projection.
        aligned_plugin = plant_session_start_plugin(tmp / "aligned-plugin", "5.7.1")
        aligned_cli = fake_keel_cli(tmp / "aligned-cli.js", "5.7.1")
        aligned = run_session_start_hook(
            repo, codex_event, keel_cli=aligned_cli, plugin_root=aligned_plugin
        )
        aligned_context = session_start_context(aligned) or ""
        aligned_message = session_start_message(aligned) or ""
        for channel, text in (
            ("additionalContext", aligned_context),
            ("systemMessage", aligned_message),
        ):
            if VERSION_DRIFT_STATEMENT in text.lower() or "5.7.1" in text:
                report(
                    f"runtime-version-drift {channel} spoke about versions that "
                    f"agree, and a line printed every session is a line nobody "
                    f"reads when it matters: {text!r}"
                )
                return 1

        drift_lines = [
            line
            for line in channels["additionalContext"].split("\n")
            if VERSION_DRIFT_STATEMENT in line.lower()
        ]
        if len(drift_lines) != 1:
            report(
                "runtime-version-drift mismatched additionalContext carries "
                f"{len(drift_lines)} version lines, expected exactly one."
            )
            return 1
        sentence = drift_lines[0].removeprefix("- ")
        human_sentence = sentence[0].upper() + sentence[1:]
        if human_sentence + " " not in channels["systemMessage"]:
            report(
                "runtime-version-drift channels disagree: the human message "
                "does not carry the sentence the model was given: "
                f"{channels['systemMessage']!r}"
            )
            return 1
        stripped = {
            "additionalContext": "\n".join(
                line
                for line in channels["additionalContext"].split("\n")
                if line != drift_lines[0]
            ),
            "systemMessage": channels["systemMessage"].replace(
                human_sentence + " ", "", 1
            ),
        }
        for channel, baseline in (
            ("additionalContext", aligned_context),
            ("systemMessage", aligned_message),
        ):
            if stripped[channel] != baseline:
                report(
                    f"runtime-version-drift {channel} changed beyond the version "
                    f"line:\n  with drift removed: {stripped[channel]!r}\n"
                    f"  aligned:             {baseline!r}"
                )
                return 1

        # Keel reports and does not manage. The obvious next sentence after
        # "your plugin is stale" is "so let me update it", and the host already
        # owns that command; naming it is the whole remedy Keel offers.
        if "claude plugin update" not in sentence:
            report(
                "runtime-version-drift report does not name the host's own "
                f"update command, leaving the reader with no move: {sentence!r}"
            )
            return 1
        for forbidden in ("keel update", "npm install", "npm i "):
            if forbidden in sentence.lower():
                report(
                    "runtime-version-drift report offers a Keel-side remedy "
                    f"for a host-owned action ({forbidden!r}): {sentence!r}"
                )
                return 1

        # Naming is not running. Every subprocess the hook starts is recorded
        # from inside its own process, so the two `keel` invocations it already
        # made are the recorder's positive control: a recorder that stopped
        # working leaves an empty log, which this count rejects.
        spawn_log = tmp / "spawns.log"
        recorded = run_session_start_hook(
            repo,
            codex_event,
            keel_cli=stale_cli,
            plugin_root=stale_plugin,
            extra_env={
                "NODE_OPTIONS": plant_spawn_recorder(tmp / "recorder.js"),
                "KEEL_FIXTURE_SPAWN_LOG": str(spawn_log),
            },
        )
        if VERSION_DRIFT_STATEMENT not in (
            session_start_context(recorded) or ""
        ).lower():
            report(
                "runtime-version-drift the recorded run did not reach the "
                "mismatch branch, so its spawn log proves nothing."
            )
            return 1
        recorded_lines = (
            spawn_log.read_text(encoding="utf-8").splitlines()
            if spawn_log.exists()
            else []
        )
        spawns = [line for line in recorded_lines if line.strip()]
        # Three distinct causes, three distinct messages. An empty log is the
        # recorder having failed, not the hook having behaved: reporting it as
        # a rogue subprocess sends the reader looking for a process that was
        # never there.
        if not spawns:
            report(
                "runtime-version-drift recorded no subprocess at all, so the "
                "recorder never loaded and every no-extra-spawn claim below it "
                "would pass vacuously. The hook makes two `keel` invocations of "
                "its own and both should appear."
            )
            return 1
        beyond = [line for line in spawns if "stale-cli.js" not in line]
        if beyond:
            report(
                "runtime-version-drift hook spawned something beyond the keel "
                f"invocations it already made: {beyond!r}"
            )
            return 1
        if len(spawns) != 2:
            report(
                f"runtime-version-drift hook made {len(spawns)} keel "
                "invocations, not the two it already made before this change: "
                f"{spawns!r}"
            )
            return 1

        # Missing is not mismatched. A repository with no managed block is a
        # normal state, and warning about it every session would train its
        # reader past the one session that mattered — the same credibility
        # argument as silence when aligned, running the other way.
        bare = tmp / "bare"
        write_text(bare / "openspec/changes/demo/tasks.md", task_contract_fixture())
        undiscovered = run_session_start_hook(
            bare, codex_event, keel_cli=aligned_cli, plugin_root=aligned_plugin
        )
        for channel, text in (
            ("additionalContext", session_start_context(undiscovered) or ""),
            ("systemMessage", session_start_message(undiscovered) or ""),
        ):
            if VERSION_DRIFT_STATEMENT in text.lower():
                report(
                    f"runtime-version-drift {channel} called an undiscoverable "
                    f"protocol version a disagreement: {text!r}"
                )
                return 1

        # One version out of reach does not suppress the others. The reader is
        # told which two disagree and, so the report cannot be misread as a
        # complete comparison, which one was never read at all.
        partial = run_session_start_hook(
            bare, codex_event, keel_cli=stale_cli, plugin_root=aligned_plugin
        )
        partial_context = session_start_context(partial) or ""
        partial_message = session_start_message(partial) or ""
        for channel, text in (
            ("additionalContext", partial_context),
            ("systemMessage", partial_message),
        ):
            lowered = text.lower()
            if VERSION_DRIFT_STATEMENT not in lowered:
                report(
                    f"runtime-version-drift {channel} stayed silent about two "
                    f"readable versions that disagree because a third could not "
                    f"be read: {text!r}"
                )
                return 1
            if "protocol" not in lowered or "undiscovered" not in lowered:
                report(
                    f"runtime-version-drift {channel} reported a partial "
                    "comparison as a complete one, without naming the version "
                    f"it never read: {text!r}"
                )
                return 1
            if "null" in lowered or "undefined" in lowered:
                report(
                    f"runtime-version-drift {channel} printed an absent version "
                    f"as a value: {text!r}"
                )
                return 1

        # The comparison is an addition to the projection, never a precondition
        # for it. With no manifest to read and no CLAUDE_PLUGIN_ROOT to fall
        # back on, the continuity report a session actually depends on has to
        # arrive intact.
        rootless = plant_session_start_plugin(tmp / "rootless-plugin", None)
        degraded = run_session_start_hook(
            repo,
            codex_event,
            keel_cli=stale_cli,
            plugin_root=rootless,
            extra_env={"CLAUDE_PLUGIN_ROOT": ""},
        )
        degraded_context = session_start_context(degraded) or ""
        if degraded.returncode != 0:
            report(
                "runtime-version-drift an unreadable plugin manifest stopped "
                "the hook from exiting 0."
            )
            report((degraded.stderr or degraded.stdout).strip())
            return 1
        for needle in ("demo#1.1", "task-start", SESSION_START_DISCLOSURE):
            if needle not in degraded_context:
                report(
                    "runtime-version-drift an unreadable plugin manifest "
                    f"degraded the continuity report, which lost {needle!r}: "
                    f"{degraded_context!r}"
                )
                return 1

    report("runtime-version-drift scenario passed.")
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


def plant_path_keel(directory: Path, cli_script: Path) -> Path:
    """A `keel` command on PATH that answers from the given fake CLI."""
    node = shutil.which("node") or "node"
    write_text(
        directory / "keel",
        f'#!/bin/sh\nexec "{node}" "{cli_script}" "$@"\n',
    )
    (directory / "keel").chmod(0o755)
    write_text(
        directory / "keel.cmd",
        f'@"{node}" "{cli_script}" %*\r\n',
    )
    return directory


def validate_plugin_runs_its_own_cli_scenario() -> int:
    """Issue #164: on Claude the plugin carries the whole package.

    The hook, running from inside that package, must run the CLI the package
    ships rather than whatever `keel` is on PATH, and must report a PATH copy
    that disagrees, because the host puts the user's PATH ahead of plugin
    `bin/` directories and the agent's own commands resolve that copy first.
    """
    label = "plugin-runs-its-own-cli"
    event = {"hook_event_name": "SessionStart", "source": "startup"}
    with tempfile.TemporaryDirectory(
        prefix="keel-own-cli-", ignore_cleanup_errors=True
    ) as raw_tmp:
        tmp = Path(raw_tmp)
        repo = tmp / "repo"
        write_text(repo / "openspec/changes/demo/tasks.md", task_contract_fixture())
        write_text(
            repo / "AGENTS.md",
            "# Keel v5.80.0 Agent Protocol\n\n"
            "<!-- keel:start version=5.80.0 -->\n## Session Start\n"
            "<!-- keel:end -->\n",
        )
        package = tmp / "package"
        write_text(
            package / "package.json",
            json.dumps({"name": "@christang/keel", "version": "5.80.0"}) + "\n",
        )
        fake_keel_cli(package / "bin/keel.js", "5.80.0")
        plugin = plant_session_start_plugin(package / "plugins/keel", "5.80.0")

        stale_path = plant_path_keel(
            tmp / "stale-path", Path(fake_keel_cli(tmp / "path-cli.js", "5.70.0").split('"')[1])
        )
        spawn_log = tmp / "spawns.log"
        shadowed = run_session_start_hook(
            repo,
            event,
            keel_cli=None,
            plugin_root=plugin,
            extra_env={
                "PATH": str(stale_path) + os.pathsep + os.environ.get("PATH", ""),
                "NODE_OPTIONS": plant_spawn_recorder(tmp / "recorder.js"),
                "KEEL_FIXTURE_SPAWN_LOG": str(spawn_log),
            },
        )
        spawns = (
            spawn_log.read_text(encoding="utf-8").splitlines()
            if spawn_log.exists()
            else []
        )
        own = str(package / "bin/keel.js")
        answered = [line for line in spawns if own in line and "context" in line]
        # M2 — which program answered the projection.
        if not answered:
            report(
                f"{label} M2 ran the keel on PATH instead of the CLI its package "
                f"ships ({own}): {spawns!r}"
            )
            return 1
        # M3 — the PATH copy that disagrees is named, on both channels.
        for channel, text in (
            ("additionalContext", session_start_context(shadowed) or ""),
            ("systemMessage", session_start_message(shadowed) or ""),
        ):
            lowered = text.lower()
            absent = [
                needle
                for needle in (
                    VERSION_DRIFT_STATEMENT,
                    "5.70.0",
                    "shadows",
                    "npm rm -g @christang/keel",
                )
                if needle not in lowered
            ]
            if absent:
                report(
                    f"{label} M3 {channel} did not report the keel that shadows "
                    f"the plugin's CLI; it lacks {absent!r}: {text!r}"
                )
                return 1

        # A PATH copy at the plugin's own version shadows nothing that
        # differs, and silence when aligned is the whole credibility argument.
        aligned_path = plant_path_keel(
            tmp / "aligned-path", Path(fake_keel_cli(tmp / "aligned-cli.js", "5.80.0").split('"')[1])
        )
        aligned = run_session_start_hook(
            repo,
            event,
            keel_cli=None,
            plugin_root=plugin,
            extra_env={"PATH": str(aligned_path) + os.pathsep + os.environ.get("PATH", "")},
        )
        if VERSION_DRIFT_STATEMENT in (session_start_context(aligned) or "").lower():
            report(
                f"{label} M3 reported drift for a PATH keel at the plugin's own "
                f"version: {session_start_context(aligned)!r}"
            )
            return 1

        # M4 — the plugin-only install: nothing called `keel` on PATH at all.
        # PATH holds only a directory with `node` in it, so no global install
        # on the machine running the suite can answer.
        bare_path = tmp / "bare-path"
        bare_path.mkdir()
        node = shutil.which("node")
        if node:
            try:
                (bare_path / Path(node).name).symlink_to(node)
            except OSError:
                shutil.copy2(node, bare_path / Path(node).name)
        alone = run_session_start_hook(
            repo,
            event,
            keel_cli=None,
            plugin_root=plugin,
            extra_env={"PATH": str(bare_path)},
        )
        alone_context = session_start_context(alone) or ""
        if "demo#1.1" not in alone_context:
            report(
                f"{label} M4 the projection fell back with no keel on PATH, "
                f"which is the plugin-only install: {alone_context!r}"
            )
            return 1
        if VERSION_DRIFT_STATEMENT in alone_context.lower():
            report(
                f"{label} M4 the projection reported drift with no keel on "
                f"PATH, as if an absent copy disagreed: {alone_context!r}"
            )
            return 1
    report(f"{label} scenario passed.")
    return 0


def validate_drift_names_a_pending_reload_scenario() -> int:
    """Issue #172: an update the host already installed needs only a reload.

    The session keeps the hooks it loaded, and `/clear` does not reload them, so
    a plugin the host has already updated keeps reporting drift until the
    reader reloads. Naming the host's update command there sends them to an
    action that already happened, and aligning the PATH copy with the loaded
    plugin is a downgrade.
    """
    label = "drift-names-a-pending-reload"
    event = {"hook_event_name": "SessionStart", "source": "clear"}
    with tempfile.TemporaryDirectory(
        prefix="keel-pending-reload-", ignore_cleanup_errors=True
    ) as raw_tmp:
        tmp = Path(raw_tmp)
        repo = tmp / "repo"
        write_text(repo / "openspec/changes/demo/tasks.md", task_contract_fixture())
        write_text(
            repo / "AGENTS.md",
            "# Keel v5.81.0 Agent Protocol\n\n"
            "<!-- keel:start version=5.81.0 -->\n## Session Start\n"
            "<!-- keel:end -->\n",
        )
        # The host's layout: <plugins>/cache/<marketplace>/<plugin>/<version>,
        # with its install record in <plugins>. The loaded copy is 5.80.0.
        plugins_dir = tmp / "plugins"
        package = plugins_dir / "cache/mkt/keel/5.80.0"
        write_text(
            package / "package.json",
            json.dumps({"name": "@christang/keel", "version": "5.80.0"}) + "\n",
        )
        fake_keel_cli(package / "bin/keel.js", "5.80.0")
        plugin = plant_session_start_plugin(package / "plugins/keel", "5.80.0")
        record = plugins_dir / "installed_plugins.json"

        def write_record(entries: dict) -> None:
            write_text(record, json.dumps({"version": 2, "plugins": entries}) + "\n")

        installed = str(plugins_dir / "cache/mkt/keel/5.81.0")
        write_record(
            {
                "keel@mkt": [
                    {"scope": "user", "installPath": installed, "version": "5.81.0"}
                ]
            }
        )
        path_cli = Path(fake_keel_cli(tmp / "path-cli.js", "5.81.0").split('"')[1])
        path_dir = plant_path_keel(tmp / "path", path_cli)
        env = {"PATH": str(path_dir) + os.pathsep + os.environ.get("PATH", "")}

        def channels() -> dict[str, str]:
            run = run_session_start_hook(
                repo, event, keel_cli=None, plugin_root=plugin, extra_env=env
            )
            return {
                "additionalContext": session_start_context(run) or "",
                "systemMessage": session_start_message(run) or "",
            }

        pending = channels()
        for channel, text in pending.items():
            lowered = text.lower()
            # M1 — the update is named as installed, and the reload as the remedy.
            if "claude plugin update" in lowered:
                report(
                    f"{label} M1 {channel} named claude plugin update for an "
                    f"update the host already installed: {text!r}"
                )
                return 1
            if "already installed plugin 5.81.0" not in lowered:
                report(
                    f"{label} M1 {channel} does not say the host already "
                    f"installed plugin 5.81.0: {text!r}"
                )
                return 1
            if "/reload-plugins" not in lowered:
                report(f"{label} M1 {channel} does not name /reload-plugins: {text!r}")
                return 1
            # M2 — a PATH copy at the installed version is not a shadow.
            if "shadows" in lowered or "@christang/keel@5.80.0" in lowered:
                report(
                    f"{label} M2 {channel} called a PATH keel at the installed "
                    f"version a shadow: {text!r}"
                )
                return 1

        # M3 — another plugin's install is not this one's, and no record at
        # all is the same as a record that names nothing of ours. Its directory
        # exists, as the host's would, so the entry is excluded by being
        # another plugin's and not by being unreadable.
        (plugins_dir / "cache/mkt/other/9.9.9").mkdir(parents=True)
        write_record(
            {
                "other@mkt": [
                    {
                        "scope": "user",
                        "installPath": str(plugins_dir / "cache/mkt/other/9.9.9"),
                        "version": "9.9.9",
                    }
                ]
            }
        )
        unrelated = channels()
        for channel, text in unrelated.items():
            lowered = text.lower()
            if "already installed" in lowered:
                report(
                    f"{label} M3 {channel} read another plugin's install as "
                    f"this one's: {text!r}"
                )
                return 1
            if "claude plugin update" not in lowered:
                report(
                    f"{label} M3 {channel} dropped the update command with no "
                    f"install of this plugin recorded: {text!r}"
                )
                return 1
        record.unlink()
        absent = channels()
        if absent != unrelated:
            report(
                f"{label} M3 a missing install record changed the report:\n"
                f"  no record:      {absent!r}\n  other plugin:   {unrelated!r}"
            )
            return 1
    report(f"{label} scenario passed.")
    return 0


def validate_hook_hands_off_to_installed_update_scenario() -> int:
    """Issue #204: a Claude hook runs the newest installed compatible copy.

    Claude binds a session's hooks to the version directory it loaded and keeps
    that directory after an update, so without a hand-off a running session
    executes the old scripts until `/reload-plugins`. The loaded script reads
    the host's install record and hands the event to the newer install's copy
    of itself when, and only when, that copy is a compatible one.
    """
    label = "hook-hands-off-to-installed-update:"
    with tempfile.TemporaryDirectory(prefix="keel-handoff-", ignore_cleanup_errors=True) as raw:
        tmp = Path(raw)
        cwd = tmp / "work"
        cwd.mkdir()
        plugins_dir = tmp / "plugins"
        cache = plugins_dir / "cache/m/keel"
        stubs = ("session-start.js", "mail-hook.js")
        loaded = plant_handoff_package(cache / "5.0.0", "5.0.0")
        newer = plant_handoff_package(cache / "5.1.0", "5.1.0", stubs=stubs)
        plant_handoff_package(cache / "6.0.0", "6.0.0", stubs=stubs)
        lacking = plant_handoff_package(cache / "5.2.0", "5.2.0")
        (lacking / "plugins/keel/scripts/mail-hook.js").unlink()
        (lacking / "plugins/keel/scripts/session-start.js").unlink()
        # The loaded copy's own logic must print nothing a stub prints: an
        # empty CLI for mail-hook, and no `openspec/` for session-start.
        quiet_cli = tmp / "quiet-cli.js"
        write_text(quiet_cli, "process.exit(0);\n")
        base_env = {"KEEL_CLI": f'node "{quiet_cli}"'}
        event = json.dumps({"hook_event_name": "SessionStart", "cwd": str(cwd), "probe": "stdin-bytes"})

        def run(script: str, extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
            args = ["session-start"] if script == "mail-hook.js" else []
            env = dict(base_env)
            env.update(extra or {})
            return run_hook_script(loaded / "plugins/keel/scripts" / script, args, event, cwd, env)

        # M1 — an installed, newer, same-major copy runs, with the same input.
        write_install_record(plugins_dir, newer)
        for script in stubs:
            result = run(script, {"HANDOFF_STUB_STATUS": "3"})
            seen = stub_output(result)
            if seen is None:
                report(f"{label} {script} 5.0.0 did not hand off to installed 5.1.0: "
                       f"stdout={result.stdout!r} stderr={result.stderr!r}")
                return 1
            expected_args = ["session-start"] if script == "mail-hook.js" else []
            problems = []
            if seen["stub"] != "5.1.0" or seen["script"] != script:
                problems.append(f"ran {seen['script']} at {seen['stub']}")
            if seen["argv"] != expected_args:
                problems.append(f"argv {seen['argv']!r}")
            if seen["input"] != event:
                problems.append(f"stdin {seen['input']!r}")
            if seen["forwarded"] != "5.0.0":
                problems.append(f"KEEL_HOOK_FORWARDED={seen['forwarded']!r}")
            if Path(seen["root"] or "").resolve() != newer.resolve():
                problems.append(f"CLAUDE_PLUGIN_ROOT={seen['root']!r}")
            if result.returncode != 3:
                problems.append(f"exit {result.returncode}, not the stub's 3")
            if problems:
                report(f"{label} {script} handed off wrongly: {'; '.join(problems)}")
                return 1

        # Every other case runs the loaded script's own logic.
        cases = [
            ("the record names the loaded install", lambda: write_install_record(plugins_dir, loaded), {}),
            ("the record names a different major", lambda: write_install_record(plugins_dir, cache / "6.0.0"), {}),
            ("the recorded path does not exist", lambda: write_install_record(plugins_dir, cache / "5.9.0"), {}),
            ("the recorded tree lacks the script", lambda: write_install_record(plugins_dir, lacking), {}),
            ("there is no install record", lambda: (plugins_dir / "installed_plugins.json").unlink(), {}),
            ("the run is already a hand-off", lambda: write_install_record(plugins_dir, newer),
             {"KEEL_HOOK_FORWARDED": "4.9.0"}),
        ]
        for name, arrange, extra in cases:
            arrange()
            for script in stubs:
                result = run(script, extra)
                if stub_output(result) is not None:
                    report(f"{label} {script} handed off although {name}: {result.stdout!r}")
                    return 1

        # Codex resolves the plugin root per hook call, so a Codex-shaped
        # install — the plugin directory itself is the cached root — never hands off.
        codex_cache = tmp / "codex-home/plugins/cache/m/keel"
        for version, stubbed in (("5.0.0", ()), ("5.1.0", stubs)):
            plugin = codex_cache / version
            write_text(plugin / ".codex-plugin/plugin.json",
                       json.dumps({"name": "keel", "version": version}) + "\n")
            write_text(plugin / ".claude-plugin/plugin.json",
                       json.dumps({"name": "keel", "version": version}) + "\n")
            for source in sorted((ROOT / PLUGIN_ROOT / "scripts").glob("*.js")):
                body = HANDOFF_STUB if source.name in stubbed else source.read_text(encoding="utf-8")
                write_text(plugin / "scripts" / source.name, body)
        write_install_record(tmp / "codex-home/plugins", codex_cache / "5.1.0")
        result = run_hook_script(codex_cache / "5.0.0/scripts/session-start.js", [], event, cwd, base_env)
        if stub_output(result) is not None:
            report(f"{label} a Codex-shaped install handed off: {result.stdout!r}")
            return 1

    if "hook-hands-off-to-installed-update" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("hook-hands-off-to-installed-update scenario passed.")
    return 0


def plant_real_package(root: Path, version: str) -> Path:
    """A cached Claude install made from this working tree's real package,
    stamped with `version`, so its hooks run their real logic end to end."""
    for part in ("bin", "src", "scripts", "plugins", "assets", ".claude-plugin"):
        shutil.copytree(ROOT / part, root / part,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    pkg["version"] = version
    write_text(root / "package.json", json.dumps(pkg, indent=2) + "\n")
    for manifest in (root / ".claude-plugin/plugin.json",
                     root / "plugins/keel/.claude-plugin/plugin.json"):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["version"] = version
        write_text(manifest, json.dumps(data, indent=2) + "\n")
    if (ROOT / "node_modules").exists():
        (root / "node_modules").symlink_to(ROOT / "node_modules", target_is_directory=True)
    return root


def validate_adopted_update_is_silent_unless_reload_scenario() -> int:
    """Issue #204: an adopted update says nothing unless a reload is needed.

    A handed-off SessionStart runs as the installed version, so with the CLI
    and protocol at that version there is no drift to report. What the hand-off
    cannot bring forward is what the host loaded at session start — skills,
    agents, and declared hooks — and only a difference there earns a line,
    naming `/reload-plugins` and nothing else.
    """
    label = "adopted-update-is-silent-unless-reload:"
    event = {"hook_event_name": "SessionStart", "source": "clear"}
    with tempfile.TemporaryDirectory(prefix="keel-adopt-", ignore_cleanup_errors=True) as raw:
        tmp = Path(raw)
        plugins_dir = tmp / "plugins"
        cache = plugins_dir / "cache/m/keel"
        loaded = plant_real_package(cache / "5.0.0", "5.0.0")
        newer = plant_real_package(cache / "5.1.0", "5.1.0")
        write_install_record(plugins_dir, newer)

        repo = tmp / "repo"
        write_text(repo / "openspec/changes/demo/tasks.md", task_contract_fixture())
        write_text(
            repo / "AGENTS.md",
            "# Keel v5.1.0 Agent Protocol\n\n<!-- keel:start version=5.1.0 -->\n"
            "## Session Start\n<!-- keel:end -->\n",
        )
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        # No `keel` on PATH, so the suite rather than the developer's global
        # install decides whether a PATH copy is compared.
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        for tool in ("node", "git"):
            found = shutil.which(tool)
            if found:
                (bin_dir / tool).symlink_to(found)
        env = {"PATH": str(bin_dir) + os.pathsep + "/usr/bin" + os.pathsep + "/bin"}

        def channels() -> tuple[str, str]:
            run = run_session_start_hook(
                repo, event, keel_cli=None, plugin_root=loaded / "plugins/keel", extra_env=env
            )
            return session_start_context(run) or "", session_start_message(run) or ""

        context, human = channels()
        for name, text in (("additionalContext", context), ("systemMessage", human)):
            lowered = text.lower()
            if "fallback" in lowered:
                report(f"{label} {name} is the hook's fallback, so the handed-off SessionStart "
                       f"did not reach a working CLI: {text!r}")
                return 1
            if "projection" not in lowered and "keel:" not in lowered:
                report(f"{label} {name} carries no projection: {text!r}")
                return 1
            if "versions disagree" in lowered or "/reload-plugins" in lowered or "5.0.0" in text:
                report(f"{label} {name} reported versions or a reload after a compatible, "
                       f"identical update: {text!r}")
                return 1

        skill = next((newer / "plugins/keel/skills").rglob("SKILL.md"))
        skill.write_text(skill.read_text(encoding="utf-8") + "\nChanged in 5.1.0.\n", encoding="utf-8")
        context, human = channels()
        for name, text in (("additionalContext", context), ("systemMessage", human)):
            lowered = text.lower()
            lines = [line for line in text.splitlines() if "/reload-plugins" in line]
            if len(lines) != 1:
                report(f"{label} {name} carries {len(lines)} lines naming /reload-plugins "
                       f"after a skill changed, not one: {text!r}")
                return 1
            line = lines[0].lower()
            if "5.1.0" not in line or "skill" not in line:
                report(f"{label} {name} does not name 5.1.0 and the skills: {lines[0]!r}")
                return 1
            if "claude plugin update" in lowered:
                report(f"{label} {name} named an update command for an installed update: {text!r}")
                return 1

    if "adopted-update-is-silent-unless-reload" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("adopted-update-is-silent-unless-reload scenario passed.")
    return 0


# One fake for npm, claude, and codex. It appends its argv to FAKE_LOG and keeps
# each host's installed Keel version in FAKE_STATE, so `plugin list --json`
# answers 5.0.0 before the host's update command and 5.1.0 after it.
UPDATE_FAKE = r"""const fs = require("fs");
const path = require("path");
const host = process.env.FAKE_HOST;
const args = process.argv.slice(2);
fs.appendFileSync(process.env.FAKE_LOG, JSON.stringify([host, ...args]) + "\n");
// FAKE_LIST_SLEEP_<HOST> holds `plugin list --json` for N seconds, and
// FAKE_LIST_EXIT_<HOST> makes it exit with that status (#354).
// FAKE_LIST_SLEEP_TIMES_<HOST> holds only the first N such calls (#365); the
// count is written before the hold, since a held call is killed.
if (args.join(" ") === "plugin list --json") {
  let hold = Number(process.env[`FAKE_LIST_SLEEP_${host.toUpperCase()}`] || "0");
  const times = Number(process.env[`FAKE_LIST_SLEEP_TIMES_${host.toUpperCase()}`] || "Infinity");
  const counter = `${process.env.FAKE_STATE}.held-${host}`;
  const held = fs.existsSync(counter) ? Number(fs.readFileSync(counter, "utf8")) : 0;
  if (held >= times) hold = 0;
  else if (hold > 0) fs.writeFileSync(counter, String(held + 1));
  if (hold > 0) Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, hold * 1000);
  const code = process.env[`FAKE_LIST_EXIT_${host.toUpperCase()}`];
  if (code) process.exit(Number(code));
}
const stateFile = process.env.FAKE_STATE;
const state = fs.existsSync(stateFile) ? JSON.parse(fs.readFileSync(stateFile, "utf8")) : {};
const save = () => fs.writeFileSync(stateFile, JSON.stringify(state));
const version = state[host] || "5.0.0";
const failOn = process.env[`FAKE_FAIL_${host.toUpperCase()}`] || "";
// FAKE_FAIL_TIMES_<HOST> limits the failures to the first N matching calls.
const failTimes = Number(process.env[`FAKE_FAIL_TIMES_${host.toUpperCase()}`] || "Infinity");
if (failOn && args.join(" ").includes(failOn)) {
  const failed = (state.failed && state.failed[host]) || 0;
  if (failed < failTimes) {
    state.failed = { ...(state.failed || {}), [host]: failed + 1 };
    save();
    // FAKE_FAIL_STDERR_<HOST> replaces the refusal's last line, as a host's own
    // error text would read (#421).
    const said = process.env[`FAKE_FAIL_STDERR_${host.toUpperCase()}`] || `fake ${host}: refused ${args.join(" ")}`;
    process.stderr.write(`fake ${host}: warming up\n${said}\n`);
    process.exit(1);
  }
}
if (host === "npm") {
  if (args[0] === "pack") {
    const dest = args[args.indexOf("--pack-destination") + 1];
    fs.writeFileSync(path.join(dest, "christang-keel-5.1.0.tgz"), "");
    process.stdout.write(JSON.stringify([{ filename: "christang-keel-5.1.0.tgz" }]));
  }
  // FAKE_NPM_LATEST is what `npm view <package> version` prints, and
  // FAKE_NPM_VIEW_EXIT makes it exit with that status instead (#421).
  if (args[0] === "view") {
    if (process.env.FAKE_NPM_VIEW_EXIT) {
      process.stderr.write("npm error code E404\n");
      process.exit(Number(process.env.FAKE_NPM_VIEW_EXIT));
    }
    process.stdout.write(`${process.env.FAKE_NPM_LATEST || "5.1.0"}\n`);
  }
  process.exit(0);
}
const joined = args.join(" ");
if (joined === "plugin list --json") {
  if (host === "claude") {
    process.stdout.write(JSON.stringify([{ id: "keel@keel-marketplace", version,
      installPath: `/fake/claude/cache/keel-marketplace/keel/${version}` }]));
  } else {
    process.stdout.write(JSON.stringify({ installed: [{ pluginId: "keel@keel-marketplace", name: "keel",
      marketplaceName: "keel-marketplace", version, installed: true,
      source: { source: "local", path: process.env.FAKE_CODEX_SOURCE },
      marketplaceSource: { sourceType: process.env.FAKE_CODEX_MARKET_TYPE || "git",
        source: "https://github.com/TanglmChris/keel.git" } }], available: [] }));
  }
  process.exit(0);
}
if (joined === "plugin update keel@keel-marketplace" || joined === "plugin add keel@keel-marketplace") {
  state[host] = "5.1.0";
  save();
  // FAKE_CODEX_CACHE: `plugin add` installs into the plugin cache and deletes
  // the previous version's directory, as Codex does (#412).
  const cache = process.env.FAKE_CODEX_CACHE;
  if (host === "codex" && cache) {
    for (const entry of fs.existsSync(cache) ? fs.readdirSync(cache) : []) {
      fs.rmSync(path.join(cache, entry), { recursive: true, force: true });
    }
    fs.mkdirSync(path.join(cache, "5.1.0", "hooks"), { recursive: true });
    fs.writeFileSync(path.join(cache, "5.1.0", "hooks", "codex.json"), "{}\n");
  }
}
process.exit(0);
"""


# A claude for #424: the Keel plugin, the background sessions `agents --json`
# lists, `stop` (which kills the row's process, as the host does a moment after
# returning), and `--bg --resume`, which records whether the old process was
# still alive when it ran.
ADOPT_FAKE_CLAUDE = r"""const fs = require("fs");
const args = process.argv.slice(2);
const joined = args.join(" ");
const statePath = process.env.FAKE_STATE;
const state = JSON.parse(fs.readFileSync(statePath, "utf8"));
const save = () => fs.writeFileSync(statePath, JSON.stringify(state));
fs.appendFileSync(process.env.FAKE_LOG, JSON.stringify({ args, cwd: process.cwd() }) + "\n");
const alive = (pid) => { try { process.kill(pid, 0); return true; } catch { return false; } };
if (joined === "plugin list --json") {
  process.stdout.write(JSON.stringify([{ id: "keel@keel-marketplace", version: state.version,
    lastUpdated: state.lastUpdated }]));
} else if (joined === "plugin update keel@keel-marketplace") {
  state.version = "5.1.0";
  save();
} else if (joined === "agents --json") {
  process.stdout.write(JSON.stringify(state.rows));
} else if (args[0] === "stop") {
  const row = state.rows.find((item) => item.id === args[1]);
  if (row) {
    setTimeout(() => { try { process.kill(row.pid, "SIGKILL"); } catch {} }, 300);
    delete row.status;
    save();
  }
  process.stdout.write(`stopped ${args[1]}\n`);
  setTimeout(() => process.exit(0), 400);
  return;
} else if (args[0] === "--bg" && args[1] === "--resume") {
  const row = state.rows.find((item) => item.sessionId === args[2]);
  fs.appendFileSync(process.env.FAKE_LOG, JSON.stringify({ resumed: args[2], oldAlive: row ? alive(row.pid) : null }) + "\n");
  if (row) { row.status = "idle"; row.startedAt = Date.now(); save(); }
  process.stdout.write(`backgrounded · ${args[2].slice(0, 8)} · resumed\n`);
}
process.exit(0);
"""


def validate_update_adopts_idle_sessions_scenario() -> int:
    """Issue #424: a release reaches the running background sessions on request.

    Each Claude background session keeps the plugin it loaded. A hand-over starts
    a new process, so it adopts the update; a session that does not change shift
    stays on the old one. Measured on 2026-10-21 (Claude Code 2.1.304), stop and
    resume with no prompt restarts it on the installed plugin without a turn.
    `--adopt` does that for the idle sessions started before the update, and
    leaves busy, guarded, and its own session alone.
    """
    label = "update-adopts-idle-sessions:"
    t0 = 1792540800000  # 2026-10-21T00:00:00Z, the update's lastUpdated
    with tempfile.TemporaryDirectory(prefix="keel-adopt-424-", ignore_cleanup_errors=True) as raw:
        tmp = Path(raw)
        fake = tmp / "fake-claude.js"
        write_text(fake, ADOPT_FAKE_CLAUDE)
        launcher = tmp / "fake-claude"
        write_text(launcher, f'#!/bin/sh\nexec node "{fake}" "$@"\n')
        launcher.chmod(0o755)
        npm_fake = tmp / "fake-npm.js"
        write_text(npm_fake, UPDATE_FAKE)
        npm = tmp / "fake-npm"
        write_text(npm, f'#!/bin/sh\nFAKE_HOST=npm exec node "{npm_fake}" "$@"\n')
        npm.chmod(0o755)
        guarded = tmp / "guarded"
        write_text(guarded / "keel" / "guard.json", "{}\n")
        sleepers: list[int] = []

        def row(name: str, sid: str, status: str, started: int, cwd: Path) -> dict:
            # Not this process's child: a killed child stays a zombie until reaped,
            # and a zombie still answers kill(pid, 0), which a host process never does.
            pid = int(subprocess.run(["sh", "-c", "sleep 300 >/dev/null 2>&1 & echo $!"], text=True,
                                     capture_output=True, check=True).stdout.strip())
            sleepers.append(pid)
            return {"kind": "background", "name": name, "sessionId": sid, "id": sid[:8], "status": status,
                    "state": "working", "pid": pid, "cwd": str(cwd), "startedAt": started}

        def run(*extra: str) -> tuple[subprocess.CompletedProcess, list[dict]]:
            log = tmp / "log.jsonl"
            log.write_text("")
            rows = [
                row("lead · old idle", "aaaaaaaa-0000-0000-0000-000000000001", "idle", t0 - 3600000, tmp),
                row("verify · old busy", "bbbbbbbb-0000-0000-0000-000000000002", "busy", t0 - 3600000, tmp),
                row("rtl · old guarded", "cccccccc-0000-0000-0000-000000000003", "idle", t0 - 3600000, guarded),
                row("pm · fresh idle", "dddddddd-0000-0000-0000-000000000004", "idle", t0 + 3600000, tmp),
                row("maint · this session", "eeeeeeee-0000-0000-0000-000000000005", "busy", t0 - 3600000, tmp),
            ]
            (tmp / "state.json").write_text(json.dumps({"version": "5.0.0", "lastUpdated": "2026-10-21T00:00:00.000Z", "rows": rows}))
            env = dict(os.environ)
            env.update({"KEEL_UPDATE_NPM": str(npm), "KEEL_UPDATE_CLAUDE": str(launcher),
                        "KEEL_UPDATE_CODEX": str(tmp / "no-codex"), "FAKE_LOG": str(log),
                        "FAKE_STATE": str(tmp / "state.json"), "CLAUDE_CODE_SESSION_ID": rows[4]["sessionId"]})
            env.pop("KEEL_UPDATE_SOURCE", None)
            result = subprocess.run(["node", str(ROOT / "bin/keel.js"), "--update", *extra], cwd=tmp, env=env,
                                    text=True, capture_output=True, check=False, timeout=90)
            # The npm fake logs arrays to the same file; the claude fake logs objects.
            entries = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
            return result, [entry for entry in entries if isinstance(entry, dict)]

        try:
            adopted, calls = run("--adopt")
            stops = [c["args"][1] for c in calls if c.get("args", [None])[0] == "stop"]
            resumes = [c for c in calls if c.get("args", [None])[:2] == ["--bg", "--resume"]]
            witnessed = [c for c in calls if "resumed" in c]
            line = next((l for l in adopted.stdout.splitlines() if l.startswith("keel update: claude sessions:")), "")
            if adopted.returncode != 0:
                report(f"{label} keel --update --adopt exited {adopted.returncode}: {adopted.stdout!r} {adopted.stderr!r}")
                return 1
            if stops != ["aaaaaaaa"]:
                report(f"{label} --adopt stopped {stops!r}, not only the idle session started before the update.")
                return 1
            if len(resumes) != 1 or resumes[0]["args"] != ["--bg", "--resume", "aaaaaaaa-0000-0000-0000-000000000001"]:
                report(f"{label} --adopt did not resume the stopped session with exactly `--bg --resume <id>`: {resumes!r}")
                return 1
            if resumes[0]["cwd"] != os.path.realpath(tmp) and resumes[0]["cwd"] != str(tmp):
                report(f"{label} the resume ran in {resumes[0]['cwd']!r}, not the session's worktree {str(tmp)!r}.")
                return 1
            if not witnessed or witnessed[0]["oldAlive"]:
                report(f"{label} the resume ran while the stopped session's process was still alive: {witnessed!r}")
                return 1
            for needle in ("adopted", "lead · old idle", "verify · old busy", "rtl · old guarded"):
                if needle not in line:
                    report(f"{label} the claude sessions line does not name {needle!r}: {line!r}")
                    return 1
            for absent in ("pm · fresh idle", "maint · this session"):
                if absent in line:
                    report(f"{label} the claude sessions line names {absent!r}, which is not on an older plugin or is this session: {line!r}")
                    return 1

            named, calls = run()
            line = next((l for l in named.stdout.splitlines() if l.startswith("keel update: claude sessions:")), "")
            if any(c.get("args", [None])[0] == "stop" or c.get("args", [None])[:2] == ["--bg", "--resume"] for c in calls):
                report(f"{label} keel --update without --adopt stopped or resumed a session: {calls!r}")
                return 1
            for needle in ("lead · old idle", "verify · old busy", "rtl · old guarded", "keel --update --adopt"):
                if needle not in line:
                    report(f"{label} without --adopt the claude sessions line does not name {needle!r}: {line!r}")
                    return 1
        finally:
            for pid in sleepers:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        refused = subprocess.run(["node", str(ROOT / "bin/keel.js"), "--adopt"], cwd=ROOT, text=True,
                                 capture_output=True, check=False)
        if refused.returncode != 2:
            report(f"{label} --adopt outside --update exited {refused.returncode}, not 2: {refused.stderr!r}")
            return 1
    if label.rstrip(":") not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report(f"{label.rstrip(':')} scenario passed.")
    return 0


def validate_update_covers_installed_hosts_scenario() -> int:
    """Issue #204: one owner-run `keel --update` covers every installed component.

    After the CLI, it updates the Claude and Codex plugins through each host's
    own documented commands, and reports one line per component that says what
    changed, when it applies, and what the owner must still do.
    """
    label = "update-covers-installed-hosts:"
    with tempfile.TemporaryDirectory(prefix="keel-update-hosts-", ignore_cleanup_errors=True) as raw:
        tmp = Path(raw)
        fake = tmp / "fake.js"
        write_text(fake, UPDATE_FAKE)
        launchers = {}
        for host in ("npm", "claude", "codex"):
            launcher = tmp / f"fake-{host}"
            write_text(launcher, f'#!/bin/sh\nFAKE_HOST={host} exec node "{fake}" "$@"\n')
            launcher.chmod(0o755)
            launchers[host] = launcher
        codex_home = tmp / "codex-home"
        installed_hooks = codex_home / "plugins/cache/keel-marketplace/keel/5.0.0/hooks/codex.json"
        source = tmp / "codex-source"
        hooks = (ROOT / PLUGIN_ROOT / "hooks/codex.json").read_text(encoding="utf-8")
        write_text(installed_hooks, hooks)
        write_text(source / "hooks/codex.json", hooks)

        def update(*extra: str, env_extra: dict[str, str] | None = None):
            log = tmp / "log.jsonl"
            state = tmp / "state.json"
            for stale in (log, state):
                if stale.exists():
                    stale.unlink()
            log.write_text("")
            env = dict(os.environ)
            env.update({
                "KEEL_UPDATE_NPM": str(launchers["npm"]),
                "KEEL_UPDATE_CLAUDE": str(launchers["claude"]),
                "KEEL_UPDATE_CODEX": str(launchers["codex"]),
                "CODEX_HOME": str(codex_home),
                "FAKE_LOG": str(log), "FAKE_STATE": str(state),
                "FAKE_CODEX_SOURCE": str(source),
            })
            env.pop("KEEL_UPDATE_SOURCE", None)
            env.update(env_extra or {})
            result = subprocess.run(["node", str(ROOT / "bin/keel.js"), "--update", *extra], cwd=tmp, env=env,
                                    text=True, capture_output=True, check=False, timeout=60)
            calls = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
            return result, [c for c in calls if c[1:] != ["plugin", "list", "--json"]]

        def line_for(output: str, component: str) -> str:
            found = [l for l in output.splitlines() if l.startswith(f"keel update: {component}:")]
            return found[0] if len(found) == 1 else ""

        result, calls = update()
        expected = [
            ["npm", "pack"], ["npm", "install", "-g"],
            ["claude", "plugin", "marketplace", "update", "keel-marketplace"],
            ["claude", "plugin", "update", "keel@keel-marketplace"],
            ["codex", "plugin", "marketplace", "upgrade", "keel-marketplace"],
            ["codex", "plugin", "add", "keel@keel-marketplace"],
        ]
        got = [c[:len(e)] for c, e in zip(calls, expected)]
        if result.returncode != 0 or got != expected or len(calls) != len(expected):
            report(f"{label} the update did not run the CLI then each host's commands once, in order: "
                   f"exit={result.returncode} calls={calls!r} stderr={result.stderr!r}")
            return 1
        claude_line = line_for(result.stdout, "claude plugin")
        codex_line = line_for(result.stdout, "codex plugin")
        cli_line = line_for(result.stdout, "cli")
        for name, line, needles in (
            ("cli", cli_line, ["next command"]),
            ("claude plugin", claude_line, ["5.0.0 -> 5.1.0", "next hook call", "/reload-plugins"]),
            ("codex plugin", codex_line, ["5.0.0 -> 5.1.0", "next hook call"]),
        ):
            missing = [n for n in needles if n not in line]
            if not line or missing:
                report(f"{label} the {name} line is missing or lacks {missing!r}: {result.stdout!r}")
                return 1
        if "/hooks" in codex_line:
            report(f"{label} the Codex line asked for hook review with unchanged hooks: {codex_line!r}")
            return 1

        result, calls = update(env_extra={"KEEL_UPDATE_CODEX": str(tmp / "no-such-codex")})
        codex_line = line_for(result.stdout, "codex plugin")
        if result.returncode != 0:
            report(f"{label} a missing Codex failed the update: exit={result.returncode} {result.stdout!r}")
            return 1
        if "absent" not in codex_line:
            report(f"{label} a missing Codex was not reported absent: {codex_line!r}")
            return 1
        if any(c[0] == "codex" for c in calls):
            report(f"{label} a missing Codex still received commands: {calls!r}")
            return 1

        result, calls = update(env_extra={"FAKE_CODEX_MARKET_TYPE": "local"})
        codex_line = line_for(result.stdout, "codex plugin")
        if "manual" not in codex_line:
            report(f"{label} a local Codex marketplace was not reported manual: {codex_line!r}")
            return 1
        if "codex plugin marketplace add TanglmChris/keel --ref main --sparse .agents/plugins --sparse plugins/keel" not in codex_line:
            report(f"{label} the manual Codex line does not name the sparse Git marketplace command (--sparse): {codex_line!r}")
            return 1
        if any(c[0] == "codex" for c in calls):
            report(f"{label} a local Codex marketplace still received commands: {calls!r}")
            return 1

        write_text(source / "hooks/codex.json", hooks.replace('"timeout": 15', '"timeout": 16'))
        result, calls = update()
        write_text(source / "hooks/codex.json", hooks)
        if "/hooks" not in line_for(result.stdout, "codex plugin"):
            report(f"{label} changed Codex hook definitions were not named: {result.stdout!r}")
            return 1

        result, calls = update(env_extra={"FAKE_FAIL_CLAUDE": "plugin update"})
        claude_line = line_for(result.stdout, "claude plugin")
        codex_line = line_for(result.stdout, "codex plugin")
        if result.returncode == 0:
            report(f"{label} a failed Claude update left the exit status 0: {result.stdout!r}")
            return 1
        if "failed" not in claude_line:
            report(f"{label} a failed Claude update was not reported failed: {claude_line!r}")
            return 1
        if "5.0.0 -> 5.1.0" not in codex_line:
            report(f"{label} Codex did not still update after Claude failed: {codex_line!r}")
            return 1

        result, calls = update("--dry-run")
        if result.returncode != 0:
            report(f"{label} --dry-run failed: exit={result.returncode} {result.stderr!r}")
            return 1
        if calls:
            report(f"{label} --dry-run ran commands: {calls!r}")
            return 1
        for planned in ("claude plugin update keel@keel-marketplace", "codex plugin add keel@keel-marketplace"):
            if planned not in result.stdout:
                report(f"{label} --dry-run did not print `{planned}`: {result.stdout!r}")
                return 1

    if "update-covers-installed-hosts" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("update-covers-installed-hosts scenario passed.")
    return 0


def validate_update_registry_lag_scenario() -> int:
    """Issue #421: a version the registry does not serve yet is `pending`.

    Right after a release, the Claude marketplace names the new version while
    the npm registry the machine reaches still serves the old one, and
    `claude plugin update` exits 1 with `E404 No match found for version`.
    A rerun minutes later succeeds, so that is not a failure; any E404 the
    registry's own answer does not explain still is.
    """
    label = "update-registry-lag:"
    e404 = ('✘ Failed to update plugin "keel@keel-marketplace": Could not resolve @christang/keel@5.2.0 '
            "from the npm registry: E404 No match found for version 5.2.0")
    with tempfile.TemporaryDirectory(prefix="keel-update-421-", ignore_cleanup_errors=True) as raw:
        tmp = Path(raw)
        fake = tmp / "fake.js"
        write_text(fake, UPDATE_FAKE)
        launchers = {}
        for host in ("npm", "claude", "codex"):
            launcher = tmp / f"fake-{host}"
            write_text(launcher, f'#!/bin/sh\nFAKE_HOST={host} exec node "{fake}" "$@"\n')
            launcher.chmod(0o755)
            launchers[host] = launcher
        source = tmp / "codex-source"
        write_text(source / "hooks/codex.json", "{}\n")

        def update(env_extra: dict[str, str]):
            log = tmp / "log.jsonl"
            state = tmp / "state.json"
            for stale in (log, state):
                if stale.exists():
                    stale.unlink()
            log.write_text("")
            env = dict(os.environ)
            env.update({
                "KEEL_UPDATE_NPM": str(launchers["npm"]),
                "KEEL_UPDATE_CLAUDE": str(launchers["claude"]),
                "KEEL_UPDATE_CODEX": str(launchers["codex"]),
                "CODEX_HOME": str(tmp / "codex-home"),
                "FAKE_LOG": str(log), "FAKE_STATE": str(state),
                "FAKE_CODEX_SOURCE": str(source),
                "FAKE_FAIL_CLAUDE": "plugin update keel", "FAKE_FAIL_STDERR_CLAUDE": e404,
            })
            env.pop("KEEL_UPDATE_SOURCE", None)
            env.update(env_extra)
            result = subprocess.run(["node", str(ROOT / "bin/keel.js"), "--update"], cwd=tmp, env=env,
                                    text=True, capture_output=True, check=False, timeout=60)
            lines = {}
            for component in ("cli", "claude plugin", "codex plugin"):
                found = [l for l in result.stdout.splitlines() if l.startswith(f"keel update: {component}:")]
                lines[component] = found[0] if len(found) == 1 else ""
            return result, lines

        result, lines = update({"FAKE_NPM_LATEST": "5.1.0"})
        claude = lines["claude plugin"]
        if not claude.startswith("keel update: claude plugin: pending"):
            report(f"{label} a version the registry does not serve yet was not reported pending: {claude!r}")
            return 1
        for needle in ("5.2.0", "5.1.0", "rerun keel --update", "few minutes"):
            if needle not in claude:
                report(f"{label} the pending Claude line does not name {needle!r}: {claude!r}")
                return 1
        if "failed" in claude:
            report(f"{label} the pending Claude line still reads failed: {claude!r}")
            return 1
        if "registry's latest here is 5.1.0" not in lines["cli"]:
            report(f"{label} the CLI line does not name 5.1.0 as the registry's latest: {lines['cli']!r}")
            return 1
        if "5.0.0 -> 5.1.0" not in lines["codex plugin"]:
            report(f"{label} the Codex line did not still update: {lines['codex plugin']!r}")
            return 1
        if result.returncode != 0:
            report(f"{label} a pending Claude plugin failed the update: exit={result.returncode} {result.stdout!r}")
            return 1

        for case, env_extra in (("the registry serves 5.2.0", {"FAKE_NPM_LATEST": "5.2.0"}),
                                ("npm view exits 1", {"FAKE_NPM_VIEW_EXIT": "1"})):
            result, lines = update(env_extra)
            claude = lines["claude plugin"]
            if not claude.startswith("keel update: claude plugin: failed"):
                report(f"{label} when {case}, the Claude line does not read failed: {claude!r}")
                return 1
            if "E404 No match found" not in claude:
                report(f"{label} when {case}, the failed Claude line does not carry the host's E404: {claude!r}")
                return 1
            if result.returncode == 0:
                report(f"{label} when {case}, the update exited 0: {result.stdout!r}")
                return 1

    if "update-registry-lag" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("update-registry-lag scenario passed.")
    return 0


OVERLAY_START_RE = re.compile(r"<!--\s*keel:openspec-surface-overlay version=([^ ]+) -->")


OVERLAY_BLOCK_RE = re.compile(
    r"<!--\s*keel:openspec-surface-overlay(?:\s+[^>]*)?\s*-->[\s\S]*?"
    r"<!--\s*keel:openspec-surface-overlay:end\s*-->"
)


def validate_update_host_query_timeout_scenario() -> int:
    """Issue #354: a hung or failed host query is `failed`, never `absent`.

    `plugin list --json` once hung for minutes through a proxy; every host call
    had five minutes, and a query that failed read as a host with no Keel.
    """
    label = "update-host-query-timeout:"
    with tempfile.TemporaryDirectory(prefix="keel-update-354-", ignore_cleanup_errors=True) as raw:
        tmp = Path(raw)
        fake = tmp / "fake.js"
        write_text(fake, UPDATE_FAKE)
        launchers = {}
        for host in ("npm", "claude", "codex"):
            launcher = tmp / f"fake-{host}"
            write_text(launcher, f'#!/bin/sh\nFAKE_HOST={host} exec node "{fake}" "$@"\n')
            launcher.chmod(0o755)
            launchers[host] = launcher
        source = tmp / "codex-source"
        write_text(source / "hooks/codex.json", "{}\n")

        def update(*extra: str, env_extra: dict[str, str]):
            log = tmp / "log.jsonl"
            state = tmp / "state.json"
            for stale in (log, state):
                if stale.exists():
                    stale.unlink()
            log.write_text("")
            env = dict(os.environ)
            env.update({
                "KEEL_UPDATE_NPM": str(launchers["npm"]),
                "KEEL_UPDATE_CLAUDE": str(launchers["claude"]),
                "KEEL_UPDATE_CODEX": str(launchers["codex"]),
                "KEEL_UPDATE_QUERY_TIMEOUT_MS": "30000",
                "CODEX_HOME": str(tmp / "codex-home"),
                "FAKE_LOG": str(log), "FAKE_STATE": str(state),
                "FAKE_CODEX_SOURCE": str(source),
            })
            env.pop("KEEL_UPDATE_SOURCE", None)
            env.update(env_extra)
            started = time.monotonic()
            result = subprocess.run(["node", str(ROOT / "bin/keel.js"), "--update", *extra], cwd=tmp, env=env,
                                    text=True, capture_output=True, check=False, timeout=120)
            calls = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
            return result, calls, time.monotonic() - started

        def line(output: str, component: str) -> str:
            return next((l for l in output.splitlines() if l.startswith(f"keel update: {component}:")), "")

        result, _, _ = update(env_extra={"FAKE_LIST_EXIT_CLAUDE": "3"})
        claude = line(result.stdout, "claude plugin")
        if "absent" in claude:
            report(f"{label} a claude plugin list --json that exited 3 was reported absent: {claude!r}")
            return 1
        if "failed" not in claude or "exited 3" not in claude:
            report(f"{label} a claude plugin list --json that exited 3 does not read failed with exited 3: {claude!r}")
            return 1

        # Only the hung case needs a short limit; the others keep 30 s, so load cannot trip them.
        result, calls, took = update(env_extra={"FAKE_LIST_SLEEP_CODEX": "15", "KEEL_UPDATE_QUERY_TIMEOUT_MS": "4000"})
        codex = line(result.stdout, "codex plugin")
        if "absent" in codex:
            report(f"{label} a hung codex plugin list --json was reported absent: {codex!r}")
            return 1
        for needle in ("failed", "codex plugin list --json", "4 s"):
            if needle not in codex:
                report(f"{label} the hung-query line does not name {needle!r}: {codex!r}")
                return 1
        if any(c[:4] == ["codex", "plugin", "marketplace", "upgrade"] for c in calls):
            report(f"{label} a Codex update command ran after its query failed: {calls!r}")
            return 1
        if "updated" not in line(result.stdout, "claude plugin"):
            report(f"{label} the Claude line did not still report its update: {result.stdout!r}")
            return 1
        if result.returncode == 0:
            report(f"{label} a failed query left keel --update exiting 0.")
            return 1
        if took > 20:
            report(f"{label} the hung query held keel --update for {took:.1f} s, past two 4 s attempts.")
            return 1

        result, _, _ = update(env_extra={"KEEL_UPDATE_CODEX": str(tmp / "no-such-codex")})
        if "absent" not in line(result.stdout, "codex plugin"):
            report(f"{label} a missing codex executable no longer reads absent: {result.stdout!r}")
            return 1

        result, _, _ = update("--dry-run", env_extra={"FAKE_LIST_SLEEP_CODEX": "15", "KEEL_UPDATE_QUERY_TIMEOUT_MS": "4000"})
        if result.returncode != 0:
            report(f"{label} --dry-run with a hung query exited {result.returncode}: {result.stdout!r}")
            return 1
    report("update-host-query-timeout scenario passed.")
    return 0


def validate_update_codex_from_disk_scenario() -> int:
    """Issue #412: a hung `codex plugin list --json` stopped an update that worked.

    On 2026-10-20 the query hung past 90 s while `codex plugin marketplace
    upgrade` succeeded by hand in 35 s. Codex's own config and plugin cache say
    what the query would have, so the update runs from them; with neither, the
    failure stays a failure (#354), and a local source stays manual.
    """
    label = "update-codex-from-disk:"
    upgrade = ["codex", "plugin", "marketplace", "upgrade", "keel-marketplace"]
    add = ["codex", "plugin", "add", "keel@keel-marketplace"]
    with tempfile.TemporaryDirectory(prefix="keel-update-412-", ignore_cleanup_errors=True) as raw:
        tmp = Path(raw)
        fake = tmp / "fake.js"
        write_text(fake, UPDATE_FAKE)
        launchers = {}
        for host in ("npm", "claude", "codex"):
            launcher = tmp / f"fake-{host}"
            write_text(launcher, f'#!/bin/sh\nFAKE_HOST={host} exec node "{fake}" "$@"\n')
            launcher.chmod(0o755)
            launchers[host] = launcher

        def update(source_type: str | None):
            codex_home = tmp / f"codex-home-{source_type}"
            if codex_home.exists():
                shutil.rmtree(codex_home)
            cache = codex_home / "plugins/cache/keel-marketplace/keel"
            write_text(cache / "5.0.0/hooks/codex.json", "{}\n")
            if source_type:
                write_text(codex_home / "config.toml",
                           "[features]\nx = true\n\n[marketplaces.keel-marketplace]\n"
                           f'source_type = "{source_type}"\n'
                           'source = "https://github.com/TanglmChris/keel.git"\n\n[other]\ny = 1\n')
            log, state = tmp / "log.jsonl", tmp / "state.json"
            for stale in (log, state):
                if stale.exists():
                    stale.unlink()
            log.write_text("")
            env = dict(os.environ)
            env.update({
                "KEEL_UPDATE_NPM": str(launchers["npm"]), "KEEL_UPDATE_CLAUDE": str(launchers["claude"]),
                "KEEL_UPDATE_CODEX": str(launchers["codex"]), "CODEX_HOME": str(codex_home),
                "KEEL_UPDATE_QUERY_TIMEOUT_MS": "2000", "FAKE_LIST_SLEEP_CODEX": "15",
                "FAKE_LOG": str(log), "FAKE_STATE": str(state), "FAKE_CODEX_SOURCE": str(tmp / "codex-source"),
                "FAKE_CODEX_CACHE": str(cache),
            })
            env.pop("KEEL_UPDATE_SOURCE", None)
            result = subprocess.run(["node", str(ROOT / "bin/keel.js"), "--update"], cwd=tmp, env=env,
                                    text=True, capture_output=True, check=False, timeout=120)
            calls = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
            line = next((l for l in result.stdout.splitlines() if l.startswith("keel update: codex plugin:")), "")
            return result, calls, line, cache

        result, calls, line, cache = update("git")
        for args in (upgrade, add):
            runs = sum(1 for c in calls if c[:len(args)] == args)
            if runs != 1:
                report(f"{label} with a git marketplace on disk, {' '.join(args)} ran {runs} time(s), not 1: {line!r}")
                return 1
        for needle in ("5.0.0 -> 5.1.0", "did not answer", str(cache)):
            if needle not in line:
                report(f"{label} the Codex line does not name {needle!r}: {line!r}")
                return 1
        if result.returncode != 0:
            report(f"{label} an update carried from disk exited {result.returncode}: {result.stdout!r}")
            return 1

        _, calls, line, _ = update("local")
        if "manual" not in line:
            report(f"{label} a local marketplace on disk does not read manual: {line!r}")
            return 1
        if any(c[:len(upgrade)] == upgrade for c in calls):
            report(f"{label} a local marketplace on disk was upgraded: {calls!r}")
            return 1

        result, calls, line, _ = update(None)
        if "failed" not in line or "absent" in line:
            report(f"{label} with no config on disk the Codex line does not read failed: {line!r}")
            return 1
        if any(c[:2] == ["codex", "plugin"] and c[2:3] != ["list"] for c in calls):
            report(f"{label} with no config on disk a Codex update command ran: {calls!r}")
            return 1
    if label.rstrip(":") not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report("update-codex-from-disk scenario passed.")
    return 0


def validate_update_claude_refresh_retry_scenario() -> int:
    """Issue #359: the Claude marketplace refresh failed once and passed on a direct retry.

    `keel --update` retries `claude plugin marketplace update` once, as it does
    Codex's refresh, and a step that still fails names the host's last stderr
    line instead of only its exit status.
    """
    label = "update-claude-refresh-retry:"
    refresh = ["claude", "plugin", "marketplace", "update", "keel-marketplace"]
    plugin_update = ["claude", "plugin", "update", "keel@keel-marketplace"]
    with tempfile.TemporaryDirectory(prefix="keel-update-359-", ignore_cleanup_errors=True) as raw:
        tmp = Path(raw)
        fake = tmp / "fake.js"
        write_text(fake, UPDATE_FAKE)
        launchers = {}
        for host in ("npm", "claude", "codex"):
            launcher = tmp / f"fake-{host}"
            write_text(launcher, f'#!/bin/sh\nFAKE_HOST={host} exec node "{fake}" "$@"\n')
            launcher.chmod(0o755)
            launchers[host] = launcher

        def update(fail_on: str, times: str):
            log, state = tmp / "log.jsonl", tmp / "state.json"
            for stale in (log, state):
                if stale.exists():
                    stale.unlink()
            log.write_text("")
            env = dict(os.environ)
            env.update({
                "KEEL_UPDATE_NPM": str(launchers["npm"]), "KEEL_UPDATE_CLAUDE": str(launchers["claude"]),
                "KEEL_UPDATE_CODEX": str(launchers["codex"]), "CODEX_HOME": str(tmp / "codex-home"),
                "FAKE_LOG": str(log), "FAKE_STATE": str(state), "FAKE_CODEX_SOURCE": str(tmp / "codex-source"),
                "FAKE_FAIL_CLAUDE": fail_on, "FAKE_FAIL_TIMES_CLAUDE": times,
            })
            env.pop("KEEL_UPDATE_SOURCE", None)
            result = subprocess.run(["node", str(ROOT / "bin/keel.js"), "--update"], cwd=tmp, env=env,
                                    text=True, capture_output=True, check=False, timeout=60)
            calls = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
            line = [l for l in result.stdout.splitlines() if l.startswith("keel update: claude plugin:")]
            return result, calls, (line[0] if len(line) == 1 else "")

        result, calls, line = update("marketplace update", "1")
        runs = sum(1 for c in calls if c[:5] == refresh)
        if runs != 2:
            report(f"{label} the Claude marketplace update ran {runs} time(s) after one failure, not 2: {calls!r}")
            return 1
        if sum(1 for c in calls if c[:4] == plugin_update) != 1:
            report(f"{label} a refresh that succeeded on retry did not run plugin update once: {calls!r}")
            return 1
        if "5.0.0 -> 5.1.0" not in line:
            report(f"{label} a refresh that succeeded on retry did not report the new version: {line!r}")
            return 1
        if result.returncode != 0:
            report(f"{label} a refresh that succeeded on retry exited {result.returncode}: {result.stdout!r}")
            return 1

        result, calls, line = update("marketplace update", "9")
        runs = sum(1 for c in calls if c[:5] == refresh)
        if runs != 2:
            report(f"{label} a lasting failure ran the marketplace update {runs} time(s), not 2: {calls!r}")
            return 1
        if any(c[:4] == plugin_update for c in calls):
            report(f"{label} a lasting refresh failure still ran plugin update: {calls!r}")
            return 1
        if result.returncode == 0:
            report(f"{label} a lasting refresh failure left the exit status 0: {result.stdout!r}")
            return 1
        for needle in ("failed", "failed twice", "fake claude: refused plugin marketplace update"):
            if needle not in line:
                report(f"{label} the failed Claude line does not name {needle!r}: {line!r}")
                return 1
        if "warming up" in line:
            report(f"{label} the failed Claude line carries more than the last stderr line: {line!r}")
            return 1

        # A step with no retry still names the host's own error, not only its status.
        result, calls, line = update("plugin update keel", "9")
        if sum(1 for c in calls if c[:4] == plugin_update) != 1:
            report(f"{label} a failing plugin update was retried or skipped: {calls!r}")
            return 1
        for needle in ("failed", "exited 1", "fake claude: refused plugin update"):
            if needle not in line:
                report(f"{label} the failed plugin-update line does not name {needle!r}: {line!r}")
                return 1
    if "update-claude-refresh-retry" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("update-claude-refresh-retry scenario passed.")
    return 0


def validate_update_host_query_retry_scenario() -> int:
    """Issue #365: `codex plugin list --json` usually answers in about 1 s and
    sometimes took 58 s through the owner's proxy.

    A query that times out is retried once before the component reads
    `failed`, so one slow spell no longer leaves the plugin a release behind.
    """
    label = "update-host-query-retry:"
    listing = ["codex", "plugin", "list", "--json"]
    with tempfile.TemporaryDirectory(prefix="keel-update-365-", ignore_cleanup_errors=True) as raw:
        tmp = Path(raw)
        fake = tmp / "fake.js"
        write_text(fake, UPDATE_FAKE)
        launchers = {}
        for host in ("npm", "claude", "codex"):
            launcher = tmp / f"fake-{host}"
            write_text(launcher, f'#!/bin/sh\nFAKE_HOST={host} exec node "{fake}" "$@"\n')
            launcher.chmod(0o755)
            launchers[host] = launcher
        source = tmp / "codex-source"
        write_text(source / "hooks/codex.json", "{}\n")

        def update(times: str):
            log, state = tmp / "log.jsonl", tmp / "state.json"
            for stale in (log, state, tmp / "state.json.held-codex"):
                if stale.exists():
                    stale.unlink()
            log.write_text("")
            env = dict(os.environ)
            env.update({
                "KEEL_UPDATE_NPM": str(launchers["npm"]), "KEEL_UPDATE_CLAUDE": str(launchers["claude"]),
                "KEEL_UPDATE_CODEX": str(launchers["codex"]), "KEEL_UPDATE_QUERY_TIMEOUT_MS": "4000",
                "CODEX_HOME": str(tmp / "codex-home"), "FAKE_LOG": str(log), "FAKE_STATE": str(state),
                "FAKE_CODEX_SOURCE": str(source),
                "FAKE_LIST_SLEEP_CODEX": "15", "FAKE_LIST_SLEEP_TIMES_CODEX": times,
            })
            env.pop("KEEL_UPDATE_SOURCE", None)
            started = time.monotonic()
            result = subprocess.run(["node", str(ROOT / "bin/keel.js"), "--update"], cwd=tmp, env=env,
                                    text=True, capture_output=True, check=False, timeout=120)
            calls = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
            line = next((l for l in result.stdout.splitlines() if l.startswith("keel update: codex plugin:")), "")
            return result, calls, line, time.monotonic() - started

        result, calls, line, _ = update("1")
        if "5.0.0 -> 5.1.0" not in line:
            report(f"{label} a query that timed out once did not go on to update the Codex plugin: {line!r}")
            return 1
        if result.returncode != 0:
            report(f"{label} a query that answered on retry left keel --update exiting {result.returncode}: {result.stdout!r}")
            return 1

        result, calls, line, took = update("9")
        for needle in ("failed", "codex plugin list --json", "timed out twice", "4 s"):
            if needle not in line:
                report(f"{label} a lasting hang's line does not name {needle!r}: {line!r}")
                return 1
        runs = sum(1 for c in calls if c[:4] == listing)
        if runs != 2:
            report(f"{label} a lasting hang ran the query {runs} time(s), not 2: {calls!r}")
            return 1
        if took > 25:
            report(f"{label} two 4 s attempts held keel --update for {took:.1f} s.")
            return 1
    if "update-host-query-retry" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("update-host-query-retry scenario passed.")
    return 0


def validate_update_codex_refresh_retry_scenario() -> int:
    """Issue #329: a slow link can cut Codex's whole-repository marketplace clone.

    `keel --update` retries the refresh once, and when it still fails, names the
    sparse marketplace paths that make it fetch only the plugin. Those paths
    hold the Codex catalog and the plugin it names, and the docs use them.
    """
    label = "update-codex-refresh-retry:"
    upgrade = ["codex", "plugin", "marketplace", "upgrade", "keel-marketplace"]
    add = ["codex", "plugin", "add", "keel@keel-marketplace"]
    with tempfile.TemporaryDirectory(prefix="keel-update-retry-", ignore_cleanup_errors=True) as raw:
        tmp = Path(raw)
        fake = tmp / "fake.js"
        write_text(fake, UPDATE_FAKE)
        launchers = {}
        for host in ("npm", "claude", "codex"):
            launcher = tmp / f"fake-{host}"
            write_text(launcher, f'#!/bin/sh\nFAKE_HOST={host} exec node "{fake}" "$@"\n')
            launcher.chmod(0o755)
            launchers[host] = launcher

        def update(times: str):
            log, state = tmp / "log.jsonl", tmp / "state.json"
            for stale in (log, state):
                if stale.exists():
                    stale.unlink()
            log.write_text("")
            env = dict(os.environ)
            env.update({
                "KEEL_UPDATE_NPM": str(launchers["npm"]), "KEEL_UPDATE_CLAUDE": str(launchers["claude"]),
                "KEEL_UPDATE_CODEX": str(launchers["codex"]), "CODEX_HOME": str(tmp / "codex-home"),
                "FAKE_LOG": str(log), "FAKE_STATE": str(state), "FAKE_CODEX_SOURCE": str(tmp / "codex-source"),
                "FAKE_FAIL_CODEX": "marketplace upgrade", "FAKE_FAIL_TIMES_CODEX": times,
            })
            env.pop("KEEL_UPDATE_SOURCE", None)
            result = subprocess.run(["node", str(ROOT / "bin/keel.js"), "--update"], cwd=tmp, env=env,
                                    text=True, capture_output=True, check=False, timeout=60)
            calls = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
            line = [l for l in result.stdout.splitlines() if l.startswith("keel update: codex plugin:")]
            return result, calls, (line[0] if len(line) == 1 else "")

        result, calls, line = update("1")
        runs = sum(1 for c in calls if c[:5] == upgrade)
        if runs != 2:
            report(f"{label} the Codex marketplace upgrade ran {runs} time(s) after one failure, not 2: {calls!r}")
            return 1
        if sum(1 for c in calls if c[:4] == add) != 1:
            report(f"{label} a refresh that succeeded on retry did not run plugin add once: {calls!r}")
            return 1
        if "5.0.0 -> 5.1.0" not in line:
            report(f"{label} a refresh that succeeded on retry did not report the new version: {line!r}")
            return 1
        if result.returncode != 0:
            report(f"{label} a refresh that succeeded on retry exited {result.returncode}: {result.stdout!r}")
            return 1

        result, calls, line = update("9")
        runs = sum(1 for c in calls if c[:5] == upgrade)
        if runs != 2:
            report(f"{label} a lasting failure ran the upgrade {runs} time(s), not 2: {calls!r}")
            return 1
        if any(c[:4] == add for c in calls):
            report(f"{label} a lasting refresh failure still ran plugin add: {calls!r}")
            return 1
        if result.returncode == 0:
            report(f"{label} a lasting refresh failure left the exit status 0: {result.stdout!r}")
            return 1
        if "failed" not in line:
            report(f"{label} a lasting refresh failure was not reported failed: {line!r}")
            return 1
        for needle in ("sparse_paths", ".agents/plugins", "plugins/keel"):
            if needle not in line:
                report(f"{label} the failed Codex line does not name {needle}: {line!r}")
                return 1

    catalog = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    paths = [entry["source"]["path"] for entry in catalog["plugins"] if entry["name"] == "keel"]
    if paths != ["./plugins/keel"]:
        report(f"{label} the Codex catalog's keel source is not under the sparse path plugins/keel: {paths!r}")
        return 1
    for relative in ("README.md", "README.zh-CN.md", "docs/updating.md"):
        if "--sparse .agents/plugins --sparse plugins/keel" not in (ROOT / relative).read_text(encoding="utf-8"):
            report(f"{label} {relative} does not add the Codex marketplace sparse.")
            return 1
    if "update-codex-refresh-retry" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("update-codex-refresh-retry scenario passed.")
    return 0


def validate_refresh_covers_every_target_scenario() -> int:
    """Issue #204: a protocol refresh brings every installed target forward.

    Each project's own session refreshes its protocol, usually through the one
    target that session runs on. A refresh that touched only that target left
    another target's overlays at an old version (TanglmChris/rtl_ppa_prj, Codex
    at 5.84.0 after a Claude refresh to 5.88.0), and doctor called them
    missing, which sends the reader looking for files that are there.
    """
    label = "refresh-covers-every-target:"
    version = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]
    with tempfile.TemporaryDirectory(prefix="keel-refresh-targets-", ignore_cleanup_errors=True) as raw:
        repo = Path(raw) / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        # `--install` per target after both inits, because before this change
        # `--init --target codex` rewrote Claude's surfaces through OpenSpec and
        # put back only Codex's overlays.
        for action, target in (("--init", "claude"), ("--init", "codex"),
                               ("--install", "claude"), ("--install", "codex")):
            setup = run_keel(repo, action, "--target", target)
            if setup.returncode != 0:
                report(f"{label} {action} --target {target} failed: {setup.stdout}{setup.stderr}")
                return 1
        surfaces = sorted(
            [p for p in (repo / ".claude").rglob("*.md") if OVERLAY_START_RE.search(p.read_text(encoding="utf-8"))]
            + [p for p in (repo / ".agents/skills").rglob("SKILL.md")
               if OVERLAY_START_RE.search(p.read_text(encoding="utf-8"))]
        )
        codex = [p for p in surfaces if ".agents" in p.parts]
        if not codex or len(codex) == len(surfaces):
            report(f"{label} the fixture does not carry overlays on both targets: {surfaces!r}")
            return 1
        bodies = {}
        for surface in surfaces:
            text = OVERLAY_START_RE.sub("<!-- keel:openspec-surface-overlay version=5.0.0 -->",
                                        surface.read_text(encoding="utf-8"))
            surface.write_text(text, encoding="utf-8")
            bodies[surface] = OVERLAY_BLOCK_RE.sub("", text)

        doctor = run_keel(repo, "--doctor", "--target", "claude")
        codex_line = next((l for l in doctor.stdout.splitlines() if l.startswith("Codex Keel")), "")
        if "stale" not in codex_line:
            report(f"{label} doctor did not report the old Codex overlays stale: {codex_line!r}")
            return 1
        if "missing" in codex_line:
            report(f"{label} doctor called present Codex overlays missing: {codex_line!r}")
            return 1
        if "keel --install" not in codex_line:
            report(f"{label} doctor's stale Codex line names no refresh command: {codex_line!r}")
            return 1

        refresh = run_keel(repo, "--install", "--target", "claude")
        if refresh.returncode != 0:
            report(f"{label} --install --target claude failed: {refresh.stdout}{refresh.stderr}")
            return 1
        for surface in surfaces:
            text = surface.read_text(encoding="utf-8")
            versions = OVERLAY_START_RE.findall(text)
            if versions != [version]:
                report(f"{label} {surface.relative_to(repo)} carries overlay versions {versions!r} "
                       f"after a Claude refresh, not one at {version}.")
                return 1
            if OVERLAY_BLOCK_RE.sub("", text) != bodies[surface]:
                report(f"{label} the refresh changed upstream content in {surface.relative_to(repo)}.")
                return 1

    with tempfile.TemporaryDirectory(prefix="keel-refresh-one-target-", ignore_cleanup_errors=True) as raw:
        repo = Path(raw) / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        run_keel(repo, "--init", "--target", "claude")
        refresh = run_keel(repo, "--install", "--target", "claude")
        created = [name for name in (".agents", ".opencode", ".codex") if (repo / name).exists()]
        if refresh.returncode != 0 or created:
            report(f"{label} a Claude-only repository gained {created!r} from a refresh "
                   f"(exit {refresh.returncode}).")
            return 1

    if "refresh-covers-every-target" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("refresh-covers-every-target scenario passed.")
    return 0


def npm_pack_paths() -> set[str]:
    npm = "npm.cmd" if os.name == "nt" else "npm"
    packed = subprocess.run([npm, "pack", "--dry-run", "--json"], cwd=ROOT, text=True,
                            capture_output=True, check=True)
    return {entry["path"] for entry in json.loads(packed.stdout)[0]["files"]}


def png_side(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def validate_directory_tree_is_the_package_renamed_scenario() -> int:
    """Issue #175: the directory sees the npm package, named keel-openspec.

    The name `keel` belongs to another directory listing, and the whole
    repository was too large to be scanned. The directory tree is therefore the
    files the npm package publishes plus a manifest renamed for the directory
    and an icon, while the repository's own manifest keeps `keel`.
    """
    label = "directory-tree-is-the-package-renamed:"
    script = ROOT / "scripts/directory_tree.js"
    if not script.is_file():
        report(f"{label} scripts/directory_tree.js does not exist.")
        return 1
    with tempfile.TemporaryDirectory(prefix="keel-directory-tree-", ignore_cleanup_errors=True) as raw:
        tree = Path(raw) / "tree"
        built = subprocess.run(["node", str(script), str(tree)], cwd=ROOT, text=True,
                               capture_output=True, check=False)
        if built.returncode != 0:
            report(f"{label} the build failed: {built.stdout}{built.stderr}")
            return 1
        files = {p.relative_to(tree).as_posix() for p in tree.rglob("*") if p.is_file()}
        runtime_scripts = {"scripts/run_python.js", "scripts/install_to_repo.py"}
        expected = {p for p in npm_pack_paths() if not p.startswith("scripts/") or p in runtime_scripts}
        expected |= {".claude-plugin/plugin.json", ".claude-plugin/icon.png"}
        if files != expected:
            report(f"{label} the tree is not the npm package less development scripts, plus the "
                   f"manifest and icon: extra={sorted(files - expected)!r} missing={sorted(expected - files)!r}")
            return 1
        root_manifest = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        manifest = json.loads((tree / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        if manifest.get("name") != "keel-openspec":
            report(f"{label} the tree manifest is named {manifest.get('name')!r}, not keel-openspec.")
            return 1
        if manifest.get("homepage") != "https://github.com/TanglmChris/keel":
            report(f"{label} the tree manifest's homepage is {manifest.get('homepage')!r}.")
            return 1
        policy = "https://github.com/TanglmChris/keel/blob/main/PRIVACY.md"
        if manifest.get("privacyPolicyUrl") != policy:
            report(f"{label} the tree manifest's privacyPolicyUrl is {manifest.get('privacyPolicyUrl')!r}, not {policy}.")
            return 1
        if not (ROOT / "PRIVACY.md").is_file():
            report(f"{label} the privacyPolicyUrl names PRIVACY.md, which the repository does not have.")
            return 1
        added = ("name", "homepage", "privacyPolicyUrl")
        renamed = {k: v for k, v in manifest.items() if k not in added}
        if renamed != {k: v for k, v in root_manifest.items() if k not in added}:
            report(f"{label} the tree manifest differs from the root manifest beyond name, homepage, and privacyPolicyUrl.")
            return 1
        version = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]
        cli = subprocess.run(["node", str(tree / "bin/keel.js"), "--version"], text=True,
                             capture_output=True, check=False)
        if cli.returncode != 0:
            report(f"{label} the tree's CLI does not run: exit={cli.returncode} {cli.stderr}")
            return 1
        if version not in cli.stdout:
            report(f"{label} the tree's CLI reports {cli.stdout.strip()!r}, not {version}.")
            return 1
        consumer = Path(raw) / "consumer"
        consumer.mkdir()
        subprocess.run(["git", "init", "-q", str(consumer)], check=True)
        install = subprocess.run(["node", str(tree / "bin/keel.js"), "--install", "--target", "claude",
                                  "--dry-run"], cwd=consumer, text=True, capture_output=True, check=False)
        if install.returncode != 0:
            report(f"{label} the tree's CLI cannot plan an install: exit={install.returncode} "
                   f"{install.stdout[-400:]}{install.stderr[-400:]}")
            return 1
        if root_manifest.get("name") != "keel":
            report(f"{label} the repository's root manifest no longer names keel: {root_manifest.get('name')!r}")
            return 1
        declared = list(manifest.get("skills", [])) + list(manifest.get("agents", []))
        for event in manifest.get("hooks", {}).values():
            for group in event:
                for hook in group.get("hooks", []):
                    declared += [a.replace("${CLAUDE_PLUGIN_ROOT}/", "./") for a in hook.get("args", [])
                                 if "${CLAUDE_PLUGIN_ROOT}" in a]
        unresolved = [d for d in declared if not (tree / d).exists()]
        if unresolved:
            report(f"{label} manifest paths do not resolve inside the tree: {unresolved!r}")
            return 1
        icon = tree / ".claude-plugin/icon.png"
        side = png_side(icon)
        if side is None or side[0] != side[1] or not 512 <= side[0] <= 2048:
            report(f"{label} the icon is not a square PNG between 512 and 2048 px: {side!r}")
            return 1
        if icon.stat().st_size >= 2 * 1024 * 1024:
            report(f"{label} the icon is {icon.stat().st_size} bytes, not under 2 MB.")
            return 1
        again = subprocess.run(["node", str(script), str(tree)], cwd=ROOT, text=True,
                               capture_output=True, check=False)
        if again.returncode == 0:
            report(f"{label} a build into a non-empty directory succeeded.")
            return 1

    if "directory-tree-is-the-package-renamed" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("directory-tree-is-the-package-renamed scenario passed.")
    return 0


def validate_directory_branch_advances_scenario() -> int:
    """Issue #175: each release advances the branch the directory tracks.

    The directory follows a branch rather than a pinned commit, so the release
    job commits the directory tree to `claude-directory` and pushes it. A run
    with nothing new commits nothing, so a re-run of a release adds no noise.
    """
    label = "directory-branch-advances:"
    script = ROOT / "scripts/directory_branch.js"
    if not script.is_file():
        report(f"{label} scripts/directory_branch.js does not exist.")
        return 1
    sha = "a" * 40
    with tempfile.TemporaryDirectory(prefix="keel-directory-branch-", ignore_cleanup_errors=True) as raw:
        base = Path(raw)
        origin = base / "origin.git"
        work = base / "work"
        subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True)
        write_text(work / "README.md", "scratch\n")
        git = lambda *a: subprocess.run(["git", "-C", str(work), *a], text=True, capture_output=True, check=False)
        git("add", "-A")
        git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "init")
        git("remote", "add", "origin", str(origin))
        git("push", "-q", "origin", "main")

        def run(*extra: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(["node", str(script), "9.9.9", sha, *extra], cwd=work, text=True,
                                  capture_output=True, check=False, timeout=180)

        def branch_head() -> str:
            out = subprocess.run(["git", "-C", str(origin), "rev-parse", "--verify", "-q",
                                  "refs/heads/claude-directory"], text=True, capture_output=True)
            return out.stdout.strip()

        first = run()
        head = branch_head()
        if first.returncode != 0 or not head:
            report(f"{label} the first run did not create origin's claude-directory: "
                   f"exit={first.returncode} {first.stdout}{first.stderr}")
            return 1
        if head not in first.stdout:
            report(f"{label} the run did not print the commit it pushed ({head}): {first.stdout!r}")
            return 1
        show = lambda ref, path: subprocess.run(["git", "-C", str(origin), "show", f"{ref}:{path}"],
                                                text=True, capture_output=True).stdout
        message = subprocess.run(["git", "-C", str(origin), "log", "-1", "--format=%s", head],
                                 text=True, capture_output=True).stdout
        if "9.9.9" not in message or sha not in message:
            report(f"{label} the commit message does not name the version and sha: {message!r}")
            return 1
        if json.loads(show(head, ".claude-plugin/plugin.json") or "{}").get("name") != "keel-openspec":
            report(f"{label} the branch manifest does not name keel-openspec.")
            return 1
        listed = set(subprocess.run(["git", "-C", str(origin), "ls-tree", "-r", "--name-only", head],
                                    text=True, capture_output=True).stdout.split())
        reference = base / "reference"
        subprocess.run(["node", str(ROOT / "scripts/directory_tree.js"), str(reference)], check=True,
                       capture_output=True)
        built = {p.relative_to(reference).as_posix() for p in reference.rglob("*") if p.is_file()}
        if listed != built:
            report(f"{label} the branch files differ from a directory_tree.js build: "
                   f"extra={sorted(listed - built)!r} missing={sorted(built - listed)!r}")
            return 1

        second = run()
        if second.returncode != 0 or branch_head() != head:
            report(f"{label} a run with an unchanged tree moved the branch: "
                   f"exit={second.returncode} head={branch_head()} was {head}")
            return 1

        changed = base / "changed"
        shutil.copytree(reference, changed)
        write_text(changed / "README.md", (changed / "README.md").read_text(encoding="utf-8") + "\nplanted\n")
        third = run("--tree", str(changed))
        new_head = branch_head()
        parent = subprocess.run(["git", "-C", str(origin), "rev-parse", f"{new_head}^"],
                                text=True, capture_output=True).stdout.strip()
        if third.returncode != 0 or new_head == head or parent != head:
            report(f"{label} a changed package did not add exactly one commit on top: "
                   f"exit={third.returncode} new={new_head} parent={parent} was {head}")
            return 1

    if "directory-branch-advances" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("directory-branch-advances scenario passed.")
    return 0


def validate_release_notes_name_the_directory_branch_scenario() -> int:
    """Issue #175: the release step advances the branch and names its commit.

    The step replaces the pinned "Official directory entry", which described a
    commit the directory no longer reads.
    """
    label = "release-notes-name-the-directory-branch:"
    workflow = (ROOT / ".github/workflows/publish.yml").read_text(encoding="utf-8")
    start = workflow.find("- name: Tag and release the landed version")
    if start < 0:
        report(f"{label} the release step is missing from publish.yml.")
        return 1
    following = workflow.find("\n      - name:", start + 1)
    step = workflow[start:] if following < 0 else workflow[start:following]
    if 'node scripts/directory_branch.js "$VERSION" "$SHA"' not in step:
        report(f"{label} the release step does not run scripts/directory_branch.js for the version and sha.")
        return 1
    for needle in ("keel-openspec", "claude-directory"):
        if needle not in step:
            report(f"{label} the release notes written by the step do not name {needle}.")
            return 1
    if "official_entry.js" in workflow:
        report(f"{label} publish.yml still references official_entry.js.")
        return 1
    if (ROOT / "scripts/official_entry.js").exists():
        report(f"{label} scripts/official_entry.js still exists.")
        return 1
    if "release-notes-name-the-directory-branch" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("release-notes-name-the-directory-branch scenario passed.")
    return 0


def stage_claude_market_under_test(tmp: Path) -> tuple[Path, str, str] | str:
    """A Claude marketplace that installs this tree's npm package, not npm's.

    The committed entry installs `@christang/keel` from npm at this release's
    version, which is not published until the release lands, and a published
    version installs npm's copy and tests nothing here. An npm source also
    refuses a local folder or `file:` package (#337). So an install smoke packs
    this tree with `npm pack`, unpacks the tarball — exactly the files the
    package publishes — and serves it as a scratch git repository behind a copy
    of the committed entry whose source points at it and whose other fields are
    unchanged. The host then copies it and installs its dependencies as it
    would from npm; only the transport differs. A sentinel only the staged
    package carries lets the caller prove which copy was installed. Returns the
    marketplace directory, its name, and the sentinel, or a failure message.
    """
    git = shutil.which("git")
    npm = shutil.which("npm")
    if git is None or npm is None:
        return "needs git and npm to stage the package under test."
    packs = tmp / "packed"
    packs.mkdir(parents=True, exist_ok=True)
    packed = subprocess.run(
        [npm, "pack", "--json", "--pack-destination", str(packs)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    try:
        tarball = packs / json.loads(packed.stdout)[0]["filename"]
    except (ValueError, KeyError, IndexError):
        return "npm pack failed: " + (packed.stderr or packed.stdout).strip()[:400]
    with tarfile.open(tarball) as archive:
        archive.extractall(packs, filter="data")
    staged = packs / "package"
    sentinel = ".keel-package-under-test"
    write_text(staged / sentinel, "\n")
    committed = json.loads(
        (ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8")
    )
    entry = next(
        (e for e in committed.get("plugins", []) if e.get("name") == "keel"), None
    )
    if not isinstance((entry or {}).get("source"), dict):
        return f"the committed Claude entry has no source object: {entry!r}"
    identity = ["-c", "user.name=keel", "-c", "user.email=keel@invalid"]
    for args in (
        ["init", "-q"],
        ["add", "-A"],
        [*identity, "commit", "-q", "-m", "package under test"],
    ):
        done = subprocess.run(
            [git, *args], cwd=staged, capture_output=True, text=True, check=False
        )
        if done.returncode != 0:
            return f"git {args[-1]} failed staging the package: {done.stderr.strip()}"
    entry["source"] = {"source": "url", "url": staged.resolve().as_uri()}
    market = tmp / "claude-market"
    write_text(
        market / ".claude-plugin/marketplace.json",
        json.dumps(committed, indent=2) + "\n",
    )
    return market, committed["name"], sentinel


def shrinkwrap_openspec_version() -> str | None:
    """The OpenSpec version the committed lockfile pins."""
    lock = json.loads((ROOT / "npm-shrinkwrap.json").read_text(encoding="utf-8"))
    return (
        lock.get("packages", {})
        .get("node_modules/@fission-ai/openspec", {})
        .get("version")
    )


def installed_elsewhere(config: Path, market_name: str, sentinel: str) -> list | None:
    """None when Keel was installed from the package under test, else the paths."""
    installed = json.loads(
        (config / "plugins/installed_plugins.json").read_text(encoding="utf-8")
    )
    paths = [
        record.get("installPath", "")
        for record in installed.get("plugins", {}).get(f"keel@{market_name}", [])
    ]
    return None if any((Path(p) / sentinel).is_file() for p in paths) else paths


# Issue #164: project setup declares Claude plugin auto-update. Claude reads a
# marketplace's auto-update first from `autoUpdate` on its
# `extraKnownMarketplaces` entry in any settings file, and defaults it off for
# every marketplace that is not Anthropic's own.
KEEL_MARKETPLACE_NAME = "keel-marketplace"


KEEL_MARKETPLACE_ENTRY = {
    "source": {"source": "github", "repo": "TanglmChris/keel"},
    "autoUpdate": True,
}


AUTO_UPDATE_LABEL = "init-declares-plugin-auto-update"


def _settings(repo: Path) -> dict | None:
    path = repo / ".claude/settings.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _marketplace_entry(repo: Path) -> dict | None:
    settings = _settings(repo) or {}
    return (settings.get("extraKnownMarketplaces") or {}).get(KEEL_MARKETPLACE_NAME)


def _auto_update_m1(tmp: Path) -> str | None:
    repo = tmp / "fresh"
    repo.mkdir()
    init = run_keel(repo, "--init", "--target", "claude")
    if init.returncode != 0:
        return f"M1 keel --init failed: {(init.stderr or init.stdout).strip()}"
    entry = _marketplace_entry(repo)
    if entry != KEEL_MARKETPLACE_ENTRY:
        return (
            f"M1 keel --init declared no plugin auto-update: {KEEL_MARKETPLACE_NAME} "
            f"in .claude/settings.json is {entry!r}, expected "
            f"{KEEL_MARKETPLACE_ENTRY!r}"
        )
    return None


def _auto_update_m2(tmp: Path) -> str | None:
    permissions = {"allow": ["Bash(git:*)"]}
    local_source = {"source": "directory", "path": "/somewhere/keel"}
    cases = {
        "permissions-only": ({"permissions": permissions}, None),
        "own-source": (
            {"extraKnownMarketplaces": {KEEL_MARKETPLACE_NAME: {"source": local_source}}},
            {"source": local_source, "autoUpdate": True},
        ),
        "declared-off": (
            {
                "extraKnownMarketplaces": {
                    KEEL_MARKETPLACE_NAME: {**KEEL_MARKETPLACE_ENTRY, "autoUpdate": False}
                }
            },
            {**KEEL_MARKETPLACE_ENTRY, "autoUpdate": False},
        ),
    }
    for name, (existing, expected) in cases.items():
        repo = tmp / name
        write_text(repo / ".claude/settings.json", json.dumps(existing, indent=2) + "\n")
        installed = run_keel(repo, "--install", "--target", "claude")
        if installed.returncode != 0:
            return f"M2 {name} keel --install failed: {(installed.stderr or installed.stdout).strip()}"
        settings = _settings(repo) or {}
        want = expected if expected is not None else KEEL_MARKETPLACE_ENTRY
        if _marketplace_entry(repo) != want:
            return (
                f"M2 {name}: install did not merge into an existing "
                f".claude/settings.json as declared; entry is "
                f"{_marketplace_entry(repo)!r}, expected {want!r}"
            )
        if name == "permissions-only" and settings.get("permissions") != permissions:
            return (
                f"M2 {name}: the merge into an existing .claude/settings.json "
                f"lost what the project wrote: {settings!r}"
            )
        again = run_keel(repo, "--install", "--target", "claude")
        if "skip .claude/settings.json" not in (again.stdout or ""):
            return (
                f"M2 {name}: a second install did not skip the merge into an "
                f"existing .claude/settings.json: {again.stdout!r}"
            )
    return None


def _auto_update_m3(tmp: Path) -> str | None:
    permissions = {"allow": ["Bash(git:*)"]}
    ours = tmp / "uninstall-ours"
    write_text(
        ours / ".claude/settings.json",
        json.dumps(
            {
                "permissions": permissions,
                "extraKnownMarketplaces": {KEEL_MARKETPLACE_NAME: KEEL_MARKETPLACE_ENTRY},
            },
            indent=2,
        )
        + "\n",
    )
    run_keel(ours, "--uninstall", "--target", "claude")
    settings = _settings(ours) or {}
    if _marketplace_entry(ours) is not None:
        return f"M3 uninstall left Keel's own marketplace entry behind: {settings!r}"
    if settings.get("permissions") != permissions:
        return f"M3 uninstall left the file without the project's permissions: {settings!r}"
    changed = {**KEEL_MARKETPLACE_ENTRY, "autoUpdate": False}
    theirs = tmp / "uninstall-theirs"
    write_text(
        theirs / ".claude/settings.json",
        json.dumps({"extraKnownMarketplaces": {KEEL_MARKETPLACE_NAME: changed}}, indent=2)
        + "\n",
    )
    run_keel(theirs, "--uninstall", "--target", "claude")
    if _marketplace_entry(theirs) != changed:
        return (
            "M3 uninstall left the file without the entry the project changed; "
            f"it removed what Keel did not write: {_settings(theirs)!r}"
        )
    return None


def _auto_update_m4(tmp: Path) -> str | None:
    states = {
        "on": (KEEL_MARKETPLACE_ENTRY, "plugin auto-update: ok"),
        "off": ({**KEEL_MARKETPLACE_ENTRY, "autoUpdate": False}, "plugin auto-update: manual"),
        "absent": (None, "plugin auto-update: manual"),
    }
    for name, (entry, prefix) in states.items():
        repo = tmp / f"doctor-{name}"
        settings = {"extraKnownMarketplaces": {KEEL_MARKETPLACE_NAME: entry}} if entry else {}
        write_text(repo / ".claude/settings.json", json.dumps(settings) + "\n")
        doctor = run_keel(repo, "--doctor", "--target", "claude")
        lines = [
            line
            for line in (doctor.stdout or "").splitlines()
            if line.startswith("plugin auto-update:")
        ]
        if len(lines) != 1:
            return f"M4 {name}: doctor printed no plugin auto-update line: {lines!r}"
        line = lines[0]
        if not line.startswith(prefix):
            return f"M4 {name}: doctor's plugin auto-update line is not {prefix!r}: {line!r}"
        if name == "off" and "false" not in line:
            return f"M4 off: the line does not name the project's false: {line!r}"
        if name == "absent" and "keel --install --target claude" not in line:
            return f"M4 absent: the line does not name the command that declares it: {line!r}"
    return None


def _auto_update_m5(tmp: Path) -> str | None:
    repo = tmp / "codex"
    repo.mkdir()
    run_keel(repo, "--init", "--target", "codex")
    if (repo / ".claude/settings.json").exists():
        return (
            "M5 keel --init --target codex wrote .claude/settings.json for codex: "
            f"{_settings(repo)!r}"
        )
    return None


def validate_init_declares_plugin_auto_update_scenario() -> int:
    with tempfile.TemporaryDirectory(
        prefix="keel-auto-update-", ignore_cleanup_errors=True
    ) as raw:
        tmp = Path(raw)
        for check in (
            _auto_update_m1,
            _auto_update_m2,
            _auto_update_m3,
            _auto_update_m4,
            _auto_update_m5,
        ):
            problem = check(tmp)
            if problem:
                report(f"{AUTO_UPDATE_LABEL} {problem}")
                return 1
    report(f"{AUTO_UPDATE_LABEL} scenario passed.")
    return 0


# Issue #164: the managed protocol block is the one piece of a release that a
# plugin update cannot carry, so `keel context` names its refresh, and a
# standing `protocol-refresh` lets the agent run it without asking.
PROTOCOL_REFRESH_LABEL = "context-names-the-protocol-refresh"


def _installed_repo(tmp: Path, name: str, target: str, stamp: str) -> Path:
    repo = tmp / name
    repo.mkdir()
    installed = run_keel(repo, "--install", "--target", target)
    if installed.returncode != 0:
        raise RuntimeError((installed.stderr or installed.stdout).strip())
    agents = repo / "AGENTS.md"
    text = agents.read_text(encoding="utf-8")
    agents.write_text(
        re.sub(r"<!-- keel:start version=[0-9.]+ -->", f"<!-- keel:start version={stamp} -->", text, count=1),
        encoding="utf-8",
    )
    return repo


def _protocol_lines(repo: Path) -> list[str]:
    result = run_keel(repo, "context")
    return [line for line in (result.stdout or "").splitlines() if line.startswith("Protocol:")]


def _protocol_json(repo: Path):
    result = run_keel(repo, "context", "--json")
    try:
        return json.loads(result.stdout).get("protocol")
    except ValueError:
        return "unparseable"


def _protocol_refresh_m1(tmp: Path) -> str | None:
    repo = _installed_repo(tmp, "older", "claude", "5.0.0")
    lines = _protocol_lines(repo)
    if len(lines) != 1:
        return f"M1 context printed no Protocol line for a 5.0.0 stamp under Keel {PACKAGE_VERSION}: {lines!r}"
    line = lines[0]
    for needle in ("5.0.0", PACKAGE_VERSION, "keel --install --target claude", "ask"):
        if needle not in line:
            return f"M1 context printed no Protocol line carrying {needle!r}: {line!r}"
    found = _protocol_json(repo)
    if not isinstance(found, dict) or found.get("stamped") != "5.0.0":
        return f"M1 context printed no Protocol line in its JSON result: protocol is {found!r}"
    return None


def _protocol_refresh_m2(tmp: Path) -> str | None:
    repo = _installed_repo(tmp, "authorized", "claude", "5.0.0")
    write_text(repo / "keel/config.yaml", "authorize:\n  - protocol-refresh\n")
    lines = _protocol_lines(repo)
    if len(lines) != 1 or "standing-authorized" not in lines[0]:
        return f"M2 context did not read protocol-refresh as authorized: {lines!r}"
    # Issue #238: the authorization covers the refresh, not its commit.
    if "committing it is a separate action" not in lines[0]:
        return f"M2 context does not say committing the refresh is a separate action: {lines!r}"
    doctor = run_keel(repo, "--doctor").stdout or ""
    if "protocol-refresh: authorized" not in doctor or "commit: not authorized" not in doctor:
        return (
            "M2 doctor did not read protocol-refresh as authorized alone: "
            + repr([l for l in doctor.splitlines() if "authoriz" in l])
        )
    return None


def _protocol_refresh_m3(tmp: Path) -> str | None:
    repo = _installed_repo(tmp, "guarded", "claude", "5.0.0")
    write_text(repo / "keel/config.yaml", "authorize:\n  - protocol-refresh\n")
    write_text(repo / "keel/guard.json", "{}\n")
    lines = _protocol_lines(repo)
    if len(lines) != 1 or "deferred" not in lines[0] or "write guard" not in lines[0]:
        return f"M3 the refresh was not deferred while a write guard is active: {lines!r}"
    return None


def _protocol_refresh_m4(tmp: Path) -> str | None:
    repo = _installed_repo(tmp, "newer", "claude", "99.0.0")
    for where, target in (("a 99.0.0 stamp", repo), ("Keel's own source repository", ROOT)):
        lines = _protocol_lines(target)
        found = _protocol_json(target)
        if lines or found is not None:
            return (
                f"M4 context offered a refresh for a protocol that is not older ({where}): "
                f"{lines!r}, json {found!r}"
            )
    return None


def _protocol_refresh_m5(tmp: Path) -> str | None:
    repo = _installed_repo(tmp, "codex", "codex", "5.0.0")
    lines = _protocol_lines(repo)
    if len(lines) != 1 or "keel --install --target codex" not in lines[0]:
        return f"M5 context named the wrong target for a Codex repository: {lines!r}"
    return None


def validate_context_names_the_protocol_refresh_scenario() -> int:
    with tempfile.TemporaryDirectory(
        prefix="keel-protocol-refresh-", ignore_cleanup_errors=True
    ) as raw:
        tmp = Path(raw)
        for check in (
            _protocol_refresh_m1,
            _protocol_refresh_m2,
            _protocol_refresh_m3,
            _protocol_refresh_m4,
            _protocol_refresh_m5,
        ):
            problem = check(tmp)
            if problem:
                report(f"{PROTOCOL_REFRESH_LABEL} {problem}")
                return 1
    report(f"{PROTOCOL_REFRESH_LABEL} scenario passed.")
    return 0


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
        staged = stage_claude_market_under_test(tmp)
        if isinstance(staged, str):
            report(f"native-plugin-marketplaces {staged}")
            return 1
        claude_market, claude_market_name, sentinel = staged
        claude_market_add = run_claude(
            "plugin", "marketplace", "add", str(claude_market)
        )
        if claude_market_add.returncode != 0:
            report("native-plugin-marketplaces claude marketplace add failed:")
            report((claude_market_add.stderr or claude_market_add.stdout).strip())
            return 1
        claude_install = run_claude(
            "plugin", "install", f"keel@{claude_market_name}"
        )
        if claude_install.returncode != 0:
            report("native-plugin-marketplaces claude plugin install failed:")
            report((claude_install.stderr or claude_install.stdout).strip())
            return 1
        elsewhere = installed_elsewhere(claude_config, claude_market_name, sentinel)
        if elsewhere is not None:
            report(
                "native-plugin-marketplaces claude plugin install failed to use "
                f"the package under test; it installed from {elsewhere!r}, "
                "which does not carry the sentinel the staged tree does."
            )
            return 1
        # M4 — the packaged install is a working plugin: the host loaded the
        # skills and both hooks from the root manifest, and installed the
        # OpenSpec the lockfile pins, since nothing in the tree carries it.
        details = run_claude("plugin", "details", f"keel@{claude_market_name}")
        details_text = details.stdout or ""
        missing = [
            needle
            for needle in (
                "keel-align-expectations",
                "keel-review-checklist",
                "SessionStart",
                "PreToolUse",
            )
            if needle not in details_text
        ]
        if details.returncode != 0:
            report(
                "native-plugin-marketplaces claude plugin details failed for "
                f"the packaged plugin: {(details.stderr or details_text).strip()!r}"
            )
            return 1
        if missing:
            report(
                "native-plugin-marketplaces the packaged plugin lacks "
                f"{missing!r} in claude plugin details: {details_text!r}"
            )
            return 1
        installed = json.loads(
            (claude_config / "plugins/installed_plugins.json").read_text(
                encoding="utf-8"
            )
        )
        install_path = Path(
            installed["plugins"][f"keel@{claude_market_name}"][0]["installPath"]
        )
        openspec_bin = install_path / "node_modules/.bin/openspec"
        if not openspec_bin.exists():
            report(
                "native-plugin-marketplaces the packaged plugin has no "
                f"installed OpenSpec at {openspec_bin}; the host did not "
                "install the tree's dependencies."
            )
            return 1
        probe = subprocess.run(
            [str(openspec_bin), "--version"],
            text=True,
            capture_output=True,
            check=False,
        )
        pinned = shrinkwrap_openspec_version()
        if probe.returncode != 0:
            report(
                "native-plugin-marketplaces the packaged OpenSpec failed "
                f"to run: {(probe.stderr or probe.stdout).strip()!r}"
            )
            return 1
        if pinned not in probe.stdout:
            report(
                "native-plugin-marketplaces the packaged plugin does not "
                f"carry the pinned OpenSpec {pinned}: {probe.stdout.strip()!r}"
            )
            return 1
        claude_list = run_claude("plugin", "list")
        if f"Version: {PACKAGE_VERSION}" not in (claude_list.stdout or ""):
            report(
                "native-plugin-marketplaces claude plugin list does not show "
                f"keel {PACKAGE_VERSION} installed from the package under test."
            )
            report((claude_list.stderr or claude_list.stdout).strip())
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
            "  - Verification Strategy: evidence-first\n"
            "  - Verification Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
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
                    or projection.get("prohibitions")
                    != gate_contract.get("capsule", {}).get("prohibitions")
                ):
                    report(
                        f"native-runtime-projection {target} did not consume capsule."
                    )
                    report(json.dumps(payload, indent=2))
                    return 1

            completion_without_evidence = run_keel(
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
                completion_without_evidence.returncode != 3
                or json.loads(completion_without_evidence.stdout).get("status")
                != "fail"
            ):
                report(
                    f"native-runtime-projection {target} a projection satisfied "
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
        staged = stage_claude_market_under_test(tmp)
        if isinstance(staged, str):
            report(f"native-plugin-install-matrix {staged}")
            return 1
        staged_market, claude_market, sentinel = staged
        if run_claude(
            "plugin", "marketplace", "add", str(staged_market)
        ).returncode != 0:
            report("native-plugin-install-matrix claude marketplace add failed.")
            return 1
        if run_claude("plugin", "install", f"keel@{claude_market}").returncode != 0:
            report("native-plugin-install-matrix claude install failed.")
            return 1
        elsewhere = installed_elsewhere(claude_config, claude_market, sentinel)
        if elsewhere is not None:
            report(
                "native-plugin-install-matrix claude install did not use the "
                f"package under test; it installed from {elsewhere!r}."
            )
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
        "    - Reason: this is a gate fixture; it exercises contract structure and has no executable behavior that can fail first\n"
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

    for name in ("README.md", "README.zh-CN.md"):
        if "--event compaction" not in (ROOT / name).read_text(encoding="utf-8"):
            report(f"precompact-probe: {name} lacks the manual compaction command.")
            return 1
    registered = {name for name, _ in registry.SCENARIOS}
    for scenario in ("plugin-compaction-continuity", "precompact-probe"):
        if scenario not in registered:
            report(f"precompact-probe: the scenario registry lacks {scenario}.")
            return 1

    report("precompact-probe scenario passed.")
    return 0


# The workflow serializes, or it does not. Asserted by reading the file, because
# it runs only on GitHub, only on a `release` event, and nothing local can
# exercise it — which is exactly why an edit could drop the declaration and
# nobody would find out until the next day someone cut several releases at once.
PUBLISH_WORKFLOW = ".github/workflows/publish.yml"


def publish_serialization_problem(workflow: str) -> str | None:
    """Return the problem the publish workflow's ordering has, or None.

    Takes the text rather than reading the path, so each broken shape can be
    exercised on a planted copy. A rule that could only ever see the file already
    known to be correct would pass forever without anyone learning whether it
    fires.
    """
    block = re.search(
        r"^concurrency:\n((?:[ \t]+\S[^\n]*\n)+)", workflow, re.M
    )
    if not block:
        return (
            "simultaneous releases publish concurrently — "
            f"{PUBLISH_WORKFLOW} declares no `concurrency:` group, so every "
            "release event starts its own publish against the same package."
        )
    body = block.group(1)
    if not re.search(r"^[ \t]+cancel-in-progress:\s*false\s*$", body, re.M):
        return (
            "a queued publish would be cancelled — the group declares no "
            "`cancel-in-progress: false`, and the default is `true`: the next "
            "release would cancel a publish still waiting to run, losing that "
            "version outright rather than appearing to."
        )
    if not re.search(r"^[ \t]+queue:\s*max\s*$", body, re.M):
        return (
            "a pending publish would be cancelled by the next one — the group "
            "declares no `queue: max`, and the default `queue: single` keeps one "
            "pending run and cancels it when a newer one arrives, so a burst of "
            "three releases drops the middle version (#157)."
        )
    group = re.search(r"^[ \t]+group:\s*(\S.*?)\s*$", body, re.M)
    if not group:
        return (
            "a per-run group serializes nothing — the `concurrency:` block "
            "names no `group:`, so there is nothing for a run to queue behind."
        )
    if "${{" in group.group(1):
        return (
            "a per-run group serializes nothing — the group expression "
            f"`{group.group(1)}` is evaluated per run, so each release gets a "
            "group of its own and none of them wait. The thing being protected "
            "is the package, and there is one of those."
        )
    return None


def validate_a_publish_waits_for_the_one_before_it_scenario() -> int:
    """Issue #153: eleven releases at once, and a registry that lied about it.

    Nothing was lost — every job logged its own `+ @christang/keel@<version>`,
    and the write side proved it by refusing a re-run with `You cannot publish
    over the previously published versions`. What broke was the read side: the
    packument reported published versions as missing, and the set changed
    between reads. Two re-runs were triggered on that false reading and are now
    red rows against a release that succeeded. Serialized, each publish finishes
    before the next begins and the window does not exist.
    """
    label = "a-publish-waits-for-the-one-before-it"
    path = ROOT / PUBLISH_WORKFLOW
    if not path.is_file():
        report(f"{label}: {PUBLISH_WORKFLOW} is missing.")
        return 1
    workflow = path.read_text(encoding="utf-8")

    # M1 — the real file declares it, and a copy with the block removed does not.
    # The removal is the state the file was actually in on 2026-09-25.
    problem = publish_serialization_problem(workflow)
    if problem:
        report(f"{label}: {problem}")
        return 1
    stripped = re.sub(
        r"^concurrency:\n(?:[ \t]+\S[^\n]*\n)+", "", workflow, flags=re.M
    )
    if stripped == workflow:
        report(
            f"{label}: simultaneous releases publish concurrently — no "
            "`concurrency:` block could be located to remove, so the real file "
            "does not declare one and the check has nothing to prove."
        )
        return 1
    if not publish_serialization_problem(stripped):
        report(
            f"{label}: simultaneous releases publish concurrently — a workflow "
            "with no concurrency group was accepted, which is the configuration "
            "that let eleven releases publish at once."
        )
        return 1

    # The pending half (#157). `cancel-in-progress: false` protects the running
    # publish; the default `queue: single` still cancels a pending one when a
    # newer run arrives, so a burst of three releases drops the middle version.
    # A copy without `queue: max` is exactly what 5.70.0 shipped.
    unqueued = workflow.replace("  queue: max\n", "")
    if unqueued == workflow:
        report(
            f"{label}: a pending publish would be cancelled by the next one — "
            "`queue: max` could not be located to remove, so the real file keeps "
            "at most one pending run and cancels the rest."
        )
        return 1
    if not publish_serialization_problem(unqueued):
        report(
            f"{label}: a pending publish would be cancelled by the next one — a "
            "group without `queue: max` was accepted."
        )
        return 1

    # M2 — the option whose default is wrong for this job. A check satisfied by
    # the block alone would pass on the configuration that loses a version
    # outright, which is worse than the one being fixed here.
    cancelling = workflow.replace("  cancel-in-progress: false\n", "")
    if cancelling == workflow:
        report(
            f"{label}: a queued publish would be cancelled — "
            "`cancel-in-progress: false` could not be located to remove, so the "
            "real file does not declare it."
        )
        return 1
    if not publish_serialization_problem(cancelling):
        report(
            f"{label}: a queued publish would be cancelled — a group without "
            "`cancel-in-progress: false` was accepted, and the default cancels "
            "a queued publish when the next release fires."
        )
        return 1

    # M3 — the shape that looks like a fix and is not. A group keyed per release
    # gives every run its own group, so nothing ever queues behind anything.
    per_ref = workflow.replace(
        "  group: publish\n", "  group: publish-${{ github.ref }}\n"
    )
    if per_ref == workflow:
        report(f"{label}: a per-run group serializes nothing — `group: publish` could not be located to vary.")
        return 1
    if not publish_serialization_problem(per_ref):
        report(
            f"{label}: a per-run group serializes nothing — a group expression "
            "that differs per release was accepted, so each publish gets a group "
            "of its own and none of them wait."
        )
        return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def validate_a_merge_names_who_makes_it_scenario() -> int:
    """Issue #155: the protocol says the agent may not merge, and stops there.

    Once a repository merges on its own rule — auto-merge behind a required
    check — that sentence is literally true and misleading: a reader concludes
    every change reaching the default branch was looked at by a person. The
    declaration says who merges, so the projection can say it too.
    """
    label = "a-merge-names-who-makes-it"

    with tempfile.TemporaryDirectory(prefix="keel-merge-") as raw:
        root = Path(raw)

        def fixture(name: str, body: str) -> Path:
            repo = root / name
            repo.mkdir()
            (repo / "keel").mkdir()
            (repo / "keel" / "config.yaml").write_text(body, encoding="utf-8")
            return repo

        def merge_lines(out: str) -> list[str]:
            return [l for l in out.splitlines() if l.startswith("Merge:")]

        # M1 — a repository merge is reported with its consequence.
        repo = fixture("repository", "fast_check: echo r\nmerge: repository:full-gate\n")
        out = run_keel(repo, "context").stdout
        lines = merge_lines(out)
        if not lines:
            report(
                f"{label}: no merge declaration reported — a repository that "
                "declared its default branch merges on `full-gate` is told "
                "nothing about it where the session starts."
            )
            report(out)
            return 1
        if "full-gate" not in lines[0]:
            report(f"{label}: the Merge line does not name the check; got {lines[0]!r}.")
            return 1
        if "no human" not in lines[0].lower():
            report(
                f"{label}: the Merge line echoes the value without its "
                f"consequence — that no human reviews before merge; got {lines[0]!r}."
            )
            return 1

        human = fixture("human", "fast_check: echo h\nmerge: human\n")
        lines = merge_lines(run_keel(human, "context").stdout)
        if not lines:
            report(f"{label}: no merge declaration reported for `merge: human`.")
            return 1
        if "human" not in lines[0]:
            report(f"{label}: the `merge: human` line does not say human; got {lines[0]!r}.")
            return 1

        absent = fixture("absent", "fast_check: echo a\n")
        out = run_keel(absent, "context").stdout
        if merge_lines(out):
            report(
                f"{label}: an undeclared repository was given a Merge line — "
                "Keel cannot know how it merges and must not claim it."
            )
            report(out)
            return 1

        # M2 — a claim without its basis claims nothing. A bare `repository`
        # says no person reviews without naming what does, which is the claim
        # that misleads most; an unknown value is a typo its author believes.
        for name, value in (("bare", "repository"), ("unknown", "robots")):
            bad = fixture(name, f"fast_check: echo b\nmerge: {value}\n")
            out = run_keel(bad, "context").stdout
            if merge_lines(out):
                report(
                    f"{label}: accepted a merge claim with no basis — "
                    f"`merge: {value}` produced {merge_lines(out)!r}."
                )
                return 1
            if value not in out:
                report(f"{label}: the refusal does not name `{value}`.")
                report(out)
                return 1
            if "repository:<check>" not in out:
                report(f"{label}: the refusal does not name the accepted forms.")
                report(out)
                return 1

        # M3 — the declaration is not a permission. `merge` under `authorize:`
        # stays an unrecognized action, so nobody can read the new key as leave
        # for the agent to merge.
        perm = fixture("perm", "fast_check: echo p\nauthorize:\n  - merge\n")
        doctor = run_keel(perm, "--doctor").stdout
        if "unrecognized action: merge" not in doctor:
            report(
                f"{label}: `authorize: merge` is not reported as an unrecognized "
                "action, so the new declaration could be read as permission."
            )
            report(doctor)
            return 1

        for name, repo_, expected in (
            ("repository", repo, "full-gate"),
            ("human", human, "human"),
            ("absent", absent, "undeclared"),
        ):
            doctor = run_keel(repo_, "--doctor").stdout
            merge_doctor = [l for l in doctor.splitlines() if l.startswith("merge:")]
            if not merge_doctor:
                report(
                    f"{label}: no merge declaration reported by the doctor for the "
                    f"{name} fixture — it has no `merge:` line at all."
                )
                return 1
            if expected not in merge_doctor[0]:
                report(
                    f"{label}: the doctor's merge line for the {name} fixture does "
                    f"not name {expected!r}; got {merge_doctor[0]!r}."
                )
                return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0


def workflow_job_block(workflow: str, job: str) -> str:
    """The text of one job under `jobs:`, up to the next job at the same indent."""
    match = re.search(
        r"^  " + re.escape(job) + r":\n((?:(?:    [^\n]*|[ \t]*)\n)*)",
        workflow,
        re.M,
    )
    return match.group(1) if match else ""


def registry_wait_problem(workflow: str) -> str | None:
    """Return why `publish.yml` would release before the registry serves it, or None.

    Takes text so a planted copy can prove the rule fires (#421).
    """
    publish = workflow_job_block(workflow, "publish")
    steps = re.split(r"\n(?=      - name: )", publish)
    names = [re.match(r"\s*- name: ([^\n]*)", step).group(1).strip() if re.match(r"\s*- name: ", step) else ""
             for step in steps]
    waits = [i for i, step in enumerate(steps) if "scripts/await_registry.js" in step]
    if not waits:
        return f"releases before the registry serves the version — {PUBLISH_WORKFLOW} never runs scripts/await_registry.js."
    if "Publish" not in names or "Tag and release the landed version" not in names:
        return f"{PUBLISH_WORKFLOW} has no `Publish` or no `Tag and release the landed version` step to order the wait between."
    wait = waits[0]
    if not names.index("Publish") < wait < names.index("Tag and release the landed version"):
        return ("releases before the registry serves the version — the scripts/await_registry.js step is not "
                "between `Publish` and `Tag and release the landed version`.")
    condition = re.search(r"^\s*if: ([^\n]*)", steps[names.index("Publish")], re.M)
    if not condition or f"if: {condition.group(1)}" not in steps[wait]:
        return "the registry wait does not share the `Publish` step's skip condition."
    if "steps.plan.outputs.version" not in steps[wait]:
        return "the registry wait does not wait for the planned version."
    return None


AWAIT_NPM_FAKE = r"""const fs = require("fs");
const count = process.env.FAKE_COUNT;
const calls = (fs.existsSync(count) ? Number(fs.readFileSync(count, "utf8")) : 0) + 1;
fs.writeFileSync(count, String(calls));
fs.appendFileSync(process.env.FAKE_LOG, JSON.stringify(process.argv.slice(2)) + "\n");
const after = process.env.FAKE_SERVE_AFTER;
if (after === "never" || calls <= Number(after)) {
  process.stderr.write("npm error code E404\nnpm error 404 No match found for version 5.2.0\n");
  process.exit(1);
}
process.stdout.write("5.2.0\n");
"""


def validate_publish_awaits_registry_scenario() -> int:
    """Issue #421: a release is created only once the registry serves it.

    The release used to announce a version the registry's read side would not
    serve for minutes, and the first `keel --update` after it failed.
    """
    label = "publish-awaits-registry:"
    script = ROOT / "scripts/await_registry.js"
    if not script.is_file():
        report(f"{label} scripts/await_registry.js is missing.")
        return 1
    with tempfile.TemporaryDirectory(prefix="keel-await-421-", ignore_cleanup_errors=True) as raw:
        tmp = Path(raw)
        fake = tmp / "fake-npm.js"
        write_text(fake, AWAIT_NPM_FAKE)
        launcher = tmp / "fake-npm"
        write_text(launcher, f'#!/bin/sh\nexec node "{fake}" "$@"\n')
        launcher.chmod(0o755)

        def wait(serve_after: str, *extra: str):
            count, log = tmp / "count", tmp / "log.jsonl"
            for stale in (count, log):
                if stale.exists():
                    stale.unlink()
            log.write_text("")
            env = dict(os.environ)
            env.update({"KEEL_AWAIT_NPM": str(launcher), "FAKE_COUNT": str(count), "FAKE_LOG": str(log),
                        "FAKE_SERVE_AFTER": serve_after})
            result = subprocess.run(["node", str(script), "@christang/keel", "5.2.0", "--interval-seconds", "0", *extra],
                                    cwd=tmp, env=env, text=True, capture_output=True, check=False, timeout=60)
            calls = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
            return result, calls

        result, calls = wait("2")
        if result.returncode != 0 or len(calls) != 3:
            report(f"{label} a version served on the third poll did not end the wait after 3 polls with exit 0: "
                   f"exit={result.returncode} polls={len(calls)} {result.stdout!r} {result.stderr!r}")
            return 1
        if calls[0][:3] != ["view", "@christang/keel@5.2.0", "version"]:
            report(f"{label} the wait did not ask npm for the exact version: {calls[0]!r}")
            return 1

        result, calls = wait("never", "--timeout-seconds", "1")
        said = result.stdout + result.stderr
        if result.returncode == 0:
            report(f"{label} a version never served ended the wait with exit 0: {said!r}")
            return 1
        for needle in ("5.2.0", "1 s"):
            if needle not in said:
                report(f"{label} the timed-out wait does not name {needle!r}: {said!r}")
                return 1

    workflow = (ROOT / PUBLISH_WORKFLOW).read_text(encoding="utf-8")
    problem = registry_wait_problem(workflow)
    if problem:
        report(f"{label} {problem}")
        return 1
    tag_step = workflow.find("      - name: Tag and release the landed version")
    wait_start = workflow.rfind("      - name: ", 0, workflow.find("scripts/await_registry.js"))
    wait_end = workflow.find("\n      - name: ", wait_start + 1) + 1
    moved = workflow[:wait_start] + workflow[wait_end:] + workflow[wait_start:wait_end]
    if tag_step < 0:
        report(f"{label} {PUBLISH_WORKFLOW} has no `Tag and release the landed version` step to plant a copy against.")
        return 1
    if not registry_wait_problem(moved):
        report(f"{label} a planted copy with the wait moved after the tag step was not refused.")
        return 1

    if "publish-awaits-registry" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("publish-awaits-registry scenario passed.")
    return 0


def landing_problem(workflow: str) -> str | None:
    """Return the problem the landing path in `publish.yml` has, or None.

    Takes text so each broken shape can be planted. The workflow runs only on
    GitHub from the default branch; the repository's copy is the one input
    guaranteed to be correct, so a rule that only read it would never be seen to
    fire.
    """
    land = workflow_job_block(workflow, "land")
    if not land:
        return (
            f"merges without confirming full-gate — {PUBLISH_WORKFLOW} has no "
            "`land` job."
        )
    if "check_name=full-gate" not in land:
        return (
            "merges without confirming full-gate — the `land` job never reads "
            "the `full-gate` check-run on the head commit before merging."
        )
    if "--match-head-commit" not in land:
        return (
            "merges without confirming full-gate — the merge is not pinned to the "
            "tested head commit, so a push after the check could land untested."
        )
    if "actions/checkout" in land:
        return (
            "pull request code could run with a write token — the `land` job "
            "checks out code, and it runs in the base repository's context with "
            "write permission."
        )
    if '.user.login == \\"$OWNER\\"' not in land:
        return (
            "pull request code could run with a write token — the `land` job "
            "does not restrict itself to the repository owner's pull requests."
        )
    if '.head.repo.full_name == \\"$REPO\\"' not in land:
        return (
            "pull request code could run with a write token — the `land` job "
            "does not refuse pull requests from forks."
        )
    publish = workflow_job_block(workflow, "publish")
    published_at = publish.find("npm publish")
    released_at = publish.find("gh release create")
    if published_at < 0 or released_at < 0:
        return (
            "a failed publish would be left tagged and never retried — the "
            "`publish` job lacks `npm publish` or `gh release create`."
        )
    if released_at < published_at:
        return (
            "a failed publish would be left tagged and never retried — the "
            "`publish` job creates the tag and release before `npm publish`, and "
            "a tag is what tells the next run the version is already released."
        )
    return None


def validate_the_repository_lands_what_passed_scenario() -> int:
    """#155 follow-up: the repository merges, not the agent, with no stored secret.

    Events made with `GITHUB_TOKEN` start no new workflow runs, so a chain of
    workflows (merge, then release, then publish) needs a personal token at every
    hand-off. One run that merges, publishes and releases has no hand-off. The
    price is that the landing job runs with write permission in the base
    repository's context — so it must run no pull-request code, land only the
    owner's own pull requests, and merge only the commit `full-gate` passed.
    """
    label = "the-repository-lands-what-passed"
    workflow = (ROOT / PUBLISH_WORKFLOW).read_text(encoding="utf-8")

    problem = landing_problem(workflow)
    if problem:
        report(f"{label}: {problem}")
        return 1
    land = workflow_job_block(workflow, "land")
    if not land:
        report(
            f"{label}: merges without confirming full-gate — {PUBLISH_WORKFLOW} "
            "has no `land` job, so nothing lands a pull request that passed."
        )
        return 1

    # M1 — the check is read and the tested commit is what merges.
    for needle, why in (
        ("check_name=full-gate", "without reading the `full-gate` check-run"),
        ("--match-head-commit", "without pinning the merge to the tested head commit"),
    ):
        planted = workflow.replace(needle, "")
        if planted == workflow:
            report(f"{label}: merges without confirming full-gate — `{needle}` is absent.")
            return 1
        if not landing_problem(planted):
            report(
                f"{label}: merges without confirming full-gate — a landing job "
                f"that merges {why} was accepted."
            )
            return 1

    # M2 — no pull-request code under a write token, and only the owner's own
    # pull requests from this repository. `workflow_run` and
    # `pull_request_target` run in the base repository's context with the
    # permissions the job asks for, so a checkout there hands the token to
    # whatever the pull request contains.
    checkout = workflow.replace(
        "      - name: Land an owner's pull request whose head passed full-gate\n",
        "      - uses: actions/checkout@v4\n"
        "      - name: Land an owner's pull request whose head passed full-gate\n",
    )
    if checkout == workflow:
        report(f"{label}: pull request code could run with a write token — the land step could not be located.")
        return 1
    if not landing_problem(checkout):
        report(
            f"{label}: pull request code could run with a write token — a "
            "`land` job with a checkout step was accepted."
        )
        return 1
    for needle, why in (
        ('.user.login == \\"$OWNER\\"', "any author's pull request"),
        ('.head.repo.full_name == \\"$REPO\\"', "a pull request from a fork"),
    ):
        planted = workflow.replace(" and " + needle, "")
        if planted == workflow:
            report(f"{label}: pull request code could run with a write token — `{needle}` is absent.")
            return 1
        if not landing_problem(planted):
            report(
                f"{label}: pull request code could run with a write token — a "
                f"`land` job that would land {why} was accepted."
            )
            return 1

    # M3 — publish before tagging. A tag is what tells the next run "already
    # released", so a tag created before a publish that then fails marks a version
    # released that never reached npm, and nothing would ever retry it.
    publish_step = workflow[workflow.index("      - name: Publish\n"):workflow.index("      - name: Tag and release the landed version\n")]
    tag_step = workflow[workflow.index("      - name: Tag and release the landed version\n"):]
    swapped = workflow.replace(publish_step + tag_step, tag_step.rstrip("\n") + "\n\n" + publish_step.rstrip("\n") + "\n")
    if swapped == workflow:
        report(f"{label}: a failed publish would be left tagged and never retried — the two steps could not be swapped.")
        return 1
    if not landing_problem(swapped):
        report(
            f"{label}: a failed publish would be left tagged and never retried — "
            "a `publish` job that creates the release before `npm publish` was "
            "accepted."
        )
        return 1

    if label not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label}: the scenario registry does not include it.")
        return 1
    report(f"{label} scenario passed.")
    return 0

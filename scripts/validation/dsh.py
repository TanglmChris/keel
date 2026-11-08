"""Keel validation: dsh (#504). DSH is a target that shares Codex's repository surface."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from validation.common import report, run_keel


def dsh_env(home: Path) -> dict[str, str]:
    """An environment with no DSH on it and a Codex home of its own, so the real machine is not read."""
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE", "KEEL_"))}
    env["CODEX_HOME"] = str(home / "codex-home")
    env["HOME"] = str(home)
    return env


def validate_dsh_capabilities_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-dsh-cap-") as raw:
        base = Path(raw).resolve()
        repo = base / "repo"
        repo.mkdir()
        env = dsh_env(base)
        result = run_keel(repo, "capabilities", "--target", "dsh", "--json", env=env)
        if result.returncode != 0:
            report(f"dsh-capabilities: exit {result.returncode}: {(result.stderr or result.stdout).strip()}")
            return 1
        payload = json.loads(result.stdout)
        if payload.get("target") != "dsh":
            report(f"dsh-capabilities: target is {payload.get('target')!r}, not 'dsh'")
            return 1
        capabilities = payload.get("capabilities", {})
        if len(capabilities) != 6:
            report(f"dsh-capabilities: expected six capabilities, got {sorted(capabilities)}")
            return 1
        not_manual = [name for name, c in capabilities.items() if c.get("level") != "manual"]
        if not_manual:
            report(f"dsh-capabilities: not manual: {not_manual}")
            return 1
        for name, capability in capabilities.items():
            evidence = capability.get("evidence", "")
            if "no session-start, resume or compaction hook" not in evidence or "AGENTS.md bootstrap" not in evidence:
                report(f"dsh-capabilities: {name} evidence does not state the probe: {evidence!r}")
                return 1
        plain = run_keel(repo, "capabilities", "--target", "dsh", env=env)
        if "Target capabilities (dsh):" not in plain.stdout:
            report(f"dsh-capabilities: plain rendering lacks its heading: {plain.stdout[:200]!r}")
            return 1
        bad = run_keel(repo, "capabilities", "--target", "nope", env=env)
        if bad.returncode == 0:
            report("dsh-capabilities: an unknown target exited 0")
            return 1
        if "invalid target: nope" not in bad.stderr:
            report(f"dsh-capabilities: an unknown target was refused without naming it: {bad.stderr!r}")
            return 1
    report("dsh-capabilities scenario passed.")
    return 0


def validate_dsh_project_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-dsh-proj-") as raw:
        base = Path(raw).resolve()
        repo = base / "repo"
        repo.mkdir()
        env = dsh_env(base)
        init = run_keel(repo, "--init", "--target", "codex", env=env)
        if init.returncode != 0:
            report(f"dsh-project: init failed: {(init.stderr or init.stdout).strip()}")
            return 1
        results = {}
        for target in ("dsh", "codex"):
            out = run_keel(repo, "project", "--target", target, "--event", "startup", "--json", env=env)
            if out.returncode != 0:
                report(f"dsh-project: {target} exit {out.returncode}: {(out.stderr or out.stdout).strip()}")
                return 1
            results[target] = json.loads(out.stdout)
        if set(results["dsh"]) != set(results["codex"]):
            report(f"dsh-project: keys differ: {sorted(results['dsh'])} vs {sorted(results['codex'])}")
            return 1
        if results["dsh"].get("target") != "dsh":
            report(f"dsh-project: target is {results['dsh'].get('target')!r}, not 'dsh'")
            return 1
    report("dsh-project scenario passed.")
    return 0


def restricted_path(base: Path, *, dsh_version: str | None) -> dict[str, str]:
    """An environment whose PATH holds node, git and python3, and a `dsh` only when a version is given."""
    bin_dir = base / "bin"
    bin_dir.mkdir(exist_ok=True)
    for tool in ("node", "git", "python3", "python3.11"):
        found = shutil.which(tool)
        if found and not (bin_dir / tool).exists():
            (bin_dir / tool).symlink_to(found)
    if dsh_version is not None:
        script = bin_dir / "dsh"
        script.write_text(f'#!/bin/sh\necho "{dsh_version}"\n', encoding="utf-8")
        script.chmod(0o755)
    env = dsh_env(base)
    env["PATH"] = str(bin_dir)
    return env


def validate_dsh_init_doctor_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-dsh-init-") as raw:
        base = Path(raw).resolve()
        repo = base / "repo"
        repo.mkdir()
        env = dsh_env(base)
        init = run_keel(repo, "--init", "--target", "dsh", env=env)
        if init.returncode != 0:
            report(f"dsh-init-doctor: init exit {init.returncode}: {(init.stderr or init.stdout).strip()}")
            return 1
        agents = repo / "AGENTS.md"
        if not agents.exists():
            report("dsh-init-doctor: init wrote no AGENTS.md")
            return 1
        if "keel:start" not in agents.read_text(encoding="utf-8"):
            report("dsh-init-doctor: AGENTS.md carries no Keel bootstrap block")
            return 1
        if not (repo / ".agents/skills/openspec-apply-change/SKILL.md").exists():
            report("dsh-init-doctor: init left no OpenSpec skill under .agents/skills")
            return 1
        for forbidden in (".dsh", ".claude"):
            if (repo / forbidden).exists():
                report(f"dsh-init-doctor: init created {forbidden}")
                return 1
        check = run_keel(repo, "--check", "--target", "dsh", env=env)
        if check.returncode != 0:
            report(f"dsh-init-doctor: check exit {check.returncode}: {(check.stderr or check.stdout).strip()}")
            return 1
        doctor = run_keel(repo, "--doctor", "--target", "dsh", env=env)
        if doctor.returncode != 0:
            report(f"dsh-init-doctor: doctor exit {doctor.returncode}: {(doctor.stderr or doctor.stdout).strip()}")
            return 1
        for expected in ("bootstrap: ok", "Target capabilities (dsh):", "DSH hooks: manual", "DSH surface: ok"):
            if expected not in doctor.stdout:
                report(f"dsh-init-doctor: doctor output lacks {expected!r}")
                return 1
    report("dsh-init-doctor scenario passed.")
    return 0


def validate_dsh_binary_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-dsh-bin-") as raw:
        base = Path(raw).resolve()
        repo = base / "repo"
        repo.mkdir()
        (base / "absent").mkdir()
        absent = restricted_path(base / "absent", dsh_version=None)
        init = run_keel(repo, "--init", "--target", "dsh", env=absent)
        if init.returncode != 0:
            report(f"dsh-binary: init exit {init.returncode}: {(init.stderr or init.stdout).strip()}")
            return 1
        missing = run_keel(repo, "--doctor", "--target", "dsh", env=absent)
        if missing.returncode != 0:
            report(f"dsh-binary: doctor without dsh exit {missing.returncode}: {(missing.stderr or missing.stdout).strip()}")
            return 1
        if "DSH CLI: not found" not in missing.stdout:
            report("dsh-binary: doctor without dsh did not say `DSH CLI: not found`")
            return 1
        (base / "present").mkdir()
        present = restricted_path(base / "present", dsh_version="9.9.9")
        found = run_keel(repo, "--doctor", "--target", "dsh", env=present)
        if found.returncode != 0:
            report(f"dsh-binary: doctor with dsh exit {found.returncode}: {(found.stderr or found.stdout).strip()}")
            return 1
        line = next((l for l in found.stdout.splitlines() if l.startswith("DSH CLI:")), "")
        if "ok" not in line:
            report(f"dsh-binary: doctor with dsh did not report ok: {line!r}")
            return 1
        if "9.9.9" not in line:
            report(f"dsh-binary: doctor with dsh did not carry the version: {line!r}")
            return 1
    report("dsh-binary scenario passed.")
    return 0


def validate_dsh_uninstall_shared_scenario() -> int:
    with tempfile.TemporaryDirectory(prefix="keel-dsh-un-") as raw:
        base = Path(raw).resolve()
        repo = base / "repo"
        repo.mkdir()
        env = dsh_env(base)
        for target in ("claude", "dsh"):
            init = run_keel(repo, "--init", "--target", target, env=env)
            if init.returncode != 0:
                report(f"dsh-uninstall-shared: init {target} exit {init.returncode}: {(init.stderr or init.stdout).strip()}")
                return 1
        dsh_plan = run_keel(repo, "--uninstall", "--target", "dsh", "--dry-run", env=env)
        codex_plan = run_keel(repo, "--uninstall", "--target", "codex", "--dry-run", env=env)
        if dsh_plan.returncode != 0 or codex_plan.returncode != 0:
            report(f"dsh-uninstall-shared: dry-run exits {dsh_plan.returncode}/{codex_plan.returncode}")
            return 1
        if "shared with Codex" not in dsh_plan.stdout + dsh_plan.stderr:
            report("dsh-uninstall-shared: the DSH plan does not say the files are shared with Codex")
            return 1
        kept = [l for l in dsh_plan.stdout.splitlines() if "shared with Codex" not in l]
        if kept != codex_plan.stdout.splitlines():
            report("dsh-uninstall-shared: the DSH plan lists removals the Codex plan does not (or the reverse)")
            return 1
        real = run_keel(repo, "--uninstall", "--target", "dsh", env=env)
        if real.returncode != 0:
            report(f"dsh-uninstall-shared: uninstall exit {real.returncode}: {(real.stderr or real.stdout).strip()}")
            return 1
        marker = "keel:openspec-surface-overlay"
        shared = (repo / ".agents/skills/openspec-apply-change/SKILL.md").read_text(encoding="utf-8")
        if marker in shared:
            report("dsh-uninstall-shared: the Keel overlay is still in .agents/skills after the uninstall")
            return 1
        claude = (repo / ".claude/skills/openspec-apply-change/SKILL.md").read_text(encoding="utf-8")
        if marker not in claude:
            report("dsh-uninstall-shared: the Claude overlay was removed with DSH's")
            return 1
    report("dsh-uninstall-shared scenario passed.")
    return 0


def validate_dsh_docs_scenario() -> int:
    from validation.common import ROOT

    with tempfile.TemporaryDirectory(prefix="keel-dsh-docs-") as raw:
        base = Path(raw).resolve()
        env = dsh_env(base)
        helped = run_keel(base, "--help", env=env)
        target_lines = [l for l in helped.stdout.splitlines() if "--target claude|codex|opencode" in l or "--target claude|codex|opencode|dsh" in l]
        if not target_lines:
            report("dsh-docs: --help lists no target line at all")
            return 1
        without = [l.strip() for l in target_lines if "dsh" not in l]
        if without:
            report(f"dsh-docs: --help target lines without dsh: {without}")
            return 1
        bare = run_keel(base, "--init", "--target", env=env)
        if bare.returncode == 0:
            report("dsh-docs: `--init --target` with no value exited 0")
            return 1
        if "dsh" not in bare.stderr:
            report(f"dsh-docs: the missing-value message does not name dsh: {bare.stderr!r}")
            return 1
    for name in ("README.md", "README.zh-CN.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        if "--target dsh" not in text:
            report(f"dsh-docs: {name} never mentions `--target dsh`")
            return 1
        head = "\n".join(text.splitlines()[:12])
        if "DSH" not in head:
            report(f"dsh-docs: {name} tagline and badge do not name DSH")
            return 1
    report("dsh-docs scenario passed.")
    return 0

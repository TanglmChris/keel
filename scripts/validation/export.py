"""Keel validation: export — the retired Markdown-to-Word export (#405, retired by #464)."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from validation.common import (
    ROOT,
    report,
    write_text,
)
from validation import registry


def validate_docx_retired_scenario() -> int:
    """Issue #464 (owner, 2026-10-25): Markdown-to-Word export is not Keel's job.

    `keel docx` stays a recognized word so that a caller learns the export was
    retired instead of reading the general usage, and it installs and converts
    nothing. The plugin no longer ships the skill.
    """
    label = "docx-retired:"
    with tempfile.TemporaryDirectory(prefix="keel-docx-464-") as raw:
        tmp = Path(raw)
        home = tmp / "home"
        source = tmp / "a.md"
        write_text(source, "# A\n")
        env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp), "KEEL_HOME": str(home)}
        node = subprocess.run(["which", "node"], text=True, capture_output=True).stdout.strip() or "node"
        for args in (("setup", "--yes"), ("convert", str(source))):
            ran = subprocess.run([node, str(ROOT / "bin/keel.js"), "docx", *args], cwd=tmp, env=env,
                                 text=True, capture_output=True, check=False)
            said = ran.stdout + ran.stderr
            if "keel docx was retired" not in said:
                report(f"{label} keel docx {' '.join(args)} does not say it was retired (exit {ran.returncode}): {said[:300]!r}")
                return 1
            if ran.returncode != 2:
                report(f"{label} keel docx {' '.join(args)} exited {ran.returncode}, not 2.")
                return 1
        if (home / "docx").exists():
            report(f"{label} keel docx wrote {home / 'docx'}.")
            return 1
        written = sorted(p.name for p in tmp.iterdir() if p.suffix == ".docx")
        if written:
            report(f"{label} keel docx convert wrote {written!r}.")
            return 1
    for shipped in (ROOT / "plugins/keel/skills/keel-md-docx", ROOT / "src/skills/keel-md-docx"):
        if shipped.exists():
            report(f"{label} {shipped.relative_to(ROOT)} still ships the export skill.")
            return 1
    if "docx-retired" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} scenario is not registered.")
        return 1
    report("docx-retired scenario passed.")
    return 0

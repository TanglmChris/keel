"""Keel validation: export — Markdown with SVG to Word (#405)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from validation.common import (
    ROOT,
    report,
    write_text,
)
from validation import registry


DOCX_SKILL = "keel-md-docx"
DOCX_SCRIPTS = ("md2word.py", "runtime.mjs", "fonts-macos.conf", "requirements.txt", "package.json")
# The SHA-256 #405 states for the prototype files that ship unchanged.
DOCX_PROTOTYPE_SUMS = {
    "md2word.py": "73331af530b524eeafe465a9d50bc6434d64abadc2f64e2140826a68b9a1bd1f",
    "runtime.mjs": "7fa52c333d16f92bb2c7eb54ad5c5e25d04ee71c13f2501927fd53492eb381a2",
}
DOCX_LICENCES = {
    "python-docx": "MIT",
    "lxml": "BSD-3-Clause",
    "Pillow": "MIT-CMU",
    "marked": "MIT",
    "sharp": "Apache-2.0",
}


def skill_description(text: str) -> str:
    match = re.search(r"^description:\s*(?:[>|]-?\s*\n((?:[ \t]+.*\n?)+)|(.+))$", text, re.M)
    if not match:
        return ""
    return " ".join((match.group(1) or match.group(2) or "").split())


def validate_docx_skill_ships_scenario() -> int:
    """Issue #405: the plugin carries the export skill and the converter it runs."""
    label = "docx-skill-ships:"
    source = ROOT / "src/skills" / DOCX_SKILL
    shipped = ROOT / "plugins/keel/skills" / DOCX_SKILL
    for relative in ("SKILL.md", *(f"scripts/{name}" for name in DOCX_SCRIPTS)):
        plugin_file = shipped / relative
        if not plugin_file.is_file():
            report(f"{label} the plugin does not ship {DOCX_SKILL}/{relative}.")
            return 1
        source_file = source / relative
        if not source_file.is_file() or source_file.read_bytes() != plugin_file.read_bytes():
            report(f"{label} plugins/keel/skills/{DOCX_SKILL}/{relative} is not byte-identical to src/skills.")
            return 1
    for name, expected in DOCX_PROTOTYPE_SUMS.items():
        actual = hashlib.sha256((shipped / "scripts" / name).read_bytes()).hexdigest()
        if actual != expected:
            report(f"{label} scripts/{name} is not the #405 prototype file: sha256 {actual}, expected {expected}.")
            return 1

    text = (shipped / "SKILL.md").read_text(encoding="utf-8")
    description = skill_description(text).lower()
    for word in ("markdown", "svg", "word"):
        if word not in description:
            report(f"{label} the description does not name {word!r}, so a request for this export may not load it: {description!r}")
            return 1
    for needle in ("keel docx setup", "--yes", "--replace", "unverified"):
        if needle not in text:
            report(f"{label} SKILL.md does not name {needle!r}.")
            return 1
    for package, licence in DOCX_LICENCES.items():
        if package not in text or licence not in text:
            report(f"{label} SKILL.md does not state {package} and its licence {licence}.")
            return 1

    evidence_path = ROOT / "keel/archive/skill-evidence" / f"{DOCX_SKILL}-v1.md"
    if not evidence_path.is_file():
        report(f"{label} {evidence_path.relative_to(ROOT)} is missing.")
        return 1
    evidence = evidence_path.read_text(encoding="utf-8")
    positives = re.findall(r"^## Positive case P\d+", evidence, re.M)
    negatives = re.findall(r"^## Negative control N\d+", evidence, re.M)
    if len(positives) < 2:
        report(f"{label} the evidence carries {len(positives)} positive trigger case(s), fewer than 2.")
        return 1
    if len(negatives) < 2:
        report(f"{label} the evidence carries {len(negatives)} negative control(s), fewer than 2.")
        return 1
    for package, licence in DOCX_LICENCES.items():
        if not re.search(rf"^- {re.escape(package)}\b.*{re.escape(licence)}", evidence, re.M):
            report(f"{label} the evidence has no licence line for {package} ({licence}).")
            return 1

    if "docx-skill-ships" not in {name for name, _ in registry.SCENARIOS}:
        report(f"{label} the scenario registry does not include it.")
        return 1
    report("docx-skill-ships scenario passed.")
    return 0

"""Keel validation: what kind of evidence each scenario is (#408).

A green summary reads as more than it proves when much of the suite runs Keel
against a stand-in host — a fake `claude`, the host's environment, a host data
directory, a hook payload — and none of it against a real one. Every
registered scenario is classified as deterministic or stand-in host, from
markers derived from Keel's own sources, through the validation helpers and
scripts it reaches. The classification is static and over-approximates: a
scenario that only mentions a marker counts as stand-in host, which claims
less real evidence, never more.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from validation.common import ROOT

# A program or service Keel calls, overridable for a test: `process.env.X ||`
# a program name, a constant, `npmCommand(…)`, or a platform conditional.
# Path and identity overrides (`path.join(…)`, `os.hostname()`) are not hosts.
PROGRAM_OVERRIDE = re.compile(r"process\.env\.(KEEL_[A-Z_]+) \|\| (\"[^\"]+\"|[A-Z][A-Z_]+\b|npmCommand\(|\(process\.platform)")
HOST_VARIABLE = re.compile(r"\b((?:CLAUDE|CODEX)_[A-Z0-9_]+)\b")
HOST_PROGRAMS = ("claude", "codex", "npm", "gh", "launchctl", "security")
SHADOWED_PROGRAM = re.compile(r"/ \"(" + "|".join(HOST_PROGRAMS) + r")\"")
HOOK_PAYLOAD = "hook_event_name"
SCRIPT_PATH = re.compile(r"scripts/([a-z_]+\.py)")
CONTRACT = "docs/host-contract.md"


def keel_sources() -> str:
    files = [*sorted((ROOT / "src").rglob("*.js")), ROOT / "bin" / "keel.js", *sorted((ROOT / "plugins" / "keel" / "scripts").rglob("*.js"))]
    return "\n".join(path.read_text(encoding="utf-8") for path in files)


def markers() -> list[str]:
    text = keel_sources()
    found = {match.group(1) for match in PROGRAM_OVERRIDE.finditer(text)} | set(HOST_VARIABLE.findall(text))
    return sorted(found | {HOOK_PAYLOAD})


def definitions() -> dict[str, tuple[set[str], str]]:
    """Each module-level function or assignment under scripts/validation/: the names it references and its source."""
    found: dict[str, tuple[set[str], str]] = {}
    for module in sorted((ROOT / "scripts" / "validation").glob("*.py")):
        source = module.read_text(encoding="utf-8")
        for node in ast.parse(source).body:
            if isinstance(node, ast.FunctionDef):
                names = [node.name]
            elif isinstance(node, ast.Assign):
                names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            else:
                continue
            refs = {item.id for item in ast.walk(node) if isinstance(item, ast.Name)}
            refs |= {item.attr for item in ast.walk(node) if isinstance(item, ast.Attribute)}
            for name in names:
                found[name] = (refs, ast.get_source_segment(source, node) or "")
    return found


def reached_text(function: str, found: dict[str, tuple[set[str], str]]) -> tuple[str, set[str]]:
    seen: set[str] = set()
    todo = [function]
    while todo:
        name = todo.pop()
        if name in seen or name not in found:
            continue
        seen.add(name)
        todo.extend(ref for ref in found[name][0] if ref in found)
    text = "\n".join(found[name][1] for name in sorted(seen))
    for script in sorted(set(SCRIPT_PATH.findall(text))):
        path = ROOT / "scripts" / script
        if path.is_file() and script != "validate_plugin.py":
            text += "\n" + path.read_text(encoding="utf-8")
    return text, seen


def classify(scenarios) -> dict:
    """{"markers", "stand-in host", "deterministic", "can skip"} for the registered scenarios, in registry order."""
    marks = markers()
    found = definitions()
    standin, deterministic, skippable = [], [], []
    for name, function in scenarios:
        defined = getattr(function, "__name__", None)
        text, seen = reached_text(defined, found) if defined in found else ("", set())
        # A scenario whose code cannot be read cannot be shown deterministic.
        if defined not in found or any(mark in text for mark in marks) or SHADOWED_PROGRAM.search(text):
            standin.append(name)
        else:
            deterministic.append(name)
        if "skip_scenario" in seen:
            skippable.append(name)
    return {"markers": marks, "stand-in host": standin, "deterministic": deterministic, "can skip": skippable}


def evidence_line(classes: dict, ran: set[str]) -> str:
    """The line after a passing run: the classes of the scenarios that ran."""
    deterministic = sum(1 for name in classes["deterministic"] if name in ran)
    standin = sum(1 for name in classes["stand-in host"] if name in ran)
    return (f"evidence: {deterministic} deterministic, {standin} against a stand-in host, "
            f"none on a real host (host measurements: {CONTRACT})")


def measured_rows() -> int:
    """Rows of the host contract whose evidence cell records a real-host measurement."""
    text = (ROOT / CONTRACT).read_text(encoding="utf-8")
    return sum(1 for line in text.splitlines()
               if line.startswith("|") and "measured" in line.rstrip().rstrip("|").rsplit("|", 1)[-1])


def render(classes: dict) -> str:
    return "\n".join([
        f"evidence: {len(classes['deterministic'])} deterministic, {len(classes['stand-in host'])} against a stand-in host, "
        f"none on a real host (host measurements: {CONTRACT})",
        f"stand-in markers: {', '.join(classes['markers'])}",
        f"stand-in host: {', '.join(classes['stand-in host'])}",
        f"deterministic: {', '.join(classes['deterministic'])}",
        f"can skip: {', '.join(classes['can skip'])}",
    ])


def render_markdown(classes: dict) -> str:
    skips = ", ".join(f"`{name}`" for name in classes["can skip"]) or "none"
    return "\n".join([
        "",
        "## Evidence",
        "",
        "What the full gate ran for this release, by kind (`validate_plugin.py --evidence`):",
        "",
        f"- **Deterministic:** {len(classes['deterministic'])} scenarios run Keel's own code against real git, Node and files.",
        f"- **Stand-in host:** {len(classes['stand-in host'])} scenarios run Keel against a stand-in for a host program, "
        "the host's environment, a host data directory or a hook payload. They show what Keel does with the shapes they "
        "model, not that a host still produces them.",
        f"- **Real host:** none. CI has no Claude Code or Codex. `{CONTRACT}` records {measured_rows()} conditions "
        "measured on a real host, each with its version and date.",
        f"- **Can skip:** {skips} skip when the runtime they need is missing; the full gate's log names any that did.",
        "",
    ])

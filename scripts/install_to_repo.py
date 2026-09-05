#!/usr/bin/env python3
"""Install the thin Keel host surface: OpenSpec schema, overlays, and bootstrap."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MANAGED_START_RE = re.compile(r"<!--\s*keel:start(?:\s+[^>]*)?\s*-->")
MANAGED_END = "<!-- keel:end -->"
TEMPLATE_CHECKSUM_PREFIX = "<!-- keel:content-sha256 "
TEMPLATE_CHECKSUM_SUFFIX = " -->"
KEEL_ROOT = Path("keel")
HANDOFF_PATH = KEEL_ROOT / "HANDOFF.md"
KEEL_CONFIG_PATH = KEEL_ROOT / "config.yaml"
KEEL_CONFIG_TEMPLATE = (
    "# Keel project configuration.\n"
    "#\n"
    "# fast_check (optional): your project's fast inner-loop check — a\n"
    "# seconds-scale command run at a local pre-push (see\n"
    "# `keel --install --with-git-hooks`) and during iteration. The full or slow\n"
    "# suite belongs to CI or `keel gate change-close`, not the local pre-push.\n"
    "#\n"
    "# Example:\n"
    "#   fast_check: npm test -- --fast\n"
)
KEEL_GITIGNORE_PATH = KEEL_ROOT / ".gitignore"
KEEL_GITIGNORE_TEMPLATE = (
    "# Keel local state. keel/ otherwise holds project content that belongs in\n"
    "# version control (config.yaml, CHANGELOG.md, archive/); the write-guard\n"
    "# manifest is per-clone session state that a gate run writes and\n"
    "# `keel guard clear` removes.\n"
    "guard.json\n"
)
GITHOOKS_DIR = ".githooks"
PRE_PUSH_PATH = Path(GITHOOKS_DIR) / "pre-push"
OPENSPEC_ROOT = Path("openspec")
OPENSPEC_CONFIG_PATH = OPENSPEC_ROOT / "config.yaml"
OPENSPEC_SCHEMA_NAME = "keel-spec-driven"
OPENSPEC_SCHEMA_ROOT = OPENSPEC_ROOT / "schemas" / OPENSPEC_SCHEMA_NAME
BOOTSTRAP_ASSET = Path("assets") / "bootstrap" / "AGENTS.md"
OPENSPEC_ASSET_ROOT = Path("assets") / "openspec"


def _bootstrap_marker() -> str:
    # The shipped bootstrap asset is the single canonical source of the
    # managed-block marker (including its version); install code derives the
    # marker instead of restating the literal, so the two can never drift.
    first_line = (
        (PACKAGE_ROOT / BOOTSTRAP_ASSET)
        .read_text(encoding="utf-8")
        .splitlines()[0]
        .strip()
    )
    if not MANAGED_START_RE.fullmatch(first_line):
        raise SystemExit(
            "bootstrap asset must begin with a keel:start marker; found: "
            + first_line
        )
    return first_line


MANAGED_START = _bootstrap_marker()
CLAUDE_IMPORT_BLOCK = f"{MANAGED_START}\n@AGENTS.md\n{MANAGED_END}\n"
KEEL_HOOK_NAME = "keel-gate"
KEEL_HOOK_ROOT = Path(".claude") / "hooks" / KEEL_HOOK_NAME
SUPPORTED_TARGETS = ("claude", "codex", "opencode")
AGENT_PROTOCOL_TARGETS = {"codex", "opencode"}
TARGET_ADAPTER_PATHS = {
    "claude": Path(".claude") / "keel" / "keel-adapter.js",
    "codex": Path(".agents") / "keel" / "keel-adapter.js",
    "opencode": Path(".opencode") / "keel" / "keel-adapter.js",
}
HANDOFF_FIELDS = {"schema", "owner", "action", "reason"}
HANDOFF_ACTIONS = {
    "discuss",
    "author",
    "task-start",
    "task-complete",
    "change-close",
}
HANDOFF_OWNER_RE = re.compile(
    r"^openspec/changes/[A-Za-z0-9][A-Za-z0-9._-]*/"
    r"(?:proposal|design|tasks)\.md(?:#.+)?$"
)
TASKS_LEGACY_HEADING_PATTERNS = (
    (
        re.compile(r"(?im)^##\s+Execution Status\s*$"),
        "replace legacy ## Execution Status with ## Workflow Notes; tasks.md is not an execution or commit ledger",
    ),
    (
        re.compile(r"(?im)^##\s+Current Completion\s*$"),
        "remove legacy ## Current Completion; derive progress from checklist [x]/[ ] state",
    ),
)
TASKS_COMMIT_STATUS_PATTERNS = (
    (
        re.compile(r"(?i)\bcommit[-\s]?hash\b"),
        "remove commit hash wording from tasks.md; git log is the source of truth",
    ),
    (
        re.compile(r"(?i)\b(?:dirty|uncommitted|not\s+committed|pending\s+commit)\b"),
        "remove dirty/uncommitted state from tasks.md; keep durable work state in OpenSpec and use HANDOFF only as an explicit pointer override",
    ),
    (
        re.compile(r"(?:未合入|待合入|已合入|合入\s*(?:master|main))"),
        "remove commit or merge state from tasks.md; git log is the source of truth",
    ),
    (
        re.compile(r"(?i)\b(?:merged|merge[d]?)\s+(?:to|into)\s+(?:master|main)\b"),
        "remove branch merge state from tasks.md; git log is the source of truth",
    ),
)
# 合入 names the git act and has no other reading, so it is refused on its own
# above. 提交 is an ordinary transitive verb — 提交资料, 提交审核, 提交申请 — and
# matching it bare refused an Evidence line about a third-party review queue
# while accepting the same sentence in English (#103). A check whose verdict
# depends on which language the author wrote in is not checking what it claims
# to, so this family is refused only where the line says the subject is git.
TASKS_SUBMISSION_STATE_RE = re.compile(r"(?:未提交|待提交|已提交|尚未提交)")
# The words that name git or a git object. Deliberately not `_HASH_CONTEXT_WORD`:
# that list holds 提交 and 合入 themselves, because its job is to let a state word
# supply context to a hash-shaped token, and reusing it here would let 已提交
# supply its own context and change nothing. The ASCII words carry boundaries for
# the reason #65 established; the Chinese ones cannot and do not.
TASKS_GIT_CONTEXT_RE = re.compile(
    r"(?i)\b(?:git|commits?|committed|committing|master|main|HEAD|branch(?:es)?"
    r"|PR|merges?|merged)\b"
    r"|分支|仓库|代码库|代码|合入|工作区|暂存"
)
TASKS_SUBMISSION_MESSAGE = (
    "remove commit or merge state from tasks.md; git log is the source of truth"
)


# A commit identifier is hexadecimal, and `a`-`f` are the only reason those
# letters appear in one. A run of decimal digits alone is a phone number, a
# timestamp, an order number, or a port — evidence prose, not state git owns.
# Matching one as a recorded identifier (#58) asks the author to reword
# something that was true, and a check that refuses correct work is one people
# learn to route around. The length and word-boundary conditions are kept
# verbatim inside the lookahead, so the token that matches is the token that
# always matched, minus the all-decimal ones.
_HASH_SHAPED_TOKEN = r"\b(?=[0-9a-f]{7,40}\b)[0-9a-f]*[a-f][0-9a-f]*\b"
# A context word has to be a word. Matched anywhere on the line, `main` was
# supplied by `remaining`, `domain`, and `maintains`, and `head` by `heading`
# — and the tokens sitting beside those words in this repository's own
# history are `sha256:` contract anchors, not commit identifiers (#65).
# The inflections are spelled out rather than left to a prefix match: they are
# the words an author writes about the act this rule exists to catch, and the
# stricter list that drops `committed` and `hashes` would cost real refusals.
# The Chinese words carry no boundary because none is definable between two
# word characters — `\b提交\b` matches neither `已提交` nor `未提交`. What that
# buys is this rule: a state word beside a hash-shaped token still supplies the
# context that makes the token an identifier. The wording rule above no longer
# rests on it, because 提交 needs a git word of its own (#103).
_HASH_CONTEXT_WORD = (
    r"(?:\b(?:commits?|committed|committing|master|main|HEAD|hash(?:es)?)\b"
    r"|提交|合入|哈希)"
)
TASKS_CONTEXTUAL_HASH_RE = re.compile(
    rf"(?i){_HASH_CONTEXT_WORD}.*{_HASH_SHAPED_TOKEN}|"
    rf"{_HASH_SHAPED_TOKEN}.*{_HASH_CONTEXT_WORD}"
)


@dataclass(frozen=True)
class InstallAction:
    relative_path: Path
    source_path: Path | None = None
    content: str | None = None
    strategy: str = "copy"


@dataclass(frozen=True)
class PlannedAction:
    kind: str
    relative_path: Path
    content: str | None = None


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def require_inside_repo(repo: Path, relative_path: Path) -> Path:
    destination = (repo / relative_path).resolve()
    if not is_relative_to(destination, repo):
        raise ValueError(f"refusing to write outside target repo: {relative_path}")
    return destination


def dist_asset(*parts: str) -> Path:
    return PACKAGE_ROOT.joinpath("dist", *parts)


def target_names(target: str) -> list[str]:
    if target == "both":
        return ["claude"]
    return [target]


def target_set(target: str) -> set[str]:
    return set(target_names(target))


def file_action(relative_path: str, source_path: Path) -> InstallAction:
    if not source_path.is_file():
        raise ValueError(f"missing packaged asset: {source_path}")
    return InstallAction(
        relative_path=Path(relative_path),
        source_path=source_path,
    )


def managed_file_action(relative_path: str, source_path: Path) -> InstallAction:
    if not source_path.is_file():
        raise ValueError(f"missing packaged asset: {source_path}")
    return InstallAction(
        relative_path=Path(relative_path),
        source_path=source_path,
        strategy="managed-block",
    )


def managed_content_action(relative_path: str, content: str) -> InstallAction:
    return InstallAction(
        relative_path=Path(relative_path),
        content=content,
        strategy="managed-block",
    )


def template_file_action(relative_path: str, source_path: Path) -> InstallAction:
    if not source_path.is_file():
        raise ValueError(f"missing packaged asset: {source_path}")
    return InstallAction(
        relative_path=Path(relative_path),
        source_path=source_path,
        strategy="template",
    )


def gitkeep_action(relative_path: str) -> InstallAction:
    return InstallAction(
        relative_path=Path(relative_path),
        content="",
    )


def openspec_config_action() -> InstallAction:
    return InstallAction(
        relative_path=OPENSPEC_CONFIG_PATH,
        content=f"schema: {OPENSPEC_SCHEMA_NAME}\n",
        strategy="openspec-config",
    )


def keel_config_action() -> InstallAction:
    return InstallAction(
        relative_path=KEEL_CONFIG_PATH,
        content=KEEL_CONFIG_TEMPLATE,
        strategy="keel-config-scaffold",
    )


def keel_gitignore_action() -> InstallAction:
    return InstallAction(
        relative_path=KEEL_GITIGNORE_PATH,
        content=KEEL_GITIGNORE_TEMPLATE,
        strategy="keel-config-scaffold",
    )


def read_fast_check(repo: Path) -> str | None:
    """Return the project's declared fast inner-loop command, or None.

    Parses keel/config.yaml with the same flat-key style Keel uses elsewhere;
    a commented `# fast_check:` line does not count as declared.
    """
    config_path = repo / KEEL_CONFIG_PATH
    if not config_path.is_file():
        return None
    for line in config_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        match = re.match(r"fast_check\s*:\s*(.+?)\s*$", stripped)
        if match:
            return match.group(1)
    return None


def is_git_repo(repo: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def git_config_get(repo: Path, key: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo), "config", "--local", "--get", key],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def pre_push_hook_content(fast_check: str) -> str:
    return (
        "#!/bin/sh\n"
        "# Managed by keel --install --with-git-hooks: the fast inner-loop check.\n"
        "# The full or slow suite belongs to CI or `keel gate change-close`.\n"
        f"exec {fast_check}\n"
    )


def apply_git_hooks(repo: Path, dry_run: bool) -> int:
    if not is_git_repo(repo):
        print(
            "keel --install --with-git-hooks: not a git repository; run "
            "`git init` first",
            file=sys.stderr,
        )
        return 1
    fast_check = read_fast_check(repo)
    if fast_check is None:
        print(
            "keel --install --with-git-hooks: no fast_check declared in "
            f"{KEEL_CONFIG_PATH.as_posix()}; add a `fast_check:` line, then rerun",
            file=sys.stderr,
        )
        return 1
    if dry_run:
        print(
            f"would write {PRE_PUSH_PATH.as_posix()} running the fast_check and "
            f"set core.hooksPath to {GITHOOKS_DIR}"
        )
        return 0
    hook_path = repo / PRE_PUSH_PATH
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(pre_push_hook_content(fast_check), encoding="utf-8")
    os.chmod(hook_path, 0o755)
    result = subprocess.run(
        ["git", "-C", str(repo), "config", "--local", "core.hooksPath", GITHOOKS_DIR],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(
            "keel --install --with-git-hooks: failed to set core.hooksPath: "
            + (result.stderr.strip() or "git config error"),
            file=sys.stderr,
        )
        return 1
    print(
        f"git hooks: wrote {PRE_PUSH_PATH.as_posix()} (runs the fast_check) and "
        f"set core.hooksPath to {GITHOOKS_DIR}"
    )
    return 0


def revert_git_hooks(repo: Path, dry_run: bool) -> None:
    """Unset core.hooksPath only when Keel is the one that set it to .githooks."""
    if not is_git_repo(repo):
        return
    if git_config_get(repo, "core.hooksPath") != GITHOOKS_DIR:
        return
    if dry_run:
        print(f"would unset core.hooksPath (currently {GITHOOKS_DIR})")
        return
    subprocess.run(
        ["git", "-C", str(repo), "config", "--local", "--unset", "core.hooksPath"],
        capture_output=True,
        text=True,
    )
    print(f"git hooks: unset core.hooksPath (was {GITHOOKS_DIR})")


def openspec_schema_actions() -> list[InstallAction]:
    schema_root = PACKAGE_ROOT / OPENSPEC_ASSET_ROOT / "schemas" / OPENSPEC_SCHEMA_NAME
    if not schema_root.is_dir():
        raise ValueError(f"missing packaged OpenSpec schema: {schema_root}")

    actions: list[InstallAction] = []
    for schema_file in sorted(schema_root.rglob("*")):
        if not schema_file.is_file():
            continue
        relative_file = schema_file.relative_to(schema_root).as_posix()
        actions.append(
            file_action(
                (OPENSPEC_SCHEMA_ROOT / relative_file).as_posix(),
                schema_file,
            )
        )
    return actions


def agent_actions(target: str) -> list[InstallAction]:
    actions: list[InstallAction] = []
    if "claude" not in target_set(target):
        return actions
    agents_root = dist_asset("claude", "agents")
    if not agents_root.is_dir():
        return actions
    for agent in sorted(agents_root.iterdir()):
        if not agent.is_dir():
            continue
        for agent_file in sorted(agent.rglob("*")):
            if not agent_file.is_file():
                continue
            relative_file = agent_file.relative_to(agent).as_posix()
            actions.append(
                file_action(
                    f".claude/agents/{agent.name}/{relative_file}",
                    agent_file,
                )
            )
    return actions


def adapter_actions(target: str) -> list[InstallAction]:
    actions: list[InstallAction] = []
    for target_name in target_names(target):
        source = dist_asset(target_name, "adapters", "keel-adapter.js")
        actions.append(
            file_action(TARGET_ADAPTER_PATHS[target_name].as_posix(), source)
        )
    return actions


def keel_hook_source_root() -> Path:
    source = dist_asset("claude", "hooks", KEEL_HOOK_NAME)
    if not source.is_dir():
        raise ValueError(f"missing packaged Keel hook: {source}")
    if not (source / "hooks.json").is_file():
        raise ValueError(f"missing packaged Keel hook config: {source / 'hooks.json'}")
    return source


def keel_hook_actions(target: str) -> list[InstallAction]:
    if "claude" not in target_set(target):
        return []
    source_root = keel_hook_source_root()
    actions = [
        file_action(
            (KEEL_HOOK_ROOT / source.relative_to(source_root)).as_posix(),
            source,
        )
        for source in sorted(source_root.rglob("*"))
        if source.is_file()
    ]
    actions.append(
        InstallAction(
            relative_path=Path(".claude/settings.json"),
            source_path=source_root / "hooks.json",
            strategy="keel-hook-settings",
        )
    )
    return actions


def unmanaged_keel_content_warning(repo: Path, relative_path: str) -> bool:
    path = repo / relative_path
    if not path.is_file():
        return False
    content = path.read_text(encoding="utf-8")
    if MANAGED_START_RE.search(content):
        return False
    if "keel gate task-start" in content or "keel context" in content:
        print(
            f"preserve {relative_path}: Keel-looking resident content has no "
            "managed markers and cannot be matched to a known managed version; "
            "resolve it manually before Keel merges the v4 bootstrap"
        )
        return True
    return False


KEEL_PACKAGE_NAME = "@christang/keel"


def is_keel_source_repo(repo: Path) -> bool:
    """Whether `repo` is Keel's own source repository.

    Mirrors `isKeelSourceRepo` in src/core/capabilities.js. Both signals are
    required so a project that merely vendors a plugins/keel/ directory is not
    misclassified as Keel's own source.
    """
    try:
        manifest = json.loads((repo / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if manifest.get("name") != KEEL_PACKAGE_NAME:
        return False
    return (repo / "plugins" / "keel").is_dir()


def collect_actions(repo: Path, target: str) -> list[InstallAction]:
    actions: list[InstallAction] = []
    targets = target_set(target)

    # Keel's own AGENTS.md carries the full protocol that the validation suite
    # asserts on; the packaged bootstrap is the shorter consumer-facing text.
    # Writing it here replaces the protocol and turns the repository red.
    if is_keel_source_repo(repo):
        print(
            "skip AGENTS.md: Keel source repository, whose AGENTS.md carries "
            "the full protocol; the consumer bootstrap is not written here"
        )
    elif not unmanaged_keel_content_warning(repo, "AGENTS.md"):
        actions.append(
            managed_file_action("AGENTS.md", PACKAGE_ROOT / BOOTSTRAP_ASSET)
        )
    if "claude" in targets and not unmanaged_keel_content_warning(repo, "CLAUDE.md"):
        actions.append(managed_content_action("CLAUDE.md", CLAUDE_IMPORT_BLOCK))

    actions.append(openspec_config_action())
    actions.append(keel_config_action())
    actions.append(keel_gitignore_action())
    actions.extend(openspec_schema_actions())
    return actions


def has_managed_block(path: Path) -> bool:
    if not path.is_file():
        return False
    return extract_managed_block(path.read_text(encoding="utf-8")) is not None


def has_openspec_schema_config(repo: Path) -> bool:
    config_path = repo / OPENSPEC_CONFIG_PATH
    if not config_path.is_file():
        return False
    config = config_path.read_text(encoding="utf-8")
    return re.search(rf"(?m)^\s*schema\s*:\s*{re.escape(OPENSPEC_SCHEMA_NAME)}\s*$", config) is not None


def is_keel_hook_handler(handler: object) -> bool:
    if not isinstance(handler, dict) or handler.get("command") != "node":
        return False
    args = handler.get("args")
    return isinstance(args, list) and any(
        isinstance(arg, str) and ".claude/hooks/keel-gate/keel-gate.js" in arg
        for arg in args
    )


def has_keel_hook_settings(repo: Path) -> bool:
    settings_path = repo / ".claude/settings.json"
    if not settings_path.is_file():
        return False
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return False
    groups = hooks.get("UserPromptExpansion")
    return isinstance(groups, list) and any(
        isinstance(group, dict)
        and isinstance(group.get("hooks"), list)
        and any(is_keel_hook_handler(handler) for handler in group["hooks"])
        for group in groups
    )


def check_status_items(repo: Path, target: str) -> list[tuple[str, bool]]:
    items: list[tuple[str, bool]] = []
    targets = target_set(target)
    items.append(("AGENTS.md bootstrap", has_managed_block(repo / "AGENTS.md")))
    if "claude" in targets:
        claude_path = repo / "CLAUDE.md"
        items.append(
            (
                "CLAUDE.md @AGENTS.md import",
                claude_path.is_file()
                and "@AGENTS.md" in claude_path.read_text(encoding="utf-8"),
            )
        )

    items.append(
        (
            f"{OPENSPEC_CONFIG_PATH.as_posix()} schema {OPENSPEC_SCHEMA_NAME}",
            has_openspec_schema_config(repo),
        )
    )
    for action in openspec_schema_actions():
        items.append((action.relative_path.as_posix(), (repo / action.relative_path).is_file()))
    return items


def line_number_for_offset(content: str, offset: int) -> int:
    return content.count("\n", 0, offset) + 1


def inspect_handoff(repo: Path) -> tuple[str, str, list[str]]:
    handoff_path = repo / HANDOFF_PATH
    if not handoff_path.is_file():
        return (
            "absent",
            "normal; keel context will infer from OpenSpec",
            [],
        )

    try:
        content = handoff_path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        message = "keel/HANDOFF.md is not valid UTF-8"
        return ("invalid", message, [message])
    if not content.startswith(("---\n", "---\r\n")):
        return (
            "legacy",
            "preserved byte-for-byte; migrate to keel-handoff/v1 or clear with "
            "keel context --clear-handoff",
            [],
        )
    match = re.fullmatch(
        r"---\r?\n(?P<front>[\s\S]*?)\r?\n---(?:\r?\n)?",
        content,
    )
    if match is None:
        message = "keel/HANDOFF.md has invalid or non-pointer v1 content"
        return ("invalid", message, [message])

    fields: dict[str, str] = {}
    for line in match.group("front").splitlines():
        if not line.strip():
            continue
        field = re.fullmatch(r"([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*", line)
        if field is None or field.group(1) in fields:
            message = "keel/HANDOFF.md has invalid v1 front matter"
            return ("invalid", message, [message])
        fields[field.group(1)] = field.group(2).strip("\"'")

    if fields.get("schema") != "keel-handoff/v1":
        return (
            "legacy",
            "preserved byte-for-byte; migrate to keel-handoff/v1 or clear with "
            "keel context --clear-handoff",
            [],
        )
    if set(fields) != HANDOFF_FIELDS or not all(fields.values()):
        message = "keel/HANDOFF.md v1 must contain only schema, owner, action, and reason"
        return ("invalid", message, [message])
    if fields["action"] not in HANDOFF_ACTIONS:
        message = f"keel/HANDOFF.md has unsupported action: {fields['action']}"
        return ("invalid", message, [message])
    if HANDOFF_OWNER_RE.fullmatch(fields["owner"]) is None:
        message = f"keel/HANDOFF.md has unsupported owner: {fields['owner']}"
        return ("invalid", message, [message])
    owner_path = fields["owner"].split("#", 1)[0]
    if not (repo / owner_path).is_file():
        message = f"keel/HANDOFF.md owner is missing: {fields['owner']}"
        return ("invalid", message, [message])
    return ("v1", f"validated override -> {fields['owner']}", [])


def report_handoff_status(repo: Path) -> list[str]:
    state, detail, errors = inspect_handoff(repo)
    print(f"handoff: {state} - {detail}")
    return errors


def is_tasks_rule_line(line: str) -> bool:
    normalized = line.strip().lstrip("> ").lower()
    return any(
        phrase in normalized
        for phrase in (
            "do not record",
            "must not record",
            "not record",
            "source of truth",
            "belongs in keel/handoff.md",
            "不在此记录",
            "不写入",
            "不要记录",
            "唯一真相源",
        )
    )


# The task contract compiler's own field bound, from `parseTasks()` in
# `src/core/task-contract.js`: a field starts at a two-space `- Name:` line and
# holds every line until the next one. Keeping the two readers on one rule is
# what stops a line being a Covers entry for the compiler and prose for this
# check.
TASKS_FIELD_LABEL_RE = re.compile(r"^ {2}- ([A-Za-z][A-Za-z /-]+):")


def covers_field_lines(content: str) -> set[int]:
    """1-based line numbers inside a `Covers` field.

    A Covers entry is a citation — its segments must resolve to a requirement
    or scenario that exists in a spec — so naming a requirement about dirty
    worktrees or commit identifiers is not recording one. Read as prose, those
    citations left an author no repair but to rename the requirement, which is
    what 5.19.0 did and what #65 reports. Every citation is written on a line
    below the label, so the exempt region is the field and not the label line.
    """
    inside = False
    lines: set[int] = set()
    for number, line in enumerate(content.splitlines(), start=1):
        label = TASKS_FIELD_LABEL_RE.match(line)
        if label is not None:
            inside = label.group(1) == "Covers"
        if inside:
            lines.add(number)
    return lines


# What an author quotes is content they cite, not a claim they make. Evidence
# prose quotes the command that ran, the output it printed, the branch base it
# ran against, and the name of the requirement under change — and every one of
# those carries exactly the words these rules refuse. `withoutInlineCode()` in
# `src/core/task-contract.js` settled this shape for the field reader; the two
# reports that reached this reader (#65 items 2 and 4) are the same shape
# arriving late.
#
# The ASCII single quote is deliberately absent. It is an apostrophe far more
# often than a quotation mark, and a span opened by `doesn't` would silence the
# remainder of the line — a rule that stops running without saying so, which is
# the failure no fixture catches by accident.
QUOTED_SPAN_RE = re.compile(
    r"`[^`\n]*`"
    r"|\"[^\"\n]*\""
    r"|\u201c[^\u201d\n]*\u201d"
    r"|\u300c[^\u300d\n]*\u300d"
    r"|\u300a[^\u300b\n]*\u300b"
)
FENCE_RE = re.compile(r"^\s*(?:```|~~~)")


def without_quoted_spans(line: str) -> str:
    """Blank out the quoted spans of a line, leaving its length reading intact.

    The replacement is a space rather than nothing so two tokens either side of
    a span cannot be joined into a third word that neither of them was.
    """
    return QUOTED_SPAN_RE.sub(" ", line)


def check_tasks_semantics(repo: Path) -> list[str]:
    changes_root = repo / OPENSPEC_ROOT / "changes"
    if not changes_root.is_dir():
        return []

    errors: list[str] = []
    for tasks_path in sorted(changes_root.rglob("tasks.md")):
        if not tasks_path.is_file():
            continue
        if tasks_path.relative_to(changes_root).parts[0] == "archive":
            continue
        relative = tasks_path.relative_to(repo).as_posix()
        content = tasks_path.read_text(encoding="utf-8")

        for pattern, message in TASKS_LEGACY_HEADING_PATTERNS:
            match = pattern.search(content)
            if match is not None:
                line = line_number_for_offset(content, match.start())
                errors.append(f"{relative}:{line}: {message}")

        cited = covers_field_lines(content)
        fenced = False
        for line_number, line in enumerate(content.splitlines(), start=1):
            # A fenced block is one long quoted span, and its own delimiter
            # lines carry no prose. Tracking the state here rather than
            # pre-stripping the file keeps every reported line number the
            # line number the author sees.
            if FENCE_RE.match(line):
                fenced = not fenced
                continue
            if fenced or is_tasks_rule_line(line) or line_number in cited:
                continue
            line = without_quoted_spans(line)
            for pattern, message in TASKS_COMMIT_STATUS_PATTERNS:
                if pattern.search(line):
                    errors.append(f"{relative}:{line_number}: {message}")
            if TASKS_SUBMISSION_STATE_RE.search(line) and TASKS_GIT_CONTEXT_RE.search(
                line
            ):
                errors.append(
                    f"{relative}:{line_number}: {TASKS_SUBMISSION_MESSAGE}"
                )
            if TASKS_CONTEXTUAL_HASH_RE.search(line):
                errors.append(
                    f"{relative}:{line_number}: remove contextual commit hash from tasks.md; git log is the source of truth"
                )

    return errors


def report_check_status(repo: Path, target: str) -> int:
    items = check_status_items(repo, target)
    missing = [name for name, present in items if not present]
    handoff_errors = report_handoff_status(repo)

    if not missing:
        print("status: installed")
        semantic_errors = [
            *handoff_errors,
            *check_tasks_semantics(repo),
        ]
        if semantic_errors:
            print("keel state: failed")
            for error in semantic_errors:
                print(f"state-error {error}")
            return 1
        print("keel state: ok")
        return 0
    if len(missing) == len(items):
        print("status: missing")
    else:
        print("status: partial")

    for name in missing:
        print(f"missing {name}")
    return 0


def extract_managed_block(content: str) -> str | None:
    start_match = MANAGED_START_RE.search(content)
    if start_match is None:
        return None
    end = content.find(MANAGED_END, start_match.end())
    if end == -1:
        return None
    return content[start_match.start() : end + len(MANAGED_END)]


def remove_managed_block(content: str) -> tuple[str, bool]:
    block = extract_managed_block(content)
    if block is None:
        return content, False
    return content.replace(block, "", 1), True


def merge_managed_block(existing: str, source: str) -> tuple[str, str]:
    source_block = extract_managed_block(source)
    if source_block is None:
        raise ValueError("packaged managed-block file is missing keel managed markers")

    existing_block = extract_managed_block(existing)
    if existing_block is None:
        separator = "" if existing.endswith("\n") or not existing else "\n"
        return existing + separator + source_block + "\n", "append"

    if existing_block == source_block:
        return existing, "skip"

    return existing.replace(existing_block, source_block, 1), "update"


def merge_openspec_config(existing: str) -> tuple[str, str]:
    desired_line = f"schema: {OPENSPEC_SCHEMA_NAME}"
    schema_re = re.compile(r"(?m)^(\s*schema\s*:\s*).*$")
    match = schema_re.search(existing)
    if match is None:
        separator = "" if existing.startswith("\n") or not existing else "\n"
        updated = desired_line + "\n" + separator + existing
        return updated, "update"

    current_line = match.group(0).strip()
    if current_line == desired_line:
        return existing, "skip"

    updated = existing[: match.start()] + desired_line + existing[match.end() :]
    return updated, "update"


def template_checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def template_payload(content: str) -> str:
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


def action_source_content(action: InstallAction) -> str:
    if action.source_path is not None:
        return action.source_path.read_text(encoding="utf-8")
    return action.content or ""


def load_hook_config(content: str) -> dict:
    try:
        config = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Keel hook config is not valid JSON: {exc}") from exc
    if not isinstance(config, dict) or not isinstance(config.get("hooks"), dict):
        raise ValueError("Keel hook config must contain an object field 'hooks'")
    return config


def remove_keel_hook_handlers(groups: object) -> list[object]:
    if not isinstance(groups, list):
        raise ValueError("existing Claude settings hooks event must be an array")
    kept_groups: list[object] = []
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
            kept_groups.append(group)
            continue
        kept_handlers = [
            handler for handler in group["hooks"] if not is_keel_hook_handler(handler)
        ]
        if kept_handlers:
            updated = dict(group)
            updated["hooks"] = kept_handlers
            kept_groups.append(updated)
    return kept_groups


def merge_keel_hook_settings(existing: str, source: str) -> tuple[str, str]:
    config = load_hook_config(source)
    if not existing.strip():
        settings: dict = {}
    else:
        try:
            settings = json.loads(existing)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"cannot merge Keel Hook into .claude/settings.json because it is not valid JSON: {exc}"
            ) from exc
        if not isinstance(settings, dict):
            raise ValueError("cannot merge Keel Hook into .claude/settings.json because it is not a JSON object")

    hooks = settings.get("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("cannot merge Keel Hook because .claude/settings.json field 'hooks' is not an object")
    hooks = dict(hooks)
    for event, keel_groups in config["hooks"].items():
        if not isinstance(keel_groups, list):
            raise ValueError(f"Keel hook config event {event!r} must be an array")
        existing_groups = remove_keel_hook_handlers(hooks.get(event, [])) if event in hooks else []
        hooks[event] = [*existing_groups, *keel_groups]
    settings = dict(settings)
    settings["hooks"] = hooks
    merged = json.dumps(settings, indent=2, ensure_ascii=False) + "\n"
    existing_normalized = json.dumps(json.loads(existing), indent=2, ensure_ascii=False) + "\n" if existing.strip() else ""
    return merged, "skip" if existing_normalized == merged else "update"


def remove_keel_hook_settings(existing: str) -> tuple[str, str]:
    try:
        settings = json.loads(existing)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"cannot remove Keel Hook from .claude/settings.json because it is not valid JSON: {exc}"
        ) from exc
    if not isinstance(settings, dict):
        raise ValueError("cannot remove Keel Hook because .claude/settings.json is not a JSON object")
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return existing, "skip"
    updated_hooks = dict(hooks)
    changed = False
    for event, groups in list(updated_hooks.items()):
        if not isinstance(groups, list):
            continue
        filtered = remove_keel_hook_handlers(groups)
        if filtered != groups:
            changed = True
            if filtered:
                updated_hooks[event] = filtered
            else:
                del updated_hooks[event]
    if not changed:
        return existing, "skip"
    updated_settings = dict(settings)
    if updated_hooks:
        updated_settings["hooks"] = updated_hooks
    else:
        updated_settings.pop("hooks", None)
    return json.dumps(updated_settings, indent=2, ensure_ascii=False) + "\n", "update"


def plan_template_action(
    destination: Path,
    action: InstallAction,
    source_content: str,
    force_template_update: bool,
) -> PlannedAction:
    payload = template_payload(source_content)
    if not destination.exists():
        return PlannedAction("create", action.relative_path, payload)

    existing = destination.read_text(encoding="utf-8")
    existing_base, existing_checksum = strip_template_checksum(existing)
    current_checksum = template_checksum(source_content)

    if existing_base == source_content and existing_checksum == current_checksum:
        return PlannedAction("skip", action.relative_path)
    if force_template_update:
        return PlannedAction("update", action.relative_path, payload)
    if existing_checksum == template_checksum(existing_base):
        return PlannedAction("update", action.relative_path, payload)

    return PlannedAction("skip", action.relative_path)


def plan_action(
    repo: Path,
    action: InstallAction,
    force_template_update: bool = False,
) -> PlannedAction:
    destination = require_inside_repo(repo, action.relative_path)
    source_content = action_source_content(action)

    if action.strategy == "keel-hook-settings":
        existing = destination.read_text(encoding="utf-8") if destination.exists() else ""
        merged, kind = merge_keel_hook_settings(existing, source_content)
        return PlannedAction("create" if not destination.exists() else kind, action.relative_path, merged if kind != "skip" else None)

    if action.strategy == "template":
        return plan_template_action(
            destination,
            action,
            source_content,
            force_template_update,
        )

    if not destination.exists():
        return PlannedAction("create", action.relative_path, source_content)

    existing = destination.read_text(encoding="utf-8")
    if action.strategy == "managed-block":
        merged, kind = merge_managed_block(existing, source_content)
        return PlannedAction(kind, action.relative_path, None if kind == "skip" else merged)
    if action.strategy == "openspec-config":
        merged, kind = merge_openspec_config(existing)
        return PlannedAction(kind, action.relative_path, None if kind == "skip" else merged)
    if action.strategy == "keel-config-scaffold":
        # Scaffold once: never overwrite a project's own keel/config.yaml.
        return PlannedAction("skip", action.relative_path)

    if existing == source_content:
        return PlannedAction("skip", action.relative_path)
    return PlannedAction("update", action.relative_path, source_content)


def plan_actions(
    repo: Path,
    actions: list[InstallAction],
    force_template_update: bool = False,
) -> list[PlannedAction]:
    return [
        plan_action(repo, action, force_template_update=force_template_update)
        for action in actions
    ]


def template_matches_packaged(path: Path, source_content: str) -> bool:
    if not path.is_file():
        return False
    existing_base, existing_checksum = strip_template_checksum(
        path.read_text(encoding="utf-8")
    )
    current_checksum = template_checksum(source_content)
    return existing_base == source_content and existing_checksum in {
        None,
        current_checksum,
    }


def plan_uninstall_managed(repo: Path, relative_path: str) -> PlannedAction:
    path = require_inside_repo(repo, Path(relative_path))
    if not path.is_file():
        return PlannedAction("skip", Path(relative_path))
    updated, removed = remove_managed_block(path.read_text(encoding="utf-8"))
    if not removed:
        return PlannedAction("skip", Path(relative_path))
    return PlannedAction("remove-managed", Path(relative_path), updated)


def plan_uninstall_template(
    repo: Path,
    relative_path: str,
    source_path: Path,
) -> PlannedAction:
    path = require_inside_repo(repo, Path(relative_path))
    if not path.exists():
        return PlannedAction("skip", Path(relative_path))
    source_content = source_path.read_text(encoding="utf-8")
    if template_matches_packaged(path, source_content):
        return PlannedAction("remove", Path(relative_path))
    return PlannedAction("skip", Path(relative_path))


def directory_has_only_gitkeep(path: Path) -> bool:
    if not path.is_dir():
        return False
    entries = list(path.iterdir())
    return len(entries) == 1 and entries[0].name == ".gitkeep"


def plan_uninstall_gitkeep(repo: Path, relative_dir: str) -> list[PlannedAction]:
    directory = require_inside_repo(repo, Path(relative_dir))
    gitkeep = directory / ".gitkeep"
    if not gitkeep.is_file() or not directory_has_only_gitkeep(directory):
        return []
    return [
        PlannedAction("remove", Path(relative_dir) / ".gitkeep"),
        PlannedAction("rmdir", Path(relative_dir)),
    ]


def plan_uninstall_packaged_file(
    repo: Path,
    relative_path: str,
    source_path: Path,
) -> PlannedAction:
    path = require_inside_repo(repo, Path(relative_path))
    if not path.exists():
        return PlannedAction("skip", Path(relative_path))
    if not path.is_file():
        return PlannedAction("skip", Path(relative_path))
    source_content = source_path.read_text(encoding="utf-8")
    if path.read_text(encoding="utf-8") == source_content:
        return PlannedAction("remove", Path(relative_path))
    return PlannedAction("skip", Path(relative_path))


def plan_uninstall_keel_hook_settings(repo: Path) -> PlannedAction:
    relative_path = Path(".claude/settings.json")
    path = require_inside_repo(repo, relative_path)
    if not path.is_file():
        return PlannedAction("skip", relative_path)
    updated, kind = remove_keel_hook_settings(path.read_text(encoding="utf-8"))
    if kind == "update" and json.loads(updated) == {}:
        return PlannedAction("remove", relative_path)
    return PlannedAction(kind, relative_path, updated if kind != "skip" else None)


def plan_uninstall_keel_hook_actions(repo: Path, target: str) -> list[PlannedAction]:
    if "claude" not in target_set(target):
        return []
    actions: list[PlannedAction] = []
    for action in keel_hook_actions("claude"):
        if action.strategy == "keel-hook-settings":
            actions.append(plan_uninstall_keel_hook_settings(repo))
        elif action.source_path is not None:
            actions.append(
                plan_uninstall_packaged_file(
                    repo,
                    action.relative_path.as_posix(),
                    action.source_path,
                )
            )
    actions.extend(
        [
            rmdir_if_empty_action(KEEL_HOOK_ROOT.as_posix()),
            rmdir_if_empty_action(".claude/hooks"),
        ]
    )
    return actions


def plan_uninstall_empty_dir(repo: Path, relative_dir: str) -> PlannedAction:
    directory = require_inside_repo(repo, Path(relative_dir))
    if not directory.is_dir():
        return PlannedAction("skip", Path(relative_dir))
    if any(directory.iterdir()):
        return PlannedAction("skip", Path(relative_dir))
    return PlannedAction("rmdir", Path(relative_dir))


def rmdir_if_empty_action(relative_dir: str) -> PlannedAction:
    return PlannedAction("rmdir", Path(relative_dir))


def plan_uninstall_agent_actions(repo: Path, target: str) -> list[PlannedAction]:
    actions: list[PlannedAction] = []
    if "claude" not in target_set(target):
        return actions
    for action in agent_actions(target):
        if action.source_path is None:
            continue
        actions.append(
            plan_uninstall_packaged_file(
                repo,
                action.relative_path.as_posix(),
                action.source_path,
            )
        )

    agent_dirs: set[Path] = set()
    for action in agent_actions(target):
        parent = action.relative_path.parent
        while parent != Path(".claude/agents"):
            agent_dirs.add(parent)
            parent = parent.parent
    for agent_dir in sorted(agent_dirs, key=lambda path: len(path.parts), reverse=True):
        actions.append(rmdir_if_empty_action(agent_dir.as_posix()))
    actions.append(rmdir_if_empty_action(".claude/agents"))
    return actions


def plan_uninstall_actions(repo: Path, target: str) -> list[PlannedAction]:
    actions: list[PlannedAction] = []
    targets = target_set(target)
    actions.append(plan_uninstall_managed(repo, "AGENTS.md"))
    if "claude" in targets:
        actions.append(plan_uninstall_managed(repo, "CLAUDE.md"))

    for action in openspec_schema_actions():
        if action.source_path is not None:
            actions.append(
                plan_uninstall_packaged_file(
                    repo,
                    action.relative_path.as_posix(),
                    action.source_path,
                )
            )
    actions.append(rmdir_if_empty_action((OPENSPEC_SCHEMA_ROOT / "templates").as_posix()))
    actions.append(rmdir_if_empty_action(OPENSPEC_SCHEMA_ROOT.as_posix()))
    actions.append(rmdir_if_empty_action((OPENSPEC_ROOT / "schemas").as_posix()))
    actions.append(rmdir_if_empty_action((KEEL_ROOT / "backlog").as_posix()))
    actions.append(rmdir_if_empty_action((KEEL_ROOT / "templates").as_posix()))
    actions.append(rmdir_if_empty_action(KEEL_ROOT.as_posix()))
    return actions


def describe_actions(actions: list[PlannedAction]) -> None:
    for action in actions:
        print(f"{action.kind} {action.relative_path.as_posix()}")


def apply_actions(repo: Path, actions: list[PlannedAction]) -> None:
    for action in actions:
        if action.kind == "skip":
            continue
        destination = require_inside_repo(repo, action.relative_path)
        if action.kind == "remove":
            if destination.is_file():
                destination.unlink()
            continue
        if action.kind == "rmdir":
            if destination.is_dir() and not any(destination.iterdir()):
                destination.rmdir()
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(action.content or "", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", help="Target repository path.")
    parser.add_argument(
        "--target",
        choices=["both", "claude", "codex", "opencode"],
        default="claude",
        help="Protocol target to install. Defaults to claude; both is a legacy alias for claude.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report planned actions without modifying files.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report installed, partial, or missing status without modifying files.",
    )
    parser.add_argument(
        "--force-template-update",
        action="store_true",
        help="Overwrite user-edited keel templates during install or project refresh.",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove managed protocol blocks and safe generated skeleton files.",
    )
    parser.add_argument(
        "--with-git-hooks",
        action="store_true",
        help=(
            "Generate .githooks/pre-push from the declared fast_check and set "
            "core.hooksPath (install only); refuses without a fast_check."
        ),
    )
    parser.add_argument(
        "--profile",
        action="append",
        help="Obsolete; domain guidance is now user-authored lenses in keel/lenses/*.md.",
    )
    args = parser.parse_args()

    try:
        repo = Path(args.repo).resolve()
        if args.profile:
            print(
                "Install failed: --profile is no longer supported; web, hardware, "
                "and hardware-dsl guidance is now user-authored lenses in "
                "keel/lenses/*.md (scaffold with `keel lenses add`)",
                file=sys.stderr,
            )
            return 1
        if args.check:
            return report_check_status(repo, args.target)
        if args.uninstall:
            actions = plan_uninstall_actions(repo, args.target)
            describe_actions(actions)
            if not args.dry_run:
                apply_actions(repo, actions)
            revert_git_hooks(repo, args.dry_run)
            return 0
        repo.mkdir(parents=True, exist_ok=True)
        actions = plan_actions(
            repo,
            collect_actions(repo, args.target),
            force_template_update=args.force_template_update,
        )
        describe_actions(actions)
        report_handoff_status(repo)
        if not args.dry_run:
            apply_actions(repo, actions)
        if args.with_git_hooks:
            return apply_git_hooks(repo, args.dry_run)
        return 0
    except ValueError as exc:
        print(f"Install failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

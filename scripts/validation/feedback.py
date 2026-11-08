"""Issue #505: `keel feedback` drafts, redacts, searches and (under a declaration or a confirmation) creates."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

from validation.common import ROOT, report, run_keel, write_authorize_config, write_text

KEEL_REPO = "TanglmChris/keel"
CREATED_URL = f"https://github.com/{KEEL_REPO}/issues/999"


def version() -> str:
    return json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]


def secret(*parts: str) -> str:
    """Join pieces so this file holds no literal that looks like a credential."""
    return "".join(parts)


@contextmanager
def feedback_world(prefix: str, *, with_gh: bool = True):
    """A scratch git project that is not Keel, a stub `gh`, and an environment that finds both.

    Yields `(project, env, log, bin_dir)`. The stub logs its arguments, prints
    `list.json` for `issue list` and a fixed URL for `issue create`, and with a
    `fail` file beside it prints `gh: not logged in` and exits 1.
    """
    with tempfile.TemporaryDirectory(prefix=prefix) as raw:
        base = Path(raw).resolve()
        project = base / "secret-project-name"
        project.mkdir()
        for args in (["init", "-q", "-b", "main"], ["config", "user.email", "t@example.invalid"], ["config", "user.name", "t"]):
            subprocess.run(["git", *args], cwd=project, check=True, capture_output=True)
        home = base / "home"
        home.mkdir()
        bin_dir = base / "stub-bin"
        bin_dir.mkdir()
        for tool in ("node", "git", "cat"):
            found = shutil.which(tool)
            (bin_dir / tool).symlink_to(found)
        log = base / "gh.log"
        if with_gh:
            script = bin_dir / "gh"
            script.write_text(
                "#!/bin/sh\n"
                f'echo "$*" >> "{log}"\n'
                'case "$1 $2" in\n'
                f'  "issue list"|"issue create") if [ -f "{bin_dir}/fail" ]; then echo "gh: not logged in" >&2; exit 1; fi ;;\n'
                "esac\n"
                'case "$1 $2" in\n'
                f'  "issue list") cat "{bin_dir}/list.json" ;;\n'
                f'  "issue create") echo "{CREATED_URL}" ;;\n'
                "esac\n",
                encoding="utf-8",
            )
            script.chmod(0o755)
            write_text(bin_dir / "list.json", "[]")
        env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE", "KEEL_"))}
        env["PATH"] = str(bin_dir)
        env["HOME"] = str(home)
        yield project, env, log, bin_dir


def gh_log(log: Path) -> str:
    return log.read_text(encoding="utf-8") if log.exists() else ""


def saved_file(stdout: str) -> Path | None:
    match = re.search(r"^Saved: (\S+)$", stdout, re.MULTILINE)
    return Path(match.group(1)) if match else None


def validate_feedback_draft_scenario() -> int:
    """Issue #505: a draft carries the version, the command and its output, and creates nothing."""
    label = "feedback-draft:"
    with feedback_world("keel-feedback-draft-") as (project, env, log, _bin):
        write_text(project / "out.txt", "keel gate: FAILED no task 1.1 in the change\n")
        result = run_keel(
            project, "feedback", "gate refuses a valid task",
            "--command", "keel gate task-start", "--output-file", "out.txt",
            "--expected", "the gate passes", "--repro", "run it in the project", "--impact", "blocks the work",
            env=env,
        )
        if result.returncode != 0:
            report(f"{label} exit {result.returncode}: {result.stdout}{result.stderr}")
            return 1
        out = result.stdout
        needles = (
            version(), "keel gate task-start", "no task 1.1 in the change", "gate refuses a valid task",
            "现象", "期望", "复现", "证据", "影响", "环境", "the gate passes", "blocks the work",
        )
        missing = [n for n in needles if n not in out]
        if missing:
            report(f"{label} the draft lacks {missing!r}: {out}")
            return 1
        saved = saved_file(out)
        if saved is None:
            report(f"{label} the draft does not name the file it saved: {out}")
            return 1
        if not saved.exists():
            report(f"{label} the file {saved} the draft names does not exist.")
            return 1
        if "no task 1.1 in the change" not in saved.read_text(encoding="utf-8"):
            report(f"{label} the saved file does not hold the output: {saved}")
            return 1
        if "issue create" in gh_log(log):
            report(f"{label} a draft without --create asked gh to create an issue: {gh_log(log)}")
            return 1
        for private in ("secret-project-name", "origin"):
            if private in out:
                report(f"{label} the draft holds {private!r}, project content nobody asked to publish: {out}")
                return 1
    report("feedback-draft scenario passed.")
    return 0


def validate_feedback_redacts_scenario() -> int:
    """Issue #505: tokens, Slack IDs, e-mail, credentials and local paths never reach the draft."""
    label = "feedback-redacts:"
    with feedback_world("keel-feedback-redact-") as (project, env, log, _bin):
        home = Path(env["HOME"])
        secrets = {
            "a GitHub token": secret("gh", "p_", "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"),
            "a Slack bot token": secret("xo", "xb-", "1234567890-abcdefghijklmnop"),
            "a Slack user ID": secret("U", "01ABC", "DE23F"),
            "a bearer credential": secret("Bearer ", "abcdef0123456789zz"),
            "a key=value secret": secret("hunt", "er2"),
            "an e-mail address": secret("someone", "@", "example.org"),
            "a URL password": secret("pa", "ssw0rd9"),
        }
        lines = [
            f"token was {secrets['a GitHub token']} and {secrets['a Slack bot token']}",
            f"posted as {secrets['a Slack user ID']} to the channel",
            f"Authorization: {secrets['a bearer credential']}",
            f"API_KEY={secrets['a key=value secret']}",
            f"contact {secrets['an e-mail address']}",
            f"clone https://deploy:{secrets['a URL password']}@git.example.org/x.git",
            f"read {home}/notes/private.txt and {project}/src/a.js",
            "The Gate refused TASK 12 at line 4 with UNREADABLE input",
        ]
        write_text(project / "out.txt", "\n".join(lines) + "\n")
        result = run_keel(project, "feedback", "output leaks", "--output-file", "out.txt", env=env)
        if result.returncode != 0:
            report(f"{label} exit {result.returncode}: {result.stdout}{result.stderr}")
            return 1
        saved = saved_file(result.stdout)
        if saved is None or not saved.exists():
            report(f"{label} no saved file: {result.stdout}")
            return 1
        shown = result.stdout + saved.read_text(encoding="utf-8")
        for what, value in secrets.items():
            if value in shown:
                report(f"{label} {what} reached the draft or the saved file: {value!r}")
                return 1
        if not re.search(r"[Rr]edacted \d+", result.stdout):
            report(f"{label} the draft does not report how many values it redacted: {result.stdout}")
            return 1
        for expected in ("~/notes/private.txt", "<project>/src/a.js"):
            if expected not in shown:
                report(f"{label} the draft lacks the shortened path {expected!r}: {shown}")
                return 1
        if "The Gate refused TASK 12 at line 4 with UNREADABLE input" not in shown:
            report(f"{label} ordinary prose was changed by the redaction: {shown}")
            return 1
    report("feedback-redacts scenario passed.")
    return 0


def validate_feedback_duplicates_scenario() -> int:
    """Issue #505: near-duplicates are listed first, and Keel runs no comment."""
    label = "feedback-duplicates:"
    with feedback_world("keel-feedback-dup-") as (project, env, log, bin_dir):
        write_text(bin_dir / "list.json", json.dumps([
            {"number": 12, "title": "the push guard refuses a tag", "state": "OPEN", "url": f"https://github.com/{KEEL_REPO}/issues/12"},
        ]))
        result = run_keel(project, "feedback", "push guard refuses tag pushes", env=env)
        if result.returncode != 0:
            report(f"{label} exit {result.returncode}: {result.stdout}{result.stderr}")
            return 1
        for needle in ("#12", "the push guard refuses a tag", f"https://github.com/{KEEL_REPO}/issues/12", "gh issue comment 12"):
            if needle not in result.stdout:
                report(f"{label} the draft lacks {needle!r}: {result.stdout}")
                return 1
        recorded = gh_log(log)
        if f"issue list --repo {KEEL_REPO}" not in recorded:
            report(f"{label} the duplicate search was not run against {KEEL_REPO}: {recorded!r}")
            return 1
        if "issue comment" in recorded:
            report(f"{label} Keel ran a comment: {recorded!r}")
            return 1
    report("feedback-duplicates scenario passed.")
    return 0


def creations(log: Path) -> list[str]:
    return [line for line in gh_log(log).splitlines() if line.startswith("issue create")]


def validate_feedback_create_scenario() -> int:
    """Issue #505: --create needs the declaration or a confirmation, and adds no label."""
    label = "feedback-create:"
    with feedback_world("keel-feedback-create-") as (project, env, log, _bin):
        refused = run_keel(project, "feedback", "gate refuses a valid task", "--create", env=env)
        if refused.returncode != 3:
            report(f"{label} --create with no declaration and no --confirmed exited {refused.returncode}, not 3: {refused.stdout}{refused.stderr}")
            return 1
        if "Title:" not in refused.stdout:
            report(f"{label} the refusal did not print the draft: {refused.stdout}")
            return 1
        if creations(log):
            report(f"{label} a refused --create still ran gh: {gh_log(log)!r}")
            return 1
        confirmed = run_keel(project, "feedback", "gate refuses a valid task", "--create", "--confirmed", env=env)
        if confirmed.returncode != 0:
            report(f"{label} --create --confirmed exited {confirmed.returncode}: {confirmed.stdout}{confirmed.stderr}")
            return 1
        if CREATED_URL not in confirmed.stdout:
            report(f"{label} the new issue's URL was not printed: {confirmed.stdout}")
            return 1
        made = creations(log)
        if len(made) != 1:
            report(f"{label} --confirmed ran {len(made)} creations: {gh_log(log)!r}")
            return 1
        for needle in (f"--repo {KEEL_REPO}", "--title", "--body-file"):
            if needle not in made[0]:
                report(f"{label} the creation lacks {needle!r}: {made[0]!r}")
                return 1
        for forbidden in ("--label", "--assignee", "--milestone"):
            if forbidden in made[0]:
                report(f"{label} the creation carries {forbidden}: {made[0]!r}")
                return 1
        write_authorize_config(project, "authorize:\n  - issue:acme/widgets\n")
        elsewhere = run_keel(project, "feedback", "gate refuses a valid task", "--create", env=env)
        if elsewhere.returncode != 3:
            report(f"{label} a declaration for another repository exited {elsewhere.returncode}, not 3: {elsewhere.stdout}")
            return 1
        write_authorize_config(project, f"authorize:\n  - issue:{KEEL_REPO}\n")
        declared = run_keel(project, "feedback", "gate refuses a valid task", "--create", env=env)
        if declared.returncode != 0:
            report(f"{label} the declared project was refused ({declared.returncode}): {declared.stdout}{declared.stderr}")
            return 1
        if len(creations(log)) != 2:
            report(f"{label} the declared project did not create exactly one more issue: {gh_log(log)!r}")
            return 1
    report("feedback-create scenario passed.")
    return 0


def validate_feedback_gh_missing_scenario() -> int:
    """Issue #505: no usable gh loses nothing."""
    label = "feedback-gh-missing:"
    attempts = (("no gh on PATH", False, None), ("a gh that is not logged in", True, "fail"))
    for what, with_gh, marker in attempts:
        with feedback_world("keel-feedback-nogh-", with_gh=with_gh) as (project, env, log, bin_dir):
            if marker:
                write_text(bin_dir / marker, "")
            draft = run_keel(project, "feedback", "gate refuses a valid task", env=env)
            if draft.returncode != 0:
                report(f"{label} with {what} the draft exited {draft.returncode}: {draft.stdout}{draft.stderr}")
                return 1
            if "not searched" not in draft.stdout:
                report(f"{label} with {what} the draft does not say the search was not run: {draft.stdout}")
                return 1
            created = run_keel(project, "feedback", "gate refuses a valid task", "--create", "--confirmed", env=env)
            if created.returncode != 4:
                report(f"{label} with {what} --create --confirmed exited {created.returncode}, not 4: {created.stdout}{created.stderr}")
                return 1
            saved = saved_file(created.stdout)
            if saved is None or not saved.exists():
                report(f"{label} with {what} the draft was lost: {created.stdout}")
                return 1
            if f"gh issue create --repo {KEEL_REPO}" not in created.stdout:
                report(f"{label} with {what} no command to run was printed: {created.stdout}")
                return 1
    report("feedback-gh-missing scenario passed.")
    return 0


def validate_feedback_command_surface_scenario() -> int:
    """Issue #505: the slash command orders the steps, and the docs list it."""
    label = "feedback-command-surface:"
    command = ROOT / "plugins/keel/commands/feedback.md"
    if not command.exists():
        report(f"{label} {command.relative_to(ROOT)} does not exist.")
        return 1
    text = command.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        report(f"{label} the command file has no front matter.")
        return 1
    front = text.split("---", 2)[1]
    for key in ("description:", "argument-hint:"):
        if key not in front:
            report(f"{label} the command file's front matter lacks {key}")
            return 1
    for needle in ("keel feedback", "--create", "--confirmed", "$ARGUMENTS", "no label", "comment"):
        if needle not in text:
            report(f"{label} the command file lacks {needle!r}.")
            return 1
    for answer in ("new issue", "add to", "cancel"):
        if answer not in text.lower():
            report(f"{label} the command file does not offer the answer {answer!r}.")
            return 1
    for doc, count in (("docs/commands.md", "six"), ("docs/commands.zh-CN.md", "六个")):
        body = (ROOT / doc).read_text(encoding="utf-8")
        if "/keel:feedback" not in body:
            report(f"{label} {doc} does not list /keel:feedback.")
            return 1
        if count not in body:
            report(f"{label} {doc} does not say {count!r} commands.")
            return 1
    for readme in ("README.md", "README.zh-CN.md"):
        if "keel feedback" not in (ROOT / readme).read_text(encoding="utf-8"):
            report(f"{label} {readme} does not name `keel feedback`.")
            return 1
    report("feedback-command-surface scenario passed.")
    return 0

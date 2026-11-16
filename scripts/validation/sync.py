"""Scenarios for `keel sync` and the device hand-over (#526)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from validation.common import report, run_keel, write_text


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    for name in ("KEEL_CHAT_ROLE", "KEEL_MAIL_ROLE", "GIT_DIR", "GIT_WORK_TREE"):
        env.pop(name, None)
    return env


class _Repo:
    """A repository with a bare `origin`, built for the sync scenarios."""

    def __init__(self, base: Path) -> None:
        self.base = base
        self.repo = base / "repo"
        self.remote = base / "remote.git"
        self.env = _git_env()
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Sync test")
        (self.repo / "seed").write_text("base\n", encoding="utf-8")
        self.git("add", "seed")
        self.git("commit", "-qm", "base")
        self.git("init", "--bare", "-q", "-b", "main", str(self.remote))
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "-qu", "origin", "main")
        self.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")

    def git(self, *args: str, cwd: Path | None = None) -> str:
        return subprocess.run(
            ["git", *args], cwd=cwd or self.repo, env=self.env, check=True,
            capture_output=True, text=True,
        ).stdout.strip()

    def commit(self, name: str, cwd: Path | None = None) -> str:
        where = cwd or self.repo
        (where / name).write_text(f"{name}\n", encoding="utf-8")
        self.git("add", name, cwd=where)
        self.git("commit", "-qm", f"add {name}", cwd=where)
        return self.git("rev-parse", "HEAD", cwd=where)

    def chat(self) -> Path:
        return Path(self.git("rev-parse", "--path-format=absolute", "--git-common-dir")) / "keel-chat"

    def state(self) -> dict[str, object]:
        """Everything a read-only command must leave as it was."""
        chat = self.chat()
        return {
            "refs": self.git("for-each-ref", "--format=%(refname) %(objectname)"),
            "stash": self.git("stash", "list"),
            "status": self.git("status", "--porcelain=v1", "--untracked-files=all"),
            "chat": {str(f.relative_to(chat)): f.read_bytes() for f in chat.rglob("*") if f.is_file()}
            if chat.exists() else {},
            "fetch_head": (Path(self.git("rev-parse", "--path-format=absolute", "--git-common-dir")) / "FETCH_HEAD").exists(),
        }


def _unknown(label: str, result: subprocess.CompletedProcess[str]) -> int:
    report(f"{label} `keel sync status` is an unknown command here (exit {result.returncode}): "
           f"{(result.stderr or result.stdout).strip()[:300]}")
    return 1


def _populate(r: _Repo) -> dict[str, Path]:
    """feat two ahead in worktree a; scratch local-only with no worktree;
    worktree b clean branch with an untracked file; done merged; one stash."""
    a, b = r.base / "a", r.base / "b"
    r.git("worktree", "add", "-qb", "feat", str(a), "main")
    r.commit("f0", cwd=a)
    r.git("push", "-qu", "origin", "feat", cwd=a)
    r.commit("f1", cwd=a)
    r.commit("f2", cwd=a)
    r.git("branch", "scratch", "main")
    r.git("checkout", "-q", "scratch")
    r.commit("s1")
    r.git("checkout", "-q", "main")
    r.git("worktree", "add", "-qb", "clean", str(b), "main")
    r.git("push", "-qu", "origin", "clean", cwd=b)
    (b / "untracked.txt").write_text("loose\n", encoding="utf-8")
    r.git("branch", "done", "main")
    r.git("checkout", "-q", "done")
    r.commit("d1")
    r.git("push", "-q", "origin", "done:main")
    r.git("checkout", "-q", "main")
    r.git("merge", "-q", "--ff-only", "origin/main")
    (r.repo / "seed").write_text("stashed change\n", encoding="utf-8")
    r.git("stash", "push", "-q", "-m", "keep this")
    return {"a": a, "b": b}


def validate_sync_status_lists_local_only_scenario() -> int:
    """#526 D2: every kind of local-only work is listed, merged work is not."""
    label = "sync-status-lists-local-only:"
    with tempfile.TemporaryDirectory(prefix="keel-sync-list-") as raw:
        r = _Repo(Path(raw).resolve())
        trees = _populate(r)
        before = r.state()
        result = run_keel(trees["b"], "sync", "status", "--json", env=r.env)
        if result.returncode not in (0, 1) or not result.stdout.strip().startswith("{"):
            return _unknown(label, result)
        data = json.loads(result.stdout)
        branches = {row["branch"]: row for row in data.get("branches", [])}
        if set(branches) != {"feat", "scratch"}:
            report(f"{label} expected local-only branches feat and scratch, got {sorted(branches)}.")
            return 1
        if branches["feat"].get("unpushed") != 2:
            report(f"{label} feat should have 2 unpushed commits: {branches['feat']}.")
            return 1
        if branches["scratch"].get("remote") is not None:
            report(f"{label} scratch should have no remote counterpart: {branches['scratch']}.")
            return 1
        worktrees = {Path(row["path"]).name: row for row in data.get("worktrees", [])}
        if worktrees.get("b", {}).get("dirty") != 1:
            report(f"{label} worktree b should have 1 uncommitted path: {worktrees}.")
            return 1
        if "a" not in worktrees:
            report(f"{label} worktree a, on local-only feat, should be listed: {worktrees}.")
            return 1
        if "repo" in worktrees:
            report(f"{label} the clean main checkout was listed as local-only.")
            return 1
        stash_rows = data.get("stashes", [])
        if len(stash_rows) != 1:
            report(f"{label} expected exactly one stash entry, got {stash_rows}.")
            return 1
        if "keep this" not in stash_rows[0].get("subject", ""):
            report(f"{label} the stash entry does not carry its subject: {stash_rows[0]}.")
            return 1
        if result.returncode != 1:
            report(f"{label} exit {result.returncode}, expected 1 while work is local-only.")
            return 1
        text = run_keel(trees["b"], "sync", "status", env=r.env)
        if "as of the last fetch" not in text.stdout or "never fetched" not in text.stdout:
            report(f"{label} the text output does not say counts are as of the last fetch and when: {text.stdout}")
            return 1
        for name in ("feat", "scratch", "untracked", "stash"):
            if name not in text.stdout:
                report(f"{label} the text output does not name {name}: {text.stdout}")
                return 1
        if "done" in [line.split()[0] for line in text.stdout.splitlines() if line.strip() and not line.startswith(" ")]:
            report(f"{label} the merged branch done was listed.")
            return 1
        if r.state() != before:
            report(f"{label} the command changed the repository, a ref, or the chat store.")
            return 1
    report("sync-status-lists-local-only scenario passed.")
    return 0


def validate_sync_status_read_only_exit_codes_scenario() -> int:
    """#526 D4: exit 0 when clean, 2 for an operational error, the same from `/`."""
    label = "sync-status-read-only-exit-codes:"
    with tempfile.TemporaryDirectory(prefix="keel-sync-exit-") as raw:
        base = Path(raw).resolve()
        r = _Repo(base)
        clean = run_keel(r.repo, "sync", "status", env=r.env)
        if clean.returncode != 0:
            report(f"{label} a clean repository should exit 0, got {clean.returncode}: {clean.stderr.strip()}")
            return 1
        if "nothing is only on this machine" not in clean.stdout.lower():
            report(f"{label} a clean repository should say nothing is only on this machine: {clean.stdout.strip()}")
            return 1
        outside = base / "outside"
        outside.mkdir()
        for name, args in (("outside a repository", ("--repo", str(outside))), ("an unknown argument", ("--bogus",))):
            failed = run_keel(outside if args[0] == "--repo" else r.repo, "sync", "status", *args, env=r.env)
            if failed.returncode != 2:
                report(f"{label} {name} should exit 2, got {failed.returncode}: {failed.stderr.strip()}")
                return 1
            if failed.stdout.strip():
                report(f"{label} {name} listed something: {failed.stdout.strip()}")
                return 1
        trees = _populate(r)
        before = r.state()
        here = run_keel(trees["a"], "sync", "status", "--json", env=r.env)
        rooted = run_keel(Path("/"), "sync", "status", "--json", "--repo", str(trees["a"]), env=r.env)
        for name, run in (("inside the worktree", here), ("from / with --repo", rooted)):
            if run.returncode != 1:
                report(f"{label} the run {name} exited {run.returncode}, expected 1: {run.stderr.strip()}")
                return 1
        if json.loads(here.stdout) != json.loads(rooted.stdout):
            report(f"{label} a run from / with --repo differs from a run inside the worktree.")
            return 1
        if r.state() != before:
            report(f"{label} the command changed the repository, a ref, FETCH_HEAD, or the chat store.")
            return 1
    report("sync-status-read-only-exit-codes scenario passed.")
    return 0


def _git_wrapper(base: Path) -> tuple[dict[str, str], Path]:
    """A `git` first on PATH that logs each invocation and runs the real one."""
    real = shutil.which("git")
    bindir, log = base / "wrapbin", base / "git.log"
    bindir.mkdir()
    script = bindir / "git"
    script.write_text(f'#!/bin/sh\nprintf "%s\\n" "$*" >> "{log}"\nexec "{real}" "$@"\n', encoding="utf-8")
    script.chmod(0o755)
    env = _git_env()
    env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', '')}"
    return env, log


def _logged(log: Path, word: str) -> list[str]:
    if not log.exists():
        return []
    return [line for line in log.read_text(encoding="utf-8").splitlines() if line.split(" ", 1)[0] == word]


def _verify_rows(result: subprocess.CompletedProcess[str]) -> dict[str, dict]:
    data = json.loads(result.stdout)
    return {row["branch"]: row for row in data.get("verify", {}).get("branches", [])}


def validate_sync_status_verify_classifies_scenario() -> int:
    """#526 D3: --verify reads the remote's real sha, once per remote."""
    label = "sync-status-verify-classifies:"
    with tempfile.TemporaryDirectory(prefix="keel-sync-verify-") as raw:
        base = Path(raw).resolve()
        r = _Repo(base)
        # feat: the remote moved to a commit this clone never fetched.
        r.git("checkout", "-qb", "feat")
        r.commit("f1")
        r.git("push", "-qu", "origin", "feat")
        other = base / "other"
        subprocess.run(["git", "clone", "-q", str(r.remote), str(other)], env=r.env, check=True)
        for key, value in (("user.email", "o@example.invalid"), ("user.name", "Other")):
            r.git("config", key, value, cwd=other)
        r.git("checkout", "-q", "feat", cwd=other)
        r.commit("from-other", cwd=other)
        r.git("push", "-q", "origin", "feat", cwd=other)
        # partial: three commits past the remote, the tracking ref advanced by hand.
        r.git("checkout", "-qb", "partial", "main")
        r.git("push", "-qu", "origin", "partial")
        for name in ("p1", "p2", "p3"):
            tip = r.commit(name)
        r.git("update-ref", "refs/remotes/origin/partial", tip)
        r.git("checkout", "-q", "main")
        env, log = _git_wrapper(base)
        offline = run_keel(r.repo, "sync", "status", "--json", env=env)
        if offline.returncode not in (0, 1):
            report(f"{label} plain `keel sync status` failed: {offline.stderr.strip()}")
            return 1
        listed = {row["branch"] for row in json.loads(offline.stdout).get("branches", [])}
        if listed & {"feat", "partial"}:
            report(f"{label} without --verify feat and partial should look pushed, got {sorted(listed)}.")
            return 1
        if _logged(log, "ls-remote"):
            report(f"{label} a run without --verify ran ls-remote.")
            return 1
        verified = run_keel(r.repo, "sync", "status", "--verify", "--json", env=env)
        if verified.returncode != 1 or not verified.stdout.strip().startswith("{"):
            report(f"{label} --verify should exit 1 and report feat as unknown-to-local: exit {verified.returncode}, "
                   f"{(verified.stderr or verified.stdout).strip()[:300]}")
            return 1
        rows = _verify_rows(verified)
        if rows.get("feat", {}).get("state") != "unknown-to-local":
            report(f"{label} feat should be unknown-to-local, got {rows.get('feat')}.")
            return 1
        if rows.get("partial", {}).get("state") != "remote-behind":
            report(f"{label} partial should be remote-behind, got {rows.get('partial')}.")
            return 1
        if rows.get("main", {}).get("state") != "same":
            report(f"{label} main should be same, got {rows.get('main')}.")
            return 1
        calls = _logged(log, "ls-remote")
        if len(calls) != 1:
            report(f"{label} expected exactly one ls-remote for three branches on one remote, got {calls}.")
            return 1
        text = run_keel(r.repo, "sync", "status", "--verify", env=env)
        if "unknown-to-local" not in text.stdout or "remote-behind" not in text.stdout:
            report(f"{label} the text output does not name the states: {text.stdout}")
            return 1
        # A remote that is not named origin.
        hub = base / "hub"
        subprocess.run(["git", "clone", "-q", "-o", "hub", str(r.remote), str(hub)], env=r.env, check=True)
        named = run_keel(hub, "sync", "status", "--verify", "--remote", "hub", "--json", env=r.env)
        if _verify_rows(named).get("main", {}).get("state") != "same":
            report(f"{label} --remote hub did not verify main: {named.stdout.strip()[:300]} {named.stderr.strip()}")
            return 1
    report("sync-status-verify-classifies scenario passed.")
    return 0


def validate_sync_status_verify_failure_scenario() -> int:
    """#526 D3: a lookup that fails is `cannot verify`, never `same`."""
    label = "sync-status-verify-failure:"
    with tempfile.TemporaryDirectory(prefix="keel-sync-verify-fail-") as raw:
        base = Path(raw).resolve()
        r = _Repo(base)
        r.git("remote", "set-url", "origin", str(base / "nowhere.git"))
        verified = run_keel(r.repo, "sync", "status", "--verify", "--json", env=r.env)
        if verified.returncode != 1:
            report(f"{label} --verify against an unreachable remote should exit 1, got {verified.returncode}: "
                   f"{verified.stderr.strip()}")
            return 1
        rows = _verify_rows(verified)
        main = rows.get("main", {})
        if main.get("state") != "cannot verify":
            report(f"{label} main should be `cannot verify`, got {main}.")
            return 1
        if not main.get("error"):
            report(f"{label} `cannot verify` should carry git's error, got {main}.")
            return 1
        if any(row.get("state") == "same" for row in rows.values()):
            report(f"{label} a branch was reported same after a failed lookup: {rows}.")
            return 1
        offline = run_keel(r.repo, "sync", "status", env=r.env)
        if offline.returncode != 0:
            report(f"{label} without --verify the run should complete from local refs, got {offline.returncode}: "
                   f"{offline.stderr.strip()}")
            return 1
    report("sync-status-verify-failure scenario passed.")
    return 0


def validate_sync_status_push_guidance_scenario() -> int:
    """#526 D5: each fix is printed with the authorization that covers it, and run by nobody."""
    label = "sync-status-push-guidance:"
    with tempfile.TemporaryDirectory(prefix="keel-sync-guidance-") as raw:
        base = Path(raw).resolve()
        r = _Repo(base)
        r.git("checkout", "-qb", "feat")
        r.commit("f1")
        r.git("push", "-qu", "origin", "feat")
        r.commit("f2")
        r.git("checkout", "-qb", "scratch", "main")
        r.commit("s1")
        r.git("checkout", "-q", "main")
        write_text(r.repo / "keel" / "config.yaml", "authorize:\n  - push:feat*\n")
        r.git("add", "keel/config.yaml")
        r.git("commit", "-qm", "declare push:feat*")
        r.git("push", "-q", "origin", "main")
        covered = run_keel(r.repo, "sync", "status", env=r.env)
        lines = covered.stdout.splitlines()
        feat = next((i for i, line in enumerate(lines) if line.startswith("branch feat")), None)
        if feat is None:
            report(f"{label} feat is not listed: {covered.stdout}")
            return 1
        block = "\n".join(lines[feat:feat + 3])
        if "git push origin feat" not in block:
            report(f"{label} feat's fix `git push origin feat` is not printed: {block}")
            return 1
        if "push:feat*" not in block:
            report(f"{label} feat's fix does not say `push:feat*` covers it: {block}")
            return 1
        scratch = next((i for i, line in enumerate(lines) if line.startswith("branch scratch")), None)
        block = "\n".join(lines[scratch:scratch + 3]) if scratch is not None else ""
        if "git push -u origin scratch" not in block:
            report(f"{label} scratch's fix `git push -u origin scratch` is not printed: {covered.stdout}")
            return 1
        if "push:scratch" not in block:
            report(f"{label} scratch's fix does not name `push` or `push:scratch` to declare: {block}")
            return 1
        remote_heads = r.git("ls-remote", "--heads", str(r.remote))
        if "refs/heads/scratch" in remote_heads:
            report(f"{label} scratch reached the remote; the report must run nothing.")
            return 1
    report("sync-status-push-guidance scenario passed.")
    return 0


def _declare(r: _Repo, text: str) -> None:
    write_text(r.repo / "keel" / "config.yaml", text)


def _doctor_lines(r: _Repo) -> list[str]:
    return run_keel(r.repo, "--doctor", env=r.env).stdout.splitlines()


def _context(r: _Repo) -> dict:
    return json.loads(run_keel(r.repo, "context", "--json", env=r.env).stdout)


def validate_device_sync_authorization_name_scenario() -> int:
    """#526 D10: `device-sync` is a bare authorization name; `sync` is still refused with its hint."""
    label = "device-sync-authorization-name:"
    with tempfile.TemporaryDirectory(prefix="keel-device-sync-") as raw:
        r = _Repo(Path(raw).resolve())
        _declare(r, "authorize:\n  - device-sync\n")
        warnings = " ".join(_context(r).get("warnings", []))
        if "unrecognized" in warnings:
            report(f"{label} `device-sync` was reported as unrecognized: {warnings}")
            return 1
        if "device-sync: authorized" not in _doctor_lines(r):
            report(f"{label} keel --doctor does not list `device-sync: authorized`.")
            return 1
        _declare(r, "authorize:\n  - sync\n")
        warnings = " ".join(_context(r).get("warnings", []))
        if "change-close --action" not in warnings:
            report(f"{label} `sync` lost its `change-close --action` hint: {warnings}")
            return 1
        if "device-sync" not in warnings:
            report(f"{label} the accepted names printed for `sync` do not include device-sync: {warnings}")
            return 1
        _declare(r, "authorize:\n  - issue\n")
        warnings = " ".join(_context(r).get("warnings", []))
        if "issue:<owner>/<repo>" not in warnings:
            report(f"{label} a bare `issue` is no longer refused with its form: {warnings}")
            return 1
    report("device-sync-authorization-name scenario passed.")
    return 0


def validate_sync_declaration_read_scenario() -> int:
    """#526 D11: `sync:` is read with `lock` and `ttl`; anything else is named and ignored."""
    label = "sync-declaration-read:"
    with tempfile.TemporaryDirectory(prefix="keel-sync-decl-") as raw:
        r = _Repo(Path(raw).resolve())
        _declare(r, "sync:\n  lock: true\n  ttl: 45m\n")
        declared = _context(r).get("sync")
        if declared != {"lock": True, "ttl": "45m", "ttlSeconds": 2700}:
            report(f"{label} context's `sync` should be the lock in force with a 45-minute lease, got {declared}.")
            return 1
        doctor = [line for line in _doctor_lines(r) if line.startswith("sync:")]
        if not doctor:
            report(f"{label} keel --doctor has no `sync` line.")
            return 1
        for word in ("lock: true", "45m"):
            if word not in doctor[0]:
                report(f"{label} keel --doctor's `sync` line does not name `{word}`: {doctor[0]}")
                return 1
        for text, named in (("sync:\n  lock: true\n  ttl: soon\n", "ttl: soon"),
                            ("sync:\n  lock: true\n  ttl: 3m\n", "ttl: 3m"),
                            ("sync:\n  lock: true\n  colour: blue\n", "colour"),
                            ("sync:\n  lock: maybe\n", "lock: maybe")):
            _declare(r, text)
            context = _context(r)
            warnings = " ".join(context.get("warnings", []))
            if named not in warnings:
                report(f"{label} keel context does not name `{named}`: {warnings}")
                return 1
            if context.get("sync") is not None:
                report(f"{label} an unreadable declaration `{named}` was still read as in force: {context.get('sync')}")
                return 1
            doctor = " ".join(line for line in _doctor_lines(r) if line.startswith("sync:"))
            if named not in doctor:
                report(f"{label} keel --doctor does not name `{named}`: {doctor}")
                return 1
        _declare(r, "")
        if _context(r).get("sync") is not None:
            report(f"{label} with no declaration context still reports a `sync` object.")
            return 1
    report("sync-declaration-read scenario passed.")
    return 0


def _expect(label: str, what: str, result: subprocess.CompletedProcess[str], code: int,
            needles: tuple[str, ...] = (), stream: str = "stderr") -> bool:
    """One message per way an expected outcome can fail; True when it held."""
    if result.returncode != code:
        report(f"{label} {what}: expected exit {code}, got {result.returncode}: {result.stderr.strip()[:300]}")
        return False
    text = getattr(result, stream)
    for needle in needles:
        if needle not in text:
            report(f"{label} {what}: the output does not name {needle!r}: {text.strip()[:300]}")
            return False
    return True


def _unmoved(label: str, what: str, d: "_Devices", before: str) -> bool:
    if d.lock_sha() != before:
        report(f"{label} {what}: the remote lock moved.")
        return False
    return True


# --- the branch lock (#526 D6-D10, D19, D22) ---------------------------------------------

_LOCK_CONFIG = "authorize:\n  - device-sync\n  - push:claude/*\nsync:\n  lock: true\n  ttl: 30m\n"


class _Devices:
    """A bare remote and two clones, each its own device with its own chat store."""

    def __init__(self, base: Path, config: str = _LOCK_CONFIG) -> None:
        self.base = base
        self.seed = _Repo(base)
        _declare(self.seed, config)
        self.seed.git("add", "keel/config.yaml")
        self.seed.git("commit", "-qm", "declare the lock")
        self.seed.git("push", "-q", "origin", "main")
        self.seed.git("checkout", "-qb", "feat")
        self.head = self.seed.commit("f1")
        self.seed.git("push", "-qu", "origin", "feat")
        self.remote = self.seed.remote
        self.a = self.clone("a", "pm")
        self.b = self.clone("b", "verify")

    def clone(self, name: str, role: str) -> Path:
        path = self.base / name
        subprocess.run(["git", "clone", "-q", str(self.remote), str(path)], env=_git_env(), check=True,
                       capture_output=True)
        for key, value in (("user.email", f"{name}@example.invalid"), ("user.name", name)):
            self.git(path, "config", key, value)
        self.git(path, "checkout", "-q", "feat")
        setattr(self, f"role_{name}", role)
        return path

    def env(self, path: Path) -> dict[str, str]:
        env = _git_env()
        env["KEEL_CHAT_ROLE"] = getattr(self, f"role_{path.name}")
        return env

    def git(self, path: Path, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=path, env=_git_env(), check=True,
                              capture_output=True, text=True).stdout.strip()

    def keel(self, path: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return run_keel(path, *args, env=env or self.env(path))

    def lock_sha(self) -> str:
        out = self.git(self.base / "a", "ls-remote", str(self.remote), "refs/keel/lock/feat")
        return out.split()[0] if out else ""

    def lock_message(self) -> str:
        sha = self.lock_sha()
        return subprocess.run(["git", "--git-dir", str(self.remote), "log", "-1", "--format=%B", sha],
                              env=_git_env(), check=True, capture_output=True, text=True).stdout if sha else ""

    def plant(self, message: str, parent: str | None = None) -> str:
        """Push a lock commit as some other device would have."""
        path = self.base / "a"
        if parent:
            self.git(path, "fetch", "-q", str(self.remote), "+refs/keel/lock/feat:refs/keel/lock/feat")
        empty = self.git(path, "hash-object", "-t", "tree", "/dev/null")
        args = ["commit-tree", empty, "-m", message] + (["-p", parent] if parent else [])
        sha = self.git(path, *args)
        self.git(path, "push", "-q", str(self.remote), f"{sha}:refs/keel/lock/feat")
        return sha


def _trailer(message: str, key: str) -> str | None:
    for line in message.splitlines():
        if line.startswith(f"{key}: "):
            return line[len(key) + 2:]
    return None


def validate_branch_lock_race_scenario() -> int:
    """#526 D6, D7: two devices race for a free branch; exactly one wins; the holder renews."""
    label = "branch-lock-race:"
    with tempfile.TemporaryDirectory(prefix="keel-branch-race-") as raw:
        d = _Devices(Path(raw).resolve())
        procs = [subprocess.Popen(["node", str(Path(__file__).resolve().parents[2] / "bin" / "keel.js"),
                                   "lock", "acquire", "--branch", "feat"], cwd=path, env=d.env(path),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                 for path in (d.a, d.b)]
        results = [(proc, *proc.communicate(timeout=120)) for proc in procs]
        codes = sorted(proc.returncode for proc, _, _ in results)
        if codes != [0, 1]:
            report(f"{label} `keel lock acquire --branch feat` from two devices should give one 0 and one 1, got "
                   f"{codes}: {[(out.strip()[:200], err.strip()[:200]) for _, out, err in results]}")
            return 1
        winner = d.a if results[0][0].returncode == 0 else d.b
        loser = d.b if winner == d.a else d.a
        loser_err = results[1][2] if winner == d.a else results[0][2]
        message = d.lock_message()
        if _trailer(message, "keel-lock") != "held" or _trailer(message, "Seq") != "1":
            report(f"{label} the remote lock should be one held commit with Seq 1: {message}")
            return 1
        holder = _trailer(message, "Holder") or ""
        if not holder.startswith(d.env(winner)["KEEL_CHAT_ROLE"] + "@"):
            report(f"{label} Holder should be the winner's role at its device, got {holder!r}.")
            return 1
        if "taken" not in loser_err:
            report(f"{label} the loser should say the lock was taken: {loser_err.strip()}")
            return 1
        renew = d.keel(winner, "lock", "acquire", "--branch", "feat")
        if renew.returncode != 0 or _trailer(d.lock_message(), "Seq") != "2":
            report(f"{label} the holder should renew to Seq 2: exit {renew.returncode}, {renew.stderr.strip()}, "
                   f"{d.lock_message()}")
            return 1
        before = d.lock_sha()
        refused = d.keel(loser, "lock", "acquire", "--branch", "feat")
        if refused.returncode != 1:
            report(f"{label} a second device should be refused with exit 1, got {refused.returncode}.")
            return 1
        for word in (holder, "expires", "head"):
            if word not in refused.stderr:
                report(f"{label} the refusal does not name {word!r}: {refused.stderr.strip()}")
                return 1
        if d.lock_sha() != before:
            report(f"{label} a refused acquisition moved the remote lock.")
            return 1
        listed = d.keel(loser, "lock", "list", "--json")
        rows = json.loads(listed.stdout).get("branchLocks", []) if listed.stdout.strip().startswith("{") else []
        feat = next((row for row in rows if row.get("branch") == "feat"), None)
        if not feat:
            report(f"{label} `keel lock list` on the loser does not list feat's lock: {listed.stdout.strip()[:400]}")
            return 1
        if d.env(loser)["KEEL_CHAT_ROLE"] not in json.dumps(feat.get("waiters", [])):
            report(f"{label} `keel lock list` on the loser does not list it as a waiter on feat: {feat}")
            return 1
        local = d.keel(winner, "lock", "acquire", "scratch-dir", "--for", "1h", "--note", "local lease")
        if not _expect(label, "a local lease without --branch", local, 0, ("enforces nothing",), "stdout"):
            return 1
    report("branch-lock-race scenario passed.")
    return 0


def validate_branch_lock_head_and_expiry_scenario() -> int:
    """#526 D7, D8, D19: start where the last holder finished; take an expired lock; break only with a reason."""
    label = "branch-lock-head-and-expiry:"
    with tempfile.TemporaryDirectory(prefix="keel-branch-expiry-") as raw:
        base = Path(raw).resolve()
        d = _Devices(base)
        wrap_env, log = _git_wrapper(base)
        # A released lock whose head the b clone does not have yet.
        d.git(d.a, "commit", "-q", "--allow-empty", "-m", "c2")
        d.git(d.a, "commit", "-q", "--allow-empty", "-m", "c3")
        d.git(d.a, "push", "-q", "origin", "feat")
        c3 = d.git(d.a, "rev-parse", "HEAD")
        released = d.plant(f"keel-lock: released\n\nHolder: pm@elsewhere-00000000\nDevice: elsewhere-00000000\n"
                           f"Seq: 4\nExpires: 2000-01-01T00:00:00.000Z\nHead: {c3}\n")
        behind = d.keel(d.b, "lock", "acquire", "--branch", "feat", env={**wrap_env, "KEEL_CHAT_ROLE": "verify"})
        if not _expect(label, "a device behind the released head", behind, 1, (c3[:8],)):
            return 1
        if d.lock_sha() != released:
            report(f"{label} the refused acquisition moved the lock.")
            return 1
        d.git(d.b, "pull", "-q", "--ff-only")
        caught_up = d.keel(d.b, "lock", "acquire", "--branch", "feat", env={**wrap_env, "KEEL_CHAT_ROLE": "verify"})
        message = d.lock_message()
        if caught_up.returncode != 0 or _trailer(message, "Seq") != "5" or _trailer(message, "keel-lock") != "held":
            report(f"{label} after fast-forwarding, b should hold the lock with Seq 5: {caught_up.stderr.strip()} {message}")
            return 1
        # An expired holder elsewhere: taken over with a warning showing the gap.
        stale = d.plant(f"keel-lock: held\n\nHolder: pm@gone-11111111\nDevice: gone-11111111\nSeq: 9\n"
                        f"Expires: 2000-01-01T00:00:00.000Z\nHead: {d.head}\n", parent=d.lock_sha())
        took = d.keel(d.b, "lock", "acquire", "--branch", "feat", env={**wrap_env, "KEEL_CHAT_ROLE": "verify"})
        message = d.lock_message()
        if took.returncode != 0 or _trailer(message, "Took-over") != "pm@gone-11111111":
            report(f"{label} an expired lock should be taken with Took-over: {took.stderr.strip()} {message}")
            return 1
        output = took.stdout + took.stderr
        if d.head[:8] not in output or c3[:8] not in output:
            report(f"{label} the take-over should show the last head and the remote's sha: {output.strip()}")
            return 1
        chat = Path(d.git(d.b, "rev-parse", "--path-format=absolute", "--git-common-dir")) / "keel-chat" / "groups"
        records = "".join(f.read_text(encoding="utf-8") for f in chat.rglob("*") if f.is_file()) if chat.exists() else ""
        if "feat" not in records or "pm" not in records:
            report(f"{label} the previous holder's role has no chat record of the take-over.")
            return 1
        # A live lock held elsewhere: only --break with a reason takes it.
        live = d.plant(f"keel-lock: held\n\nHolder: pm@live-22222222\nDevice: live-22222222\nSeq: 20\n"
                       f"Expires: 2999-01-01T00:00:00.000Z\nHead: {c3}\n", parent=d.lock_sha())
        bare = d.keel(d.b, "lock", "acquire", "--branch", "feat", "--break")
        if bare.returncode != 2 or d.lock_sha() != live:
            report(f"{label} --break with no reason should exit 2 and move nothing, got {bare.returncode}.")
            return 1
        broke = d.keel(d.b, "lock", "acquire", "--branch", "feat", "--break", "A's machine is gone",
                       env={**wrap_env, "KEEL_CHAT_ROLE": "verify"})
        message = d.lock_message()
        if broke.returncode != 0 or _trailer(message, "Broke") != "pm@live-22222222 — A's machine is gone":
            report(f"{label} --break with a reason should take the live lock with Broke: {broke.stderr.strip()} {message}")
            return 1
        parent = subprocess.run(["git", "--git-dir", str(d.remote), "rev-parse", f"{d.lock_sha()}^"],
                                env=_git_env(), capture_output=True, text=True).stdout.strip()
        if parent != live:
            report(f"{label} the break did not fast-forward the lock from the live commit.")
            return 1
        forced = [line for line in _logged(log, "push") if "--force" in line or " -f" in line or "+" in line.split()[-1]]
        if forced:
            report(f"{label} a lock push used force: {forced}")
            return 1
    report("branch-lock-head-and-expiry scenario passed.")
    return 0


def validate_branch_lock_release_scenario() -> int:
    """#526 D9: release confirms the push, messages the waiter, and refuses otherwise."""
    label = "branch-lock-release:"
    with tempfile.TemporaryDirectory(prefix="keel-branch-release-") as raw:
        d = _Devices(Path(raw).resolve())
        # Two worktrees of clone a on one chat store, as two devices, so the waiter can be messaged.
        other = d.base / "a-other"
        d.git(d.a, "worktree", "add", "-q", "--detach", str(other))
        a_env = {**d.env(d.a), "KEEL_DEVICE": "laptop-aaaaaaaa"}
        w_env = {**_git_env(), "KEEL_CHAT_ROLE": "verify", "KEEL_DEVICE": "desk-bbbbbbbb"}
        held = d.keel(d.a, "lock", "acquire", "--branch", "feat", env=a_env)
        if held.returncode != 0:
            report(f"{label} a could not acquire feat: {held.stderr.strip()}")
            return 1
        d.git(other, "checkout", "-q", "--detach", "origin/feat")
        waiter = run_keel(other, "lock", "acquire", "--branch", "feat", env=w_env)
        if waiter.returncode != 1:
            report(f"{label} the second device should be refused and wait, got {waiter.returncode}: {waiter.stderr}")
            return 1
        before = d.lock_sha()
        d.git(d.a, "commit", "-q", "--allow-empty", "-m", "unpushed")
        unpushed = d.keel(d.a, "lock", "release", "--branch", "feat", env=a_env)
        what = "release over an unpushed commit"
        if not _expect(label, what, unpushed, 1, ("git push origin feat",)) or not _unmoved(label, what, d, before):
            return 1
        d.git(d.a, "push", "-q", "origin", "feat")
        (d.a / "loose.txt").write_text("x\n", encoding="utf-8")
        dirty = d.keel(d.a, "lock", "release", "--branch", "feat", env=a_env)
        what = "release over an untracked file"
        if not _expect(label, what, dirty, 1, ("loose.txt",)) or not _unmoved(label, what, d, before):
            return 1
        (d.a / "loose.txt").unlink()
        theirs = run_keel(other, "lock", "release", "--branch", "feat", env=w_env)
        what = "releasing another device's lock"
        if not _expect(label, what, theirs, 1, ("pm@laptop-aaaaaaaa",)) or not _unmoved(label, what, d, before):
            return 1
        done = d.keel(d.a, "lock", "release", "--branch", "feat", env=a_env)
        message = d.lock_message()
        tip = d.git(d.a, "rev-parse", "HEAD")
        if done.returncode != 0 or _trailer(message, "keel-lock") != "released" or _trailer(message, "Head") != tip:
            report(f"{label} release after the push should publish released with Head {tip[:8]}: "
                   f"{done.returncode} {done.stderr.strip()} {message}")
            return 1
        chat = Path(d.git(d.a, "rev-parse", "--path-format=absolute", "--git-common-dir")) / "keel-chat" / "groups"
        records = "".join(f.read_text(encoding="utf-8") for f in chat.rglob("*") if f.is_file()) if chat.exists() else ""
        if "released" not in records or "verify" not in json.dumps(sorted(str(p) for p in chat.rglob("*"))):
            report(f"{label} the waiter verify has no message that feat was released.")
            return 1
    report("branch-lock-release scenario passed.")
    return 0


def validate_branch_lock_push_authorization_scenario() -> int:
    """#526 D10: lock refs only under device-sync; work branches only under push."""
    label = "branch-lock-push-authorization:"
    with tempfile.TemporaryDirectory(prefix="keel-branch-auth-") as raw:
        base = Path(raw).resolve()
        d = _Devices(base, config="authorize:\n  - push:claude/*\nsync:\n  lock: true\n")
        for action in ("acquire", "release"):
            refused = d.keel(d.a, "lock", action, "--branch", "feat")
            if not _expect(label, f"`lock {action} --branch` without device-sync", refused, 3, ("device-sync",)):
                return 1
        if d.lock_sha():
            report(f"{label} a lock ref reached the remote without device-sync.")
            return 1
        _declare_in(d, d.a, "authorize:\n  - device-sync\n  - push:claude/*\n  - push-protected:release/*\nsync:\n  lock: true\n")
        d.git(d.a, "commit", "-q", "--allow-empty", "-m", "unpushed on feat")
        remote_feat = d.git(d.a, "ls-remote", str(d.remote), "refs/heads/feat").split()[0]
        renewed = d.keel(d.a, "lock", "acquire", "--branch", "feat", "--push")
        if renewed.returncode != 0 or _trailer(d.lock_message(), "keel-lock") != "held":
            report(f"{label} with device-sync the lock should be taken: {renewed.returncode} {renewed.stderr.strip()}")
            return 1
        if d.git(d.a, "ls-remote", str(d.remote), "refs/heads/feat").split()[0] != remote_feat:
            report(f"{label} feat was pushed although only push:claude/* is declared.")
            return 1
        if "push:claude/*" not in renewed.stdout + renewed.stderr:
            report(f"{label} the skipped push does not name push:claude/*: {renewed.stdout} {renewed.stderr}")
            return 1
        # A protected branch is skipped, a failing pre-push hook reported.
        d.git(d.a, "checkout", "-qb", "release/1")
        d.git(d.a, "push", "-qu", "origin", "release/1")
        d.git(d.a, "commit", "-q", "--allow-empty", "-m", "protected")
        protected = d.keel(d.a, "lock", "acquire", "--branch", "release/1", "--push")
        if "push-protected" not in protected.stdout + protected.stderr:
            report(f"{label} a push-protected branch was not reported as skipped: {protected.stdout} {protected.stderr}")
            return 1
        d.git(d.a, "checkout", "-qb", "claude/x")
        d.git(d.a, "push", "-qu", "origin", "claude/x")
        d.git(d.a, "commit", "-q", "--allow-empty", "-m", "hooked")
        hook = d.a / ".git" / "hooks" / "pre-push"
        hook.write_text("#!/bin/sh\necho fast_check failed >&2\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        hooked = d.keel(d.a, "lock", "acquire", "--branch", "claude/x", "--push")
        if (hooked.stdout + hooked.stderr).count("fast_check failed") != 1:
            report(f"{label} a failing pre-push hook should be reported once: {hooked.stdout} {hooked.stderr}")
            return 1
        listed = d.keel(d.a, "lock", "list")
        status = d.keel(d.a, "sync", "status")
        for name, out in (("keel lock list", listed.stdout), ("keel sync status", status.stdout)):
            if "feat" not in out or "pm@" not in out:
                report(f"{label} {name} does not show feat's lock and holder: {out}")
                return 1
    report("branch-lock-push-authorization scenario passed.")
    return 0


def _declare_in(d: _Devices, path: Path, text: str) -> None:
    write_text(path / "keel" / "config.yaml", text)
    d.git(path, "add", "keel/config.yaml")
    d.git(path, "commit", "-qm", "declare")
    d.git(path, "push", "-q", "origin", "HEAD")


def validate_archive_carries_shift_notes_scenario() -> int:
    """#526 D9: the chat archive carries hand-over notes written once under shift-notes/."""
    label = "archive-carries-shift-notes:"
    with tempfile.TemporaryDirectory(prefix="keel-archive-notes-") as raw:
        base = Path(raw).resolve()
        r = _Repo(base)
        gh = base / "gh"
        write_text(gh, "#!/bin/sh\necho PUBLIC\n")
        gh.chmod(0o755)
        env = {**r.env, "KEEL_CHAT_ROLE": "pm", "KEEL_CHAT_GH": str(gh)}
        bound = run_keel(r.repo, "chat", "role", "--set", "pm", env=env)
        if bound.returncode != 0:
            report(f"{label} could not bind pm: {bound.stderr.strip()}")
            return 1
        chat = r.chat()
        note = chat / "shift-notes" / "pm" / "20261116T080000Z-mac-1a2b3c4d.md"
        write_text(note, "next: rerun R007 on 1b64e8c\n")
        write_text(chat / "shift" / "pm.md", "the rewritten-in-place note\n")

        def tree(ref: str, cwd: Path) -> list[str]:
            return r.git("ls-tree", "-r", "--name-only", ref, cwd=cwd).split()

        public = run_keel(r.repo, "chat", "archive", "sync", env=env)
        if public.returncode != 0:
            report(f"{label} archive sync failed: {public.stderr.strip()}")
            return 1
        files = tree("refs/heads/keel-chat", r.repo)
        if "shift-notes/pm/20261116T080000Z-mac-1a2b3c4d.md" not in files:
            report(f"{label} the local keel-chat commit does not carry the shift-notes file: {files}")
            return 1
        if any(name.startswith("shift/") for name in files):
            report(f"{label} a rewritten-in-place shift/ file was archived: {files}")
            return 1
        if r.git("ls-remote", str(r.remote), "refs/heads/keel-chat"):
            report(f"{label} a public repository with no archive_public pushed the archive.")
            return 1
        write_text(r.repo / "keel" / "chat.json", json.dumps({"archive": {"remote": "origin"}}) + "\n")
        pushed = run_keel(r.repo, "chat", "archive", "sync", env=env)
        if pushed.returncode != 0 or not r.git("ls-remote", str(r.remote), "refs/heads/keel-chat"):
            report(f"{label} with archive.remote the archive should be pushed: {pushed.stdout} {pushed.stderr}")
            return 1
        second = base / "second"
        subprocess.run(["git", "clone", "-q", str(r.remote), str(second)], env=r.env, check=True, capture_output=True)
        write_text(second / "keel" / "chat.json", json.dumps({"archive": {"remote": "origin"}}) + "\n")
        pulled = run_keel(second, "chat", "archive", "pull", env={**env, "KEEL_CHAT_ROLE": "verify"})
        if pulled.returncode != 0:
            report(f"{label} archive pull on a second clone failed: {pulled.stderr.strip()}")
            return 1
        copy = Path(r.git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=second)) / "keel-chat" / \
            "shift-notes" / "pm" / "20261116T080000Z-mac-1a2b3c4d.md"
        if not copy.exists():
            report(f"{label} the second clone did not import the shift-notes file.")
            return 1
        if copy.read_bytes() != note.read_bytes():
            report(f"{label} the imported note differs from the original.")
            return 1
    report("archive-carries-shift-notes scenario passed.")
    return 0


# --- the gates at the sync points (#526 D12) ---------------------------------------------

def _gate_repo(base: Path, config: str) -> _Repo:
    from validation.common import task_capsule_compact_fixture
    r = _Repo(base)
    change = r.repo / "openspec" / "changes" / "demo"
    write_text(change / "tasks.md", task_capsule_compact_fixture())
    write_text(change / "proposal.md", "# Proposal\n")
    write_text(change / "design.md", "## Context\n\nfixture\n")
    write_text(change / "specs" / "demo" / "spec.md", "## ADDED Requirements\n")
    _declare(r, config)
    r.git("add", "-A")
    r.git("commit", "-qm", "fixture")
    r.git("push", "-q", "origin", "main")
    r.git("checkout", "-qb", "feat")
    r.git("push", "-qu", "origin", "feat")
    return r


def _gate(r: _Repo, env: dict[str, str], stage: str) -> dict:
    args = ["gate", stage, "--change", "demo", "--json"]
    args += ["--task", "1.1", "--no-guard"] if stage == "task-start" else ["--action", "archive"]
    result = run_keel(r.repo, *args, env=env)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "error", "problems": [{"code": "unparsed", "message": result.stdout + result.stderr}]}


def _sync_problems(payload: dict) -> list[dict]:
    return [p for p in payload.get("problems", []) if str(p.get("code", "")).startswith("sync-")]


def _has(label: str, what: str, payload: dict, code: str, *needles: str) -> bool:
    found = [p for p in _sync_problems(payload) if p.get("code") == code]
    if not found:
        report(f"{label} {what}: expected a {code} problem, got {payload.get('status')} {_sync_problems(payload)}")
        return False
    for needle in needles:
        if needle not in found[0].get("message", ""):
            report(f"{label} {what}: the {code} problem does not name {needle!r}: {found[0].get('message')}")
            return False
    return True


def validate_sync_gates_lock_scenario() -> int:
    """#526 D12: with the lock declared, task-start and change-close check the lock and the pushed state."""
    label = "sync-gates-lock:"
    with tempfile.TemporaryDirectory(prefix="keel-sync-gates-") as raw:
        base = Path(raw).resolve()
        r = _gate_repo(base, "authorize:\n  - device-sync\nsync:\n  lock: true\n")
        wrap, log = _git_wrapper(base)
        a = {**wrap, "KEEL_CHAT_ROLE": "pm", "KEEL_DEVICE": "dev-a"}
        b = {**wrap, "KEEL_CHAT_ROLE": "verify", "KEEL_DEVICE": "dev-b"}
        if not _has(label, "no lock", _gate(r, a, "task-start"), "sync-no-lock", "keel lock acquire --branch feat"):
            return 1
        if run_keel(r.repo, "lock", "acquire", "--branch", "feat", env=a).returncode != 0:
            report(f"{label} could not acquire feat.")
            return 1
        lock_before = r.git("ls-remote", str(r.remote), "refs/keel/lock/feat")
        log.write_text("", encoding="utf-8")
        passed = _gate(r, a, "task-start")
        if r.git("ls-remote", str(r.remote), "refs/keel/lock/feat") != lock_before:
            report(f"{label} task-start moved the remote lock.")
            return 1
        if passed.get("status") != "pass":
            report(f"{label} a device holding a live lock with the branch pushed should pass task-start: {passed.get('problems')}")
            return 1
        if len(_logged(log, "ls-remote")) != 1:
            report(f"{label} task-start should make exactly one ls-remote, logged {_logged(log, 'ls-remote')}.")
            return 1
        if _logged(log, "push") or _logged(log, "fetch"):
            report(f"{label} a gate pushed or fetched: {_logged(log, 'push') + _logged(log, 'fetch')}")
            return 1
        # Unpushed commit.
        r.commit("u1")
        if not _has(label, "an unpushed commit", _gate(r, a, "task-start"), "sync-unpushed", "git push origin feat"):
            return 1
        r.git("push", "-q", "origin", "feat")
        # A stale tracking ref: the remote moved to a commit this clone lacks.
        other = base / "other"
        subprocess.run(["git", "clone", "-q", "-b", "feat", str(r.remote), str(other)], env=r.env, check=True, capture_output=True)
        r.git("config", "user.email", "o@example.invalid", cwd=other)
        r.git("config", "user.name", "Other", cwd=other)
        r.commit("o1", cwd=other)
        r.git("push", "-q", "origin", "feat", cwd=other)
        head = r.git("rev-parse", "HEAD")
        remote_tip = r.git("rev-parse", "HEAD", cwd=other)
        if not _has(label, "a remote this clone lacks", _gate(r, a, "task-start"), "sync-remote-unknown",
                    "git fetch", head[:8], remote_tip[:8]):
            return 1
        r.git("pull", "-q", "--ff-only")
        # Another device breaks the lock: the lock moved.
        if run_keel(r.repo, "lock", "acquire", "--branch", "feat", "--break", "test", env=b).returncode != 0:
            report(f"{label} dev-b could not break the lock.")
            return 1
        if not _has(label, "another device holds it", _gate(r, a, "task-start"), "sync-lock-not-held", "verify@dev-b"):
            return 1
        # An expired own lease.
        if run_keel(r.repo, "lock", "acquire", "--branch", "feat", "--break", "back", "--for", "1s", env=a).returncode != 0:
            report(f"{label} dev-a could not take the lock back.")
            return 1
        time.sleep(2)
        if not _has(label, "an expired lease", _gate(r, a, "task-start"), "sync-lease-expired", "keel lock acquire --branch feat"):
            return 1
        if run_keel(r.repo, "lock", "acquire", "--branch", "feat", env=a).returncode != 0:
            report(f"{label} dev-a could not renew.")
            return 1
        # change-close: an uncommitted path fails; clean and at the remote passes the check.
        (r.repo / "loose.txt").write_text("x\n", encoding="utf-8")
        if not _has(label, "change-close over an uncommitted path", _gate(r, a, "change-close"), "sync-uncommitted", "loose.txt"):
            return 1
        (r.repo / "loose.txt").unlink()
        closing = _gate(r, a, "change-close")
        if _sync_problems(closing):
            report(f"{label} change-close on a clean pushed branch with the lock held should raise no sync problem: "
                   f"{_sync_problems(closing)}")
            return 1
        # task-complete reads nothing remote.
        log.write_text("", encoding="utf-8")
        run_keel(r.repo, "gate", "task-complete", "--change", "demo", "--task", "1.1", "--json", env=a)
        if _logged(log, "ls-remote"):
            report(f"{label} task-complete ran ls-remote.")
            return 1
        # Unreachable remote.
        r.git("remote", "set-url", "origin", str(base / "nowhere.git"))
        if not _has(label, "an unreachable remote", _gate(r, a, "task-start"), "sync-cannot-verify"):
            return 1
        if not _has(label, "an unreachable remote at close", _gate(r, a, "change-close"), "sync-cannot-verify"):
            return 1
    report("sync-gates-lock scenario passed.")
    return 0


def validate_sync_gates_without_declaration_scenario() -> int:
    """#526 D7, D11: with no `sync:` the gates neither touch the network nor change their verdict."""
    label = "sync-gates-without-declaration:"
    with tempfile.TemporaryDirectory(prefix="keel-sync-gates-off-") as raw:
        base = Path(raw).resolve()
        r = _gate_repo(base, "authorize:\n  - commit\n")
        r.commit("unpushed")
        r.git("remote", "set-url", "origin", str(base / "nowhere.git"))
        wrap, log = _git_wrapper(base)
        started = _gate(r, wrap, "task-start")
        if started.get("status") != "pass":
            report(f"{label} task-start should pass as before: {started.get('problems')}")
            return 1
        closing = _gate(r, wrap, "change-close")
        if _sync_problems(started) or _sync_problems(closing):
            report(f"{label} a gate raised a sync problem with no declaration: {_sync_problems(started) + _sync_problems(closing)}")
            return 1
        if _logged(log, "ls-remote"):
            report(f"{label} a gate ran ls-remote with no declaration: {_logged(log, 'ls-remote')}")
            return 1
    report("sync-gates-without-declaration scenario passed.")
    return 0


# --- keel context (#526 D15) ------------------------------------------------------------

def validate_context_warns_local_only_scenario() -> int:
    """#526 D15: one offline warning counts what is only on this machine; selection is unchanged."""
    label = "context-warns-local-only:"
    with tempfile.TemporaryDirectory(prefix="keel-context-local-") as raw:
        base = Path(raw).resolve()
        r = _gate_repo(base, "authorize:\n  - commit\n")
        r.git("checkout", "-q", "main")
        clean = _context(r)
        if any("keel sync status" in w for w in clean.get("warnings", [])):
            report(f"{label} a clean repository carries a sync warning: {clean.get('warnings')}")
            return 1
        r.git("branch", "scratch", "main")
        r.git("checkout", "-q", "scratch")
        r.commit("s1")
        r.git("checkout", "-q", "main")
        (r.repo / "seed").write_text("changed\n", encoding="utf-8")
        r.git("stash", "push", "-q")
        wrap, log = _git_wrapper(base)
        found = json.loads(run_keel(r.repo, "context", "--json", env=wrap).stdout)
        warning = [w for w in found.get("warnings", []) if "keel sync status" in w]
        if len(warning) != 1:
            report(f"{label} expected one warning naming `keel sync status`, got {found.get('warnings')}")
            return 1
        for needle in ("1 local-only branch", "1 stash"):
            if needle not in warning[0]:
                report(f"{label} the warning does not count {needle!r}: {warning[0]}")
                return 1
        for key in ("status", "nextAction", "selection"):
            if found.get(key) != clean.get(key):
                report(f"{label} the warning changed {key}: {clean.get(key)} -> {found.get(key)}")
                return 1
        if _logged(log, "ls-remote") or _logged(log, "fetch"):
            report(f"{label} keel context touched the network.")
            return 1
        r.git("remote", "remove", "origin")
        none = _context(r)
        if any("keel sync status" in w for w in none.get("warnings", [])):
            report(f"{label} a repository with no remote carries a sync warning: {none.get('warnings')}")
            return 1
    report("context-warns-local-only scenario passed.")
    return 0


def validate_context_lock_next_action_scenario() -> int:
    """#526 D15: under the lock, context sends the session to acquire or resume before a task."""
    from validation.common import ROOT, PLUGIN_ROOT, run_session_start_hook, session_start_context
    label = "context-lock-next-action:"
    with tempfile.TemporaryDirectory(prefix="keel-context-lock-") as raw:
        base = Path(raw).resolve()
        r = _gate_repo(base, "authorize:\n  - device-sync\nsync:\n  lock: true\n")
        pm_a = {**r.env, "KEEL_CHAT_ROLE": "pm", "KEEL_DEVICE": "dev-a"}
        pm_b = {**r.env, "KEEL_CHAT_ROLE": "pm", "KEEL_DEVICE": "dev-b"}
        verify_b = {**r.env, "KEEL_CHAT_ROLE": "verify", "KEEL_DEVICE": "dev-b"}

        def ctx(env: dict[str, str]) -> dict:
            return json.loads(run_keel(r.repo, "context", "--json", env=env).stdout)

        if run_keel(r.repo, "lock", "acquire", "--branch", "feat", env=verify_b).returncode != 0:
            report(f"{label} verify@dev-b could not acquire feat.")
            return 1
        held = ctx(pm_a)
        action = held.get("nextAction", {})
        if action.get("kind") != "lock-acquire" or action.get("command") != "keel lock acquire --branch feat":
            report(f"{label} with feat held live by another device, nextAction should be lock-acquire "
                   f"`keel lock acquire --branch feat`, got {action}")
            return 1
        if "verify@dev-b" not in " ".join(held.get("reasons", [])):
            report(f"{label} the reasons do not name the holder: {held.get('reasons')}")
            return 1
        if held.get("status") != "ready":
            report(f"{label} status should stay ready, got {held.get('status')}")
            return 1
        if (held.get("selection") or {}).get("task") != "1.1":
            report(f"{label} the selection changed: {held.get('selection')}")
            return 1
        hook = run_session_start_hook(r.repo, {"hook_event_name": "SessionStart", "source": "startup"},
                                      keel_cli=f'node "{ROOT / "bin" / "keel.js"}"', extra_env=pm_a)
        projected = session_start_context(hook) or ""
        if "keel lock acquire --branch feat" not in projected:
            report(f"{label} the SessionStart projection does not show `keel lock acquire --branch feat`: {projected[:400]}")
            return 1
        # pm on dev-b takes it and releases it; pm on dev-a is sent to resume.
        if run_keel(r.repo, "lock", "acquire", "--branch", "feat", "--break", "test", env=pm_b).returncode != 0:
            report(f"{label} pm@dev-b could not take feat.")
            return 1
        released = run_keel(r.repo, "lock", "release", "--branch", "feat", env=pm_b)
        if released.returncode != 0:
            report(f"{label} pm@dev-b could not release feat: {released.stderr.strip()}")
            return 1
        resume = ctx(pm_a).get("nextAction", {})
        if resume.get("kind") != "shift-resume" or resume.get("command") != "keel shift resume":
            report(f"{label} a lock released by this role should send the session to `keel shift resume`, got {resume}")
            return 1
        if run_keel(r.repo, "lock", "acquire", "--branch", "feat", env=pm_a).returncode != 0:
            report(f"{label} pm@dev-a could not acquire feat.")
            return 1
        mine = ctx(pm_a).get("nextAction", {})
        if mine.get("kind") != "task-start":
            report(f"{label} with this device holding a live lock, nextAction should be task-start, got {mine}")
            return 1
    report("context-lock-next-action scenario passed.")
    return 0


# --- keel shift (#526 D9, D14, D16, D17) ----------------------------------------------

def _shift_json(path: Path, env: dict[str, str], *args: str) -> tuple[int, dict]:
    result = run_keel(path, "shift", *args, "--json", env=env)
    try:
        return result.returncode, json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.returncode, {"raw": result.stdout + result.stderr}


def validate_shift_check_stash_and_notes_scenario() -> int:
    """#526 D16: a stash of this branch holds the shift; other local-only work is a note."""
    label = "shift-check-stash-and-notes:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-stash-") as raw:
        base = Path(raw).resolve()
        r = _Repo(base)
        env = {**r.env, "KEEL_CHAT_ROLE": "pm", "KEEL_DEVICE": "dev-a"}
        r.git("checkout", "-qb", "feat")
        r.git("push", "-qu", "origin", "feat")
        r.git("checkout", "-qb", "other")
        (r.repo / "seed").write_text("other change\n", encoding="utf-8")
        r.git("stash", "push", "-q")
        r.git("checkout", "-q", "feat")
        loose = r.git("commit-tree", r.git("hash-object", "-t", "tree", "/dev/null"), "-m", "detached")
        r.git("stash", "store", "-m", "custom message", loose)
        (r.repo / "seed").write_text("feat change\n", encoding="utf-8")
        r.git("stash", "push", "-q")
        r.git("branch", "scratch", "main")
        r.git("checkout", "-q", "scratch")
        r.commit("s1")
        r.git("checkout", "-q", "feat")
        code, data = _shift_json(r.repo, env, "check")
        items = data.get("items", [])
        stash_items = [i for i in items if i.get("kind") == "stash"]
        for failed, why in ((code != 1, f"the check should exit 1, got {code}"),
                            (len(stash_items) != 1, f"expected exactly one stash item, got {items}"),
                            (bool(stash_items) and "feat" not in stash_items[0].get("detail", ""), f"the stash item does not name feat: {stash_items}")):
            if failed:
                report(f"{label} {why}")
                return 1
        notes = " ".join(data.get("notes", []))
        for needle in ("scratch", "on other", "custom message", "keel sync status"):
            if needle not in notes:
                report(f"{label} the notes do not name {needle!r}: {data.get('notes')}")
                return 1
        ref = next((s.split(":")[0] for s in r.git("stash", "list").splitlines() if "on feat" in s), None)
        r.git("stash", "drop", "-q", ref)
        code, data = _shift_json(r.repo, env, "check")
        if code != 0:
            report(f"{label} with the feat stash dropped the check should exit 0: {data.get('items')}")
            return 1
        _declare(r, "authorize:\n  - device-sync\nsync:\n  lock: true\n")
        r.git("add", "keel/config.yaml")
        r.git("commit", "-qm", "lock")
        r.git("push", "-q", "origin", "feat")
        if run_keel(r.repo, "lock", "acquire", "--branch", "feat", env=env).returncode != 0:
            report(f"{label} could not acquire feat.")
            return 1
        code, data = _shift_json(r.repo, env, "check")
        if not any("keel shift ready" in n and "releases" in n for n in data.get("notes", [])):
            report(f"{label} a held lock should be a note that `keel shift ready` releases it: {data.get('notes')}")
            return 1
    report("shift-check-stash-and-notes scenario passed.")
    return 0


def _archived_devices(base: Path) -> _Devices:
    d = _Devices(base, config=_LOCK_CONFIG)
    for path in (d.a, d.b):
        write_text(path / "keel" / "chat.json", json.dumps({"archive": {"remote": "origin"}}) + "\n")
        info = path / ".git" / "info" / "exclude"
        info.write_text(info.read_text(encoding="utf-8") + "keel/chat.json\n", encoding="utf-8")
    return d


def _note_body(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def validate_shift_ready_releases_lock_scenario() -> int:
    """#526 D9, D16: ready releases the lock with the archived note and lists what stays local."""
    label = "shift-ready-releases-lock:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-ready-") as raw:
        base = Path(raw).resolve()
        d = _archived_devices(base)
        env = d.env(d.a)
        if d.keel(d.a, "lock", "acquire", "--branch", "feat").returncode != 0:
            report(f"{label} could not acquire feat.")
            return 1
        d.git(d.a, "branch", "scratch", "feat")
        d.git(d.a, "checkout", "-q", "scratch")
        d.git(d.a, "commit", "-q", "--allow-empty", "-m", "local only")
        d.git(d.a, "checkout", "-q", "feat")
        chat = Path(d.git(d.a, "rev-parse", "--path-format=absolute", "--git-common-dir")) / "keel-chat"
        # A remote that cannot be reached: ready refuses and stores nothing.
        d.git(d.a, "remote", "set-url", "origin", str(base / "nowhere.git"))
        failed = run_keel(d.a, "shift", "ready", "next: rerun R007", env=env)
        if failed.returncode != 1 or (chat / "shift" / "pm.md").exists() or (chat / "shift-notes").exists():
            report(f"{label} with the remote unreachable ready should exit 1 and store nothing: {failed.returncode} "
                   f"{failed.stderr.strip()[:300]}")
            return 1
        d.git(d.a, "remote", "set-url", "origin", str(d.remote))
        done = run_keel(d.a, "shift", "ready", "next: rerun R007", env=env)
        if done.returncode != 0:
            report(f"{label} ready should succeed: {done.stderr.strip()[:400]}")
            return 1
        message = d.lock_message()
        if _trailer(message, "keel-lock") != "released":
            report(f"{label} the lock should be released: {message}")
            return 1
        head = d.git(d.a, "rev-parse", "HEAD")
        if _trailer(message, "Head") != head:
            report(f"{label} the released Head should be {head[:8]}: {message}")
            return 1
        note_path = _trailer(message, "Note") or ""
        if not note_path.startswith("shift-notes/pm/"):
            report(f"{label} Note should name a shift-notes/pm/ file: {note_path!r}")
            return 1
        if "next: rerun R007" not in _note_body(chat / note_path):
            report(f"{label} the file Note names does not hold the note: {note_path!r}")
            return 1
        archived = d.git(d.a, "ls-tree", "-r", "--name-only", "refs/heads/keel-chat").split()
        if note_path not in archived:
            report(f"{label} the archive does not carry {note_path}: {archived}")
            return 1
        stored = _note_body(chat / "shift" / "pm.md")
        if "## Not on the remote at hand-over" not in stored or "scratch" not in stored.split("## Not on the remote at hand-over")[1]:
            report(f"{label} the stored note should end with the local-only section naming scratch: {stored}")
            return 1
    with tempfile.TemporaryDirectory(prefix="keel-shift-ready-off-") as raw:
        base = Path(raw).resolve()
        r = _Repo(base)
        env = {**r.env, "KEEL_CHAT_ROLE": "pm"}
        chat = r.chat()
        plain = run_keel(r.repo, "shift", "ready", "just the text", env=env)
        body = _note_body(chat / "shift" / "pm.md")
        for failed, why in ((plain.returncode != 0, f"ready with nothing to list failed: {plain.stderr.strip()}"),
                            (not body.rstrip().endswith("just the text"), f"the note should end with the text given: {body!r}"),
                            ("Not on the remote" in body, f"with nothing to list the note carries a section: {body!r}")):
            if failed:
                report(f"{label} {why}")
                return 1
        run_keel(r.repo, "shift", "resume", env=env)
        r.git("branch", "scratch", "main")
        r.git("checkout", "-q", "scratch")
        r.commit("s1")
        r.git("checkout", "-q", "main")
        listed = run_keel(r.repo, "shift", "ready", "with a branch left", env=env)
        body = _note_body(chat / "shift" / "pm.md")
        for failed, why in ((listed.returncode != 0, f"ready without the declaration failed: {listed.stderr.strip()}"),
                            ("## Not on the remote at hand-over" not in body, f"the section is missing: {body!r}"),
                            ("scratch" not in body, f"the section does not name scratch: {body!r}")):
            if failed:
                report(f"{label} {why}")
                return 1
        if r.git("for-each-ref", "refs/keel/"):
            report(f"{label} without the declaration a lock ref was written.")
            return 1
    report("shift-ready-releases-lock scenario passed.")
    return 0


def validate_shift_resume_takes_over_scenario() -> int:
    """#526 D14: resume is the takeover: switch, acquire, pull the archive, print the note."""
    label = "shift-resume-takes-over:"
    with tempfile.TemporaryDirectory(prefix="keel-shift-resume-") as raw:
        base = Path(raw).resolve()
        d = _archived_devices(base)
        a_env = d.env(d.a)
        if d.keel(d.a, "lock", "acquire", "--branch", "feat").returncode != 0:
            report(f"{label} could not acquire feat on a.")
            return 1
        d.git(d.a, "commit", "-q", "--allow-empty", "-m", "a's last commit")
        d.git(d.a, "push", "-q", "origin", "feat")
        head = d.git(d.a, "rev-parse", "HEAD")
        ready = run_keel(d.a, "shift", "ready", f"next: verify feat @ {head[:10]}", env=a_env)
        if ready.returncode != 0:
            report(f"{label} a could not hand over: {ready.stderr.strip()[:300]}")
            return 1
        d.git(d.b, "checkout", "-q", "main")
        b_env = {**_git_env(), "KEEL_CHAT_ROLE": "pm"}
        run_keel(d.b, "chat", "role", "--set", "pm", env=b_env)
        resumed = run_keel(d.b, "shift", "resume", env=b_env)
        if resumed.returncode != 0:
            report(f"{label} resume on b failed: {resumed.stderr.strip()[:400]}")
            return 1
        if d.git(d.b, "rev-parse", "--abbrev-ref", "HEAD") != "feat" or d.git(d.b, "rev-parse", "HEAD") != head:
            report(f"{label} b should be on feat at a's head {head[:8]}.")
            return 1
        holder = _trailer(d.lock_message(), "Holder") or ""
        if _trailer(d.lock_message(), "keel-lock") != "held":
            report(f"{label} the lock should be held after b's resume: {d.lock_message()}")
            return 1
        if not holder.startswith("pm@"):
            report(f"{label} the holder should be pm at b's device, got {holder!r}")
            return 1
        if f"next: verify feat @ {head[:10]}" not in resumed.stdout:
            report(f"{label} resume should print a's note: {resumed.stdout[:400]}")
            return 1
        # A third clone: a dirty worktree, then a live lock held elsewhere, are refused.
        c = d.clone("c", "pm")
        d.git(c, "checkout", "-q", "main")
        c_env = {**_git_env(), "KEEL_CHAT_ROLE": "pm"}
        run_keel(c, "chat", "role", "--set", "pm", env=c_env)
        (c / "untracked.txt").write_text("x\n", encoding="utf-8")
        dirty = run_keel(c, "shift", "resume", env=c_env)
        if not _expect(label, "resume over an untracked file", dirty, 1, ("untracked.txt",)):
            return 1
        (c / "untracked.txt").unlink()
        held = run_keel(c, "shift", "resume", env=c_env)
        if not _expect(label, "resume while b holds feat live", held, 1, (holder,)):
            return 1
        if "next: verify" in held.stdout:
            report(f"{label} a refused resume printed the note as current.")
            return 1
    report("shift-resume-takes-over scenario passed.")
    return 0


def validate_handover_waits_for_lock_scenario() -> int:
    """#526 D17: a queued hand-over starts no session while another device holds the branch."""
    label = "handover-waits-for-lock:"
    with tempfile.TemporaryDirectory(prefix="keel-handover-lock-") as raw:
        base = Path(raw).resolve()
        d = _Devices(base)
        if d.keel(d.b, "lock", "acquire", "--branch", "feat").returncode != 0:
            report(f"{label} b could not acquire feat.")
            return 1
        d.git(d.a, "fetch", "-q", "origin", "+refs/keel/lock/*:refs/keel/lock/*")
        a_env = d.env(d.a)
        run_keel(d.a, "chat", "role", "--set", "pm", env=a_env)
        chat = Path(d.git(d.a, "rev-parse", "--path-format=absolute", "--git-common-dir")) / "keel-chat"
        write_text(chat / "shift" / "queue" / "pm.json", json.dumps({
            "role": "pm", "session": "11111111-2222-3333-4444-555555555555", "pid": None,
            "worktree": str(d.a), "requested_at": "2026-11-16T08:00:00+08:00", "state": "pending"}))
        calls = base / "claude.log"
        stub = base / "claude"
        stub.write_text(f'#!/bin/sh\nprintf "%s\\n" "$*" >> "{calls}"\n'
                        'case "$1" in agents) echo "[]";; esac\nexit 0\n', encoding="utf-8")
        stub.chmod(0o755)
        tick = run_keel(Path("/"), "tick", "--repo", str(d.a), env={**a_env, "KEEL_CLAUDE": str(stub)})
        started = [line for line in (calls.read_text(encoding="utf-8").splitlines() if calls.exists() else []) if "--bg" in line]
        if started:
            report(f"{label} a session was started while b holds feat: {started} {tick.stdout[-300:]}")
            return 1
        entry = json.loads((chat / "shift" / "queue" / "pm.json").read_text(encoding="utf-8"))
        holder = _trailer(d.lock_message(), "Holder") or ""
        if "feat" not in str(entry.get("waiting_on")) or holder not in str(entry.get("waiting_on")):
            report(f"{label} the entry should wait naming feat and {holder}: {entry}")
            return 1
        shown = run_keel(d.a, "shift", "status", env=a_env)
        if "feat" not in shown.stdout or holder not in shown.stdout:
            report(f"{label} `keel shift status` does not name feat and the holder: {shown.stdout[:400]}")
            return 1
    report("handover-waits-for-lock scenario passed.")
    return 0


def validate_tick_renews_and_pushes_scenario() -> int:
    label = "tick-renews-and-pushes:"
    with tempfile.TemporaryDirectory(prefix="keel-tick-sync-") as raw:
        base = Path(raw)
        d = _Devices(base, _LOCK_CONFIG.replace("push:claude/*", "push"))
        env, log = _git_wrapper(base)
        env.update(KEEL_CHAT_ROLE="pm", KEEL_DEVICE="dev-a")
        d.keel(d.a, "lock", "acquire", "--branch", "feat", env=env)
        before = _trailer(d.lock_message(), "Expires")
        d.git(d.a, "commit", "--allow-empty", "-qm", "finished work")
        head = d.git(d.a, "rev-parse", "HEAD")
        log.write_text("")
        tick = run_keel(Path("/"), "tick", "--repo", str(d.a), "--json", env=env)
        message = d.lock_message()
        if tick.returncode:
            report(f"{label} tick failed: {tick.stderr}")
            return 1
        if _trailer(message, "Seq") != "2":
            report(f"{label} tick must renew once: {message}")
            return 1
        if _trailer(message, "Expires") <= before:
            report(f"{label} tick must renew from /: {tick.stdout} {tick.stderr}; lock {message}")
            return 1
        if d.git(d.a, "ls-remote", "origin", "refs/heads/feat").split()[0] != head or _trailer(message, "Head") != head:
            report(f"{label} tick must push finished work and record the remote Head: {message}")
            return 1
        pushes = _logged(log, "push")
        if any("--force" in line or not ("refs/heads/feat:refs/heads/feat" in line or ":refs/keel/lock/feat" in line) for line in pushes):
            report(f"{label} unexpected push: {pushes}")
            return 1
        other = {**env, "KEEL_DEVICE": "dev-b", "KEEL_CHAT_ROLE": "verify"}
        d.keel(d.a, "lock", "acquire", "--branch", "feat", "--break", "test takeover", env=other)
        # Restore the stale local observation so renewal must check the remote.
        old = d.git(d.a, "rev-parse", "refs/keel/lock/feat^")
        d.git(d.a, "update-ref", "refs/keel/lock/feat", old)
        held = d.lock_sha()
        first = run_keel(Path("/"), "tick", "--repo", str(d.a), env=env)
        second = run_keel(Path("/"), "tick", "--repo", str(d.a), env=env)
        if d.lock_sha() != held:
            report(f"{label} tick changed the other device lock")
            return 1
        if "dev-b" not in first.stdout:
            report(f"{label} takeover report missing: {first.stdout}")
            return 1
        if "dev-b" in second.stdout:
            report(f"{label} takeover was reported twice: {second.stdout}")
            return 1
        _declare_in(d, d.a, "sync:\n  lock: true\n")
        log.write_text("")
        run_keel(Path("/"), "tick", "--repo", str(d.a), env=env)
        if _logged(log, "push") or _logged(log, "ls-remote"):
            report(f"{label} no device-sync must leave network untouched: {log.read_text()}")
            return 1
    report("tick-renews-and-pushes scenario passed.")
    return 0


def validate_prompt_hook_renews_when_due_scenario() -> int:
    label = "prompt-hook-renews-when-due:"
    with tempfile.TemporaryDirectory(prefix="keel-prompt-sync-") as raw:
        base = Path(raw)
        d = _Devices(base)
        env, log = _git_wrapper(base)
        env["KEEL_DEVICE"] = "dev-a"
        d.keel(d.a, "lock", "acquire", "--branch", "feat", env=env)
        message = d.lock_message()
        # The commit trailer is the public lease clock; 15 minutes left means renewal is due.
        from datetime import datetime, timedelta, timezone
        due = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat().replace("+00:00", "Z")
        message = message.replace(_trailer(message, "Expires"), due)
        d.plant(message, d.lock_sha())
        d.git(d.a, "fetch", "-q", "origin", "+refs/keel/lock/feat:refs/keel/lock/feat")
        before = int(_trailer(message, "Seq"))
        payload = json.dumps({"cwd": str(d.a)})
        def prompt() -> subprocess.CompletedProcess[str]:
            from validation.common import ROOT
            return subprocess.run(["node", str(ROOT / "bin/keel.js"), "chat", "hook", "user-prompt-submit"],
                                  input=payload, cwd="/", env=env, text=True, capture_output=True)
        first, second = prompt(), prompt()
        if first.returncode or second.returncode or int(_trailer(d.lock_message(), "Seq")) != before + 1:
            report(f"{label} two due prompts must renew only once: {first.stdout} {first.stderr} / {second.stdout} {second.stderr}")
            return 1
        message = d.lock_message().replace(_trailer(d.lock_message(), "Expires"), due)
        d.plant(message, d.lock_sha())
        d.git(d.a, "fetch", "-q", "origin", "+refs/keel/lock/feat:refs/keel/lock/feat")
        state = d.a / ".git/keel-chat/lock-renewals.json"
        state.unlink(missing_ok=True)
        d.git(d.a, "remote", "set-url", "origin", str(base / "gone"))
        failed = prompt()
        if failed.returncode or failed.stdout or failed.stderr:
            report(f"{label} unreachable remote must stay quiet and exit 0: {failed}")
            return 1
        # A foreign lock in the last fetched refs makes no network calls.
        d.git(d.a, "remote", "set-url", "origin", str(d.remote))
        message = message.replace("Device: dev-a", "Device: dev-b")
        d.plant(message, d.lock_sha())
        d.git(d.a, "fetch", "-q", "origin", "+refs/keel/lock/feat:refs/keel/lock/feat")
        log.write_text("")
        prompt()
        if _logged(log, "push") or _logged(log, "ls-remote") or _logged(log, "fetch"):
            report(f"{label} a foreign lock must not renew: {log.read_text()}")
            return 1
    report("prompt-hook-renews-when-due scenario passed.")
    return 0


def validate_patrol_old_local_only_risk_scenario() -> int:
    label = "patrol-old-local-only-risk:"
    with tempfile.TemporaryDirectory(prefix="keel-patrol-sync-") as raw:
        base = Path(raw)
        r = _Repo(base)
        r.git("checkout", "-qb", "feat")
        wrap, log = _git_wrapper(base)
        wrap["KEEL_CHAT_ROLE"] = "pm"
        run_keel(r.repo, "chat", "role", "--set", "verify", env=_git_env())
        def commit_at(hours: int) -> None:
            env = {**r.env, "GIT_COMMITTER_DATE": f"{int(time.time()) - hours * 3600} +0000"}
            subprocess.run(["git", "commit", "--allow-empty", "-qm", "work"], cwd=r.repo, env=env, check=True)
        commit_at(30)
        def patrol() -> subprocess.CompletedProcess[str]:
            return run_keel(r.repo, "patrol", "--since-last", "--notify", env=wrap)
        def records(needle: str) -> list[str]:
            files = (r.chat() / "groups/dm-keel-patrol--pm/log").glob("*.md")
            return [f.read_text() for f in files if needle in f.read_text() and "kind: message" in f.read_text()]
        log.write_text("")
        runs = [patrol(), patrol(), patrol()]
        sent = records("feat")
        if len(sent) != 1:
            report(f"{label} keel-patrol must send one old feat risk, got {len(sent)}: {[x.stdout for x in runs]}")
            return 1
        if "verify" not in sent[0]:
            report(f"{label} old branch risk must name covered role verify: {sent}")
            return 1
        commit_at(0)
        patrol()
        if len(records("feat")) != 1:
            report(f"{label} growing feat must not send its risk twice")
            return 1
        r.git("checkout", "-qb", "recent", "origin/main")
        commit_at(2)
        recent = patrol()
        if "recent" in recent.stdout:
            report(f"{label} two-hour work should add no risk: {recent.stdout}")
            return 1
        r.git("checkout", "-q", "main")
        for i in range(20):
            (r.repo / f"dirty{i}").write_text("uncommitted")
        dirty = patrol()
        if "local-only" in dirty.stdout and "main" in dirty.stdout:
            report(f"{label} dirty paths alone should add no main risk: {dirty.stdout}")
            return 1
        for i in range(20):
            (r.repo / f"dirty{i}").unlink()
        (r.repo / "seed").write_text("stash this")
        env = {**r.env, "GIT_COMMITTER_DATE": f"{int(time.time()) - 3 * 86400} +0000"}
        subprocess.run(["git", "stash", "push", "-qm", "old stash"], cwd=r.repo, env=env, check=True)
        patrol(); patrol()
        if len(records("stash@{0}")) != 1:
            report(f"{label} old stash must send one standing risk: {records('stash')}")
            return 1
        if _logged(log, "fetch") or _logged(log, "ls-remote"):
            report(f"{label} patrol must use only local refs: {log.read_text()}")
            return 1
    report("patrol-old-local-only-risk scenario passed.")
    return 0


def validate_doctor_reports_branch_locks_scenario() -> int:
    label = "doctor-reports-branch-locks:"
    with tempfile.TemporaryDirectory(prefix="keel-doctor-sync-") as raw:
        d = _Devices(Path(raw))
        env = {**d.env(d.a), "KEEL_DEVICE": "dev-a"}
        d.keel(d.a, "lock", "acquire", "--branch", "feat", env=env)
        doctor = d.keel(d.a, "--doctor", env=env)
        sync = "\n".join(line for line in (doctor.stdout + doctor.stderr).splitlines() if "sync" in line)
        for expected in ("lock: true", "30m", "dev-a", "feat", _trailer(d.lock_message(), "Expires"), "last renewal", "hook"):
            if expected not in sync:
                report(f"{label} sync line lacks {expected!r}: {sync}")
                return 1
    report("doctor-reports-branch-locks scenario passed.")
    return 0


def validate_release_skips_nested_worktrees_scenario() -> int:
    from validation.common import ROOT
    label = "release-skips-nested-worktrees:"
    with tempfile.TemporaryDirectory(prefix="keel-release-nested-") as raw:
        fixture = Path(raw) / "candidate"
        def ignore(directory: str, names: list[str]) -> list[str]:
            excluded = {".git", "node_modules", "__pycache__"}
            if Path(directory) == ROOT / ".claude":
                excluded.add("worktrees")
            return [name for name in names if name in excluded]
        shutil.copytree(ROOT, fixture, ignore=ignore, symlinks=True)
        (fixture / "node_modules").symlink_to(ROOT / "node_modules", target_is_directory=True)
        subprocess.run(["git", "init", "-q", str(fixture)], check=True)
        nested = fixture / ".claude/worktrees/other"
        nested.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(nested)], check=True)
        version = json.loads((fixture / "package.json").read_text())["version"]
        marker = nested / "AGENTS.md"
        marker.write_text(f"<!-- keel:start version={version} -->\nindependent checkout\n")
        old = nested / "historical.md"
        old.write_text("<!-- keel:start version=5.28.0 -->\n")
        before = {p.name: p.read_bytes() for p in (marker, old)}
        bump = subprocess.run(["node", "scripts/bump_version.js", "minor"], cwd=fixture, text=True, capture_output=True)
        if bump.returncode:
            report(f"{label} bump failed: {bump.stderr}")
            return 1
        after_version = json.loads((fixture / "package.json").read_text())["version"]
        if after_version == version:
            report(f"{label} outer version did not increment")
            return 1
        for p in (marker, old):
            if p.read_bytes() != before[p.name]:
                report(f"{label} bump modified another checkout: {p.name}")
                return 1
        baseline = subprocess.run(["node", "scripts/run_python.js", "scripts/validate_plugin.py"],
                                  cwd=fixture, text=True, capture_output=True)
        if baseline.returncode:
            report(f"{label} baseline must ignore another checkout's markers: {baseline.stdout} {baseline.stderr}")
            return 1
    report("release-skips-nested-worktrees scenario passed.")
    return 0

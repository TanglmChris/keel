## Context

Issue #243, part of the #250 family. The owner decided on 2026-10-11 that its implementation is delegated to codex from this session, which reviews the result and re-runs every check.

## Facts

- F1 — `git worktree list --porcelain` lists every worktree with its path, head, and branch, or `detached`, plus `locked` and `prunable` markers.
- F2 — The chat store maps a worktree's absolute path to its role in `roles.json` (`src/core/chat/store.js` `readRoles`, `currentRole`), and `notice.presenceOf(where, role)` gives `online`, `idle`, or `offline` with `last_active`.
- F3 — Keel never fetches anything (AGENTS.md, Unattended runs), so ahead/behind is only as current as the last `git fetch` the caller ran, and issue update times can only come from what the caller passes.
- F4 — The default branch is what `refs/remotes/origin/HEAD` points at when it exists; otherwise `main`, then `master`, if one exists locally.

## Decisions

- D1 — The command is `keel worktrees`; Keel has no `status` command to hang a `--worktrees` flag on.
- D2 — Per worktree: `path`, `branch` (null when detached), `head` (short), `upstream` (null when none), `ahead` and `behind` (null without an upstream), `lastCommit` (`subject`, `time` as ISO), `dirty` (count of `git status --porcelain` lines), `role` (null when unbound), `presence` (`state`, `last_active`, or null without a role), `issues` (sorted unique numbers from `#<n>` in the subjects and bodies of commits in `<default>..HEAD`), and `locked`/`prunable` as Git reports them. A worktree whose directory is gone is listed with `missing: true` and nothing else read.
- D3 — The text output says ahead/behind are as of the last fetch, and names the default branch it compared against.
- D4 — `--issues <file>` reads a JSON array of objects with `number` and `updatedAt`. A referenced issue found there carries `updatedAt`; one not found carries null. A file that cannot be read or parsed is refused, naming it, with exit 1, and nothing else is printed.
- D5 — The command writes nothing: no file under the repository or the chat store changes, which the scenario checks by comparing the chat store's files before and after.
- D6 — Running job counts against a declared budget (the issue's later ask) are out of scope.

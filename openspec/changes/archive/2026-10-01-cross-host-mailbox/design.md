## Context

Issue #180 proposes a Markdown mailbox between hosts, with each host receiving through its own hooks. The owner decided the four open questions on 2026-10-01: location, gate, receipt timing, and addressing (D1–D4). Host behavior below was probed on Claude Code 2.1.283 on this machine.

## Goals / Non-Goals

**Goals:** a host-neutral store and CLI that any session can send from and read with; Claude Code sessions are told about mail at session start, at each prompt, and while idle.

**Non-Goals:** Codex's receiving hooks (the owner leaves those to Codex); writing into any host's session storage; a gate on unread mail; delivery across machines; treating message content as authority.

## Decisions

- F1 — On Claude Code 2.1.283 a SessionStart hook returning `hookSpecificOutput.watchPaths` with an absolute path makes a later external change to that file run FileChanged hooks with `event: "change"` and that `file_path`; the same list at the top level of the output started no watcher. Basis: 2026-10-01 headless probes in a scratch repository.
- F2 — On Claude Code 2.1.283 a FileChanged hook with `asyncRewake: true` that exits 2 wakes an idle session: in a `--input-format stream-json` session that had finished its turn, an external change produced a new assistant turn quoting the hook's stderr. Within a single `-p` turn the same stderr did not reach the model. Basis: the same probes.
- F3 — `plugins/keel/hooks/hooks.json` is loaded by Codex as well as mirrored into the Claude root manifest, and FileChanged and `asyncRewake` are Claude Code fields. Basis: `native-plugin-manifests` and the Codex default-discovery check in `scripts/validate_plugin.py`.
- D1 — The mailbox lives at `<git common dir>/keel-mailbox/`, so every worktree of a repository shares one store, repositories stay isolated, and nothing enters version control. Basis: owner's choice, 2026-10-01.
- D2 — Delivery and notice only; no gate reads the mailbox. A message is data and grants no authorization; the single-writer rule is unchanged. Basis: owner's choice, 2026-10-01.
- D3 — Claude Code is notified at SessionStart and UserPromptSubmit and is woken while idle by a FileChanged `asyncRewake` hook watching a per-role signal file (F1, F2). Because F2 shows mid-turn rewake text can be lost, notices are pointers that stay true until the mail is read — every notice lists the unread messages and the `keel mail read` command — rather than the only copy of a body. Codex's receiving side is left to Codex. Basis: owner's choice, 2026-10-01, that idle wake-up is required and Codex may develop its own side.
- D4 — Addresses are user-chosen role names (`^[a-z0-9][a-z0-9-]{0,31}$`), bound to a worktree's absolute top-level path in `roles.json` inside the mailbox, overridable per process by `KEEL_MAIL_ROLE`. Basis: owner's choice, 2026-10-01.
- D5 — Layout: `<role>/new/<id>.md` for unread, `<role>/done/<id>.md` for read, `<role>/.signal` appended on each delivery, and `.tmp/` for atomic write-then-rename. An id is `<UTC timestamp>-<from>-<random>`. Reading prints the message and renames it into `done/`. Basis: issue #180's delivery and receipt proposal.
- D6 — The mailbox hooks are declared only in the Claude root manifest, and `plugins/keel/hooks/hooks.json` stays the Codex-shared set (F3). The hook script resolves the CLI the way `session-start.js` does and exits 0 with no output when the worktree has no role. Basis: F3 and D3.

## Hidden Knowledge / Assumptions

None beyond F1–F3, which are recorded probes rather than assumptions.

## Risks / Trade-offs

- UserPromptSubmit runs the hook on every prompt. With no role bound it returns after one `git rev-parse`; with unread mail the notice repeats until the mail is read, which is the intended inbox-badge behavior.
- Wake-up depends on the host's file watcher (F1, F2) and is not provable by a Keel gate; the validation checks the hook contract (output shape and exit code), and the probes are the host evidence.

## Open Questions

None.

## Context

Issues #241 and #246; owner decisions of 2026-10-11 recorded on #241 (scope by worktree; read-only declaration; read-only capsule command not chosen) and answered in conversation the same day (read-only as `read_only_roles:` in `keel/config.yaml`; ownership by `owner:` first, then branch history).

## Facts

- F1 — `inferContext` in `src/core/context.js` reads `openspec/changes/` in the current working tree only, compiles each active change with `selectionForChange`, and returns `blocked` for one blocked candidate and `ambiguous` for several.
- F2 — `pauseDeclaration` already reads a `keel:` block from a change's `.openspec.yaml`; an entry other than `status: paused` is reported as unreadable only when `status` is present.
- F3 — The chat role bound to a worktree is read by `currentRole` in `src/core/chat/store.js`, from the repository's chat store or `KEEL_CHAT_ROLE`.
- F4 — `plugins/keel/scripts/session-start.js` prints "next: run `keel context` and select an owner explicitly" for every non-ready status.
- F5 — The published continuity spec forbids using Git dirty state to choose a change.

## Decisions

- D1 — A change whose `keel:` block declares `owner: <role>` belongs to the worktree bound to that role; a worktree bound to another role, or to none, treats it as elsewhere.
- D2 — With no owner declared, a change belongs elsewhere when another worktree's branch has commits touching `openspec/changes/<change>/` beyond the default branch and this worktree's `HEAD` has none. Only committed history counts, never dirty state (F5). Without a resolvable default branch, this step decides nothing.
- D3 — Inference runs over the changes that belong here, exactly as before. Each change belonging elsewhere is reported as `Change <c> (<status>) belongs to <role R | worktree W on branch B>; it does not set this session's status.`, in the result's reasons when nothing here is actionable and in its warnings otherwise, and in a structured `elsewhere` list. When every active change belongs elsewhere, the status is `idle`.
- D4 — `read_only_roles:` is a list of chat role names; an entry that is not a role name is reported and ignored. When this worktree's bound role is listed, `keel context` without `--change` and without a HANDOFF returns `idle` with one reason, `Read-only session: role <r> is listed in keel/config.yaml read_only_roles, so no change is selected.`, and a `readOnly` field. Explicit selection and HANDOFF keep their precedence.
- D5 — The session-start note, for a `readOnly` result, prints `next: none — read-only session (role <r>)` in place of the select-an-owner line.

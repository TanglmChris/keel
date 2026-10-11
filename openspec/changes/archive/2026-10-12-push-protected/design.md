## Context

Issue #280 and the owner's decision of 2026-10-12 recorded on it.

## Facts

- F1 — `checkPushes` in `plugins/keel/scripts/pretooluse-guard.js` denies a push whose target matches no `push:` glob, and runs only when one is declared; `readPushGlobs` reads `push:` entries itself.
- F2 — The Claude Code hooks reference (read 2026-10-12): `"ask"` prompts the user to confirm, and a hook's `"ask"` also forces a permission prompt in auto mode, where the classifier can deny but cannot approve silently. It does not document `bypassPermissions`, `dontAsk`, or `-p`. A probe with `claude -p` 2.1.283 could not run: the CLI's OAuth session on this machine had expired.
- F3 — The PreToolUse hook input carries `permission_mode`.
- F4 — A worktree's chat role is in `<git common dir>/keel-chat/roles.json`, or `KEEL_CHAT_ROLE`.

## Decisions

- D1 — `push-protected:<glob>` or `push-protected:<glob>@<role>`: required scope, glob from branch-name characters and `*`, role a chat role name. It may repeat. A bare `push` beside it is refused, as beside `push:` (it would allow every branch).
- D2 — The push check runs when any `push:` or `push-protected:` entry exists. A target matching a `push:` glob passes; else one matching a `push-protected:` glob is asked; else it is denied. One command with several targets is denied if any is denied, else asked if any is protected.
- D3 — For a protected target: if the entry names a role and the session's bound role (F4) differs, deny naming the role. If `permission_mode` is `bypassPermissions` or `dontAsk`, deny naming the mode, since F2 cannot show a prompt appears there. Otherwise return `ask` with a reason naming the branch. This fails closed in every mode F2 left unmeasured.
- D4 — `keel --doctor` reports `push-protected` with its globs and roles, and the enforcement line covers both forms.

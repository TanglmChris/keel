## Why

Issue #280 (rtl_ppa_prj, 2026-10-11): with `push:<glob>` enforced (#257), a repository must either list `main` — so every session may push it — or not, so not even the coordinator can. rtl_ppa_prj's rule is that only the PM session pushes `main`, each time with the user's approval. The owner decided on 2026-10-12: the guard asks the host, so the user approves that one push, optionally only for a named role; and the behavior of `ask` under every permission mode is checked before shipping.

## What Changes

- `push-protected:<branch glob>`, or `push-protected:<branch glob>@<role>`, in `authorize:` names a branch the Claude write guard does not refuse but asks about: a push to it returns `permissionDecision: "ask"`, so Claude Code asks the user to confirm that one command. Keel stores no approval; the next push asks again.
- With `@<role>`, only a session bound to that role is asked; any other session is refused, naming the role.
- Where the host cannot be relied on to ask — `bypassPermissions` and `dontAsk` — the push is refused instead, naming the mode.
- Branches neither in `push:` nor in `push-protected:` are refused as before. Declaring `push-protected:` turns the check on by itself, and a bare `push` beside it is refused.
- `keel --doctor` lists the protected globs with the same enforcement line.

## Capabilities

### Modified Capabilities
- `keel-standing-authorization`: a protected-branch form.
- `keel-touch-write-guard`: a push to a protected branch is asked, not refused.

## Impact

`src/core/config.js`, `bin/keel.js`, `plugins/keel/scripts/pretooluse-guard.js`, `README.md`, `keel/config.yaml` (comments), `scripts/validate_plugin.py`, two published specs, and the changelog.

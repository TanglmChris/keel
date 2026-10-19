## Context

`readStandingAuthorization` (`src/core/config.js`) is read by the task capsule, `keel context`, the chat (`chat-reply` groups in `notice.js` and `wake.js`), the shift commands and `keel --doctor`. The Claude write guard (`plugins/keel/scripts/pretooluse-guard.js`) parses `push:` and `push-protected:` lines itself, spawns no Keel CLI, and reads the session's role from `KEEL_CHAT_ROLE` or `roles.json`.

## Facts

- F1 — kaiwu-ip's `authorize:` (main, 2026-10-19) holds `push-protected:main@kaiwu-pm-iecc`, eight `push:` globs, and one each of `issue:`, `issue-close:`, `cleanup:scratch` and `chat-reply:dmc-iecc`, grouped by comments.
- F2 — The guard skips the push check when no `push:` and no `push-protected:` line is declared (`checkPushes`).

## Decisions

- D1 — Every scoped action (`issue`, `issue-close`, `cleanup`, `chat-reply`, `push:<glob>`, `push-protected`) accepts an optional `@<pattern>` suffix. The pattern is chat-role characters plus `*`, which matches any run of them. A malformed suffix is refused like any malformed scope, and the whole declaration authorizes nothing. Unscoped actions take no role: `commit@x` stays an unknown action.
- D2 — `readStandingAuthorization(repo, { role })` filters by the session's role. When `role` is not passed, it resolves it as the chat does: `KEEL_CHAT_ROLE` or `KEEL_MAIL_ROLE`, else the worktree's binding in `roles.json`, read through `renames.json`. An entry whose pattern does not match is left out of `declared`, `scopes`, `chatReplyGroups` and `pushGlobs`, and is listed in `otherRoles`. `push-protected` is the exception: it stays listed for every session with its pattern, as today, because its pattern already says who may ask, and the guard refuses every other role by name (#280). A session with no role gets no role-limited entry. The bare-`push` conflict is checked against every entry, whatever its role.
- D3 — The guard parses `push:<glob>@<pattern>` and role globs on `push-protected`. The check runs while any push entry is declared, for any role. A branch counts as allowed only by an entry whose pattern matches the session's role. A branch that some other role's entry covers is refused naming that pattern and the session's role.
- D4 — `keel --doctor` prints the per-action lines for the current worktree's role, followed by `roles` lines: for each role bound in `roles.json`, the scoped entries that apply to it.

## Risks

- The tracker, chat and scratchpad scopes stay carried, not enforced, as before: the role only decides which session reads the grant.

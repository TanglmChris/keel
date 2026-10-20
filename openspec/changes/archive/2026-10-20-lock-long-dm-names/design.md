## Context

A direct group is named `dm-<a>--<b>` from its two sorted roles (`directName`). Its members are read back from the name (`directMembers`), and role renames are mapped through that reading. Group names are checked against the role-name pattern `^[a-z0-9][a-z0-9-]{0,31}$`, which is 32 characters at most. Two role names can each be up to 32 characters, so a direct group name can be up to 69.

## Facts

- F1 — #403: `dm-kaiwu-design-iecc--kaiwu-pm-iecc` is 35 characters. `keel lock release`, the expiry sweep, and `keel lock list` all failed on it, because `notify` posts through `directPost` → `createGroup` → `checkName(group, "Group")` before the lease file is removed.
- F2 — `listGroupNames` filters the `groups/` directory with the same pattern, so a longer direct group written by some other path would not be listed either.
- F3 — `AUTHORIZATION_SCOPES["chat-reply"]` in `src/core/config.js` uses the same 32-character pattern for `<group>`.
- F4 — A group name is used as a directory name and in record fields only. 69 characters is well within filesystem limits.

## Decisions

- D1 — `validGroup(name)` is true for a valid role-shaped name, or for `dm-<a>--<b>` that splits on `--` into exactly two valid role names with `a < b`. `checkGroup` refuses anything else, naming both forms. It replaces `checkName(group, "Group")` in `createGroup`, `post`, `wait`, `view`, and `keel chat summary --group`, and the filter in `listGroupNames`. The `chat-reply` scope pattern accepts the same direct form. Direct names stay derived from the roles, so `directMembers` and rename mapping keep working unchanged. No hashing is used, because a hashed name could not be read back into members.
- D2 — `release` and `reap` remove the lease file before notifying. `notify` posts to each role separately and collects each failure as a warning line naming the role and the reason. `runLock` prints warnings to stderr as `keel lock: warning: …`, and they do not change the exit status.

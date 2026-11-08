## Facts

- F1 — `pushTargets` in `plugins/keel/scripts/pretooluse-guard.js` reads each refspec's destination; `refs/heads/x` becomes branch `x`, any other `refs/…` returns `undetermined: "<raw> is not a branch"`, which the check turns into a deny naming the declared grants. `--delete` and a `:dst` refspec make the destination the deletion target.
- F2 — `checkPushes` skips a repository that declares neither `push:` nor `push-protected:` (`continue`); with either, a branch matching no grant is `outside` and denied. A push carrying tags (`--follow-tags`, `push.followTags`) is allowed only when every target is a protected branch, as an ask.
- F3 — `readPushGlobs` reads `push:` and `push-protected:` lines of `authorize:` by regex, deliberately not through the validator, so a typo elsewhere leaves the check standing (#257 D3). Role patterns after `@` are matched by `roleMatches`.
- F4 — `src/core/config.js` holds the accepted vocabulary: `STANDING_AUTHORIZATION_ACTIONS`, `SCOPED_AUTHORIZATION_ACTIONS`, `AUTHORIZATION_SCOPES` (form and pattern per action), a message per malformed action, and `readStandingAuthorization`, whose `scopes` map `keel --doctor` prints as `<action>: authorized … scoped to <scope>`.
- F5 — `git push origin tag v1` is git's shorthand for `refs/tags/v1:refs/tags/v1`; the refspec list after the remote is `["tag", "v1"]`.

## Decisions

- D1 — The action is `push-tag`, scoped (a bare form is refused), with the branch-glob pattern `[A-Za-z0-9._/*-]+` and an optional `@<role>`, in `config.js` as a sibling of `push-protected`. It does not take part in the "bare `push` beside scoped ones" check: a tag grant widens no branch.
- D2 — `pushTargets` returns `tagTargets` beside `targets`. A destination under `refs/tags/` with no deletion, and each name after a `tag` word, are tag targets; `--delete` / `-d` / a `:refs/tags/x` refspec keep returning the undetermined verdict (F1), as do `--tags`, `--mirror` and the rest of `PUSH_UNDETERMINED`.
- D3 — `checkPushes` evaluates tag targets after the branch targets: a tag is allowed when some `push-tag:` entry of this session's role (or with no role) matches it; otherwise the push is denied naming `push-tag:` and the declared tag grants, or, when only another role's grant matches, that role (as `push:` does). A tag push never asks.
- D4 — A repository declaring `push-tag:` alone is checked for tags only: branch targets are not limited, since no branch grant was declared (F2), and the verdicts that a missing branch grant would add are skipped. With `push:` or `push-protected:` also declared, branches are limited as before.
- D5 — `readPushGlobs` also reads `push-tag:` lines by the same regex (F3); `declared` in messages lists them.
- D6 — `keel --doctor` prints the `push-tag` scope through the existing loop, leaves it out of the "carried, not enforced" note, and adds one line saying the Claude write guard enforces it.

## Context

Issue #327 reports that `git push --follow-tags origin <granted branch>` passes the Claude write guard and publishes annotated tags, although every explicit tag push is refused. The issue offers two remedies — deny unless a tag rule grants it, or require a `push-protected` branch (ask) — and an optional `push-tag:<glob>@<role>` grant. This change takes the second remedy and leaves the grant out (D4).

## Facts

- F1 — `pushTargets` (`plugins/keel/scripts/pretooluse-guard.js`) lists `--follow-tags` and `--no-follow-tags` in `PUSH_FLAGS` and skips both; `--tags` is in `PUSH_UNDETERMINED` and denied.
- F2 — `findPushes` skips a global `-c <key=value>` without reading it, and skips leading `NAME=value` assignments.
- F3 — git resolves `push.followTags` itself: `git -C <dir> -c push.followTags=false config --type=bool --get push.followTags` prints `false`, a bare `-c push.followTags` prints `true`, the last `-c` wins over repository config, and the key is case-insensitive (git 2.50.1, probed 2026-10-18). Environment config (`GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_<n>`, `GIT_CONFIG_PARAMETERS`) set in the hook's own environment is read the same way, since the hook's git inherits it.
- F4 — A `push-protected:` ask already carries the role limit and refuses `bypassPermissions`/`dontAsk` (#280).

## Decisions

- D1 — A push carries tags when the last of `--follow-tags`/`--no-follow-tags` in its arguments is `--follow-tags`; with neither, when `git -C <dir> <each -c pair of the command> config --type=bool --get push.followTags` prints `true`. git does the parsing (F3), so the guard does not re-implement boolean or key-case rules.
- D2 — A push that carries tags is never allowed by a `push:` glob alone. When every target matches a `push-protected:` entry, it takes that entry's path (role check, mode refusal, `ask`), and the ask reason says the push also carries annotated tags. Otherwise it is denied, naming `--follow-tags` or `push.followTags` and `--no-follow-tags` as the way to push the branch alone.
- D3 — A `git` command preceded by a `GIT_CONFIG*` assignment (`GIT_CONFIG`, `GIT_CONFIG_COUNT`, `GIT_CONFIG_PARAMETERS`, `GIT_CONFIG_KEY_<n>`, …) in a push segment is denied as undetermined, naming the variable: it can set `push.followTags` for that command only, out of the guard's sight.
- D4 — No `push-tag:` grant. The reporting project's coordinator already pushes tags with `main` under the user's approval, which D2 keeps; a grant is new authorization syntax with no second user and can be added when one appears.
- D5 — Nothing changes while no `push:` or `push-protected:` entry is declared: the guard still intercepts nothing then.

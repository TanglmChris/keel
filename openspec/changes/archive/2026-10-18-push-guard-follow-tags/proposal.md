## Why

Issue #327 (rtl_ppa_prj #300, 2026-10-13): the Claude write guard judges a `git push` only by its branch refspecs. With `--follow-tags`, or with `push.followTags=true` in git config, git also pushes every local annotated tag that points at a pushed or already-remote commit and is missing on the remote. So a session holding a `push:flow-*` grant can publish any annotated tag, release tags included, by pushing its own feature branch: `git push --follow-tags origin flow-release-tag-300` is allowed today, while every explicit tag push is refused. Tags are outward-facing and hard to retract once fetched.

## What Changes

- The guard treats a push that carries tags — `--follow-tags` not undone by a later `--no-follow-tags`, or neither flag and `push.followTags` true for that command (repository config, environment, or `git -c`) — as a tag push.
- Such a push is never allowed outright. When every target branch matches a `push-protected:` entry, it takes that entry's ask path (role limit and permission-mode refusal included), and the ask says it also pushes annotated tags. Otherwise it is denied, naming the tag carriage and `--no-follow-tags`.
- A `git` invocation preceded by a `GIT_CONFIG*` environment assignment is refused as undetermined, since that assignment can turn tag carriage on where the guard cannot read it.
- No `push-tag:` grant is added; the coordinator's existing workflow (push main with `--follow-tags` under the user's approval) keeps working through the protected ask.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-touch-write-guard`: a push that carries tags is a tag push.

## Impact

`plugins/keel/scripts/pretooluse-guard.js`, `scripts/validate_plugin.py`, `README.md`, one published spec, the changelog.

## Why

`#72` measured that `keel gate task-complete`'s dirty-worktree attribution subtracts a path from
attribution the moment it was dirty when the task started, regardless of what happens to it
afterwards. Two tasks of the same change, each declaring one file in Touch, walked in the normal
order this repository's own tasks run in — no commit between them — and the second task's
undeclared write to the first task's now-dirty output passed `task-complete` and
`change-close --action archive` with zero problems and zero warnings. The issue measured this
shape as the common case, not the edge case: 81% of this repository's 44 archived changes carry
two or more tasks, and 70% of tasks are not the first task of their change, so most tasks begin
with a tree that already carries a prior task's legitimate output — and every one of those paths
is, today, a no-further-checks zone for every task that follows.

Three directions were measured on the issue (2026-08-03). **乙** (commit after every task) was
excluded because it collides with `repo-action` being the only mode allowed to commit — a
protocol change, not a gate fix. **丙** (exempt only the union of prior tasks' own declared
Touch, not every path dirty at start) was the initial recommendation and the owner's first
decision (2026-08-04), but replaying it against this repository's own 44 archived changes fires
458 times across 87% of non-first tasks — the same structural fact that makes the issue common
makes the fix noisy on the same scale, without ever catching the actual defect the issue
reproduces (the 2026-08-04 measurement's own probe change never triggered it). At least one of
those 458 replays is already proven false: `2026-08-04-a-word-inside-a-word-is-not-the-word`'s
own Review recorded `scripts/install_to_repo.py` as this task's legitimate, already-attributed
output, not an unowned write.

The owner picked **甲** over 丙 (2026-08-05, [dasauto#18](https://github.com/TanglmChris/dasauto/issues/18)):
record a content signature (sha256, or absent) for each dirty path at task start, and attribute
a path only when that signature no longer matches at completion. This answers the question the
issue actually asks — "did this task write it again" — without reading `startedDirty` as a set
of names uninterested in what they held.

## What Changes

- `keel gate task-start` records each dirty path's content signature alongside its name in
  `keel/guard.json`, taken at the same moment and by the same worktree read `gitPaths` already
  uses, so recording and comparing never disagree about what "dirty" means.
- `keel gate task-complete`'s default (no `--base`) comparison exempts a path already dirty at
  task start only while its content still matches the signature recorded then. A path whose
  content changed since task start is attributed as outside Touch even though it was already
  dirty when the task began — the defect `#72` reproduces.
- `--base`-driven comparison, the completed-sibling exclusion, the guard-manifest and
  change-directory exemptions, and every other `outside-touch` behavior are unchanged: this
  touches only the no-base, has-a-record branch of `scopeEvidence`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-touch-write-guard`: the manifest's recorded dirty-path set carries a content signature
  per path, not only the path.
- `keel-core-gates`: the "already dirty at task start" exemption is conditioned on the path's
  content being unchanged since task start, instead of unconditional.

## Impact

- `src/core/guard.js` — `startGuard` hashes each dirty path's content when it records
  `startedDirty`; a new `contentSignature` helper backs both this write and the completion-side
  comparison; the manifest shape check for `startedDirty` validates the new per-entry shape.
- `src/core/gates.js` — `scopeEvidence`'s no-base branch compares each baseline entry's recorded
  signature against its current one instead of subtracting the whole recorded path set.
- `scripts/validate_plugin.py` — the existing `default-completion-attributes-writes` scenario
  gains an assertion that a path dirty at task start and then modified again by the task is
  attributed, alongside its existing assertion that one left unmodified is not.
- `plugins/keel/skills/keel-review-checklist/SKILL.md` and `src/skills/keel-review-checklist/SKILL.md`
  — the sentence stating the old unconditional exemption is corrected to state the content
  condition.
- No change to `--base`-driven comparison, `pathAllowed`, `completedSiblingOwners`, the
  guard-manifest or change-directory exemptions, `gitPaths`, or the write guard
  (`plugins/keel/scripts/pretooluse-guard.js`), which was already established (issue #72's own
  measurement) to bind only the host's file-writing tools and to be a separate, already-shipped
  concern (5.15.0/5.16.0) rather than one this change touches.

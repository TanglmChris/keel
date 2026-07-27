## Why

`openspec/changes/follow-up-backlog/` was created as the durable owner for deferred project follow-ups. It has not earned its keep, and it actively harms continuity.

It carries a `proposal.md` and a `specs/follow-up-ownership/spec.md` but **zero task checkboxes**. That shape is not the storage-only backlog the continuity spec expects to exclude from inference (`keel-stateless-continuity / Keel resolves continuity conservatively / Storage-only standing backlog does not create ambiguity` requires a directory with no proposal, design, specs, or task checkboxes). Instead it matches `Incomplete authoring remains actionable`, so `keel context` correctly but uselessly reports it as the current owner with `nextAction: author` in perpetuity:

```
$ keel context --json
"status": "ready",
"selection": { "source": "inferred", "change": "follow-up-backlog", "task": null },
"nextAction": { "kind": "author" }
```

Every session therefore starts pointed at a change nobody intends to author. This is not a Keel defect — Keel follows its spec. The directory is mis-shaped for its purpose.

Its spec delta was never synced: `openspec/specs/` holds seventeen `keel-*` capabilities and no `follow-up-ownership`. The authority it tried to establish is already carried by a synced capability — `keel-expectation-slice-evidence-gates` requires each critical expectation to have behavior evidence, a durable follow-up owner, or an explicit discard reason, and requires unresolved follow-ups to live outside `keel/HANDOFF.md`. That requirement never mandated an OpenSpec change as the owner.

Its content had also decayed. The single deferred item claimed the repository has no CI, that npm publish was blocked on interactive login, and that the registry served 3.0.0 against a 5.0.0 repo. All three are false: `.github/workflows/publish.yml` has existed since 2026-07-19, OIDC trusted publishing works, and npm serves 5.2.2. Only one gap survived, and it is now GitHub issue #10.

## What Changes

Retire the standing backlog and name GitHub issues as this repository's durable follow-up owner.

- Delete `openspec/changes/follow-up-backlog/`, including its never-synced spec delta.
- Record the follow-up ownership convention in `AGENTS.md`, outside the Keel managed block so `keel --install` cannot rewrite it.
- The one surviving deferred item is already rescued into GitHub issue #10 with its evidence refreshed and its three obsolete claims marked.

## Capabilities

### New Capabilities

- None. This is repository housekeeping and a documented convention, not a product capability. No spec delta accompanies this change, so it archives without a sync.

### Modified Capabilities

- None. `keel-expectation-slice-evidence-gates` already carries the durable-owner requirement and is unchanged.

## Impact

- `keel context` stops inferring a permanent false pointer; with no unarchived change it reports a non-ready status that invites explicit selection instead of naming work nobody intends to do.
- Deferred follow-ups gain a searchable, assignable, closable owner that is visible without cloning the repository.
- `keel/HANDOFF.md` stays pointer-only and `keel/archive/` stays historical evidence, unchanged by this change.

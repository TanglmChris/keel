# Contents of the retired follow-up-backlog, and what became of them

Date: 2026-07-27. Owner: commits `b56b51e..38d37ec`.

`openspec/changes/follow-up-backlog/` was deleted. This note is the historical record of what it held, so the deletion loses nothing.

The retirement was authored as the OpenSpec change `retire-follow-up-backlog`, with three gated tasks whose contracts and evidence are in the commits above. It was then demoted to plain housekeeping: `keel gate change-close --action archive` reports `missing-delta-spec` — "archive requires at least one change delta spec" — and this work honestly changed no capability. Rather than invent a spec delta to satisfy the gate, the change directory was removed. The gate's position is defensible: an OpenSpec change is the unit for capability deltas, and delta-free housekeeping does not need one. Recorded here because a reader finding these commits will otherwise look for a change directory that no longer exists.

## The single deferred item

The backlog held exactly one deferred item, written 2026-07-18. Three of its four claims had gone stale by 2026-07-27:

| Original claim | Status on 2026-07-27 |
| --- | --- |
| "the repository has no CI" | **False.** `.github/workflows/publish.yml` has existed since 2026-07-19. |
| "npm publish has been blocked on interactive `npm login` across three releases" | **False.** OIDC trusted publishing works; the workflow publishes on release. |
| "npm registry still serves 3.0.0 while the repo is at 5.0.0" | **False.** npm serves `@christang/keel@5.2.2`, matching the repo and the `v5.2.2` tag. |
| "all 50 validator scenarios run only in the local pre-push hook" | **Still true**, now 58 scenarios. This is the only surviving gap. |

The surviving gap — no test CI on pull requests, so the local pre-push hook is the sole regression net — is now GitHub issue https://github.com/TanglmChris/keel/issues/10. That issue carries the refreshed evidence, records the three obsolete claims above so nobody re-derives them, and notes that the validator is currently Windows/CLI-specific and unproven on a Linux runner.

## The intake rules it documented

The backlog's `tasks.md` documented rules for what belonged in it. Their surviving substance now lives in the Project Conventions section of `AGENTS.md`: follow-ups are owned by GitHub issues, each recording source evidence, rationale, and the consequence of not doing it; `keel/HANDOFF.md` stays pointer-only; `keel/archive/` holds historical evidence rather than active follow-ups.

## Its spec delta

`specs/follow-up-ownership/spec.md` declared a requirement that deferred follow-ups have a durable owner and that `keel/HANDOFF.md` must not be it. **It was never synced** — `openspec/specs/` contains seventeen `keel-*` capabilities and no `follow-up-ownership`. Its substance was already carried by the synced `keel-expectation-slice-evidence-gates`, which requires behavior evidence, a durable follow-up owner, or an explicit discard reason, and requires unresolved follow-ups to live outside `keel/HANDOFF.md`. Nothing was lost by deleting it.

## Why the directory was retired rather than reshaped

It carried a proposal and a spec delta but zero task checkboxes. That is not the storage-only shape `keel-stateless-continuity / Storage-only standing backlog does not create ambiguity` excludes from inference, so `keel context` inferred it as actionable authoring work on every session start:

```
"selection": { "source": "inferred", "change": "follow-up-backlog", "task": null },
"nextAction": { "kind": "author" }
```

Keel was following its spec; the directory was mis-shaped for its purpose. Stripping it to storage-only would also have removed the false pointer but would have left two competing owners for one concern.

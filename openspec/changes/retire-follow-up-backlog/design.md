## Verified facts

- F1 — Verified fact: `openspec/specs/` contains seventeen `keel-*` capability directories and no `follow-up-ownership`. The backlog's spec delta at `openspec/changes/follow-up-backlog/specs/follow-up-ownership/spec.md` was never synced. Basis: directory listing.
- F2 — Verified fact: `keel context --json` returns `status: ready` with `selection.source: inferred`, `selection.change: follow-up-backlog`, `selection.task: null`, and `nextAction.kind: author`. Both the globally installed CLI and `node bin/keel.js` agree. Basis: both commands run in this repository.
- F3 — Verified fact: the backlog's `tasks.md` contains zero task checkboxes (`grep -c "^\s*-\s*\[" ` returns 0) while `proposal.md` and `specs/` are present. Basis: direct count.
- F4 — Verified fact: `.github/workflows/publish.yml` exists and triggers only on `release: [published]`, and npm serves `@christang/keel@5.2.2`. The backlog's deferred item claimed no CI, a login-blocked publish, and a 3.0.0 registry against a 5.0.0 repo. Basis: file contents and `npm view`.
- F5 — Verified fact, discovered during task 1.2: `keel gate task-complete` rejects a bare GitHub issue URL as a Review Findings owner. `findingOwnerIsDurable` (`src/core/gates.js:417`) accepts only a `Discard reason:`/`Discard rationale:` prefix, a `keel/archive/…` path, or an existing `openspec/changes/…` artifact. Basis: the gate returned `finding-owner` for a Findings line whose owner was an issue URL, and passed once the owner became a `keel/archive/…` path.

## Decisions

- D1 — GitHub issues are this repository's durable follow-up owner. `keel-expectation-slice-evidence-gates / Completion Gate closes expectation evidence / Completed work has evidence closure` requires a durable owner but never requires that owner to be an OpenSpec change. The only owners the specs exclude are `keel/HANDOFF.md` and native runtime state — memory, goals, todos, transcripts, checkpoints (`keel-stateless-continuity / Keel continuity is stateless / Native runtime state is not continuity authority`). An issue tracker is durable, external to any session, and excluded by neither. Basis: F1 plus both cited scenarios.

- D2 — Retire rather than reshape. Stripping the proposal and spec delta would turn the directory into the storage-only shape the continuity spec excludes from inference, which also removes the false pointer. It is rejected because it leaves two competing owners for one concern and keeps a directory whose only content is a pointer to issues. One owner is the point. Basis: F3 and D1.

- D3 — The convention is recorded in `AGENTS.md` below `<!-- keel:end -->`, not inside the managed block and not in a spec. `keel --install` rewrites the managed block from `assets/bootstrap/AGENTS.md` and would discard anything placed inside it (see issue #9). A spec is also wrong: this is a convention of the keel repository, not behavior Keel ships to consumers, and a product spec would leak it to every consuming project. Basis: the block markers at `AGENTS.md:3` and `AGENTS.md:81`, and the overwrite reproduced while installing the Claude target.

- D5 — The `AGENTS.md` convention must also state the gate's accepted owner forms, discovered after D1 was written. D1 remains correct as a statement of intent and is spec-legal, but a bare issue URL does not pass `finding-owner` (F5), so an agent following the convention as first written would be blocked at `task-complete` with a diagnostic that never mentions issues. The operational rule is therefore: issues own the substance, and a `keel/archive/…` note is the gate-recognized pointer to the issue. The spec-versus-implementation mismatch itself is not fixed here — it is product behavior, out of scope for a housekeeping change — and is owned by issue #12. Basis: F5 and the reproduction recorded in `keel/archive/follow-ups/2026-07-27-guard-json-gitignore.md`.

- D4 — This change carries no spec delta and archives without a sync. Nothing in `openspec/specs/` changes: the requirement being honored is already synced, and the delta being deleted was never synced. Basis: F1 and D1.

## Risks

- A1 — Assumption: `keel gate change-close --action archive` accepts a change with no `specs/` directory. Basis: the change alters no capability, so there is nothing to sync. Resolve by: running the gate and, if it demands a delta, reporting the gate output rather than inventing a spec change to satisfy it.
- A2 — Risk: deleting the directory loses the intake rules its `tasks.md` documented (actionable, project-related, includes evidence and rationale and consequence). Mitigation: D3's `AGENTS.md` entry carries the surviving substance — issues own follow-ups, record evidence and rationale and consequence, and do not create a standing change as a store.

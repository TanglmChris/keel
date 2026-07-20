## Context

Keel's completion and close gates hard-validate three forms — the Review `Status`
vocabulary, the Findings ownership shape, and the `## Expectation Coverage`
section — but those required and accepted forms live only in the validators
(`src/core/gates.js`, `src/core/context.js`), never in the author-facing surface:
the `keel-spec-driven` tasks template and the `tasks` artifact instruction in
`schema.yaml`. GitHub issue #1 Cases B, C, and D. See proposal.md.

## Goals / Non-goals

- Goals: align each hard-validated form with the surface an author reads;
  single-source the accepted `Status` vocabulary; make the three rejection errors
  self-describing.
- Non-goals: issue #1 Case A and issues #2/#3 (sibling change
  `install-runtime-honesty`); redesigning the gate model or the task-capsule
  format beyond surfacing the accepted forms.

## Decisions

- **D1 — Accept `done` into the Review `Status` set.** Basis: aligns with
  OpenSpec's own `done` vocabulary and is the lowest-friction token an author
  reaches for; the proposal's chosen resolution for Case B.
- **D2 — Single-source the accepted `Status` vocabulary.** The token set
  duplicated verbatim at `gates.js:379` and `context.js:72` becomes one shared
  constant both consume, so the gate check and the context "already reviewed"
  probe can never diverge. Basis: the duplication is the internal-consistency
  defect called out in the proposal.
- **D3 — The author surface carries the accepted forms.** The accepted Status
  tokens, the Findings forms, and the `## Expectation Coverage` section are
  written into the `keel-spec-driven` tasks template and the `tasks` artifact
  instruction; both the `openspec/` and `assets/openspec/` copies stay aligned.
  Basis: an author who follows the shipped template must not hit an avoidable
  hard-stop.
- **D4 — Rejection errors carry the accepted forms or a format sample.** The
  `semantic-review` (Status), `finding-owner` (Findings), and
  `expectation-coverage` (change-close) errors name the failing field/section and
  show the accepted tokens or a minimal format sample. Basis: the failure must be
  diagnosable from the message, not from reading validator source.

## Facts

- **F1** — Accepted Findings ownership forms (`findingOwnerIsDurable`,
  `gates.js:216`): `none`; a `discard reason:`/`discard rationale:` prefix
  (optionally `explicit`); a `keel/archive/…` path; or an existing
  `openspec/changes/<change>/(proposal|design|tasks).md` path. HANDOFF is
  rejected.
- **F2** — Archive requires both `proposal.md` and `design.md` (`gates.js:572`);
  change-close requires at least one delta spec (`gates.js:564`).

## Risks

- The two `tasks.md` template copies and two `schema.yaml` copies must stay
  aligned (`validate_plugin.py` already enforces byte-identity for schema
  assets); each task touches both copies together.
- The shared `Status` constant must be importable by both `gates.js` and
  `context.js` without a circular dependency; place it where neither module gains
  a back-edge.

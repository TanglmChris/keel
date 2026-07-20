## Context

The shipped tasks template's Contract anchor (`- Contract: pending task-start
capsule and fingerprint`) does not match the `--record` matcher, which requires
the literal `- Contract: pending`. See proposal.md.

## Decisions

- **D1 — Align the template to the spec's bare anchor, not the matcher.** The
  `keel-core-gates` spec already mandates the literal `- Contract: pending` for
  `--record`; the template was the deviation, so it is brought into compliance
  rather than broadening the matcher. Basis: the spec is the authority.

## Facts

- **F1** — The `--record` matcher at `src/core/gates.js` is
  `^(\s*)-\s*Contract:\s*pending(\r?)$` (anchor must end at `pending`); the
  validator needle previously required the long descriptive form, so the two
  contradicted and `--record` always refused a fresh scaffold.

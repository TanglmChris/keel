## Why

Two refusals added with the 5.3.x gates stop honest work and do not say what would be accepted.

`Durable owner:` accepts `openspec/changes/…`, `keel/archive/…`, or an `https://` URL, and the diagnostic says only "lacks a durable owner". An author pointing at their repo's own ledger — `openspec/FOLLOWUP.md` in [#20](https://github.com/TanglmChris/keel/issues/20) — is told the entry has no owner when it plainly names one, and can only find the boundary by trial.

A red-green strategy demands `.red` and `.green` Evidence for **every** `M<n>`, but a regression check asserts that something already green stays green and has no honest red. The author's two options are to fabricate a red or to fold the regression assertion into the behavior check ([#21](https://github.com/TanglmChris/keel/issues/21)). This repository chose the fold twice while implementing 5.3.2 and 5.3.3, and recorded both times that it cost expressiveness — the gate's shape decided the task's decomposition.

## What Changes

- A `Durable owner:` may name **any repo-relative path that exists**, alongside the existing forms. `keel/HANDOFF.md` stays refused. The shared owner check gains real verification it never had: the current whitelist confirms nothing, since a gate cannot resolve a URL or an archive path, while a repo path can be stat'd on the spot.
- Every refusal of an owner or a closure names the forms it accepts.
- An `M<n>` check may carry a `(regression)` tag, which exempts that check from `.red`/`.green` while still requiring concrete Evidence. A red-green strategy MUST keep at least one untagged check, so the strategy cannot be emptied out by tagging everything.
- The tasks template states both: the accepted owner forms, and that `.red`/`.green` are recorded **in addition to** the bare label rather than replacing it — a second wording trap [#21](https://github.com/TanglmChris/keel/issues/21) reports.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `keel-expectation-slice-evidence-gates`: the durable-owner vocabulary admits any existing repo path, and every closure refusal states the accepted forms.
- `keel-task-capsule`: an `M<n>` check may declare itself a regression check, and a red-green strategy requires at least one check that is not one.

## Impact

- `src/core/gates.js` — the shared owner form, the three closure refusals, and the red-green completion check.
- `src/core/task-contract.js` — the `M<n>` label parser and the capsule's verification shape.
- `scripts/validate_plugin.py` — scenarios for both.
- The tasks template and schema instruction, in both the repo-local and packaged copies.
- `AGENTS.md` — two resident statements describing the old boundaries.
- **Fingerprint:** the `(regression)` tag follows the `(fast)`/`(full)` precedent and is emitted only when present, so untagged checks compile to a byte-identical capsule and no existing task's fingerprint moves. Verified during implementation, not assumed.
- No consumer migration: both changes widen what is accepted, so every currently passing tasks.md keeps passing.

## Why

Issue #389 (2026-10-19): with stronger models, is Keel's red-then-green still worth it? Keel already has seven Verify strategies and no rule that every task goes red first, but `keel-tdd-or-test-first` lists the strategies without saying how to pick one, and it does not mention `Detects:` or `Measured:` at all — they are reachable only through `AGENTS.md` and the README. A reader can come away thinking every task goes red first, or that a complete Evidence shape means the testing was enough.

Measured over the archive (561 tasks in 213 changes, July–October 2026), the strategies people reach for are `vertical-tdd` (279) and `evidence-first` (231, 188 of them release tasks). `equivalence` was never chosen, `Detects:` was declared on 10 tasks and `Measured:` on 3. The forms built for the issue's concerns are barely found.

## What Changes

- `keel-tdd-or-test-first` gains a `guidance.md`: a table that picks the strategy by what would make the Acceptance false, worked right and wrong choices, when a red adds information and when it does not, when `Detects:`, `Measured:`, `(regression)` with `deferred to C<n>`, and `artifact` pay for themselves, and an abstract hardware example.
- The skill body states the selection criterion — what would make the Acceptance false, not the task's size, apparent risk, or the model running it — and the `Detects:` and `Measured:` contracts beside the `Fails with:` and `artifact` ones it already has.
- A validator scenario keeps the skill naming every strategy the parser accepts and every evidence clause the gate enforces.
- No gate, CLI, configuration key, or strategy changes; no "strong model" switch.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-verification-layering`: Keel documents how to choose a Verify strategy and where each evidence form is found.

## Impact

`src/skills/keel-tdd-or-test-first/`, its plugin copy, `scripts/validate_plugin.py`, `README.md`, the published spec, the changelog.

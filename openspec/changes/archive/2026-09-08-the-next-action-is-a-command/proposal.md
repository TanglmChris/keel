## Why

Issue #112's fifth group is three small things that share one shape: Keel knows the invocation that works and prints something else, or nothing.

**`keel context` names an action and not the command.** `Next action: change-close` is the whole answer, and `keel gate change-close --change x` then fails with `change-close requires --action sync or --action archive`. The error is good; it arrives after a wrong attempt that Keel had everything it needed to prevent. The usage line shows `[--action sync|archive]` in brackets on a line shared by all three stages, so the one stage that requires it is documented as optional.

**The installed OpenSpec surfaces tell an agent to run a command that is not there.** `keel --init` writes `.claude/commands/opsx/*.md` and `.claude/skills/openspec-*/SKILL.md`, whose text is OpenSpec's and says `openspec new change "<name>"`. With only `@christang/keel` installed globally, a bare `openspec` is not on PATH — `keel --doctor` reports exactly this and names `keel openspec` as the working invocation. The reporter had to record the workaround in their own project documentation, per project.

Those files belong to OpenSpec and Keel appends an overlay to them rather than editing their body — a boundary this change keeps. What it does is make Keel's own block, in those same files, say which invocation works.

## What Changes

- `keel context` reports the command for its next action, not only the action's name. `Next action: change-close` is followed by the invocation that runs it, `--action` included. The `--json` result carries the same string.
- Every Keel OpenSpec surface overlay states that the CLI is invoked as `keel openspec …` in a repository where a bare `openspec` may not resolve, and points at `keel --doctor` for the check that says which case this is.
- `keel --help` marks `--action` as required for `change-close` rather than showing it as optional for all three stages.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-stateless-continuity`: the next action is reported as a command.
- `keel-openspec-surface-overlay`: the overlay states the invocation that resolves.

## Impact

- `src/core/context.js` — the next-action command.
- `bin/keel.js` — the overlay text and the usage line.
- `scripts/validate_plugin.py` — one new scenario.
- **Not changed**: `keel openspec validate --change X` still fails while `status --change X` works, which the report also asks about. That is OpenSpec's own CLI surface, reached through a proxy that passes arguments unaltered. Translating flags inside the proxy would make `keel openspec` a second CLI that behaves differently from the tool it proxies, and the divergence would be worse than the inconsistency. Recorded as a discard with its reason rather than left unanswered.

## Why

Issue #413, first of three changes. Three read-only audits on 2026-10-20 compared Keel's model-facing surfaces with each other and with the code. They found two kinds of problem.

First, what #414 missed: the compiled capsule, which every `task-start`, `keel project`, and `keel agents brief` prints, still says "must not continue to another task", "must not mark tasks complete", and "must not transfer Keel ownership", and still defaults the owner to `keel-agent`. That is the opposite of 5.172.0's default continuation and "a subagent is treated as the main agent is". The owner chose to remove them (2026-10-20), relying on the gates to recognize the resulting one-time fingerprint drift.

Second, places where the surfaces contradict each other or the code:
- The schema still asks coupled tasks for "retry counting" and claims a "Claude Keel Hook completion gate" that does not exist.
- The schema and the tasks template omit the `equivalence` strategy and the `Resolved here:` disposition.
- `AGENTS.md` says diagnose-only may write when Touch authorizes it, while the code requires `Touch: none`.
- The protocol and the overlays still call `Verify` checks "Commands".
- Three surfaces require "explicit authorization" for commit/push and ignore `keel/config.yaml`.
- The standing-authorization spec lists 10 of the 13 names the code accepts.
- The lens spec still limits reading to one lens, which the skills stopped saying in 5.172.0.
- `keel chat help` omits the `post-tool-use` hook, and the apply, archive, and sync overlays tell the agent to use `keel openspec` twice.
- `keel --help` omits `keel patrol` and `keel tick`.
- A config comment says `self-shift` turns Remote Control off, which it no longer does (#324).

## What Changes

- **Capsule**: `prohibitions` drops the three sentences, and `owner` is present only when a task authors one. A task recorded before this release drifts once. The `#342` diagnosis names it a compiler change and tells the author to re-record with `--record`, with the evidence kept.
- **Surfaces made consistent with each other and the code**:
  - the schema and its installed copy;
  - the tasks template and its installed copy;
  - `AGENTS.md` and the bootstrap;
  - the overlay text in `bin/keel.js` and the regenerated surfaces;
  - the `keel-debug-failure` skill;
  - `keel --help`;
  - the `config.js` comment.
- **Specs**: `keel-task-capsule`, `keel-standing-authorization` (all 13 names), and `keel-domain-lenses` (no single-lens limit).

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-task-capsule`, `keel-standing-authorization`, `keel-domain-lenses`.

## Impact

`src/core/task-contract.js`, `src/core/config.js`, `bin/keel.js`, the schema and template (two copies each), `AGENTS.md`, `assets/bootstrap/AGENTS.md`, the regenerated `.claude/` and `.codex/` surfaces, `keel-debug-failure`, `scripts/validate_plugin.py`, the published specs, and the changelog. README and docs are the next change of #413.

## Context

After `keel --init`, several surfaces claim or imply something the runtime does
not deliver, and one lifecycle gap leaves a dangling guard. GitHub issue #1 Case
A, issue #2 (and its guard addendum), and issue #3. See proposal.md. Two of the
立项 directions conflicted with current spec authority and were re-resolved during
authoring (D4, D5 below).

## Goals / Non-goals

- Goals: make the install/openspec/lifecycle surfaces honest and complete without
  contradicting the v4 thin-CLI or write-guard specs.
- Non-goals: reversing plugin-based skill delivery; patching `@fission-ai/openspec`
  internals; issue #1 Cases B/C/D (sibling change `align-gate-authoring-surface`).

## Decisions

- **D1 — openspec invocation (Q1).** Add a `keel openspec …` passthrough that
  forwards to Keel's resolved openspec, and point the overlays at it instead of a
  bare `openspec` that may be off PATH. Basis: the proposal's Q1; avoids PATH
  surgery.
- **D2 — archive idempotency (Q2).** The archive overlay sequences `/opsx:sync`
  then directs archive to pass `--skip-specs`, so an already-promoted delta is not
  re-applied. Root idempotency stays upstream in `@fission-ai/openspec`. Basis:
  the proposal's Q2.
- **D3 — doctor openspec honesty (issue #2).** Doctor downgrades the openspec line
  from `ok` to a warning when the resolved openspec is not reachable as a bare
  `openspec` on PATH, naming the working invocation. Basis: `findOpenSpecCommand()`
  resolves the internal shim (`bin/keel.js:1262`), so `ok` currently overstates.
- **D4 — Case A is honesty, not a CLI install (re-resolved).** keel-* skills are
  plugin-delivered by design; the thin-CLI spec forbids the CLI creating
  `.claude/skills/keel-*`. So remove the dead `skill_actions` keel-* path, correct
  the false `keel --help` text, and make doctor report the keel-* inventory as a
  plugin surface with remediation. Basis: the 立项 "CLI 应该装" direction conflicted
  with `keel-openspec-surface-overlay` "Thin CLI ... MUST NOT copy .claude/skills/keel-*";
  the user's goal is a verifiably complete `keel --init`, which honesty serves
  without double-delivering to Claude.
- **D5 — guard clear is an overlay reminder, not a gate write (Q3 re-resolved).**
  The archive overlay reminds the agent to run `keel guard clear` after archiving;
  the gate stays read-only. Basis: the 立项 "gate 自动清" direction conflicted with
  `keel-touch-write-guard` ("read-only gates never delete the manifest") and
  `keel-core-gates` write-bounding; the user chose to preserve those invariants.

## Facts

- **F1** — The six keel-* skills ship in `plugins/keel/skills/` and are delivered
  via `package.json` `files: ["plugins/"]`; the Codex plugin manifest declares
  `"skills": "./skills/"`. Plugin delivery already works; the CLI copy is dead.
- **F2** — `install_to_repo.py:skill_actions` (~236) sources keel-* from
  `dist_asset(target,"skills")` = retired `dist/`; `skills_root.is_dir()` is always
  false, so it installs nothing. `keel --help` (bin/keel.js:104-106) nonetheless
  claims CLI install.
- **F3** — `keel --doctor` reports `openspec: ok` whenever `findOpenSpecCommand()`
  resolves the internal shim (`bin/keel.js:1262-1267`), regardless of PATH.
- **F4** — The archive overlay body lives in `bin/keel.js` `keelOpenSpecOverlay`
  (~1021-1027); it references `/opsx:sync`, `/opsx:archive`, and
  `openspec-sync-specs` but no `--skip-specs` or guard-clear reminder.

## Risks

- The archive delta idempotency itself is upstream in `@fission-ai/openspec`; keel
  guides around it (D2) rather than patching upstream.
- Doctor PATH-reachability probing must not mutate PATH or runtime config
  (`keel-target-surface-diagnostics` "Probe does not mutate runtime configuration").

<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Omitted fields inherit versioned defaults: Owner is the current Keel agent,
     Mode is implementation, Read is this change's proposal/design/specs/tasks
     plus discovered repository context, Acceptance derives from Covers, autonomy
     defaults to hard-stop, and commit/push/sync/archive stay unauthorized. -->

## 1. Honest skill delivery (issue #1 Case A)

- [ ] 1.1 Remove the dead CLI keel-* install path and make help + doctor honest
  - Covers:
    - keel-skill-sourcing-and-portability / keel-* skills are plugin-delivered, not CLI-installed
    - keel-target-surface-diagnostics / Doctor reports keel-* skills as a plugin surface
  - Touch:
    - scripts/install_to_repo.py
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: evidence-first
    - M1: `keel --init` on a temp repo creates no `keel-*` skill files under any target skill root, and `install_to_repo.py` no longer sources keel-* skills from `dist/` (the dead `skill_actions` keel-* path is removed)
    - M2: `keel --help` states the keel-* skills are delivered by the Keel plugin and no longer claims the CLI installs them under a target skill root
    - M3: `keel --doctor` reports the keel-* inventory as a plugin surface with remediation when the plugin is absent, and `npm test` passes with validator assertions for the above
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - M3: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 2. openspec invocable (issue #2)

- [ ] 2.1 Add a `keel openspec` passthrough and direct overlays to it
  - Covers:
    - keel-openspec-surface-overlay / Keel makes openspec invocable for skill-driven agents
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: rendered-behavior
    - M1: `keel openspec` forwards its arguments to the resolved openspec (for example `keel openspec --version` prints the openspec version) and works when bare `openspec` is not on PATH
    - M2: the apply and archive overlays direct agents to `keel openspec` in place of a bare `openspec`
    - M3: `npm test` passes with a scenario covering the passthrough and the overlay direction
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - M3: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 3. Doctor openspec honesty (issue #2)

- [ ] 3.1 Downgrade doctor `openspec: ok` to a warning when bare openspec is off PATH
  - Covers:
    - keel-target-surface-diagnostics / Doctor distinguishes keel-resolvable openspec from PATH-reachable
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: when Keel resolves its internal openspec shim but bare `openspec` is not on PATH, `keel --doctor` reports the openspec line as a warning naming `keel openspec`, not `ok`; before the change it reported `ok`
    - M2: when bare `openspec` is reachable on PATH, doctor still reports `ok`
    - M3: `npm test` passes with a scenario covering both PATH states
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - M3: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 4. Archive idempotency + guard hygiene (issue #3 + Q3)

- [ ] 4.1 Sequence sync then archive `--skip-specs` and remind to clear the guard
  - Covers:
    - keel-openspec-surface-overlay / Archive overlay skips already-promoted specs and reminds to clear the guard
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: evidence-first
    - M1: the archive overlay text sequences `/opsx:sync` then archive with `--skip-specs`, and reminds the agent to run `keel guard clear` after archiving
    - M2: no guard deletion is added to any gate — the gate stays read-only
    - M3: `npm test` passes with validator assertions for the archive-overlay `--skip-specs` sequence and the guard-clear reminder
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - M3: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Expectation Coverage

- E1: Case A honesty — the CLI creates no keel-* files, help states plugin delivery, and doctor reports the plugin skill surface with remediation. Covered by: 1.1
- E2: openspec invocable — a keel openspec passthrough plus overlay direction to it. Covered by: 2.1
- E3: doctor openspec honesty — ok is downgraded to a warning when bare openspec is off PATH. Covered by: 3.1
- E4: archive idempotency and guard hygiene — the archive overlay sequences sync then skip-specs and reminds to clear the guard. Covered by: 4.1

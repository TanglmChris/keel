## 1. Restore bundled DSH discovery

- [x] 1.1 Resolve bundled DSH consistently for discovery and briefs
  - Covers:
    - D1
    - D2
    - keel-external-agents / The bundled DSH entry discovers local installations
  - Touch:
    - src/core/agents.js
    - scripts/validation/guard.py
  - Verify:
    - Strategy: regression-first
    - M1: Run the external-agent-catalog and external-agent-brief public CLI scenarios. Exercise Linux PATH discovery, the executable macOS bundle at the filesystem boundary, PATH fallback, genuinely missing paths, explicit machine overrides, and agreement between catalog and allowed helper brief. Check that neither query launches DSH and an unallowed project remains disallowed. Fails with: `DSH did not resolve from fixture PATH`
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:30991cf7e49bc6ad2f65a82e11e8af3739ae13c87c0627bbeb8d07cec64f5fbc (keel 5.231.7)
    - M1: Both public CLI scenarios and the exit-status regression passed. The real local Linux catalog found DSH 0.2.2-rc.1 on PATH and separately reported that the project does not allow it.
    - M1.red: external-agent-catalog and external-agent-brief failed with `DSH did not resolve from fixture PATH`; the catalog printed the missing macOS bundle.
    - M1.green: `python3 scripts/validate_plugin.py --scenario external-agent-catalog --scenario external-agent-brief --scenario external-agent-exit-status` passed all 3. macOS bundle handling stands in only for platform and bundle filesystem lookup.
    - Review:
      - Status: pass
      - Acceptance check: Both catalog and allowed brief use the real Keel CLI. Access checks still refuse the existing denied cases, and fixture call logs prove no process launch.
      - Scope check: Two Touch files and the change artifacts. No settings, credentials, provider requests, or authorization changed.
      - Findings: Resolved here: M1 proves Linux resolution and compatibility with machine overrides and macOS bundle discovery.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "the catalog keeps the bundle path, which works with or without it" — dated DSH catalog entry in `src/core/agents.js`. Updated by: 1.1

## Expectation Coverage

- E1: Resolve DSH for both supported installation paths without changing allowance (D1, D2). Covered by: 1.1

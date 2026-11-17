# Tasks

- [x] 1.1 Repair the compatible locked Zod dependency
  - Covers:
    - D1
    - D2
    - keel-release-artifact / Locked validation dependency excludes the affected Zod release
  - Touch:
    - npm-shrinkwrap.json
  - Verify:
    - Strategy: regression-first
    - M1: `npm audit --json` reports no GHSA-mrhx-c7xc-m3w5 after installation; the same command first reports the existing high-severity Zod advisory. Inspect the lock diff to confirm only Zod changed and OpenSpec remains 1.14.0.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` validates the existing public OpenSpec requirements with the newly installed dependency.
    - M3 (regression): the complete `npm test` is deferred to C1 after both authorized fixes are implemented.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:55833b81a58f61307fb28f08552a56332a0f57075da30e966a8cb4d14841ca80 (keel 5.229.0)
    - M1: pass: installed Zod 4.6.7; npm audit reports zero vulnerabilities. Diff comparison shows only node_modules/zod changed; OpenSpec remains 1.14.0 and its declared range is unchanged.
    - M1.red: fail before update: npm audit reports one high-severity Zod finding, GHSA-mrhx-c7xc-m3w5, locked 4.4.3.
    - M1.green: pass after npm ci --ignore-scripts: all audit severities zero; installed lock resolves 4.6.7.
    - M2: pass: 37 published specs validate strictly through installed OpenSpec 1.14.0 with repaired dependency.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: actual audit and clean installation remove the advisory, public OpenSpec strict checks preserve compatibility, and final full regression is explicitly deferred to C1.
      - Scope check: only npm-shrinkwrap.json product bytes changed, limited to Zod version, tarball URL and integrity. Own proposal/spec/tasks/evidence use the record layer.
      - Findings: Resolved here: M1 — affected locked dependency replaced inside the existing range. Durable owner: https://github.com/TanglmChris/keel/issues/531 — separate lifecycle repair precedes the shared patch release.
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: evidence-first
- C1: `npm test` passes baseline and all registered scenarios on the final patch candidate, including compatibility checks with the patched installed dependency.

## Change Evidence

- C1: pending

## Invalidates

- I1: "The package continues to install an affected Zod version" — open issue #528; close with published patch and install evidence. Durable owner: https://github.com/TanglmChris/keel/issues/528

## Expectation Coverage

- E1: Patched dependency with a bounded graph change and observable validation compatibility (D1, D2). Covered by: 1.1
- E2: Published/local deployment and #531 lifecycle fix remain separately owned. Durable owner: https://github.com/TanglmChris/keel/issues/531

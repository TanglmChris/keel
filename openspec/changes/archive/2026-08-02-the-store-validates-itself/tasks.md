## 1. Read the store the consumers read

- [x] 1.1 Assert the published spec store against the validator Keel ships
  - Covers:
    - keel-validation-runner / The published spec store is validated by the tool Keel ships / A published spec that fails strict validation fails the suite
    - keel-validation-runner / The published spec store is validated by the tool Keel ships / The store is asserted rather than a change
    - keel-validation-runner / The published spec store is validated by the tool Keel ships / The validator that answered is named
    - keel-validation-runner / The published spec store is validated by the tool Keel ships / No validator resolves
    - D1 — the assertion is absolute
    - D2 — no ratchet, because the store is at zero
    - D3 — the validator version is stated and an absent validator is a skip
    - F1 — no scenario reads the store today
    - F2 — the store currently passes, which is what makes an absolute assertion available
    - A1 — the scenario reads both the exit status and the per-spec lines
  - Touch:
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes, reporting the validator version it exercised and the per-spec totals. Its red is proved by introducing a requirement whose modal verb sits below its first paragraph — the exact shape of the 8 failures #46 recorded — and confirming the scenario fails naming that spec, then removing it.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario validation-runner` still passes, so the registry and runner contract are unchanged.
    - M3 (regression): `npm test` passes, so adding a check that reads the whole store does not disturb the scenarios that write into temporary repositories.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:bc0c9d973172d4b96646d4eb69f058fb5a5c46adac828ab5807a59c16204a249
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` reports `published-specs-validate-strictly scenario passed: 21 published specs validate strictly against openspec 1.6.0.` — the count and the validator version both stated, so the result is attributable.
    - M1.red: fail, as required, against a real failing store rather than a contrived one. Pointing the scenario's resolution at the `openspec` on PATH — 1.4.1 here — makes it report `8 published spec(s) fail strict validation against openspec 1.4.1`, followed by all eight `✗ spec/…` lines, and name the usual cause. That is the defect #46 describes, reproduced through this scenario's own failure branch. Restoring the pinned resolution returns it to green. The branch is therefore live and its message names what actually happened.
    - M1.green: pass. With `node_modules/.bin/openspec` resolved, the same command reports 21 passed and 0 failed. The two readings the scenario takes — the per-spec `✗` lines and the `Totals:` line — agree, and the exit status agrees with both; the scenario refuses the result if any of the three disagree rather than trusting whichever is convenient.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario validation-runner` reports `validation-runner scenario passed.` The registry and runner contract are unchanged.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 126 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: the check runs the validator Keel ships over the store Keel publishes, which is the behavior the requirement names, and it asserts the outcome from three independent readings rather than one. The red half was proved with a genuinely failing store — the same eight specs #46 lists — rather than by a synthetic fixture, so the failure branch is known to fire on the real defect.
      - Scope check: `git status --short` lists exactly `scripts/validate_plugin.py`, the single Touch entry, plus this change's own untracked directory. The completion gate's own attribution — added in 5.16.0 and recorded in this task's manifest — reported no out-of-Touch path.
      - Findings: two. First, and it changes what issue #46 says: **the 8 failures #46 records as an `openspec 1.6.0` result are 1.4.1's output.** Bare `openspec` on PATH here is 1.4.1 and reports `13 passed, 8 failed`; `node_modules/.bin/openspec` is 1.6.0 and reports `21 passed, 0 failed`, and the eight names in #46 match 1.4.1's list exactly. The store has always passed under the version this repository pins. This change's first draft reproduced the 8 failures and briefly recorded them as current, because the suite's shared `run_openspec` helper resolves through `shutil.which("openspec")` — so every scenario using it reads PATH rather than the pinned dependency. This scenario now resolves the pinned binary directly and skips rather than falling back. Repairing the shared helper is real work for the scenarios that share it and is deliberately not bundled here. Durable owner: https://github.com/TanglmChris/keel/issues/46. Second: rewriting the text of `D2` and `F2` in `design.md` mid-task did not move the compiled fingerprint — `task-start --record` returned `sha256:bc0c9d97…` both before and after. A task's `Covers` can name a decision and that decision's wording can change under an anchored contract without the drift check noticing, which is a narrower version of what the anchor is for. Durable owner: https://github.com/TanglmChris/keel/issues/51
    - Blocker: none

## 2. Close

- [x] 2.1 Release 5.17.0
  - Covers:
    - E4 — a reader of the release notes learns that a spec written in the house style now fails the suite
    - I1, I2 — the wordings this change makes stale
  - Touch:
    - package.json
    - package-lock.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - scripts/validate_plugin.py
    - .claude/commands/opsx/apply.md
    - .claude/commands/opsx/archive.md
    - .claude/commands/opsx/propose.md
    - .claude/commands/opsx/sync.md
    - .claude/skills/openspec-apply-change/SKILL.md
    - .claude/skills/openspec-archive-change/SKILL.md
    - .claude/skills/openspec-propose/SKILL.md
    - .claude/skills/openspec-sync-specs/SKILL.md
    - .codex/skills/openspec-apply-change/SKILL.md
    - .codex/skills/openspec-archive-change/SKILL.md
    - .codex/skills/openspec-propose/SKILL.md
    - .codex/skills/openspec-sync-specs/SKILL.md
    - openspec/specs/keel-validation-runner/spec.md
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names 5.17.0
    - M2: `keel/CHANGELOG.md` carries a 5.17.0 entry stating that the published store is now asserted, that the assertion is absolute rather than the ratchet #46 proposed and why the count changing to zero inverted that advice, and what a spec author has to do differently
    - M3: the spec delta is promoted into `openspec/specs/`, `node bin/keel.js openspec validate the-store-validates-itself --strict` passes, and the new `published-specs-validate-strictly` scenario passes against the promoted store — so the requirement this change adds is satisfied by the store that now contains it
    - M4: `npm test` passes with no failing scenario and no exception
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:e0d9864999deb5514807726c0734e85d3e149bc58fdc8eb1069967eec42ef1d9
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` 20 markers moved from 5.16.0 to 5.17.0 across the package and lockfile, both plugin manifests, the three `keel:start` managed blocks, the twelve overlay markers, the AGENTS.md title and preflight line, and the validator constants.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.17.0 - the store validates itself`, and its load-bearing bullet is the correction rather than the feature: the 8 failures #46 records as a 1.6.0 result are 1.4.1's, the store has always passed under the pinned version, and the suite's shared helper has been reading PATH all along. It states what a spec author must do differently — modal verb in the first paragraph — and names the shared-helper repair as deliberately not bundled.
    - M3: pass. The delta is promoted into `openspec/specs/keel-validation-runner/spec.md`, `node bin/keel.js openspec validate the-store-validates-itself --strict` reports the change valid, and `published-specs-validate-strictly` passes against the promoted store — `21 published specs validate strictly against openspec 1.6.0`. The requirement this change adds is satisfied by the store that now contains it, including by its own text.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 126 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: M3 is the one that matters and it is self-applying — the new requirement was promoted into the store, and then the new check was run over that store and passed, so the requirement's own wording satisfies the rule it states. A requirement about modal-verb placement that itself failed modal-verb placement would have been the same defect it describes.
      - Scope check: `git status --short` lists only 2.1 Touch entries plus this change's own directory, and the completion gate's attribution — recorded in this task's manifest at task start — reported no out-of-Touch path. This is the second task bound by the 5.16.0 check.
      - Findings: none
    - Blocker: none

## Invalidates

- I1: "第 2 条更符合本仓已有立场:一次改 8 个 spec 是一次大而无验证的改写,而棘轮能让它只减不增。" — the closing recommendation of https://github.com/TanglmChris/keel/issues/46. It was correct at a failure count of 8 and inverts at 0, where a recorded tolerance becomes a budget rather than a ceiling. Discard reason: an issue body records what was true when it was written, and the reasoning is what makes the reversal legible. The live correction is the 5.17.0 changelog entry and design D2, and the issue is closed by this change's pull request.
- I2: "version=5.16.0" — grep it and you find the `keel:start` managed block in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, plus the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`; the same version is written as `"version": "5.16.0"` in `package.json`, `package-lock.json`, and both plugin manifests, in the AGENTS.md title and its preflight line, and in the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants of `scripts/validate_plugin.py`. Updated by: 2.1

## Expectation Coverage

- E1: The published spec store is read by the validator Keel ships, inside the suite that runs on every change. Covered by: 1.1
- E2: A failing spec is named, so the next action is fixing it rather than reproducing the failure by hand. Covered by: 1.1
- E3: No tolerated failure count is recorded, so a new failure cannot hide inside a budget. Covered by: 1.1
- E4: A reader of the release notes learns that a spec written background-first now fails, and what to change. Covered by: 2.1

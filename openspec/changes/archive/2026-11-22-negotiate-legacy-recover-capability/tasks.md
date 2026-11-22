# Tasks

## Invalidates

- None.

## Expectation Coverage

- E1: Legacy recovery and real native verification (D1, D2). Covered by: 1.1
- E2: Repository-controlled patch publication and downstream update (D2). Durable owner: https://github.com/TanglmChris/keel/issues/550
- E3: Desktop composer, cold reopen and Kaiwu production automatic delivery remain separate. Durable owner: https://github.com/TanglmChris/keel/issues/550

- [x] 1.1 Negotiate legacy recovery capability
  - Covers:
    - D1
    - D2
  - Touch:
    - src/core/codex-host.js
    - scripts/test_codex_host.js
  - Verify:
    - Strategy: regression-first
    - M1: Public CLI recovery against a WebSocket native boundary rejects missing experimentalApi for runtimeWorkspaceRoots, then succeeds with no reviewer/policy record. Preserve exact role bytes, original thread and worktree, and zero turns.
    - M2: On an empty-auth native 0.167.2 private worktree, reproduce the published recovery error, then prove corrected recovery, cold persistence, original policy and claims, and migration without model turns or production actions.
    - M3 (regression): Run node --test scripts/test_codex_host.js scripts/test_codex_onboarding.js.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ab4d4dbe5959e5eef85aabcb2c39bce77c543d00c49602378d64148488f8acd1 (keel 5.231.0)
    - M1: Public legacy recovery regression passes, with no explicit reviewer/policy, exact original ID/cwd/roots, record bytes and no recovery-created turns.
    - M1.red: New CLI test reproduced thread/resume.runtimeWorkspaceRoots requires experimentalApi capability before the fix.
    - M1.green: Public CLI recovery completed after explicit handshake negotiation; all 30 extended host tests passed.
    - M2: Real 0.167.2 recovery/cold/restart/migration same-ID with prior claims preserved, policy and roots unchanged, no model turns, stable native refusal. evidence/legacy-recover-native.md.
    - M2.red: Real native 0.167.2 returned the same runtimeWorkspaceRoots requires experimentalApi capability error before the fix.
    - M2.green: Same native fixture recovered original worktree and policy, passed cold source/target and restart, migrated and refused unknown replay; processes exited.
    - M3: 30 host and onboarding CLI tests passed, zero failures or skips.
    - Review:
      - Status: pass
      - Acceptance check: Exact legacy error reproduced both at native boundary and on 0.167.2; narrow handshake fix restored behavior with same identity, policy and claims.
      - Scope check: Two declared product/test files and own change records. All native verification used temporary homes and zero model turns.
      - Findings: Resolved here: M1 and M2 prove legacy recovery. Durable owner: https://github.com/TanglmChris/keel/issues/550 — track desktop composer and production rollout independently.
    - Blocker: none
    - Reauthorizations: none

- [x] 2.1 Prepare the verified patch release
  - Covers:
    - D2
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/plugin.json
    - .claude-plugin/marketplace.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validation/common.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - .claude/skills/openspec-sync-specs/SKILL.md
    - .claude/skills/openspec-archive-change/SKILL.md
    - .claude/skills/openspec-apply-change/SKILL.md
    - .claude/skills/openspec-propose/SKILL.md
    - .codex/skills/openspec-sync-specs/SKILL.md
    - .codex/skills/openspec-archive-change/SKILL.md
    - .codex/skills/openspec-apply-change/SKILL.md
    - .codex/skills/openspec-propose/SKILL.md
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: evidence-first
    - Reason: version alignment, full local regression and actual package checks for an already tested behavior.
    - M1: Verify latest remote main and registry version, align patch metadata using bump script, run strict OpenSpec, full test suite, and temporary candidate clean and updater installation checks. Preserve OpenSpec 1.14.0.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:db117f8852ffb61093729c6a706e2ac63615103d9a1070bc7bc59f4aeb9a97ca (keel 5.231.0)
    - M1: Remote main and the public npm 5.231.0 baseline confirmed. Version aligned to 5.231.1; full 426-scenario test run passed without skips, strict delta passed, and disposable clean/updater installs locked OpenSpec 1.14.0 with 37 validated specs in each. evidence/release-checks.txt.
    - Review:
      - Status: pass
      - Acceptance check: All release checks passed, including isolated package installation and public CLI real native evidence in task 1.1.
      - Scope check: Only declared metadata markers and changelog, plus this change evidence; no global installation at candidate stage.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/550 — publication, local update, downstream and desktop remain tracked.
    - Blocker: none
    - Reauthorizations: none

- [x] 2.2 Commit verified release candidate
  - Mode: repo-action
  - Covers:
    - D2
  - Touch:
    - none
  - Verify:
    - Strategy: evidence-first
    - Reason: authorized repository commit, with publication using separate repository workflow.
    - M1: Stage and review only completed task scope and evidence, check diff, and commit verified patch. Subsequent archive, push, PR and release verification proceed through their own gates and standing authorization.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:61a0bc12e316654099f331224fd62b5b2e1014bfcd0ee3d404e3836abbf913fd (keel 5.231.0)
    - M1: 29 reviewed staged task paths under authorized two-file product/test scope, version markers, and change-local records. Staged diff check passed; initial commit a0affd65. Final tree adds only archive/spec sync and checked evidence.
    - Review:
      - Status: pass
      - Acceptance check: Committed candidate contains the verified legacy fix and release validation evidence. Publication follows repository full-gate.
      - Scope check: Only declared product, test, version metadata, changelog and change records.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/550 — follow official release and production validation; desktop remains open.
    - Blocker: none
    - Reauthorizations: none

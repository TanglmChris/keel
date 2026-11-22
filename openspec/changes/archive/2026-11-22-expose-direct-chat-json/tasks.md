# Tasks

## Invalidates

- None.

## Expectation Coverage

- E1: Public direct metadata and canonical renames without persistence or wake changes (D1, D2). Covered by: 1.1
- E2: Patch publication and downstream verification (D2). Durable owner: https://github.com/TanglmChris/keel/issues/552

- [x] 1.1 Project direct participants with or without renames
  - Covers:
    - D1
    - D2
  - Touch:
    - src/core/chat/store.js
    - scripts/validation/chat.py
    - scripts/validation/registry.py
  - Verify:
    - Strategy: regression-first
    - M1: Through the public CLI send ordinary and no-wake DMs and a plain group post; read the exact records using unread, group peek and show with an absent rename map and after a legal receiver rename. Verify canonical participants, unmentioned ordinary DM wake, no-wake suppression, no direct metadata on plain group, and compare stored record/cursor bytes before and after the reads.
    - M2 (regression): Run existing role rename, chat core, no-wake and wake-default scenarios.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:384269e16cd8ec94428b2b3e4f0b012fdcdbd000c2ca2574b47be93b576dae28 (keel 5.231.1)
    - M1: All three public read surfaces expose canonical participants, before and after rename; same records, no cursor advancement, ordinary group and no-wake preserved. evidence/direct-json.md.
    - M1.red: New CLI scenario failed before the fix with unread lost canonical DM participants: None.
    - M1.green: Same scenario passed on both absent and populated rename maps, stored records unchanged, after deriving direct metadata before the fast path.
    - M2: Five existing role rename, chat core and wake scenarios passed, six including the new case.
    - Review:
      - Status: pass
      - Acceptance check: Real public commands read the exact records and verify both positive addressing and non-waking cases, comparing logs and cursors after each set of reads.
      - Scope check: Three declared implementation/test paths and own change evidence only. All fixtures are disposable Git worktrees.
      - Findings: Resolved here: M1 verifies the corrected public JSON projection. Durable owner: https://github.com/TanglmChris/keel/issues/552 — verify publication and hand off consumer acceptance.
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
    - Contract: keel-task-capsule/v1 sha256:cdb4a645be2b68aa378f53852906c3b5d4ca54b25a2addb8917885dbe421650d (keel 5.231.1)
    - M1: Confirmed remote main baseline and public 5.231.1; aligned 5.231.2 and ran strict change validation. Full baseline plus 427 scenarios passed, zero skips. Candidate clean installation and old updater both used OpenSpec 1.14.0 and validated 37 published specs. evidence/release-checks.txt.
    - Review:
      - Status: pass
      - Acceptance check: Full regression including the new public JSON test, strict specs, and real candidate package tests pass.
      - Scope check: Only declared metadata and change-local evidence; candidacy tests used disposable install prefixes.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/552 — actual publication and downstream coordination.
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
    - Contract: keel-task-capsule/v1 sha256:eefe24e76be685413ac225abe6ec43e8e5a0193ccc852fda9841e77ed37e5805 (keel 5.231.1)
    - M1: Reviewed 29 staged paths: three product/test files, version manifests and change records. Staged diff check passed; initial commit f9ec15c8. Final tree adds only archive/spec sync and completed task evidence.
    - Review:
      - Status: pass
      - Acceptance check: Reviewed candidate contains the verified public JSON fix, focused and complete suite evidence and temporary install acceptance. The repository controls publication.
      - Scope check: Only declared product/test and release metadata plus this change records.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/552 — official publish and delivery of candidate proof. Kaiwu consumer acceptance remains on https://github.com/TanglmChris/kaiwu-ip/issues/561.
    - Blocker: none
    - Reauthorizations: none

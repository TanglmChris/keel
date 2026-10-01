## 1. Model chooses organization

- [x] 1.1 Remove extra subagent activation and declaration requirements, preserve guarded authority
  - Covers:
    - D1
    - D2
    - D3
    - D4
    - D5
    - D6
  - Touch:
    - bin/keel.js
    - src/core/projection.js
    - src/core/capabilities.js
    - plugins/keel/agents/keel-single-task-goal-codex.md
    - plugins/keel/agents/keel-single-task-goal-claude.md
    - src/core/config.js
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - AGENTS.md
    - assets/bootstrap/AGENTS.md
    - keel/config.yaml
    - keel/CHANGELOG.md
    - README.md
    - README.zh-CN.md
    - assets/openspec/schemas/keel-spec-driven/schema.yaml
    - assets/openspec/schemas/keel-spec-driven/templates/tasks.md
    - openspec/schemas/keel-spec-driven/schema.yaml
    - openspec/schemas/keel-spec-driven/templates/tasks.md
    - src/skills/keel-run-single-task-goal/SKILL.md
    - src/skills/keel-run-single-task-goal/guidance.md
    - plugins/keel/skills/keel-run-single-task-goal/SKILL.md
    - plugins/keel/skills/keel-run-single-task-goal/guidance.md
    - .claude/skills/openspec-apply-change/SKILL.md
    - .claude/skills/openspec-archive-change/SKILL.md
    - .codex/skills/openspec-apply-change/SKILL.md
    - .codex/skills/openspec-archive-change/SKILL.md
    - .claude/commands/opsx/apply.md
    - .claude/commands/opsx/archive.md
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario model-chosen-subagents` exercises public projection without activation, independent helpers with malformed delegation metadata, guarded implementation without a tier, explicit helper posture, malformed/stale/mismatched guards, no-write task rejection, native goal activation refusal, and ownership prohibitions.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario delegation-projection` preserves legacy declared-tier posture, its guard requirement and return authority.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario native-runtime-projection` preserves goal/task-view explicit activation and bounded helper context.
    - M4: Source/generated protocol, schema and skill text consistently leaves subagent choice to the model and retains goal activation, scope, guard and master completion boundaries; host policy is identified separately.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:db9755934144736385effa1ea27a925305c06d799aa36b18de085665060d9e0c
    - M1: pass. Public model-chosen-subagents scenario passes: no helper activation, independent helper metadata, guarded implementation without tier, malformed and mismatched guard/refused Touch widening, authored/config tier refusal, non-implementation modes, explicit helper override and explicit goal boundary. Active other-owner guards, delegate return non-mutation and malformed-guard independent helpers are also exercised; assertion-shape-count remains at 80 sites after separating failure causes.
    - M1.red: fail. Before implementation, model-chosen-subagents reported ordinary helper still requires activation: subagent-start projection requires explicit subagent authorization.
    - M1.green: pass. Same public CLI scenario now passes.
    - M2: pass. delegation-projection passes with legacy posture, declared metadata validation, guard checks and evidence-only return.
    - M3: pass. native-runtime-projection passes on supported targets; goal/task-view activation remains explicit and helper context bounded.
    - M4: pass. Source/generated protocol, schema and skill audits pass via delegation-resident-text, delegation-overlay, delegation-sole-authority and single-task-goal-skill. Goal-agent adapter metadata was re-audited and now carries matching guard and host-policy boundaries; delegation-sole-authority passes with explicit adapter assertions. Capability hints require no helper activation. Full-suite wording failures were repaired; resident-topic-matching, the-routing-rule-reaches-the-decision and skill-portability-policy independently pass. Canonical goal skill and packaged copy match. Actual bounded read-only helper subagent_policy_review returned an audit, without writes, goal activation or nested delegation; its findings were independently incorporated and re-tested. Current task D6 explicitly authorized this real helper check; this proves a launch accepted in this session, not host permission for arbitrary proactive launches or hook enforcement.
    - M4.red: fail. Before implementation, AGENTS required a declared delegation block, task templates stated delegation defaults to none, and the goal skill excluded Unrequested helpers, or an undeclared delegation. These conflicted with the owner decision.
    - M4.green: pass. All three old policy statements are absent from active authority, generated copies match, and the semantic boundary audit passed.
    - Review:
      - Status: pass
      - Acceptance check: model choice is available through real CLI without activation or required tier; negative tests refuse invalid write authority, guard drift and scope mismatch. Helper output is read-only; native completion remains advisory.
      - Scope check: git diff changes only declared task Touch and this change record; durable capsule schema and fingerprint fields remain unchanged. Protected generated overlays were refreshed only for apply/archive.
      - Findings: Resolved here: M1 proves rejection of guard Touch mismatch and task-authored invalid tiers found by the helper audit, and requires master-only task record/contract authority. Active other-owner guards, malformed-guard independent helpers and delegate native completion non-mutation are exercised. Host policy remains an explicit limitation in README and projection, not a claim Keel overrides it.
    - Blocker: none
    - Reauthorizations: owner-approved #190 scope includes capability projection guidance; expand Touch to src/core/capabilities.js to remove stale subagent activation hints. M1-M3 results remain valid for tested behavior. Adapter document discovery adds the two goal-agent metadata files to Touch; M4 will be re-audited along with full regression for both the capability hints and adapters.

## 2. Publish requirements

- [x] 2.1 Publish the reviewed policy requirements
  - Covers:
    - D1
    - D3
    - D5
  - Touch:
    - openspec/specs/keel-authorized-delegation/spec.md
    - openspec/specs/keel-native-runtime-projection/spec.md
    - openspec/specs/keel-openspec-surface-overlay/spec.md
    - openspec/specs/keel-single-task-goal-execution/spec.md
  - Verify:
    - Strategy: evidence-first
    - Reason: this publishes requirements proven by 1.1 without introducing another behavior.
    - M1: `keel openspec validate model-chosen-subagents --strict` passes and published requirements match the delta, with no standing contradiction about required activation or undeclared tiers.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:5946e8d188a1510d2970c9823e675e6b43290635158e52671d5d77f6a0f97b1f
    - M1: pass. keel openspec validate model-chosen-subagents --strict reports valid; published-specs-validate-strictly passes all 28 specs on OpenSpec 1.13.2. Requirement replacements remove mandatory activation and absent-tier refusals, keeping guarded write authority and explicit goal activation.
    - Review:
      - Status: pass
      - Acceptance check: all four published capabilities match reviewed delta requirements, with no active contradictory extra helper or tier permission.
      - Scope check: this task changed only its four published spec files and its record layer.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 3. Delivery

- [x] 3.1 Commit reviewed policy and evidence
  - Mode: repo-action
  - Covers:
    - D5
  - Touch:
    - none
  - Verify:
    - Strategy: evidence-first
    - Reason: committing reviewed work adds no behavior.
    - M1: `git show --stat HEAD` identifies this policy repair and `git diff --exit-code` confirms product files committed.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:83aeabc46ddb80645ac9d896a66239c750c64bc8309ce3d83df8ff5137d52382
    - M1: pass. git show --stat HEAD identifies the reviewed model-chosen subagent repair; git diff --exit-code passed before recording delivery evidence.
    - Review:
      - Status: pass
      - Acceptance check: commit contains the verified policy, behavior, generated surfaces and requirement authority.
      - Scope check: this repo-action changed no product content; only delivery records followed commit.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` in a clean Git snapshot passes baseline and all registered scenarios.

## Change Evidence

- C1: pass. Final clean Git snapshot matching the finalized product source passed npm test: baseline plus 210 scenarios, 1 macOS F_SETPIPE_SZ skip. Temporary npm cache and local fake Slack service permissions isolate external/environment effects. Earlier wording and test-diagnostic failures were corrected, then the full suite re-run. Log: /private/tmp/keel-subagent-full-test-passed.log.

## Invalidates

- I1: "subagent-start projection requires explicit subagent authorization" — src/core/projection.js and native-runtime-projection requirement. Updated by: 1.1, 2.1
- I2: "delegation defaults to none" — source and installed task templates. Updated by: 1.1
- I3: "Unrequested helpers, or an undeclared delegation" — single-task-goal skill copies. Updated by: 1.1
- I4: "where `delegation:` is declared" — resident protocol and generated overlays. Updated by: 1.1
- I5: "delegation is unauthorized" — published delegation spec and config documentation. Updated by: 1.1, 2.1

## Expectation Coverage

- E1: D1 and D2 leave bounded helper choice to the model without extra activation. Covered by: 1.1, 2.1
- E2: D3 and D4 allow guarded implementation with optional metadata, preserving scope and anchors. Covered by: 1.1, 2.1
- E3: D5 and D6 keep all surfaces consistent and distinguish host permission from projection and launch. Covered by: 1.1, 2.1

## Archive Review — 2026-10-01

- Status: pass
- Acceptance check: Rechecked completed task evidence and public-interface verification; every delta requirement is present in the published specs. All 29 published specs pass strict validation.
- Scope check: This closure only synchronizes published specifications and moves the completed change with its metadata and evidence; no implementation or task contract is changed.
- Findings: none. Existing follow-up ownership remains as recorded in the task Reviews.

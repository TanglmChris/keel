# Tasks

## 1. Route by a set of labels

- [ ] 1.1 Read label sets in `issue_roles:`, let the most specific matching route win, and document the form
  - Covers:
    - keel-coordinator-patrol / Issue labels route issue updates to roles / A set of labels routes to the team that carries them all
    - keel-coordinator-patrol / Issue labels route issue updates to roles / A set that cannot be read routes nothing
    - keel-coordinator-patrol / Issue labels route issue updates to roles / A labelled issue reaches its role once per update
    - D1
    - D2
    - D3
    - D4
    - D5
  - Read:
    - openspec/changes/issue-roles-label-sets/design.md
    - src/core/config.js
    - src/core/patrol.js
    - scripts/validation/shift.py
  - Touch:
    - src/core/config.js
    - src/core/patrol.js
    - scripts/validation/shift.py
    - scripts/validation/registry.py
    - README.md
    - README.zh-CN.md
    - keel/config.yaml
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-issue-label-sets`: with `issue_roles:` mapping `design` to `design-iecc`, `design + dmc_rmw` to `design-rmw`, and `flow` to `flow`, one patrol over issue 160 (`design`, `dmc_rmw`, `flow`) and issue 161 (`design`) leaves `design-rmw` and `flow` one unread notice naming #160 each, `design-iecc` none naming #160 and one naming #161, and `design-rmw` none naming #161. Fails with: `patrol-issue-label-sets:` Detects: `drop the strict-subset suppression in routeIssues` -> `design-iecc has 1 notices about #160`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario patrol-issue-label-set-unreadable`: with `issue_roles:` holding `design + : design-rmw` and `design + design: design-rmw`, a patrol over an issue labelled `design` prints both lines as unreadable and leaves `design-rmw` no notice. Fails with: `patrol-issue-label-set-unreadable:`
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py` with `--scenario patrol-issue-routing`, `--scenario coordinator-patrol`, `--scenario readme-zh-matches-english`, `--scenario config-documents-in-declaration-order`, `--scenario surfaces-agree-with-code`, `--scenario assertion-shape-count`, and every other `patrol-*` scenario passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:4707ad12763971cd13e61e215802d91e9875b5e2ac6a48dec2cdbe20107cc1bf (keel 5.191.0)
    - M1: pass. `patrol-issue-label-sets scenario passed.` (exit 0).
    - M1.red: fail. Before the change: `patrol-issue-label-sets: design-rmw has 0 notices about #160, not 1.` (exit 1).
    - M1.green: pass. `readIssueRoles` now returns routes as `{ labels, role }` and splits a key on ` + ` (D1, D2); `routeIssues` keeps the routes whose labels the issue all carries and drops one refined by a larger matching set (D3).
    - M1.detects: with `matching.filter((route) => !refined(route))` replaced by `matching` in `src/core/patrol.js`, the scenario failed: `patrol-issue-label-sets: design-iecc has 1 notices about #160, not 0.` (exit 1). Restored, it passes (exit 0).
    - M2: pass. `patrol-issue-label-set-unreadable scenario passed.` (exit 0).
    - M2.red: fail. Before the change: `patrol-issue-label-set-unreadable: the unreadable line \`design + : design-rmw\` is not reported: 'keel patrol: nothing new.\nrole design-iecc: …` (exit 1).
    - M2.green: pass. A set with an empty or repeated member is now an unreadable line, and the warning names both shapes (D4).
    - M3: pass. Each scenario was run on its own, and each exited 0:
      - `patrol-issue-routing`, `coordinator-patrol`, `patrol-since-last`, `patrol-next`, `patrol-exit-says-who-acts`, `patrol-nudge`, `patrol-escalate`, `patrol-quota`, `patrol-host-task`, `patrol-rearm`;
      - `readme-zh-matches-english`, `config-documents-in-declaration-order`, `surfaces-agree-with-code`;
      - `assertion-shape-count`, at 74 sites.
    - Review:
      - Status: pass
      - Acceptance check: E1 is met through the real `keel patrol --issues`. An issue labelled `design` + `dmc_rmw` + `flow` reaches `design-rmw` and `flow` and not `design-iecc`. An issue labelled `design` alone still reaches `design-iecc`. The single-label `role:verify` route behaves as before. Unreadable sets are reported and route nothing.
      - Scope check: `git status --short` lists the seven Touch files and this change's directory.
      - Findings: one defect outside this task. When given more than one `--scenario`, `validate_plugin.py` runs only the baseline and still exits 0, so a run that asked for several scenarios can read as passing. Running them all at once printed only `Keel v4.1.0 baseline validation passed.`, which is why M3 was run one scenario at a time. Durable owner: https://github.com/TanglmChris/keel/issues/444
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [ ] 2.1 Release and promote the spec
  - Covers:
    - E2
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/marketplace.json
    - .claude-plugin/plugin.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validation/common.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-coordinator-patrol/spec.md
    - .claude/skills/openspec-apply-change/SKILL.md
    - .claude/skills/openspec-archive-change/SKILL.md
    - .claude/skills/openspec-propose/SKILL.md
    - .claude/skills/openspec-sync-specs/SKILL.md
    - .codex/skills/openspec-apply-change/SKILL.md
    - .codex/skills/openspec-archive-change/SKILL.md
    - .codex/skills/openspec-propose/SKILL.md
    - .codex/skills/openspec-sync-specs/SKILL.md
  - Verify:
    - Strategy: evidence-first
    - Reason: this task changes only version markers, a changelog entry, and the spec promotion. Task 1.1 proves the behavior, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the delta is promoted into `keel-coordinator-patrol`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3165013edd371c33e7cbd7d9ab7c43c5e77c0642dd5e8ad489935ce29394d12f (keel 5.191.0)
    - M1: pending
    - M2: pending
    - M3: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "One `<label>: <role>` per line; a label may contain a colon." — the `issue_roles` comment in `keel/config.yaml`. Updated by: 1.1.
- I2: "`issue_roles:` in `keel/config.yaml` maps a label to a role" — `README.md`, and "`issue_roles:` 把一个标签映射到一个角色" in `README.zh-CN.md`. Updated by: 1.1.
- I3: "one `<label>: <role>` per line, read by `keel patrol`" — the `readIssueRoles` comment in `src/core/config.js`, and "is not `<label>: <role>`; it routes nothing." in `src/core/patrol.js`. Updated by: 1.1.
- I4: "`keel/config.yaml` MAY declare `issue_roles:`, one `<label>: <role>` per line" — `openspec/specs/keel-coordinator-patrol/spec.md`. Updated by: 2.1.

## Expectation Coverage

- E1: An issue carrying every label of a set route reaches that route's role once per update and not the role of a single-label route it refines; single-label lines work unchanged; an unreadable line is reported and routes nothing (#433; D1–D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1

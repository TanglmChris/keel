# Tasks

## 1. A task field refuses a state claim and not its provenance

- [x] 1.1 Bind the hash and worktree-state rules to a state claim inside task fields
  - Covers:
    - keel-stateless-continuity / A task field refuses a state claim and not its provenance / A cited base in a Review field is evidence
    - keel-stateless-continuity / A task field refuses a state claim and not its provenance / A base named in an Acceptance criterion is a condition
    - keel-stateless-continuity / A task field refuses a state claim and not its provenance / A domain term or a negation is not dirty state
    - keel-stateless-continuity / A task field refuses a state claim and not its provenance / A bound state claim in a field is still refused
    - keel-stateless-continuity / A task field refuses a state claim and not its provenance / A line outside any task field keeps the line-wide rule
    - D1
    - D2
    - D3
    - F1
    - F3
  - Read:
    - scripts/install_to_repo.py
  - Touch:
    - scripts/install_to_repo.py
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario a-task-field-cites-its-provenance` installs Keel into a temporary repository and runs `keel --check` over an active tasks.md. It requires `keel state: ok` for the five #213 shapes inside task fields: a Scope check naming `base 1f3a6b0` beside `hashes identify actual 211dfb5`, an Acceptance check `on dec4d6e` beside `source hashes`, an Acceptance criterion `after synchronized base dec4d6e` beside `Capture shared HEAD … before commit.`, `no dirty groups`, and `copied from uncommitted Claude changes`. It requires `keel state: failed`, naming the line, for each bound claim in a field (`committed to main as a1b2c3d`, `HEAD is at a1b2c3d`, `已合入 a1b2c3d`, `the work is still uncommitted`, `Status: dirty`) and for a task title line carrying `commit` and `a1b2c3d` apart. Fails with: `a-task-field-cites-its-provenance:`
    - M2: `node scripts/run_python.js scripts/install_to_repo.py --target claude --check ../../../../rtl_ppa_prj` prints no `state-error` naming `add-iecc-basic-verification/tasks.md`.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario a-context-word-is-a-word`, `a-submission-is-not-a-commit`, `a-quoted-span-is-not-a-claim`, `a-covers-citation-is-not-a-record`, `decimal-runs-are-not-hash-shaped`, and `cli` each pass (F3).
    - M4 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if an F3 fixture would have to change to pass, because that would narrow what the rule refuses beyond D1 and D2.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8ea17e062f4ba915359b305d090242e1e3cda3c9be32ad5934db3bf46cf7df53
    - Blocker: none
    - Reauthorizations: M3 named a scenario that does not exist (`a-quoted-span-is-a-citation`); corrected to `a-quoted-span-is-not-a-claim` and the contract re-recorded before any Evidence was written. No check's meaning changed, and M1's red stands.
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-task-field-cites-its-provenance` reports `a-task-field-cites-its-provenance scenario passed.` The five #213 shapes inside task fields are accepted. Each bound claim in a field, and a title line with `main` and `a1b2c3d` apart, is refused, and every refusal names its line.
    - M1.red: fail. With the scenario written and the check unchanged, it reported `a-task-field-cites-its-provenance: a Scope check naming its base was refused as recorded state.` beside the check's own `state-error openspec/changes/reading-lines/tasks.md:12: remove contextual commit hash from tasks.md`, carrying the declared signature `a-task-field-cites-its-provenance:`.
    - M1.green: pass. The same scenario passes once `check_tasks_semantics()` applies `TASKS_FIELD_BOUND_HASH_RE` and `TASKS_FIELD_DIRTY_STATE_RE` to lines inside `task_field_lines()`.
    - M2: pass. `node scripts/run_python.js scripts/install_to_repo.py --target claude --check ../../../../rtl_ppa_prj` prints `keel state: ok`, with no `state-error`; before the change it printed the eight in F1. The same check over this repository also turned from failed to ok, because a Review sentence in `directory-branch` on main had tripped the bare-word rule.
    - M2.red: fail. Before the change, the same command printed `keel state: failed` with eight `state-error` lines naming `add-iecc-basic-verification/tasks.md` lines 169, 219, 262, 277, 278 (twice), 327, and 328.
    - M2.green: pass. After the change it prints `keel state: ok`, with rtl_ppa_prj untouched at `4dbc89f`.
    - M3: pass. `a-context-word-is-a-word`, `a-submission-is-not-a-commit`, `a-quoted-span-is-not-a-claim`, `a-covers-citation-is-not-a-record`, `decimal-runs-are-not-hash-shaped`, and `cli` each report `scenario passed.` with no fixture changed.
    - M4: pass. `npm test` prints `validation --all passed: baseline plus 223 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: every check runs `keel --check` over a real tasks.md, and M2 runs it over the reporter's own checkout. The negatives sit in the same run as the positives, because what a narrowing risks is what stops being caught. The Stop rule held: no F3 fixture changed.
      - Scope check: `git status --short` lists `scripts/install_to_repo.py` and `scripts/validate_plugin.py`, both in Touch, plus this change's own directory.
      - Findings: Discard reason: a loosely phrased claim inside a field, such as one where `at a1b2c3d` is not bound to a context word, now passes. The design's Risks section accepts that, because fingerprints, gates, and Review hold the contract and refusing provenance costs more.

## 2. Release

- [x] 2.1 Release 5.91.0 and promote the spec
  - Covers:
    - E1
    - I1
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/marketplace.json
    - .claude-plugin/plugin.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validate_plugin.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-stateless-continuity/spec.md
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
  - Verify:
    - Strategy: evidence-first
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to 5.91.0, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.91.0 section written.
    - M2: the delta is promoted into `openspec/specs/keel-stateless-continuity/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ef0c69e9688f53da0e9e263f8c7b8280e41086bd1610a8273f56d95ed2da49c2
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.91.0. With the 5.91.0 section written, `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirement is appended to `openspec/specs/keel-stateless-continuity/spec.md`, and both MODIFIED requirements replace their published text, which updates I1. `published-specs-validate-strictly` reports `29 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the promoted store validates strictly, and the changelog names the reported failure, both bound forms, and what stays refused.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the promoted spec, both in Touch. The two scripts are 1.1's, which its gate attributed.
      - Findings: none

## Invalidates

- I1: "what makes a line a statement is bounded by two other requirements" and "the same wording that is exempt inside a `Covers` field appears in an `Evidence` or `Verify` line" — `openspec/specs/keel-stateless-continuity/spec.md`. Updated by: 2.1

## Expectation Coverage

- E1: A task's fields can cite the base a comparison ran against, the commit a result ran on, and domain uses of `dirty`, without failing the state check, while a bound state claim and any line outside a field are refused as before. Covered by: 1.1, 2.1

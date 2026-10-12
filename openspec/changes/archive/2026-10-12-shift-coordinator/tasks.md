# Tasks

## 1. Shift fixes

- [x] 1.1 `ready --role`, the unbound-worktree refusal, and accurate `status` hints
  - Covers:
    - keel-shift-change / A role's note is filed under the role from any worktree / A role working elsewhere files its note under the role
    - keel-shift-change / A role's note is filed under the role from any worktree / An unbound worktree does not misfile
    - keel-shift-change / Status suggests only what works / A worktree note's hint works
    - D4
    - D5
    - D6
    - F1
    - F2
    - F3
    - F4
  - Read:
    - src/core/shift.js
  - Touch:
    - src/core/shift.js
    - docs/shift-change.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-role-elsewhere` uses roles `rtl` and `verify` and an unbound worktree `loose`, with `rtl` requesting `verify`'s shift, and requires: `keel shift ready` in `loose` without `--role` refused naming `--role verify` with no worktree note written; `keel shift ready --role verify` in `loose` accepted, closing `verify`'s request; `keel shift start verify` by `rtl` accepted; `--role rtl` (no open request) refused; and, with a worktree note written by a second unbound worktree with no request open, `keel shift status` naming that worktree's path and `keel shift resume` and not `keel shift start worktree`. Fails with: `shift-role-elsewhere:`
    - M2 (regression): `shift-change` and `shift-without-role` still pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8b0f2b53a41ca79da0af900d8d4e88967c44267088f463fa74135f819125d1b5
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-role-elsewhere` reports `shift-role-elsewhere scenario passed.`
    - M1.red: fail. Before the change the scenario reported `shift-role-elsewhere: ready in an unbound worktree with verify's request open was accepted.`, carrying the declared signature `shift-role-elsewhere:` — the misfiling #290 describes.
    - M1.green: pass. With `readyRole`, the reply and closing record written as the `--role` role, and the status hints, the unbound `ready` is refused naming `--role verify` with no note written, `--role rtl` is refused, `--role verify` files `verify.md` and closes the request, `start verify` is accepted, and the second worktree's note line names its path and `keel shift resume` with no `keel shift start worktree`. A first green attempt failed because the closing reply was posted as the worktree's (absent) role; it is now written as the named role.
    - M2: pass. `shift-change` and `shift-without-role` each report `scenario passed.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives real `keel shift` commands across three role-bound and two unbound worktrees with a bare remote, reading exit codes, stderr, the note files, and `status`.
      - Scope check: `git status --short` lists `src/core/shift.js`, `docs/shift-change.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 The coordinator's check refuses while notes wait unstarted, and its resume lists them
  - Covers:
    - keel-shift-change / The coordinator starts the others before its own shift ends / A coordinator cannot leave while notes wait unstarted
    - keel-shift-change / The coordinator starts the others before its own shift ends / A new coordinator learns who still waits
    - D1
    - D2
    - D3
    - F1
    - F2
  - Read:
    - src/core/shift.js
  - Touch:
    - src/core/shift.js
    - docs/shift-change.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-coordinator-last` has `rtl` request `verify`'s shift and `verify` run `ready`, then requires `rtl`'s `keel shift check --json` to exit 1 with an `unstarted` item naming `verify` and `rtl`'s `ready` refused; after `keel shift start verify`, `rtl`'s check carrying no `unstarted` item; and, on a second round where `rtl` runs `ready --force-reason` with `verify` unstarted, `rtl`'s `keel shift resume` naming `verify` as still waiting for `keel shift start`; and the request text and `ready` output naming scheduled jobs. Fails with: `shift-coordinator-last:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:67d5c9a5c17543f0fd19e64c6fed613d1768ea6811346c80b55755354566594f
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-coordinator-last` reports `shift-coordinator-last scenario passed.`
    - M1.red: fail. Before the change the scenario reported `shift-coordinator-last: the request does not name scheduled jobs: …`, carrying the declared signature `shift-coordinator-last:`.
    - M1.green: pass. With `unstarted` in `check`, the waiting list in `resume`, and the request step and clear hint naming session state, the request and `ready` output name scheduled jobs, `rtl`'s check exits 1 with an `unstarted` item for `verify` and its `ready` is refused, after `start verify` the item is gone, and on the second round `rtl`'s `resume` names `verify` as still waiting for `keel shift start`. `shift-role-elsewhere`, `shift-change`, `shift-without-role`, and `patrol-rearm` still pass.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 261 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario runs a full request, ready, check, start, resume cycle twice through the real CLI with a bare remote, reading exit codes, the JSON items, chat records, and resume output.
      - Scope check: `git status --short` lists `src/core/shift.js`, `docs/shift-change.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Discard reason: a coordinator who clears with `--force-reason` still leaves its team dark until someone types into its new session, because Claude has no waker and Keel schedules nothing; the refusal makes that a stated choice rather than an accident, which is what the owner decided.
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [x] 2.1 Release and promote the spec
  - Covers:
    - E3
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
    - openspec/specs/keel-shift-change/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1 and 1.2, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the ADDED requirements are appended to `openspec/specs/keel-shift-change/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f3f01e04a009e8f0b5bc677a7ab209d8fb908d5becdb5db71c2deb843e8a9e27
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.113.0 on top of `main` at 5.112.1 (#288). With the 5.113.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The three ADDED requirements are appended to `openspec/specs/keel-shift-change/spec.md`; `published-specs-validate-strictly` reports `34 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the published spec carries all three requirements with their scenarios, and the changelog names the three issues and the decisions.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the spec, both in Touch.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump to 5.113.0 reports `validation --all passed: baseline plus 261 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- I1: "`keel shift start worktree <name>-<id>` wakes it to resume" — the worktree-note line of `keel shift status` in `src/core/shift.js`. Updated by: 1.1
- I2: "| role | `keel shift ready \"<note>\"` | Stores the note and closes the request, if there is one." — the steps table in `docs/shift-change.md`, which says nothing of `--role` or of the coordinator's own shift. Updated by: 1.1, 1.2

## Expectation Coverage

- E1: A role whose session worked in another worktree hands over under its role, and an unbound worktree cannot misfile (D4, D5, D6). Covered by: 1.1
- E2: A coordinator cannot leave the team waiting unstarted without saying so, and its successor sees who still waits (D1, D2, D3). Covered by: 1.2
- E3: The release carries it. Covered by: 2.1

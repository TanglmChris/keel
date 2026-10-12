# Tasks

## 1. Self shift

- [x] 1.1 `start` refuses yourself, `resume --role`, and status and `ready` say how a self-filed note resumes
  - Covers:
    - keel-shift-change / A role neither starts itself nor loses its note to another worktree / Starting yourself is refused
    - keel-shift-change / A role neither starts itself nor loses its note to another worktree / A new shift in another worktree resumes the role's note
    - keel-shift-change / A session changes its own shift and is woken once its next session starts / A role without a coordinator is told how its new session starts
    - D3
    - D4
    - D5
    - D6
  - Read:
    - src/core/shift.js
  - Touch:
    - src/core/shift.js
    - docs/shift-change.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-self` uses role `pm` and an unbound worktree `other`, and requires: `keel shift start pm` by `pm` exiting non-zero naming `ready --wake` with no `dm-pm--pm` group; `keel shift ready` by `pm` (no request) saying nobody is set to start the new session and naming `--wake`; `keel shift status` saying `pm`'s note is resumed by its own next session; and `keel shift resume --role pm` in `other` printing the note, after which `pm`'s note no longer waits. Fails with: `shift-self:`
    - M2 (regression): `shift-change`, `shift-without-role`, `shift-role-elsewhere`, and `shift-coordinator-last` still pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:18ddf38f950dd935c193e88772f96411ca6577dcad471195daf924a23b26dc00
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-self` reports `shift-self scenario passed.`
    - M1.red: fail. Before the change the scenario reported `shift-self: ready does not say nobody is set to start the new session: …`, carrying the declared signature `shift-self:`; the output still ended with "The coordinator's `keel shift start` then wakes the new shift".
    - M1.green: pass. With `clearHint`, the self-start refusal, `resumeRole`, and the status branch for a note no request asked for: `pm`'s `ready` says nobody is set to start the new session and names `--wake`, `start pm` by `pm` exits 1 naming `ready --wake` with no `dm-pm--pm` log, status says `pm`'s own next session resumes it, `resume --role pm` in `rtl`'s worktree is refused, and in the unbound `other` worktree it prints the note and `pm.md` no longer waits.
    - M2: pass. `shift-change`, `shift-without-role`, `shift-role-elsewhere`, and `shift-coordinator-last` each report `scenario passed.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives real `keel shift` commands from role-bound and unbound worktrees with a bare remote, reading exit codes, stdout, stderr, the chat log directory, and the note file.
      - Scope check: `git status --short` lists `src/core/shift.js`, `docs/shift-change.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 `ready --wake` leaves a one-shot waiter that wakes the role's next session, and the protocol states the exception
  - Covers:
    - keel-shift-change / A session changes its own shift and is woken once its next session starts / The cleared session is woken once
    - keel-unattended-triage / Keel ships no scheduler / The shift wake is the one named exception
    - D1
    - D2
    - D7
    - F1
    - F2
    - F3
    - F4
    - F5
  - Read:
    - src/core/shift.js
    - src/core/chat/notice.js
  - Touch:
    - src/core/shift.js
    - src/core/chat/notice.js
    - AGENTS.md
    - README.md
    - docs/shift-change.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-self-wake` with `KEEL_SHIFT_WAKE_POLL_MS=100` has `dev` run `keel shift ready --wake`, then feeds `keel chat hook session-start` a `compact` payload and requires no record from `keel-shift` after 1 s, then a `clear` payload and requires, within 5 s, exactly one unread record for `dev` from `keel-shift` naming `keel shift resume` and `keel chat notice --check` exiting 0; requires `ready --wake` in an unbound worktree with no `--role` refused; and requires the `AGENTS.md` line beginning `- Keel schedules nothing` to name `keel shift ready --wake`. Fails with: `shift-self-wake:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:02c42e1e2c97be39bbf7b9e7c00a501ca378c5c73925746eaa32785335484e4e
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-self-wake` reports `shift-self-wake scenario passed.`
    - M1.red: fail. Before the change the scenario reported `shift-self-wake: ready --wake in an unbound worktree with no --role was accepted.` (the flag was ignored), and after the protocol check was added `shift-self-wake: the protocol's scheduling line does not name the keel shift ready --wake exception: …`, both carrying the declared signature `shift-self-wake:`.
    - M1.green: pass. With `session_started`/`session_source` recorded by the chat SessionStart hook, `armWake` spawning the detached `keel shift wake-wait`, and the protocol line naming the exception: the unbound `ready --wake` is refused, a `compact` start writes nothing within 1 s, a `clear` start yields exactly one record from `keel-shift` in `dm-keel-shift--verify` naming `keel shift resume` and still one 0.5 s later, and `keel chat notice --check` for `verify` exits 0.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 263 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario drives the real `keel shift ready --wake`, the real `keel chat hook session-start` with host-shaped payloads, and reads the chat log and `notice --check`, so the detached waiter is exercised as a real process.
      - Scope check: `git status --short` lists `src/core/shift.js`, `src/core/chat/notice.js`, `AGENTS.md`, `README.md`, `docs/shift-change.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Discard reason: the waiter sees only a session opened in a worktree bound to the role, because the SessionStart hook records presence only for a bound role; a new session in another worktree still needs someone to type into it, which `docs/shift-change.md` states. Widening it would mean guessing which unbound session is the role's.
    - Blocker: none
    - Reauthorizations: 1. During implementation the published requirement "Keel ships no scheduler" (`keel-unattended-triage`) was found to contradict the owner's decision; the change gained a MODIFIED delta stating the exception, 1.2 gained its Covers entry and the AGENTS.md assertion in M1, and `keel gate task-start --record` re-recorded the contract before any Evidence was written.
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
    - openspec/specs/keel-unattended-triage/spec.md
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
    - M2: the ADDED requirements are appended to `openspec/specs/keel-shift-change/spec.md`, the MODIFIED requirement replaces its counterpart in `openspec/specs/keel-unattended-triage/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f3501815e14eccf1cacb64197b3e9ef99fd33dc3d0c2870101f443fcdedd611c
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.114.0; with the 5.114.0 changelog section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirements are appended to `openspec/specs/keel-shift-change/spec.md` and the MODIFIED "Keel ships no scheduler" replaces its counterpart in `openspec/specs/keel-unattended-triage/spec.md`; `published-specs-validate-strictly` reports `34 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the version markers, the changelog section, and both promoted specs are checked by the two scenarios, and the full suite passes on the bumped tree (C1).
      - Scope check: `git status --short` lists the version-marker files, `keel/CHANGELOG.md`, the two published specs, and the files 1.1 and 1.2 changed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Invalidates

- I1: "Keel schedules nothing. `/loop`, cron, and CI triggers belong to the host runtime" — `AGENTS.md` Unattended runs, and "**Keel schedules nothing.**" in `README.md`. Updated by: 1.2
- I3: "Keel MUST NOT provide, imply, or claim a scheduling capability" — `openspec/specs/keel-unattended-triage/spec.md`, Keel ships no scheduler. Updated by: 2.1
- I2: "The coordinator's `keel shift start` then wakes the new shift" — the clear hint in `src/core/shift.js`, untrue for a role no request named. Updated by: 1.1

## Expectation Coverage

- E1: A role with no coordinator — the PM going last, or any session changing its own shift — is told how its new session starts, cannot start itself, and finds its note from any worktree (D3–D6). Covered by: 1.1
- E2: Such a session is woken once its next session starts, by a one-shot waiter the protocol names as its only scheduling exception (D1, D2, D7). Covered by: 1.2
- E3: The release carries it. Covered by: 2.1

## Change Evidence

- C1: pass. `npm test` on the 5.114.0 tree reports `validation --all passed: baseline plus 263 scenarios, 1 skipped: output-survives-the-pipe.`

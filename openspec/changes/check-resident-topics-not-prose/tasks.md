<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Record only task-specific authority. Omitted fields inherit versioned
     defaults: Owner is the current Keel agent, Mode is implementation, Read
     is the change proposal/design/specs/tasks plus discovered repository
     context, Acceptance derives from Covers, autonomy defaults to hard-stop,
     Coupling defaults to none, helpers stay read-only/evidence-only, and
     commit, push, sync, archive, and cross-task continuation stay
     unauthorized. Declare a field only when it differs from these defaults. -->

## 1. Match topics by pattern, commands by literal

- [x] 1.1 Let a required resident-block entry be a topic pattern, and convert the one that blocked work
  - Covers:
    - D1 a required entry is a literal for a command or marker and a pattern for prose, and the diagnostic names which kind is missing
    - D2 only the entry that has demonstrably blocked work is converted, with the mechanism as the path for the rest
    - keel-validation-runner / Resident-block content is checked as topics, not as prose / Rewording a topic keeps the check green
    - keel-validation-runner / Resident-block content is checked as topics, not as prose / Deleting a topic still fails
    - keel-validation-runner / Resident-block content is checked as topics, not as prose / Renaming a command still fails
  - Touch:
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: with the bootstrap's Touch sentence reworded so it keeps both concepts but not the old phrasing, the baseline run and the skill-portability-policy scenario both pass where both previously reported the missing topic by its exact prose; with that statement deleted entirely, both still fail and name the topic; with a rewrite that keeps only the word Touch and drops the boundary concept, both still fail; and with a required command name changed in the block, both still fail with a diagnostic that distinguishes a missing literal from a missing topic. A new validator scenario drives all four against a temporary copy of the block so the shipped bootstrap is never left modified, and the full suite stays green with the real bootstrap unchanged
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:896d605a466c016db94595e7e29717791526f950e97dfd5be8aef8bcb1839002
    - M1: `validate_resident_blocks` gained a `root: Path = ROOT` parameter so the check can be driven against a copy, and its required-entry loop now branches on type: a `str` is matched as a substring and reported as a `missing required literal`, a compiled pattern is matched with `search` and reported as a `missing required topic`. A comment states the rule — a literal names a command, marker, or identifier whose rename must fail; a pattern states prose whose wording may move because the block is under a line and byte budget. Only the Touch entry was converted, to `re.compile(r"Touch\b[^\n]*\bbound", re.IGNORECASE)`, with a comment saying the others stay literal until one needs the same freedom. Both callers go through this one function, so `run_baseline` and the `skill-portability-policy` scenario behave identically by construction rather than by duplicated logic
    - M1.red: the new `resident-topic-matching` scenario exited non-zero with `TypeError: validate_resident_blocks() takes 1 positional argument but 2 were given` — the check read the shipped bootstrap from `ROOT` unconditionally, so the behavior could not be exercised against any wording but the current one
    - M1.green: the scenario exits 0 across six checks driven through the real check function against temporary copies. The unmodified bootstrap passes; rewording the sentence to "Touch bounds product writes, not the task's own records;" — which shares no phrasing with the old entry — passes; deleting the statement fails and names the topic; a rewrite keeping only the word `Touch` and dropping the boundary concept fails, so a partial mention does not satisfy it; renaming `keel context` to `keel status` fails and is reported as a **missing required literal**; and a missing topic is never reported as a missing literal. The scenario re-reads the shipped bootstrap at the end and asserts it is byte-identical. `npm test` reported "validation --all passed: baseline plus 72 scenarios"
    - Review:
      - Status: pass
      - Acceptance check: pass — the block's prose can be reworded without a validator edit, deleting a topic and renaming a command both still fail with distinguishable diagnostics, and every case runs through the single function both callers use, satisfying D1, D2 and the three referenced scenarios
      - Scope check: pass — `scripts/validate_plugin.py` only, within Touch, verified against `--base HEAD`. The shipped bootstrap is unchanged and the scenario asserts that
      - Findings: measured what this actually buys for issue #15's remaining half, since D3 predicted "a few bytes, not enough" and a number is better than an adjective. Dropping the pinned phrasing frees **13 bytes** — "Touch bounds product writes only;" puts the block at 1003 of 1024. Naming the exemption still does not fit: the nearest phrasing, "Touch bounds product writes, not the task's own records;", lands at **1026, over by 3**. So the budget question is still the binding constraint, now with a hard number instead of an estimate, and it is 3 bytes rather than the ~19 estimated before this task. Durable owner: https://github.com/TanglmChris/keel/issues/15
    - Blocker: none

## Expectation Coverage

- E1: the resident block's prose can be improved without editing the validator Covered by: 1.1
- E2: deleting a required topic still fails, and a partial mention does not satisfy it Covered by: 1.1
- E3: renaming a required command still fails, distinguishably from a missing topic Covered by: 1.1
- E4: both callers of the check behave identically Covered by: 1.1

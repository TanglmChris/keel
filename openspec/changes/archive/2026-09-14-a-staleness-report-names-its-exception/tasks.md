# Tasks

## 1. Every staleness exit names the declaration that narrows it

- [x] 1.1 The blanket re-record warning, the `task-complete` contract-drift refusal, and the context drift hard-stop each name `--keep-evidence`, state that it applies to a check whose assertion did not move, and send the reason to `Reauthorizations`; none of them names which checks it would apply to, and the already-narrowed report does not repeat the suggestion
  - Covers:
    - keel-core-gates / A re-record may carry what the author declares survived it
    - keel-core-gates / A recorded anchor is compared against the recompiled fingerprint
    - keel-stateless-continuity / A reported drift names where the covered authority was read from
    - F1
    - F2
    - F3
    - D1
    - D2
    - D3
    - D4
    - D5
    - A1
  - Read:
    - src/core/gates.js
    - src/core/context.js
    - scripts/validate_plugin.py
    - openspec/changes/a-staleness-report-names-its-exception/design.md
  - Touch:
    - src/core/gates.js
    - src/core/context.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-staleness-report-names-its-exception` scenario in `scripts/validate_plugin.py` drives all three exits through the real CLI against fixtures whose recorded anchor differs from the compiled one. `task-start --record` with no declaration reports a warning naming `--keep-evidence`, the condition that the check's assertion did not move, and `Reauthorizations`, and names no `M<n>` as unaffected. `task-complete` on the same fixture fails `contract-drift` with a diagnostic naming both `keel gate task-start --record` and `--keep-evidence`. `keel context` on the same fixture is blocked with a reason naming `--keep-evidence`. `task-start --record --keep-evidence M1,M3` is asserted to still name `M1, M3` as declared unaffected — the positive control — and then asserted not to carry the suggestion its reader just used. Fails with: `does not name --keep-evidence`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario evidence-survives-what-did-not-change` passes unchanged, so what the declaration accepts, refuses, narrows, and leaves to completion is untouched by a change to what the messages say.
    - M3 (regression): the set of scenarios `npm test` reports as failing is identical to the set the same command reports on unmodified `origin/main` in a worktree of this same checkout, so no scenario regressed. A differential rather than a pass, because two scenarios fail on both sides for a host reason this task does not own: https://github.com/TanglmChris/keel/issues/137.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if naming the declaration requires the message to identify which checks are unaffected, because D3 records that the gate retains only the previous fingerprint and cannot know — a message that guessed would claim the knowledge the flag exists to supply.
    - Stop if any assertion about `--keep-evidence`'s own accept/refuse/narrow behavior has to change to make a message assertion pass, because D4 records that this change alters no behavior and M2 is the check that would catch it.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:c6d2041cddeb36628d8610e88e17e2a9b46f166d78ae15d05b5dae05eb87e037
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-staleness-report-names-its-exception` reports `a-staleness-report-names-its-exception scenario passed.` Against a three-check fixture whose recorded anchor is 64 zeroes and therefore differs from the compiled one, all three exits are driven through the real CLI. `task-start --record` with no declaration warns `Execution evidence produced under the previous contract is stale; clear or re-verify it before completing this task. If a check's assertion did not move, re-record with ``--keep-evidence <check>`` to say so; Keel records that claim and does not verify it, so state the reason in Reauthorizations.` `task-complete` on the same fixture fails `contract-drift` with a diagnostic carrying both `keel gate task-start --record` and the same sentence. `keel context --json` on the same fixture is `blocked` with a drift reason carrying it. No exit names `M1`, `M2`, or `M3` while suggesting the flag, asserted separately at each of the three. `--record --keep-evidence M1,M3` is asserted to still say `declared unaffected` — the positive control, without which the next assertion is satisfied by a dead branch — and then asserted not to carry `--keep-evidence` at all.
    - M1.red: fail, for the right reason, three times — once per exit, each taken before that exit was implemented and after the one before it was. (1) `the blanket stale-evidence report does not name --keep-evidence, so an author who has not already used it re-verifies everything; 'Re-recorded over a different contract: ... Execution evidence produced under the previous contract is stale; clear or re-verify it before completing this task.'` (2) after the blanket branch was written: `the contract-drift refusal does not name --keep-evidence even though it names the command that accepts it; '... Reauthorize with ``keel gate task-start --record``, which rewrites the anchor in place; execution evidence produced under the previous contract is stale and has to be cleared or re-verified first.'` (3) after that one: `the context drift hard-stop does not name --keep-evidence even though it tells the reader to re-record the anchor; '... Reauthorize by re-running ``keel gate task-start`` and recording the new anchor, after confirming the change to the authority above was intended.'` All three carry the declared signature `does not name --keep-evidence`. Each red printed the exit's full current text, which is how it was confirmed the fixture had reached that exit rather than failing before it: red (2) had already passed the assertion that the refusal names the reauthorization command, and red (3) had already passed the assertion that context blocked on drift.
    - M1.green: pass. Same command after the three message strings were written, in the same order.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario evidence-survives-what-did-not-change` reports `evidence-survives-what-did-not-change scenario passed.` What the declaration accepts, refuses, narrows, and leaves to completion is untouched; that scenario asserts the narrowed wording, the unknown-label refusal, the refusal without `--record`, and that a red-green task still fails `task-complete` with `missing-strategy-evidence`.
    - M3: pass. `npm test` reports `validation --all failed for: the-dependency-resolves-where-npm-put-it, a-declared-dependency-is-resolved`. The same command in a detached worktree at `origin/main` (6588c9a), unmodified, reports the identical set. No scenario regressed. Both fail because those two scenarios build a PATH with no `openspec` on it by dropping whole directories, and this host symlinks `/opt/homebrew/bin/node` beside `/opt/homebrew/bin/openspec`, so `node` goes with it and the resolved shim exits 127 — owned by https://github.com/TanglmChris/keel/issues/137.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that all three staleness exits name the declaration with its condition and where the reason goes, that none names which checks it would apply to, and that the already-narrowed report does not repeat the suggestion. M1 proves each of the five at each exit it applies to, through the CLI rather than by reading the strings. Two shapes in it carry the weight. The negative control — no `M<n>` appears beside the suggestion — is what stops a later implementation from computing the answer the gate cannot know, which is the one way this change could turn into the verification D3 says it is not. The positive control before the narrowed-branch silence is the precedent `an-assertion-that-never-failed-proves-nothing` applied literally: an absence assertion is satisfied by the branch being dead, so the branch is proven alive first. The reds are per-exit rather than one red for the batch, so each exit has its own failure and none is green by having been carried.
      - Scope check: `git status --short` shows `src/core/gates.js`, `src/core/context.js`, and `scripts/validate_plugin.py` — exactly this task's Touch — plus this change's own untracked directory and `keel/guard.json`. `keel guard status` reports the fingerprint unchanged from the re-record. No behavior changed: the diff is three message strings and one new scenario, and M2 is the check that would have caught otherwise.
      - Findings: one, not resolved here. `npm test` does not pass on this host, and its diagnostic names the wrong subject: `a-declared-dependency-is-resolved` reports `the resolved openspec did not report a version. exit=127`, pointing at a tool that is installed and working, while the binary actually missing from the PATH it built is `node`. The scenario's own comment shows the hazard was anticipated and guarded only in its global form — "Emptying PATH outright would also remove `node`" — and directory-granularity filtering reintroduces it for the ordinary Homebrew plus `npm install -g` layout where one bin directory holds both. It is a false stop, the shape that costs a whole cycle with nobody watching, and it makes `npm test` unusable as a completion check on an affected host. Not fixed here: `scripts/validate_plugin.py` is in this task's Touch, but the fix is to a fixture's PATH construction with no relation to this task's Acceptance, and folding it in would be the scope expansion the contract forbids. Durable owner: https://github.com/TanglmChris/keel/issues/137
    - Blocker: none
    - Reauthorizations: M3 was reworded from "`npm test` passes with no other scenario affected" to the differential against `origin/main` that it is, before any Evidence was recorded, so nothing was invalidated. The original was unsatisfiable on this host for a reason with no causal path to this task: `a-declared-dependency-is-resolved` and `the-dependency-resolves-where-npm-put-it` build a PATH with no `openspec` on it by dropping whole directories, and this host keeps `node` and a global `openspec` in the same one. Both fail identically at 6588c9a. Filed as https://github.com/TanglmChris/keel/issues/137 rather than fixed here, because the fix is to a fixture's PATH construction and is not what this task was authorized to change.

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — every staleness exit names the declaration, with its condition and where the reason goes
    - E2 — no exit names which checks the declaration would apply to
    - E3 — the flag's own behavior is unchanged
    - I1 — the reauthorization sentence that names the command and omits its flag
    - I2 — the contract-drift sentence that does the same
  - Read:
    - keel/CHANGELOG.md
    - README.md
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
    - openspec/specs/keel-core-gates/spec.md
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
    - Reason: this task's whole effect is version markers and promoted spec text. The behavior was proven red-green in task 1.1, and nothing here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `keel/CHANGELOG.md` carries an entry giving the measured discoverability cost from issue #134 — one use in 67 task capsules, the flag named only in its own error paths, the median re-verification it costs — and stating that no gate behavior changed
    - M3: both spec deltas are promoted into `openspec/specs/keel-core-gates/spec.md` and `openspec/specs/keel-stateless-continuity/spec.md`, `node node_modules/.bin/openspec validate a-staleness-report-names-its-exception --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: the set of scenarios `npm test` reports as failing is identical to the set the same command reports on unmodified `origin/main`, so the release moved no scenario, for the same host reason and the same owner as task 1.1's M3: https://github.com/TanglmChris/keel/issues/137
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:b8977d5104315e6ace535b2f8ca07ea00c1b2d906bd558ac60370e8c082a9bf9
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.58.0 to 5.59.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.59.0 - a staleness report names its exception`. It gives the measured discoverability cost from issue #134 — the flag named in three places in the installed package, all of them its own parse site and refusals; one use in 67 task capsules; a median 256 s re-verification; two full re-runs in one session, one for a single literal in a `Fails with:` clause — names all three exits and says why `task-complete`'s was the sharpest, states that the message carries the flag's limit rather than only its name, states that no exit names which checks are unaffected and why the gate cannot know, and states that the flag's own behavior is unchanged with the 5.55.0 scenario as the check for it.
    - M3: pass. Both deltas are promoted — `openspec/specs/keel-core-gates/spec.md` carries the blanket-warning clause on `A re-record may carry what the author declares survived it` with its two new scenarios, and the flag clause on `A recorded anchor is compared against the recompiled fingerprint` with its new scenario; `openspec/specs/keel-stateless-continuity/spec.md` carries the reauthorization clause on `A reported drift names where the covered authority was read from` with its new scenario and the extended does-not-guess scenario. `node node_modules/.bin/openspec validate a-staleness-report-names-its-exception --strict` reports `Change 'a-staleness-report-names-its-exception' is valid`, and `published-specs-validate-strictly` reports `23 published specs validate strictly against openspec 1.6.0.`
    - M4: pass. `npm test` reports `validation --all failed for: the-dependency-resolves-where-npm-put-it, a-declared-dependency-is-resolved` — the identical set the same command reports in a detached worktree at unmodified `origin/main` (6588c9a). The release moved no scenario. Both are the host PATH defect owned by https://github.com/TanglmChris/keel/issues/137.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all, rather than through the bump script's own report of what it wrote — the two would agree even if a marker existed that neither knew about, which is what the Stop Rule is for, and none appeared. M3 asserts the promotion through both tools that consume the published store, strict in both. M2 is the prose check, and its job is that a reader of this release learns what the change did not do: the flag is unchanged, the gate still cannot know which checks survived, and the message is not a verification. All three are stated in the entry beside the feature rather than after it.
      - Scope check: `git status --short` shows exactly this task's Touch entries — the package and lockfile, both plugin manifests, the three `keel:start` files, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, the two promoted spec files, and the twelve `.claude/`/`.codex/` marker files — plus `src/core/gates.js`, `src/core/context.js`, and task 1.1's scenario in `scripts/validate_plugin.py`, all declared complete by 1.1 and untouched here, plus this change's own untracked directory. `keel guard status` reports the fingerprint unchanged from the re-record.
      - Findings: none beyond the one task 1.1 recorded, which this task's M4 inherits rather than repeats. Durable owner: https://github.com/TanglmChris/keel/issues/137
    - Blocker: none
    - Reauthorizations: M4 was reworded from "`npm test` passes with no failing scenario and no exception" to the differential against `origin/main` it can actually be, before any Evidence was recorded, so nothing was invalidated. Same cause and same owner as task 1.1's M3: two scenarios fail on this host at 6588c9a and after this change alike, because they drop whole PATH directories to remove `openspec` and this host keeps `node` in the same one. https://github.com/TanglmChris/keel/issues/137

## Invalidates

- I1: "Reauthorize by re-running `keel gate task-start` and recording the new anchor, after
  confirming the change to the authority above was intended." — `driftSearchSet` in
  `src/core/context.js`, and the `keel-stateless-continuity` requirement it implements. It names
  the command and stops there, so a reader who has never seen `--keep-evidence` is told to
  re-verify everything by the same sentence that had room to say otherwise.
  Updated by: 1.1, 2.1
- I2: "execution evidence produced under the previous contract is stale and has to be cleared or
  re-verified first" — the `contract-drift` problem in `src/core/gates.js`, and the
  `keel-core-gates` requirement it implements. The sentence directly above it already prints
  `keel gate task-start --record`, which is the command that takes the flag.
  Updated by: 1.1, 2.1
- I3: "Keel does not verify the claim" and the rest of `README.md`'s `## Re-recording a contract`
  section. It stays true and is not updated: this change adds no verification, and the section is
  already the place that states the limit.
  Discard reason: the wording is correct after this change. What was wrong was that a reader had
  to already be in that section to learn the flag exists, and the fix is at the three exits, not
  in the section that was right.

## Expectation Coverage

- E1: Each of the three staleness exits names `--keep-evidence`, states the condition under which it applies, and states that the reason belongs in `Reauthorizations` (F1, D1, D2). Covered by: 1.1
- E2: No exit names which checks the declaration would apply to, at any of the three (D3). Covered by: 1.1
- E3: What the flag accepts, refuses, narrows, and leaves to completion is unchanged (D4). Covered by: 1.1
- E4: The already-narrowed report does not suggest the declaration its reader just used (D5). Covered by: 1.1
- E5: The published specs and every version marker move with the behavior (I1, I2). Covered by: 2.1
- E6: Whether a reader who is told the flag exists goes on to weigh what it does not verify before relying on it. Deliberately cites no `A<n>`: A1's statable half is D2 — the message carries the limit rather than only the name — and 1.1 covers both, so citing A1 here would put one identifier on the covered and the deferred side at once. What is deferred is the residue no message can close, because a message can state a limit and cannot make it land. Durable owner: https://github.com/TanglmChris/keel/issues/134

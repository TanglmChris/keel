# Tasks

## 1. The declaration

- [x] 1.1 `publish.yml` declares one concurrency group with `cancel-in-progress: false`, and a scenario refuses each way that declaration can be absent, per-run, or cancelling
  - Covers:
    - keel-validation-runner / The publish workflow serializes / A missing concurrency group is refused
    - keel-validation-runner / The publish workflow serializes / A cancelling group is refused
    - keel-validation-runner / The publish workflow serializes / A per-ref group is refused
    - D1
    - D2
    - D3
    - F2
    - F3
    - F4
  - Read:
    - .github/workflows/publish.yml
    - scripts/validate_plugin.py
  - Touch:
    - .github/workflows/publish.yml
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-publish-waits-for-the-one-before-it` scenario asserts the real `.github/workflows/publish.yml` declares a `concurrency` group scoped to the whole workflow, and refuses a copy with the block removed — the state the file was in when eleven releases published at once. Fails with: `simultaneous releases publish concurrently`
    - M2: a copy declaring a group but omitting `cancel-in-progress: false` is refused. The default is `true`, so a check satisfied by the block alone would pass on the configuration that *loses* a version rather than appearing to, which is worse than the state being fixed. Fails with: `a queued publish would be cancelled`
    - M3: a copy whose group expression varies per run — `publish-${{ github.ref }}` — is refused, because a group that differs per release serializes nothing while looking exactly like a fix. Fails with: `a per-run group serializes nothing`
    - M4 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` and `--scenario the-tarball-is-the-repository` pass, so nothing else that reads the release machinery moves
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if asserting the declaration needs a YAML parser, because D4 of the config reader records that this repository reads its own flat configuration line-oriented rather than taking a dependency for a format it controls, and two keys plus a trigger are matchable without one.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a08e57609f14460b93a7b71a4dfaf5a3dd4b8ff02258e479eb2ecd0c704c5d6a
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-publish-waits-for-the-one-before-it` reports the scenario passing. `publish_serialization_problem` takes the workflow text, per the Stop Rule, so each broken shape runs on a planted copy. The real file is asserted clean, and a copy with the `concurrency:` block stripped is refused — that copy is not hypothetical, it is byte-for-byte the state the file was in on 2026-09-25 when eleven releases published at once. The strip itself is asserted to have changed something, or the removal would prove nothing about a file that never declared the block.
    - M1.red: fail, for the declared reason. `a-publish-waits-for-the-one-before-it: simultaneous releases publish concurrently — no \`concurrency:\` block could be located to remove, so the real file does not declare one and the check has nothing to prove.` Carries the declared signature `simultaneous releases publish concurrently`.
    - M1.green: pass. Same command after `publish.yml` declared `concurrency: {group: publish, cancel-in-progress: false}` and the rule looked for the block.
    - M2: pass. A copy with `cancel-in-progress: false` removed is refused. This is the assertion that earns its place: GitHub's default for a declared group is `true`, so a check satisfied by the block alone would pass on the configuration that cancels a queued publish and loses that version outright — strictly worse than the state being fixed, and indistinguishable from the fix by eye.
    - M2.red: fail, for the declared reason. `a-publish-waits-for-the-one-before-it: a queued publish would be cancelled — a group without \`cancel-in-progress: false\` was accepted, and the default cancels a queued publish when the next release fires.` Carries the declared signature `a queued publish would be cancelled`.
    - M2.green: pass. Same command after the rule read the block body for the key.
    - M3: pass. A copy whose group reads `publish-${{ github.ref }}` is refused, and the diagnostic quotes the expression. This is the shape that looks like a fix and is not: every release has its own ref, so every run gets its own group and none of them wait.
    - M3.red: fail, for the declared reason, taken by removing the `${{` branch after it had been written in the same edit as M2's. `a-publish-waits-for-the-one-before-it: a per-run group serializes nothing — a group expression that differs per release was accepted, so each publish gets a group of its own and none of them wait.` Carries the declared signature `a per-run group serializes nothing`. Recorded plainly: this is a red for code that existed, not for code that did not. The alternative was to claim a red I had not produced.
    - M3.green: pass. Same command with the branch restored.
    - M4: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes and `--scenario the-tarball-is-the-repository` reports `42 packed files, all tracked.`, so neither the release-marker checks nor the packaging check moved. `npm test` reports `validation --all passed: baseline plus 182 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the defect had no victim — #153 records that nothing was lost and that the cost was a wrong diagnosis acted on — so nothing here is a repair; what 1.1 adds is the ordering that removes the window, plus the check that keeps it. The Acceptance is that the workflow serializes and that the declaration cannot be silently weakened. Every assertion runs against planted text, which is the only way to know a rule over a file like this fires — `publish.yml` executes only on GitHub, only on a `release` event, so the repository's own copy is the one input guaranteed to be correct and a check that only ever saw it would pass forever. The three refused shapes are ordered by how convincing they look: absent, present-but-cancelling, present-and-per-run. The last two both read as "concurrency is handled" to a reviewer skimming the file, which is precisely why they are asserted separately rather than folded into one presence check.
      - Scope check: `git status --short` shows `.github/workflows/publish.yml` and `scripts/validate_plugin.py` — this task's two Touch entries — plus this change's own directory. The Stop Rule held: the rule uses three regexes over the block's text and takes no YAML dependency, consistent with how this repository already reads its own flat configuration.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1
    - E2
    - E3
    - I1
  - Read:
    - keel/CHANGELOG.md
  - Touch:
    - package.json
    - package-lock.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-validation-runner/spec.md
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
    - Reason: this task's whole effect is version markers, a changelog entry, and a promoted spec. The behavior was proven red-green in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, and the 5.70.0 changelog section is written into the stub rather than above it — the rule 5.69.0 added judges this release too
    - M2: `keel/CHANGELOG.md` records that nothing was lost, that the damage was a wrong diagnosis acted on from the registry read side, and that `cancel-in-progress: false` is the load-bearing half
    - M3: the delta is promoted, `node node_modules/.bin/openspec validate a-publish-waits-for-the-one-before-it --strict` passes, and `published-specs-validate-strictly` passes
    - M4: `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:4aa08246989346c5b39e592343ad1a0607a530841926048d398116e8bb4f2e85
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes; every marker moved 5.69.0 to 5.70.0 via `node scripts/bump_version.js minor`. The 5.70.0 section was written *into* the stub `bump_version.js` wrote, not above it — the rule 5.69.0 added judges this release like any other, and this is the first release authored after it where the temptation to prepend existed. The Stop Rule held.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.70.0 - a publish waits for the one before it`. It records that **nothing was lost** and that the write side proved it; that the damage was a wrong diagnosis acted on from the registry read side, with the practical rule that follows — confirm a publish from the job log, not the listing; that `cancel-in-progress: false` is the load-bearing half and why the default is wrong here; why a per-ref group serializes nothing; why all three shapes are asserted on planted copies given that this file cannot run locally; and why registry polling was not added.
    - M3: pass. The delta is promoted into `openspec/specs/keel-validation-runner/spec.md`. `node node_modules/.bin/openspec validate a-publish-waits-for-the-one-before-it --strict` reports valid, and `published-specs-validate-strictly` passes inside `npm test`.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 182 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all, and this release is also the second one judged by 5.69.0's stub rule — the two checks meet on the same file. M3 asserts the promotion through both consuming tools. M2's bar was that the entry not read as an incident report: the fact worth carrying is not "eleven releases collided" but that **the registry's read side can report a published version as missing**, which is the thing a future reader will otherwise rediscover by triggering pointless re-runs exactly as happened here.
      - Scope check: `git status --short` shows the version markers, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, and the promoted spec, plus `.github/workflows/publish.yml` and `scripts/validate_plugin.py` declared complete by 1.1, and this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "The full validation suite is Windows/CLI-specific and runs in the pre-push hook before any
  release tag is pushed, so it is not re-run here." — the comment in `.github/workflows/publish.yml`.
  It stays true and stops being the only thing that comment block says about how releases are
  sequenced, now that the file declares an ordering of its own.
  Updated by: 1.1
- I2: "Landing a stack is only expensive if you squash" and the 11-PR procedure recorded in native
  memory on 2026-09-25 — that procedure creates eleven releases in a loop, which is the event this
  change makes safe. The wording stays correct and its hazard section no longer needs to warn about
  the publish side.
  Discard reason: native memory is not a repository artifact and is not owned by an OpenSpec change;
  it was corrected in the same session the fix was authored, and the durable record is this change
  plus https://github.com/TanglmChris/keel/issues/153.

## Expectation Coverage

- E1: The publish workflow declares one group for the whole workflow, so simultaneous releases publish
  one at a time (D1, F2). Covered by: 1.1
- E2: `cancel-in-progress: false` is declared and separately asserted, because the default loses a
  version (D2, F3). Covered by: 1.1
- E3: A group that varies per run is refused, since it looks like a fix and serializes nothing (D1).
  Covered by: 1.1
- E4: Whether the workflow should confirm its own publish by reading the registry back (D4).
  Discard reason: deliberately not done rather than deferred. The registry read side is what produced
  the false reading this change exists because of; `npm publish` already prints
  `+ @christang/keel@<version>` from the write path, and polling the packument to confirm a publish
  would reintroduce the lag with a longer feedback loop.

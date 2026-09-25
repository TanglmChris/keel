# Tasks

## 1. The declaration

- [x] 1.1 `keel/config.yaml` declares `executor_tier:`, `keel context` and `keel --doctor` report it, and an unreadable value fails closed to `standard` naming what it rejected
  - Covers:
    - keel-guidance-tiering / The skip is declared by the repository / An absent declaration reads the guidance
    - keel-guidance-tiering / The skip is declared by the repository / An unreadable value fails closed
    - keel-guidance-tiering / The tier is visible where the session starts / The projection reports the tier and its limit
    - D2
    - D5
    - D6
    - D7
  - Read:
    - src/core/config.js
    - src/core/context.js
    - bin/keel.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/config.js
    - src/core/context.js
    - bin/keel.js
    - scripts/validate_plugin.py
    - keel/config.yaml
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-tier-declares-what-is-skipped` scenario asserts `keel context` in a fixture declaring `executor_tier: high` reports that tier, that a fixture declaring nothing reports `standard`, and that both report guidance as the only thing the tier affects. Fails with: `no executor tier reported`
    - M2: the same scenario declares `executor_tier: aggressive` and asserts the surface reports `standard` while naming both the rejected value and the accepted set — a typo must not silently buy the skip it asked for. Fails with: `accepted a tier outside the set`
    - M3: `executor_tier` is the seventh name in the exported declaration list and `keel/config.yaml`'s header names it, proven by the derived header rule added in 5.66.0 rather than by a new assertion
    - M4 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario a-count-is-derived-from-what-it-counts` and `--scenario delegation-resident-text` pass, so adding a declaration costs a header line and a list entry and nothing else
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if reporting the tier requires the projection to read a skill body, because a projection that parsed skills would make the declaration's effect depend on what is installed rather than on what is declared.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:382cc8c4243067ed7985b81be5e1beedb6bd3cb512c0916aa06fb807b316ca72
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-tier-declares-what-is-skipped` reports `a-tier-declares-what-is-skipped scenario passed.` A fixture declaring `executor_tier: high` reports `Executor tier: high`, one declaring nothing reports `standard`, and both lines are asserted to contain the word `guidance` — the tier's reach is part of the line rather than something a reader is expected to look up.
    - M1.red: fail, for the declared reason. `a-tier-declares-what-is-skipped: no executor tier reported — the high repository is told nothing about which guidance its skills load.` Carries the declared signature `no executor tier reported`.
    - M1.green: pass. Same command after `readExecutorTier` was added to `src/core/config.js` and `resolveContext`/`renderContext` reported it.
    - M2: pass. A fixture declaring `executor_tier: aggressive` reports `Executor tier: standard`, and the projection names both `aggressive` and `high`, so the author of a typo learns which value was refused and which are accepted. `keel --doctor` reports the same verdict — `executor_tier: unreadable` naming the value — and a readable declaration prints `executor_tier: high`, so the tier is not a field the doctor mentions only when it is broken.
    - M2.red: fail, for the declared reason. `a-tier-declares-what-is-skipped: accepted a tier outside the set — an unreadable value did not fall back to reading the guidance; got 'Executor tier: aggressive — affects which skill guidance is read and nothing else; …'.` Carries the declared signature `accepted a tier outside the set`. The unvalidated reader had passed the value straight through, which is the exact failure: a misspelling silently buying the reduction it asked for.
    - M2.green: pass. Same command after `readExecutorTier` fell back to `EXECUTOR_TIER_DEFAULT` for an unrecognized value and `executorTierUnreadableMessage` named the value and the set.
    - M3: pass. `executor_tier` is the seventh name in `CONFIG_DECLARATIONS`, and `keel/config.yaml`'s header names it. Proven by the two scenarios that already derive the header rule from the export: `a-count-is-derived-from-what-it-counts` and `delegation-resident-text` both pass, and no assertion was added for the new declaration. No assertion was added, which is the point: the red and green below were produced by the two existing scenarios reacting to the export.
    - M3.red: fail, from both derived-header scenarios, taken by adding `executor_tier` to `CONFIG_DECLARATIONS` before the header named it. `a-count-is-derived-from-what-it-counts: keel/config.yaml's header does not name 'executor_tier', which is the declaration a new project would never learn it may write.` and `delegation-resident-text: keel/config.yaml's header does not name the \`executor_tier\` declaration, so a project reading it would never learn it may write one. Add it to the header's list.` Both name the declaration and neither reports a count — the behavior 5.66.0 was built for, observed on the first declaration added after it.
    - M3.green: pass. Both scenarios pass once the header names `executor_tier` beside the other six, after the mutation repair recorded in Findings.
    - M4: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-count-is-derived-from-what-it-counts` and `--scenario delegation-resident-text` both pass, and `npm test` reports `validation --all passed: baseline plus 179 scenarios, 1 skipped: output-survives-the-pipe.` The declaration cost a header line and a list entry, as designed — plus one repair, recorded in Findings.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the declaration — not the executor — decides, that an unreadable value reads the guidance anyway, and that both surfaces state the tier's limit. Each is asserted on the observable projection and doctor output rather than on the reader's return value, so the proof runs through the interface a session actually meets. The fallback direction is the part worth being explicit about: every other declaration in this file fails closed toward *less* happening, and closed here means more reading, which is why M2 asserts the value `standard` rather than merely asserting that something was refused.
      - Scope check: `git status --short` shows `src/core/config.js`, `src/core/context.js`, `bin/keel.js`, `scripts/validate_plugin.py`, and `keel/config.yaml` — this task's five Touch entries — plus this change's own untracked directory. The Stop Rule held: the projection reads `keel/config.yaml` and nothing under `src/skills/`, so what it reports depends on what is declared and not on what is installed.
      - Findings: `a-count-is-derived-from-what-it-counts` still pinned the header's numeral — one level down from the literal it removed. The scenario varies the prose count to prove membership is the only checked property, and it did so by replacing the exact string `"Six independent declarations"`; adding `executor_tier` moved the header to "Seven" and the mutation stopped finding anything to vary, failing with `the header's prose count could not be located to vary it`. So 5.66.0 removed the hand-bumped assertion and left a hand-bumped mutation behind it, and the first declaration added afterward hit it. The mutation now locates the numeral by shape (`\b\w+ independent declarations\b`), which is the same fix applied consistently. Resolved here: M3, which passes only because both derived-header scenarios pass after the repair, and M4, which re-runs them.

    - Blocker: none
    - Reauthorizations: one. Task 1.2's M3 named `plugin-skills-match-source`, a scenario that does not exist — caught by `authored-scenario-names-are-registered`, which reads a name after `--scenario` and refuses an unregistered one. The real check is inside `native-plugin-manifests`, so 1.2's M3 was rewritten to name it and to extend it to `guidance.md`. Editing another task's Verify text moved this task's fingerprint from `sha256:47c33f2…` to `sha256:382cc8c…`, so 1.1 was re-recorded. No text of 1.1's own contract moved and no evidence had been written yet, so nothing was carried forward with `--keep-evidence`; every check above was run under the recorded contract.

- [x] 1.2 `keel-run-single-task-goal`'s conditional how-to prose moves to `guidance.md`, the body names it and the condition, and a guidance file stating a criterion is refused by name
  - Covers:
    - keel-guidance-tiering / A skill's stepwise guidance is referenced, not resident / The body points at the guidance it moved
    - keel-guidance-tiering / A skill's stepwise guidance is referenced, not resident / A guidance file carries no criterion
    - D1
    - D3
    - D4
    - F1
    - F3
    - F4
  - Read:
    - src/skills/keel-run-single-task-goal/SKILL.md
    - scripts/validate_plugin.py
    - openspec/changes/guidance-loads-by-declaration/design.md
  - Touch:
    - src/skills/keel-run-single-task-goal/SKILL.md
    - src/skills/keel-run-single-task-goal/guidance.md
    - plugins/keel/skills/keel-run-single-task-goal/SKILL.md
    - plugins/keel/skills/keel-run-single-task-goal/guidance.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `guidance-is-referenced-and-carries-no-criterion` scenario asserts every `src/skills/*/guidance.md` is named by the `SKILL.md` beside it together with the condition under which it is read, and that the body is measurably smaller than before the split. Fails with: `guidance file is not referenced`
    - M2: the same scenario plants `MUST` into a copy of a guidance file and asserts the check fails naming that file and that word, so "the tier removes no criterion" is a property the suite holds rather than a claim the design makes. Fails with: `states a criterion`
    - M3: `native-plugin-manifests` compares a skill's `guidance.md` against its source the way it already compares `SKILL.md`, and passes — the host reads the plugin copy directly, so a guidance file the parity check ignored could drift from the body that references it. Fails with: `guidance file diverges`
    - M4 (regression): `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if any sentence that would move to `guidance.md` states a criterion, because D3 forbids the tier from removing one and the split is then the wrong shape for that sentence.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:fc6ae3695999c57ce29cd356869f6a3231188d54ba818d7469af9caf7cfb94fc
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario guidance-is-referenced-and-carries-no-criterion` reports `guidance-is-referenced-and-carries-no-criterion scenario passed.` Every `src/skills/*/guidance.md` is asserted to be named by the `SKILL.md` beside it, and that body is asserted to name both `executor_tier` and `high` — the condition, not just the file, because a pointer with no condition is the self-assessment #135 argues against. "Measurably smaller" is checked as a property of what is on disk: the guidance holds at least 500 bytes and none of its `##` headings survive in the body, so the section moved rather than being copied. The empty glob is refused before the loop, or the whole scenario would pass by reading nothing.
    - M1.red: fail, for the declared reason. `guidance-is-referenced-and-carries-no-criterion: guidance file is not referenced — keel-run-single-task-goal's SKILL.md never names guidance.md, so the prose that left the body is unreachable from it.` Carries the declared signature `guidance file is not referenced`. Taken with the split already made and the pointer deliberately withheld, which is the state a careless split actually produces: content gone, nothing pointing at it.
    - M1.green: pass. Same command after the body gained a `## Guidance` section naming the file and the declaration that skips it.
    - M2: pass. Planting `An executor MUST record the fingerprint before implementing.` into a copy of the guidance file is refused, and the refusal names both `keel-run-single-task-goal` and `MUST`. The rule takes the text rather than a path, so it can be exercised on a copy; a rule that could only ever read files already known to be clean would pass forever without anyone learning whether it fires.
    - M2.red: fail, for the declared reason. `guidance-is-referenced-and-carries-no-criterion: states a criterion — a guidance file carrying \`MUST\` was accepted, so nothing stops a criterion from moving into the file the tier skips.` Carries the declared signature `states a criterion`. The red was taken against `guidance_criterion_problem` as a stub returning `None`: the property under test is that the rule is not vacuous, and the only state that demonstrates the assertion would notice a vacuous rule is one where the rule returns nothing. Stated plainly because it is a seam introduced to be red, not a defect found in the field.
    - M2.green: pass. Same command with the rule scanning for `CRITERION_VOCABULARY` — `MUST`, `SHOULD`, `refuses`, `rejects`, `hard-stops` — and applied to every real guidance file in the same loop.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario native-plugin-manifests` reports `native-plugin-manifests scenario passed.` The parity loop now compares `guidance.md` against its source the way it already compares `SKILL.md`, and refuses a body whose referenced guidance the plugin does not ship at all — the two ways the reference can resolve to the wrong bytes for a host that reads the plugin copy directly.
    - M3.red: fail, for the declared reason, taken with the body synced and the guidance not. `native-plugin-manifests guidance file diverges from canonical source: keel-run-single-task-goal has guidance.md that the plugin does not ship, so the body's reference resolves to nothing` Carries the declared signature `guidance file diverges`.
    - M3.green: pass. Same command after `plugins/keel/skills/keel-run-single-task-goal/guidance.md` was written and tracked; `the-tarball-is-the-repository` had refused it as untracked first, which is the same property from the packaging side.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 180 scenarios, 1 skipped: output-survives-the-pipe.` Four scenarios failed on the way there and are recorded in Findings.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the guidance is referenced with its condition and carries no criterion. The first is asserted on the files themselves; the second is asserted by planting a criterion, which is the only operation that separates a working rule from a rule that has never been given anything to catch. The split's actual yield is worth stating rather than implying: the body went from 6,265 to 5,554 bytes, an 11% reduction, with 1,708 bytes in the referenced file. That is a modest number and it is the honest one — Keel's skill bodies are criteria-dense, which is the measurement recorded in design F3 and the reason D4 splits one skill rather than six.
      - Scope check: `git status --short` shows `src/skills/keel-run-single-task-goal/SKILL.md`, its new `guidance.md`, both plugin copies, and `scripts/validate_plugin.py` — this task's five Touch entries — plus this change's own directory. The Stop Rule held: nothing that moved into `guidance.md` states a criterion, and the sentences that came closest — "do not fake activation", the evaluator never completing a task, Claude and Codex only — stayed in the body on purpose.
      - Findings: three scenarios pinned content of this skill that the split moved, and all three failed: `single-task-goal-skill` on the four official doc links and on the provenance/license wording, `native-goal-codex` on `advisory`, and `native-goal-claude` on `disabled hooks`. This is the split's real hazard rather than an accident of these three: a requirement asserted against `SKILL.md` can be silently satisfied-away by moving its sentence, and a split skill's content now lives in two files. Resolved here: M4, via `skill_guidance_text`, which returns the referenced half for a split skill and `""` for every other — so each assertion reads body-plus-guidance and no scenario has to know which skills were split. `native-plugin-manifests` (M3) closes the other half by requiring the guidance to ship byte-identically, so a statement cannot be kept only in a file the host never receives. Two of the four failures were mine to fix rather than the suite's: a tightening pass had dropped the literal phrase `disabled hooks` and the word `provenance` while rewriting for length, and both were restored — a check pinning an exact phrase is the reason that loss was caught in one run instead of by a reader months later.
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1
    - E2
    - E3
    - E4
    - I1
    - I2
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
    - README.md
    - keel/config.yaml
    - openspec/specs/keel-guidance-tiering/spec.md
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
    - Reason: this task's whole effect is version markers, a changelog entry, documentation, and a promoted spec. The behavior was proven red-green in 1.1 and 1.2, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes
    - M2: `keel/CHANGELOG.md` records that the mechanism the issue assumed does not exist (F1), the measurement that redirected it (F2, F3), and that the tier is checked to remove no criterion rather than promising not to
    - M3: `README.md` documents `executor_tier:` beside the other declarations and states that it affects guidance only
    - M4: the delta is promoted, `node node_modules/.bin/openspec validate guidance-loads-by-declaration --strict` passes, and `published-specs-validate-strictly` passes
    - M5: `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:54de79347fa11469af72c487e24144c3aa7f45a7d80afcbbeaa2dc2ba0b0afc4
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes; every marker moved 5.66.0 to 5.67.0 via `node scripts/bump_version.js minor`. The Stop Rule held.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.67.0 - guidance loads by declaration`. It records that the mechanism #135 assumed does not exist and why — the host reads the plugin's `SKILL.md` directly and Keel is not on that path; the measurement that redirected the work, including the 32,518 bytes of stepwise prose that belong to OpenSpec and are reverted by the command Keel's own doctor prints; the 11% the one split actually yielded, stated as the honest number rather than the hoped-for one; that the tier is *checked* to remove no criterion and why a rule that only reads clean files proves nothing; the three scenarios the split broke and the shape of the fix; and the 5.66.0 repair, where removing a hand-bumped assertion left a hand-bumped mutation one level down.
    - M3: pass. `README.md` gains "How much guidance the agent loads" beside the routing declaration. It states the two kinds of content and why their value moves in opposite directions, the `executor_tier: high` declaration and that the default and every unreadable value read the guidance, that `keel context` and `keel --doctor` report it, that the tier reaches guidance and nothing else *and* that this is checked rather than promised, why the skip is declared instead of self-assessed, and that one skill is split with the measurement as the reason.
    - M4: pass. The delta is promoted into `openspec/specs/keel-guidance-tiering/spec.md`. `node node_modules/.bin/openspec validate guidance-loads-by-declaration --strict` reports valid, and `published-specs-validate-strictly` reports `25 published specs validate strictly against openspec 1.6.0.` The published spec needed a `## Purpose` section the delta does not carry; `published-specs-validate-strictly` refused it first, which is the check doing its job at the moment of promotion.
    - M5: pass. `npm test` reports `validation --all passed: baseline plus 180 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all. M4 asserts the promotion through both consuming tools. M2 and M3 are about what a reader learns without running anything, and the bar for both was the same: record the two measurements that changed the design, not only the design they produced. A reader who sees an 11% reduction and no explanation will read the single split as an unfinished sweep and try to finish it.
      - Scope check: `git status --short` shows the version markers, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `README.md`, and the promoted spec, plus the files 1.1 and 1.2 declared complete and this change's own directory. `keel/config.yaml` was declared in Touch here and needed nothing beyond the header line 1.1 already wrote.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: one. This task's Touch omitted the twelve `opsx` overlay files that carry a
      version marker, so `keel gate task-complete` refused them as outside Touch after
      `node scripts/bump_version.js minor` rewrote them. The omission is an authoring error rather
      than a scope expansion — `version-alignment` requires every marker to move together, and those
      markers are why. The twelve paths were added to Touch and the task re-recorded from
      `sha256:d9959ae…`. No check's assertion moved, so nothing was carried forward with
      `--keep-evidence`; every check above was re-run under the new contract.

## Invalidates

- I1: "Six independent declarations live here" — the header of `keel/config.yaml`. A seventh is added,
  and the header's enumeration is the checked part after 5.66.0, so the entry must be added there and
  not only in the code.
  Updated by: 1.1, 2.1
- I2: "generic test-writing mechanics … belong to the host runtime and are not restated here" in
  `src/skills/keel-tdd-or-test-first/SKILL.md` — still true, and it is the closest existing statement
  to what this change generalises, so a reader may take it as the whole policy on resident guidance.
  Durable owner: https://github.com/TanglmChris/keel/issues/135
- I3: "Confirm detailed conditional knowledge uses progressive references when it is not needed on
  every activation." — the skill-change criterion in `src/skills/keel-review-checklist/SKILL.md`. It
  stays exactly as written and stops being a rule Keel applies only to other people's skills.
  Discard reason: the wording is correct after this change; what moves is Keel's compliance with it,
  not the criterion.
- I4: "28,939 bytes across six skill bodies" and any statement of Keel's resident skill cost — the
  measurement recorded in issue #135 and in this change's proposal. The split moves bytes out of one
  body, so a figure quoted from before it is wrong the moment 1.2 lands.
  Updated by: 1.2

## Expectation Coverage

- E1: A repository can declare `executor_tier:`, and the declaration — not the executor's judgement —
  decides whether guidance is read (D2). Covered by: 1.1
- E2: A tier Keel cannot read reads the guidance anyway, naming what it rejected (D7). Covered by: 1.1
- E3: A guidance file is referenced by its body with its condition, and carries no criterion, checked
  by planting one (D1, D3). Covered by: 1.2
- E4: The declaration is reported where the session starts, with its limit stated (D6). Covered by: 1.1
- E5: Whether the five criteria-dense skill bodies are also split (D4). Discard reason: deliberately
  not done rather than deferred. Splitting them would move criteria out of the resident body, which
  D3 forbids and M2 of 1.2 refuses; the measurement in F3 is the reason, and it is recorded in the
  changelog so a future author does not read the single split as an unfinished sweep.
- E6: Whether `guidance.md` gets its own target-native projection (Q1). Discard reason: the plugin
  already copies a skill directory wholesale, so the file travels with the body it belongs to and a
  projection would be a second delivery path for the same bytes — which is the drift
  `plugin-skills-match-source` exists to refuse.

# Tasks

## 1. The check

- [x] 1.1 `version-alignment` refuses a changelog whose released version is not described — a `TODO` heading, a `- TODO:` bullet, or two sections for that version — and names the line it found
  - Covers:
    - keel-validation-runner / A release describes itself / An unfilled stub is refused
    - keel-validation-runner / A release describes itself / Two sections for one version are refused
    - keel-validation-runner / A release describes itself / An older unfilled section is not the current author's problem
    - D1
    - D2
    - D3
    - F1
    - F2
  - Read:
    - scripts/validate_plugin.py
    - keel/CHANGELOG.md
  - Touch:
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: the rule is a function taking the changelog text and the released version, and a copy of `keel/CHANGELOG.md` carrying the stub `bump_version.js` writes for the current version is refused, with the diagnostic naming the `TODO` line verbatim rather than the file. Fails with: `an unfilled stub was accepted`
    - M2: a copy carrying two `## <version>` headings for the released version is refused — the shape the real defect had, which neither `TODO` rule catches once the stub's heading is renamed. Fails with: `a version described twice was accepted`
    - M3: a `TODO` inside a section for some *other* version passes, and the repository's own changelog passes unchanged — an older section is history the current author cannot act on, and a rule that swept the file would fail on the archive. Fails with: `an older section was refused`
    - M4 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so the marker assertions the scenario already carries are unaffected by the one added inside it
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the rule has to read `keel/CHANGELOG.md` from disk to be tested, because a rule that can only see the file that is already correct is one nobody can prove fires.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:c000099e70152eb7ccb39031af6aefdc2a7b8dda6c2c27f05a2ffe0219d01f16
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` `release_description_problem` takes the changelog text and the released version, per the Stop Rule, and is exercised on planted copies. Both halves of the stub are refused: a `## 5.68.0 - TODO: summarize this release` heading, and — separately — a section with a plausible heading whose only content is `- TODO: describe the change.`, because renaming the stub's title would otherwise be enough to ship an undescribed release. Each refusal is asserted to contain the offending line verbatim rather than only a verdict.
    - M1.red: fail, for the declared reason. `version-alignment scenario: an unfilled stub was accepted — a changelog whose 5.68.0 section is the stub `bump_version.js` writes produced no problem, so a release can ship describing nothing while this scenario passes.` Carries the declared signature `an unfilled stub was accepted`. Recorded plainly: this red was taken against `release_description_problem` as a stub returning `None`. The property under test is that the rule is not vacuous, and a rule that returns nothing is the only state that shows the assertion would notice one. The bullet half then produced a second, unmanufactured red under the same signature, against the real heading rule.
    - M1.green: pass. Same command after the heading rule, and then the section-body bullet rule, were implemented.
    - M2: pass. Two `## 5.68.0` headings are refused, the diagnostic says the version is described `twice` and lists both headings. This is the shape the actual defect had — 5.67.0 and 5.68.0 each carried a real entry *and* an orphan stub — and neither `TODO` rule catches it once the stub's heading has been renamed.
    - M2.red: fail, for the declared reason. `version-alignment scenario: a version described twice was accepted — two `## 5.68.0` sections produced no problem, which is the shape the defect this rule exists for actually had.` Carries the declared signature `a version described twice was accepted`.
    - M2.green: pass. Same command after the duplicate-heading branch was added ahead of the `TODO` branches, so the defect's real shape is named as itself rather than as whichever stub half happened to survive.
    - M3: pass. A `TODO` in a `## 5.0.0` section does not fail the 5.68.0 release, and the repository's own 705-line changelog passes unchanged — which matters because that file legitimately quotes `TODO` when describing the rules that refuse it, in the 5.29.0 entry. A rule firing on its own documentation is one an author deletes.
    - M3.red: fail, for the declared reason, taken by widening the bullet scan from the released section's body to the whole file. `version-alignment scenario: an older section was refused — a TODO in a section for another version failed the current release, which is a check the archive can only be edited to satisfy.` Carries the declared signature `an older section was refused`. The unscoped version also failed against the repository's real changelog, which is the same defect arriving from the other direction.
    - M3.green: pass. Same command with the scan bounded by the next `## ` heading.
    - M4: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with every marker assertion it already carried — package.json, both plugin manifests, the dependency pin, `keel --version`, the newest-heading claim, and the init overlay — untouched; the new rule is added inside the scenario rather than replacing anything. `npm test` reports `validation --all passed: baseline plus 181 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the defect this task guards against was found and fixed before this change existed — both orphan stubs were removed on branch `an-equivalence-claim-names-its-base` — so nothing here is a repair; what 1.1 adds is the guard that was missing. The Acceptance is that a release which does not describe itself is refused, by name, for the version being released. Every assertion runs against planted text, which is the only way to know a rule of this kind fires — the repository's own changelog is the one input guaranteed to be correct, and a check that only ever saw it would pass forever. The three refusals correspond to the three ways the stub survives, and the duplicate-heading one is first because it is the shape the defect actually had; the other two would each have been satisfied by a half-edit. The negative case is asserted twice, on a planted older section and on the real file, because the failure mode of over-scoping is a check the archive can only be edited to satisfy.
      - Scope check: `git status --short` shows `scripts/validate_plugin.py` — this task's only Touch entry — plus this change's own directory. The Stop Rule held: `release_description_problem` takes text and a version and never reads a path, which is what made all four planted fixtures possible.
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
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, and passes against a changelog whose stub this release filled in rather than left standing — this release is the first one the new rule judges
    - M2: `keel/CHANGELOG.md` carries an entry recording that the stub was what satisfied the check, that it happened in the two releases immediately before this one with the suite green both times, and why `bump_version.js` keeps writing the stub
    - M3: the delta is promoted, `node node_modules/.bin/openspec validate a-release-describes-itself --strict` passes, and `published-specs-validate-strictly` passes
    - M4: `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the new rule refuses this release's own changelog for a reason the entry cannot fix.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d843e5217b083e0b82cfa4b074c9853a54b834b8dc4393eaa49ae6b815030dc2
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes; every marker moved 5.68.0 to 5.69.0 via `node scripts/bump_version.js minor`. It passes against a changelog whose stub this release filled in rather than left standing, which is the point worth recording: 5.69.0 is the first release the new rule judges, and it judged it. Between the bump and the entry being written the scenario was refused — the stub heading was there — so the green is the rule working on its own release rather than a green it was handed. The Stop Rule held: nothing in the entry was written to satisfy the rule in a way the entry could not honestly say.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.69.0 - a release describes itself`. It records that the stub was what satisfied the check and why — it carries the `Version alignment:` line the scenario reads; that it happened in 5.67.0 and 5.68.0 with the suite green both times and was found by eye three commits later; the three refused shapes and why the duplicate-heading one is checked first; both scoping decisions, including that this file quotes the token when describing the rules that refuse it; why `bump_version.js` keeps writing the stub; and why the rule takes text rather than a path.
    - M3: pass. The delta is promoted into `openspec/specs/keel-validation-runner/spec.md`. `node node_modules/.bin/openspec validate a-release-describes-itself --strict` reports valid, and `published-specs-validate-strictly` passes inside `npm test`.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 181 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all, and this time that scenario also judges the entry M2 is about — the two checks meet on the same file, which is the closest this change gets to proving itself in production. M3 asserts the promotion through both consuming tools. M2's bar was that the entry records the *mechanism*, not the incident: a reader who learns only "two stubs were left behind" will read it as carelessness, when the fact worth carrying is that the unfilled stub was what passed the check.
      - Scope check: `git status --short` shows the version markers, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, and the promoted spec, plus `scripts/validate_plugin.py` declared complete by 1.1 and this change's own directory.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "`## <version> - TODO: summarize this release`" and "`- TODO: describe the change.`" — the stub
  text `scripts/bump_version.js` writes into `keel/CHANGELOG.md`. The text does not move and stops
  being something a release can carry to completion, which changes what a reader should conclude from
  seeing it: previously a habit, now a refusal.
  Updated by: 1.1
- I2: "Version alignment: the npm package, both native plugin manifests, protocol docs, and this
  changelog share Keel <version>" — the line every changelog section ends on. It stays exactly as it
  is and stops being the only thing `version-alignment` reads about a section, which is the property
  that let an unfilled stub pass.
  Updated by: 1.1

## Expectation Coverage

- E1: A release whose section is an unfilled stub is refused, naming the line (D2, D3, F1).
  Covered by: 1.1
- E2: Two sections for one version are refused — the shape the real defect had (D2). Covered by: 1.1
- E3: Only the version being released is judged, so the archive cannot fail the check (D1).
  Covered by: 1.1
- E4: Whether `bump_version.js` should stop writing the stub (D4). Discard reason: deliberately not
  done rather than deferred. The stub carries the `Version alignment:` line the check reads, so
  removing it would let an author who wrote no entry at all pass with no section, and the check would
  then have to distinguish absent from unfilled — the same defect with less on screen.

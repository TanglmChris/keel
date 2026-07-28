## 1. The bootstrap says what Touch actually bounds

- [x] 1.1 Name the record-write exemption, and pay for it by listing one opt-out
  - Covers:
    - keel-openspec-surface-overlay / The consumer bootstrap names the record-write exemption / A consumer learns the exemption from the bootstrap alone
    - keel-openspec-surface-overlay / The consumer bootstrap names the record-write exemption / The block stays within its budget
    - F1 the exemption fits at 1012 bytes when only one guard opt-out is listed
    - D1 the second opt-out is the lower-value sentence
  - Touch:
    - assets/bootstrap/AGENTS.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a consumer repository installed by `keel --install` receives a bootstrap that states both that Touch bounds product writes and that the change's own directory is exempt, and the installed block measures under the unchanged 1024-byte and 12-line budgets
    - M2 (regression): the resident-block required entries all still match, including the `Touch … bound` topic pattern that the rewording moves, and `keel guard clear` remains a real command outside the bootstrap
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:cbafaff2fd2d4c67e6043abd6375388fcece841f37d20bba18f5dba83859c57f
    - M1: pass. `thin-native-install` now reads the block a real `keel --install` writes into a temporary repository and requires two things of it: a statement of what Touch bounds, and the record-write exemption named outright. The installed block measures **1012 bytes and 9 lines** against the unchanged 1024-byte and 12-line budgets, so the budget was not touched — the room came from listing `--no-guard` alone. The sentence now reads "Touch bounds product writes; the change's own dir is exempt."
    - M1.red: with the old wording in place, the new assertion failed `bootstrap does not name the record-write exemption, so a consumer still infers that tasks.md belongs in Touch` — the misreading issue #8 reported, reproduced against the shipped surface rather than argued about.
    - M1.green: the sentence rewritten; both assertions pass and the block is 4 bytes smaller than before, not larger.
    - M2: pass. Every resident-block required entry still matches, the `Touch … bound` topic pattern included — which is the whole point of 5.3.1's topic matching, since this rewrite moved the wording the pattern covers. `keel guard clear` is unchanged as a command; only the bootstrap stopped spending bytes naming it.
    - M2.red: two existing checks caught the rewrite, both correctly. `resident-topic-matching` failed `the fixture's anchor sentence is not in the bootstrap; update this scenario alongside the wording` — the scenario asking to be updated with the sentence it pins, which I1 had declared. `touch-guard-surface` failed `bootstrap does not mention the guard`, because dropping `keel guard clear` removed the only literal `keel guard`. That second one was not foreseen in design.
    - M2.green: the pinned anchor moved to the new sentence, and the guard assertion now keys on `--no-guard` plus "guards it by default" — the flag the bootstrap does name stays literal, so renaming it still fails, while the command it no longer names is no longer demanded of it.
    - Review:
      - Status: pass
      - Acceptance check: both checks read the block a real install produces, not the source asset, so a change that does not reach a consumer fails. The two covered scenarios map directly: the exemption assertion to "A consumer learns the exemption from the bootstrap alone", and the measured 1012/9 against unchanged budgets to "The block stays within its budget". The change dropped is named here and in the changelog, as that scenario requires.
      - Scope check: two files changed, both declared in Touch. `npm test` passes with baseline plus 79 scenarios.
      - Findings: `touch-guard-surface` asserted the literal `keel guard` while meaning "the bootstrap tells you the guard exists" — the same literal-versus-topic confusion 5.3.1 fixed for the resident-block check, surviving in a scenario that check does not cover. Rewritten to key on `--no-guard`, which the bootstrap does name. Discard reason: the over-specified assertion was inside this task's Touch and is repaired here; no work is left to own.
    - Blocker: none

## 2. Version alignment stops naming a version and starts being checked

- [ ] 2.1 One derived check over every shipped marker, and a bump that reaches every target
  - Covers:
    - keel-expectation-slice-evidence-gates / Shipped version markers agree with the package version / Every shipped marker matches the package version
    - keel-expectation-slice-evidence-gates / Shipped version markers agree with the package version / The release bump reaches every target
    - keel-expectation-slice-evidence-gates / Shipped version markers agree with the package version / The marker list is derived, not fixed
    - F2 seven version-pinned statements sit in two live specs
    - D2 the requirement is rewritten to the invariant rather than deleted
    - D3 the invariant is enforced by a check and by the bump reaching every target
    - A2 the marker list is derived from what ships, not hardcoded
  - Touch:
    - scripts/bump_version.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a check fails, naming the file, when any shipped version marker disagrees with the package version — demonstrated by leaving one `.codex/` overlay marker behind, which is exactly the state issue #23 recorded twice
    - M2: running the release bump refreshes the overlay markers of every initialized target in one step, so the marker set is uniform immediately afterwards with no manual `keel --install` call
    - M3 (regression): the bump's existing pins still move together and `npm test` stays green at the bumped version, so adding targets did not break the eight pins it already maintained
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - M3: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 3. The fingerprint guarantee states its bound

- [ ] 3.1 Say that an anchor is reverifiable while its change is live
  - Covers:
    - keel-core-gates / A contract anchor is reverifiable while its change is live / A live anchor recompiles to its recorded value
    - keel-core-gates / A contract anchor is reverifiable while its change is live / An archived anchor is a record, not an assertion
    - F3 archiving renames the change directory, which the capsule records in every authority source
    - D4 the bound is documented rather than the reproducibility restored
  - Touch:
    - AGENTS.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a check demonstrates the boundary rather than asserting prose — a task of a live change recompiles to its recorded anchor, and the same task under an archive path does not — and the resident protocol states that bound where it describes recompilation
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Invalidates

- I1: "Touch is the write boundary for product files" — `assets/bootstrap/AGENTS.md`, and the anchor sentence pinned by the `resident-topic-matching` scenario in `scripts/validate_plugin.py`. The qualifier stays, but the sentence is rewritten around it and the scenario's literal anchor must move with it. Updated by: 1.1
- I2: "(`--no-guard`/`keel guard clear` opt out)" — `assets/bootstrap/AGENTS.md`. Only `--no-guard` remains listed there; the command itself is unchanged everywhere else. Updated by: 1.1
- I3: "Keel MUST release … as version `3.0.0`" and "the reported Keel version is `3.0.0`" and "no current generated target asset continues to advertise `2.7.0`" — the live `keel-expectation-slice-evidence-gates` spec. Removed as a requirement and replaced by the version-agnostic invariant. Updated by: 2.1
- I4: "npm and both plugin manifests report base version `4.0.0`" and "version `4.0.0`" in the two manifest scenarios — the live `keel-native-plugin-package` spec. Replaced by "the package version". Updated by: 2.1
- I5: "resume, projection, and completion recompile and compare it" — `AGENTS.md` Completion gates. True while the change is live and silently untrue after archive. Updated by: 3.1
- I6: "**5.3.2 was tagged but never published**, because its whole change was in the plugin script and `bin`/`src` were byte-identical to 5.3.1" — the 5.3.4 entry in `keel/CHANGELOG.md`. Discard reason: still true of 5.3.2, and changelog entries are dated records; 5.3.4 is now publishable for a different reason, which its own entry states.

## Expectation Coverage

- E1: a consumer learns from the bootstrap alone that the change's own directory is writable Covered by: 1.1
- E2: the byte budget holds, so the block does not grow to fit each addition Covered by: 1.1
- E3: no live spec requires a version that has already shipped Covered by: 2.1
- E4: a marker left behind fails rather than waits for someone to grep Covered by: 2.1
- E5: the release bump reaches every target, so the drift cannot recur once per release Covered by: 2.1
- E6: the fingerprint guarantee names the boundary it holds within Covered by: 3.1
- E7: archived anchors remain unverifiable, so the archive cannot serve as a fingerprint-stability corpus. Discard reason: accepted as D4; the only fix would make the displayed `source` name a path that does not exist, and no runtime path recompiles an archived task.
- E8: other kinds of staleness in live specs — prose rather than version literals — are not swept here. Durable owner: https://github.com/TanglmChris/keel/issues/22

# Tasks

## 1. A marker opens its clause

- [x] 1.1 Both disposition-marker scans recognize a marker only where it opens its clause — start of value, line break, or sentence-ending punctuation — and the no-disposition refusal names that requirement
  - Covers:
    - keel-expectation-slice-evidence-gates / A disposition marker is recognized only where it opens its clause / A negated mention is not a disposition
    - keel-expectation-slice-evidence-gates / A disposition marker is recognized only where it opens its clause / A marker opening a clause still parses
    - keel-expectation-slice-evidence-gates / A disposition marker is recognized only where it opens its clause / A marker that opens no clause is refused, not ignored
    - F1
    - F2
    - D1
    - D2
    - D3
    - A1
  - Read:
    - src/core/gates.js
    - openspec/changes/a-negation-is-not-a-marker/design.md
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-negation-is-not-a-marker` scenario drives the real `keel gate task-complete` against a fixture whose `Findings` reads `… Not resolved here: it is a different module … Durable owner: https://example.com/issues/1` — the exact text that produced #144. The task completes, and the output is asserted to contain no diagnostic about resolution evidence. Fails with: `names neither a check nor a path`
    - M2: a fixture whose marker opens the value, one where it follows a line break in wrapped prose, and one where it follows a full stop are each still read as dispositions and still held to their evidence — a `Resolved here:` naming an unknown check is refused in all three positions. Without this the narrowing could pass by recognizing nothing at all. Fails with: `stopped recognizing a real marker`
    - M3: a fixture whose only marker is preceded by a word is refused for carrying no disposition, and the diagnostic names the opening requirement, so an author whose sentence visibly contains a marker is not told to add one. Fails with: `does not name the opening requirement`
    - M4 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario a-quoted-marker-is-not-a-disposition` passes unchanged. Added after that scenario caught a real regression this task introduced: the blanking of a marker inside a quoted span used the same pattern as recognition, and an opening rule stopped it blanking, because inside a span the character before the marker is a backtick. Blanking asks whether text is marker vocabulary; recognition asks whether a marker opens a clause. The two questions now have two patterns.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the rule is implemented by shortening or rewriting the `Findings` text, because F2 records that every rule downstream reads positionally and a shortened copy would move what they read.
    - Stop if only one of the two scans is narrowed, because D2 records that a marker counted as present while supplying no evidence accepts a finding as disposed with nothing behind it.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:2aeb8ac9990bc37cf2a3bd96fdb804406047fcf874e051da718f4677df09f42f
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-negation-is-not-a-marker` reports `a-negation-is-not-a-marker scenario passed.` A fixture whose `Findings` reads `… Not resolved here: it is a different module … Durable owner: https://example.com/issues/1` — the shape that produced #144 — completes through the real `task-start --record` then `task-complete`, and the output is asserted to carry no resolution-evidence diagnostic, so the negated phrase is not merely tolerated but not read as a claim at all.
    - M1.red: fail, reproducing #144 exactly. `a-negation-is-not-a-marker: names neither a check nor a path — a finding saying it was *not* resolved here, closing with a durable owner, was refused; ['finding-resolution-evidence'] 'Review Findings records a finding as resolved here, but its evidence is not usable — it read \`it\`, which names neither a check nor a path.'` Carries the declared signature `names neither a check nor a path`.
    - M1.green: pass. Same command after both marker scans required a clause opening.
    - M2: pass. The positive control, in all three opening positions: a `Resolved here: M9` naming a check the task does not declare is refused, and the refusal names `M9`, when the marker opens the value, follows a line break in wrapped prose, and follows a full stop. Asserted on the cited label appearing in the diagnostic rather than on the refusal alone, because a refusal for some other reason would satisfy a bare status check.
    - M2.red: fail, for the declared reason, taken by over-narrowing the rule to `(?<=^)` — only the value's own start opens a clause. `a-negation-is-not-a-marker: stopped recognizing a real marker (after-break) — the refusal does not name the cited check` followed by the no-disposition refusal, which is exactly the shape of the failure: the marker after the line break stopped being seen, so the finding read as carrying no disposition. Carries the declared signature `stopped recognizing a real marker`. Without this control the narrowing could have passed by recognizing nothing anywhere.
    - M2.green: pass. Same command with the opening class restored.
    - M3: pass. A fixture whose only marker is preceded by a word is refused, and the diagnostic names the requirement — `A marker counts only where it opens its clause — after the start of the value, a line break, or sentence-ending punctuation. This text mentions one mid-sentence, so it was read as prose`. The sentence is added only where a marker is visibly present and was not counted, which is the one case where "carry a disposition" contradicts what the author can see they wrote.
    - M3.red: fail, for the declared reason, with the conditional sentence suppressed: `does not name the opening requirement — an author whose sentence visibly contains a marker is told to add a disposition`, followed by the unextended refusal. Carries the declared signature `does not name the opening requirement`. **This check was vacuous before the red was taken and the red is what exposed it:** the assertion first looked for `opens`, which matches inside `openspec/changes/archive/…` — a path the same diagnostic already prints — so it passed against a message that said nothing about the rule. It now asserts the phrase `opens its clause`. The precedent `an-assertion-that-never-failed-proves-nothing` applied to this task's own work.
    - M3.green: pass. Same command with the sentence restored.
    - M4: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-quoted-marker-is-not-a-disposition` reports `a-quoted-marker-is-not-a-disposition scenario passed.` `npm test` reports `validation --all passed: baseline plus 177 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a negated mention is not a disposition, that a real marker still parses, and that a swallowed one is refused with a reason. M1 proves the first against the exact text that produced the issue, driven through both gates. M2 is the control that keeps M1 honest — a narrowing that recognized nothing would satisfy M1 perfectly — and it is asserted in all three legitimate opening positions rather than one. M3's history is the part worth reading: the check passed before its red was taken, and only taking the red revealed that `opens` was matching inside `openspec`. Two of this task's four checks were therefore corrected by the act of making them fail, which is the whole argument for taking reds one at a time.
      - Scope check: `git status --short` shows `src/core/gates.js` and `scripts/validate_plugin.py` — exactly this task's Touch — plus this change's own untracked directory. Both Stop Rules held: the rule is a lookbehind, so no text is shortened or rewritten and every downstream positional read is unmoved; and both scans were narrowed together. One regression was introduced and caught by the suite rather than by me: narrowing the pattern that *blanks* a quoted marker stopped it blanking, because inside a backtick span the preceding character is a backtick. Blanking asks whether text is marker vocabulary and recognition asks whether a marker opens a clause; those are now two patterns, and M4 was added to the contract so the check that caught it is declared rather than incidental.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: M4 was added mid-task, and the contract re-recorded with `--keep-evidence M1,M3` — those two checks' texts did not move, which is the claim Keel records and does not verify. The reason it was added: `a-quoted-marker-is-not-a-disposition` turned red on a regression this task introduced, and the contract had no check standing for the property it guards. Declaring it after the suite found it is worse than declaring it first and is better than leaving the contract silent about the one check that caught the defect.

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a negated mention is not a disposition
    - E2 — a marker opening a clause still parses and is still held to its evidence
    - E3 — a marker that opens no clause is refused rather than ignored
    - I1
  - Read:
    - keel/CHANGELOG.md
    - openspec/specs/keel-expectation-slice-evidence-gates/spec.md
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
    - openspec/specs/keel-expectation-slice-evidence-gates/spec.md
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
    - Reason: this task's whole effect is version markers, a changelog entry, and promoted spec text. The behavior was proven red-green in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes
    - M2: `keel/CHANGELOG.md` carries an entry quoting the refused text and the diagnostic it produced, and stating that the narrowing cannot pass silently
    - M3: the delta is promoted, `node node_modules/.bin/openspec validate a-negation-is-not-a-marker --strict` passes, and `published-specs-validate-strictly` passes
    - M4: `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:c9e8440c43eb985a0ee5c126110818d809a0d771cccf5083dcfd0ff886a5b356
    - M1: pass. `version-alignment` passes; every marker moved 5.64.0 to 5.65.0 via `node scripts/bump_version.js minor`. The Stop Rule held.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.65.0 - a negation is not a marker`, quoting the refused text and the pattern that matched it, naming the inversion plainly — a dismissal read as a repair, then refused for lacking repair evidence — and stating that the narrowing cannot pass silently and what the loud refusal says. It also records the regression this change introduced and its own suite caught, rather than leaving that only in the task Evidence.
    - M3: pass. The delta is promoted into `openspec/specs/keel-expectation-slice-evidence-gates/spec.md`. `node node_modules/.bin/openspec validate a-negation-is-not-a-marker --strict` reports valid, and `published-specs-validate-strictly` reports `24 published specs validate strictly against openspec 1.6.0.`
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 177 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: M1 reads the markers through the scenario that checks them all. M3 asserts the promotion through both consuming tools, strict in both. M2's job here is that the entry records the regression as well as the fix: a reader who only learns the rule would narrow the next marker pattern the same way and break the same blanking.
      - Scope check: `git status --short` shows the version markers, `keel/CHANGELOG.md`, the promoted spec, and `src/core/gates.js` plus `scripts/validate_plugin.py` declared complete by 1.1, plus this change's own untracked directory.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "A quoted marker is a quotation, not a disposition" and the positional rationale beneath it —
  the comment above `DISPOSITION_MARKER` in `src/core/gates.js`. It stays true and stops being the
  whole rule: quoting was the first way a marker could appear without being one, and negating it is
  the second.
  Updated by: 1.1
- I2: "Measured on this change's own task 1.3. That block used to be one line and may now wrap across
  several" — the comment above the resolution capture in `src/core/gates.js`. It explains why the
  capture is narrow and says nothing about where the marker may begin, which is the property this
  change adds.
  Updated by: 1.1
- I3: "a path counts only when it follows `Durable owner:`, because mentioning the file a finding
  concerns does not give that finding an owner" — this repository's `## Project Conventions` in
  `AGENTS.md`. It stays correct: this change narrows where a marker is recognized and changes nothing
  about what follows one.
  Discard reason: the wording is correct after this change.

## Expectation Coverage

- E1: A negated mention of a marker is not a disposition, and nothing is demanded of the word following it (F1, D1). Covered by: 1.1
- E2: A marker opening a clause — at the value's start, after a line break, or after sentence-ending punctuation — still parses and is still held to its evidence (F2, D1). Covered by: 1.1
- E3: A marker that opens no clause is refused rather than ignored, and the refusal names the requirement (D2, D3). Covered by: 1.1
- E4: The published spec and every version marker move with the behavior (I1, I2). Covered by: 2.1
- E5: Whether a marker after a closing bracket or quotation mark should open a clause (A1). Discard reason: deliberately not done rather than deferred. Sentence-ending punctuation is approximated by a character class rather than parsed, no such form exists in this repository's archive, and D3 guarantees the consequence is a loud refusal naming the requirement — recoverable in one edit. Parsing English sentence structure to widen it would be a far larger claim than this change makes.

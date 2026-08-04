# Tasks

## 1. The extent

- [x] 1.1 A Review entry is read as the text the author wrote under its label
  - Covers:
    - keel-core-gates / A Review entry is the text written under its label / A durable owner below the first line is read
    - keel-core-gates / A Review entry is the text written under its label / A finding written below a none first line is not invisible
    - keel-core-gates / A Review entry is the text written under its label / A Review entry stops at its sibling
    - keel-core-gates / A Review entry is the text written under its label / An unwrapped Review entry is unchanged
    - D1 — the entry ends at the next sibling label at the same or shallower indentation
    - D2 — the bound is computed inside `reviewValue()` and no caller changes
    - D3 — no accepted form, diagnostic code, or message text changes
    - D5 — `fieldValues()` and every list-shaped field keep their line-wise splitting
    - D6 — both directions plus the sibling bound are driven through `task-complete`
    - D7 — the sibling-bound check is proven able to fail by mutation
    - D8 — the block read applies to all four entries, and `Status` is the one newly-refusing edge
    - F1 — the reported defect reproduces at 5.27.0
    - F2 — the same text on one line passes, so the cause is the line
    - F3 — the continuation lines already reach `reviewValue()` and are dropped there
    - F4 — the same defect also fails open, which #49 does not report
    - F5 — 0 of 640 archived Review entries wrap
    - A1 — a deeper-indented `-` line is a continuation, not a sibling
  - Read:
    - src/core/gates.js
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - openspec/changes/a-review-field-is-what-the-author-wrote/design.md
    - openspec/changes/a-review-field-is-what-the-author-wrote/specs/keel-core-gates/spec.md
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: the reported defect is gone, measured the way #49 measured it. On a scratch repository whose Review `Findings` wraps across four indented lines with `Durable owner:` naming an existing path on the last of them, `keel gate task-complete` reports no `finding-owner` problem, and the identical text joined onto one line reports the same verdict and the same problem set. The comparison is against the joined form rather than against a remembered list, so a change that broke both forms equally cannot pass it.
    - M2: the fail-open direction is closed. On a scratch repository whose Review `Findings` reads `none` on its first line and records a finding with no disposition on the lines below it, `task-complete` returns a `finding-owner` problem naming the field. This is the cell that returned no problem at all at 5.27.0.
    - M3 (regression): a Review entry does not absorb its sibling. With a wrapped `Findings` that carries no disposition of its own, followed by a sibling entry whose text would satisfy the owner check, `task-complete` still refuses it — so widening the read did not let one entry be satisfied by another's text. Proven able to fail by aiming a mutation at the sibling bound, which must turn this check red rather than leave it green.
    - M4 (regression): every unwrapped Review entry is unchanged. A task whose four Review entries each occupy one line produces the same verdict, problem codes, and message text as it did before the bound gained its continuation lines, compared against recorded pre-change values rather than against a fresh run of the same build.
    - M5 (regression): `npm test` passes with no failing scenario and no exception, so no existing fixture was passing because a Review entry was truncated at its first line.
    - M6 (regression): `assertion-shape-count` passes at its recorded number, so the added assertions did not put several failures behind one message.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the fix requires changing an accepted form, a diagnostic code, or any message text. This change moves how much text is read; it does not renegotiate the vocabulary. D3.
    - Stop if the fix requires changing `fieldValues()`, `field()`, or `parseTasks()`. Those readers serve list-shaped fields including `Touch`, which the write guard compiles, and changing them is D5's non-goal.
    - Stop if making a check pass requires exempting one of the four Review entries from the block read. That is D8, and a per-field special case is the owner's call.
    - Stop if any unwrapped-entry verdict has to change to make a wrapped-entry cell pass. Unwrapped is the shape all 640 archived entries use.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:7ef6f2599ae64080275e85a9ac11328037dad5af1f8c81973aff1495b83b53c4
    - M1: pass. The `review-entry-extent` scenario writes the same finding twice into one repository — wrapped across four indented lines with `Durable owner: openspec/changes/demo/tasks.md` on the last, and joined onto one line with no word changed — and drives `keel gate task-complete` against each. Neither reports a `finding-owner` problem, and the two forms' sorted problem codes are equal. The pair comparison is not the proof on its own, so each form is also pinned absolutely: no `finding-owner` in either. Confirmed independently through the shipped CLI on a scratch repository built from #49's own listing, where `node bin/keel.js gate task-complete --change demo --task 1.1` reported the refusal before and reports none after.
    - M1.red: fail, at 5.27.0 with `reviewValue()` untouched. `review-entry-extent refused a durable owner the author recorded, with the finding written wrapped. The owner is named after `Durable owner:` and the path exists.` followed by the full `finding-owner` message. This is the shipped state rather than a mutation: it is the defect #49's first supplement reports, reproduced through the gate.
    - M1.green: pass, after `reviewValue()` collected the entry's continuation lines up to the next sibling entry. The joined form's verdict did not move, which is what makes the wrapped form's change attributable to the read rather than to the check.
    - M2: pass. A Review whose `Findings` reads `none` on its first line and records an unowned finding on the two lines below it is refused with `finding-owner`. The cell asserts the problem is present rather than asserting a count, because the failure it guards against is silence.
    - M2.red: fail, at 5.27.0 — and the failure is a silence, not a wrong answer. `review-entry-extent accepted a finding written below a `none` first line. The gate read the word `none` and not the finding under it.` and the reported problem list was `[]`. The M1 cell had to be neutralized to reach this one, since it fails first at 5.27.0; the neutralization was a temporary `if False and …` on M1's two guards, reverted immediately, and `grep -c "False and" scripts/validate_plugin.py` returns `0`. This half is not in #49; it was found by reading the code the issue points at.
    - M2.green: pass, with the same widened read that turned M1 green and no check of its own. The value `Findings` now carries is `none` followed by two lines of findings, which no longer matches `/^none\.?$/i`, so the disposition check runs on text it previously never received. Nothing in the owner vocabulary changed to make this cell pass.
    - M3: pass, and proven able to fail rather than assumed. A wrapped `Findings` carrying no disposition, followed by a `- Blocker:` entry whose text names an existing path after `Durable owner:`, is still refused — the sibling's text does not satisfy the entry above it. This cell passes at 5.27.0 too, because an entry that is one line cannot absorb anything, so it was aimed at a mutation: changing the bound's `sibling[1].length <= indent` to `>=` leaves the four Review entries bounded by each other while letting `Findings` run past the shallower `- Blocker:`. The scenario went red naming this cell — `review-entry-extent let a `Findings` with no disposition be satisfied by the sibling entry below it.` with the problem list `['blocker']`. A first, blunter mutation — dropping the break entirely — turned **M2** red instead (`['semantic-review']`, because `Status` then swallowed the whole Review), which is why the mutation was narrowed until it struck this cell and no other. Both reverted; `diff` against the recorded green implementation reports the files identical. *Precedent applied: `an-assertion-that-never-failed-proves-nothing`.*
    - M4: pass. A task whose four Review entries each occupy one line still produces exactly one `finding-owner` problem when its finding has no disposition, and none when the finding names an existing path after `Durable owner:`. The message is pinned against five literal phrases written into the scenario — `Review Findings must be `none` or carry a disposition.`, `Resolved here:`, `Durable owner:`, `Discard reason:`, `keel/HANDOFF.md` — rather than compared against another run of the same build, so a change that altered the text in both places would still fail here. This is the shape all 640 archived Review entries use.
    - M5: pass. `npm test` reports `validation --all passed: baseline plus 136 scenarios.` — no failing scenario, no exception, none skipped. 135 before this change and 136 after, measured by stashing the working tree and re-running: one scenario added, `review-entry-extent`. No existing fixture was passing because a Review entry was truncated at its first line. `findings-resolved-here`, the nearest neighbour and the other reader of this text, was re-run by name after the comment edits and reports `scenario passed.`
    - M6: pass. `assertion-shape-count` reports `passed: 75 sites, a bound on a shape and not a count of defects.` — unchanged at its recorded number, because every added assertion is a single condition carrying its own message.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a Review entry is the text the author wrote under its label, and every check measures it the way an author would meet it — through `keel gate task-complete` on real repositories, comparing one finding against itself with only its line breaks moved. Nothing here asserts the shape of `reviewValue()`; a unit test of the extractor would have proved the half that was never in doubt. Two things are worth stating plainly. First, the pair comparison in M1 is not the proof: it passes when both forms are refused identically, so each form is also pinned absolutely. Second, the half that matters most is the one #49 does not report. The reported direction costs an author a puzzled minute; the silent one at M2.red let a finding with no owner pass `task-complete` because the word above it said `none` — the gate whose subject matter is finding ownership, failing open on it. That cell is the reason D1 widened the read for all four entries instead of special-casing the one the issue names.
      - Scope check: `git status --short` shows `src/core/gates.js` and `scripts/validate_plugin.py` — the Touch list exactly — plus this change's own untracked directory, which is the record-write layer. Both files were clean when the task started, so deterministic attribution covers every write. `keel guard status` reports the fingerprint `sha256:7ef6f2599ae64080275e85a9ac11328037dad5af1f8c81973aff1495b83b53c4`, unchanged from the one recorded at task-start, so no contract edit occurred. Every write to a product file went through the editing tools; no heredoc was used, so the write guard saw each one. The two Python heredocs in this session wrote only to `/tmp` scratch repositories, outside the repository entirely. Three temporary mutations were made to obtain the red and control measurements above — two `if False and …` guards in `scripts/validate_plugin.py` and one inverted comparison in `src/core/gates.js` — and all three are reverted: `grep -c "False and" scripts/validate_plugin.py` returns `0`, and `diff` against the recorded green implementation reports `src/core/gates.js` identical to it.
      - Findings: two. First, the mutation aimed at the sibling bound initially struck the wrong cell: dropping the break entirely turned M2 red rather than M3, because `Status` is the first of the four entries and an unbounded read makes it swallow the other three, which fails the Review before the Findings check is ever reached. The blunt mutation therefore proved that *some* bound is load-bearing without proving that M3 watches it. Narrowing the mutation to invert the comparison — which leaves the four entries bounding each other and only frees `Findings` past the shallower sibling — is what made M3 the cell that went red. Recording this because the first result looked like a successful mutation test and was not one. Resolved here: M3. Second: `AGENTS.md` still calls the Review `Findings` a line, in the sentence an agent reads before writing one, so the resident protocol contradicts what this task ships. It is declared as I3 and is not this task's to write — `AGENTS.md` is outside 1.1's Touch and inside 2.1's. Durable owner: openspec/changes/a-review-field-is-what-the-author-wrote/tasks.md
    - Blocker: none
  - Stop if:
    - Requires files outside Touch.

## 2. Close

- [x] 2.1 Release 5.28.0
  - Covers:
    - E5 — a reader of the release notes learns that the defect failed in both directions and that `Status` is the one place the wider read newly refuses
    - I3, I4 — the wordings this change makes stale
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
    - scripts/validate_plugin.py
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
    - openspec/specs/keel-core-gates/spec.md
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every shipped version marker names 5.28.0
    - M2: `keel/CHANGELOG.md` carries a 5.28.0 entry naming both failure directions, that the wider read applies to all four Review entries, that `Status` is the one place it newly refuses, and why `Verify`'s line-wise splitting was left alone
    - M3: `AGENTS.md` no longer calls the Review `Findings` a line, so the resident protocol does not contradict the behavior this release ships
    - M4: the spec delta is promoted into `openspec/specs/keel-core-gates/spec.md`, `node bin/keel.js openspec validate a-review-field-is-what-the-author-wrote --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M5: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:179fbca1501e57b7ee05aaaf9419220fc54fece11e9460da54a39c4e5e922ad0
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.27.0 to 5.28.0 through `node scripts/bump_version.js 5.28.0` — the package and lockfile, both plugin manifests, the three `keel:start` blocks in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, the `AGENTS.md` title and its preflight line, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`. The scenario reads every marker rather than sampling, so one left at 5.27.0 fails by path. Spot-confirmed in the file a reader meets first: `AGENTS.md:1` is `# Keel v5.28.0 Agent Protocol` and `AGENTS.md:3` is `<!-- keel:start version=5.28.0 -->`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.28.0 - a review field is what the author wrote`. It names both failure directions and keeps them apart — the reported one, where a `Durable owner:` on the fourth line was refused with the owner present and the path existing, and the silent one, where a `Findings` reading `none` above two unowned findings produced no problem at all. It records that the widened read covers all four Review entries and why the one the issue names was not special-cased; that `Status` is the one place the wider read newly refuses rather than newly accepts, stated rather than left to be discovered; that no accepted form, code, or message moved, with the 640-entry measurement that makes the archive provably unmoved; that `Verify`'s line-wise splitting is a separate reader and was deliberately left alone, with its own reproduction at 5.27.0; and that the sibling bound's first mutation went red on the wrong cell, which is the part a future reader would otherwise have to rediscover.
    - M3: pass. `grep -c "Review \`Findings\` line" AGENTS.md` returns `0`. The **Recording a finding on a task** convention now reads "the Review `Findings` entry — which is the whole text you write under that label, wrapped across as many lines as the finding needs, not just its first line". This was I3: the sentence an agent reads at session start before writing a finding, whose word `line` is the instruction that produced the reported failure.
    - M4: pass. The delta is promoted: `A Review entry is the text written under its label` and its four scenarios now sit at the end of `openspec/specs/keel-core-gates/spec.md`. It is an ADDED requirement, so the promotion is an append and no published requirement was rewritten. `node bin/keel.js openspec validate a-review-field-is-what-the-author-wrote --strict` reports `Change 'a-review-field-is-what-the-author-wrote' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the store now holding it.
    - M5: pass. `npm test` reports `validation --all passed: baseline plus 136 scenarios.` — no failing scenario, no exception, none skipped. Run after the version bump, the changelog entry, the `AGENTS.md` wording, and the spec promotion, so it covers this task's writes and not only 1.1's.
    - Review:
      - Status: pass
      - Acceptance check: each check names the artifact a reader would open. M1 is the scenario that reads every version marker rather than spot-checking, which is what makes "every marker names 5.28.0" a measurement instead of a claim, and the two `AGENTS.md` lines are quoted because they are the ones a session reads aloud at start. M4 asserts the promotion through the two tools that consume the published store rather than by reading the file back. M3 is a grep for the absence of the exact phrase `## Invalidates` quoted, so it fails if the sentence returns in any form that still calls the entry a line. M2 is the one prose check, and it carries what the diff cannot: that this defect had two directions with opposite signs, that the silent one is the worse and is not in the issue, and that `Status` moves in the refusing direction. A future reader who did not know that last part would meet a newly-refused wrapped `Status` and read it as a regression rather than as the decision it was.
      - Scope check: `git status --short` shows twenty-three paths — this task's twenty-two Touch entries plus `src/core/gates.js` from task 1.1 — and this change's own untracked directory, which is the record-write layer. `keel guard status` reports the fingerprint `sha256:179fbca1501e57b7ee05aaaf9419220fc54fece11e9460da54a39c4e5e922ad0`, unchanged from the one recorded at 2.1's task-start, so no contract edit occurred. The gate's limit here is the one every release task in this repository hits: `scripts/validate_plugin.py` was already dirty when 2.1 started, carrying 1.1's scenario, so deterministic attribution cannot speak to it and this Review is its scope evidence. 2.1's own write to that file is the two version constants `bump_version.js` reported changing, and M1 is what verifies them; 2.1 wrote nothing to `src/core/gates.js`, whose diff remains the `reviewValue()` replacement and one comment recorded under 1.1. Every write went through the editing tools or `scripts/bump_version.js`; no heredoc wrote to any repository file.
      - Findings: two, and this entry is deliberately written in the wrapped form
        the release ships, so that passing this gate is itself an end-to-end
        proof of the behavior rather than a claim about it.
        First: #49's second supplement is reproduced and not fixed. A
        continuation line under a `Verify` check — `- M1: …` followed by an
        indented italic note — is refused as `invalid-command-label` at 5.27.0,
        because `fieldValues()` maps every line to its own entry. It is the same
        symptom through a different reader, and D5 declined to touch it here:
        `Verify`, `Covers`, and `Touch` read entry lists, and `Touch` is what the
        write guard compiles.
        Second: #49's §1 and §2 remain open. §1 — a bare `D<n>` in `Covers`
        reported as `Missing` — is an acceptance decision already escalated to
        the owner on the issue and still unanswered; §2 asks that the
        `finding-owner` message lead with its imperative, which D4 declined so
        that this change's one message edit could not be confused with a
        behavior change.
        Durable owner: https://github.com/TanglmChris/keel/issues/49
    - Blocker: none
  - Stop if:
    - Requires files outside Touch.

## Invalidates

- I1: "Findings is one line of free prose that normally holds several findings with different dispositions, so a capture reaching to the newline swallows every marker after it" — the comment above `RESOLVED_HERE` in `src/core/gates.js`. The decision it records stays correct: the capture is still the single token after the marker. Its stated reason does not, because after this change a `Findings` is exactly what that sentence says it is not, and a reader who searches the phrase finds the code justified by a premise the same file no longer holds. Updated by: 1.1
- I2: "dispositions, all in one line of free prose" — the comment introducing the mixed-disposition cell of the `findings-resolved-here` scenario in `scripts/validate_plugin.py`. It explains what that cell is aimed at, and after this change the shape it calls the normal one is merely the common one. Updated by: 1.1
- I3: "cite the issue URL directly in the Review `Findings` line" — the **Recording a finding on a task** convention in `AGENTS.md`. It is the sentence an agent reads at session start before writing a finding, and the word `line` is the instruction that produced #49's reported failure: an author who wraps a long finding is following the protocol as written and is refused. Updated by: 2.1
- I4: "version=5.27.0" — grep it and you find the `keel:start` managed block in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, plus the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`; the same version is written as a `"version"` field in `package.json`, `package-lock.json`, and both plugin manifests, in the `AGENTS.md` title and its preflight line, and in the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants of `scripts/validate_plugin.py`. Updated by: 2.1

## Expectation Coverage

- E1: A durable owner the author recorded below the first line of a wrapped `Findings` is accepted, because the gate reads it. Covered by: 1.1
- E2: A finding recorded below a `none` first line is judged rather than discarded, so the gate cannot pass a task by reading less than the author wrote. Covered by: 1.1
- E3: Reading an entry whole never lets it be satisfied by the text of the entry below it. Covered by: 1.1
- E4: Every Review entry that occupies one line — all 640 in the archive — keeps the verdict, code, and message it had. Covered by: 1.1
- E5: A reader of the release notes learns that this defect ran in both directions, that the wider read covers all four Review entries, and that `Status` is the one place it newly refuses rather than newly accepts. Covered by: 2.1

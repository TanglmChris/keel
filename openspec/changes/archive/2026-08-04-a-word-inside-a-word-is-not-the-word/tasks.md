# Tasks

## 1. The extent

- [x] 1.1 The check reads a word as a word, and reads a citation as a citation
  - Covers:
    - keel-stateless-continuity / A context word is a word and not a substring / A word that merely contains a context word supplies no context
    - keel-stateless-continuity / A context word is a word and not a substring / An inflected context word still supplies it
    - keel-stateless-continuity / A context word is a word and not a substring / A Chinese context word needs no boundary
    - keel-stateless-continuity / A Covers citation is not a record of what it cites / A citation naming a requirement about dirty state is accepted
    - keel-stateless-continuity / A Covers citation is not a record of what it cites / The exemption is the field and not the label
    - keel-stateless-continuity / A Covers citation is not a record of what it cites / Prose outside the Covers field is still refused
    - D1 — the ASCII words gain boundaries and keep their inflections
    - D2 — the Chinese words stay unbounded because a boundary breaks them
    - D3 — the exempt region is the field as the contract compiler bounds it
    - D4 — the exemption covers both rule families
    - D6 — every accepted fixture is paired with a refused one
    - F1 — all four shapes reproduce at 5.28.0 through the CLI
    - F2 — 12 refusals become 8, and the 4 that go were fingerprints
    - F3 — 11 Covers lines in this repository's history are refused today
    - F5 — every Covers citation is written below the label, never on it
    - F6 — the parser's own field bound
  - Read:
    - scripts/install_to_repo.py
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - openspec/changes/a-word-inside-a-word-is-not-the-word/design.md
    - openspec/changes/a-word-inside-a-word-is-not-the-word/specs/keel-stateless-continuity/spec.md
  - Touch:
    - scripts/install_to_repo.py
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a word that merely contains a context word supplies none. On a scratch repository whose active `tasks.md` carries a `sha256:` anchor beside the word `remaining` and another beside the word `heading`, `node bin/keel.js --check` reports `keel state: ok` and no `state-error` names either line. Paired in the same repository with the control that makes the pass mean something: an identifier-length hexadecimal token beside each of `committed`, `commits`, and `hashes` is still refused and each names its line, so a run where the rule stopped firing altogether fails this check instead of passing it.
    - M2: a citation is not a record. On a scratch repository whose active `tasks.md` has a `Covers` field citing the two requirement names in this task's own third and fourth Covers entries — one naming the worktree state git owns, one naming the identifier this rule is about — `--check` reports `keel state: ok` and no `state-error` names any line of that field. Paired with the control: the same two wordings written into an `Evidence` line of the same task are still refused and named, so the exemption is the field and not the file. Measured a second time on this repository itself, whose own `tasks.md` — this one — cites both requirement names and is therefore a live instance rather than a fixture built to be one.
    - M3 (regression): the Chinese wording rules are untouched. The three Chinese fixtures already shipped — the two recorded-commit-state lines the `decimal-runs-are-not-hash-shaped` scenario asserts and the merge-state line of the `cli` scenario's `status-drift` fixture, which has asserted this rule since the initial commit — are each still refused, asserted in this change's own scenario as well so the check names the boundary decision that would break them. D2 is that decision, and a silently disabled Chinese rule looks exactly like a rule nobody wrote a fixture for.
    - M4 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario decimal-runs-are-not-hash-shaped` passes, so the token criterion 5.19.0 shipped is unmoved, and `--scenario cli` passes, so the `status-drift` fixture that has asserted this check since the initial commit still fails the way it did.
    - M5 (regression): `npm test` passes with no failing scenario and no exception.
    - M6 (regression): `assertion-shape-count` passes at its recorded number, so the added assertions did not put several failures behind one message.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if repairing either rule requires changing `_HASH_SHAPED_TOKEN`. The token criterion is 5.19.0's and this change is about which words and which lines, not about what a hash looks like.
    - Stop if a check can only pass by exempting backticked text or by downgrading a refusal to a warning. Those are #65's other two items, declined by 5.19.0's D3, and reopening one is the owner's call.
    - Stop if any true positive in the corpus has to be given up to make a false positive pass. D1 chose the boundary form that pays nothing; a form that pays something is a different decision.
    - Stop if the exemption has to be widened past `Covers` to make a check pass.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:86cb865055fb3e2fb60828b0cc88545692a427cb8a61bda9cf87df1e5ca89c92
    - M1: pass. The `a-context-word-is-a-word` scenario drives `keel --check` on a scratch repository through four host words — `remaining`, `heading`, `domain`, `maintains` — each on its own fixture so a failure names which one, and each carrying an identifier-length token. All four report `keel state: ok`. The control is asserted in the same repository and is what makes that mean something: `commit`, `commits`, `committed`, `committing`, and `hashes` each still produce `keel state: failed` and each refusal names its line. A build where the rule stopped firing altogether fails the control rather than passing the scenario.
    - M1.red: fail, at the shipped 5.28.0 state with `_HASH_CONTEXT_WORD` untouched — not a mutation. `a-context-word-is-a-word: \`remaining\` was read as a context word. It contains one, which is not the same thing, and the token beside it here is a contract anchor. The author's only repair is to reword a line that was correct.` followed by `state-error openspec/changes/reading-lines/tasks.md:11: remove contextual commit hash from tasks.md; git log is the source of truth`.
    - M1.green: pass, after the ASCII alternatives gained `\b` and their inflected forms. The control cases did not move — they were already refused before the change and are refused after — so the four host words' change of verdict is attributable to the boundary and not to the rule being weakened.
    - M2: pass. The `a-covers-citation-is-not-a-record` scenario cites two requirement names published in this repository today — one from `keel-core-gates` naming the worktree state git owns, one from `keel-stateless-continuity` naming the identifier this rule is about — inside a `Covers` field, and `keel --check` reports `keel state: ok` with no `state-error` on any line of that field. Neither name is invented for the fixture; both are cited by archived changes. Measured a second time on this repository itself, which is the stronger of the two: this change's own `tasks.md` cites one of those names, so `node bin/keel.js --check` on the working tree reported `keel state: failed` with one `state-error` naming `openspec/changes/a-word-inside-a-word-is-not-the-word/tasks.md:10` before the fix and reports `keel state: ok` after. That is the defect on the real repository rather than a fixture built to have it.
    - M2.red: fail, at the shipped state. `a-covers-citation-is-not-a-record: a Covers citation was read as a record of the state it names. The entry is a reference to a requirement that has to exist elsewhere, and the only repair open to the author is to rename that requirement.` followed by two `state-error` lines, one per citation.
    - M2.green: pass, after `covers_field_lines()` computed the field with the task contract compiler's own bound and `check_tasks_semantics()` skipped those lines. The Evidence-line control in the same fixture stayed refused across the change, and the refusal is asserted to name the Evidence line and not either citation line, so the exemption is the field rather than the file. The field's end was proven load-bearing by mutation rather than assumed: changing `inside = label.group(1) == "Covers"` to `inside = inside or …`, so the field never closes, turned the scenario red on exactly that cell — `the same wording in an Evidence line was accepted. The exemption is the Covers field, not the file that contains one.` Reverted; `diff` against the recorded green copy reports the file identical. *Precedent applied: `an-assertion-that-never-failed-proves-nothing`.*
    - M3: pass. The three Chinese fixtures are refused in this change's own scenario, on their own fixture each: the two recorded-state wordings and the longer sentence form that embeds one mid-clause. This is the cell D2 exists for — a word boundary around a Chinese context word matches nothing, so the rule would have gone silent rather than wrong, and silence is what no existing fixture would have caught.
    - M4: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario decimal-runs-are-not-hash-shaped` reports `decimal-runs-are-not-hash-shaped scenario passed.`, so the token criterion 5.19.0 shipped is unmoved. `--scenario cli` reports `cli scenario passed.`, so the `status-drift` fixture that has asserted this check since the initial commit still fails on its wording and still passes once cleaned.
    - M5: pass. `npm test` reports `validation --all passed: baseline plus 138 scenarios.` — no failing scenario, no exception, none skipped. 136 before this change and 138 after: two added, `a-context-word-is-a-word` and `a-covers-citation-is-not-a-record`. No existing fixture depended on a substring supplying context or on a citation being read as prose.
    - M6: pass. `assertion-shape-count` reports `passed: 75 sites, a bound on a shape and not a count of defects.` — unchanged at its recorded number, because every added assertion is a single condition carrying its own message.
    - Review:
      - Status: pass
      - Acceptance check: both halves are measured through `keel --check`, the command an author actually runs, on repositories built by `keel --install` — nothing here asserts the shape of a regular expression, which would have proved only that the diff is the diff. Two things are worth stating plainly. First, every accepted fixture is paired with a refused one in the same repository, because a check whose passing condition is acceptance passes just as well when the rule has stopped running; the controls are the inflections for M1 and the Evidence line for M2. Second, M2's stronger measurement is not the scenario but this repository: this change's own `tasks.md` cites a requirement whose name contains the word the rule refuses, so the working tree was a live instance of the defect and went from `keel state: failed` to `keel state: ok` across the fix. The corpus numbers behind the design were re-run against the implementation rather than the proposal: contextual refusals across all 53 `tasks.md` fell from 12 to 8 with none newly refused, and the citations refused inside a `Covers` field — 11 in this repository's history, 12 counting this change's own — are now 0.
      - Scope check: `git status --short` shows `scripts/install_to_repo.py` and `scripts/validate_plugin.py` — the Touch list exactly — plus this change's own untracked directory, which is the record-write layer. Both files were clean when the task started, so deterministic attribution covers every write. `keel guard status` reports the fingerprint `sha256:86cb865055fb3e2fb60828b0cc88545692a427cb8a61bda9cf87df1e5ca89c92`, unchanged from the one recorded at task-start, so no contract edit occurred. One deviation to record rather than leave to be found: the temporary mutation for M2.green was applied with a Python heredoc, so the write guard did not see it even though the file is inside Touch; the revert went through the editing tool, and `diff` against the recorded green copy reports the file identical. Every other write to a product file went through the editing tools. The measurement scripts written during this task live in `/tmp` and touch no repository file.
      - Findings: two. First, found by `keel-review-checklist` after the checks
        were already green: three of the new assertions had one condition
        guarding two distinct failures — `if state != "failed"` fires both when
        the fixture was wrongly accepted and when `keel --check` reported no
        state at all, and it reports the first message in either case, sending
        the reader to a fixture that has no problem in it. The three are the
        Chinese wording cell, the Evidence-line control, and the field-end cell.
        Each is now split, with the no-state case carrying its own message
        saying the check did not reach the point of having a verdict. The
        neighbouring `decimal-runs-are-not-hash-shaped` scenario already had
        this shape and is where the wording came from. `assertion-shape-count`
        passes at 75 both before and after, so it is not what caught this and
        would not have. Resolved here: scripts/validate_plugin.py
        Second, and not this change's own defect but a cost it made visible
        while being authored. Writing this task's `Verify` checks and its `## Invalidates` entries required rewording them three times to get past the very rules being repaired: naming the Chinese fixtures by their literal wording, quoting the stale sentence a reader would grep for, and writing an identifier beside `committed` to describe the control each produced a `state-error` on a line that asserts nothing about this project's commit state. The repairs available were all the same one — say it less precisely — which is exactly the cost #58 named and #65 §2 proposes to fix by exempting backticked text. That item is declined by 5.19.0's D3 and is not reopened here; this is one more measured instance of it, recorded because the `## Invalidates` case is new: the protocol requires quoting the wording that goes stale, and the check refuses the quote. Durable owner: https://github.com/TanglmChris/keel/issues/65
    - Blocker: none
  - Stop if:
    - Requires files outside Touch.

## 2. Close

- [x] 2.1 Release 5.29.0
  - Covers:
    - keel-stateless-continuity / A recorded commit identifier is recognized by what makes it one / Recorded commit wording fails on its own
    - E5 — a reader of the release notes learns that the Covers half is wider than the issue reported and has been costing this project since the initial commit
    - I1, I2, I3 — the wordings this change makes stale
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
    - openspec/specs/keel-stateless-continuity/spec.md
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every shipped version marker names 5.29.0
    - M2: `keel/CHANGELOG.md` carries a 5.29.0 entry naming both halves, the corpus numbers for each, the inflection trade-off the owner decided and what the stricter form would have cost, why the Chinese words keep no boundary, and the residue a Covers exemption accepts
    - M3: the spec delta is promoted into `openspec/specs/keel-stateless-continuity/spec.md` — the two added requirements appended and the modified one replaced in place — `node bin/keel.js openspec validate a-word-inside-a-word-is-not-the-word --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:c0b402914c0cc6228223c64912efad022ab5c061ed96355c9a50707b6db51a2d
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.28.0 to 5.29.0 through `node scripts/bump_version.js 5.29.0` — the package and lockfile, both plugin manifests, the three `keel:start` blocks in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, the `AGENTS.md` title and its preflight line, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`. The scenario reads every marker rather than sampling, so one left behind fails by path. Spot-confirmed in the file a session reads first: `AGENTS.md:1` is `# Keel v5.29.0 Agent Protocol` and `AGENTS.md:3` is `<!-- keel:start version=5.29.0 -->`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.29.0 - a word inside a word is not the word`. It names both halves and keeps them apart; gives each its corpus number — 12 refusals to 8 with none newly refused for the first, 11 lines across 4 changes for the second; records that the second half is wider than #65 reported and that the rules have been in the file since the initial commit, which is why the workaround was cheaper than the report; states the inflection trade-off as a decision with its price, naming what the stricter boundary would have cost and that the owner declined to pay it; explains why the Chinese words carry no boundary and that adding one would have disabled them silently rather than wrongly; states the residue a Covers exemption accepts and what bounds it; and records that #65's other two items stay declined, with the one new measured instance this change produced against the first of them.
    - M3: pass. The delta is promoted into `openspec/specs/keel-stateless-continuity/spec.md`: the two ADDED requirements appended with their six scenarios, and the MODIFIED requirement replaced in place — one sentence gained to its second paragraph, its three scenarios unchanged. `node bin/keel.js openspec validate a-word-inside-a-word-is-not-the-word --strict` reports `Change 'a-word-inside-a-word-is-not-the-word' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the store now holding it.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 138 scenarios.` — no failing scenario, no exception, none skipped. Run after the version bump, the changelog entry, and the spec promotion, so it covers this task's writes and not only 1.1's. `node bin/keel.js --check` on the working tree reports `keel state: ok`.
    - Review:
      - Status: pass
      - Acceptance check: each check names the artifact a reader would open. M1 is the scenario that reads every version marker rather than spot-checking, which is what makes "every marker names 5.29.0" a measurement instead of a claim, and the two `AGENTS.md` lines are quoted because a session reads them at start. M3 asserts the promotion through the two tools that consume the published store rather than by reading the file back, and it is the check that closes I2 — the published sentence that said every line is subject to the wording rules now says which line is not. M2 is the one prose check, and it carries what the diff cannot: that the Covers half is wider than the issue that reported it, that its cost has been paid since the initial commit by renaming requirements rather than by filing a bug, and that the boundary form is a trade-off the owner priced rather than the obvious tightening. A future reader who did not know the last part would meet `commitment` no longer supplying context and read it as an oversight.
      - Scope check: `git status --short` shows twenty-three paths — this task's twenty-two Touch entries plus `scripts/install_to_repo.py` from task 1.1 — and this change's own untracked directory, which is the record-write layer. `keel guard status` reports the fingerprint `sha256:c0b402914c0cc6228223c64912efad022ab5c061ed96355c9a50707b6db51a2d`, unchanged from the one recorded at 2.1's task-start, so no contract edit occurred. The gate's limit here is the one every release task in this repository hits: `scripts/validate_plugin.py` was already dirty when 2.1 started, carrying 1.1's two scenarios, so deterministic attribution cannot speak to it and this Review is its scope evidence. 2.1's own write to that file is the two version constants `bump_version.js` reported changing, and M1 is what verifies them; 2.1 wrote nothing to `scripts/install_to_repo.py`, whose diff remains the context-word expression and the Covers field bound recorded under 1.1. Every write went through the editing tools or `scripts/bump_version.js`.
      - Findings: none
    - Blocker: none
  - Stop if:
    - Requires files outside Touch.

## Invalidates

- I1: "paid in the spec's vocabulary" — the fifth bullet of the 5.19.0 entry in `keel/CHANGELOG.md`, which says the requirement was named as it was because naming it the other way broke every task that cited it. That constraint is what this change removes. Discard reason: a released changelog entry is a dated record of what was true at that release and is not rewritten; the 5.29.0 entry names the reversal, and 2.1's M2 is what checks that it does.
- I2: "independently of any digit run on the line" — the second paragraph of `A recorded commit identifier is recognized by what makes it one` in `openspec/specs/keel-stateless-continuity/spec.md`. Read on its own that sentence says every line of an active tasks.md is subject to the wording rules, and after this change a `Covers` field is not. Updated by: 2.1
- I3: "version=5.28.0" — grep it and you find the `keel:start` managed block in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, plus the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`; the same version is written as a `"version"` field in `package.json`, `package-lock.json`, and both plugin manifests, in the `AGENTS.md` title and its preflight line, and in the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants of `scripts/validate_plugin.py`. Updated by: 2.1

## Expectation Coverage

- E1: A line whose only context word is a substring of an ordinary English word is not refused, and the four such lines in this repository's history are each a contract fingerprint rather than a commit identifier. Covered by: 1.1
- E2: The inflected forms an author writes — `committed`, `commits`, `hashes` — still refuse a hash beside them, so the boundary the owner chose costs no true positive. Covered by: 1.1
- E3: A Covers citation naming a published requirement is accepted whatever words that requirement's name contains, and the same words in evidence prose are still refused. Covered by: 1.1
- E4: The Chinese wording rules refuse exactly what they refused before, because a word boundary would silently disable them. Covered by: 1.1
- E5: A reader of the release notes learns that the Covers half is wider than #65 reported — 11 lines across 4 changes, 8 of them citing published requirements — and that it has been refusing correct citations since the initial commit. Covered by: 2.1

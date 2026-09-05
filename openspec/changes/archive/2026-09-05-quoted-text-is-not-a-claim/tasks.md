# Tasks

## 1. Read only what the author asserts

- [x] 1.1 `check_tasks_semantics()` removes inline code spans, fenced code blocks, and `"…"`/`“…”`/`「…」`/`《…》` quotation spans from a line before the recorded-state patterns and the contextual-identifier pattern read it, leaves the text outside those spans fully read, and does not treat an ASCII single quote as a quotation delimiter
  - Covers:
    - keel-stateless-continuity / A quoted span is a citation and not a claim
    - D1
    - D2
    - D6
    - F1
    - F4
  - Read:
    - scripts/install_to_repo.py
    - scripts/validate_plugin.py
    - src/core/task-contract.js
    - openspec/changes/quoted-text-is-not-a-claim/design.md
  - Touch:
    - scripts/install_to_repo.py
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-quoted-span-is-not-a-claim` scenario in `scripts/validate_plugin.py` drives `keel --check` through the real CLI against an installed fixture repo. `keel state: ok` for each of: an Evidence line whose only match is an inline code span (`` `git status --short` ``), an Evidence line whose only hash-shaped token is inside an inline code span, the same token inside a fenced block, and a prose line naming a requirement `“A recorded commit hash is recognized by what makes it one”` outside any `Covers` field. `keel state: failed`, naming the line, for each of: a line quoting a hexadecimal token and recording `uncommitted` outside the quotes, and a line containing `doesn't` followed by recorded dirty state.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario a-covers-citation-is-not-a-record` passes unchanged, so the field-shaped `Covers` exemption still stands on its own and is not replaced by the span rule.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario decimal-runs-are-not-hash-shaped` passes unchanged, so narrowing what is read did not narrow which tokens count as identifiers.
    - M4 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if removing a quoted span requires changing `is_tasks_rule_line()` or `covers_field_lines()`; those are separate exemptions this task does not touch.
    - Stop if the fenced-block state cannot be tracked without reading the file as a whole rather than line by line, because that changes what `check_tasks_semantics()` reports a line number against.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8812593b6c1474b20500c5a7caddf27354de3db25f17e7c0ddafd070d258760d
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-quoted-span-is-not-a-claim` reports `a-quoted-span-is-not-a-claim scenario passed.` All four quoted fixtures report `keel state: ok` — inline code holding `fatal: you have uncommitted changes`, inline code holding `HEAD is at 3f2a9bc`, a fenced block holding the same output, and a quotation span naming the requirement `A recorded commit hash is recognized by what makes it one`. Both boundary fixtures report `keel state: failed` and name their line — wording outside a quoted span, and a line whose contraction must not open a span.
    - M1.red: fail, for the right reason. The scenario was written and registered before `scripts/install_to_repo.py` was touched, and reported `a-quoted-span-is-not-a-claim: inline code holding quoted output was read as a claim.` with `state-error openspec/changes/reading-lines/tasks.md:11: remove dirty/uncommitted state from tasks.md` — the unmodified checker read the backticked runner output as a claim about this repository.
    - M1.green: pass. Same command after `check_tasks_semantics()` gained the fenced-block skip and `without_quoted_spans()`: `a-quoted-span-is-not-a-claim scenario passed.`
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-covers-citation-is-not-a-record` reports `a-covers-citation-is-not-a-record scenario passed.` unchanged, so the field-shaped `Covers` exemption still holds on its own — including its boundary fixtures, which assert that an Evidence line and a `Verify` line either side of the field are still read.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario decimal-runs-are-not-hash-shaped` reports `decimal-runs-are-not-hash-shaped scenario passed.` unchanged: a decimal run is still not an identifier and a hexadecimal one beside a context word is still refused, so narrowing what is read did not narrow which tokens count.
    - M4: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a line whose every match lies inside an inline code span, a fenced block, or a `"…"`/`“…”`/`「…」`/`《…》` quotation span is not refused, that text outside those spans is still read, and that an ASCII single quote does not open a span. M1 proves all three through the real CLI — `keel --check` against an installed fixture repository, not the patterns in isolation — with four exemption fixtures and two boundary fixtures, and M1.red shows the first fixture failing against the unmodified checker for the stated reason. The two boundary fixtures are what stop this from being an exemption of the line: the refusal still fires and still names a line number.
      - Scope check: `git status --short` shows exactly the two Touch paths (`scripts/install_to_repo.py`, `scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. `task-start` warned that 1.1 and 1.2 declare the same Touch set under vertical-tdd; they are two behaviors in one file — 1.1 narrows what any rule reads, 1.2 changes what one pattern matches — and 1.2 has its own honest red, recorded there.
      - Findings: one, resolved here. The scenario's first two fixtures as first written contained no matched wording at all (`git status --short`, and a bare `` `68e4fd2` `` on a line with no context word), so they passed against the unmodified checker and would have passed against a checker that had stopped running. Caught by M1.red, which named the fenced-block fixture rather than the first one. Resolved here: M1, whose four exemption fixtures each carry wording the pre-change rules refuse, verified by the red run naming the first of them.
    - Blocker: none
    - Reauthorizations: the contract was re-recorded twice before implementation, both times over authoring corrections rather than scope: first to name `decimal-runs-are-not-hash-shaped` as the registry actually spells it (M3 had cited a name no scenario has) and to add I6/I7 for two fixtures task 1.2 must update; then to delete a redundant `Evidence: deferred to C1.` sentence from the M3/M4 check text, where the deferral does not belong. `sha256:3d204afe54…` → `sha256:fa395092e8…` → `sha256:8812593b6c…`. Every check above was run under the final contract; no evidence recorded under an earlier one is carried forward.

- [x] 1.2 The `已提交`/`未提交`/`待提交`/`尚未提交` family refuses a line only when a Git context word appears on the same line, while `未合入`/`待合入`/`已合入`/`合入 master|main` keeps matching bare, and the Chinese words keep supplying context to a hash-shaped token unchanged
  - Covers:
    - keel-stateless-continuity / A context word is a word and not a substring
    - D3
    - D4
    - A1
    - F2
  - Read:
    - scripts/install_to_repo.py
    - scripts/validate_plugin.py
    - openspec/changes/quoted-text-is-not-a-claim/design.md
  - Touch:
    - scripts/install_to_repo.py
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-submission-is-not-a-commit` scenario in `scripts/validate_plugin.py` drives `keel --check` through the real CLI. `keel state: ok` for an Evidence line recording that a user `已提交` merchant paperwork to a third-party review queue with no Git word on the line, and for the same fact written in English — the asymmetry issue #103 reports is gone in both directions. `keel state: failed`, naming the line, for: `已提交` beside `main`, beside `分支`, and beside `代码`; `已合入` and `未合入` alone with no other Git word and no hash-shaped token; and a hash-shaped token beside `已提交` with no other context word, which the contextual-identifier rule still catches.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario a-context-word-is-a-word` passes with its three bare Chinese fixtures moved to lines that carry a Git word, still asserting that `remaining`/`heading` supply no context and that `committed`/`commits`/`hashes` do.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the Git context list cannot be kept separate from `_HASH_CONTEXT_WORD`, because that list contains the state words themselves and reusing it would let `已提交` supply its own context.
    - Stop if making the 提交 family contextual changes any verdict for the 合入 family or for the English patterns.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:10e527cc3fb736b92c53d7dba5dab0b8406484082b1c3c27400123b282812a8b
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-submission-is-not-a-commit` reports `a-submission-is-not-a-commit scenario passed.` `keel state: ok` for the reported line itself (`用户当天**已提交**能填的商户与结算资料`), for its English translation, and for `表单**已提交**，开发者账户处于审核中` — the asymmetry issue #103 reports is gone in both directions. `keel state: failed`, each naming its line, for `已提交` beside `main`, `尚未提交` beside `分支`, `已提交` beside `代码`, `未合入` alone, and `已合入` alone. A hash-shaped token beside `已提交` with no other context word is still refused, so the contextual-identifier rule is untouched.
    - M1.red: fail, for the right reason. The scenario was written and registered before the patterns were changed, and reported `a-submission-is-not-a-commit: the reported line was refused as recorded commit state.` with `state-error openspec/changes/reading-lines/tasks.md:11: remove commit or merge state from tasks.md` — issue #103's own line, refused by the unmodified checker.
    - M1.green: pass. Same command after `TASKS_COMMIT_STATUS_PATTERNS[2]` was narrowed to the 合入 family and the 提交 family moved behind `TASKS_GIT_CONTEXT_RE`: `a-submission-is-not-a-commit scenario passed.`
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-context-word-is-a-word` reports `a-context-word-is-a-word scenario passed.` Its three bare Chinese fixtures now each carry a hash-shaped token and no other context word, which is what the missing word boundary actually buys — the Chinese word is the only thing that can make the token an identifier — while `remaining`/`heading` still supply no context and `committed`/`commits`/`hashes` still do.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the 提交 family refuses a line only when a Git word shares it, that the 合入 family keeps matching bare, and that the Chinese words keep supplying context to a hash-shaped token. M1 proves all three through the real CLI against an installed fixture repository, with the report's own sentence as the leading accepted fixture and its English translation beside it — the pair is the check, because the defect was that the two got different verdicts. M1.red shows that sentence refused by the unmodified checker. M2 proves the contextual-identifier half survived by asserting it from the side where the Chinese word is the only context available.
      - Scope check: `git status --short` shows exactly the two Touch paths (`scripts/install_to_repo.py`, `scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. `keel guard status` reports the fingerprint unchanged from task-start. Three pre-existing scenarios asserted the removed behavior and were repaired in this task rather than deleted, as `## Invalidates` I5, I6, and I7 declared: `a-context-word-is-a-word`'s Chinese block, `decimal-runs-are-not-hash-shaped`'s `refused_wording` fixture, and `a-covers-citation-is-not-a-record`'s field-boundary fixture. Each keeps the assertion it existed for and changes only the wording it makes it with.
      - Findings: one, still open. A recorded commit state phrased with no Git noun anywhere on the line — `该任务尚未提交，等待评审` is the concrete case, and it was a fixture in this repository until this task moved it — now passes. It is the false negative design.md A1 names and accepts: it cannot be told apart from `该申请尚未提交，等待评审` without reading the object of the verb, and per #58 a false negative costs one stale line that Git contradicts while a false positive costs a rewording round trip and teaches the reader to stop reading the check. Durable owner: https://github.com/TanglmChris/keel/issues/106 — filed for this, recording the accepted false negative and the fact that `TASKS_GIT_CONTEXT_RE`'s word list is inferred rather than measured (the Chinese patterns match zero lines of this repository's 8,169-line corpus). A real miss is recorded there and the list widens.
    - Blocker: none
    - Reauthorizations: the contract was re-recorded once after this task's checks had passed, because `keel-review-checklist` requires a `Durable owner:` URL to already carry the content it claims to hold, and issue #103 recorded the defect this task fixed rather than the false negative it accepts. Issue #106 was filed for that, and the Findings entry was repointed at it — an edit inside the Review, which the compiled capsule covers, so the anchor moved: `sha256:261ffe8c49…` → `sha256:10e527cc3f…`. Nothing about Covers, Touch, Verify, or the boundaries changed. Every check above was re-run under the new contract and reports the same result.

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a line whose match lies entirely inside a quoted span is not refused
    - E2 — `已提交` with no Git word on the line is not refused, and the check no longer depends on which language the author wrote in
    - I1 — the published wording this change makes stale
    - I3 — the published wording this change makes stale
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
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `keel/CHANGELOG.md` carries an entry naming the quoted-span rule and the Git-context requirement on the 提交 family, recording the 91→70 corpus measurement, closing issues #103 and #65, and stating that #65 item 3 was declined rather than left open
    - M3: the spec delta is promoted into `openspec/specs/keel-stateless-continuity/spec.md`, `node node_modules/.bin/openspec validate quoted-text-is-not-a-claim --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8ba0ad5cb05d42022e3c4360fadd2484faa33cc88bea78ed64a084cf1ca48d4e
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.41.0 to 5.42.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.42.0 - quoted text is not a claim`, naming the quoted-span rule with the 91→70 corpus measurement and the excluded ASCII single quote, the Git-context requirement on the 提交 family with the English/Chinese asymmetry it removes, the three repaired scenarios, and the closure of issues #103 and #65. It states the supersession of 5.29.0's "The Chinese context words carry no boundary, and must not" rather than leaving two entries that contradict each other, records that #65 item 3 was declined rather than left open, and records that issue #49 was closed with evidence rather than reopened.
    - M3: pass. The delta is promoted — `openspec/specs/keel-stateless-continuity/spec.md` carries the new `A quoted span is a citation and not a claim` requirement, the reworded `A context word is a word and not a substring` with its two new scenarios, and the reworded second paragraph of `A recorded commit identifier is recognized by what makes it one`. `node node_modules/.bin/openspec validate quoted-text-is-not-a-claim --strict` reports `Change 'quoted-text-is-not-a-claim' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the promoted store.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 147 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — up from 145 by the two scenarios this change added, no failing scenario and no exception.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all rather than spot-checking. M3 asserts the promotion through the two tools that consume the published store rather than by reading the files back. M2 is the one prose check, and what it asserts is what a diff would not show: this release makes the check accept lines it used to refuse, so the entry has to say what it stopped catching — the `该任务尚未提交，等待评审` false negative and the backticked commit hash — and name the earlier entry it supersedes.
      - Scope check: `git status --short` shows exactly this task's Touch entries — `package.json`, `package-lock.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, the promoted `openspec/specs/keel-stateless-continuity/spec.md`, and the twelve `.claude/`/`.codex/` marker files `bump_version.js` rewrites — plus `scripts/install_to_repo.py` from tasks 1.1 and 1.2, already declared complete and unrelated to this task's own writes, plus this change's own untracked directory, the record-write layer. `keel gate task-start` reports the fingerprint unchanged.
      - Findings: one, resolved here. `## Invalidates` I3 named a sentence in the `A recorded commit identifier is recognized by what makes it one` requirement and closed it with `Updated by: 2.1`, but the spec delta declared no operation on that requirement — so the task had authority to promote a change it had no delta for. Implementation stopped and returned to authoring: the delta gained the requirement as a `MODIFIED` entry, whose second paragraph now names both bounds on what counts as a statement instead of naming only the `Covers` field, and the proposal's Modified Capabilities line was extended to say so. Resolved here: M3, which validates the change strictly and the promoted store strictly after the delta was completed.
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes once for the whole change with `node_modules/.bin` on `PATH`, reporting no failing scenario and no exception, with the two new scenarios registered and every pre-existing scenario green.

## Change Evidence

- C1: pass. `npm test` reports `validation --all passed: baseline plus 147 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` Run once for the whole change with `node_modules/.bin` on `PATH`, after task 2.1's promotion: no failing scenario, no exception, both new scenarios (`a-quoted-span-is-not-a-claim`, `a-submission-is-not-a-commit`) registered and green, and every pre-existing scenario green including the three this change repaired.

## Invalidates

- I1: "The Chinese context words MUST keep matching wherever they appear, because a word boundary is not
  defined between two word characters that are both word characters, and requiring one would stop `已提交`
  and `未提交` from matching at all." and the scenario "A Chinese context word needs no boundary", whose
  THEN reads "`keel --check` still refuses it, whether or not a hash-shaped token shares the line" —
  `openspec/specs/keel-stateless-continuity/spec.md`. The boundary reasoning stays true for the hash-context
  half and stops being true for the bare state-word half. Updated by: 2.1
- I2: "which are exactly what the wording rule is for" — the comment above `_HASH_CONTEXT_WORD` in
  `scripts/install_to_repo.py`, closing a sentence about why the Chinese words carry no word boundary.
  The boundary reasoning is right and the clause names the wrong rule: the wording rule is the one this
  change makes contextual, while the boundary argument belongs to the hash-context rule. Updated by: 1.2
- I3: "This holds for every line an author writes as a statement." — the second paragraph of the
  "A recorded commit identifier is recognized by what makes it one" requirement in
  `openspec/specs/keel-stateless-continuity/spec.md`, which names the `Covers` field as the only thing that
  is not such a statement. A quoted span on any line is now also not one. Updated by: 2.1
- I4: "The Chinese context words carry no boundary, and must not." and "exactly what the wording rule exists
  for" — the 5.29.0 entry in `keel/CHANGELOG.md`. Discard reason: dated release history; the new entry
  records the supersession, and rewriting a past entry would falsify the record.
- I6: "该任务**未提交**，等待评审。" — the `refused_wording` fixture in the
  `decimal-runs-are-not-hash-shaped` scenario in `scripts/validate_plugin.py`, asserted to fail on wording
  alone. Its line carries no Git word, so after this change it passes and the assertion is wrong.
  Updated by: 1.2
- I7: "the change is 已提交 and needs no further work" — the field-boundary fixture in the
  `a-covers-citation-is-not-a-record` scenario in `scripts/validate_plugin.py`, which asserts that a
  `Verify` line following a `Covers` field is still read. The bound it proves is still right; the wording
  it proves it with stops being refused. Updated by: 1.2
- I5: "A word boundary around a Chinese context word disables it silently" — the refusal message and its
  three bare fixtures `已提交`, `未提交`, `该任务尚未提交，等待评审` in the `a-context-word-is-a-word`
  scenario in `scripts/validate_plugin.py`. The scenario asserts that those three lines must fail with no
  Git word present, which is the behavior this change removes. Updated by: 1.2

## Expectation Coverage

- E1: A `tasks.md` line whose every match lies inside an inline code span, a fenced block, or a quotation span is not refused, while text outside those spans is still read. Covered by: 1.1, 2.1
- E2: `已提交` and its family refuse a line only when a Git word shares it, so the check accepts a Chinese sentence whose English translation it already accepted. Covered by: 1.2, 2.1
- E3: A recorded commit identifier, a recorded merge state, and the English dirty-state wording are refused exactly as before, outside quoted spans. Covered by: 1.1, 1.2
- E4: The failure level is unchanged — a real match still makes `keel --check` report `keel state: failed`. Discard reason: this is the absence of a change, decided by the owner on 2026-09-05 (issue #65 item 3); D5 records the decision and no slice implements it.

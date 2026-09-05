# Tasks

## 1. Read what the author wrote

- [x] 1.1 `declaredPath()` extracts a separator-free token that has a filename shape, so a repository-root file is nameable as a `Durable owner:` or as `Resolved here:` evidence; a value with neither a separator nor that shape stays unrecognized; and existence still decides, naming a root file that does not exist rather than reporting it as unrecognized
  - Covers:
    - keel-core-gates / A declared path is extracted by where it ends, not by what it is made of
    - D1
    - D2
    - D3
    - D4
    - F1
    - F2
  - Read:
    - src/core/gates.js
    - scripts/validate_plugin.py
    - openspec/changes/a-refusal-names-the-cause/design.md
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-root-file-is-a-path` scenario in `scripts/validate_plugin.py` drives the real CLI against a fixture repository. `keel gate task-complete` passes with `Durable owner: AGENTS.md` and with `Resolved here: AGENTS.md`, both files present at the fixture root and neither spelled with a leading `./`; `./AGENTS.md` keeps passing. It fails with `Durable owner: NOT-THERE.md`, and — through `keel gate task-start` on an `## Invalidates` entry, the reader that names a missing path — accepts `AGENTS.md` and refuses `NOT-THERE.md` while naming it. It fails as unrecognized — not as a missing file — with `Durable owner: pending` and with `Durable owner: 5.44.0`. A root file ending a sentence (`Durable owner: AGENTS.md.`) is accepted, so the trailing-punctuation trim runs before the filename shape is judged.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario durable-owner-vocabulary` passes unchanged, so the separator form, the archived path, the tracker reference, and `keel/HANDOFF.md` keep their verdicts.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario an-owner-outlives-the-change` passes unchanged, so a root file being nameable did not make a self-pointer nameable.
    - M4 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the filename shape cannot exclude a version string without also excluding a real extension.
    - Stop if accepting a root file requires a second extractor rather than a branch inside `declaredPath()`.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:c7f0bee7db4079448de21445a3c4a2d31e5e2ba27315cfee7a59d77a587c2486
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-root-file-is-a-path` reports `a-root-file-is-a-path scenario passed.` Through `keel gate task-complete` against a fixture repository: `Durable owner: AGENTS.md`, `Resolved here: AGENTS.md`, `Durable owner: ./AGENTS.md`, and `Durable owner: AGENTS.md.` all pass; `NOT-THERE.md` is refused; `pending` and `5.44.0` are refused without any message reporting a file that does not exist. Through `keel gate task-start` on an `## Invalidates` entry — the reader that names a missing path — `AGENTS.md` closes the entry and `NOT-THERE.md` is refused with the name in the message.
    - M1.red: fail, for the right reason. The scenario was written and registered before `src/core/gates.js` was touched, and reported `a-root-file-is-a-path: a root file as a durable owner was refused.` with the gate's `finding-owner` problem — `AGENTS.md` exists at the fixture root and the extractor could not see it as a path.
    - M1.green: pass. Same command after `declaredPath()` gained the `ROOT_FILE_NAME` branch, tried only after the separator form and after the trailing-punctuation trim: `a-root-file-is-a-path scenario passed.`
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario durable-owner-vocabulary` reports `durable-owner-vocabulary scenario passed.` unchanged — the separator form, `openspec/FOLLOWUP.md`, the missing path, `keel/HANDOFF.md`, the archived path, and the tracker reference all keep their verdicts.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario an-owner-outlives-the-change` reports `an-owner-outlives-the-change scenario passed.` unchanged, so a root file becoming nameable did not make a self-pointer nameable; the transient verdict is judged before existence and is untouched.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 150 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.`
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a separator-free filename that exists is accepted as an owner and as resolution evidence, that a value with no path shape stays unrecognized, and that existence still decides. M1 proves all three through the real CLI rather than by calling the extractor: four accepted spellings, a missing file refused, and two non-paths refused with the *absence* of a "does not exist" message asserted — which is the boundary, because a check that reported `pending` as a missing file would have traded this refusal for a worse one. The naming half is asserted through `## Invalidates`, the reader that names a missing path, rather than claimed of `Findings`, which reports one owner refusal for every unusable owner and always has.
      - Scope check: `git status --short` shows exactly the two Touch paths (`src/core/gates.js`, `scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. `keel gate task-start` warned that 1.1 and 1.2 declare the same Touch under vertical-tdd. They are independent here, and M1 passing on its own is the evidence: this task's scenario is green before 1.2 is written, so 1.2's implementation is not what makes 1.1 correct — unlike the split that `an-owner-outlives-the-change` had to merge, where the first task's check could not pass until the second existed.
      - Findings: one, resolved here. The first draft of this task's M1 asserted that the `Durable owner:` refusal names a missing root file, and it does not — `findingOwnerIsDurable()` returns a boolean and `Findings` has always reported one generic owner refusal, in the separator form as much as the new one. The spec delta had inherited that overstatement, claiming the missing file is "refused and named" everywhere. Both were corrected before implementation completed: the requirement now says a reader that names a missing path names a separator-free name the same way, and states explicitly that `Findings` continues to report one refusal. Resolved here: M1, whose naming assertion runs against `## Invalidates`, the reader that actually names it.
    - Blocker: none
    - Reauthorizations: the contract was re-recorded once, before implementation completed, to move M1's naming assertion off `Findings` and onto `## Invalidates`. `sha256:702d0d7cea…` → `sha256:c7f0bee7db…`. The scenario and every check above were run under the final contract.

- [x] 1.2 The `## Invalidates` quoted-phrase check reads the whole entry body, so a quotation that begins on one line and ends on another is a quotation, while an entry carrying no quotation anywhere is still refused
  - Covers:
    - keel-expectation-slice-evidence-gates / Task Authoring Gate covers statements the change invalidates
    - D5
    - F3
  - Read:
    - src/core/gates.js
    - scripts/validate_plugin.py
    - openspec/changes/a-refusal-names-the-cause/design.md
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `an-invalidates-phrase-may-wrap` scenario in `scripts/validate_plugin.py` drives `keel gate task-start` through the real CLI. An entry whose quoted phrase opens on one line and closes on the next passes; the same entry with the quotation removed still fails with `names where to look but not what to look for`; and a second entry in the same section, unquoted, is still refused by its own identifier while the wrapped one is accepted, so the entry bound still holds.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario task-start-invalidation` passes unchanged, so the missing-section, `- None.`, and unclosed-entry verdicts are untouched.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if reading the phrase across lines requires changing how the section parser bounds an entry.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:988dd0364c4282db072d11ab94bd9dca11e1373b12589a6f21cdda2d271101b4
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario an-invalidates-phrase-may-wrap` reports `an-invalidates-phrase-may-wrap scenario passed.` Through `keel gate task-start` against a fixture repository: an entry whose quotation opens on one line and closes on the next passes; the same entry with the quotation marks removed is still refused, and the refusal is asserted to carry `invalidation-phrase` so the assertion is about the phrase check and not some other failure; and a section holding a wrapped I1 above an unquoted I2 fails naming I2 and not I1, which is what proves the quotation is still bounded by its own entry.
    - M1.red: fail, for the right reason. The scenario was written and registered before `src/core/gates.js` was touched, and reported the wrapped entry refused with `invalidation-phrase: I1 names where to look but not what to look for. Quote the wording a reader would search for, so the entry is a search rather than a reminder.` — for an entry that had quoted exactly that.
    - M1.green: pass. Same command after the phrase test dropped `\n` from its character class: `an-invalidates-phrase-may-wrap scenario passed.`
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario task-start-invalidation` reports `task-start-invalidation scenario passed.` unchanged — the missing-section refusal, `- None.`, and the unclosed-entry refusal keep their verdicts.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 151 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.`
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a wrapped quotation is a quotation, that an entry with none is still refused, and that the entry bound holds. M1 proves all three through the real CLI, and the third is the one that matters most: without it, widening the pattern could have let one quoted entry satisfy every entry below it, which would look like a pass. The unquoted-entry assertion also checks the problem *code*, so it cannot be satisfied by the run failing for an unrelated reason.
      - Scope check: `git status --short` shows exactly the two Touch paths (`src/core/gates.js`, `scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. `keel gate task-start` warned that 1.1 and 1.2 declare the same Touch under vertical-tdd; they are independent, and 1.1's scenario was green before this task was written, which is the evidence the warning asks for.
      - Findings: one, resolved here. The first draft of this scenario guarded two distinct failures behind one condition — `if payload.get("status") == "pass" or "I2" not in text` — which reports "an unquoted entry was accepted" when what actually happened was that the run failed for something other than I2. `assertion-shape-count` caught it and refused the suite: `81 assertion sites guard several distinct failures behind one message, but 80 are recorded`. Split into two conditions with their own messages rather than raising the bound, which is what that check exists to prevent. Resolved here: M3, the full run that reports the bound satisfied at 80 again.
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a repository-root file is nameable as an owner and as resolution evidence
    - E2 — an `## Invalidates` quoted phrase may wrap across the entry's lines
    - I1 — the published wording this change makes stale
    - I2 — the published wording this change makes stale
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
    - openspec/specs/keel-core-gates/spec.md
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
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `keel/CHANGELOG.md` carries an entry naming both refusals, the nine repository-root files that could not be named, and the 42-of-194 measurement together with why zero wrapped quotations in the corpus is the workaround rather than the absence of the shape, closing issues #107 and #108
    - M3: both spec deltas are promoted, `node node_modules/.bin/openspec validate a-refusal-names-the-cause --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:76a89916fd0c394737064c423d4562b53538d7b239903c5e0f0163ee07b25ebc
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.44.0 to 5.45.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.45.0 - a refusal names the cause`, naming both refusals with the nine repository-root files and the 42-of-194 measurement, and stating why zero wrapped quotations in the corpus is the workaround rather than the absence of the shape. It gives as much room to the boundaries as to the loosening — `pending` staying unrecognized, a version string not reading as a filename, an unquoted entry still refused — because this release makes two gates accept more and the entry has to say what still fails. It records that `assertion-shape-count` refused this change's own draft and that the condition was split rather than the bound raised. Closes issues #107 and #108.
    - M3: pass. Both deltas are promoted — `openspec/specs/keel-core-gates/spec.md` carries the reworded path-extraction requirement with its two new scenarios, and `openspec/specs/keel-expectation-slice-evidence-gates/spec.md` carries the invalidation requirement with the wrapping paragraph and its scenario. `node node_modules/.bin/openspec validate a-refusal-names-the-cause --strict` reports `Change 'a-refusal-names-the-cause' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0`.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 151 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — up from 149 by the two scenarios this change added, no failing scenario and no exception.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all rather than spot-checking. M3 asserts the promotion through the two tools that consume the published store rather than by reading the files back. M2 is the one prose check, and what it asserts is what a diff would not show: both halves of this release make a gate accept something it used to refuse, so the entry has to state the boundary on each — otherwise a reader takes "the check got looser" and stops there.
      - Scope check: `git status --short` shows exactly this task's Touch entries — `package.json`, `package-lock.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, both promoted spec files, and the twelve `.claude/`/`.codex/` marker files `bump_version.js` rewrites — plus `src/core/gates.js` from tasks 1.1 and 1.2, already declared complete and unrelated to this task's own writes, plus this change's own untracked directory, the record-write layer.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "by locating a run of non-whitespace containing a path separator" — the "A declared path is extracted
  by where it ends, not by what it is made of" requirement in `openspec/specs/keel-core-gates/spec.md`.
  The separator is what excludes every repository-root file, and it stops being a requirement of the
  extractor. Updated by: 2.1
- I2: "a run of non-whitespace containing a path separator" — the comment above `declaredPath()` in
  `src/core/gates.js`, which states the same rule beside the code that implements it. Updated by: 1.1
- I3: "A path is checked for existence, so one with no file behind it is refused by name" — the Project
  Conventions section of `AGENTS.md`. The sentence stays true and stops being the whole rule: what is
  checked for existence now includes a name with no separator in it. Discard reason: the sentence is not
  falsified by this change, and the forms list beside it already reads as illustrative rather than
  exhaustive; adding the root-file case there would restate the spec in a file that is not its owner.
- I4: "the wording a reader would search for, so the entry is a search rather than a reminder" — the
  `invalidation-phrase` refusal in `src/core/gates.js`. The message stays right and stops being the whole
  story: it fired on entries that carried that wording and had merely wrapped. Discard reason: the message
  is correct for the case that remains — an entry with no quotation at all — and this change removes the
  case where it was wrong rather than rewording it.

## Expectation Coverage

- E1: A repository-root file that exists is accepted as a `Durable owner:` and as `Resolved here:` evidence without a leading `./`, one that does not exist is refused by name, and a value that is not a path shape is still refused as unrecognized. Covered by: 1.1, 2.1
- E2: An `## Invalidates` entry whose quoted phrase wraps across lines is accepted, and an entry with no quotation anywhere in its body is still refused. Covered by: 1.2, 2.1
- E3: Every verdict these two checks give today that is correct stays correct — the separator form, the backtick form, the trailing-punctuation trim, `keel/HANDOFF.md`, the self-pointer refusal, and the missing-section and unclosed-entry refusals. Covered by: 1.1, 1.2

## 1. The gate asks

- [x] 1.1 `keel gate task-start` requires the change to declare what it invalidates
  - Covers:
    - keel-expectation-slice-evidence-gates / Task Authoring Gate covers statements the change invalidates / A change with no declaration cannot start its tasks
    - keel-expectation-slice-evidence-gates / Task Authoring Gate covers statements the change invalidates / Declaring nothing is a legitimate answer
    - keel-expectation-slice-evidence-gates / Task Authoring Gate covers statements the change invalidates / A location without a symptom phrase is refused
    - keel-expectation-slice-evidence-gates / Task Authoring Gate covers statements the change invalidates / An entry must close
    - keel-expectation-slice-evidence-gates / Task Authoring Gate covers statements the change invalidates / The declaration is not task authority
    - D2 an entry must carry a searchable symptom phrase and not only a location
    - D3 closure at task-start validates form and not completion
    - D5 the section is a sibling heading so it stays outside every task body and the capsule fingerprint
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: running the gate against a change whose tasks.md has no invalidation section returns a failing result naming the missing section, and writes neither a guard manifest nor a contract anchor
    - M2: a section stating that nothing is invalidated passes, the same fixture passes with well-formed entries carrying a phrase, a location, and each of the three closure forms, and both passing runs compile the identical capsule fingerprint, so the declaration is bookkeeping rather than task authority
    - M3: an entry naming only paths and no searchable phrase fails with a diagnostic identifying that entry, an entry with a phrase but no closure fails as unclosed, and an entry naming an updater task the change does not define fails
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:5eec8cec2b3587036dfcccd456c79de3aa270bf3257beb800ebc7cd3a723e52e
    - M1: pass. New scenario `task-start-invalidation`. A change with no section fails with `invalidation-declaration`, and the run leaves no `keel/guard.json` and an untouched tasks.md, proving a failed authoring gate records nothing even under `--record`.
    - M1.red: before the check existed the same fixture returned `status: pass` with `problems: []` — the gate had no opinion at all.
    - M1.green: the fixture now fails with `invalidation-declaration` and the diagnostic states the entry form and all three closure forms.
    - M2: pass. A `- None.` section passes; a section carrying three entries that between them use `Updated by:`, `Discard reason:`, and `Durable owner:` also passes; and both runs compile the identical fingerprint, so the section is bookkeeping and never task authority.
    - M2.red: with the `- None.` escape removed from `invalidationProblems`, the scenario failed `task-start-invalidation refused a legitimate declaration of nothing`, the gate demanding an `I` entry from a change that has nothing to declare.
    - M2.green: the escape restored; both fixtures pass and the two fingerprints match.
    - M3: pass. An entry naming only paths fails `invalidation-phrase` and the diagnostic names `I1`; an entry with a phrase but no closure fails `invalidation-closure`; an entry naming updater task 9.9, which the change does not define, fails `invalidation-owner`.
    - M3.red: with the quoted-phrase test forced false, the scenario failed `task-start-invalidation accepted an entry with no searchable phrase` and the gate reported `problems: []` for a location-only entry — precisely the memo-shaped entry D2 exists to refuse.
    - M3.green: the test restored; all three malformed entries are refused with distinct codes.
    - Review:
      - Status: pass
      - Acceptance check: every check runs the real CLI against a temporary repository and asserts on the gate's own JSON result, which is the interface an author meets. The five covered scenarios map to the checks directly: the missing-section refusal and the `- None.` acceptance to M1 and M2, the phrase and closure refusals to M3, and "the declaration is not task authority" to M2's fingerprint equality. The negative clause that a failing gate writes nothing is asserted on the filesystem, not inferred from the result.
      - Scope check: only the two declared Touch files changed, `src/core/gates.js` and `scripts/validate_plugin.py`. The two mutation edits were reverted from a byte copy and `git diff --stat` confirms `src/core/gates.js` carries only the intended additions. The new gate also broke 17 existing scenarios whose fixtures predate the requirement; every repair landed inside the already-declared `scripts/validate_plugin.py` and consisted of giving each fixture the `- None.` answer, which is the same one-line migration a real consumer performs.
      - Findings: none
    - Blocker: none

## 2. The authored surface teaches it

- [ ] 2.1 Scaffolded changes are born compliant and the protocol names the section
  - Covers:
    - keel-expectation-slice-evidence-gates / Task Authoring Gate covers statements the change invalidates / Declared updates land in Touch before implementation
    - D1 the gate runs at task-start so affected paths enter Touch before implementation
    - D4 declaring nothing is legitimate and cheap
    - F4 the tasks template exists in two synchronized copies and both must gain the section
  - Touch:
    - openspec/schemas/keel-spec-driven/templates/tasks.md
    - assets/openspec/schemas/keel-spec-driven/templates/tasks.md
    - openspec/schemas/keel-spec-driven/schema.yaml
    - assets/openspec/schemas/keel-spec-driven/schema.yaml
    - AGENTS.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a change scaffolded from the shipped schema passes `keel gate task-start` without the author adding the section by hand, because the template already carries it with a usable default
    - M2: the two template copies and the two schema copies remain byte-identical to each other, and the authoring instruction the schema returns describes the section and its closure forms rather than naming Expectation Coverage as the only trailing section
    - M3: the resident Session Start protocol names the section among the completion-gate rules, and the existing Expectation Coverage rule is still stated
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

## Invalidates

- I1: "tasks.md ends with a `## Expectation Coverage` section" — the authoring instruction returned by `openspec instructions tasks`, in both `openspec/schemas/keel-spec-driven/schema.yaml` and its `assets/openspec/...` copy. It becomes wrong as a statement about the only required trailing section. Updated by: 2.1
- I2: "task-start returns the compiled capsule and fingerprint" — `AGENTS.md` Completion gates. The sentence describes task-start as a capsule-only gate, which stops being the whole truth once it also checks a change-level section. Updated by: 2.1
- I3: "Follow-up Ownership" as the complete account of what a change owes at its close — `AGENTS.md`. It governs unresolved work; this change adds the opposite shape, statements left standing by resolved work, and a reader comparing the two sections should not have to infer that. Updated by: 2.1
- I4: "keel gate task-complete does not accept a GitHub issue URL as a Review `Findings` owner" and the two candidate directions recorded as undecided — `keel/archive/follow-ups/2026-07-27-stale-plugin-state-in-session.md`. Both were resolved in 5.2.4 and the note still reads as current guidance. Discard reason: archive notes are historical evidence by definition and are deliberately kept unedited; the project convention already records that notes predating 5.2.4 describe the old workaround. Recorded here because a symptom search finds it and a reader deserves the answer, not because it should be rewritten.

## Expectation Coverage

- E1: the gate refuses a change that has not declared what it invalidates, and accepts a declaration of nothing Covered by: 1.1
- E2: an entry is executable as a search rather than a memo, so a phrase is required and a location list alone is refused Covered by: 1.1
- E3: the declaration cannot become task authority or move a capsule fingerprint Covered by: 1.1
- E4: a scaffolded change is born compliant, so the new requirement does not land as a surprise failure on the first task-start Covered by: 2.1
- E5: nothing re-verifies at change-close that a declared update actually happened. Discard reason: accepted as D3 when the user chose authoring-time enforcement over both checkpoints; the structural implication is that a declared updater task carries the paths in its Touch, and semantic review remains the backstop.
- E6: authors may write a paraphrase that does not match the stale text, which the gate cannot detect. Durable owner: https://github.com/TanglmChris/keel/issues/16

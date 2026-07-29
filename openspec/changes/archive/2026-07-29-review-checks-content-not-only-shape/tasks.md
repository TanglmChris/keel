## 1. The checks

- [x] 1.1 Add the content-at-citation and actual-cause checks to `keel-review-checklist`, keeping both in the semantic-review layer
  - Covers:
    - keel-expectation-slice-evidence-gates / Semantic review checks the content a gate can only shape-check
    - D1 — both checks belong to semantic review, and the spec says so
    - D3 — the durable-owner check binds at citation time, not at archive time
    - D4 — the failure-message check names one condition guarding two distinct failures
    - D5 — entries are questions with a concrete failing example
  - Touch:
    - src/skills/keel-review-checklist/SKILL.md
    - plugins/keel/skills/keel-review-checklist/SKILL.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: the checklist states that a URL durable owner must already carry its content when cited, that an empty target returns the work to create it first, and that the check happens at citation rather than at archive
    - M2: the checklist states that a failure message must name the actual cause and that one condition guarding two distinct failures must be split; and the canonical source and its distribution copy stay byte-identical
  - Evidence:
    - Contract: sha256:8d9e33ef30f5092032f9318556b62b7c1e0072d63c83426e5acff5c6d4a310af
    - M1: `python scripts/validate_plugin.py --scenario review-checks-content` passes. The Expectation and follow-up ownership section now states that a URL durable owner must `already carry the content` it claims to hold `when it is cited`, that an empty target means creating the content first, and that the check happens at citation rather than archive because a deferred check finds the same fact after the reauthorization it should have prevented.
    - M1.red: exit 1, `review-checks-content: canonical skill omits: already carry the content` — neither entry existed.
    - M1.green: all five asserted phrases present in both copies, matched after whitespace collapse so the assertion is about wording rather than hard-wrap layout.
    - M2: the deterministic-gate-check section states a failure message must `name the actual cause` and names the trigger structure — `two distinct failures` guarded by one condition — with the concrete `if result is None or result["status"] != expected` shape that produced the 5.7.0 instance. Both entries state `not a deterministic gate check` with the reason. The canonical source and its distribution copy are byte-identical.
    - M2.red: aimed by appending a newline to the distribution copy, since both checks went green in the same run. exit 1, `review-checks-content: the canonical and distributed skills diverged.`
    - M2.green: copy restored. `npm test` → `validation --all passed: baseline plus 101 scenarios.` (100 before this task).
    - Review:
      - Status: pass
      - Acceptance check: each entry is written as a concrete failing case rather than a principle, which is the form its neighbours already use and the form a reviewer can match against while scanning. The URL entry carries its timing (`when it is cited`) because the same check at archive is the failure it exists to prevent; the message entry carries its structural trigger because "write clear messages" is unactionable. Both state why they are not gate checks, so a later proposal to "strengthen the gates" reads the reason before writing the change.
      - Scope check: `git status --porcelain` shows `src/skills/keel-review-checklist/SKILL.md`, its `plugins/keel/skills/` copy, and `scripts/validate_plugin.py` modified by this task — the three paths in Touch. `keel/config.yaml` is also dirty and is **not** this task's product: it carries the owner's `triage:` declaration, made as a Lite change before this change existed, which is what admitted issue #33 to this run in the first place.
      - Findings: none
    - Blocker: none

## 2. Close

- [x] 2.1 Promote this change's spec delta and record the workflow change
  - Covers:
    - I1 — the durable-owner requirement's unassigned check
    - keel-expectation-slice-evidence-gates / Semantic review checks the content a gate can only shape-check
  - Touch:
    - openspec/specs/keel-expectation-slice-evidence-gates/spec.md
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: evidence-first
    - M1: `keel openspec validate review-checks-content-not-only-shape` passes and every `### Requirement:` and `#### Scenario:` heading in the delta appears in the live spec
    - M2: the changelog entry states both checks, that they are semantic-review rather than gate checks and why, and that this change was admitted to an unattended run by the `auto` label
    - M3: `npm test` passes after promotion
  - Evidence:
    - Contract: sha256:040c1971672bf213e6be254009d8cdc8e3540bd7d7b2f638f20c182644c9223a
    - M1: `node bin/keel.js openspec validate review-checks-content-not-only-shape` → valid. All 5 `### Requirement:` / `#### Scenario:` headings from the delta appear in the live `keel-expectation-slice-evidence-gates` spec. I1 is closed: the requirement that stated a gate "cannot confirm that a URL resolves" now sits beside one naming semantic review as the layer that does.
    - M2: `keel/CHANGELOG.md` gains a `## 5.7.1 - a valid reference is not a full one` entry stating both checks with their empirical instances (5.4.0's E5 citing an issue with zero comments; 5.7.0's triage scenario reproducing the class 5.2.3 fixed), that both stay semantic-review checks and why a gate cannot take them, that neither judges quality, and that this change was admitted to an unattended run by the `auto` label and ends at a pull request rather than a merge.
    - M3: `npm test` → `validation --all passed: baseline plus 101 scenarios.` after promotion.
    - Review:
      - Status: pass
      - Acceptance check: promotion verified by heading-set comparison rather than by re-reading. The changelog entry names the second instance's provenance plainly — the class returned in a repository that had already fixed it, in a test written by the agent that had just read the rule — because a reader who does not know the fix failed once will not understand why a checklist line was the remedy rather than another round of corrections.
      - Scope check: `git status --porcelain` shows `openspec/specs/keel-expectation-slice-evidence-gates/spec.md` and `keel/CHANGELOG.md` modified by this task — the two paths in Touch. The skill files and validator are task 1.1's completed products; `keel/config.yaml` carries the owner's `triage:` declaration made before this change existed.
      - Findings: none
    - Blocker: none

## Invalidates

- I1: "A gate runs without network and cannot confirm that a URL resolves or that an archive path is the right one, so a whitelist of prefixes verifies nothing beyond spelling." — the durable-owner requirement in `openspec/specs/keel-expectation-slice-evidence-gates/spec.md`. The sentence stays true and becomes incomplete: it names what a gate cannot do and assigns the resulting check to nobody, which is the gap issue #33 reported. Updated by: 2.1
- I2: "Each related critical expectation needs behavior evidence, a durable follow-up owner, or an explicit discard reason." — the Expectation and follow-up ownership section of `src/skills/keel-review-checklist/SKILL.md` and its distribution copy, which treats a durable owner as satisfied by naming one. Updated by: 1.1

## Expectation Coverage

- E1: A durable owner declared as a URL is checked for content at the moment it is cited, not at archive. Covered by: 1.1
- E2: A failure message is checked against the failure it actually reports, with the two-failures-one-condition structure named as the trigger. Covered by: 1.1
- E3: Both checks stay in semantic review, and the reason they must not become gate checks is recorded where a future proposer will read it. Covered by: 1.1, 2.1
- E4: Neither check judges quality — only presence and accuracy. Covered by: 2.1
- E5: The 5.2.3 diagnostics fix left no recurrence guard, which is why the class returned in 5.7.0. Covered by: 1.1
- E6: Nothing enforces either check; both depend on the review being performed. Discard reason: this is inherent to the semantic layer and is stated in design.md A1 rather than mitigated. Adding enforcement would mean adding a gate, which D2 records as the worse trade.

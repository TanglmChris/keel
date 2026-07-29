## 1. The declaration and the command

- [x] 1.1 Read a `triage:` label allowlist from `keel/config.yaml`, add `keel triage` evaluating it against supplied issue labels, and report the surface on `keel --doctor`
  - Covers:
    - keel-unattended-triage / A repository declares which work may start without asking
    - keel-unattended-triage / Triage evaluation performs no network access
    - D2 — admission is a label allowlist, not a heuristic
    - D3 — attributes are supplied, not fetched
    - D4 — a refusal names the reason and the accepted policy
  - Touch:
    - src/core/config.js
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a repo declaring `triage:` accepting `auto` admits an issue whose labels include `auto`, naming that label as the reason, and refuses one carrying only other labels, naming both the labels carried and the labels accepted
    - M2: a repo with no `triage:` block, or an empty one, refuses every issue with a reason stating no policy is declared rather than implying the issue was judged unsuitable; `keel --doctor` reports the triage surface in both the declared and undeclared states
    - M3: `keel triage` succeeds under a preload that makes every network primitive throw, and returns the identical verdict and reason on two consecutive runs with the same inputs
  - Evidence:
    - Contract: sha256:a4ef7b8721dc2a37ebb3cf05283dd83188f5d09b19444c0b031e25a142dd1a63
    - M1: `python scripts/validate_plugin.py --scenario triage-declaration` passes. A repo declaring `triage: [auto]` returns `admit` for `--labels auto,bug` with a reason naming `auto`, and `refuse` for `--labels bug,docs` with a reason naming all of `bug`, `docs`, and `auto` — the labels carried and the labels accepted.
    - M1.red: exit 1, `triage: a declared label did not admit: None` — no such command existed.
    - M1.green: reached after one intermediate failure that was mine: `keel triage . --labels auto --json` was rejected by the shared option guard with `selection and JSON options apply only to keel context or keel gate`, because the new action was not in that guard's allowlist. Adding it fixed the command rather than working around the guard.
    - M2: a repo with no `triage:` block and a repo with an empty one both refuse every issue, with a reason containing `no triage policy` and stating explicitly that this is not a judgement about the issue. `keel --doctor` reports `triage: none` in both, and `Unattended triage:` / `triage: ok` in the declared repo.
    - M2.red: aimed by replacing the `accepted.length === 0` branch guard with `if (false)`, so an undeclared repo fell through to the generic refusal. exit 1, `triage: the absent refusal does not distinguish an undeclared policy from an unsuitable issue: the issue carries auto and this repository accepts .` — which is exactly the confusion the check exists to prevent, and which the trailing empty list makes visible.
    - M2.green: guard restored; both undeclared states report the policy-absent reason.
    - M3: `keel triage` returns `admit` under `NODE_OPTIONS=--require <guard>` where the guard makes `net.connect`, `http.request`/`get`, `https.request`/`get`, `dns.lookup`, and `fetch` throw, and two consecutive runs return byte-equal JSON.
    - M3.red: aimed twice. Network — injecting `fetch('https://example.com')` into `triageIssue` gave `no JSON under the no-network guard`. Determinism — making the label match depend on `Math.random()` gave `the offline run reached a different verdict than the online one`.
    - M3.green: both mutations reverted. `npm test` → `validation --all passed: baseline plus 98 scenarios.` (97 before this task).
    - Review:
      - Status: pass
      - Acceptance check: every check drives the `keel triage` CLI and asserts its JSON, not the reader. The refusal checks are the load-bearing ones and are asserted by content rather than by status alone, because "refused" is the same word for "your policy excludes this" and "you have no policy" — two states a reader must be able to tell apart. The no-network guard is the same preload used for the precedent store, and it was proven to fire here rather than assumed to.
      - **The determinism mutation exposed a flaw in the test, not the code.** The network and verdict assertions were collapsed into one condition, so a wrong verdict reported `evaluation attempted network access` — sending a reader to the wrong cause entirely. That is the misleading-diagnostic failure this repository fixed in 5.2.3 and I reproduced it in a new test. The two are now separate conditions with separate messages, and the re-aimed mutation reports the real cause.
      - Scope check: `git status --porcelain` shows `bin/keel.js`, `scripts/validate_plugin.py`, and `src/core/config.js` modified — the three paths in Touch. `readStandingAuthorization` was refactored onto the shared `configList` helper this task introduced; the behavior is unchanged and the existing standing-authorization scenarios still pass.
      - Findings: none
    - Blocker: none

- [x] 1.2 Prove admission decides nothing that follows it
  - Covers:
    - keel-unattended-triage / Admission starts work and decides nothing that follows
    - D5 — admission starts work; it does not finish it
  - Touch:
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: evidence-first
    - M1: for one fixture task, every gate stage returns an equal `{status, sorted problems}` in a repo declaring a triage policy and in an identical repo declaring none, with a positive control first asserting the two repositories actually differ on the triage surface
    - M2: a task with missing evidence still fails completion in the triage-declaring repo, with failure text equal to the undeclared repo's
  - Evidence:
    - Contract: sha256:2045914292cebd89f6f2b55d8d7f6411a2c422fb54bd06138248bd59c03f269f
    - M1: `python scripts/validate_plugin.py --scenario triage-admits-only-a-start` passes. For one fixture task, `task-start` and `task-complete` each return an equal `{status, sorted problems}` in a repo declaring `triage: [auto]` and in an identical repo declaring none.
    - M2: over a task whose `M1` evidence is `pending`, the triage-declaring repo does not return `pass` from `task-complete`, and its status and problem set equal the undeclared repo's — the declaration changed neither the outcome nor the failure text.
    - Positive control: each pair first asserts the declaring fixture reports `triage: ok` and the silent one reports `triage: none`, raising if either fails. **The control was verified to fire** rather than assumed to: replacing the declaring fixture's `triage:\n  - auto\n` with an empty `triage:\n` produced `triage-inert: the complete declaring fixture never loaded a triage policy; the comparisons below would be vacuous.` followed by the `AssertionError`. Without the control, that same state would have made both comparisons trivially equal and the scenario would have passed while proving nothing.
    - Review:
      - Status: pass
      - Acceptance check: the checks assert the negative requirement through the public gate interface — same verdict, same failure text — rather than by inspecting whether triage was consulted. This is the third declaration surface to get this treatment (`authorize:` in 5.5.0, `precedents:` in 5.6.0, `triage:` here), and the shape is deliberately identical so a reader who has seen one recognises the others. Verifying the control this time was not ceremony: two assertions earlier in this session looked correct and were not.
      - Scope check: `git status --porcelain` shows this task modified only `scripts/validate_plugin.py`; `bin/keel.js` and `src/core/config.js` are task 1.1's completed products, unchanged here. `npm test` → `validation --all passed: baseline plus 99 scenarios.` (98 before this task).
      - Findings: none
    - Blocker: none

## 2. The boundary

- [x] 2.1 State the unattended-run boundary in the protocol and the alignment skill: what a run may do, where it stops, that it may not merge, and that Keel ships no scheduler
  - Covers:
    - keel-unattended-triage / An unattended run may open a pull request and may not merge
    - keel-unattended-triage / Keel ships no scheduler
    - keel-decision-precedent / A precedent answers a recurrence and never reclassifies a decision / A precedent cannot admit work into an unattended run
    - D1 — triage admission is an owner declaration, never a precedent inference
    - D6 — a run may open a pull request and may not merge
    - D7 — Keel ships no scheduler, and the documentation says so
    - D8 — stopping at a material decision is the designed end state
  - Touch:
    - AGENTS.md
    - src/skills/keel-align-expectations/SKILL.md
    - plugins/keel/skills/keel-align-expectations/SKILL.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: the protocol and the skill each state that an unattended run may triage, author, implement, verify, and open a pull request; that it may not merge; that scheduling belongs to the host and not to Keel; and that stopping at a material decision is the designed boundary rather than a failure
    - M2: both state that admission comes only from the declared triage policy and never from a precedent, and the portable source and its distribution copy stay byte-identical
  - Evidence:
    - Contract: sha256:3611471a89d0fb0cee5b0165d3ecbefcc83fb55e997d716a9591e320377639fa
    - M1: `python scripts/validate_plugin.py --scenario unattended-boundary` passes. `AGENTS.md` gains an `## Unattended runs` section and the skill an `## Unattended runs` heading; both carry all five asserted phrases — `open a pull request`, `may not merge`, `Keel schedules nothing`, `designed boundary rather than a failure`, and `never from a precedent`. Each phrase was chosen to carry distinguishing content: a keyword check for "unattended" would pass while the section stated none of what a run may or may not do.
    - M1.red: exit 1, `unattended-boundary: protocol omits: open a pull request` — neither document said anything about the boundary.
    - M1.green: all five phrases present in the protocol, the canonical skill, and the distribution copy. Matching collapses whitespace first, so the assertion is about the wording and not the hard-wrap layout — the lesson taken from task 3.1 of the previous change, where three phrases straddled line breaks.
    - M2: the canonical `src/skills/keel-align-expectations/SKILL.md` and its `plugins/keel/skills/` copy are byte-identical, asserted here and independently by `skill-portability-policy`.
    - M2.red: aimed by appending a newline to the distribution copy, since both checks went green in the same run and an assertion that never failed proves nothing. exit 1, `unattended-boundary: the canonical and distributed skills diverged.`
    - M2.green: copy restored from the canonical source. `npm test` → `validation --all passed: baseline plus 100 scenarios.` (99 before this task).
    - Review:
      - Status: pass
      - Acceptance check: the boundary is asserted in both places a run could read it — the resident protocol and the alignment skill — because either alone leaves a reader who consulted the other with no statement of the limit. The negative half is asserted as explicitly as the positive: `may not merge` and `never from a precedent` are the two claims that constrain, and a document stating only what a run may do would satisfy a looser check while authorizing everything by omission.
      - Scope check: `git status --porcelain` shows `AGENTS.md`, the canonical skill, its distribution copy, and `scripts/validate_plugin.py` modified — the four paths in Touch. `bin/keel.js` and `src/core/config.js` are tasks 1.1's completed products, unchanged here.
      - Findings: none
    - Blocker: none

## 3. Statements this change made stale

- [x] 3.1 Correct the config header's declaration count and document the triage policy and the unattended run
  - Covers:
    - I1 — the config header's declaration count
    - I2 — the README command block, which lists every Keel command
  - Touch:
    - keel/config.yaml
    - README.md
  - Verify:
    - Strategy: evidence-first
    - M1: `keel/config.yaml`'s header no longer says three declarations live in it, and documents `triage:` including that admission starts work and decides nothing after it, that Keel performs no fetch, and that no declaration authorizes a merge
    - M2: `README.md` documents the triage declaration, `keel triage` in the command block, the unattended-run boundary, and that scheduling is the host's `/loop` or cron rather than a Keel capability
    - M3: `npm test` passes, proving no resident-topic or docs scenario regressed
  - Evidence:
    - Contract: sha256:674b9cb70364e3d9c4c3e919ebd8bf8453b58ca4af832b2014b14eac142101b3
    - M1: `grep -c "Three independent declarations" keel/config.yaml` → `0`; the header now reads "Four independent declarations live here" and names `triage` beside the other three. The file documents that admission answers "may this begin" and nothing after it, that Keel never fetches the issue, that no key authorizes a merge, and that admission never comes from a precedent. It also records A1 explicitly — Keel cannot verify a human applied the label, so a repository whose automation can label issues has a broader policy than it appears — and states why this repository declares none.
    - M2: `README.md` gains an `### Unattended runs` section with the declaration, a worked `gh` invocation showing Keel being handed the labels rather than fetching them, why a label is the unit and what the rejected alternative would have authorized, the may/may-not list including the merge prohibition, and the note that scheduling belongs to the host. I2 is closed: the `## Commands` block now lists `keel triage --labels <l1,l2> [--json]`, so the block a reader treats as complete is complete again.
    - M3: `npm test` → `validation --all passed: baseline plus 100 scenarios.`, so no resident-topic or docs scenario regressed against the longer protocol and README.
    - Review:
      - Status: pass
      - Acceptance check: I1 is the third time this session that a config header's declaration count went stale — two → three in 5.5.0's successor, three → four here — and M1 verifies it by searching for the exact stale phrase rather than by reading the file I knew I had edited. The README section documents the *rejected* alternatives beside the chosen one, because a reader who does not know why heuristics were refused will propose them again. The `gh | xargs` example is deliberate: it shows the boundary between what the agent does and what Keel evaluates, which prose alone kept blurring.
      - Scope check: `git status --porcelain` shows `keel/config.yaml` and `README.md` modified by this task — the two paths in Touch. `AGENTS.md`, both skill copies, `bin/keel.js`, `src/core/config.js`, and `scripts/validate_plugin.py` are tasks 1.1, 1.2, and 2.1's completed products, unchanged here.
      - Findings: none
    - Blocker: none

## 4. Close

- [x] 4.1 Promote this change's spec delta into the live specs
  - Covers:
    - I3 — the live precedent spec's reclassification requirement
  - Touch:
    - openspec/specs/keel-unattended-triage/spec.md
    - openspec/specs/keel-decision-precedent/spec.md
  - Verify:
    - Strategy: evidence-first
    - M1: `keel openspec validate declare-what-may-run-unattended` passes and every `### Requirement:` and `#### Scenario:` heading in each delta appears in the corresponding live spec
    - M2: `npm test` passes after promotion
  - Evidence:
    - Contract: sha256:7109b16f9a244fc6c0d782bf215fc582e282177730b924d66f0831b5a23ec0bb
    - M1: `node bin/keel.js openspec validate declare-what-may-run-unattended` → valid. Promotion completeness checked by extracting every `### Requirement:` and `#### Scenario:` heading from each delta and asserting it appears in the live spec: 15 headings for `keel-unattended-triage`, 5 for `keel-decision-precedent`, all present. I3 is closed — the live reclassification requirement now names the unattended-run case explicitly, which is the one a reader with a store of triage history would most likely try to apply.
    - M2: `npm test` → `validation --all passed: baseline plus 100 scenarios.` after promotion.
    - Review:
      - Status: pass
      - Acceptance check: promotion verified by heading-set comparison rather than by re-reading, so a truncated or partially pasted requirement fails. The new capability spec was generated from the delta body with only a Purpose header prepended, so its text is the delta's own.
      - Scope check: `git status --porcelain` shows `openspec/specs/keel-decision-precedent/spec.md` modified and `openspec/specs/keel-unattended-triage/` added — the two paths in Touch.
      - Findings: none
    - Blocker: none

- [x] 4.2 Record the workflow change in the Keel changelog
  - Covers:
    - keel-unattended-triage / A repository declares which work may start without asking
  - Touch:
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: evidence-first
    - M1: the changelog entry states what a repository can declare, why admission had to be a declaration rather than a precedent, that Keel performs no fetch and ships no scheduler, that a run may open a pull request and may not merge, that stopping at a material decision is the designed end state, and that a repository declaring nothing is unchanged
  - Evidence:
    - Contract: sha256:6ad3f8f57b0985caaa3654ad7e38f72033daa6ae1d31c9a2794b14d929482a28
    - M1: `keel/CHANGELOG.md` gains a `## 5.7.0 - declare what may run unattended` entry stating what a repository can declare; why admission had to be a declaration rather than a precedent, tracing it to 5.6.0's own rule; why a label is the unit, with the three refused alternatives and what each would have authorized; that Keel never fetches and how that was proven; that admission decides nothing after it, with the positive control named; that a run may open a pull request and may not merge; that stopping at a material decision is the designed boundary and the policy must not be widened to prevent it; that Keel schedules nothing, as a spec requirement rather than a disclaimer; and that a repository declaring nothing is unchanged with nothing to do on upgrade.
    - M1 (the gap, named): the entry records that this repository declares no triage policy, so unlike 5.5.0 and 5.6.0 the interface ships fixture-tested rather than in use, and names #34 as the owner of that gap.
    - Review:
      - Status: pass
      - Acceptance check: the entry explains each choice by the failure it was made against rather than stating the choice alone — most importantly for the label decision, where a reader who does not know why heuristics were refused will propose them again. It states the dogfood gap plainly instead of letting two prior releases' pattern imply this one was exercised too.
      - Scope check: this task modified `keel/CHANGELOG.md` alone, the single path in Touch.
      - Findings: none
    - Blocker: none

## Invalidates

- I1: "Three independent declarations live here: fast_check, which names a command; authorize, which names repository actions ... and precedents, which points at a directory" — the header comment of `keel/config.yaml`, made wrong by this change adding a fourth. The same sentence was already corrected once this session, from "Two" to "Three". Updated by: 3.1
- I2: "# Domain lenses — user-authored guidance in keel/lenses/" and "# Install / maintenance" — the section comments inside the `## Commands` block of `README.md`, which enumerates every Keel command and now omits `keel triage`. A reader treats that block as complete, so an absent command reads as a command that does not exist. Updated by: 3.1
- I3: "A precedent MUST NOT move a decision out of the materiality categories that require asking the owner." — the reclassification requirement in `openspec/specs/keel-decision-precedent/spec.md`. Still true, but silent on the specific case this change creates, where a store of triage history is the most tempting thing a reader would try to apply. Updated by: 4.1
- I4: "the honest ceiling is a loop that runs to a branch with full gate evidence and a PR, and one human merge click" — the L3 paragraph of https://github.com/TanglmChris/keel/issues/34. Discard reason: the statement is correct and this change implements exactly it; nothing there becomes wrong, and the issue is updated on delivery rather than corrected.

## Expectation Coverage

- E1: A repository declares once, in a tracked file, which issues may start work without being asked about. Covered by: 1.1
- E2: Evaluating that declaration is local, offline, deterministic, and repeatable. Covered by: 1.1
- E3: A refusal is distinguishable from an undeclared policy. Covered by: 1.1
- E4: Admission authorizes a start and nothing after it; every later gate is unaffected. Covered by: 1.2
- E5: An unattended run may open a pull request and may never merge one. Covered by: 2.1
- E6: Stopping at a material decision is reported as the designed boundary, not a failure. Covered by: 2.1
- E7: Keel claims no scheduling capability, because `/loop` and cron belong to the host. Covered by: 2.1, 3.1
- E8: A precedent can never admit work, however much triage history the store accumulates. Covered by: 2.1, 4.1
- E9: A repository declaring no triage policy behaves exactly as it does at 5.6.0. Covered by: 1.1, 1.2
- E10: The admitting label is applied by a human, which Keel cannot verify and does not try to. Covered by: 3.1
- E11: This repository does not declare a triage policy of its own, so the interface ships fixture-tested rather than in use — unlike 5.5.0 and 5.6.0, which each dogfooded their declaration. Declaring one would start unattended work on this repository's own issues, which is the owner's decision and not this change's to make. Durable owner: https://github.com/TanglmChris/keel/issues/34
- E12: Auto-merge of a pull request. Discard reason: explicitly out of scope and forbidden by D6; merging is the last point where a human sees the whole change at once, and no declaration in Keel authorizes one.

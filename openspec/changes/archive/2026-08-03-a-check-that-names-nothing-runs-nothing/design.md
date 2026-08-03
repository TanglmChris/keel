## Context

`scripts/validate_plugin.py` owns `SCENARIOS`, an ordered registry of every validator scenario. A task contract names scenarios in its `Verify` block — that is how a check says what it will run — and the registry is the only thing that decides whether such a name resolves. Nothing compares the two.

The gap has a specific shape. A non-regression check names a scenario it is about to write, so a wrong name surfaces the moment it runs. A **regression** check names a scenario that already exists, and its wrong name surfaces as `unknown validation scenario` only if someone runs it — which is exactly the check an author under time pressure is most likely to record from memory. All three recorded occurrences of this class are regression checks.

## Goals / Non-Goals

**Goals:**
- A scenario name written into an active change's task contract is checked against the registry before the task runs.
- The report names the file, the line, and the name, so the correction needs no search.
- Zero false positives, measured against every `tasks.md` this repository has produced.
- The check itself cannot pass vacuously when there is nothing to check.

**Non-Goals:**
- The `Touch` path check, #51's other candidate (Q1). Different mechanism, different surface, and a materiality question underneath it.
- The third class #51 separates out — a check asserting a behavior that never existed. #51 already concludes it is not mechanically decidable, and red-green discipline is what holds it.
- Archived changes. A scenario rename is legitimate and must not turn history red.
- A gate diagnostic. The check reads a repository-local registry that exists only here; `keel gate task-start` runs in repositories that have no such thing.
- Recognizing every way a scenario name could be written. Two measured forms are covered; a third form is a spec change, not a bug fix.

## Decisions

- **F1** — #51 records four authored contracts naming something that did not exist, two of them scenario names: `gate-diagnostics` in `2026-08-02-a-message-that-cannot-be-true` task 1.1, and `target-surface-doctor` in `2026-08-02-surfaces-that-agree-with-each-other` task 1.1. Both were `M5 (regression)` checks, both corrected at execution time, both costing a reauthorization cycle. *Basis: the Review `Findings` of both archived tasks, at `:43` and `:41`.*
- **F2** — a fifth occurrence, unrecorded on #51: `2026-08-01-the-name-is-not-the-thing/tasks.md:132` declares `M3 (regression): \`tasks-template-validates\` … stay green`, and `git log -S"tasks-template-validates" -- scripts/validate_plugin.py` returns no commit. The name has never existed. The task recorded M3 as passing. *Basis: that grep and that git query at 5.21.0.*
- **F3** — the naive rule is unusable. Every backticked token matching `^[a-z0-9]+(-[a-z0-9]+)+$` inside a `Verify`/`Commands` `M<n>` line, across all archived changes: 55 tokens, 33 registered, **22 not**. The 22 are gate stages (`task-start`, `task-complete`, `change-close`), diagnostic codes (`record-refused`, `missing-field`, `contract-drift`, `unresolved-covers`, `missing-command-check`, `unresolved-authority`), skill names (`keel-review-checklist`, `keel-spec-driven`), capability names (`keel-openspec-surface-overlay`, `keel-surface-evolution-policy`), hook events (`subagent-start`, `subagent-stop`), and helper-authority values (`read-only-evidence-only`, `report-and-evidence-only`). Kebab-case is this project's spelling for most of its vocabulary, not for scenarios specifically. *Basis: direct measurement over `openspec/changes/archive/*/tasks.md` at 5.21.0.*
- **F4** — the `--scenario` form is exact. A token following `--scenario`, anywhere in an archived `tasks.md`: **113 references, 0 unregistered.** *Basis: the same measurement.*
- **F5** — the regression form is exact when it is keyed on the assertion, not on the token. A backticked token matching `^[a-z0-9][a-z0-9-]*$` inside a `Verify`/`Commands` `M<n>` line that also contains `stay green` / `stays green`: **30 references, 1 unregistered — F2's.** Allowing tokens with no hyphen adds no false positive and is what lets `cli` and `uninstall`, the two registered names without one, be checked at all. *Basis: the same measurement, run once with the hyphen required and once without.*
- **F6** — keying on the bare word `scenario` instead of `--scenario` is not exact. `2026-07-20-align-gate-authoring-surface` writes "the core-gates scenario `done`-accept assertion passes", where the backticked token after the word is not a name. One false positive is enough to disqualify the form. *Basis: the same measurement.*
- **F7** — both of F1's occurrences were written in F5's form: each is an `M5 (regression)` line whose surviving text reads "… stay green". The rule would have caught both at authoring time. *Basis: `:23` and `:21` of the two archived `tasks.md` files.*
- **F8** — for #51's other candidate, over the last 40 commits: 11 files were added outside `openspec/changes/`, of which 5 sat in a directory that did not exist in the parent commit — 4 of those 5 being `openspec/specs/<new-capability>/spec.md`. The one recorded `Touch` mistake named `bin/keel.js`, a file that exists. So the base rule fires 11 times and the refined rule 5 times, and neither fires on the defect. *Basis: `git log --diff-filter=A` with a `git cat-file -e <parent>:<dir>` probe per added file, at 5.21.0.*

- **D1** — two recognized forms and no others: a name after `--scenario`, and a backticked lowercase token in a `Verify`/`Commands` `M<n>` line asserting that something stays green. Each is chosen because it was measured at zero false positives over every `tasks.md` this repository has written, and the wider rule was measured and rejected rather than argued about. *Basis: F3, F4, F5, F6.*
- **D2** — the scan covers active changes only. Archived tasks record what was true when they ran, and a scenario legitimately renamed later would make history red for a reason no reader can act on. This also puts the check exactly where the value is: before the task runs. *Basis: #51's own scoping, and F2 — the archive is read once here as evidence, not as a gate.*
- **D3** — a validator scenario, failing the run, not a `task-start` warning. The registry is a fact about *this* repository; a gate that shipped to other projects could not evaluate it. A hard failure is honest at zero measured false positives, and a warning nobody must act on is how the class went unnoticed five times. *Basis: F3–F6, and #51's own placement of this candidate in the suite.*
- **D4** — the extractor is a pure function over text plus a name set, and the scenario drives it two ways: against synthetic `tasks.md` content with a synthetic registry, where every branch is asserted, and against this repository's real active changes with the real registry. The synthetic half is where the assertions live, because the live half's input is whatever happens to be in the tree. *Basis: D2 — the live set is normally empty, since a change is archived when it closes.*
- **D5** — the live half carries a positive control: the scenario asserts that a reference planted into a copy of the real tasks content is reported, so a run that passes because the extractor silently found nothing is distinguishable from a run that passes because the names are right. Both an empty active set and a broken extractor produce the same green otherwise. *Precedent applied: `an-assertion-that-never-failed-proves-nothing` — a check whose passing condition is agreement or absence needs a positive control, not only a red. Without it this would have been a question about whether an empty active set should fail.*
- **D6** — the report names the path, the 1-indexed line, and the token, and states the two recognized forms. A name that is wrong is usually wrong by one word, so the correction is a search away only if the message withholds where it is. *Basis: F1 — both recorded corrections were found by executing the check, which is the search this message replaces.*

## Hidden Knowledge / Assumptions

- **A1** — a registered scenario name matches `^[a-z0-9][a-z0-9-]*$`. All 130 currently registered names do, and only `cli` and `uninstall` carry no hyphen. If a future name breaks the shape, references to it are not checked rather than wrongly reported. *Basis: the registry at 5.21.0. Owner: this change — the failure mode is the pre-change behavior for that one name.*
- **A2** — a `tasks.md` under `openspec/changes/` whose parent directory is `archive` is archived, and everything else there is active. This is the layout every other reader in the repository already assumes. *Basis: `openspec/changes/archive/` as used by the gates and by `openspec archive`. Owner: this change.*

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- A reference written in neither form is not checked. That is the deliberate trade for zero false positives, and it is stated in the spec so a later author reads it as a boundary rather than discovering it as a hole. The two forms cover every scenario reference in the archive.
- The check reads the registry by parsing `SCENARIOS` out of the validator's own source rather than importing it, because the scenario runs inside that same file. It is a text parse of a literal this repository owns and keeps flat.

## Open Questions

- **Q1** — should `keel gate task-start` warn on a `Touch` path that does not exist? #51 offers it as a candidate and states two examples that cannot both be satisfied: a new file the task will create and a mistyped filename are indistinguishable on disk, since both are a missing path under an existing parent. F8 measures both proposed criteria against real history: the base rule ("any missing path") fires on 11 legitimately added files in 40 commits, the refined rule ("missing path with a missing parent") on 5, four of which are the `openspec/specs/<new-capability>/spec.md` every capability-adding change creates — and neither fires on the one recorded `Touch` mistake, which named an existing file. Shipping either adds a warning that, on this repository's evidence, would have been wrong every time it fired; this project has already recorded on #58 what repeated false positives cost a check. Whether to accept that trade is user-visible gate behavior and the owner's call. **This question opens no `Covers` entry and blocks no task in this change** — nothing here touches `task-start`. *Durable owner: https://github.com/TanglmChris/keel/issues/51, where the measurement is recorded so a later run authoring against that candidate finds it before writing either rule.*

## Alignment

Ran `keel-align-expectations` before tasks finalized. No `keel/lenses/` directory exists, so the domain-agnostic path applied. The declared precedent store `../decision-precedents` is present and was consulted: `an-assertion-that-never-failed-proves-nothing` (category: acceptance, status: recorded) decided D5 in the owner's place and is cited there; the other two precedents did not match a decision here.

Quick path for the work itself: the request, the reproduction, and the intended observable outcome agree, and the whole effect is one validator scenario with no product surface. Deep path fired once, on Q1 — the issue's own two examples contradict each other, and the measurement says the check as specified would be wrong more often than right.

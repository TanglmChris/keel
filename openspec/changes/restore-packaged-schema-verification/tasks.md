## 1. The packaged-schema assertions run

- [x] 1.1 The helper resolves the root the installer reads, and fails when it cannot
  - Covers:
    - keel-validation-runner / A derived assertion set that collapses to empty fails instead of passing / A missing packaged asset root fails loudly
    - keel-validation-runner / A derived assertion set that collapses to empty fails instead of passing / An empty derived set is a failure, not a pass
    - keel-validation-runner / A derived assertion set that collapses to empty fails instead of passing / The packaged schema install surface is actually verified
    - F2 the installer reads assets/openspec/schemas/keel-spec-driven and writes openspec/schemas/keel-spec-driven
    - D1 the helper raises on a missing root rather than returning an empty set
    - D5 the new scenario asserts on emptiness, not on a pinned filename list
    - A1 the restored assertions have never executed and their first-run outcome is recorded as evidence
  - Touch:
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: new scenario `packaged-schema-derivation` — the helper raises, naming the path it expected, when handed a root that does not exist, and against the real root returns a non-empty set of consumer-repo paths matching the files the installer's own action list writes
    - M2: the restored assertions bite — removing an installed schema file from the fixture repo fails `cli` and `thin-native-install` by name, and leaving one behind after removal fails `uninstall`; the identical fixture perturbations passed before the helper was repointed
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:bfcada61153cd2f59929ca90387ac26cd4a43940538daff59121549c7ab9b307
    - M1: pass. New scenario `packaged-schema-derivation`. Handed a root that does not exist the helper raises `FileNotFoundError` naming that path; against its default root it derives five consumer-repo paths, and those paths equal exactly the files a real `keel --install` writes under `openspec/schemas/` in a temporary repository. The comparison is against installer output, not against a pinned filename list, so adding a template changes both sides together (D5).
    - M1.red: captured twice. With the helper still answering `[]` for an absent root the scenario failed `returned a set for a missing packaged root instead of failing; an absent root must not silently empty its callers' assertions`. Adding the raise but keeping the old root then failed with `packaged OpenSpec schema root is missing: …\dist\shared\assets\openspec\schemas\keel-spec-driven` — the helper's own default root proving it does not exist.
    - M1.green: root repointed at `assets/openspec/schemas/keel-spec-driven`, the root `install_to_repo.openspec_schema_actions` reads; scenario exits 0.
    - M2: pass, and the decisive case is `thin-native-install`. Deleting `openspec/schemas/keel-spec-driven/templates/tasks.md` from the installed fixture now fails it with `missed OpenSpec schema file: openspec/schemas/keel-spec-driven/templates/tasks.md`. In `cli`, deleting `schema.yaml` after install now fails with `keel --install missed file: openspec/schemas/keel-spec-driven/schema.yaml`. **Recorded honestly:** `cli` and `uninstall` each have an adjacent net — `keel --check` reports `not installed`, and a leftover file keeps the schema directory alive — so for those two the fix changes which assertion fires and how precisely it names the fault, not pass to fail. `thin-native-install` had no such net.
    - M2.red: with the helper reverted to `dist/` + `return []` and the identical deletion in place, `thin-native-install scenario passed.` and exited 0 — a consumer repository missing a packaged schema template was verified as correctly installed. That is the coverage this task restores. Under the same revert `cli` still failed, but at `keel --check did not report installed`, never mentioning the schema.
    - M2.green: helper repointed; both deletions fail their own scenario by name, and with no deletion the four restored scenarios (`cli`, `uninstall`, `thin-native-install`, `native-plugin-install-matrix`) pass.
    - A1 outcome: all four restored scenarios passed on their first-ever real execution, so no product defect was hiding behind the vacuity. This change is coverage restoration only; no reauthorization was needed.
    - Review:
      - Status: pass
      - Acceptance check: M1 asserts the helper against what `keel --install` actually writes into a temporary repository, which is the consumer-visible behavior, and against a raise rather than a return value for the missing-root branch — both through the interface a scenario author meets. M2 proves the restored assertions are load-bearing by perturbing installed state and observing the specific diagnostic, with `thin-native-install` giving a clean pass-to-fail transition rather than a message change. The three covered spec scenarios map directly: missing root to M1's first branch, empty derived set to M1's second, and the install surface being actually verified to M2.
      - Scope check: only `scripts/validate_plugin.py` changed, which is the sole declared Touch path; `git diff --stat` shows one file, +69/-10. All four mutations (two fixture deletions, two helper reverts) were removed by restoring a byte copy taken before the first mutation, and `grep MUTATION` returns nothing. `npm test` passes with baseline plus 76 scenarios.
      - Findings: none
    - Blocker: none

## 2. Retired paths stop being referenced

- [ ] 2.1 Remove the dead references and lock the class out
  - Covers:
    - keel-validation-runner / A derived assertion set that collapses to empty fails instead of passing / Retired distribution paths are not referenced
    - F1 dist and src/assets do not exist and are asserted not to exist
    - F3 run_keel_hook has zero callers
    - D2 the compact-task-authoring projection loop is deleted rather than repointed
    - D3 run_keel_hook is deleted and the hygiene loops are repointed at the roots package.json ships
    - D4 the duplicated source and dist pass in validate_openspec_schema is collapsed
  - Touch:
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: a baseline assertion fails when the validator's own source resolves a path under a retired distribution tree, naming the tree and the offending expression; it fails today and passes once the references are gone
    - M2: the deletions cost no live coverage — with `SCHEMA_COPY_PAIRS` pointed at a deliberately divergent pair, `invalidation-authoring-surface` still fails on the divergence the removed projection loop was meant to catch, and `validate_openspec_schema` still reports a missing packaged schema file
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Invalidates

- I1: "compact-task-authoring already means to assert they agree, but its canonical root does not exist in this layout, so its rglob compares nothing" — the comment above `validate_invalidation_authoring_surface_scenario` in `scripts/validate_plugin.py`. It explains this scenario's existence by pointing at a loop that will no longer be there. Updated by: 2.1
- I2: "Validator at **75 scenarios**" and "the dead loop itself is issue #18" — the 5.3.3 entry in `keel/CHANGELOG.md`. Discard reason: changelog entries are dated records of what a release contained, and both statements were true of 5.3.3; the count moves in the new entry rather than by rewriting the old one. Recorded because a symptom search for the scenario count lands here first and the reader deserves to know it is history, not a current claim.

## Expectation Coverage

- E1: whether `keel --install` writes the packaged OpenSpec schema into a consumer repo, and whether `--uninstall`/`--clear` remove it, is actually verified Covered by: 1.1
- E2: a derived assertion set that collapses to empty fails instead of reporting success Covered by: 1.1
- E3: the validator holds no reference to a distribution tree the repository asserts has been removed Covered by: 2.1
- E4: a restored assertion may fail on first execution, exposing a real product defect. Durable owner: openspec/changes/restore-packaged-schema-verification/design.md
- E5: the same vacuity class can exist outside `scripts/validate_plugin.py` — any derived set in `src/core` or the plugin scripts. Discard reason: out of scope; the requirement added here states the rule for validator assertions, and no second instance was found by the retired-path sweep that motivated this change.

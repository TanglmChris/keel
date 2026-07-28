## 1. The dry run tells the truth in both directions

- [x] 1.1 Classify overlay surfaces in the dry run, and let --check reach it
  - Covers:
    - keel-target-surface-diagnostics / A dry run accounts for every write its real run would make / The plan covers steps the enumerated plan does not
    - keel-target-surface-diagnostics / A dry run accounts for every write its real run would make / A dry run does not claim writes that will not happen
    - keel-target-surface-diagnostics / A dry run accounts for every write its real run would make / Both paths share one definition of pending work
    - F1 --check never reaches the overlay step
    - F2 the dry-run branch lists every surface without reading one
    - F3 the real run's classification is a pure read-and-compare
    - D1 the dry run computes the classification rather than listing
    - D2 the dry run reports in the real run's shape
    - D3 --check calls the overlay dry run after the installer plan
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: with exactly one overlay surface stale, `keel --check` names that one file and no other, and `keel --install --dry-run` agrees with it — where before, `--check` said nothing and `--install --dry-run` named all six
    - M2: the counts a dry run reports equal the counts the real run reports immediately afterwards, for a stale surface, an already-current one, and a missing one
    - M3 (regression): `keel --install` still writes exactly what it wrote before — the dry run gained a classification, the real run kept its own
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:e5a180328c5f84bc7d7d81bff04e6a39359ac51ad8d8926b07d8cad181bc5e31
    - M1: pass. New scenario `dry-run-overlay-accounting`, plus the real repository. With exactly one of six overlay surfaces stale, `keel --check` names that one file and prints `refreshed=1 current=5 missing=0`, and `keel --install --dry-run` prints the identical pair of lines. With nothing stale, both report `refreshed=0 current=6 missing=0` and name no file at all.
    - M1.red: captured separately for each half, because they were two independent defects. Removing the overlay call from the `check` action reproduced #27 exactly — the scenario failed `--check did not name exactly the one stale surface` with `(no overlay output)`, an empty plan for a run that writes. Restoring the old unconditional listing made the dry run print all six surfaces for one stale file, failing on the same assertion from the opposite direction.
    - M1.green: the dry run reads and compares like the real run, so it names exactly what would change; `--check` calls it after the installer plan.
    - M2: pass. The plan's counts equal the real run's: the dry run promised `refreshed=1 current=5 missing=0` and the install immediately afterwards reported `refreshed=1 current=5 missing=0`, then the stale marker was gone. The scenario asserts this equality on a fixture rather than trusting the two code paths to stay aligned, and covers the current and missing classifications as well as refresh.
    - M2.red: under the removed-call state the plan reported no counts at all while the real run immediately afterwards reported `refreshed=1 current=5 missing=0`, so plan and outcome could not be compared, let alone agree. Under the unconditional-listing state the dry run contradicted itself, naming six files above a `refreshed=1` summary.
    - M2.green: both paths derive their counts from one read-and-compare, so a change to what counts as current cannot move one without the other.
    - M3: pass. `keel --install` writes exactly what it wrote before — the dry run gained the classification, the real run kept its own branch unchanged. Verified on the real repository: the stale marker was refreshed to `5.3.5` and nothing else changed, and the dry runs beforehand left the file untouched at its rolled-back value. `npm test` passes with baseline plus 81 scenarios.
    - Review:
      - Status: pass
      - Acceptance check: the checks run the real CLI and compare its two dry-run entry points against each other and against the real run's own report, which is the only way to prove the property in question — that a plan and its outcome agree. Both directions of the requirement are asserted separately: naming a write that will not happen, and omitting one that will. The three covered scenarios map directly to M1's two halves and M2's equality.
      - Scope check: two files changed, `bin/keel.js` and `scripts/validate_plugin.py`, both declared in Touch. Both reds were reverted from a byte copy of `bin/keel.js`; the `.claude/` marker used to reproduce the defect on the real repository was restored with `git checkout`, and `git status` shows only the two Touch files and this change's own directory.
      - Findings: `## Invalidates` and `## Expectation Coverage` are absorbed into the last task's `Evidence` field — the field parser appends every non-field line to the current field, and a `##` heading does not terminate it. So an unfilled-slot token quoted inside either section makes the whole Evidence non-concrete, and `task-start` reports `Evidence must be concrete` while pointing at a task whose Evidence is fine. It bit this very task: I1 quotes the log line this change rewrites, which contains two angle-bracket tokens. The fingerprint half of 5.3.3's claim holds — verified, an added entry leaves the last task's fingerprint byte-identical — but "stays outside every task body" does not. Worked around by paraphrasing the quoted tokens. Durable owner: https://github.com/TanglmChris/keel/issues/29
    - Blocker: none

## Invalidates

- I1: "would refresh OpenSpec … overlay in …" printed once per known surface (the line quotes an action name and a path; the literal token forms are omitted here to work around issue #29) — the dry-run branch of `refreshOpenSpecSurfaceOverlay` in `bin/keel.js`. The line survives but stops being unconditional, so a reader can no longer take it as a list of all surfaces. Updated by: 1.1
- I2: "`keel --check` prints an empty dry-run plan while `keel --install` reports `refreshed=1`" — issue #27's reproduction and the Findings line of task 1.1 in `openspec/changes/archive/2026-07-28-the-suite-does-not-write-to-the-repo/tasks.md`. Discard reason: both are dated records of the defect being fixed here; the archive is historical evidence by definition and the issue is closed with the correction.

## Expectation Coverage

- E1: a reader of the dry run learns about every file the real run would change Covered by: 1.1
- E2: a reader is not told about files that will not change Covered by: 1.1
- E3: the two paths cannot drift, because they share the classification Covered by: 1.1
- E4: the overlay refresh still lives outside the Python installer's action plan, so the two halves of a real install are reported by two mechanisms. Discard reason: accepted as design non-goal; unifying them relocates working product code to fix a reporting defect, and the reporting is now correct either way.

## Context

`OPENSPEC_OVERLAY_ACTIONS` (`bin/keel.js:82`) is `["propose", "apply", "archive", "sync"]`. `overlayActionLabel()` (`bin/keel.js:1085`) joins that list minus `propose` — propose governs authoring rather than a state-changing command, and the doctor line counts command surfaces.

Three places report an action label. Two derive it; one states it.

| Line | Source | Asserted |
| --- | --- | --- |
| `--uninstall` removal summary (`bin/keel.js:1263`) | `overlayActionLabel()` | counts only |
| `--doctor` overlay health (`bin/keel.js:1459-1465`) | `overlayActionLabel()` | literal, 4 sites |
| refresh summary (`bin/keel.js:1306`) | literal `apply/archive` | nothing |

## Goals / Non-Goals

**Goals:**

- The refresh summary reports the managed action set rather than a remembered copy of it.
- A check fails when the refresh label and the doctor label stop agreeing.

**Non-Goals:**

- Changing which actions receive the overlay, or `overlayActionLabel()`'s exclusion of `propose`.
- Changing the counts (`refreshed=` / `current=` / `missing=`) or the per-surface dry-run lines.
- Converting the doctor assertions from literals to derivation. They work; this change is about the line that has none.
- Making the summary line machine-readable. It is human-facing output and stays prose.

## Decisions

- D1 — Derive the label from the managed set rather than correct the literal to `apply/archive/sync`. Basis: correcting the literal reproduces the defect one action later, and the function that ends it already exists three lines away and is already used by the two sibling lines. The issue names this implementation directly.

- D2 — Assert by comparing the refresh label against the doctor label from the same repository, with a positive control requiring both lines to be present and non-empty. Basis: precedent `an-assertion-that-never-failed-proves-nothing`. A check whose passing condition is *agreement* also passes when the mechanism producing both sides is broken — here, when a regex matches nothing and both sides come back empty. The control is what distinguishes "the two agree" from "neither was found". *Precedent applied: `an-assertion-that-never-failed-proves-nothing`.*

- D3 — Pin the pair transitively rather than writing a second literal. Basis: the doctor label is already asserted as the literal `apply/archive/sync` at `scripts/validate_plugin.py:2547` and `:2570`. Comparing refresh to doctor means an action joining the set needs exactly one literal updated, and the line this change is about follows automatically. A second literal here would be a third copy of the string whose copies caused the defect.

- D4 — Split each new assertion so it carries its own message. Basis: `OR_GUARDED_ASSERTION_SITES` in `scripts/validate_plugin.py` is a recorded count that fails in both directions, and one condition guarding two failures names the wrong cause whenever the other fires. Four distinct failures are reported distinctly: the refresh line is absent, the doctor line is absent, the labels disagree, and the label is empty.

- F1 — Nothing consumes the refresh summary line. Basis: `grep -rn "overlay refreshed"` over the tree on 2026-08-04 finds only its own definition; the one nearby suite reader (`scripts/validate_plugin.py:4137`) matches `would refresh OpenSpec` together with `.md`, which is the per-surface dry-run line, not this summary.

- F2 — Neither the removal nor the refresh side is currently pinned to a wrong literal. Basis: `uninstall-removes-the-overlay` M4 asserts `removed=` / `absent=` counts and not the label, so no existing assertion has to move for this change to land.

- F3 — The defect reproduces at 5.24.0 on the current tree. Basis: measured 2026-08-04 in a scratch repository — `--init` printed `OpenSpec apply/archive overlay refreshed=8 current=0 missing=0` and `--uninstall` immediately after printed `OpenSpec apply/archive/sync overlay removed=8 absent=0 missing=0`.

## Hidden Knowledge / Assumptions

- A1 — The `openspec-surface-overlay` scenario is the right home for the assertion. Basis: it already installs both targets, already captures the init stdout that carries the refresh line, and already owns the doctor label assertion the comparison depends on. Adding a scenario would duplicate two installs to assert one line.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- The transitive pin means a wrong doctor literal would make a wrong refresh label pass. Accepted: that literal is asserted at two sites against real output, and the alternative — a third independent copy of the same string — is the failure mode this change exists to remove.
- Output text changes for `--init` / `--install` / `--check`. Accepted as the point of the change; no parser depends on it (F1).

## Open Questions

None.

## Context

Issue #236.

## Facts

- F1 — `withEvidenceSlots` in `src/core/gates.js` appends every missing slot at the end of the Evidence block.
- F2 — `capsuleSlots` lists slots as Contract, each check's bare, `.red`, `.green`, `.detects`, then Review, Blocker, Reauthorizations, and the bundled `assets/openspec/schemas/keel-spec-driven/templates/tasks.md` uses the same order. The issue's "template order" with Blocker and Reauthorizations before the checks is the order this repository's own changes were written in, not the bundled template's.
- F3 — An Evidence slot is a line at four spaces, `    - <key>:`, followed by its more deeply indented lines, which only Review has.

## Decisions

- D1 — The canonical order is the one F2 names, already shared by `capsuleSlots` and the bundled template; neither changes.
- D2 — Walking the slots in that order, a missing slot goes directly after the extent (F3) of the last slot already placed, whether present or just added; before any, it goes first in the block. Present slots are never moved.

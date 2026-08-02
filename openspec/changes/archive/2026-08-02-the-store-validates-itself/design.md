## Context

The repository validates a great deal and never validated the one artifact it publishes. Each change's closing task runs `openspec validate <change> --strict`, which reads the change directory; the published store under `openspec/specs/` was read by nothing. Issue #46 found 8 of 21 specs failing strict validation and noted that the failures "从来没有出现在任何人面前" — they had never appeared in front of anyone.

## Goals / Non-Goals

**Goals:**
- The published spec store is validated by the validator Keel ships, inside `npm test`.
- A failure names which specs failed, so the next action is fixing a spec rather than re-running the command by hand.
- The check states which OpenSpec answered, because a validation result describes the program that produced it.

**Non-Goals:**
- Rewriting specs. The store is already at zero failures; this change adds the check that keeps it there.
- A tolerated failure count. See D2.
- Changing what any Keel command does. This is coverage of an existing artifact.

## Decisions

- **F1** — no scenario runs `--specs`. Measured 2026-08-02 at 5.16.0: `grep -c '\-\-specs' scripts/validate_plugin.py` returns 0. *Basis: direct execution.*
- **F2** — the published store passes under the validator this repository pins, and the 8 failures #46 recorded were never a result from it. Measured 2026-08-02 at 5.16.0: `node_modules/.bin/openspec` is 1.6.0 and reports `Totals: 21 passed, 0 failed (21 items)`; bare `openspec` on PATH here is **1.4.1** and reports `Totals: 13 passed, 8 failed`, naming the same eight specs #46 lists, in the same order. #46 records its measurement as "openspec 1.6.0". It is 1.4.1's output. *Basis: both binaries executed directly and their outputs compared.*
- **F4** — the suite's existing `run_openspec` helper resolves through `shutil.which("openspec")`, so every scenario using it reads PATH rather than the pinned dependency. That is how this change's first draft reproduced #46's 8 failures and briefly believed them current. *Basis: `scripts/validate_plugin.py:10673`.*
- **F3** — the repository already has a shape for this: `A shipped template is validated by the tool that consumes it` requires assertion through the consuming tool rather than through prose, and its third scenario reports a skip when that tool is unavailable. The new requirement is the same idea applied to the store instead of the template. *Basis: `openspec/specs/keel-validation-runner/spec.md:184-198`.*
- **D1** — the assertion is absolute: zero failures, and the failure message names the failing specs. *Basis: F2 — the store is at zero, so an absolute assertion is available now and costs nothing.*
- **D2** — no ratchet. #46 proposed recording the current failure count and reducing it, which was the right shape for the count it believed it had. Under the pinned validator that count is and was 0, so there is nothing to ratchet down from, and a recorded tolerance would be a budget for failures to hide in. *Basis: F2.*
- **D4** — the scenario resolves `node_modules/.bin/openspec` and reports a skip when it is absent, rather than falling back to PATH. Falling back is what produced the mistaken reading this change was nearly authored on, and `keel-target-surface-diagnostics` already forbids it: a suite that silently changes which program it runs reports facts about a different program. Repairing `run_openspec` for the scenarios that share it is real work and is not bundled here. *Basis: F2, F4.*
- **D3** — the scenario reports the OpenSpec version it exercised, and reports a skip rather than a pass when no validator resolves. Both follow the repository's existing treatment of a consuming tool: a result that does not say which program produced it describes a program nobody can identify, and a silent pass on an absent tool is the failure mode `The consuming tool is unavailable` already exists to prevent. *Basis: F3, and `keel-target-surface-diagnostics` requiring validation to assert the OpenSpec version it tests against.*

## Hidden Knowledge / Assumptions

- **A1** — `openspec validate --specs --strict` exits non-zero when any spec fails, and its output names each failing spec on its own line. The scenario reads both the exit status and the per-spec lines so it does not depend on either alone. *Basis: observed output `✗ spec/<name>` per failure and `Totals: N passed, M failed`; verified before authoring. Owner: this change — if the output shape moves, the scenario fails loudly rather than passing silently, which is the correct direction for a check whose whole purpose is to not be silent.*

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- A spec written in the repository's house style — background paragraph first, modal verb after — now fails `npm test`. That is the point, and it is a wording fix with no semantic content. The alternative is what #46 documented: the failure exists for months and is found by a consumer.
- The check reads whichever OpenSpec resolves, which 5.15.0 established may differ from what a repository declares. Mitigated by D3: the scenario states the version, so a result is attributable.

## Open Questions

None.

## Why

Issue #213: `keel --doctor` in rtl_ppa_prj reports eight `state-error`s against one active `tasks.md`, which fails every session's state check there. Each is correct work:
- A Scope check names the base it compared against (`base 1f3a6b0`). `keel-review-checklist` asks for exactly that.
- An Acceptance check names the input commit a result ran on (`P2 55/55 on dec4d6e`).
- An Acceptance criterion bounds scope relative to a base (`after synchronized base dec4d6e`).
- A sentence says the verifier saw `no dirty groups`, which is the cache buffer under test.
- A sentence says no edits were copied `from uncommitted Claude changes`, a negation about another checkout.

The rule refuses a hash-shaped token anywhere on a line that carries a context word anywhere. It also refuses `dirty` and `uncommitted` anywhere. Inside a task's fields, that reads cited provenance as recorded state. Rewording line 262 would also move a completed task's contract fingerprint.

## What Changes

- Inside a task field, the check refuses a hash only when a state claim binds it: a context word directly naming it (`commit a1b2c3d`, `HEAD is at a1b2c3d`, `已提交 a1b2c3d`), or the hash followed by `committed`, `merged`, or `pushed`.
- Inside a task field, the check refuses `dirty` and `uncommitted` only as a claim about the work's state: predicative (`is still uncommitted`, `was dirty`) or a `Status:`/`State:` value. Attributive and negated uses pass (`no dirty groups`, `from uncommitted Claude changes`). `not committed` and `pending commit` stay refused.
- Lines outside any task field (task titles, headings, notes sections) keep the line-wide rules.

## Capabilities

### Modified Capabilities
- `keel-stateless-continuity`: a third bound on what the state rules read, beside the `Covers` field and quoted spans.

## Impact

`scripts/install_to_repo.py` (`check_tasks_semantics`), `scripts/validate_plugin.py` (a new scenario), and the published spec. No gate, contract, or fingerprint changes. rtl_ppa_prj needs no edit and only refreshes its protocol.

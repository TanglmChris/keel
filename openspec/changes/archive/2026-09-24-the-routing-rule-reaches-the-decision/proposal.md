## Why

Routing — deciding whether a piece of work opens an OpenSpec change at all — is the first
decision in every session, and it is the only durable rule in Keel that is neither installed,
declared, nor gated (#131).

Measured at 5.62.0:

- `assets/bootstrap/AGENTS.md`, the block `keel --init` writes into a consuming repository, is
  **9 lines and 5 bullets**: session start, the capsule and its gates, write ownership,
  projections as disposable views, and where the plugin comes from. **Not one word about
  routing.**
- `grep -rn "Full mode\|Lite mode\|full_mode\|routing" src/ bin/` returns two unrelated hits.
  There is **no routing machinery at all**. The rule is four lines of prose at `README.md:271`.

So the decision falls back to whatever the project wrote in its own `AGENTS.md` by hand — the
duplication `keel --init` exists to remove — or to the agent having read Keel's README.

The rule is also size-based, and size is the wrong axis for some repositories. The reporting
project's durable asset is an append-only `results/experiments.jsonl`: a schema change is a
one-field diff, so size routes it to Lite, while it is the highest-risk change in the repository —
two months of records depend on every existing field keeping its meaning, and nothing is
backfilled, so a bad decision is not revertible by editing the file. The heaviest process is
needed and the heuristic gives the lightest.

A lens cannot carry the exception: a lens loads when a *change's* artifacts or Touch match it, and
routing decides whether that change is created. It fires strictly too late.

## What Changes

- **The rule is installed.** The bootstrap gains one line naming Full and Lite, the size
  heuristic, and that a project may declare paths the heuristic gets wrong. One line, inside the
  block's existing 12-line budget, because the budget is the mechanical form of the same token
  discipline #135 is about.
- **`full_mode_paths:` in `keel/config.yaml`**, one entry per path, each carrying **the reason it
  must route Full**:

  ```yaml
  full_mode_paths:
    - results/experiments.jsonl: append-only; a one-field diff is not revertible
  ```

  The reason is required, not decoration. A bare path says *this file is special* and the agent
  still cannot recognise the sibling nobody listed; the reason is the part that transfers, which
  is the precedent store's own founding principle applied to a declaration.
- **One direction only.** There is no `lite_mode_paths`. A project wanting less process declares
  nothing. Every other declaration in this file removes a confirmation and never a gate, and a
  routing entry that held work *out* of the flow would be the first to break that. Recorded as the
  precedent `a-declaration-raises-the-floor-never-lowers-it`.
- **An unreadable declaration routes everything Full**, and says so. This is the opposite of
  `authorize:`'s fail-closed and the same principle: those fail toward *more* human involvement,
  and for this declaration more involvement is more Full mode, not less.
- **`keel context` reports the declared paths** when there are any, so the rule and its exceptions
  arrive at the one moment the decision is made. Silent when nothing is declared.

## Capabilities

### New Capabilities

- `keel-full-lite-routing`: the routing rule is carried to the agent that decides, and a project
  declares the paths the size heuristic gets wrong, each with its reason.

### Modified Capabilities

None.

## Impact

- `src/core/config.js` — a third reader, for `- <path>: <free-text reason>` entries.
- `src/core/context.js` — the `Routing:` line and the unreadable-declaration warning.
- `bin/keel.js` — the doctor surface for the declaration.
- `assets/bootstrap/AGENTS.md` — one line, and the resident-block topic that pins it.
- `README.md`, `keel/config.yaml` — the declaration documented where a project reads forms from.
- **Keel carries the rule and does not enforce it.** Routing happens before a change exists, so
  there is nothing for a gate to hold; what Keel can do is make sure the rule and the project's
  exceptions are in front of the agent at the moment it decides, instead of in a README it may
  never open.

## Why

5.5.0 gave a repository somewhere to say which *actions* may proceed unattended. 5.6.0 gave it
somewhere to record *why decisions went the way they did*. Neither says which **work** may be
started without asking, so an unattended run has nothing to consult at the moment it matters most:
an issue arrives and something must decide whether it becomes a change at all.

That decision cannot be reached by precedent. "Should this issue be done" is a product decision in
the materiality list, and `keel-decision-precedent` forbids a precedent from moving a decision out
of that list — deliberately, because a system that can learn its way out of asking drifts toward
asking nothing at a rate nobody notices. The only route left is the one standing authorization
already established: the owner declares it, and the declaration *is* the decision rather than an
inference about one.

## What Changes

- `keel/config.yaml` gains a `triage:` declaration naming which issues may enter the pipeline
  without asking. Absent declaration means nothing may, which is today's behavior.
- A new `keel triage` command evaluates that declared policy against issue attributes **passed to
  it on the command line** and returns `admit` or `refuse` with the reason. Keel performs no
  network access: the agent fetches with `gh` and feeds the attributes in, so the command stays
  local, offline, deterministic, and model-free like every other Keel gate.
- The protocol states what an unattended run may and may not do. It may triage, author, implement,
  verify, and open a pull request. It must still stop at every material decision the existing
  alignment gates catch, and it may not merge.
- **Keel ships no scheduler.** `/loop` and cron are host capabilities; Keel's part is making each
  step decidable with authority. Documentation says so rather than implying Keel drives the loop.

No breaking change: a repository that declares no triage policy admits nothing, which is exactly
how every repository behaves at 5.6.0.

## Capabilities

### New Capabilities
- `keel-unattended-triage`: how a repository declares which work may start without asking, how that
  declaration is evaluated without network access, what an unattended run may and may not do, and
  why admission is a declaration rather than an inference.

### Modified Capabilities
- `keel-decision-precedent`: state explicitly that triage admission is outside what a precedent may
  supply, so the two mechanisms are not confused as the store grows.

## Impact

- **Code**: `src/core/config.js` (triage declaration), `bin/keel.js` (the `triage` command, help,
  doctor surface), `src/skills/` and the `plugins/keel/skills/` copies, `AGENTS.md`, `README.md`,
  `scripts/validate_plugin.py`, `keel/CHANGELOG.md`.
- **Dependencies**: none added.
- **Risk — an over-broad triage policy starts work nobody chose.** This is the change's central
  risk and the reason admission is a label allowlist rather than a heuristic: a label is applied by
  a human to a specific issue, so the declaration authorizes a *class the owner curates one issue at
  a time*, not a guess about which issues look simple. Mitigated further by the run stopping at any
  material decision and by never merging.
- **Risk — the loop appears more autonomous than it is.** A run that stops at a genuine product
  decision is the designed outcome, not a failure. Mitigated by the protocol and documentation
  stating the stop condition as the expected end state rather than an error path.
- **Risk — pressure to let Keel fetch.** Reading an issue from Keel would be convenient and would
  cost the properties that make its results worth trusting (issue #33). Mitigated by the command
  taking attributes as arguments, which also makes it testable without a network.
- **Out of scope**: scheduling of any kind; merging a pull request; and any network access from
  Keel itself.
- **Authority**: issue #34 and its decision comments.

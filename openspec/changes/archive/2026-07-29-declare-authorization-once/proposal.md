## Why

Keel interrupts for confirmations the repository owner has already decided, and it interrupts
again next session because the decision lived only in chat. `keel/config.yaml` can already hold a
project-level declaration (`fast_check`), and the task capsule already has authorization
vocabulary (`Autonomy boundary:` / `Pre-authorized fallback:`), but there is no way to declare an
authorization **once** in a tracked file and have every later task inherit it. The consequence is
that autonomy today is bought with host-level bypass — an unauditable silence — instead of a
declaration that can be reviewed, diffed, and revoked.

## What Changes

- `keel/config.yaml` gains an `authorize:` block declaring standing authorization for named
  repository actions (`commit`, `push`, `release`). Absent or empty means today's behavior.
- `keel gate task-start` injects the declared authorization into the compiled capsule's autonomy
  boundary when the task itself declares none, replacing the `Default: hard-stop` fallback for
  those actions only. An explicit task-level `Autonomy boundary:` still wins.
- The compiled capsule and gate JSON name the authorization source, so a reader can tell an
  inherited authorization from a task-authored one.
- The `apply` and `archive` OpenSpec overlays gain a rule directing the agent to consult the
  declared authorization instead of re-asking for a confirmation the owner already granted.
- Standing authorization authorizes an **action**, never the proof of it: a declared `push` does
  not survive a failing gate, and no declaration suppresses evidence, Review, or a gate result.
- Declaration cannot authorize outside its own vocabulary; an unknown action name is a
  configuration error naming the accepted names, not a silent grant.

No breaking change: a repository that declares nothing behaves exactly as it does at 5.4.0.

## Capabilities

### New Capabilities
- `keel-standing-authorization`: how a repository declares standing authorization for named
  actions, how a task inherits or overrides it, what it can never authorize, and how the
  authorization source is reported.

### Modified Capabilities
- `keel-task-capsule`: capsule compilation resolves the autonomy default from the declared
  authorization when the task declares none, and names the declaration as that entry's source.
- `keel-openspec-surface-overlay`: the apply and archive overlays direct the agent to the declared
  authorization instead of a repeated confirmation.

## Impact

- **Code**: `bin/keel.js` (config reader, overlay bodies), `src/core/task-contract.js` (autonomy
  resolution), `src/core/gates.js` (source reporting), `keel/config.yaml` (this repo's own
  declaration), `README.md`, `scripts/validate_plugin.py`.
- **Dependencies**: none added. The config reader stays hand-rolled; the package has one runtime
  dependency and zero devDependencies, and a YAML library would be the first new commitment for a
  format Keel controls.
- **Risk — over-broad grant.** A declaration is a durable widening of what runs unattended.
  Mitigated by a closed action vocabulary, by gates remaining mandatory, and by the declaration
  living in a tracked file that diffs and reverts.
- **Risk — inherited authorization read as task-authored.** Mitigated by naming the source in the
  capsule and gate output rather than merging the two silently.
- **Out of scope**: the precedent/sedimentation system (issue #34 layer L2), which must not be
  designed before this change fixes the declaration format it would extend; and the `sync` surface,
  which is not an overlay target today.
- **Authority**: issue #34 and its two comments record the accepted decisions this change
  implements.

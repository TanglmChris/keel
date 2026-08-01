## Why

Keel tells the human what task state it is working from at every session start, and says nothing about whether the runtime enforcing that protocol is the protocol. On 2026-08-01 an installed plugin five minor versions behind the working tree silently enforced the old rules for a whole session — the projection, `keel context`, and several gates all ran and all looked normal. It surfaced only when a write the newer record layer should have allowed was denied by the older hook.

Every answer Keel gives rests on the claim that its checks are local, deterministic, and reproducible. It has never reported which build produced them.

## What Changes

- **The SessionStart projection reports version alignment.** Three things are comparable in any repository: the plugin actually executing, the `keel` CLI it invokes, and the protocol version stamped in the repository's managed block. When they disagree, both channels say so — the human line and the model payload.
- **Silence when aligned.** A matching set adds nothing the reader has to skim past. A line printed every session is a line nobody reads, and this one exists to be noticed.
- **Missing is not mismatched.** A version that cannot be discovered is reported as undiscoverable, never as drift. A false alarm every session would be worse than the silence this change fixes.
- **No new mechanism.** The hook already runs `keel --version` and already emits both channels; it currently parses that version only far enough to check the major number and discards the rest. This uses what is already in hand.
- **Keel reports, and does not manage.** Installing, updating, or pinning a plugin is the host's, and stays the host's. This is the scope rule 5.8.0 promoted, applied to the change that most tempts a fix — the obvious next step after "your plugin is stale" is to update it, and that step is not Keel's.

## Capabilities

### New Capabilities
<!-- None. This extends an existing projection rather than introducing a surface. -->

### Modified Capabilities
- `keel-native-runtime-projection`: the SessionStart projection gains runtime version alignment on both channels, with an undiscoverable version reported as such rather than as drift.

## Impact

- **Code**: `plugins/keel/scripts/session-start.js`, and the validator scenario covering the hook's branches.
- **Cost**: a `plugin.json` read and a managed-block regex against a file the hook can already reach. No new subprocess — the CLI version is already being fetched. This matters because the hook runs on every session including post-compaction reinjection, under `KEEL_HOOK_TIMEOUT_MS`.
- **Offline**: nothing reaches the network. Keel compares what is installed against what this repository declares, and never asks what the newest release is.
- **Risk**: a comparison that is wrong in the noisy direction trains the reader to ignore it, which would leave the repository worse off than silent. The undiscoverable-versus-mismatched distinction is the mitigation, and it is the one thing here worth testing hardest.
- **Out of scope**: L1 preflight self-checks, L2 cross-platform decoupling, and L3 version-alignment mechanisms, all tracked on issue #38.
- **Dependencies**: none added.

## Why

The SessionStart projection reaches only the model. `keel context` state is injected as
`additionalContext`, and the human sees it only if the agent chooses to restate it — and only
after the human sends a first message. A human who opens a session and waits is told nothing,
which is exactly the case reported in issue #32.

Claude Code 2.1.220's common hook-output schema carries `systemMessage`, rendered to the human
on an exit-0 hook alongside the `additionalContext` the projection already emits. The channel
the projection needs already exists and Keel does not use it.

## What Changes

- The SessionStart projection emits `systemMessage` carrying the human-readable Keel state and
  next action, in addition to the unchanged `additionalContext` model projection.
- Every projection branch — ready, idle, ambiguous, blocked, and the degraded fallbacks —
  carries the human line, so a failing hook is visible rather than silent.
- The hook keeps its existing discipline: always exit 0, never block, never write state.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-native-runtime-projection`: the SessionStart projection gains a human-visible channel
  and must populate it on every branch; the existing model-facing `additionalContext` contract
  is unchanged.

## Impact

- `plugins/keel/scripts/session-start.js` — the only product file whose behavior changes.
- `scripts/validate_plugin.py` — the `native-plugin-session-start` scenarios assert the new
  field on each branch.
- Depends on a Claude Code capability read from the 2.1.220 binary, not from published
  documentation. An older or changed host that ignores unknown hook-output fields degrades to
  today's behavior; a host that rejects them does not, which is why rendering is confirmed by
  smoke check before the contract hardens.
- Out of scope: `terminalSequence` (OSC notification/title), the `keel context --statusline`
  segment proposed in issue #32, and any change to `keel context` output or `schemaVersion`.

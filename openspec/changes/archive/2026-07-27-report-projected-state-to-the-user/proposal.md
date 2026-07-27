## Why

The Keel SessionStart projection reaches only the agent. It is delivered as
`additionalContext`, a model-only channel the host does not render, so the
human starting the session sees nothing — no context status, no selected
change, no next action. The agent holds an accurate picture of where the work
stands and stays silent about it until asked.

Nothing in the protocol closes that gap. `AGENTS.md` Session Start tells the
agent to run `keel context` and follow its result; it never tells the agent to
say what it found. The projection text itself ends at `next: run keel context`,
an instruction the agent executes privately. Both are written as if the agent
were the only reader that mattered.

The cost is a silent continuity failure. A human who cannot see the projected
state cannot catch the case where it is wrong — a stale selection, an
unexpected `idle`, a fallback that fired because the CLI was missing. Keel's
own premise is that projection is disposable and must be checked against
OpenSpec and Git; a projection nobody sees is a projection nobody checks.

## What Changes

- The SessionStart projection instructs the agent to state the projected
  context to the user in its first response of the session, in both the
  ready branch and the non-ready branch (idle, ambiguous, and the fallback
  diagnostics).
- This repository's resident `AGENTS.md` Session Start section carries the
  same rule, so it still holds when the native plugin is absent or was not
  loaded.
- The `native-plugin-session-start` validator scenario asserts the
  instruction is present in both branches.

No breaking changes. The projection stays disposable, non-blocking, and
authority-free: it gains one instruction and still selects nothing, records
nothing, and starts nothing.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-native-runtime-projection`: the SessionStart projection contract gains
  a requirement that projected context is surfaced to the user, not consumed
  silently by the agent.

## Impact

- `plugins/keel/scripts/session-start.js` — projection text, both branches.
- `AGENTS.md` — Session Start section.
- `scripts/validate_plugin.py` — `native-plugin-session-start` scenario
  assertions.
- Explicit non-goal: `assets/bootstrap/AGENTS.md` is not touched. Its managed
  block sits at 1017 of a hard sub-1024-byte budget with roughly seven bytes
  of headroom, and that wedge is owned by
  https://github.com/TanglmChris/keel/issues/15. Consumers without the native
  plugin therefore do not receive this rule yet; that residue is recorded as a
  follow-up rather than smuggled into a full budget.
- Risk: the projection is a bounded context injection under a line budget in
  spirit, and every added line competes for attention with the pointer itself.
  Mitigated by adding one short line per branch, not a paragraph.

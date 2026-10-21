## Why

5.186.0 (#408) classifies each scenario by evidence kind. A scenario counts as stand-in host when a marker derived from Keel's sources appears anywhere in its reachable code. `chat_environment` names the host's `CLAUDE_*` variables in order to *remove* them, as 5.181.0 (#415) made it do, so the suite does not inherit the running session. Every scenario built on it is therefore counted as stand-in host, and the counts overstate how much of the suite runs against a host stand-in.

Measured on 5.187.0: `--group shift` reported `2 deterministic, 45 against a stand-in host`. A prototype that matches a marker only where it is set — as a dict key, an item assignment, a `NAME=` in shell text, or an attribute assignment — moved 37 of 137 scenarios to deterministic. The scenarios that move include `chat-core`, `shift-self`, `patrol-nudge`, and `release-evidence-classes`, which names markers in its assertions. Every scenario that sets `KEEL_CLAUDE`, `CLAUDE_CONFIG_DIR`, a hook payload, or a fake program stays stand-in host.

## What Changes

- **`scripts/validation/evidence.py` counts a marker only where the code sets it.** This applies to the derived variables and to the hook payload's `hook_event_name` key. A file named for a host program still counts wherever it appears, because writing one is what stands it in.
- **`release-evidence-classes` asserts that `chat-core` is deterministic.**

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-validation-runner`

## Impact

The change touches `scripts/validation/evidence.py`, `scripts/validation/selfcheck.py`, the published spec, and the changelog. The counts printed after a run, and in release notes, change.

## Why

Issue #226, found 2026-10-05 while connecting rtl_ppa_prj: `keel chat bridge stop` followed at once by `keel chat bridge start` reported success, but launchd had no service and the bridge was not running. Meanwhile `keel chat bridge status` reported `running (pid 17759), connected` from the status file of the process that had just been stopped. The owner would believe Slack was connected when nothing was relayed.

## What Changes

- `start` retries `launchctl bootstrap` while it fails because the previous `bootout` is still in progress, up to a bounded wait, and fails naming launchctl's output if the service still cannot be loaded; it no longer treats that failure as success. `start` on an already running service reports that and changes nothing.
- `stop` and `install` wait, bounded, until launchd has unloaded the service before returning or reloading.
- `status` asks launchd for the service's state and pid where launchd can answer, and reports the bridge as not running when the service is unloaded or its pid differs from the status file's.

## Capabilities

### Modified Capabilities
- `keel-chat-slack-bridge`: start, stop, install, and status reflect launchd's actual state.

## Impact

`src/core/chat/{lifecycle,bridge,cli}.js`, `scripts/validate_plugin.py`, the published spec, and the changelog.

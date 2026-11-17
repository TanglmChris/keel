## Why
Kaiwu #546 cannot complete deployment while real App input and background role delivery use separate writers, and foreground cwd changes now fail managed-role identity checks. Issue #541 requests native serial handoff, explicit thread-level automatic review and safe same-id recovery.
## What Changes
- Diagnose native writer ownership, unload/subscriber lifecycle and public queue capabilities on private fixtures before implementation.
- Establish same-id foreground/background acceptance and safe cwd/endpoint recovery boundaries.
- Expose only explicitly requested thread-level review policy, preserving sandbox and approval policy; document native persistent lifecycle without touching existing daemons.
## Capabilities
### New Capabilities
None.
### Modified Capabilities
- `keel-codex-host-team`: real foreground/background serial use, explicit thread reviewer and owned identity recovery.
## Impact
Managed Codex adapter/public CLI/tests and host deployment documentation. No production Kaiwu role/registry/endpoint changes, daemon restarts, replacement threads, writer bypass or #535 policy activation. #527 remains deferred.

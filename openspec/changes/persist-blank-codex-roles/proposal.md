## Why
Kaiwu issue #537 reports successful blank managed starts that cannot accept their first delayed delivery. Role initialization must survive the creating connection closing without silently replacing its identity.
## What Changes
- Reproduce blank start/disconnect/delay/read/deliver on an isolated real host role.
- Determine the host-supported same-id persistence/recovery boundary before authoring implementation.
- Deliver a tested formal patch once the mechanism is established; preserve ownership, claims and permission boundaries.
## Capabilities
### New Capabilities
None.
### Modified Capabilities
- `keel-codex-host-team`: successful managed-role initialization survives delayed first delivery.
## Impact
Codex host lifecycle adapter, public CLI tests, native-host acceptance and deployment documentation. No kaiwu production files, roles, replacement threads, new dependencies or permission relaxation.

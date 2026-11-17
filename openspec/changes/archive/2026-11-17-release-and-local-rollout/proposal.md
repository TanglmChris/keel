## Why

The verified 5.229.0 candidate is local only, installed Keel components remain 5.228.0, and the shared Codex daemon inherited a stale proxy. The owner explicitly requested publication, local updates, proxy repair and notification to kaiwu-ip after all checks pass.

## What Changes

- Publish the verified candidate through the repository Full gate and automatic landing/publishing workflow.
- Update local Keel CLI and installed native plugins to the published version.
- Restart the idle managed daemon with the working environment, verify actual model completion through its default endpoint, and record evidence.
- Notify kaiwu-ip only after the rollout is verified. Leave #527 untouched.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-codex-host-team`: observable release and local rollout acceptance.

## Impact

Repository release refs and npm, local CLI/plugin installations, the idle managed Codex service and a notification to the existing kaiwu-ip owner. No new dependency or product redesign. No direct agent merge; repository automation owns landing.

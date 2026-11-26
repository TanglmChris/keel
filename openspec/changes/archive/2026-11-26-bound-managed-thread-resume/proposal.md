## Why
Kaiwu reported repeated oversized Codex responses during Flow dispatch (#570). Managed deliver and recover consume identity and policy from resume while the default response can include the entire history.

## What Changes
Request the native metadata-only resume response on both paths. Retain the current response limit.

## Capabilities
- Modified: `keel-codex-host-team` requires bounded managed resume.

## Impact
Managed host client and transport regression. No production replay.

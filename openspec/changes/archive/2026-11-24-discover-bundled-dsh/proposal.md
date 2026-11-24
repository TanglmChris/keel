## Why

Keel reports the bundled DSH entry as missing on Linux even when the installed executable is on PATH (#565).

## What Changes

Resolve bundled DSH from the native macOS application bundle when present on macOS, with PATH discovery for standalone installations. Preserve explicit machine overrides, project permission and brief checks.

## Capabilities

Modify `keel-external-agents` for built-in DSH discovery.

## Impact

External-agent catalog and generated brief commands. Discovery invokes no external agent.

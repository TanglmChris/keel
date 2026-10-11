## Why

Issue #240, reported by verify_sub (rtl_ppa_prj, via rtl_ppa_flow) on 2026-10-05: the session-start line printed `runtime versions disagree: … protocol 5.92.0` with `claude plugin update` as the only remedy. The plugin and CLI were current. What lagged was the repository's managed protocol block, whose fix is the protocol refresh `keel context` names on its `Protocol:` line. The session followed a remedy that changed nothing, and the line kept coming back.

## What Changes

- The drift line names the remedy of each item behind the newest version it read. The plugin update is named only when the plugin or CLI is behind. When the protocol is behind, the line names the protocol refresh, `keel --install --target <target>`. The PATH copy keeps its own remedy.

## Capabilities

### Modified Capabilities
- `keel-native-runtime-projection`: the drift report names the remedy of whichever item lags.

## Impact

`plugins/keel/scripts/session-start.js`, `scripts/validate_plugin.py`, the published spec, and the changelog.

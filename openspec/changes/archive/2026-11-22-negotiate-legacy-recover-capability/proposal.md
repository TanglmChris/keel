## Why

Keel 5.231.0 legacy managed roles fail native recovery because the restore request sends runtime workspace roots without negotiating the required experimental API. Kaiwu reported the exact native error in Keel #550.

## What Changes

Negotiate the capability for recover independently of reviewer or policy storage. Preserve original identity, worktree, policy, claims and fail-closed native behavior.

## Capabilities

### Modified Capabilities

- `keel-codex-host-team` — preserve recovery for legacy managed records.

## Impact

One host-client handshake, one public CLI regression, isolated native acceptance and a patch release. Desktop composer and Kaiwu production acceptance remain owned by #550 and Kaiwu #546.

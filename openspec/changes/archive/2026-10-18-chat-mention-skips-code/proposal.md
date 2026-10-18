## Why

Issue #345 (rtl_ppa_prj, keel 5.138.0): `keel chat post` refuses a whole message when it contains an `@<token>` that is not a member or alias. In that project the commonest `@` is `<branch> @ <sha>`, so `@638059e4` refused the post (`@638059e4 is not a member or alias in group iecc.`), as did an `@verify` quoted in backticks; several roles had to rewrite and resend (TanglmChris/rtl_ppa_prj#311). The refusal is meant for typos (design D3/D4), and these are not mentions.

## What Changes

- Text inside inline code or a fenced block is not scanned for mentions, in `post`, `dm` and `todo` alike, and in the Slack bridge's lenient reading.
- An `@` token of 7–40 hex digits that names no member or alias is a commit id, left as text rather than refused.
- A bare `@typo` is still refused by name.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-cross-host-mailbox`: quoted text and commit ids are not mentions.

## Impact

`src/core/chat/store.js`, `src/core/chat/bridge.js`, `scripts/validate_plugin.py`, one published spec, the changelog.

## Context

Owner's decision of 2026-10-05: "keel bot可以作为你用了".

## Facts

- F1 — `verifyBots` in `src/core/chat/bridge.js` builds role apps only from `~/.keel/chat/bots.json`. The shared app is `ctx` itself, and `directApps` never includes it.
- F2 — Slack spreads one app's events across all of that app's open Socket Mode connections. A second connection with the shared app token would take channel events away from the first.
- F3 — On 2026-10-05 the shared app's bot token carried no `im:history` or `im:write` scope (`x-oauth-scopes` of auth.test).

## Decisions

- D1 — The shared app serves a role when a project's `slack.bots` maps the shared app's own bot user id to it. No new configuration key is added.
- D2 — The one-role rule of registered bots applies unchanged: mapped to more than one role, it takes no direct messages, and status says why.
- D3 — Direct messages to the shared app arrive on its existing connection (F2). `handleEvent` passes an `im` event to the direct handler, and the shared hello also catches up its direct channels. No second connection is opened.
- D4 — Records of the mapped role are posted with the shared token as the app itself, without a custom username, the same way a role's own bot posts.

## Context

The owner's request of 2026-10-05: "在slack的信息需要我知道的，请@我".

## Facts

- F1 — `slackText` in `src/core/chat/bridge.js` prefixes `<@owner-id>` to a posted record whose mentions include `owner`, and only when `slack.owner` is set.
- F2 — Slack's default notification setting is "mentions, direct messages, and keywords", so an unmentioned channel message shows as unread only.
- F3 — `bridgeLine` in `src/core/chat/notice.js` is the only Slack-specific text in the session-start notice, and is returned only for a Slack-enabled project.

## Decisions

- D1 — The rule is stated in the session-start notice, beside the bridge line, because that is the one text every bound session in a Slack-enabled project reads; a rule in a guide alone reaches only whoever reads the guide.
- D2 — The line appears only when `slack.owner` is set, since without it `@owner` produces no mention (F1), and it appears whether or not the bridge is running, because records written while it is down are posted later.
- D3 — The line asks for `@owner` on what the owner needs to see or decide on and asks to leave it out of routine discussion, so that a mention keeps meaning something.

## Context

Issue #187. Owner request 2026-10-05: Slack messages should carry formatting, because plain text hides the point.

## Facts

- F1 — `chat.postMessage` renders `text` as mrkdwn for a bot message: `*bold*`, `_italic_`, `~strike~`, `` `code` ``, fenced code, `>` quotes, and links written `<url|text>`; a literal `&`, `<`, or `>` must be sent as `&amp;`, `&lt;`, `&gt;`. Basis: Slack's message formatting documentation; as with the bridge's other Slack shapes, the fake server records what was sent and a real run is the evidence.
- F2 — The bridge sends a record's text verbatim after redaction and the length cut (`slackText`), and imports a person's text verbatim apart from `<@U…>` mentions (`humanText`).

## Decisions

- D1 — Outbound order is redact, translate to mrkdwn, cut, then address the owner, so the cut pointer and the owner mention are added after translation and never translated themselves.
- D2 — Markdown to mrkdwn: `**x**` and `__x__` become `*x*`; a single `*x*` or `_x_` becomes `_x_`; `~~x~~` becomes `~x~`; a line starting with `#` to `######` becomes a bold line; a line starting with `- `, `* `, or `+ ` becomes `• `; `[text](url)` becomes `<url|text>`; `&`, `<`, `>` are escaped first. Text inside backtick code spans and fenced blocks is escaped but otherwise unchanged.
- D3 — mrkdwn to Markdown, for inbound text after mentions are resolved: `*x*` becomes `**x**`, `_x_` becomes `*x*`, `~x~` becomes `~~x~~`, `<url|text>` becomes `[text](url)`, `<url>` becomes `url`, and `&amp;`, `&lt;`, `&gt;` are unescaped; code is left alone. Headings and bullets come back as bold lines and `•` lines: the round trip keeps meaning, not the exact markers.

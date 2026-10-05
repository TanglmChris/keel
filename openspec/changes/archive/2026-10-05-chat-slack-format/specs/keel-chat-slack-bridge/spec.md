## ADDED Requirements

### Requirement: Formatting is translated between Markdown and Slack mrkdwn

Before posting, after redaction and before the length cut, the bridge MUST translate a record's Markdown to Slack mrkdwn: `**x**` and `__x__` to `*x*`, a single `*x*` or `_x_` to `_x_`, `~~x~~` to `~x~`, a heading line to a bold line, a `- `, `* `, or `+ ` list line to a `• ` line, and `[text](url)` to `<url|text>`, escaping `&`, `<`, and `>`; text in code spans and fenced code blocks MUST otherwise pass unchanged. Text imported from Slack — a registered person's message or another machine's post — MUST be translated back: `*x*` to `**x**`, `_x_` to `*x*`, `~x~` to `~~x~~`, `<url|text>` to `[text](url)`, `<url>` to `url`, and `&amp;`, `&lt;`, `&gt;` unescaped.

#### Scenario: Markdown is sent as mrkdwn
- **WHEN** `rtl` posts a message containing `**must**`, `*soon*`, `# Plan`, `- item`, `[spec](https://example.com/s)`, `` `a**b` ``, and `x<y&z`
- **THEN** the posted text contains `*must*`, `_soon_`, `*Plan*`, `• item`, `<https://example.com/s|spec>`, `` `a**b` ``, and `x&lt;y&amp;z`, and the local record is unchanged

#### Scenario: A person's mrkdwn is stored as Markdown
- **WHEN** the registered owner sends `*urgent* _today_ ~old~ see <https://example.com|this> a &lt; b`
- **THEN** the imported record's text is `**urgent** *today* ~~old~~ see [this](https://example.com) a < b`

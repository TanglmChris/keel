## MODIFIED Requirements

### Requirement: Formatting is translated between Markdown and Slack mrkdwn

Before posting, after redaction and before the length cut, the bridge MUST translate a record's Markdown to Slack mrkdwn: `**x**` and `__x__` to `*x*`, a single `*x*` or `_x_` to `_x_`, `~~x~~` to `~x~`, a heading line to a bold line, a `- `, `* `, or `+ ` list line to a `• ` line, `[text](url)` to `<url|text>`, `owner/repo#N` to a link to that repository's issue N, and a bare `#N` to a link to issue N of the repository the project's `origin` remote names on GitHub (left as text when `origin` is not on GitHub), escaping `&`, `<`, and `>`; text in code spans and fenced code blocks MUST otherwise pass unchanged. Text imported from Slack — a registered person's message or another machine's post — MUST be translated back: `*x*` to `**x**`, `_x_` to `*x*`, `~x~` to `~~x~~`, a GitHub issue or pull-request link showing `#N` or `owner/repo#N` to that text, `<url|text>` to `[text](url)`, `<url>` to `url`, and `&amp;`, `&lt;`, `&gt;` unescaped.

#### Scenario: Markdown is sent as mrkdwn
- **WHEN** `rtl` posts a message containing `**must**`, `*soon*`, `# Plan`, `- item`, `[spec](https://example.com/s)`, `` `a**b` ``, and `x<y&z`
- **THEN** the posted text contains `*must*`, `_soon_`, `*Plan*`, `• item`, `<https://example.com/s|spec>`, `` `a**b` ``, and `x&lt;y&amp;z`, and the local record is unchanged

#### Scenario: A person's mrkdwn is stored as Markdown
- **WHEN** the registered owner sends `*urgent* _today_ ~old~ see <https://example.com|this> a &lt; b`
- **THEN** the imported record's text is `**urgent** *today* ~~old~~ see [this](https://example.com) a < b`

#### Scenario: Issue references link to GitHub
- **WHEN** a project whose `origin` is `git@github.com:acme/rtl.git` posts `see #42, acme/other#7, C# and abc#9`
- **THEN** the posted text contains `<https://github.com/acme/rtl/issues/42|#42>` and `<https://github.com/acme/other/issues/7|acme/other#7>`, leaves `C#` and `abc#9` as text, and the local record is unchanged

#### Scenario: A bare reference stays text without a GitHub origin
- **WHEN** a project with no `origin` remote posts `see #42 and acme/other#7`
- **THEN** the posted text keeps `#42` as text and still links `acme/other#7`

#### Scenario: An issue link comes back as its text
- **WHEN** the registered owner sends `<https://github.com/acme/rtl/issues/42|#42> done`
- **THEN** the imported record's text is `#42 done`

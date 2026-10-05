## Context

The owner's request of 2026-10-05.

## Facts

- F1 — Slack renders `<url|text>` as a link and does not link `#226` by itself.
- F2 — `mrkdwn.toSlack` already translates prose outside code spans and fenced blocks, and `mrkdwn.fromSlack` translates `<url|text>` back to `[text](url)`.
- F3 — GitHub redirects `https://github.com/<owner>/<repo>/issues/<n>` to the pull request when n is one, so one URL form serves both.

## Decisions

- D1 — A bare `#N` refers to the project's own repository, read from `git remote get-url origin` when it is a `github.com` URL (https or ssh). No new configuration is introduced; a project without a GitHub origin keeps bare `#N` as text.
- D2 — `owner/repo#N` always links to that repository, so a reference to another project works in any channel.
- D3 — A reference links only at a word boundary. Before it there must be no ASCII word character, `#`, `/`, `;`, `&`, `.`, or `-`, so CJK text and full-width punctuation may sit right beside it. After it there must be a non-word character or the end. That way `C#`, `abc#12`, a heading `# Plan`, and an escaped entity such as `&#12;` do not link. N is 1 to 7 digits.
- D4 — Inbound, a `github.com/.../issues/N` or `/pull/N` link whose shown text is `#N` or `owner/repo#N` comes back as that text, not as a Markdown link, so the stored record reads as the session wrote it.

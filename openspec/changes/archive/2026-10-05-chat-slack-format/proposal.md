## Why

Issue #187, owner request 2026-10-05 while using the rtl_ppa_prj channel: messages arrive in Slack as plain text, and the point of a long one is hard to catch. Sessions write Markdown (`**bold**`, lists, code, links), but Slack renders its own mrkdwn (`*bold*`, `<url|text>`), so the bridge's verbatim text shows the Markdown markers instead of formatting.

## What Changes

- Outbound text is translated from Markdown to Slack mrkdwn: bold, italic, strikethrough, headings (as bold lines), bullet lists, and links, with `&`, `<`, `>` escaped as Slack requires; code spans and fenced blocks pass through unchanged.
- Inbound text — a person's message, and another machine's post rebuilt from Slack — is translated back from mrkdwn to Markdown, so the local store stays Markdown.
- The setup guides tell sessions they can format with ordinary Markdown.

## Capabilities

### Modified Capabilities
- `keel-chat-slack-bridge`: formatting is translated between Markdown and Slack mrkdwn in both directions.

## Impact

A new `src/core/chat/mrkdwn.js`, `src/core/chat/bridge.js`, `scripts/validate_plugin.py`, both setup guides, the published spec, and the changelog.

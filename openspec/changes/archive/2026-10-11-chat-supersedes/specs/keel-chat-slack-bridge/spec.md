## ADDED Requirements

### Requirement: A superseded record's Slack copy says so

When the bridge posts a record that supersedes another, it MUST also update the superseded record's Slack message, when it has one, so that the message opens with `(superseded by <id>)`, using the token of the app that posted that message.

#### Scenario: The superseded Slack message is updated
- **WHEN** a record in a Slack-mapped group supersedes an earlier record the bridge already posted
- **THEN** the bridge calls `chat.update` on the earlier message with text opening `(superseded by <id>)`

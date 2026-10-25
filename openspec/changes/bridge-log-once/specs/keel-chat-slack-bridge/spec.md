## ADDED Requirements

### Requirement: The bridge logs a repeating failure once and names a missing scope

The running bridge MUST log a periodic archive sync's refusal or error, and a connection's catch-up failure, when it first occurs and again only when its message changes, and MUST log one recovery line when that sync or catch-up next succeeds; it MUST NOT log the same failure again at each sync or reconnect. A Slack API error MUST keep the response's `needed` and `provided` scopes, and its message MUST name the needed scopes as `missing_scope: needs <scopes>`.

#### Scenario: A refusal that never changes is logged once
- **WHEN** the bridge runs connected through several archive syncs of a Slack-enabled project that has no remote
- **THEN** its log holds `this repository has no remote` for that project exactly once

#### Scenario: A missing scope is named once across reconnects
- **WHEN** the fake server answers `conversations.history` with `missing_scope` and `needed: channels:history`, and the bridge reconnects three times
- **THEN** its log holds one `catch-up failed` line, and that line names `missing_scope: needs channels:history`
- **AND THEN** once the server answers normally and the bridge reconnects, the log holds one `catch-up works again` line

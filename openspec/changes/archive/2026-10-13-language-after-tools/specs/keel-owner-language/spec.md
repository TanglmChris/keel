## ADDED Requirements

### Requirement: The owner's language is restated after runs of tool calls

With `owner_language:` declared, the Claude PostToolUse chat hook MUST restate the rule once a session has made a set number of tool calls (default 15) or a set time has passed (default 10 minutes) since it was last stated there, whichever comes first, and MUST stay silent otherwise; a restatement on UserPromptSubmit MUST reset the count. A host-run session and a repository without the declaration MUST get nothing.

#### Scenario: The rule returns after a run of tool calls
- **WHEN** `owner_language: zh` is declared, a prompt is submitted, and the session then makes 16 tool calls
- **THEN** the first 14 PostToolUse calls print nothing, the 15th prints the rule naming `中文`, the 16th prints nothing, and after a new prompt the count starts over

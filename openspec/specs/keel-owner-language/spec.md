# keel-owner-language

## Purpose

Define how a repository declares the language every message to its owner is written in, and how Keel restates that
rule where replies are written, so an agent that works and reads in another language still addresses the owner in theirs.

## Requirements

### Requirement: A declared owner language is restated where replies are written

`keel/config.yaml` MAY declare `owner_language:` with a language tag. When it does, `keel context` MUST carry the tag, the session-start projection MUST state that every message to the owner is in that language, and the chat UserPromptSubmit hook MUST restate it on every prompt in every worktree of the repository, with or without a chat role, except in a host-run session. A malformed value MUST be reported and ignored. The protocol MUST make the declared language binding for every message to the owner, including the question and options of a structured-choice prompt.

#### Scenario: Every prompt restates the owner's language
- **WHEN** `keel/config.yaml` declares `owner_language: zh` and a prompt is submitted in a worktree with no chat role
- **THEN** the hook's `additionalContext` names `中文` and the structured-choice options, `keel context --json` carries `ownerLanguage` `zh`, and the session-start note states the rule

#### Scenario: A malformed language is reported
- **WHEN** `keel/config.yaml` declares `owner_language: Chinese!`
- **THEN** `keel context` warns that it is not a language tag and carries no `ownerLanguage`, and the prompt hook adds no language line

### Requirement: The owner's language is restated after runs of tool calls

With `owner_language:` declared, the Claude PostToolUse chat hook MUST restate the rule once a session has made a set number of tool calls (default 15) or a set time has passed (default 10 minutes) since it was last stated there, whichever comes first, and MUST stay silent otherwise; a restatement on UserPromptSubmit MUST reset the count. A host-run session and a repository without the declaration MUST get nothing.

#### Scenario: The rule returns after a run of tool calls
- **WHEN** `owner_language: zh` is declared, a prompt is submitted, and the session then makes 16 tool calls
- **THEN** the first 14 PostToolUse calls print nothing, the 15th prints the rule naming `中文`, the 16th prints nothing, and after a new prompt the count starts over

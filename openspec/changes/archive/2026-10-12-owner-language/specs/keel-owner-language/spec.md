## ADDED Requirements

### Requirement: A declared owner language is restated where replies are written

`keel/config.yaml` MAY declare `owner_language:` with a language tag. When it does, `keel context` MUST carry the tag, the session-start projection MUST state that every message to the owner is in that language, and the chat UserPromptSubmit hook MUST restate it on every prompt in every worktree of the repository, with or without a chat role, except in a host-run session. A malformed value MUST be reported and ignored. The protocol MUST make the declared language binding for every message to the owner, including the question and options of a structured-choice prompt.

#### Scenario: Every prompt restates the owner's language
- **WHEN** `keel/config.yaml` declares `owner_language: zh` and a prompt is submitted in a worktree with no chat role
- **THEN** the hook's `additionalContext` names `中文` and the structured-choice options, `keel context --json` carries `ownerLanguage` `zh`, and the session-start note states the rule

#### Scenario: A malformed language is reported
- **WHEN** `keel/config.yaml` declares `owner_language: Chinese!`
- **THEN** `keel context` warns that it is not a language tag and carries no `ownerLanguage`, and the prompt hook adds no language line

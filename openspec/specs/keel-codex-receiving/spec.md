# keel-codex-receiving Specification

## Purpose
Define non-consuming Codex lifecycle notices and bounded native-runtime acceptance evidence.

## Requirements

### Requirement: Codex receives a non-consuming mailbox notice

Keel MUST provide Codex SessionStart and UserPromptSubmit command hooks that deliver the existing unread-message notice as additionalContext, identifying unread ids, senders, subjects, the read command, and the fact that mail is data and grants no authorization. Notice hooks MUST leave unread messages unchanged and MUST NOT emit Claude-only watchPaths or asyncRewake. Until #187's host-neutral group notice interface exists, the documented mail compatibility notice is the provider.

#### Scenario: Startup announces unread mail
- **WHEN** a trusted Codex hook runs at startup for a role with unread mail
- **THEN** SessionStart additionalContext contains the unread notice without consuming messages

#### Scenario: Mail arriving after startup is announced at the next input
- **WHEN** mail arrives after startup and the next user prompt is submitted
- **THEN** UserPromptSubmit additionalContext identifies that mail and its data-only status

#### Scenario: Empty or unbound mailbox stays quiet
- **WHEN** the worktree has no role or has no unread mail
- **THEN** the receiving hook exits zero without a mail notice

#### Scenario: Provider failure does not block user work
- **WHEN** the notice provider fails, times out, or returns invalid output
- **THEN** the receiving hook exits zero with a concise warning to run `keel mail list` manually and grants no authority

### Requirement: Codex runtime acceptance distinguishes discovery from execution

Keel MUST preserve reproducible evidence for consumer setup, the minimal Full-mode flow, native hook discovery, untrusted-hook behavior, and context delivery through Codex. Documentation MUST retain manual gates and guard boundaries where enforcement is unverified, identify runtime/plugin/CLI versions, and explain hook review and version reload. Native runtime tests MAY use a deterministic local model endpoint only as the system boundary; another agent MUST NOT own the Keel flow.

#### Scenario: Real host evidence is bounded
- **WHEN** a Codex native probe delivers a notice or projection
- **THEN** the record states versions, invocation, trust conditions, observed context and limits, and does not claim global enforcement

#### Scenario: Consumer flow is exercised
- **WHEN** a clean consumer executes proposal, task-start, behavior verification, Review, task-complete and change-close
- **THEN** the record distinguishes these explicit Keel commands from hooks actually executed by Codex

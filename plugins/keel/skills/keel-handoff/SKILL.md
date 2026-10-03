---
name: keel-handoff
description: Create, validate, or clear the optional keel-handoff/v1 pointer override when human intent cannot be inferred uniquely.
---

# keel-handoff

## Purpose

Use this skill only when `keel context` is ambiguous or blocked because human intent cannot be inferred, or when the user explicitly asks to set or clear an override. HANDOFF is not session state or a startup summary, and it is not a durable follow-up owner.

## Context to read

Run `keel context --json`, then read only the returned paths and the intended durable OpenSpec owner under `openspec/changes/<change>/`.

## Override contract

Write `keel/HANDOFF.md` with YAML front matter only:

```yaml
---
schema: keel-handoff/v1
owner: openspec/changes/<change>/tasks.md#<task>
action: task-start
reason: Concise reason automatic inference is insufficient
---
```

The only fields are `schema`, `owner`, `action`, and `reason`. The owner must be a durable OpenSpec proposal, design, or tasks pointer. Supported actions are `discuss`, `author`, `task-start`, `task-complete`, and `change-close`.

Never copy task progress, expectation state, evidence details, risks, conversation summaries, `active-backlog`, or `head=...`. Those belong to OpenSpec, archive evidence, or an explicit discard reason.

## Legacy and clearing

Do not rewrite a pre-v1 HANDOFF heuristically. Preserve it byte-for-byte and report the explicit choices: migrate it manually to the v1 contract or run `keel context --clear-handoff`.

Clearing removes only the override; it does not modify the durable owner. Run `keel context --clear-handoff --json`, then verify normal inference resumes.

## Lite boundary

Lite mode does not create HANDOFF for routine cross-session continuity. Use the same optional override contract only when explicit human intent must supersede inference.

## Standalone use

Validate the intended owner first, write or clear only the override, run `keel context --json`, and report the resulting source and next action.

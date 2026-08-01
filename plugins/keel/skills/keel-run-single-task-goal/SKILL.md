---
name: keel-run-single-task-goal
description: Use when the user explicitly authorizes automatic execution or resume of exactly one OpenSpec task on Codex or Claude. Drives the single-task native goal lifecycle through Keel gates, keeps the current agent the sole holder of write authority, and stops at the task boundary. Never activate for ordinary apply, proposal work, ambiguous or multiple tasks, or OpenCode.
license: UNLICENSED
metadata:
  keel-role: single-task-goal-activation
  keel-targets: codex, claude
---

# keel-run-single-task-goal

## Purpose

Activate a native goal or subagent runtime to execute exactly one authorized OpenSpec task end to end, while OpenSpec, Git, the task-capsule fingerprint, and deterministic Keel gates stay the only durable authority. The current agent remains the sole holder of write authority and owns Review, gate invocation, the task checkbox, and completion. Where delegation is declared, an authorized delegate may write inside the `Touch` boundary that authority already defined and acquires none of those decisions; the current agent re-runs each `M<n>` check itself before recording Evidence, because a delegate's reported result is a claim and the byte-identity check that validates a read-only helper cannot apply to a writer. A native evaluator declaring success never marks or reports the task complete.

## Authoritative sources and provenance

These official runtime docs are linked as authoritative references, not copied. Their text and trademarks belong to their owners; Keel paraphrases only the activation semantics it needs and bundles none of their prose.

- Codex goal-following: https://learn.chatgpt.com/use-cases/follow-goals
- Codex subagents: https://developers.openai.com/codex/subagents
- Claude goal execution: https://code.claude.com/docs/en/goal
- Claude subagents: https://code.claude.com/docs/en/sub-agents

License note: this skill is distributed under the Keel package license (UNLICENSED, all rights reserved by the author). Linking the official docs does not relicense them; do not paste their content into Keel artifacts.

## When to activate

Activate only on an explicit, unambiguous request to automatically execute or resume **one** task:

- The user names one OpenSpec change and one executable task and asks to run or continue it automatically.
- A resume request points at the same durable task whose recorded authorization fingerprint still matches the recompiled capsule.

## When NOT to activate

- Ordinary `/opsx:apply` or manual step-by-step work the user is driving.
- Proposal, design, or spec authoring before tasks are final.
- Ambiguous selection, multiple tasks, or a whole task group or change backlog.
- An unrelated native `/goal` use that is not a Keel OpenSpec task.
- Unrequested helpers, or an undeclared delegation of implementation to another agent.
- OpenCode, which stays manual compatibility only with no v4 native activation.

If any of these hold, stop and use the normal manual Keel loop.

## Single-task goal lifecycle

1. `keel gate task-start --change C --task T` and record the returned fingerprint in the task Evidence `Contract` line as the durable authorization.
2. `keel project goal --target codex|claude --change C --task T --json` to compile the disposable `keel-native-goal/v1` projection (objective, Acceptance, command labels, verification strategy, Touch, stop boundary, ownership, terminal condition). The projection is a view, never authority, and never checks the box.
3. Implement within Touch and produce the strategy's evidence (for example red/green slices for vertical-tdd).
4. Surface every command result and gate outcome in the transcript before any success claim.
5. Pass the current agent's Review, then `keel gate task-complete`.
6. The current agent durably checks the task checkbox.
7. Stop. Continuing to another task requires a new explicit user instruction and a new start fingerprint; there is no hidden scheduler or automatic next-task selection.

Resume reconstructs the goal from OpenSpec and Git only. Fingerprint drift, checkout divergence, a completed authorization, or missing authorization hard-stops before any product write; pass `--expected-fingerprint` and `--expected-owner` to assert the recorded authorization.

## Bounded read-only helpers

Helpers are optional, read-only evidence producers and never a second writer. Compile one with `keel project helper` for a single bounded question or one repository-byte-stable verification command; a helper never writes products, delegates, nests, or holds acceptance or completion authority. Accept a helper return only after `keel project helper --verify` proves before/after repository byte identity; a modified, added, removed, renamed, or permission-changed path rejects the evidence with exact paths and no cleanup. Helper absence never disables current-agent goal execution.

## Manual fallback

When native activation is unavailable — no plugin, disabled hooks, managed policy, missing trust, or an unsupported surface — do not fake activation. Run the same lifecycle by hand: `keel gate task-start`, `keel project goal ... --json` for the view, implement, surface evidence, `keel gate task-complete`, then check the box. The manual loop preserves the identical single-task lifecycle and stop boundary.

## Target activation

- Codex: where a callable goal/subagent surface exists, activate one bounded goal for the selected task and use subagents only as bounded read-only helpers. Without a callable surface, paste the exact `keel project goal` command and treat the capability as advisory.
- Claude: activate one `/goal` whose condition stays within the 4,000-character budget; the evaluator is transcript-only, so surface command and gate evidence explicitly. If hooks are disabled, policy blocks activation, or trust is missing, report the manual fallback.

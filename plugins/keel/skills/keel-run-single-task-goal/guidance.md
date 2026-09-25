# keel-run-single-task-goal — guidance

How to carry out the lifecycle. Every criterion is in `SKILL.md`; nothing here decides whether a task
may start, pass, or complete.

## Authoritative runtime references

Provenance: linked, not copied. Their text and trademarks belong to their owners, and Keel paraphrases
only the activation semantics it needs. License note: see `SKILL.md`.

- Codex goal-following: https://learn.chatgpt.com/use-cases/follow-goals
- Codex subagents: https://developers.openai.com/codex/subagents
- Claude goal execution: https://code.claude.com/docs/en/goal
- Claude subagents: https://code.claude.com/docs/en/sub-agents

## Running the lifecycle by hand

Native activation can be unavailable — no plugin, disabled hooks, managed policy, missing trust, or an
unsupported surface. Type the same numbered steps `SKILL.md` lists, in the same order: `keel gate task-start`, record the
fingerprint, `keel project goal … --json` for the view, implement inside `Touch`, surface every result
in the transcript, `keel gate task-complete`, check the box. What changes is who types them.

## Per-target activation notes

- **Codex**: where a callable goal or subagent surface exists, activate one bounded goal for the
  selected task and use subagents only as bounded read-only helpers. Without a callable surface, paste
  the exact `keel project goal` command and treat the capability as advisory.
- **Claude**: activate one `/goal` whose condition fits the 4,000-character budget. The evaluator sees
  the transcript only, so command and gate evidence has to appear there explicitly. If hooks are
  disabled, policy blocks activation, or trust is missing, the manual sequence above applies.

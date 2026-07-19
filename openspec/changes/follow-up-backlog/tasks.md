# Follow-up Backlog

> Boundary: this file owns deferred project follow-ups that are worth tracking but not part of the current task. Do not use chat history or `keel/HANDOFF.md` as the durable owner for actionable follow-ups.

## Intake Rules

- Add a follow-up here only when it is actionable, project-related, and intentionally out of scope for the current task.
- Keep each item small enough to become an OpenSpec task or to spawn a more specific OpenSpec change.
- Include source evidence, rationale, proposed owner, and the consequence of not doing it.
- Do not mark a future item `[ ]` until it has enough authority to be executed under a Keel task contract.
- If a follow-up is no longer useful, remove it with an explicit discard reason in the current task report or archive evidence.

## Deferred Items

- CI pipeline plus npm trusted publishing. Source evidence: as of 2026-07-18 the repository has no CI — all 50 validator scenarios run only in the local pre-push hook (3-4 minutes), and npm publish has been blocked on interactive `npm login` across three releases (npm registry still serves 3.0.0 while the repo is at 5.0.0). Rationale: a GitHub Actions workflow running `npm test` on pull requests plus OIDC trusted publishing on tags removes the recurring login blocker and lets the pre-push hook slim down to fast checks. Proposed owner: a future OpenSpec change, preferably authored after `consolidate-and-parallelize-validation-runner` lands so CI inherits the faster single-entry runner. Consequence if not done: releases keep stalling on manual login, and the full local chain stays the only regression net.


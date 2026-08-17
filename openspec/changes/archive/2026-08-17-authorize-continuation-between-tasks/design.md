## Context

The protocol stops at every task boundary and requires a fresh user instruction to continue, including inside a change whose `tasks.md` the owner reviewed and approved as one document. Issue #94 measured that this approval has no durable home: the `authorize:` vocabulary (`src/core/config.js:10`) is `commit`, `push`, `release`, `archive` — nothing names between-task continuation — and `keel-run-single-task-goal`'s stop rule requires "a new explicit user instruction", a conversational grant that dies at the next context reset (the exact failure class issue #34 catalogued). The issue separates two kinds of stops: stops at real decisions (blocker, drift, out-of-scope need, material alignment escalation, unresolved `Q<n>`), each with its own independent trigger, and the stop at a task boundary with nothing ambiguous about it, which re-asks for an approval already given. The owner decided on issue #94 (2026-08-17): adopt candidate ② — add `continuation` to the standing-authorization vocabulary, removing only the between-task confirmation and none of the gates, evidence, or Review. Reproduced against the current tree (2026-08-17, 5.40.0) before authoring.

## Goals / Non-Goals

**Goals:**
- Give the between-task approval a durable, git-tracked, diffable, revocable home with the same nature as the four existing names.
- Keep every real-decision stop exactly as it is: continuation spans only the boundary where nothing is undecided.
- Keep the texts an agent reads at that boundary — the goal skill's stop rule, the resident protocol, the README, the config comment — accurate about the new name.

**Non-Goals:**
- No change-level goal compilation (issue #94 candidate ①): one native goal still covers exactly one task, and `keel project goal` is untouched.
- No change to any gate verdict, evidence requirement, Review, or write-guard behavior; the declaration stays inert to proofs.
- No `continuation` entry in this repository's own declared `authorize:` list: widening this repo's policy is a separate owner decision this change does not make.
- No scheduler: nothing initiates work, and task order still comes from the approved `tasks.md`, never from a backlog scan.

## Decisions

D1 — `continuation` joins `STANDING_AUTHORIZATION_ACTIONS` in `src/core/config.js` as the fifth name, and no other production code changes. Every consumer reads the constant: `readStandingAuthorization()` filters by it, `standingAuthorizationUnknownMessage()` joins it into the accepted-names error, `keel context` surfaces that error through its warnings, `bin/keel.js` iterates it for the doctor's per-action rows, and `task-contract.js` joins the declared entries into a capsule's inherited `Standing authorization (keel/config.yaml): …` entry. Basis: owner decision on issue #94 (2026-08-17); the consumer inventory greps recorded in F2.

D2 — What `continuation` covers: exactly the boundary between a durably complete task and the next unchecked task of the same change, inside a change whose `tasks.md` the owner approved. Basis: issue #94 candidate ②'s own semantic restriction, quoted in the owner's decision.

D3 — What `continuation` never covers: it is not a trigger (nothing initiates or schedules), it selects no work outside the change, it removes no gate, evidence requirement, semantic Review, or write-guard step, each next task still starts through `keel gate task-start` with its own recorded fingerprint, and it authorizes no repository action — `commit`, `push`, `release`, and `archive` each still require their own name. Basis: the published `keel-standing-authorization` requirement "Standing authorization covers the action and never its proof"; the owner's decision wording "gate、Evidence、Review 一项不少".

D4 — A stop with its own trigger is not a between-task confirmation, and `continuation` does not span it. Blocker, fingerprint drift, out-of-scope need, a material choice escalated by alignment, an unresolved `Q<n>`, and a task's own Stop Rules all halt exactly as they do today. Basis: issue #94's two-kinds-of-stops argument, which the owner's decision accepted.

D5 — The goal skill's stop rule keeps its shape: stopping at the task boundary remains the step, and the declaration substitutes only for the "new explicit user instruction" clause. A new start fingerprint remains required, and there is still no hidden scheduler or automatic next-task selection beyond the approved `tasks.md` order. Basis: candidate ① was presented to the owner beside candidate ② and not chosen; one goal still equals one task.

D6 — The vocabulary stays fail-closed, and a `continuation` entry on an older Keel is therefore a whole-declaration outage, not a partial one: a runtime whose constant predates the word reports it unrecognized and the declaration authorizes nothing — including the `commit`/`push` entries beside it — until corrected. This is the existing, deliberate unknown-entry behavior, not new; the README notes it where the new name is introduced. Basis: `readStandingAuthorization()`'s fail-closed branch, unchanged since 5.13.0.

F1 — Reproduced 2026-08-17 on the 5.40.0 tree: `src/core/config.js:10` lists exactly four names; `src/skills/keel-run-single-task-goal/SKILL.md` step 7 reads "Continuing to another task requires a new explicit user instruction and a new start fingerprint"; `keel --doctor` prints exactly four per-action authorization rows. Basis: this session's reads of the working tree and `node bin/keel.js` runs.

F2 — The vocabulary's consumers all read the constant, so one edit reaches every surface: grep for `STANDING_AUTHORIZATION_ACTIONS` finds `src/core/config.js` (definition, filter, error message), `bin/keel.js:1645` (doctor rows), and `scripts/validate_plugin.py:15805` (the suite's own mirror tuple). The capsule side joins `declared` in `src/core/task-contract.js:973` without naming actions. Basis: greps this session against the 5.40.0 tree.

F3 — The owner's decision is recorded on issue #94: a recommendation comment (2026-08-17) comparing all three candidates, and the decision comment (2026-08-17) adopting candidate ② with the semantic bounds restated. Basis: `gh issue view 94` this session.

## Hidden Knowledge / Assumptions

None.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- An owner who declares `continuation` removes the human glance between tasks of an approved change. That is the declared intent, made in a git-tracked file that a diff shows and a one-line edit revokes; alignment escalation, gates, the write guard, and Review all still hold, and D4's stops still fire.
- Per D6, declaring `continuation` in a repository that also runs an older Keel takes the whole declaration down on that runtime until the entry is removed. Fail-closed is the designed behavior for an unrecognized name; the cost is a temporarily louder failure, never a silent grant.
- The word makes unattended multi-task runs easier to authorize, which concentrates more unreviewed-in-the-moment work behind one declaration. The merge boundary is unchanged — an unattended run still may not merge — so the accumulation is reviewable before it becomes history.

## Open Questions

None.

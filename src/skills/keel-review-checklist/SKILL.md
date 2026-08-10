---
name: keel-review-checklist
description: Run the current agent's thin semantic consistency review after shared Keel Core gates and before task completion, sync, archive, or meaningful handoff.
---

# keel-review-checklist

## Purpose

Use this thin Keel consistency gate only at completion gates: after a complete `/opsx:apply` task group, before `/opsx:sync` or `/opsx:archive`, before meaningful handoff, or when delivery reports risks, findings, follow-ups, or out-of-scope need.

Shared Core commands (`keel gate task-start`, `task-complete`, and `change-close`) validate deterministic structure. They do not judge product intent, behavioral test sufficiency, design quality, or risk completeness. Those judgments remain with the current agent.

## Context to read

Read the selected OpenSpec proposal, design, specs, tasks, diff, and command evidence. Read `keel/HANDOFF.md` only when validating an optional override; it is never evidence or a durable follow-up owner.

## Deterministic gate check

- Confirm the appropriate shared Core gate was run and its versioned result is `pass`.
- Confirm the task's Evidence `Contract` line records the task-start capsule fingerprint and that completion recompiled the same fingerprint; a drift result returns the task to authoring for explicit reauthorization instead of review.
- A behavioral task's checks must prove observable Acceptance through the public interface, not build-only or shape-only evidence.
- For a red-green strategy (`vertical-tdd`, `regression-first`), confirm concrete per-label `.red` and `.green` Evidence exists for the same check; evidence-first tasks instead name their observable proof.
- A failure message must **name the actual cause** of what it reports. Watch for one condition guarding **two distinct failures** — `if result is None or result["status"] != expected` reports the first failure's message when the second one happened, sending the reader to a place with no problem in it. Split the condition. No gate can judge this: deciding whether a sentence misleads needs a model, so it stays here.
- When two tasks in the change declared the same Touch set under a red-green strategy — `keel gate task-start` warns about this — ask whether they turned out to be **one behavior** split in half. The tell is that the first task's minimal implementation was wrong in the field, or that the second had no honest red left because the first already made its checks pass. The gate can only see the shape; by completion you can see the outcome, which is the only point at which this is answerable.
- Scope attribution is now the gate's job by default: `keel gate task-complete` compares the worktree against the dirty set `task-start` recorded and refuses a path outside Touch, so a `pass` is evidence about scope rather than silence about it. Two cases still need you. When the gate reports paths as *unattributed* — no recorded set, because the manifest predates the field or the guard was cleared — nothing was checked and the review is the only scope evidence. And a path already dirty when the task started stays unattributed only while its content matches what was recorded then; if the task changed it again, the gate attributes it — so read the gate's silence about such a path as evidence its content was never touched again, not as an unconditional exemption.
- For `Coupling: required`, confirm one complete candidate reached its completion gate and generated artifacts are aligned.

## Semantic Review

Record the current agent's judgment inside the selected task Evidence:

- `Status`: `pass` only when the task is ready to complete.
- `Acceptance check`: why the behavior evidence proves the authored Acceptance.
- `Scope check`: why the actual changes stay within Touch; identify an explicit base if deterministic comparison was used.
- `Findings`: `none`, or every finding with the disposition it actually has.

A finding has three, and the criterion is what the task did about it — not
whichever marker gets past the gate:

- **`Resolved here:`** — found and fixed inside this task. Name what proves it:
  an `M<n>` check this task declares, or a repo-relative path that exists. If no
  check covers it, the fix is not proved and the finding is one of the other two.
- **`Durable owner:`** — real, still open, and someone must do it. Name an
  absolute `https://…` tracker reference or a repo-relative path that exists.
  The reference must already carry the content it claims to hold.
- **`Discard reason:`** — considered, and deliberately not being done. Say why.

Picking the marker that passes rather than the one that is true is how a repair
gets filed as a dismissal, and the archive then records the opposite of what
happened.

The Review remains in tasks.md. A user-facing Report summarizes delivery but is not hidden gate state. Do not let Core or this checklist write evidence automatically.

## Domain lenses

When the change's artifacts or Touch extensions signal a domain, consult the matching lens's `Execution and review checks` section from `keel/lenses/` — the lens whose `Applies when:` header matches — before concluding the review, and load only that one. When no lens matches, load nothing.

## Expectation and follow-up ownership

Each related critical expectation needs behavior evidence, a durable follow-up owner, or an explicit discard reason. Relevant `D<n>`, `F<n>`, `A<n>`, and `Q<n>` references in Covers must agree with their OpenSpec basis and resolution owner. Unresolved authority returns to OpenSpec authoring.

A durable owner declared as a URL must **already carry the content** it claims to hold, at the moment
it is cited. A valid link to an empty issue owns nothing: create the content, then reference it. Check
this **when it is cited**, not at archive — a check deferred to the close finds the same fact after
the reauthorization it should have prevented. This is **not a deterministic gate check** and must not
become one: a gate that fetched a reference would stop being local and offline, which is the property
its verdict rests on.

`keel/HANDOFF.md` is an optional pointer override and cannot own findings, critical expectation state, evidence details, or follow-ups.

## Skill change review

For a new or materially expanded dedicated skill, confirm the authoring evidence
identifies authoritative sources, provenance and license implications, realistic
positive and negative trigger cases, and real-task evidence. Confirm detailed
conditional knowledge uses progressive references when it is not needed on
every activation.

The canonical portable `SKILL.md` must agree with every declared target
projection. Target metadata may be additive, but it must not redefine skill
behavior or make Keel the authority for target-native discovery or activation.

## Planning artifact funnel

When the work followed an accepted native plan-mode artifact, confirm its decisions affecting scope, Acceptance, completion, or execution boundaries were recorded in proposal, design, specs, or tasks before implementation. A material decision found only in session state is missing authority and returns to OpenSpec authoring; the session plan file is never execution authority.

## Output

Report one of:

- `pass`
- `return-to-work`
- `create-owner-first`
- `escalate`

Do not expand implementation scope during review.

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
- When no trustworthy explicit Git base exists, do not attribute dirty paths automatically. Review scope semantically.
- For `Coupling: required`, confirm one complete candidate reached its completion gate and generated artifacts are aligned.

## Semantic Review

Record the current agent's judgment inside the selected task Evidence:

- `Status`: `pass` only when the task is ready to complete.
- `Acceptance check`: why the behavior evidence proves the authored Acceptance.
- `Scope check`: why the actual changes stay within Touch; identify an explicit base if deterministic comparison was used.
- `Findings`: `none`, or each unresolved finding with a durable OpenSpec task/new change, archive-evidence owner, or explicit discard rationale.

The Review remains in tasks.md. A user-facing Report summarizes delivery but is not hidden gate state. Do not let Core or this checklist write evidence automatically.

## Domain lenses

When the change's artifacts or Touch extensions signal a domain, consult the matching lens's `Execution and review checks` section from `keel/lenses/` — the lens whose `Applies when:` header matches — before concluding the review, and load only that one. When no lens matches, load nothing.

## Expectation and follow-up ownership

Each related critical expectation needs behavior evidence, a durable follow-up owner, or an explicit discard reason. Relevant `D<n>`, `F<n>`, `A<n>`, and `Q<n>` references in Covers must agree with their OpenSpec basis and resolution owner. Unresolved authority returns to OpenSpec authoring.

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

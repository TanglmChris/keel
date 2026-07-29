---
name: keel-align-expectations
description: Align explicit requirements, implicit expectations, non-goals, observable acceptance, evidence, and decision authority before OpenSpec specs and executable tasks finalize. Use when authoring or updating a proposal, design, specs, or tasks, or when a request hides a material product choice. Do not use for routine implementation of an already-authorized task, unrelated conversation, or facts the repository can answer.
---

# keel-align-expectations

## Purpose

Turn user intent and repository facts into durable OpenSpec authority before specs and executable tasks harden. Alignment is risk-scaled: clear, complete, low-risk requests pass through a compact quick path; material ambiguity switches to a focused deep path. This skill owns materiality routing, acceptance authority, and write-back ownership; how questions are presented interactively is the host runtime's concern, and it does not replace `/opsx:apply`, review, or OpenSpec artifact mechanics.

## Routing

Take the quick path when the request, repository facts, and intended observable outcome are coherent and no material choice is unresolved. Switch to the deep path when a choice can materially change: user-visible behavior, an external interface, acceptance, security/privacy/permission boundaries, data loss or migration, protocol/state/timing/reset semantics, generated equivalence, irreversible cost, a dependency or architecture commitment, or when a contradiction appears between user intent and repository facts.

Missing wording, stylistic preference, discoverable facts, and reversible implementation detail stay on the quick path. For routine implementation of an authorized task, unrelated conversation, or a factual question the repository answers, do not start a product interview and do not mutate OpenSpec artifacts.

## Quick path

State the extracted goals, non-goals, observable Acceptance, constraints, and evidence expectations compactly, label any non-material assumptions, and proceed. A complete low-risk request may satisfy the checkpoint in one compact confirmation without an interactive pause.

## Deep path

Pause spec/task finalization and ask one material decision at a time. Each question explains in plain terms why the decision matters and provides a recommended answer. Continue only until executable authority is clear; do not run a broad brainstorming session. A material choice that stays unresolved becomes a Q<n> with an owner or resolution gate, and no affected task becomes executable until it is accepted, verified, durably owned, or explicitly discarded.

## Implicit expectations are proposals

Label inferred expectations (accessibility, compatibility, failure behavior, migration, performance, security, and similar unstated candidates) as candidate expectations and explain their impact. A candidate becomes authority only when the user explicitly accepts it or durable repository/product authority verifies it. Silence does not authorize a material product choice, interface change, risk boundary, or acceptance downgrade.

## Repository facts before user questions

Before asking the user, inspect the relevant code, tests, docs, OpenSpec artifacts, issues, and verified runtime behavior. Record verified facts as F<n> with their basis; escalate only the user-owned product choice that remains after the facts are known. When sources disagree on an acceptance-relevant fact, surface the contradiction and ask who or what has authority instead of silently choosing one source.

## Write-back

Accepted alignment routes to existing OpenSpec owners; create no separate alignment ledger, chat-memory dependency, or HANDOFF payload:

- proposal.md owns motivation, scope, goals, and non-goals.
- design.md owns accepted D/F/A/Q statements, rationale, constraints, and risks.
- specs own observable requirements and positive/negative/edge/failure scenarios.
- tasks.md owns Covers, verification strategy and checks, scope, and stop boundaries that reference the accepted authority instead of duplicating chat prose.

## Decision precedents

When the repository declares a precedent store, consult the precedent matching a decision before
escalating it, and record a new precedent when the user decides something the store does not cover.
A precedent store is user-authored and never bundled; a repository that declares none behaves
exactly as one without this section.

Record the reasoning, not only the conclusion. "Chose A" applies only to the situation literally
recorded; "chose A because B fails offline" can be applied to a case nobody has seen yet, and — just
as important — recognised as *not* applying when the new case is online. Only the reasoning transfers.
A precedent with no rationale is incomplete and is not applied.

Three rules govern use:

- **Cite only where you replaced a question.** Name the precedent you applied exactly when, without
  it, you would otherwise have interrupted the user. Decisions that would not have interrupted them
  are not cited, so that a citation always marks a decision made in the user's place rather than
  running commentary.
- **Promotion is the user's act.** A precedent enters as `recorded` and is offered as a
  recommendation while the question is still asked. To make one applicable without asking, propose
  the promotion and name the precedent; it changes only when the user accepts. There is no usage
  count, age, or other threshold that promotes anything, because a threshold crosses with nobody
  watching.
- **A precedent answers a recurrence; it never reclassifies.** It may shorten a decision inside its
  materiality category by supplying the recorded answer and its reasoning. It never moves a decision
  out of the categories that require asking, and no accumulation of precedents makes a category
  immaterial. A decision that resembles a precedent but sits in a different category is not a match.

A precedent informs a decision and never substitutes for a proof: gates, evidence, Review, and the
write guard are untouched by anything in the store.

## Unattended runs

Work enters an unattended run only by the repository's declared triage policy — an issue carrying a
label listed under `triage:` in `keel/config.yaml`, evaluated with `keel triage --labels <labels>`.
Pass what `gh` returned; Keel never fetches the issue. Admission comes from that declaration and
never from a precedent, however much triage history the store accumulates: whether an issue becomes
work is a materiality decision, and a precedent may not move one out of that list.

Admission answers "may this begin" and decides nothing after it. Alignment still escalates material
choices, the gates still run, and the write guard still binds.

An unattended run may triage, author, implement, verify, push where `authorize:` permits, and
**open a pull request**. It **may not merge** one — merging is where an unreviewed decision becomes
the project's history, and no declaration in Keel authorizes it.

Stopping at a decision the user must make is the **designed boundary rather than a failure**.
Report where the run stopped and why. Do not widen the triage policy to stop it happening.

**Keel schedules nothing.** `/loop`, cron, and CI triggers belong to the host runtime; Keel's part
is making each step decidable with authority.

## Domain lenses

When the change signals a specific domain, look in `keel/lenses/` for a lens whose `Applies when:` header matches, and read only that lens before asking domain questions; do not load unrelated lenses. When no lens matches, or the repo defines none, proceed on the domain-agnostic path. Lenses are user-authored; scaffold the bundled starting points with `keel lenses add` (web, hardware, hardware-dsl).

## Boundaries

Alignment does not implement code, expand Touch, change selected-task acceptance, replace `keel-review-checklist`, or own follow-ups. If implementation later discovers a new material expectation, stop and return to OpenSpec authoring before continuing.

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

## Domain references

When the change touches a specific domain, read only the applicable reference before asking domain questions; do not load the others:

- references/web.md for UI, API, routing, auth/session, persistence, or backend integration work.
- references/hardware.md for Verilog/SystemVerilog interface, protocol, reset, or verification work.
- references/hardware-dsl.md for hardware modeling DSL, generated RTL, or golden/equivalence work.

## Boundaries

Alignment does not implement code, expand Touch, change selected-task acceptance, replace `keel-review-checklist`, or own follow-ups. If implementation later discovers a new material expectation, stop and return to OpenSpec authoring before continuing.

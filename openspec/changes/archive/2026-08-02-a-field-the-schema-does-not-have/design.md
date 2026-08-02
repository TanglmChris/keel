## Context

A gate that refuses work has one job beyond the refusal: to say what to change. The refusals in this repository are mostly good at that — `Invalidates`, `Expectation Coverage`, and the `M<n>` check diagnostic all print the shape they want. The required-field check did not, and the completion gate printed a second problem on top of it that was true of no schema the author had chosen.

The two defects compound. Alone, `Evidence must be concrete.` is thin but honest — it names the right field, and bisecting the field finds the token. Paired with `Commands must define at least one M<n>.`, it is worse than thin: the reader has a specific, actionable-looking problem naming a specific field, and that problem is an artifact. #52 reports the whole cost landing on the artifact.

## Goals / Non-Goals

**Goals:**
- A required field refused for an unfilled token names that token, and names the escape.
- A gate that could not compile the contract reports why, and derives no second problem from a fallback to another schema's fields.
- Suppression provably cannot make a failing gate pass.

**Non-Goals:**
- Widening or narrowing `UNFILLED_TOKEN` (D3). What the gate accepts is unchanged by this entire change; only what it says changes.
- The `#49` family — `Covers` reporting present-but-unparsed as `Missing`, the `Findings` durable-owner line position, and block fields parsed per line. Same neighbourhood, different mechanism, separately owned.
- Changing the `missing-field` or `missing-commands` diagnostic codes (D4).

## Decisions

- **F1** — reproduced 2026-08-02 at 5.19.0 in a scratch repository. A compact fixture whose `Evidence` reads `M1: pass —— 最大照亮比例 0.001916（判据 <0.02），最小照亮比例 0.998107（判据 >0.98）。` produces from `task-complete`, in order, `missing-commands: Commands must define at least one M<n>.` then `missing-field: Evidence must be concrete.` The same fixture at `task-start` produces the second alone. *Basis: direct execution of `node bin/keel.js gate task-complete --json`.*
- **F2** — `UNFILLED_TOKEN` is `/(<[^>]+>|\bTODO\b|\bTBD\b|\bplaceholder\b)/i` (`src/core/task-contract.js:28`). `<[^>]+>` is unbounded, so it spans from the first `<` to the last `>` across a whole sentence. In F1's line it captures `<0.02），最小照亮比例 0.998107（判据 >`. *Basis: the expression, and the captured span printed while reproducing.*
- **F3** — `unfilledToken()` (`:54`) already returns exactly that captured token, and its comment states its purpose: "Used to explain a non-concrete field instead of letting the caller infer a different schema from it." `missingFieldProblems()` (`:416`) does not call it. *Basis: the source at 5.19.0.*
- **F4** — the same file already does this correctly one function away. `commandProblems()` (`:254-268`) names the token for an `M<n>` check and offers the inline-code escape, and `requiredFieldProblems()` (`:370-384`) names it for a non-concrete `Verify`. Both are shipped requirements in `openspec/specs/keel-task-capsule/spec.md`. *Basis: the source and the published spec.*
- **F5** — `gates.js:851` sets `usableContract = null` whenever `contract.diagnostics.length > 0`, and `:853` pushes those same diagnostics into `problems` unconditionally. So `contract === null` inside `completionChecks()` implies at least one problem is already recorded. *Basis: the source at 5.19.0.*
- **F6** — the repository has already decided the question #52's suggestion 2 reopens. `keel/archive/follow-ups/2026-07-27-unfilled-token-keywords.md` records the decision that all four token forms are exempt *inside backticks* and reported outside them, with the reasoning: "the backtick is a deliberate act", and "a token left bare in the text is still reported". The shipped `non-concrete-verify` message states the rule to users in the same terms — angle brackets read as unfilled "including inside prose". *Basis: that note and `src/core/task-contract.js:377-381`.*

- **D1** — `missingFieldProblems()` consults `unfilledToken()` and, when one matched, names it and offers the inline-code escape. The wording mirrors the `M<n>` diagnostic at `:254-268` rather than inventing a third phrasing for the same event, because an author who has learned one should recognize the other. A field that is empty, `none`, or `pending` keeps the unqualified sentence — there is no token to name, and naming none would be a worse message than the plain one. *Basis: F3, F4 — the mechanism and the wording both already exist.*
- **D2** — when `completionChecks()` receives no contract, it does not emit `missing-commands`. The honest statement is that the verification form is unknown: the contract that would have reported it failed to compile, and the fallback reads a field belonging to the other schema. Per-label evidence checks are untouched, because for an expanded v3 task the fallback returns real labels and those checks are meaningful; for a compact task it returns none and the loop is already empty. *Basis: F1, F5.*
- **D3** — `UNFILLED_TOKEN` is not touched. Two separate reasons, either sufficient. It is a material choice: today `（判据 <0.02）` is refused and after a narrowing it would be accepted, which changes what the gate lets through and belongs to the owner. And it contradicts F6, a decision already recorded with its reasoning. Recording a narrowing here would also quietly reverse the user-facing sentence in the `non-concrete-verify` message without that message changing. *Basis: F6, and the acceptance change being user-visible.*
- **D4** — the `missing-field` code is unchanged when a token is named. The verdict is the same — the field is not concrete — and only the explanation improves; a new code would make every consumer keying on `missing-field` miss the case it most needs to see. This follows `missing-command-check`, which kept its code when it gained the token. *Basis: F4; `scripts/validate_plugin.py:4916` and `:7741` both key on `missing-field`.*
- **D5** — the fix is verified through `keel gate task-complete` on a real repository, not by calling the two functions directly. #52's whole report is about the *pair* of messages a user sees together and their order; a unit test of `missingFieldProblems()` would prove the half that was never the expensive half. *Basis: F1 — the artifact only appears through the gate.*

## Hidden Knowledge / Assumptions

- **A1** — an author who sees the named token will recognize whether it is a slot or literal text. The message does not decide for them; it names the span and offers both repairs. *Basis: D1. Owner: this change — the failure mode if wrong is the message being ignored, which is today's state, not a regression.*
- **A2** — no consumer outside this repository keys on `missing-commands` appearing when a contract fails to compile. `grep` over `src`, `plugins`, `scripts`, and `openspec` finds the string only at its emission site. *Basis: that grep at 5.19.0. Owner: this change — the code and message are unchanged for every case where a contract did compile.*

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- Suppressing a problem is the direction that can make a gate wrongly pass. Bounded by F5 structurally — the suppression's precondition is that diagnostics exist, and those diagnostics are already in `problems` — and asserted directly by the scenario, which checks the gate still returns `fail`. That assertion is the one that must not be dropped.
- Naming the token prints a span of the author's own text into an error message, and F2's unbounded match means that span can be long. That is information, not noise: the length of the captured span is itself the clearest signal that the match was accidental, which is the fact #52's reporter needed and did not get.

## Open Questions

- **Q1** — should `UNFILLED_TOKEN` stop matching angle brackets in prose? #52's suggestion 2 asks for it, and F6 records the repository deciding the opposite with its reasoning. Alignment surfaced this as a contradiction between reported intent and repository fact rather than resolving it: it changes what the gate accepts, which is user-visible and is the owner's call, and no precedent may move a decision out of that category. **This question opens no `Covers` entry and blocks no task in this change** — D1 and D2 improve the explanation of a refusal that happens either way, and both remain correct whichever way Q1 is answered. *Durable owner: https://github.com/TanglmChris/keel/issues/52 — recorded there with the measurement and F6, so a later run authoring against #52 finds the contradiction before writing the narrowing.*

## Alignment

Ran `keel-align-expectations` before tasks finalized. No `keel/lenses/` directory exists and the declared precedent store `../decision-precedents` is absent, so the domain-agnostic path applied and no precedent informed any decision here.

Quick path for the work itself: the request, the reproduction, and the intended observable outcome agree, and every change is to message text or to which problems are reported — reversible, with no interface, dependency, or acceptance commitment. Deep path fired once, on the intent/fact contradiction now held as Q1.

Candidate expectations inferred and **not** taken as authority: that the named token should be truncated when long (rejected in Risks — the length is the signal), and that empty and unfilled fields deserve distinct diagnostic codes (rejected as D4). Neither is user-accepted, so neither becomes a requirement.

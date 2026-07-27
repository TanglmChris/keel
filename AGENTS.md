# Keel v5.2.2 Agent Protocol

<!-- keel:start version=5.2.2 -->
## Session Start
- Before deciding what to do, run `keel context` and follow its versioned result and minimal read list.
- `keel/HANDOFF.md` is an optional validated override for otherwise ambiguous human intent. An absent file is normal; never infer continuity from native memory, goals, transcripts, or Git dirty paths.

## Full/Lite routing
- Use Full mode for new features, external interface changes, cross-module work, changes over 3 files or 100 lines, architecture decisions, protocol or state-machine changes, and user-requested complete flow.
- Use Lite mode only for local fixes, small scripts, docs edits, or test additions with no interface change, no new dependency, no new design decision, and locally provable impact.
- hardware escalation: hardware work moves to Full mode before implementation when it changes signals, state machines, CSRs, protocol fields, reset, valid-ready, backpressure, ordering, CDC, security, permissions, random, keys, or authentication semantics.

## Full mode
- Use official OpenSpec OPSX for Full-mode proposal, design, specs, tasks, sync, and archive state under `openspec/`.
- During OpenSpec authoring, align expectations with `keel-align-expectations` before specs and executable tasks finalize: quick path for complete low-risk work; risk-triggered deep path — the only question-loop entry — when proposal, design, tasks, domain lenses (user-authored `keel/lenses/*.md`), or high-risk changes expose hidden-knowledge risk. Inspect repository facts before user questions and keep inferred candidates unauthorized until accepted. Missing authority returns to OpenSpec authoring before implementation continues. New or materially expanded dedicated skills require authoritative source research, provenance/license review, realistic positive and negative trigger cases, and real-task evidence; keep portable `SKILL.md` authority canonical, target metadata additive, and runtime discovery target-native.
- Use `/opsx:apply` as the implementation entry. Select one OpenSpec task or a small contiguous task group, then execute it in the current agent conversation.
- The current agent owns Keel execution decisions. Do not transfer Keel ownership or hand Keel-managed execution to another runtime, agent, operator, or unbounded subagent unless the selected task or user explicitly authorizes it.
- Target-native subagents are allowed only as bounded helpers/evidence producers when the current agent decides they are useful; they must receive a scoped brief and return report/evidence for current-agent review.
- Keep the selected task capsule authoritative. Author tasks in the compact v4 form (Covers, Touch, Verify with Strategy plus M<n> checks, Evidence anchor) inheriting versioned `keel-task-capsule/v1` defaults; compatible expanded v3 tasks compile through the same parser and contradictory legacy fields fail with migration diagnostics. Read gives starting context, Touch is the write boundary, Verify checks prove Acceptance, and the autonomy boundary controls fallback decisions.
- After implementation, update OpenSpec state or keel/CHANGELOG.md only when they are the correct long-term location. Create HANDOFF only as an explicit pointer override.

## Task contract discipline
- `implementation` means implement only the selected task and modify only Touch files; `diagnose-only` means reproduce, inspect, and report evidence without product writes unless Touch authorizes diagnostics; `plan-first` means propose the minimal plan before product writes.
- Do not expand scope, add dependencies, redesign interfaces, or change unauthorized state, protocol, timing, reset, ordering, permission, random, key, authentication, or security boundaries.
- Reports include Summary, Changed Files, Scope Check, Tests Run, Risks, Out-of-scope Need, and Follow-ups. Do not commit, push, create archive entries, or create handoff entries unless the selected task or human instruction explicitly allows it.

## Expectation alignment
- Critical expectations are documented statements that affect completion or execution boundaries; keep them in OpenSpec or Keel artifacts, not chat memory.
- `Expectation -> Slice -> Evidence` Completion Gate: task groups cannot be reported complete until each related critical expectation has behavior evidence, a durable owner, or explicit discard rationale.
- Task Authoring Gate: before tasks are executable, cover each relevant critical expectation with a slice, durable owner, or explicit discard reason.
- Slice Start Gate: before implementation, the selected slice/group must name source expectations and compile to a complete capsule whose Read, Touch, Acceptance, verification checks, and Stop/Autonomy boundaries execute without guessing; rough future slices cannot be selected or marked complete.

## Coupled execution
- When one task changes artifacts that must be regenerated and verified together, set `Coupling: required` and complete the Coupled Iteration Contract in design.md before execution.
- tasks.md must define one complete candidate, provisional failures allowed inside it, a completion gate, final assertions, evidence, and separate current-candidate versus immediate-task Stop Rules.
- Do not execute an incomplete coupled contract or invent missing design authority, baselines, or acceptance criteria.

## Execution boundary
- Execute implementation, diagnostics, verification, and recovery inside the current agent session. Keep scope expansion, acceptance changes, product fallback, and rollback decisions explicit in the conversation.
- Preserve the current checkout on verification failure or context pressure. Continue from the evidence, record a blocker, or explicitly roll back to last-green only when the user or selected task authorizes it.
- A task without a pre-authorized Autonomy boundary defaults to hard-stop. A bounded fallback is valid only when the task states its exact reversible limit and required evidence.

## Completion gates
- Run `keel gate task-start`, `keel gate task-complete`, and `keel gate change-close` for the shared deterministic structural gates; they are local, model-free, write-bounded — on Claude a passing `task-start` writes the disposable write-guard manifest by default (`--no-guard` opts out) and no other gate outcome writes project state — and return `pass`, `fail`, or `needs-review`. task-start returns the compiled capsule and fingerprint; record it in the task's Evidence `Contract` line before implementation, and resume, projection, and completion recompile and compare it — drift hard-stops until explicit reauthorization returns to authoring and clears stale execution evidence.
- Deterministic gates validate contract/evidence shape only. The current agent records semantic Review `Status`, `Acceptance check`, `Scope check`, and `Findings`, then runs `keel-review-checklist` at completion gates.
- `/opsx:sync` and `/opsx:archive` completion is gated by `keel gate change-close --action sync|archive` plus `keel-review-checklist`, not a runtime hook; v5 ships no sync/archive hook, so this gate is capability-`manual` on every target. The `keel` plugin's only runtime hooks are SessionStart continuity and the PreToolUse write guard.
- Target command surface differs by runtime: Codex OpenSpec commands are global prompts under `CODEX_HOME/prompts/opsx-*.md`, while OpenCode uses project-local `.opencode/commands/opsx-*.md`.
- Target automation is capability-probed, not assumed by target name. Unverified activation, trust, version, blocking, or native projection remains `manual`; `keel project` creates only one-way views from OpenSpec, and goal/task/subagent projection requires explicit authorization.

## Lite mode
- Keep Lite changes local and reversible; upgrade to Full immediately when a Full trigger appears.
- Lite does not write OpenSpec state by default.
- Do not create keel/HANDOFF.md for routine Lite continuity; use it only when explicit human intent must override inference.

## verification discipline
- A task's `Commands` MUST verify the observable behavior named in its `Acceptance`, exercised through the public interface, not compile/build success and not the shape of data structures or signatures. A behavioral task needs behavior assertions or an explicit smoke step. Author `Commands` to this bar when writing tasks.md.
- Drive test-first layers with `keel-tdd-or-test-first`: red-green in vertical slices (one test, one implementation), never horizontal (all tests, then all code). Mock only at system boundaries; never mock your own modules. `Verify` names one supported strategy (vertical-tdd, regression-first, characterization, snapshot-characterization, rendered-behavior, evidence-first); an unsupported strategy fails task-start, and red-green strategies record concrete per-label `.red`/`.green` Evidence that `keel gate task-complete` enforces.
- Default discipline by layer: deterministic/reproducible outputs keep byte or snapshot characterization tests and are not downgraded; boundary contracts and pure logic are test-first with `Commands` asserting behavior at the public interface; interactive/UI surfaces test behavior through the real rendered interface with no self-mocks and vertical slices, strict red-green optional by cost.
- `keel-review-checklist` additionally checks that each behavioral task's `Commands` actually verify its `Acceptance` behavior (not build-only, not shape-only); record a follow-up or add the missing gate when they do not.
- When a selected task needs tests, assertions, lint, TBs, or behavior proof before implementation, invoke `keel-tdd-or-test-first` before writing the implementation.

## User-facing communication
- When asking the user to decide, first explain in plain terms what the choice is, why their decision is needed, and what each option means for them.
- Keep internal jargon out of option labels. Put technical terms later only when they help the decision.
- Match the user's language where practical; understandable choices are part of the protocol.

## Follow-up Ownership
- Before archive or handoff, unresolved follow-ups must be owned by the current OpenSpec tasks, a new OpenSpec change, archive evidence, or an explicit discard reason.
- `keel/HANDOFF.md` is an optional pointer override, not a durable follow-up owner. It may name one durable owner and action but must not contain the work item.
- `keel/CHANGELOG.md` records Keel workflow/protocol/project-operation changes. Root `CHANGELOG.md` is product-facing only when the host project explicitly owns one.
- `keel/archive/` stores historical source documents and evidence. Official OpenSpec stores completed changes under `openspec/changes/archive/`.

## token discipline
- Keep resident files concise and route detail into official OpenSpec artifacts or archive evidence.
- Read only the documents needed for the current decision and summarize instead of copying long rationale.

## preflight
- Do not install automatically without explicit user approval.
- If official OpenSpec instructions or Keel protocol files are missing for Full-mode work, ask the user to run `keel --init --target <target>` before creating Full-mode artifacts. Keel carries the OpenSpec CLI dependency; do not ask for a separate OpenSpec install unless the Keel package dependencies are broken.
- If this repo is missing or partially missing the v5.2.2 protocol, prompt before install and suggest keel --init --target <target>.
<!-- keel:end -->

## Project Conventions

<!-- Deliberately outside the Keel managed block above: `keel --install` rewrites
     that block from assets/bootstrap/AGENTS.md and would discard anything placed
     inside it. -->

- Deferred, actionable project follow-ups are owned by **GitHub issues** on this repository. Record the source evidence, the rationale, and the consequence of not doing it in the issue body. This satisfies the durable-owner requirement in `keel-expectation-slice-evidence-gates`, which never required an OpenSpec change as the owner.
- `keel/HANDOFF.md` stays a pointer-only override and never owns follow-ups, findings, or expectation state. `keel/archive/` holds historical evidence, not active follow-ups.
- Do not create a standing OpenSpec change as a follow-up store. A change directory carrying a proposal or specs but no task checkboxes is inferred as actionable authoring work in perpetuity (`keel-stateless-continuity / Incomplete authoring remains actionable`), which turns every session start into a false pointer.
- **Recording a finding on a task**: `keel gate task-complete` will not accept a bare issue URL as a Review `Findings` owner. `findingOwnerIsDurable` (`src/core/gates.js`) accepts only a `Discard reason:`/`Discard rationale:` prefix, a `keel/archive/…` path, or an existing `openspec/changes/…` artifact. So write the finding as a short note under `keel/archive/follow-ups/` that points at the issue, and cite that path in `Findings`. The issue owns the substance; the note is the pointer the gate recognizes. This gap between the spec's unconstrained "durable owner" and the gate's three accepted forms is tracked in issue #12 — if it is closed, simplify this bullet.

## Context

Keel has been able to *describe* a bounded delegation since 4.1.0 and has never been able to perform one. The vocabulary, the projection event, and the capability keys all exist; the only compiled brief refuses every mutation verb, so the sole executable form of delegation is read-only evidence production.

The question this change had to answer first was not "how do we contain a subagent that writes" but "is it already contained". It is.

## Goals / Non-Goals

**Goals:**
- A repository and a task can declare that a task may be implemented by a subagent, and which capability tier runs it.
- The declaration is durable, reviewable, and diffable — it survives a context reset, which is the property a permission granted in conversation does not have.
- Every proof downstream of the declaration is unchanged: the guard binds Touch, `task-complete` demands identical evidence, Review and the checkbox stay with the current agent.

**Non-Goals:**
- Keel does not choose a model. It carries a declared tier; the target resolves it.
- Keel does not estimate task size, difficulty, or cost, and never infers a tier from them.
- No scheduling, no automatic delegation. A declaration authorizes delegation; it never triggers one.
- The read-only helper contract is not extended, relaxed, or replaced.

## Decisions

### The containment already exists

**F1** — The PreToolUse write guard fires for a subagent's tool calls and holds the Touch boundary identically. Verified 2026-08-01 by direct probe: with a live `keel/guard.json` declaring `touch: ["keel-guard-probe-ALLOWED.txt"]`, a spawned subagent's `Write` to `keel-guard-probe-DENIED.txt` was denied with the byte-identical guard message the current agent receives, while its `Write` to the allowed path succeeded. *Basis:* the successful write is the positive control — it proves the subagent could write at all, so the denial is the guard acting rather than an unrelated subagent failure. Without that control the probe would have been consistent with a subagent that simply cannot write.

**D1** — Delegation is therefore a **declaration, not a mechanism**. This change adds no enforcement machinery. *Basis:* F1.

**D9** — `plugins/keel/scripts/pretooluse-guard.js` is not modified by this change, and no task may Touch it. *Basis:* F1 establishes it already behaves correctly; an edit would be unauthorized scope, and this file has a history of ordering defects (5.3.9 was the third) that make casual edits expensive.

**F2** — The guard passes every write through silently when `keel/guard.json` is absent. *Basis:* stated in the hook's header comment and in `keel-touch-write-guard`.

**D5** — Delegation requires an **active guard manifest**. Delegating with no manifest present is refused. *Basis:* F2. Without this rule the containment the owner chose does not exist, and — this is the dangerous part — the screen looks identical either way. There is no observable difference between "the guard allowed this write" and "no guard was running", so the condition has to be checked before the delegate starts rather than inferred from its behavior afterward.

**F8** — `keel-touch-write-guard` does not mention subagents at all. *Basis:* full-text read of the spec.

**D10** — The guard spec gains the delegated writer explicitly. *Basis:* F8, and 5.3.9's finding that a spec silent on a boundary lets a reviewer reasonably "correct" the code toward the opposite behavior. A spec that describes only the current agent's writes invites exactly that.

### What the declaration says

**F9** — `authorize:` is a closed set of four names pinned at spec level, and an unrecognized entry authorizes nothing. *Basis:* `keel-standing-authorization` requirement text.

**D3** — Delegation gets its own `delegation:` block; `authorize:` is **not** extended. *Basis:* the four existing names share a property delegation does not — `commit`, `push`, `release`, and `archive` each change durable repository or outside-world state, while delegation only routes execution inside a boundary that already exists. Adding a fifth name would redefine that closed set from "outward actions" to "anything requiring permission", and the closed set's value is precisely that it is narrow enough to read at a glance. A secondary reason: `authorize:` is a flat list of names feeding `Autonomy boundary:` inheritance, and a tier is a key with a value, not a permission name — the shapes do not match.

**F10** — Keel carries no model awareness anywhere in `src/` or `bin/`. *Basis:* grep across both trees returns one unrelated comment.

**D2** — The tier vocabulary is **abstract and target-resolved**. Keel names capability tiers and never a concrete model. *Basis:* two independent failures of the alternative. A model identifier is target-specific — one named for Claude is meaningless to Codex, and Keel supports three targets — so a concrete vocabulary would have to be partitioned per target or be wrong for two of them. And model identifiers expire: the next release leaves a declaration pointing at something retired, in a file whose whole purpose is to still be correct after a context reset.

**D11** — Tiers describe the **capability the work requires**, not the size of the work. *Basis:* 5.7.0 refused size and complexity estimates for triage because they authorize the agent's guess about difficulty. A tier named for required depth of reasoning is declared by a human about the work; a tier named for estimated size invites the same guess through a different door. The vocabulary is chosen so the guess has nowhere to live.

**D4** — The delegate writes in the **current worktree**, under the existing guard. *Basis:* owner decision, 2026-08-01. Isolated worktree plus merge-back was rejected: the guard already provides the containment, and merging back would require state-machine vocabulary the protocol does not have.

### What the delegate may and may not settle

**F4** — `keel-native-runtime-projection` already requires an authorized subagent's return to be report or evidence only, and already states that native subagent completion does not satisfy `task-complete`. *Basis:* spec lines 63-79.

**F5** — `src/core/helper.js` refuses every mutation verb and the words *subagent* and *delegate*. Its contract, `keel-helper-brief/v1`, guarantees before/after repository byte identity. *Basis:* source read, lines 23-32.

**D6** — `helper.js` is untouched, and no mutation verb is admitted to it. *Basis:* F5. Byte identity is the only thing the helper contract proves, and admitting a mutation verb would destroy it; a delegate is a second role beside a helper rather than a helper with the restriction lifted. **Superseded in part by D15**: this decision originally also proposed a separate write-capable contract *module* beside the helper brief. That module is not built — the projection Keel already publishes carries the delegation instead — and the correction is recorded here rather than by rewriting the entry, because the discarded half is what D14 was formulated against.

**D7** — A delegate's return is a **claim**, and the current agent **re-runs every `M<n>` check itself** before recording Evidence. A delegate's reported command results are never recorded as Evidence. *Basis:* F4 plus a structural gap. The helper contract can accept a return because it verifies byte identity afterward; that verification is unavailable by construction for a writer, since writing is what it was authorized to do. Re-running the checks is cheap, deterministic, and restores the property the byte check was providing — the current agent's evidence comes from the current agent.

**F6** — `keel-single-task-goal-execution`'s read-only requirement governs *helpers*. A delegated implementer is a distinct role. *Basis:* spec line 95. This change therefore does not weaken that requirement; it adds a role beside it.

**F7** — The compiled capsule hardcodes `helperAuthority: "read-only-evidence-only"` (`src/core/task-contract.js:943`), and `keel-task-capsule` states that default unconditionally. *Basis:* source and spec read. This is the statement the change makes stale.

**F13** — The single-task-goal adapters activate within a 4,000-character budget, and Keel refuses activation rather than omit Acceptance, fingerprint, or stop authority. *Basis:* `keel-single-task-goal-*.md` line 12.

**D8** — The single-task goal path admits a declared delegate, and its sole-writer invariant is **restated rather than removed**: the current agent remains the sole holder of *write authority*, and a delegate writes only inside the boundary that authority defined. *Basis:* owner decision, 2026-08-01. The invariant's purpose was never that one process performs the writes — it was that one party is answerable for them. F13 is a hard constraint on the restatement: the delegation fields must fit the existing budget, or activation refuses, and refusing is correct.

**D12** — A declared tier the current target cannot provide **refuses delegation and reports** the declared tier beside what the target offers; it never falls back to a different tier. *Basis:* consistency with F9's established shape — an unrecognized action name authorizes nothing rather than being silently dropped. A silent fallback would run work on a capability the owner did not declare while reporting success.

**D13** — Delegation composes with `triage:` and widens nothing. An unattended run may delegate exactly where a declaration permits it, and admission still answers only "may this begin". *Basis:* `keel-unattended-triage` scopes admission to the start of work; delegation is execution routing after that point. Neither declaration grants what the other governs.

### What Keel builds, and what it declines to build

**D14** — **Anything that duplicates or conflicts with a target runtime's native capability is not a Keel design goal.** Keel declares policy about a capability the host performs; it does not reimplement the capability. *Basis:* owner decision, 2026-08-01, raised as a challenge to this very change. The principle already had a home — `keel-surface-evolution-policy` governs what Keel builds versus cedes — but it was stated only as procedure (do not cede a surface without a coverage report; do not integrate a host surface without recorded design authority) and never as the scope rule those procedures serve. Stating it makes the boundary reviewable before code exists rather than after.

The distinction the principle draws, applied here: spawning a subagent, restricting its tools, choosing its model, isolating it, and running it in the background are all native host capabilities, and Keel implements none of them. What Keel contributes is what the host has no concept of — a declaration that is durable and reviewable in Git rather than decided in the moment, a refusal to delegate while no guard is active, the rule that a delegate's results are a claim the current agent re-runs, and a spec that owns the guard behavior a delegated writer already meets.

**D15** — No separate write-capable brief contract module is built. The write boundary and declared tier extend the existing `subagent-start` projection, which already carries the task, Acceptance, Touch, verification checks, fingerprint, and prohibitions. *Basis:* D14 applied to this change's own plan. A new contract module would compile a brief for the host's own agent-spawning interface to consume — that is the host's carrier, and a second one beside it is the duplication the principle names. The projection is a one-way view of OpenSpec, which is what Keel already does everywhere else.

**A3** — The tier vocabulary is the thinnest surviving layer, and it is worth naming as the part of this change most exposed to D14. The host can already select a model per call, so the tier's whole contribution is that the choice is bound to the task durably and does not expire when a model is renamed. *Basis:* D2 and A1. *Owner:* recorded here so a future reader evaluating this surface against D14 finds the argument already made rather than re-deriving it; if the durability argument stops holding, the tier is the first thing to remove.

**D16** — The consumer bootstrap does not carry the delegation clause. *Basis:* measured, not estimated — the `keel:start`/`keel:end` block is 1013 bytes against a sub-1KB budget, leaving 11 bytes of headroom, and the shortest honest delegation sentence needs about 76. The decision is not only a budget one: delegation is inert until declared, so a repository that installs the bootstrap and declares nothing is fully served by the single-writer sentence already there, and a scarce byte is better spent on what can go wrong *without* a declaration. The check therefore asserts that sentence stays true and that the budget is not quietly spent later, rather than demanding wording the block cannot hold. `AGENTS.md`, the full resident protocol, carries the whole rule.

## Hidden Knowledge / Assumptions

**A1** — Keel cannot observe which model actually executed a delegated task, and does not pretend to. The declaration is carried to the target; the target resolves and runs it. *Basis:* F10, and the absence of any Keel channel that observes a runtime's model selection. *Owner:* stated plainly in the `keel-authorized-delegation` spec and the `delegation:` config comment, in the same shape `keel-unattended-triage` states that Keel cannot verify a human applied a label. Recording the limitation is what stops a later reader from treating the tier as enforced.

**A2** — A delegate is assumed to be same-target and same-repository. Cross-runtime delegation stays prohibited unless the selected task or user explicitly authorizes it. *Basis:* the existing resident protocol prohibition, which this change does not touch. *Owner:* `keel-authorized-delegation` spec.

## Coupled Iteration Contract

Not required. No task in this change declares `Coupling: required`.

## Risks / Trade-offs

- **The declaration is advisory to the host** (A1). Mitigation: state it, do not imply enforcement, and keep every downstream proof independent of which model ran — the guard, the gates, and Review all behave identically either way.
- **A delegate could report green work that is not green.** Mitigation: D7 — the current agent re-runs the checks. This is the mitigation that makes the rest of the design safe, and it is the reason a wrong tier choice costs a retry rather than a bad merge.
- **Scope reaches two execution paths** after the owner brought the single-task goal flow in. Mitigation: F13's budget is a hard, testable constraint, and the invariant restatement (D8) is a wording change with an assertion rather than a behavioral loosening.
- **`keel/config.yaml` grows a fourth declaration block.** Its header already had to be corrected twice when blocks were added (5.5.0 introduced it as if `fast_check` were the only key; 5.6.0's "two independent declarations" was stale one release later). Mitigation: a task explicitly owns the header count, and `## Invalidates` quotes the current wording.

## Open Questions

**Q1** — Should the Evidence record only the *declared* tier, or should the target adapter be required to report back what it actually resolved? Reporting back is better provenance but needs a target-native return channel that may not exist on all three targets, and inventing one would violate the capability-probed rule that unverified surfaces stay `manual`. *Basis:* A1. *Resolve by:* the capability probe during implementation — a task must determine what each target can actually report before the spec commits to either. Until resolved, Evidence records the declared tier only, which is honest and available everywhere.

## Why

Keel can already describe a bounded delegation and cannot actually perform one. The projection surface, the capability keys, and the spec permission all exist, but the only *compiled* brief refuses every mutation verb, so the sole executable form of delegation is read-only evidence production. An owner who wants a task implemented by a subagent has no way to say so, and no way to say which model should run it.

The containment that would make such a delegation safe turned out to be already in place: a probe run this session proved the PreToolUse write guard fires for a subagent's tool calls and holds the Touch boundary identically. What is missing is not a mechanism. It is a declaration.

## What Changes

- A repository and a task can **declare that a task may be implemented by a subagent**, and **which model tier runs it**. The declaration lives in `keel/config.yaml` and the task capsule, not in conversation.
- The tier vocabulary is **abstract and target-resolved**. Keel names capability tiers, never a concrete model. A model identifier is target-specific — one named for Claude means nothing to Codex — and it expires on the next model release, leaving a declaration pointing at something retired. Keel stays as model-free as it has always been: it carries a tier, and the target adapter resolves it.
- The task capsule keeps whatever it authored and inherits the repository default only where it authored nothing, naming `keel/config.yaml` as the source of any inherited entry — the inheritance 5.5.0 established for `Autonomy boundary:`.
- **Keel builds no spawning mechanism, and no second brief carrier.** The write boundary and declared tier extend the `subagent-start` projection Keel already publishes. Spawning a subagent, restricting its tools, selecting its model, and isolating it are native host capabilities, and a Keel surface that duplicated them would be the failure the new scope requirement names.
- `keel-helper-brief/v1` is not weakened: its guarantee is before/after repository byte identity, and admitting mutation verbs would destroy the only thing it proves. A delegate is a different role than a helper, not a helper with the restriction removed.
- **Delegation requires an active write-guard manifest.** With `keel/guard.json` absent the guard passes everything through silently, so without this rule the chosen containment does not exist while looking identical on screen.
- `keel-touch-write-guard` gains the behavior it already has: the guard binds a delegated subagent's writes exactly as it binds the current agent's. The spec is currently silent on subagents, which is the same gap 5.3.9 closed for the repository boundary — a reviewer reading it could reasonably conclude either way.
- The subagent-start projection carries the write boundary and the declared runner alongside the context it already emits.
- Not breaking. A repository that declares nothing delegates nothing, and every surface behaves exactly as it does today.

## Capabilities

### New Capabilities
- `keel-authorized-delegation`: when a task may be implemented by a subagent rather than the current agent, what the projected brief carries, which runner executes it, what the return may and may not settle, and the conditions under which delegation is refused.

### Modified Capabilities
- `keel-task-capsule`: the capsule gains the delegation declaration and its repository-default inheritance; the compiled-defaults requirement currently states `read-only helper authority` unconditionally.
- `keel-touch-write-guard`: the guard's scope statement gains the delegated writer, and delegation is conditioned on an active manifest.
- `keel-native-runtime-projection`: the authorized-subagent brief carries the declared runner and an explicit write boundary, not only `Touch or read-only`.
- `keel-surface-evolution-policy`: gains the scope rule the file's existing procedures always served but never stated — a capability the target runtime provides natively is not Keel's to build, and Keel's scope over it is the policy it declares about its use.
- `keel-single-task-goal-execution`: the single-task goal flow admits a declared delegate, which restates its sole-writer invariant rather than removing it — the current agent remains the sole holder of *write authority*, and a delegate writes only inside the boundary that authority already defined.

## Impact

- **Code**: `src/core/config.js` (one declaration key, following `authorize:`/`triage:`), `src/core/task-contract.js` (capsule field and inheritance, mirroring the standing-authorization block), `src/core/projection.js` (brief fields), a new delegation-brief contract module beside `src/core/helper.js`, and `bin/keel.js` for the CLI surface and overlay text.
- **Untouched by design**: `src/core/helper.js`, the deterministic gates, and `plugins/keel/scripts/pretooluse-guard.js`. The probe is the evidence that the guard needs no change; a guard edit in this change would be unauthorized scope.
- **`keel-standing-authorization` is deliberately not extended.** Its four names — `commit`, `push`, `release`, `archive` — share a property delegation does not: each changes durable repository or outside-world state. Delegation only routes execution. Adding a fifth name would dilute a set the spec pins as closed into "anything that needs permission", so the declaration gets its own block.
- **In scope by owner decision**: the `keel-single-task-goal-*` adapters and `keel-run-single-task-goal`. They run under a 4,000-character activation budget, so the delegation fields must fit inside it or activation refuses — the budget is a real constraint on how much the brief may grow.
- **Risk**: delegation moves implementation to a runner whose output the current agent must still review. The mitigation is that nothing downstream is relaxed — the guard binds Touch, `task-complete` demands identical evidence, and Review and the checkbox stay with the current agent. A wrong runner choice costs a retry, not an unreviewed merge.
- **Dependencies**: none added.

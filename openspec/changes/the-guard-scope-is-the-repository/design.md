# Design

## Verified facts

- **F1** — `plugins/keel/scripts/pretooluse-guard.js` evaluates in this order: manifest missing (allow), non-file-edit tool (allow), **manifest invalid (deny)**, no target (allow), **target outside the repo (allow)**, record prefix (allow), authority drift (deny), task checked (deny), path in Touch (allow), otherwise deny. The invalid-manifest denial therefore precedes the out-of-repo passthrough.
- **F2** — Measured on 5.3.8 with one fixture, changing only the manifest: with a valid manifest an out-of-repo edit is allowed; with `keel/guard.json` corrupted the same edit is denied with "keel/guard.json is present but invalid, so file edits fail closed".
- **F3** — The out-of-repo decision is `path.relative(repo, path.resolve(repo, target))` over `event.cwd` and `event.tool_input`. It reads no manifest field.
- **F4** — The hook's header comment states the passthrough unconditionally. `openspec/specs/keel-touch-write-guard/spec.md` does not mention the repository boundary anywhere, and its first requirement says Keel MUST deny calls "whose resolved target path falls outside the manifest's normalized Touch list", which by itself covers a path outside the repository.
- **F5** — The same ordering defect one step lower was issue #28 item 10: the drift loop ran before the passthrough, so an out-of-repo write was denied on drift. Fixed 2026-07-27 in `touch-layering-and-repo-action` task 1.1 by moving the passthrough above the drift loop. Verified fixed on 5.3.8: under genuine drift, an in-Touch write is denied while an out-of-repo write passes.
- **F6** — The guard's hashed authority set is the change's own `tasks.md` plus each Covers `source`, and the hook skips every authority entry under `openspec/changes/<change>/`. A drift denial therefore requires a Covers entry resolving to a live `openspec/specs/**` file.

## Decisions

### D1 — The repository boundary is scope, not a rule among rules

Resolve the target and return for an out-of-repo path **before** reading the manifest at all, not merely before validating it. The guard's subject is the repository it was started in; a path outside it is not a product write, so no manifest state — absent, valid, corrupt, drifted, or completed — has anything to say about it.

Placing it before the read rather than between the read and the validation is the difference between an ordering that happens to be right and one that cannot be got wrong again. Every manifest-derived denial then sits structurally downstream of a boundary that needs no manifest, so a future branch added at the top of the manifest section inherits the correct behavior instead of reintroducing F5's defect a third time.

Rejected: keeping the invalid-manifest denial first and special-casing out-of-repo inside it. That preserves the shape that has now failed twice and leaves the next added branch to rediscover it.

### D2 — The spec states the boundary and its precedence

`keel-touch-write-guard` gains a requirement naming the repository as the guard's scope and stating that the boundary precedes every manifest-derived decision. F4 is the reason this is not merely a code fix: the behavior currently has no durable owner, so a reviewer reading the spec would conclude the opposite of what the code does, and reasonably "correct" the code toward denying.

The existing outside-Touch requirement is amended to say the Touch comparison applies to in-repository paths, so the two requirements cannot be read as contradicting one another.

### D3 — The assertion pins the precedence, not the passthrough

Validation asserts the out-of-repo write is allowed **while the manifest is corrupt**, and that in-repo paths are still denied in that same state. Asserting the passthrough alone under a valid manifest would pass today and would have passed before this change, so it would not cover the defect. Asserting both halves in the corrupt state is what distinguishes "the boundary takes precedence" from "the boundary exists somewhere in the function".

## Risks

- **R1** — A path outside the repository is now unreachable by every guard denial, including the completed-task and drift denials. That is the intent, and it is already true for the valid-manifest case (F2), so the change narrows the guard only in the corrupt-manifest state.
- **R2** — An agent could evade the guard by targeting a path that resolves outside the repository. Not a new exposure: the passthrough already exists for every other manifest state, and the guard's stated subject is the repository. A path outside the repository is outside the product the task is authorized against.
- **R3** — The `cwd` the hook receives determines the boundary, so a wrong `cwd` would move it. Unchanged by this work: every existing branch already trusts `event.cwd`, including the manifest lookup itself.

## Questions

- None.

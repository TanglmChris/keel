## Why

Issue #70 measured that "a gate never false-stops" has no ongoing check. The archive under `openspec/changes/archive/` is filtered by the very gates it would need to audit — it only ever holds what passed — so a false stop leaves no trace: the author is refused, assumes the refusal is correct (usually true), edits the contract into the shape the gate accepts, and the archived artifact is the edited version, indistinguishable from one that was never rejected. The only record of a false stop today is a human noticing and writing an issue (#49, #51, #65).

An unattended run has no one to notice. It edits toward whatever the gate accepts and reports success, and the resulting archive entry looks exactly like a correct one.

Three directions were measured on the issue: **甲** (compare rejected-and-resubmitted contract text mechanically), **乙** (make "I think the gate is wrong" a cheap recordable act), **丙** (keep the rejected shape at archive time). 丙 was chosen (2026-08-03) as the only one that needs no in-the-moment human judgment — 乙 depends on someone recognizing the gate was wrong, which is exactly the step unattended runs skip, and 甲 needs 丙's raw material to compare against.

丙's most direct form — the gate itself writing the rejected shape at the moment of refusal — was then measured against `keel-core-gates:231`, which is unconditional: "every failing or `needs-review` outcome MUST NOT write project state." A failing gate has no manifest to write into either; the one write a gate makes happens on the *passing* `task-start` that arms the guard. Replaying 丙 as a gate write across this repository's own 44 archived changes fires a warning 458 times — because tasks in this repository don't commit between each other, so "a path this task's Touch doesn't own was already dirty at task start" is the normal shape of 87% of non-first tasks, not the rare shape 丙 needs it to be. At least one of those 458 replays is already proven false — the change's own Review said so at the time.

The owner picked **R2** over **R3** (2026-08-05, [dasauto#18](https://github.com/TanglmChris/dasauto/issues/18)): the task author records what a gate rejected themselves, in a new `Reauthorizations` Evidence entry; the gate adds no write of its own and validates only the entry's shape. This keeps `keel-core-gates:231` intact — recording a rejection is the same trust boundary Review, Findings, and every other author-written Evidence entry already carry, not a new mechanism.

## What Changes

- A task's `Evidence` gains an optional `Reauthorizations` entry, sibling to `Blocker`. `Reauthorizations: none` is the default; when a gate rejects the task and the author revises and resubmits, the author records what was rejected and what changed as free text under the label.
- `task-complete` validates only the entry's shape: absent or `none` is fine, and any other content must be concrete — not empty, not `pending`, not carrying an unfilled `<slot>` token. The gate does not check whether a rejection actually happened, is not a hard stop the way `Blocker` is, and writes nothing itself.
- The entry reuses the same label-to-next-sibling extent `reviewValue()` already computes for the four Review entries (5.28.0, "a review field is what the author wrote"), so a `Reauthorizations` block spanning several lines is read whole rather than truncated at its first line — the exact defect that change fixed, not reintroduced one field over.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-core-gates`: task Evidence gains a `Reauthorizations` entry and its shape-only completion check.

## Impact

- `src/core/gates.js` — a new shape check in `completionChecks()`, reusing `reviewValue()`.
- `src/core/task-contract.js` — `unfilledToken` becomes an export so the new check can name the unfilled slot the way `missing-field` already does.
- `openspec/schemas/keel-spec-driven/templates/tasks.md` and its packaged copy under `assets/` — each Evidence example gains `- Reauthorizations: none` after `Blocker`.
- `scripts/validate_plugin.py` — a scenario driving the new check through `keel gate task-complete` on real repositories.
- No change to `field()`, `fieldValues()`, `parseTasks()`, `reviewValue()` itself, or any of the four existing Review entries.
- No change to what `task-start`, `Blocker`, or any existing Evidence field accepts. No new project write on any gate outcome — `keel-core-gates:231` is unchanged and unchallenged.

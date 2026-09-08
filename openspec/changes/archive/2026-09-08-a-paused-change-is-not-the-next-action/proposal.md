## Why

Issue #112 calls this its most valuable finding, and the distinction it draws is exact: the other items cost effort, this one gives wrong instructions.

A change in the reporter's project was deliberately stopped — external conditions were not ready — with its tasks left at 2.1 unchecked. From then on, `keel context` with no `--change` recommends it every session:

```
Keel context: ready
Next action: task-start
Selection: add-fmax-and-scoring#2.1 (inferred)
```

That recommendation is wrong, and Keel has nowhere to say so. The reporter's workaround is a paragraph in the project's `CLAUDE.md` telling future sessions to ignore it — which is the failure stated plainly: **the tool's primary output needs a document to cancel it.**

Keel already has the shape. `storageOnly` marks a change that inference must skip, and inference reports what it skipped rather than hiding it. What is missing is a way for a person to say the same thing about a change that *is* actionable and is deliberately not being acted on.

## What Changes

- A change may declare itself paused in its own `.openspec.yaml`, under a `keel:` key.
- `keel context` skips a paused change during inference and names it, with its reason, rather than passing over it silently.
- When every active change is paused, `context` reports `idle` and lists each one with its reason — the state is "nothing to do here, and here is why", not "nothing exists".
- `keel context --change <paused>` still selects it. A declaration that could not be overridden would be a second thing to work around.
- Nothing else reads the declaration. The gates, the guard, and completion are untouched: pausing is about what to recommend, never about what is allowed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-stateless-continuity`: inference skips a change its owner declared paused, and says so.

## Impact

- `src/core/context.js` — the change-config reader and the inference filter.
- `scripts/validate_plugin.py` — one new scenario.
- The declaration lives under a `keel:` key rather than at the top level of `.openspec.yaml` as the report suggested. `.openspec.yaml` is OpenSpec's file; a bare `status:` would be a claim on a key OpenSpec may define differently, and the namespace costs one line. Extra keys were verified not to disturb `openspec validate`.
- Risk: a paused change is forgotten. Mitigated by never letting it be silent — inference names every paused change it skipped, and an all-paused repository reports each reason rather than reporting nothing.

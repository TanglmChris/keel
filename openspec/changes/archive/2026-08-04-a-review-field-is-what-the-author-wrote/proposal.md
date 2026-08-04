## Why

A task's Review lives inside `Evidence` as four labelled entries — `Status`, `Acceptance check`, `Scope check`, `Findings`. `reviewValue()` in `src/core/gates.js` reads each one with a single line-anchored match:

```js
field(task, "Evidence").match(new RegExp(`^\\s*-\\s*${label}:\\s*(.*)$`, "im"))
```

`(.*)` with the `m` flag stops at the newline. So a Review field is not the entry the author wrote — it is the entry's **first line**, and every continuation line under it is discarded before any check sees it.

`Findings` is the entry this hurts, because it is the one that runs long. A finding recorded across four indented lines with `Durable owner:` on the last of them is refused:

```
Problem: Review Findings must be `none` or carry a disposition. … Name a path
after `Durable owner:` so it reads as the owner rather than a file the finding
mentions.
```

The owner is present, the path exists, and the form is correct. Only the line is wrong. Joining the identical text onto one line makes the same command pass with no change to a single word of it.

The diagnostic then sends the author the wrong way. Its closing sentence — *"so it reads as the owner rather than a file the finding mentions"* — describes a **notation** mistake, and reads as an accusation that the path was written in passing. Faced with it, an author checks the wording, because the message is about wording. The cause is that lines two through four were never read. #49 reports exactly this sequence, and reports the author landing in it twice in one session.

The gate is judging text it did not read. That is worse than judging it wrongly: `Findings: none` followed by three lines of real findings passes today, because the check sees only `none`. The narrow reading fails open in one direction and closed in the other.

The repository decided the general form of this question one version ago. 5.26.0 shipped under "a section is what the author wrote": a change-level section's extent had been cut short by a bound that was right for a different document shape, and the fix made the extent the text the author actually wrote. `parseTasks()` already gathers a field's full body, continuation lines included — `field()` returns all of them joined. `reviewValue()` is the reader that was never brought along, holding the same defect one level down.

## What Changes

- A Review entry's value is the text the author wrote under its label: its first line plus every continuation line, up to the next sibling entry.
- The entry ends at the next `- Label:` line at the same or shallower indentation, so `Findings` cannot reach into `- Blocker:` or out of `Evidence`.
- Nothing about *what* is accepted moves. The disposition markers, the owner forms, the `Status` vocabulary, the concreteness rule, and every diagnostic code and message are untouched. What changes is how much of the author's text each check is given.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-core-gates`: the extent of a Review entry inside task Evidence — the same boundary question 5.26.0 answered for a change-level section, one level further in.

## Impact

- `src/core/gates.js` — `reviewValue()` gains the sibling-entry bound; no caller changes.
- `scripts/validate_plugin.py` — a scenario driving a wrapped Review entry through `task-complete` in both directions.
- `keel gate task-complete` verdicts, for a task whose Review entry wraps. A wrapped `Findings` carrying its owner below the first line now passes; a `Findings: none` with findings written under it now fails, which is the same rule applied to text that was previously invisible. A wrapped `Status: pass` is likewise judged on its whole text and refused as outside the accepted vocabulary — the one place the wider read newly refuses rather than newly accepts. See D8.
- Measured against this repository's own history: of 640 Review entries across every change under `openspec/changes`, **zero** wrap. No archived verdict moves.
- No change to `field()`, `fieldValues()`, `parseTasks()`, or any non-Review field. `Verify`'s own line-wise entry splitting (#49's second supplement) is a separate mechanism and is not touched here.

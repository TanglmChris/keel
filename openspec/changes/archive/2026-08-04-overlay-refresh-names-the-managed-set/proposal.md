## Why

`refreshOpenSpecSurfaceOverlay` ends with a summary line whose action list is the literal string `apply/archive`. The set it actually covers is apply, archive, and sync. Two commands run back to back in one repository at 5.24.0 describe the same surface list differently:

```
$ keel --init
keel: OpenSpec apply/archive overlay refreshed=8 current=0 missing=0

$ keel --uninstall
keel: OpenSpec apply/archive/sync overlay removed=8 absent=0 missing=0
```

The second line is derived from the managed set through `overlayActionLabel()`. The first is not.

`overlayActionLabel()` was introduced for exactly this defect, and its own comment says so: the label *"was the literal string `apply/archive`, which was correct while those were the managed actions and became wrong — silently — the moment a third joined them."* When it was introduced, `--doctor` was converted to call it and this line was missed. A fix for a drifting literal left a second copy of the same literal behind, and the copy left behind is the one with no assertion watching it: the doctor line carries four, this line carries none.

That asymmetry is the durable part of the defect. `sync` joined the managed set in 5.22.0 and did not appear here. The next action to join will not appear here either, and nothing will turn red when it doesn't.

Found during the implementation of #50 (`uninstall-leaves-nothing-behind`, task 1.1): the newly written removal summary used `overlayActionLabel()`, and only the contrast with the refresh line beside it made the difference visible. It was recorded there as a finding with this issue as its durable owner rather than folded in, because folding it in would have made that change's acceptance two things.

## What Changes

- The refresh summary line derives its action label from the managed set instead of stating it, so it reports the same actions as the removal and doctor lines that already do.
- The line gains an assertion, so the next time the managed set changes the omission is a failing check rather than something a reader notices.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-openspec-surface-overlay`: the overlay summary output must name the managed action set it derives from, in every direction that reports one.

## Impact

- `bin/keel.js` — one line inside `refreshOpenSpecSurfaceOverlay`.
- `scripts/validate_plugin.py` — assertions added to the `openspec-surface-overlay` scenario.
- Output text of `keel --init`, `keel --install`, and `keel --check`. Nothing parses this line: the only other reader in the suite matches the per-surface dry-run line (`would refresh OpenSpec … in …`), not this summary, and `uninstall-removes-the-overlay` asserts the removal line's counts rather than its label. So no existing check is pinned to the wrong literal in either direction.
- No change to which surfaces are overlaid, to the counts reported, or to `overlayActionLabel()` itself, including its deliberate exclusion of `propose`.

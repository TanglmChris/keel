## Why

Issue #416. On 2026-10-20 the owner said "感觉啥都会进 mem". On 2026-10-21 the owner decided that memory hygiene goes into the Keel protocol, for every repository that uses Keel, as an explicit exception to the #414 stance that Keel leaves native capabilities alone. The exception governs what memory holds, not whether memory is used. A `keel memory audit` tool was not chosen.

Today the only memory rules are the host's system prompt and this repository's own Project Conventions in `AGENTS.md`, which sit outside the managed block. A consuming repository such as kaiwu-ip or chip_sec_flow_v2 carries only the Keel bootstrap block (10 lines). That block says memory "may only inform", and says nothing about what may be written or when it is checked. Nothing in a shift change looks at memory.

Measured in this repository's memory on 2026-10-20: 17 entries, about 36 KB. The two largest are compilations of about 4.9 KB each that keep growing, and one entry recorded a session's own scripting slip.

## What Changes

- **The bootstrap block carries the memory rule.** It gets one bullet saying three things:
  - memory holds only what the next session would get wrong without it and the repository cannot answer, never a one-off slip;
  - each entry holds one fact;
  - memory is rechecked after a fix, at a release, and at a shift change.

  This needs bytes: the block is at 1395 of its 1400-byte budget. The budget is raised, with the reason recorded beside the constant, as the routing rule's raise was (#131).
- **This repository's full protocol gains a `## memory` section** that states the same rule in full.
- **`keel shift check` prints a memory note.** It reminds the session to recheck what it wrote to memory before the hand-off note. As a note, it does not block readiness.
- **`/keel:shift` tells the session to act on that note.**
- **Keel still does not read or write the host's memory.**

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-stateless-continuity`
- `keel-shift-change`

## Impact

The change touches:
- `assets/bootstrap/AGENTS.md` and `scripts/validation/common.py` (the budget and a required topic);
- `AGENTS.md` (the full protocol);
- `src/core/shift.js`;
- `plugins/keel/commands/shift.md`;
- `docs/shift-change.md`;
- the shift validation module and the registry;
- the published specs and the changelog.

Consuming repositories receive the new bootstrap when they refresh their managed block. `keel context` already names that refresh.

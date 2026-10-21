## Context

`keel --install` and `keel --init` write `assets/bootstrap/AGENTS.md` into a repository as the managed block. `scripts/validation/common.py` holds `RESIDENT_BLOCKS`, which bounds that block at 12 lines and lists its required literals and topics. The block's byte budget is `BOOTSTRAP_BLOCK_BYTE_BUDGET`, 1400. Its comment says the budget is raised only "deliberately and in a diff", with the reason, which is how the 5.63.0 raise for routing was made (#131).

`keel shift check` returns `items`, which block readiness, and `notes`, which do not. `/keel:shift` has the session deal with each item.

## Decisions

- **D1** — One bullet in the bootstrap. The text:

  `- Memory: write only what the next session would get wrong without it and the repository cannot answer, never a one-off slip; one fact per entry. Recheck it after a fix, at a release, and at a shift change.`

  It sits right after the bullet that says memory may only inform. That bullet says how memory is read; this one says what it may hold.
- **D2** — The budget rises from 1400 to 1700, with the reason kept beside the constant. Memory is like routing: never inert. Any session may write to memory whether or not a project declares anything, and the bootstrap is the only text that reaches a consuming repository. The owner chose the protocol layer (#416, 2026-10-21). The headroom stays "current content plus one short clause".
- **D3** — A required topic. `RESIDENT_BLOCKS` gains a pattern requiring memory, the repository-cannot-answer test, and a recheck at a shift change in the bootstrap block. The pattern matches the topic, not exact prose, so the sentence can be reworded under byte pressure.
- **D4** — The full protocol. This repository's `AGENTS.md` managed block gains a `## memory` section with the same rule:
  - the admission test;
  - one fact per entry, split a growing compilation;
  - stamp a behavioural claim with its version and issue;
  - recheck after a fix (grep by the symptom's wording), at a release, and at a shift change.

  The Project Conventions bullets that already say this stay as this repository's history and examples. They do not contradict the protocol, and their dated incidents are not protocol text.
- **D5** — `keel shift check` adds a note, not an item. The note: `memory: before the hand-off note, recheck what this session wrote to memory — keep only what the next session would get wrong without it and the repository cannot answer, and remove what this shift made untrue`. It appears in text and in `--json` `notes`, and does not change `ready`. Keel still reads no memory file, so it cannot know whether there is anything to recheck, and a blocking item would hold every shift on something Keel cannot see.
- **D6** — `/keel:shift` step 1 says to act on that note before writing the hand-off note. `docs/shift-change.md` mentions it in the check row.
- **D7** — Evidence. A scenario `memory-rule-reaches-every-repo` checks the following:
  - `keel --install` into an empty repository writes a bootstrap block that carries the memory rule and stays within the budget;
  - `keel shift check` on a clean bound worktree exits 0 with `ready`, and prints the memory note in both text and `--json` `notes`;
  - the `/keel:shift` command text names the note.

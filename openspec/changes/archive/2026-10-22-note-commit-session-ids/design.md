## Facts

- F1 — `NOTE_SHA` in `src/core/shift.js` is `/(?<![\w@/-])([0-9a-f]{7,40})\b/g`, gated by `looksLikeSha`, which requires a letter and a digit. Its lookbehind already skips the later segments of a UUID, but the first segment (8 hex digits followed by `-`) matches.
- F2 — `ready` writes `CLI session: <uuid>.` into every CLI note's header (`cliSession`). Notes also quote session ids in prose. In the 10-20T1317 note, `b4d145a2` and `61d93a31` have `sessions/<id>.json` records, while `d6bedfc8` and `429de332` had been removed by then. `3c77015` is a real commit.
- F3 — Keel keeps session records at `<chat root>/sessions/<id>.json` (and `<id>.language.json`), and kept shift transcripts at `<chat root>/shift/transcripts/<role>/<id>.jsonl.gz`.
- F4 — The header is built from an array in which an empty slot is `""`, and the array is joined with `\n`, so each empty slot becomes a blank line.

## Decisions

- D1 — A bare token followed by `-` and four hex digits is the first segment of a UUID and is not a commit. A `<branch> @ <sha>` pair is unaffected.
- D2 — A bare token that begins a session id from F3 is not a commit. A removed session that Keel no longer records is still read, so the check stays exact rather than heuristic. Its `not found` is a true statement about a token Keel cannot place.
- D3 — The header keeps its title line, the blank line after it, and the blank line before the note text. Empty slots are dropped. The readers that match `^Desktop session:` and `^CLI session:` line by line are unaffected.

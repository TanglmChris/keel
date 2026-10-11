## Context

Issue #261.

## Facts

- F1 — `readNoteText` in `src/core/shift.js` passes `options.file` straight to `fs.readFileSync`, so `-` is opened as a file named `-`, and any read error escapes `main`, which catches only `ShiftError` and `ChatError`.
- F2 — Without `--file`, `ready` already reads stdin when it is not a TTY.

## Decisions

- D1 — `--file -` reads file descriptor 0, as stdin without `--file` does (F2).
- D2 — Any other read failure of `--file` becomes a `ShiftError` naming the path and the system's reason, which `main` prints as `keel shift: …` and exits 1 (F1).

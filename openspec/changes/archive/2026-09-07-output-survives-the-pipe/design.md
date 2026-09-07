## Context

Everything Keel exposes to a program goes through `stdout`: `--json` on `context`, `gate`, `project`, `capabilities`, and `triage`, plus the human-readable surfaces. The CLI has always had one exit path, and that path has always discarded unflushed output.

## Goals / Non-Goals

**Goals:**

- What Keel writes for a program to read arrives whole.
- The regression is provable on demand rather than by waiting for a loaded machine.

**Non-Goals:**

- Changing any payload, schema, or exit code.
- Auditing `fail()`, which also calls `process.exit` — see A1.
- Making output smaller. A capsule is as large as its task.

## Decisions

- F1 — `bin/keel.js:2237` is `process.exit(main());`. Basis: read in the working tree, 2026-09-07.
- F2 — Through a pipe shrunk to 4096 bytes, with the reader starting after the child exits, `keel project goal --json` delivers 4096 bytes; the same invocation redirected to a file delivers 11,849. Replacing the exit call makes the piped result 11,849. Two runs each, identical. Basis: measured 2026-09-07 with `fcntl(F_SETPIPE_SZ)`.
- F3 — At the default 64KB buffer the same command is never truncated: 18 consecutive runs, including 12 in parallel, all returned 11,849. The defect is invisible until the buffer shrinks. Basis: same session.
- F4 — The first sighting was 8,192 bytes — two pages — during a parallel `npm test`. Linux reduces pipe buffers under memory pressure, so the condition that triggers this is load. Basis: observed, then explained by F2's controlled reproduction.
- F5 — `plugins/keel/scripts/session-start.js:301` runs `keel context --json` and line 308 calls `JSON.parse(result.stdout)`; a throw there routes to `fallback()`. Basis: read in the working tree.
- F6 — Real payloads exceed the pressure threshold: a real task capsule from this repository compiles to 18,364 bytes of `gate task-start --json`, and the goal projection to 11,849. Basis: measured against `openspec/changes/archive/2026-09-07-a-path-is-what-the-value-declares` restaged as a live change.
- D1 — Replace `process.exit(main())` with `process.exitCode = main()`. Basis: it removes the race by construction rather than narrowing it — there is no payload size at which the fixed form truncates, because the process ends when the event loop is empty and a pending write keeps it alive. Waiting on a drain callback would be the same guarantee with more code and one more thing to get wrong.
- D2 — The scenario forces the condition rather than waiting for it: a 4096-byte pipe and a reader that starts after the child exits. Basis: F3 — a test that runs the command and checks the length passes on an idle machine whether or not the defect is present, so it would be a green with no red behind it. Shrinking the buffer makes the red honest and the green meaningful.
- D3 — Exit codes are asserted, not assumed. Basis: `process.exitCode` is the one behavioral difference a reader would worry about; 0, 1, and 2 are each produced by a real command in the scenario.

## Hidden Knowledge / Assumptions

- A1 — `fail()` at `bin/keel.js:166` also calls `process.exit`, after writing to stderr. It is not changed here. Basis: it is reached only for usage errors, before any command has produced output, and its messages are two short lines that fit any pipe buffer — so the same race exists in principle and cannot lose anything in practice. Recorded rather than fixed so that the claim is checkable if a future caller writes something large through it. Durable owner: https://github.com/TanglmChris/keel/issues/119
- A2 — Nothing keeps Keel's event loop alive after `main()` returns. Basis: subprocesses run through `spawnSync`, and the CLI opens no server, timer, or watcher. Verified by the scenario asserting the process terminates and returns its code; if that assumption ever breaks, the scenario hangs rather than passing quietly.

## Risks / Trade-offs

- A future feature that leaves a handle open would hang the CLI instead of exiting. That is a louder failure than silent truncation, and A2's assertion is where it surfaces.
- The scenario uses `fcntl(F_SETPIPE_SZ)`, which is Linux-specific. It skips with the suite's documented skip contract elsewhere rather than failing, so a non-Linux runner reports the gap instead of a false green.

## Open Questions

None.

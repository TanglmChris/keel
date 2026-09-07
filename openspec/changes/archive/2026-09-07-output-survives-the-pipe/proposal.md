## Why

`bin/keel.js` ends with `process.exit(main())`. Node's `process.stdout` is asynchronous when it is a pipe, and `process.exit()` discards whatever has not been flushed. Whether that loses anything depends on one thing: whether the payload fits the pipe buffer. Under 64KB it does, so day to day nothing is wrong. Under memory pressure Linux shrinks pipe buffers to a page or two — and that is exactly when this fires.

Measured, deterministically, by shrinking the pipe to 4096 bytes and reading it only after the child exits: `keel project goal --target codex --json` delivers **4096 bytes through the pipe and 11,849 to a file**, from the same invocation. With `process.exitCode = main()` in place of `process.exit(main())`, the same setup delivers 11,849 through the pipe.

The failure mode is the worst kind. There is no error, no exit-code change, and no diagnostic — the consumer receives a valid prefix of an incomplete document. `plugins/keel/scripts/session-start.js` runs `keel context --json` and calls `JSON.parse` on the result; a parse failure there routes to `fallback()`, so a user sees a degraded projection and never learns why. Any CI step piping `keel gate ... --json` into `jq` has the same exposure. Real payloads clear the pressure threshold easily: a real task capsule from this repository is 18,364 bytes.

It also cost a real misattribution. The suite scenario `native-goal-projection` parses this output, and it failed intermittently during a parallel `npm test` — 150 concurrent node processes being precisely the memory pressure that shrinks the buffers. It read as a regression from an unrelated change under way at the time.

## What Changes

- `bin/keel.js` sets `process.exitCode` instead of calling `process.exit()` at the top level, so Node drains stdout before the process ends.
- A new `output-survives-the-pipe` scenario reproduces the truncation deterministically — a 4096-byte pipe and a reader that starts after the child exits — and asserts the whole document arrives.
- Exit codes are unchanged: a failing gate still returns 1, an invalid argument still returns 2.

## Capabilities

### New Capabilities

- `keel-cli-output-contract`: what Keel guarantees about the output it writes for a program to read — that it arrives complete, or that the failure is visible.

### Modified Capabilities

None.

## Impact

- `bin/keel.js` — one statement.
- `scripts/validate_plugin.py` — one new scenario.
- Consumers gain nothing to change: the same bytes arrive, and more of them.
- Risk: setting `exitCode` rather than exiting means a lingering handle would hold the process open where it previously died. Keel runs its subprocesses with `spawnSync` and opens no server, timer, or watcher; the scenario asserts the CLI still terminates and still returns 0, 1, and 2.

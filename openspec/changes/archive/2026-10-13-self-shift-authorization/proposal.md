## Why

Issue #319, second probe round on 5.129.0 (2026-10-13, comment 6146019116). After the clear, the chain ran unattended. Before it, the probe asked the owner once, because turning Remote Control off, creating the wake task, renaming itself, and clearing are outside `shift-restore`. Owner decision, 2026-10-13: add a standing authorization for those steps, so a session can change its own shift at a task boundary without asking.

## What Changes

- New standing-authorization name `self-shift`, with no scope. It covers exactly the four steps `keel shift ready --wake` prints on the desktop app, after `ready` stored the note. It does not cover the decision to change shift.
- On the desktop app, `ready --wake` says the four steps are standing-authorized when `self-shift` is declared, and otherwise names it.
- This repository declares `self-shift`. The README vocabulary, the `keel/config.yaml` comment, and both shift-change docs follow.

## Capabilities

### Modified Capabilities
- `keel-shift-change`: the desktop `ready --wake` output reads `self-shift`.
- `keel-standing-authorization`: the `self-shift` name.

## Impact

`src/core/config.js`, `src/core/shift.js`, `keel/config.yaml`, `README.md`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `scripts/validate_plugin.py`, both published specs, and the changelog.

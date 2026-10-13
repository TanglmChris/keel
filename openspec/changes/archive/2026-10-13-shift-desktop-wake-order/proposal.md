## Why

Issue #319, the follow-up tests of 2026-10-13 (comments 6143435530 and 6144856601).

- In the maintenance session, turning Remote Control off blocked for 13 min, 1 h 40 min and 3 h 36 min. The wake task, created before that call, fired during the wait, and the app then refused the clear to keep the queued wake.
- 5.128.0 printed the wrong reason for this: approval of `clear_session`.
- A fresh probe session ran the steps in the opposite order: Remote Control off, then the task, then the clear. That order worked: the clear was accepted and the wake started the new conversation. But the woken model treated "turn Remote Control back on" as another session's instruction, and stopped for 11 minutes to ask the owner.
- The owner also asked that the outgoing session be renamed before the clear, so its archived copy can be told apart.

Owner decisions, 2026-10-13: fix the order, rename before the clear, and add a repository standing authorization that lets the woken session restore itself.

## What Changes

- On the desktop app, the `ready --wake` recipe gives four ordered steps:
  1. Turn Remote Control off and wait for it to return.
  2. Only then create the one-shot task, because a task created earlier can fire first.
  3. Rename the outgoing session with `set_session_title`.
  4. Clear.
- The recipe names the `permissions.allow` entry for `set_remote_control` and the new `authorize:` entry `shift-restore`. It drops the `clear_session` approval reason.
- New standing-authorization name `shift-restore`, with no scope. It covers, right after `keel shift resume` on the desktop app, turning that session's Remote Control back on and renaming it back.
- `keel shift resume` on the desktop app tells the woken session to restore Remote Control and the title. When `shift-restore` is declared, it says the repository standing-authorizes both. Otherwise it names `shift-restore` as the declaration that would.
- This repository declares `shift-restore`.
- The docs, the README vocabulary, and the `keel/config.yaml` comment follow.

## Capabilities

### Modified Capabilities
- `keel-shift-change`: the desktop recipe's order, the rename step, and the restore step under `shift-restore`.
- `keel-standing-authorization`: the `shift-restore` name.

## Impact

`src/core/shift.js`, `src/core/config.js`, `keel/config.yaml`, `README.md`, `docs/shift-change.md`, `docs/shift-change.zh-CN.md`, `scripts/validate_plugin.py`, both published specs, and the changelog.

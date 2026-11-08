## Why

Issue #505, filed 2026-11-08 at the owner's request ("加一个类似 feedback 的 slash 功能，这样大家给你提 issue 更简单"). A session in another project that meets a Keel problem has to find the version, assemble a reproduction, find the repository and compose a `gh issue create` by hand, and each session writes it differently; some problems stay in a chat record and are never filed. The owner chose `/keel:feedback` for the command and a `keel feedback` CLI beside it, on 2026-11-08.

## What Changes

- **`keel feedback "<one sentence>"`** drafts a fixed-structure issue for `TanglmChris/keel`: title, 现象, 期望, 复现, 证据, 影响 and 环境 (Keel version, Node, platform, host, the `keel context` status line). The command that failed and its output come from `--command` and `--output-file`; `--expected`, `--repro` and `--impact` fill the other sections. By default it creates nothing.
- **Everything shown is redacted first:** tokens, keys, Slack IDs, e-mail addresses and credentials in URLs are replaced, the home directory prints as `~` and the project root as `<project>`; the draft names how many values were redacted and never the values. No project name, remote, role or chat text is collected.
- **It searches `TanglmChris/keel` for near-duplicates** with `gh` and lists them before anything is created. Supplementing an existing issue is the user's own `gh issue comment`; Keel prints the command and never runs it.
- **`--create`** runs `gh issue create` with no label, assignee or `triage:` entry. It is refused (exit 3) unless the project's `authorize:` declares `issue:TanglmChris/keel`, or the caller passes `--confirmed` to say the user has approved this draft.
- **No usable `gh` loses nothing:** the draft is printed and saved to a file, the commands to run are printed, `--create` exits 4, and the duplicate search says it was not run.
- **`/keel:feedback`** (`plugins/keel/commands/feedback.md`) orders the steps for a Claude Code session: run the draft, show it, ask new issue / supplement yourself / cancel, create only on the answer. Codex and OpenCode have no command surface, so they run the CLI.

## Capabilities

### New Capabilities
- `keel-feedback`

### Modified Capabilities
- none

## Impact

`src/core/feedback.js` (new), `bin/keel.js`, `plugins/keel/commands/feedback.md` (new), `scripts/validation/feedback.py` (new) and `registry.py`, `README.md`, `README.zh-CN.md`, `docs/commands.md`, `docs/commands.zh-CN.md`, the published specs, and the changelog.

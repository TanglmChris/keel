## Why

Issue #500, filed 2026-11-03 and approved by the owner the same day ("你做吧") after the owner stated the expectation: apart from a model specified on purpose, a shift change must not change the default model. A shift bug fix, within the 2026-10-14 freeze.

A CLI hand-over starts the new session with `claude --bg -n <name> --permission-mode <mode> <prompt>` and names no model. Claude Code then resolves one itself and records it as `--model` in the session's `respawnFlags`. Measured 2026-11-03: keel-maint's previous shift ran `claude-opus-5-5` (Claude Code 2.1.312) and every one of keel-maint's eight earlier sessions did too, yet the session the hand-over started on 2026-11-01 (2.1.316) ran `claude-sonnet-5-5`, as did the chipstride, yizhan and kaiwu-flow shifts, while the owner's `~/.claude/settings.json` says `model: opus`. Whatever Claude Code's reason, the owner's default is silently replaced and Keel cannot see it.

## What Changes

- **A hand-over names the model it starts the new session on.** With no declaration, Keel resolves the owner's current default the way Claude Code orders its own sources (the `ANTHROPIC_MODEL` environment variable, then the worktree's `.claude/settings.local.json`, the worktree's `.claude/settings.json`, and the user's `settings.json` in the Claude config directory) and passes it as `--model`, after `--permission-mode` and before the prompt. When no source names a model it passes none, as today.
- **`shift: model:` and `shift: effort:` in `keel/config.yaml`** are the explicit way to start a role's shifts on something else. A declared value wins over every source above. `effort` is one of `low`, `medium`, `high`, `xhigh`, `max`; a value Keel cannot read is named and ignored. `--effort` is passed only when declared, so Claude's own per-model effort setting still applies.
- **The delivered hand-off records what it passed** (`model`, and where it came from), and `keel shift status` shows it, so a model that differs from the owner's is visible instead of inferred from a job file.
- Not changed: a resumed session (`--bg --resume`) keeps the options it was saved with; the desktop path; `--permission-mode`.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-shift-change`

## Impact

`src/core/config.js`, `src/core/shift.js`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, `scripts/validation/common.py`, `keel/config.yaml`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md`, the published spec, and the changelog.

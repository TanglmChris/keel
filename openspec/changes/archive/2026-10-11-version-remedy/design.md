## Context

Issue #240.

## Facts

- F1 — `versionReport` in `plugins/keel/scripts/session-start.js` names `plugin.remedy` (`claude plugin update`, or the host's own update command on Codex) whatever disagrees, unless the host already installed an update.
- F2 — `keel context` names the protocol refresh as `keel --install --target <target>`, choosing the target by `installedTarget` in `src/core/context.js`: `claude` when `CLAUDE.md` carries the managed marker, `opencode` when `.opencode/commands` exists, otherwise `codex`.

## Decisions

- D1 — Versions are ordered numerically as `X.Y.Z`. The newest discovered version among plugin, CLI, and protocol is the reference. The plugin update is named only when the plugin or CLI is older than it, and the protocol refresh only when the protocol is. A protocol newer than the plugin keeps today's remedy, the plugin update.
- D2 — The hook names the refresh with the same target rule as `keel context` (F2), so both surfaces print the same command.

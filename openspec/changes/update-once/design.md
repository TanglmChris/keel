## Context

Issue #204, with two probe comments recorded on 2026-10-03. Relevant existing behavior:
- `keel --update` packs `@christang/keel` and runs `npm install -g` (`runGlobalUpdate` in `bin/keel.js`).
- The Claude plugin tree is the whole tagged repository, so its hooks run that tree's own `bin/keel.js` (`packagedCli()` in `session-start.js`).
- `session-start.js` already reads `installed_plugins.json` four levels above the package root (`pendingInstall`, #172).
- The guard reads `keel/guard.json` and never spawns the CLI.
- `keel context` prints a `Protocol:` line for a stale managed block, and `protocol-refresh` lets a session run the refresh.

## Goals / Non-Goals

**Goals:**
- One owner-run command updates the CLI and both plugins and reports what took effect.
- Running sessions on both hosts run the new hook logic at their next hook call, without anyone typing an update command in each session.
- A task in progress keeps the write guard it started under.
- A successful, compatible update says nothing more.

**Non-Goals:**
- Other machines.
- Updating project files from the global command.
- Reloading Claude skills or agents in a running session. Only the host can do that; Keel names `/reload-plugins`.
- Any network access, installation, or scheduling from a hook.

## Decisions

- **F1** — Codex CLI 0.159.3 resolves `${PLUGIN_ROOT}` per hook call. In one long-lived `codex app-server`, a thread's turn after `codex plugin add` of 2.0.0 ran the 2.0.0 hook from the new directory. 1.0.0's directory had been deleted, and both hooks stayed `trusted` because their definitions were unchanged. Basis: the isolated probe on #204 (comment 5968295276).
- **F2** — Claude binds `${CLAUDE_PLUGIN_ROOT}` to the version directory loaded at session start. It keeps old directories (5.39.0 onward are present on the owner's machine), and `/clear` re-runs the loaded hook (#172). `~/.claude/plugins/installed_plugins.json` records the current `installPath` per plugin id. Basis: #172 and the #204 probe comment 5968204226.
- **F3** — Host commands. Claude: `claude plugin marketplace update <market>` then `claude plugin update keel@<market>`. Codex: `codex plugin marketplace upgrade <market>` (Git marketplaces only) then `codex plugin add keel@<market>`, which deletes the old cache directory. Both hosts report installed plugins through `plugin list --json`. Claude reports `id`, `version`, and `installPath`. Codex reports `pluginId`, `version`, `installed`, and `marketplaceSource.sourceType`. Basis: `--help` and `--json` output on 2026-10-03.
- **F4** — `keel --install --target claude` refreshed only Claude's overlays. In TanglmChris/rtl_ppa_prj the Codex `.agents/skills` overlays stayed at 5.84.0, while doctor reported `Codex … overlay: ok - 4/4`, because doctor checks only that the marker is present. Basis: the 2026-10-03 refresh of that repository (commit c967766 there).
- **D1** — `keel --update` runs these components in order: the CLI (unchanged), then the Claude plugin, then the Codex plugin. Each plugin component does the following:
  - It runs only when the host executable resolves and `plugin list --json` shows `keel@<market>` installed. Otherwise it reports `absent`.
  - The executable is `claude` or `codex`, overridable for tests by `KEEL_UPDATE_CLAUDE` and `KEEL_UPDATE_CODEX`.
  - It runs the F3 commands and reads the version again afterwards.
  - It reports one line: `keel update: <component>: <updated A -> B | current B | absent | manual | failed> - <detail>`.

  Details:
  - **Takes effect.** The detail states when the update applies: the CLI at the next command; the Claude plugin at a running session's next hook call (with skills and agents after `/reload-plugins`); the Codex plugin at a running session's next hook call.
  - **Local Codex marketplace.** A Codex marketplace whose `sourceType` is not `git` is reported `manual`, naming its source path and `codex plugin marketplace add TanglmChris/keel --ref main`. It is never re-pointed.
  - **Changed Codex hooks.** When Codex's `hooks/codex.json` differs between the old and the new install, read before `plugin add`, the line says Codex will ask for review in `/hooks`.
  - **Exit status and dry run.** The exit status is nonzero only when a step that ran failed. `--dry-run` prints each planned host command and runs none.

  Basis: the owner chose one owner-run command.
- **D2** — Hand-off. A shared `plugins/keel/scripts/forward.js` exports `forward(scriptRelativePath)`. Each Claude hook script calls it first.

  The hand-off happens only when all of these hold:
  - `KEEL_HOOK_FORWARDED` is unset.
  - The install record beside the package (the #172 path) names this plugin id with an `installPath` other than the running package root.
  - That path exists, and its `.claude-plugin/plugin.json` version is greater than the running one, with the same major version.
  - That tree contains the same relative script.

  When they do, the loaded script spawns `node <new script>` with the same arguments, the same stdin bytes, and the environment plus `KEEL_HOOK_FORWARDED=<running version>` and `CLAUDE_PLUGIN_ROOT=<new root>`. It relays stdout, stderr, and the exit status, and returns `true`.

  In every other case, including a spawn error or a timeout below the hook's own budget, it returns `false` and the loaded script continues with its own logic. Codex needs no hand-off (F1), so `forward` returns `false` when the package is not under a Claude plugin cache.

  Basis: the owner chose automatic adoption, and F2 is why Claude needs it.
- **D3** — The guard hands off only when the repository it resolves has no `keel/guard.json`. While a manifest exists, the loaded guard enforces it, and the first call after the manifest is cleared hands off.

  Codex switches hook logic itself at the next call (F1), so the guarantee there rests on the manifest:
  - The guard's decision is a function of a `keel-write-guard/v1` manifest.
  - A guard that does not know a manifest's schema fails closed, as it does today.

  Basis: the owner chose to defer during an active task.
- **D4** — A handed-off SessionStart reports as the version it runs. When `KEEL_HOOK_FORWARDED` names a loaded version, the projection compares the loaded tree with the new one on three things: the content of `plugins/keel/skills/`, the content of `plugins/keel/agents/`, and the `hooks` block of `.claude-plugin/plugin.json`.
  - Equal: it adds nothing.
  - Different: it adds one line on both channels. The line says hooks now run the new version, names what differs, and names `/reload-plugins` as the only remaining step.

  The existing drift report keeps its rules, with "the executing plugin" meaning the version that ran. Basis: #204's acceptance 7.
- **D5** — `keel --install` and `keel --init`, for any `--target`, refresh overlays on the surfaces of every repository-installed target, using the discovery doctor already uses. They create no absent target. Doctor reports an overlay whose version marker differs from the running CLI as `stale`, with the refresh command. Basis: F4.
- **D6** — "Keel MUST NOT install, update, pin, or resolve a plugin or CLI version" becomes a rule about hooks and projections. The owner-run `keel --update` may install through the hosts' documented commands, and nothing else may. Basis: the owner's 2026-10-03 decision on #204.

## Risks / Trade-offs

- A hand-off costs one extra `node` start, roughly 40 ms, on each hook call of a session whose plugin is older than the installed one. An aligned session pays only for reading the install record.
- A future release could change a hook script's stdin or stdout contract within the same major version, and an old loader would hand it events in the old shape. The hook contract is the host's, and Keel's scripts relay it unchanged, so a breaking contract change must bump the major version.
- Real adoption can only be demonstrated across two releases that both carry `forward.js`. Task 3.2 does that with a patch release after the first one.
- Codex re-reads the hook definition per call, so a release that changes `hooks/codex.json` stops those hooks until the owner reviews them. D1 reports this rather than avoiding it.

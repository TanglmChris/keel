# Updating Keel

A Keel release reaches a machine in four places: the global `keel` CLI, the Claude Code plugin, the Codex plugin, and each project's protocol block and overlays. As of 5.89.0, one command updates the first three. The fourth catches up in each project's own next session.

## One command for the machine

```bash
keel --update
```

It updates the global CLI, then the Keel plugin of each host it finds installed, through that host's own commands:

| Component | Commands it runs | Takes effect |
| --- | --- | --- |
| CLI | `npm pack @christang/keel`, `npm install -g <tarball>` | the next command that runs `keel` |
| Claude plugin | `claude plugin marketplace update keel-marketplace`, `claude plugin update keel@keel-marketplace` | a running session's next hook call; its skills and agents after `/reload-plugins` |
| Codex plugin | `codex plugin marketplace upgrade keel-marketplace`, `codex plugin add keel@keel-marketplace` | a running session's next hook call |

Each component prints one line, `keel update: <component>: <status> - <detail>`, where the status is one of:
- `updated A -> B` or `current B`;
- `absent`: the host is not installed or has no Keel plugin;
- `manual`: a step only you can take;
- `failed`: the command that failed, which also makes `keel --update` exit nonzero.

`keel --update --dry-run` prints the commands and runs none. No hook ever runs any of this. Only you do, by running the command.

Two cases need you:
- **A Codex marketplace that is a local path.** `codex plugin marketplace upgrade` refreshes Git marketplaces only, and a local one follows whatever branch its checkout is on. The Codex line then reads `manual` and names the commands that make it upgradable: `codex plugin marketplace remove keel-marketplace`, then `codex plugin marketplace add TanglmChris/keel --ref main`. Keel does not re-point it.
- **Changed Codex hook definitions.** Codex trusts each hook by the hash of its definition. When a release changes `hooks/codex.json`, the Codex line says so, and those hooks do not run until you review them in `/hooks`.

## Projects catch up on their own

`keel --update` writes into no repository. When a session starts in a project whose protocol block is older than the running CLI, `keel context` prints a `Protocol:` line naming the refresh. A project that standing-authorizes `protocol-refresh` in `keel/config.yaml` lets that session run it, and otherwise the session asks.

The refresh brings the overlays of every target the project carries forward, not only the target the session runs on. `keel --doctor` reports an overlay left at another version as `stale`.

## What a running session picks up

| Event | Claude Code | Codex |
| --- | --- | --- |
| New session | Loads the installed plugin. | Loads the installed plugin. |
| Resume | A resumed session is a new process and loads the installed plugin (not separately probed). | A resumed thread's next hook runs the installed plugin, as the next row shows. |
| Next hook call in a running session | From 5.89.0, each Keel hook hands the event to the newest installed copy of itself with the same major version. A session loaded before 5.89.0 keeps its loaded hooks. | Runs the installed plugin: Codex resolves the plugin root at every hook call [1]. |
| Compact, clear | Fires SessionStart, which hands off as in the row above. Before 5.89.0 it ran the loaded version (#172). | Same as the next hook call. |
| Skills and agents | Stay at the loaded version until `/reload-plugins` or a new session. After a hand-off, SessionStart says so in one line, and only when they changed. | Not probed. |
| Write guard during a task | Keeps the loaded guard while `keel/guard.json` exists, and hands off on the first check after it is cleared. | Switches at the next call, which the host decides. The decision depends only on the `keel-write-guard/v1` manifest, and an unknown schema fails closed. |
| Old version directory | Kept, so a loaded session's scripts keep working. | Deleted on upgrade, which does not matter because hooks are resolved per call [1]. |

[1] Measured with codex-cli 0.159.3 on 2026-10-03 and recorded on [#204](https://github.com/TanglmChris/keel/issues/204):
- In one long-lived `codex app-server`, a thread's next hook after `codex plugin add` of a newer version ran that version from its new directory.
- The old directory had been deleted.
- Both hooks stayed trusted, because their definitions had not changed.

`node scripts/run_python.js scripts/validate_codex_receiving.py --native-upgrade` repeats this in an isolated `CODEX_HOME`, with no model run and no personal trust written.

The Claude rows are covered by `hook-hands-off-to-installed-update`, `guard-keeps-loaded-logic-under-manifest`, and `adopted-update-is-silent-unless-reload` in `scripts/validate_plugin.py`, and by #172 for the behavior before 5.89.0.

## Measured across two releases

On 2026-10-03, with 5.89.0 installed and loaded:
- A headless Claude Code 2.1.283 session (`claude -p --input-format stream-json --include-hook-events`) and a `codex app-server` (codex-cli 0.159.3, the owner's real Codex home, model requests captured locally) were started and kept running.
- 5.89.1 was published, carrying a skill-text change.
- One `keel --update` reported `cli`, `claude plugin`, and `codex plugin` each `updated 5.89.0 -> 5.89.1`.
- The project's protocol was then refreshed to 5.89.1.

Results:
- **Claude.** The session still reported keel loaded from `…/keel/5.89.0`. Its SessionStart after `/compact`, with no `/reload-plugins`, said: "Hooks now run the installed plugin 5.89.1 in place of the loaded 5.89.0; its skills changed, and `/reload-plugins` loads them — the only step left." It carried no drift line.
- **Codex.** The running app-server's four Keel hooks stayed `trusted`, and a new thread's SessionStart projection carried no drift line against CLI and protocol 5.89.1. A stale 5.89.0 plugin would have named itself in one.

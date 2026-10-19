## Context

A launchd job outlives the shell that rendered it, so what it names has to outlive that shell's environment. `process.execPath` is the binary's real location, which a package manager moves on upgrade; the `node` a person types is the symlink that the manager keeps current.

## Facts

- F1 — `process.execPath` of Homebrew's node is `/opt/homebrew/Cellar/node/<version>/bin/node`; `/opt/homebrew/bin/node` is a symlink to it that `brew upgrade` repoints (#387).
- F2 — Three places put `process.execPath` first in a plist: `tick.js` (`task`), `chat/wake.js` (`plistText`), `chat/lifecycle.js` (`plistText`). The last two also copy `process.env.PATH` whole.
- F3 — `KEEL_CHAT_LAUNCH_AGENTS_DIR` already redirects the chat LaunchAgents directory for tests and for owners.

## Decisions

- D1 — `src/core/launchd.js` holds `stableNode()` and `launchdPath()`. `stableNode()` walks `PATH`, and returns the first `<dir>/node` whose realpath equals the realpath of `process.execPath`; otherwise `process.execPath`. It uses no version-manager knowledge: whichever name on `PATH` resolves to this binary is the name the person relies on.
- D2 — `launchdPath(value)` drops directories matching `/.claude/plugins/cache/`, keeps the rest in order. Dropping is safe for the jobs because they call `node` and `keel.js` by absolute path.
- D3 — Doctor prints one `launchd` line per `dev.keel.*.plist` in the LaunchAgents directory: `ok` with the node path, or `problem` naming the file, the missing path, and the command that re-creates the job (`keel tick task`, `keel chat wake add`, `keel chat bridge install`). It prints nothing when there are none, and does not change doctor's exit status: a repository's doctor should not go red over a machine-wide job.

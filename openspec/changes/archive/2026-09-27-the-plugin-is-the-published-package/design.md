## Context

Issue #164 holds the owner's decision and the probes. The host facts below come from those probes on Claude Code 2.1.281 and are recorded there. Keel's side is stated here.

## Findings

- F1 — A `relative path` marketplace plugin is copied from its own directory only. Claude caches `plugins/keel`, so `bin/`, `src/core`, and `assets` never reach it, and the hooks run whatever `keel` is on PATH.
- F2 — An `npm` plugin source makes the package root the plugin root. Probe: a local marketplace entry `{source: npm, package: @christang/keel, version: 5.73.1}`, with the entry acting as the manifest, passed `claude plugin validate` and installed as `keel@keelnpm 5.73.1`. The same tree loaded with `--plugin-dir` ran the SessionStart projection and exposed all six `keel:` skills and the agent.
- F3 — A plugin's `bin/` is on the Bash tool's PATH, and installed plugins' `bin/` directories were also on the hook process's PATH. They come *after* the user's own PATH entries, so a global `keel` wins.
- F4 — The host installs a plugin's dependencies only when its root carries `package.json` beside a supported lockfile, and runs `npm ci --ignore-scripts`. npm never publishes `package-lock.json`, so the published package carries no lockfile today. `npm-shrinkwrap.json` is published, and npm gives it precedence over `package-lock.json`. A cold `npm ci --ignore-scripts` of this tree took 4.1 s against the host's 60 s limit.
- F5 — Without its dependencies the package's CLI still runs, and `keel context` works. OpenSpec then resolves to whatever standalone copy is on PATH (1.4.1 here, against a pinned 1.6.0), which the doctor line reports as a mismatch.
- F6 — `npm pack` keeps an executable file's mode (`bin/mp` packed `-rwxr-xr-x`). The currently published `bin/keel.js` is tracked `100644` and arrived in the cache as `-rw-r--r--`. Whether the host's npm-source unpack keeps a `755` mode has not been observed yet.
- F7 — `declaredOpenSpecVersion()` in `bin/keel.js` reads only `package-lock.json`. After the rename, doctor run on this repository would report "repo declares no OpenSpec version".
- F8 — The version-drift line currently says "an updated plugin applies only after restarting", and `runtime-version-drift` asserts the tokens `fixed at session start` and `restart`. `/reload-plugins` makes the second half untrue.

## Decisions

- D1 — **The marketplace entry is the manifest.** The Claude entry sets:
  - `source: {source: npm, package: @christang/keel, version: <v>}` and `version: <v>`;
  - `skills: ["./plugins/keel/skills/"]`;
  - `agents: ["./plugins/keel/agents/keel-single-task-goal-claude.md"]`;
  - inline `hooks` equal to `plugins/keel/hooks/hooks.json`, with each script path prefixed `plugins/keel/`.

  The package root carries no `.claude-plugin/plugin.json`. `plugins/keel/.claude-plugin/plugin.json` stays, because `--plugin-dir plugins/keel`, doctor, and the manifest scenarios read it. The host ignores it inside the package, since it is not at the root. The entry and `hooks.json` now state the same hooks twice, so a scenario asserts they agree (D7).

  Alternative rejected: moving the Claude manifest to the repository root. It needs the same inline hooks, because `hooks.json` paths are relative to `plugins/keel`, and it would move a file that doctor, `capabilities.js`, and four scenarios read by path, for no difference to the user.
- D2 — **Pin both versions to the exact release.** `source.version` pinned means a refresh between merge and publish fails the fetch and succeeds on retry. Unpinned, the host would fetch the previous package and cache it under the new version label, and that silent mislabel is what the pin prevents. `bump_version.js` moves both numbers, and `version-alignment` checks both.
- D3 — **`bin/keel`** is an extensionless, executable (`100755`) shim that requires `./keel.js`. The `package.json` `bin` map is unchanged, so global installs behave as before. F6 leaves the host's unpack mode unobserved, so the release task checks it on the first real update. The hook never depends on the mode: it runs `node <root>/bin/keel.js`.
- D4 — **Rename the lockfile.** `package-lock.json` becomes `npm-shrinkwrap.json`: `git mv`, identical content. `declaredOpenSpecVersion()` reads `npm-shrinkwrap.json` first and falls back to `package-lock.json`, the precedence npm applies. The "unreadable" detail names whichever file it read. CI runs `npm ci`, which accepts either file.
- D5 — **Which CLI the hook runs.** In order:
  1. `KEEL_CLI` when set;
  2. the package's own `bin/keel.js`, when `plugins/keel/scripts/../../..` holds a `package.json` named `@christang/keel` and that file exists;
  3. `keel` on PATH.

  The second step is identified by package name, not by path alone, so a Codex cache, which holds only `plugins/keel`, never reaches outside itself to some unrelated `bin/keel.js`.
- D6 — **Report a shadowing `keel`.** When the hook ran its own CLI (step 2), it also asks the `keel` on PATH for `--version`. If one answers with a different version, the drift report names it as `PATH keel <x>` beside the plugin's CLI version. It adds that the agent's commands resolve the PATH copy first, so it shadows the plugin's. The remedies are named, not run: `npm rm -g @christang/keel`, since the plugin carries its own, or `npm i -g @christang/keel@<plugin version>`. A PATH with no `keel` is not drift: that is the plugin-only install this change enables. The comparison stays local and offline.
- D7 — **Assertions.**
  - `native-plugin-manifests`:
    - the Claude entry is npm-sourced, with both versions equal to `package.json`;
    - its skills and agents resolve inside the package;
    - its inline hooks equal `hooks.json` after prefixing;
    - the packed file list contains `bin/keel` with an executable mode, and contains `npm-shrinkwrap.json`.
  - `native-plugin-marketplaces`: this scenario runs only where both the codex and claude CLIs are installed. It installs from a temporary marketplace whose entry points at a local copy of the package, because the version under test is not published yet.
  - `runtime-version-drift`:
    - the drift line names `/reload-plugins`;
    - no "only after restarting" remains;
    - a planted package whose own CLI disagrees with a PATH `keel` reports the shadowing;
    - a planted package with no PATH `keel` stays silent.
- D8 — **The drift wording.** "A session's hooks are fixed when it loads the plugin, so an updated plugin applies after `/reload-plugins` or at the next session start." The phrase `fixed … session` is kept, so a reader still learns why nothing changed before they reloaded.

## Risks

- The window in D2. Treated as acceptable, and stated in the proposal.
- Existing users who keep a stale global `keel` will now see D6's line whenever its version differs from the plugin's. That is the intended signal: the stale copy was already the one the agent ran.
- The host could stop honoring `bin/` on PATH, or change where it puts it. The hook does not depend on either (D3). Only the agent's bare `keel` would regress, and it would regress to exactly today's behavior.

## Findings

- F1 — `versionReport()` in `plugins/keel/scripts/session-start.js` always names `plugin.remedy` (`claude plugin update` on Claude) and, when the PATH `keel` differs from the CLI, always names `npm i -g @christang/keel@${cli}`, where `cli` is the loaded plugin's CLI.
- F2 — On 2026-09-28 the running session loaded `~/.claude/plugins/cache/keel-marketplace/keel/5.77.0`, while `~/.claude/plugins/installed_plugins.json` recorded `keel@keel-marketplace` with `installPath` `…/keel/5.78.0` and `version` `5.78.0`. `claude plugin list` reported 5.78.0. `/reload-plugins` cleared the line.
- F3 — On Claude the plugin is the published package (#164), so the hook sits at `<package root>/plugins/keel/scripts/`, and the package root is `<plugins dir>/cache/<marketplace>/<plugin>/<version>`. `installed_plugins.json` sits in `<plugins dir>`.

## Decisions

- D1 — **Where the record is read.** `path.resolve(__dirname, "../../..")` is the package root; the record is `installed_plugins.json` four directories above it. It is located from the hook's own path, like the manifest, rather than from an environment variable or the home directory, so a plugin loaded from anywhere else finds no record.
- D2 — **What counts as a pending install.** Entries of the record's `plugins` map whose `installPath`'s parent equals the package root's parent — the same plugin under the same marketplace — and whose `installPath` is not the package root itself. When those entries carry exactly one distinct `version` string, and it differs from the loaded plugin's version, that version is pending. Anything else — no file, invalid JSON, an unexpected shape, no such entry, several distinct versions — is no pending install.
- D3 — **Wording with a pending install.** The drift sentence keeps its first clause and the `fixed when it loads the plugin` / `/reload-plugins` tokens, and replaces `Updating is <remedy>, which Keel names and does not run.` with `The host has already installed plugin <v>, so nothing needs updating.` It does not name `claude plugin update`.
- D4 — **PATH with a pending install.** When the PATH `keel` equals the pending version, the shadow sentence is omitted. Otherwise it is kept and its align command names the pending version.
- D5 — **No pending install** leaves the line exactly as 5.78.0 prints it.

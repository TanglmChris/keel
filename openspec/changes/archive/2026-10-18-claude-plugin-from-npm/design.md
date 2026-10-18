## Context

#337 asks for the Claude plugin to come from npm. 5.80.0 moved it from npm to git; this change moves it back, on the owner's decision of 2026-10-18 made with that history in view.

## Facts

- F1 — Claude Code's marketplace reference: the `npm` marketplace source "Fails to load: NPM marketplace sources not yet implemented"; the `npm` plugin source takes `package`, `version`, `registry`, is fetched with the user's npm client without install scripts, and refuses a git address, a folder or `file:` path, and an `http` tarball. `/opt/homebrew/Caskroom/claude-code@latest/2.1.302/claude` contains the string twice (grep, 2026-10-18).
- F2 — Claude Code installs a copied plugin's dependencies from `npm-shrinkwrap.json` beside `package.json`, for an npm source as for git; a plugin's version comes from its manifest `version` first (plugin loading reference).
- F3 — Measured 2026-10-18 in an isolated `CLAUDE_CONFIG_DIR`: Keel 5.139.0 installed from the git entry, then the entry changed to `npm` `@christang/keel` `5.140.0`; `claude plugin marketplace update` and `claude plugin update` printed `updated from 5.139.0 to 5.140.0`, the cache held the npm package's files with `node_modules/.bin/openspec` at `1.14.0`, and `claude plugin details` listed `Skills (0)` and `Hooks (0)`, because the published package has no `.claude-plugin/`.
- F4 — The package root plus the root manifest validates as a plugin (`claude plugin validate`), and its hooks run from the unpacked package (`session-start.js` printed the Keel projection; `mail-hook.js` exited 0 for each event).
- F5 — 5.80.0's reasons (keel/CHANGELOG.md): the components were declared in the marketplace entry, and one flow should feed npm, the marketplace, and Anthropic's directory, which takes git only. The components moved to `.claude-plugin/plugin.json` in that release, and the directory now tracks the `claude-directory` branch built from the npm package's files.

## Decisions

- D1 — The Claude entry's source is `{"source": "npm", "package": "@christang/keel", "version": "<release version>"}`, an exact version so a marketplace refresh never installs an unreleased or newer package than the catalog names. The entry keeps its `version` and restates no component.
- D2 — `package.json` `files` adds `.claude-plugin/plugin.json`, and nothing else from `.claude-plugin/`: the marketplace catalog is not read from the package (F1).
- D3 — The install smoke stages `npm pack`'s tarball, unpacked, as a scratch git repository and points a copy of the committed entry at it with a `url` source. What the host installs is then exactly the package's files, through a copying install that also installs the lockfile's dependencies; only the transport differs from npm, which refuses a local package (F1).
- D4 — The catalog stays at `.claude-plugin/marketplace.json` on GitHub, and `keel --init` keeps declaring the GitHub marketplace. README documents the `url` marketplace source (`https://raw.githubusercontent.com/TanglmChris/keel/main/.claude-plugin/marketplace.json`) for a machine whose git clone of GitHub fails, as on 2026-10-14.
- D5 — Anthropic's directory flow (`scripts/directory_tree.js`, `directory_branch.js`, `official_entry.js`) is unchanged.

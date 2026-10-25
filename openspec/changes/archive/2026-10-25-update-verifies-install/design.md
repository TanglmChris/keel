## Facts

- F1 — `updateGlobalCli` in `bin/keel.js` packs `source`, runs `npm install -g <tarball>`, and on exit 0 reports `versionChange(PACKAGE_JSON.version, <version in the tarball name>)`. Nothing reads the installed package afterwards.
- F2 — 2026-10-25, measured in this session:
  - `keel --update` printed `cli: updated 5.196.1 -> 5.197.1`, then `keel --version` printed `keel 5.197.0` and `npm ls -g @christang/keel` printed `@christang/keel@5.197.0`.
  - Run again, it printed `updated 5.197.0 -> 5.197.1`, and `keel --version` then printed 5.197.1.
  - npm keeps the last 10 debug logs, and the window of the first run had rotated out. The global package directory's mtime (14:43:11 local) does not fit the version order read, so the cause stays unknown.
- F3 — The update scenarios drive stand-in npm programs. Some reject unknown calls (`update-pack-install`'s `fake_npm.py`), and `UPDATE_FAKE` exits 0 printing nothing for calls it does not model.

## Decisions

- D1 — `installedCli(npm)` runs `npm root -g`, allowed the host-query limit. It reads `<root>/@christang/keel/package.json`, returning `{ version, file }` or `{ why }`.
- D2 — "From" is `installedCli` before packing, falling back to `PACKAGE_JSON.version` when unreadable. "To" is `installedCli` after the install.
- D3 — An install that exits 0 while the prefix holds a version other than the packed one reads `failed`, naming `npm install -g <tarball>`, the file, and the version it holds. The command exits nonzero, since a step that ran failed.
- D4 — When the prefix cannot be read after the install, the line keeps its existing wording plus `; not verified: <why>`. The stand-ins that do not model `npm root -g` (F3) therefore keep passing, and the line says what was and was not checked.

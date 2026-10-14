## Context

Issue #329 and the measurements in it (2026-10-14, codex-cli 0.159.3, owner's machine behind `127.0.0.1:7890`). Not chosen: a local-path marketplace, which `marketplace upgrade` cannot refresh and which follows whatever branch the checkout is on; and Keel editing the owner's Codex config itself, which re-points a source the owner chose.

## Facts

- F1 — `codex plugin marketplace upgrade keel-marketplace` failed after 36 s with `git clone marketplace source timed out after 30s … fatal: early EOF`. A `--depth 1` clone of the repository is 3.3 MB of pack and took 44 s on the same link; `git ls-remote` took 2 s.
- F2 — In a scratch `CODEX_HOME`, `marketplace add TanglmChris/keel --ref main --sparse .agents/plugins --sparse plugins/keel` stored `sparse_paths = [".agents/plugins", "plugins/keel"]`; `upgrade` took 19 s and `plugin add` installed 5.131.0.
- F3 — On the owner's config with `sparse_paths` added, three `upgrade` runs: 37 s fail, 59 s fail (`early EOF`), 25 s pass. `keel --update` then reported `codex plugin: current 5.131.0`.
- F4 — `plugins/keel` has no symbolic links and its hooks reference only `${PLUGIN_ROOT}`; the Codex catalog `.agents/plugins/marketplace.json` names `./plugins/keel`.

## Decisions

- D1 — `updateCodexPlugin` runs the marketplace upgrade step up to twice; the second run happens only when the first fails. `plugin add` is not retried: it reads the local clone.
- D2 — When both attempts fail, the `failed` line keeps the command and exit, and adds: `a slow link can exceed Codex's 30 s clone limit; a sparse marketplace fetches only the plugin: add sparse_paths = [".agents/plugins", "plugins/keel"] under [marketplaces.keel-marketplace] in <CODEX_HOME>/config.toml`.
- D3 — The sparse path list is one constant in `bin/keel.js`, used by the D2 line and the `manual` hint, whose command gains `--sparse .agents/plugins --sparse plugins/keel`.
- D4 — README (both languages) adds the sparse `codex plugin marketplace add` line before `codex plugin add`; `docs/updating.md` names the retry and the remedy.

## Facts

- F1 — DSH 0.2.2-rc.1 reads `AGENTS.md` from the project root down to the working directory and scans `<project>/.dsh/skills` then `<project>/.agents/skills` (probed on #504, 2026-11-08). The Codex target already writes `AGENTS.md` and, since OpenSpec 1.13, `.agents/skills`.
- F2 — The factory `desktop` and `headless` profiles contain no hook plugin (searched `--dump-config` for "hook", zero hits), so there is no third-party session-start event to attach to.
- F3 — `--target` is validated in `bin/keel.js` against `VALID_TARGETS` and passed unchanged to the Python installer, to the OpenSpec tool selection and to the overlay functions, each of which branches on `claude | codex | opencode`. `probeCapabilities` and `projectRuntime` check their own `claude | codex | opencode` sets.
- F4 — `installedOpenSpecTargets(repo)` enrolls a target by the repository files it finds; it cannot tell DSH from Codex because they are the same files.

## Decisions

- D1 — `parse` accepts `dsh` and stores `options.host = "dsh"` with `options.target = "codex"`. Every file-surface path (installer, OpenSpec tools, overlays, protocol drift, bootstrap, skills count) therefore runs the Codex code unchanged. `options.host` falls back to `options.target` for the other targets.
- D2 — `capabilities.js` and `projection.js` accept `dsh` as a target and report it by name. `keel capabilities` and `keel project` receive `options.host`, so their output says `dsh`. The six capabilities are `manual` with evidence `DSH reads AGENTS.md and .agents/skills and its factory profiles carry no session-start, resume or compaction hook (probed with DSH 0.2.2-rc.1, 2026-11-08); the AGENTS.md bootstrap is the entry; installation, trust and behavior are not verifiable from Keel`. Guard and compaction diagnostics use the existing non-Claude text, which already says no verified native surface.
- D3 — The doctor block for `dsh` prints three lines: `DSH CLI` (`ok` with the version from `dsh --version`, or `not found`, never a failure, since a repository can be prepared on a machine without DSH), `DSH hooks` (`manual`, the F2 statement) and `DSH surface` (`ok`, shared with Codex: `AGENTS.md` and `.agents/skills`). The probe runs `dsh --version` with a five-second limit and writes nothing; it runs only for `--doctor --target dsh`.
- D4 — `--clear`/`--uninstall --target dsh` run the Codex removal and print, before it, that the removed files are shared with Codex (F4). Keel does not refuse, because nothing on disk says another host depends on them.
- D5 — `both` and the default target are unchanged, and `installedOpenSpecTargets` is untouched (F4): a repository is never auto-detected as DSH.

## Risks

- A repository set up with `--target dsh` and later checked with `--target codex` reports the same state; that is the intent, and README says so.

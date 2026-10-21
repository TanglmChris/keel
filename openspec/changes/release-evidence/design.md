## Context

#409 (5.184.0) split the runner into `scripts/validation/` modules with one registry, `scripts/validation/registry.py`. `--all` and `--group` share `run_scenario_processes`. The publish job's "Tag and release the landed version" step builds `notes.md` from the changelog section and the directory-branch line, then runs `gh release create`.

## Findings

- **F1. The stand-in points are visible in Keel's own sources.** Three kinds, read on 2026-10-21 at 5.185.0:
  - Program overrides read as `process.env.<VAR> || <fallback>`, with fallback `"claude"`, `"codex"`, `"gh"`, `"launchctl"`, `npmCommand(…)`, a `process.platform` conditional (`security`), or an upper-case constant (`DEFAULT_BASE`, `DEFAULT_UPDATE_SOURCE`). There are ten: `KEEL_CLAUDE`, `KEEL_UPDATE_CLAUDE`, `KEEL_UPDATE_CODEX`, `KEEL_UPDATE_NPM`, `KEEL_UPDATE_SOURCE`, `KEEL_CHAT_CODEX`, `KEEL_CHAT_GH`, `KEEL_CHAT_LAUNCHCTL`, `KEEL_CHAT_SECURITY`, `KEEL_SLACK_API_BASE`. Path and identity overrides such as `KEEL_HOME` and `KEEL_CHAT_MACHINE` fall back to `path.join(…)` or `os.hostname()` and are not host stand-ins.
  - Host-set variables named `CLAUDE_*` or `CODEX_*` in `src/`, `bin/keel.js` or `plugins/keel/scripts/`: `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_ENTRYPOINT`, `CLAUDE_CODE_HOST_SESSION_ID`, `CLAUDE_PID`, `CLAUDE_CONFIG_DIR`, `CLAUDE_PLUGIN_ROOT`, `CODEX_HOME`, and others.
  - Hook payloads, which carry `hook_event_name`.
- **F2. Scenarios reach these through helpers.** `chat_wake_scratch` sets `KEEL_CLAUDE`, and `codex-receiving` runs `scripts/validate_codex_receiving.py`. So a classification of the scenario function's own text misses them, and one over the transitive closure finds them.
- **F3. A program can also be stood in for on `PATH`.** `update-pack-install` writes a fake `npm`. The tell is a path join ending in a host program's name: `/ "npm"`.
- **F4. Five scenarios reach `skip_scenario`.** These are `output-survives-the-pipe`, `native-plugin-marketplaces`, `native-plugin-install-matrix`, `a-declared-dependency-is-resolved`, and `the-dependency-resolves-where-npm-put-it`. Which of them skip is known only at run time. CI skips `output-survives-the-pipe`.

## Decisions

- **D1** — Two run classes and a stated absence. Every registered scenario is either **deterministic** (Keel's own code against real git, Node and files) or **stand-in host** (it drives Keel against a stand-in for a host program, the host's environment, a host data directory, or a hook payload). **Real host** is reported as none: the suite never calls a host. Real-host evidence lives in `docs/host-contract.md`, measured with version and date, and the summary points there rather than inventing a count.
- **D2** — Classification is static and derived, in `scripts/validation/evidence.py`. Markers come from Keel's sources at run time: the F1 override regex, the `CLAUDE_*`/`CODEX_*` names, `hook_event_name`, and a path join to a host program name (F3). A scenario is stand-in host when any marker appears in the source of:
  - its function;
  - any module-level function or assignment in `scripts/validation/` it reaches by name;
  - any `scripts/*.py` file those mention.

  This over-approximates. A scenario that only mentions a marker counts as stand-in, which errs toward claiming less real evidence, never more.
- **D3** — The line after a pass. `--all` and `--group` print the existing summary line, then one more line:

  `evidence: <d> deterministic, <s> against a stand-in host, none on a real host (host measurements: docs/host-contract.md)`

  The counts exclude skipped scenarios, so they add up to the verified count. A failing run prints no evidence line, because its counts would describe a run that did not pass.
- **D4** — `--evidence [--markdown]` reports without running anything. It prints the classification counts and the names of the scenarios that can skip. With `--markdown` it prints an `## Evidence` section for release notes:
  - one bullet each for deterministic, stand-in host and real host, with the count of `measured` rows in `docs/host-contract.md`;
  - the scenarios that can skip;
  - a note that the counts are of registered scenarios. Run-time skips are named in the full gate's log.
- **D5** — The release notes carry it. The publish step appends the output of `node scripts/run_python.js scripts/validate_plugin.py --evidence --markdown` to `notes.md` before the directory line.
- **D6** — Desktop and Codex leave "unverified". `docs/host-contract.md` states two things in place of "unverified": the desktop app path is not maintained for the CLI team (owner, 2026-10-19), and Codex has no automated hand-over or wake. What stays unverified is whether a timed-out `claude --bg` had started its session.
- **D7** — Evidence. A new selfcheck scenario, `release-evidence-classes`, asserts the following through the public entry points:
  - `--evidence` classifies these known scenarios this way:
    - `shift-cli-self-shift`, through `KEEL_CLAUDE`: stand-in;
    - `chat-claude-hooks`, through a hook payload only: stand-in;
    - `codex-receiving`, through a delegated script only: stand-in;
    - `update-pack-install`, through a fake `npm` on PATH: stand-in;
    - `version-alignment`: deterministic.
  - The two counts add up to the registry's size.
  - The derived markers include `KEEL_CLAUDE` and `CLAUDE_CODE_SESSION_ID`, so a broken derivation cannot pass as an empty marker set.
  - `--markdown` prints the section with the measured-row count of `docs/host-contract.md`.
  - The publish release step appends that output to `notes.md`.
  - `--group docs` prints an `evidence:` line whose counts add up to its verified count. It is not `--group selfcheck`, because that group holds this scenario.

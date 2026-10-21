## Why

Issue #408 asks for release records that "分列确定性测试、桩适配测试、真实宿主实测、跳过/未验证项及版本；不以一个绿色汇总代替能力实测". On 2026-10-21 the owner chose to have the test summary count these classes automatically rather than write them by hand in each changelog entry.

Today `npm test` ends with one line: `validation --all passed: baseline plus 315 scenarios, 1 skipped: output-survives-the-pipe.`. Release notes on GitHub are the changelog section plus the directory branch. Neither says that much of the suite runs Keel against a stand-in host:
- a fake `claude`, `codex`, `gh`, `npm`, `launchctl` or `security` program;
- the host's environment, such as `CLAUDE_CODE_SESSION_ID`;
- a fake host data directory, such as `CLAUDE_CONFIG_DIR` or `CODEX_HOME`;
- a hook payload in the host's shape.

Neither says that the suite runs nothing against a real host, since the CI runner has no Claude Code or Codex. A green run is therefore read as more than it proves.

A prototype run against the 5.185.0 registry (316 scenarios) found:
- **Keel's sources name every stand-in point.** 10 program overrides read as `process.env.KEEL_X || "<program>"`, and 9 host variables `CLAUDE_*` / `CODEX_*`.
- **Static reachability classifies each scenario.** A scenario counts as stand-in if its code, any validation helper it reaches, or a validation script it runs mentions one of those variables, a hook payload's `hook_event_name`, or a program file named for a host program. The prototype counted about 134 stand-in and 182 deterministic.
- **Five scenarios can skip at run time.**

## What Changes

- **`scripts/validation/evidence.py` classifies every registered scenario.** The classes are deterministic or stand-in host. Classification is static, from markers derived from Keel's own sources, so a new override variable is picked up without a list to maintain. It also names the scenarios that can skip.
- **`--all` and `--group` print an `evidence:` line after a passing summary.** It gives the number of deterministic and stand-in-host scenarios that ran, counted without skips, and states that the suite ran nothing on a real host. It also says where real-host measurements are recorded: `docs/host-contract.md`.
- **`validate_plugin.py --evidence [--markdown]`** prints the classification without running anything. With `--markdown` it prints an `## Evidence` section.
- **The publish workflow appends that section to each GitHub release's notes.** Every release then states its evidence by kind:
  - the deterministic count;
  - the stand-in-host count;
  - that no real-host check ran, and how many conditions `docs/host-contract.md` records as measured on a real host;
  - which scenarios can skip.
- **`docs/host-contract.md` records two decisions instead of leaving them unverified:**
  - The desktop app path is not maintained for this team. The owner moved the team to CLI sessions on 2026-10-19.
  - Codex has no automated hand-over or wake. Its shift ends with "start a new session in this worktree", so it has no host calls to verify.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-validation-runner`

## Impact

- New: `scripts/validation/evidence.py`.
- Changed: `scripts/validate_plugin.py`, `scripts/validation/selfcheck.py`, `scripts/validation/registry.py`, `.github/workflows/publish.yml`, `docs/host-contract.md`, both READMEs (the test command lines), the published spec, and the changelog.
- No product code under `src/` or `bin/` changes.

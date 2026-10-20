# Tasks

## 1. Update Codex from its own state when the list query fails

- [x] 1.1 Fall back to Codex's config and plugin cache when `codex plugin list --json` fails
  - Covers:
    - keel-native-plugin-package / One owner-run update covers every installed Keel component / A hung query does not stop an update Codex's own state can carry
    - keel-native-plugin-package / One owner-run update covers every installed Keel component / A hung host query is a failure, not an absent host
    - D1
    - D2
    - D3
  - Read:
    - openspec/changes/codex-update-without-list/design.md
    - bin/keel.js
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario update-codex-from-disk`: with a fake codex whose `plugin list --json` hangs past a 2 s query limit, a `CODEX_HOME` whose `config.toml` declares `[marketplaces.keel-marketplace]` with `source_type = "git"`, and a plugin cache holding `keel/5.0.0`, `keel --update` runs `plugin marketplace upgrade keel-marketplace` and `plugin add keel@keel-marketplace` once each, prints a Codex line with `updated 5.0.0 -> 5.1.0` naming the plugin cache and that the list query did not answer, and exits 0; with `source_type = "local"` the line reads `manual`; and with no `config.toml` the line reads `failed` and no Codex command runs. Fails with: `update-codex-from-disk:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario update-host-query-timeout`, `--scenario update-host-query-retry`, `--scenario update-codex-refresh-retry`, and `--scenario update-covers-installed-hosts` pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3ea032f1faa27cfa7783b36755e50ec72543484bb7cff25b832831d2e8e375b1 (keel 5.172.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario update-codex-from-disk` reports `update-codex-from-disk scenario passed.` (exit 0): with the list query held past a 2 s limit and a git marketplace plus `keel/5.0.0` on disk, the upgrade and `plugin add` ran once each, the line read `updated 5.0.0 -> 5.1.0` naming the cache directory and that the list did not answer, and the exit was 0; a `local` source read `manual` with no upgrade; no `config.toml` read `failed` with no Codex update command.
    - M1.red: fail. Before the change: `update-codex-from-disk: with a git marketplace on disk, codex plugin marketplace upgrade keel-marketplace ran 0 time(s), not 1: 'keel update: codex plugin: failed - `codex plugin list --json` timed out twice, after 2 s each'` (exit 1) — the #412 symptom.
    - M1.green: pass. With `codexKeelFromDisk` (the `[marketplaces.keel-marketplace]` section of `$CODEX_HOME/config.toml` plus the highest version directory under the plugin cache), `updateCodexPlugin` substituting it for a failed query outside `--dry-run`, skipping the post-refresh query, reading the post-add version and hooks from the cache, and naming the list failure and the cache in the line, the scenario passed. The fake codex's `plugin add` now replaces the cache's version directory when `FAKE_CODEX_CACHE` is set, as Codex does.
    - M2: pass. `update-host-query-timeout`, `update-host-query-retry`, `update-codex-refresh-retry`, and `update-covers-installed-hosts` each report `scenario passed.`
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel --update` with a stub codex, a hung list query no longer stops an update Codex's own config and cache can carry, a local source stays manual, and an install that neither the query nor the disk shows stays `failed`, never `absent`.
      - Scope check: `git status --short` lists `bin/keel.js`, `scripts/validate_plugin.py`, and this change's directory.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [x] 2.1 Release and promote the spec
  - Covers:
    - E2
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/marketplace.json
    - .claude-plugin/plugin.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validate_plugin.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-native-plugin-package/spec.md
    - .claude/commands/opsx/apply.md
    - .claude/commands/opsx/archive.md
    - .claude/commands/opsx/propose.md
    - .claude/commands/opsx/sync.md
    - .claude/skills/openspec-apply-change/SKILL.md
    - .claude/skills/openspec-archive-change/SKILL.md
    - .claude/skills/openspec-propose/SKILL.md
    - .claude/skills/openspec-sync-specs/SKILL.md
    - .codex/skills/openspec-apply-change/SKILL.md
    - .codex/skills/openspec-archive-change/SKILL.md
    - .codex/skills/openspec-propose/SKILL.md
    - .codex/skills/openspec-sync-specs/SKILL.md
  - Verify:
    - Strategy: evidence-first
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion; the behavior is proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the delta is promoted into `keel-native-plugin-package`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:991e071d1663336262832e660089597e68657b2e3ee632d1610695e927b592bb (keel 5.172.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.173.0 → 5.174.0; with the "A hung Codex plugin query no longer stops the Codex update" section written into the stub the bump left, `version-alignment scenario passed.` (exit 0).
    - M2: the modified requirement replaced "One owner-run update covers every installed Keel component" in `keel-native-plugin-package`; `published-specs-validate-strictly scenario passed: 33 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - M3: pass. `npm test` on commit d9fdf9b (clean tree), started 19:46 at load 7: `validation --all passed: baseline plus 293 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the 5.174.0 changelog section, and the published spec carry the change; the full suite passes on the committed tree.
      - Scope check: files beyond task 1.1 are the version markers, `keel/CHANGELOG.md`, and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "a query that times out twice, exits nonzero, or prints no JSON MUST report that component `failed`" — `keel-native-plugin-package`. Updated by: 2.1.

## Expectation Coverage

- E1: A hung `codex plugin list --json` does not stop an update Codex's own config and cache can carry, and still fails when they show no install (#412; D1, D2, D3). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1

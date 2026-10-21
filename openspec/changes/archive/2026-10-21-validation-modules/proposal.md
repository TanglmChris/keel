## Why

Issue #409. `scripts/validate_plugin.py` is about 43,000 lines holding 312 registered scenarios with their fixtures, helpers, registry, runner, and summary. Every session that adds a scenario edits the same file, which is where parallel Keel sessions collide (on 2026-10-21 keel-maint held back three scenarios for #408 so the split could start from one base), and finding the helper a scenario uses means searching one file.

The owner decided on 2026-10-21 (recorded on #409): split into genuinely separate Python modules that import the shared helpers they use, and add a `--group` entry that runs one module's scenarios.

## What Changes

- The scenarios move, unchanged, into modules under `scripts/validation/` grouped by responsibility: `contract`, `install`, `hosts`, `guard`, `chat`, `shift`, `docs`, `selfcheck`. Shared helpers and constants go to `common`, the baseline checks to `baseline`, and the one ordered registry to `registry`. Each module imports what it uses from `validation.common` by name.
- `scripts/validate_plugin.py` stays the entry point and keeps the runner. `--scenario`, `--all`, and `--jobs` behave as before.
- New `--group <name>` runs one module's registered scenarios in registry order, with the same isolation, skip accounting, and summary as `--all` and without the baseline.
- The self-checks that read the runner's own source read every module: the unregistered-scenario check, the assertion-shape count, the path scan for mutating commands, and the standard-library import check. The standard-library check now accepts the local `validation` package.
- `scripts/bump_version.js` writes the version constants in their new home, `scripts/validation/common.py`.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-validation-runner`: the registry and scenarios live in modules, a group runs alone, and the self-checks read every module.

## Impact

`scripts/validate_plugin.py`, new `scripts/validation/*.py`, `scripts/bump_version.js`, `README.md`, `README.zh-CN.md`, `docs/updating.md`, the published spec, the changelog. No production code changes.

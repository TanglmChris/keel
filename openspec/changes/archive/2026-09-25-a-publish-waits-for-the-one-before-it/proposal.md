## Why

`.github/workflows/publish.yml` triggers on `release: [published]` and declares no `concurrency` group.
Landing the eleven-PR stack produced eleven releases within ~20 seconds, so eleven `npm publish` jobs
ran against the same package at once (#153).

Nothing was lost — every job logged its own `+ @christang/keel@<version>`, and the write side later
proved it by refusing a re-run with `You cannot publish over the previously published versions: 5.66.0`.
What broke was the **read** side: for several minutes the registry's packument reported published
versions as missing, and the set of missing ones changed between reads.

The cost was a wrong diagnosis acted on. Reading the registry listing is the obvious way to confirm a
publish, and it lied for long enough to trigger two re-runs that now sit in the Actions history as red
failures against a release that had succeeded — a permanently misleading record.

Serialized, each publish finishes and is confirmable before the next begins, and the window does not
exist.

## What Changes

- **`publish.yml` declares `concurrency: {group: publish, cancel-in-progress: false}`.** The `false` is
  the load-bearing half: the default cancels a queued run when the next release fires, which would turn
  a confusing-but-harmless lag into a genuinely missing version.
- **A validation scenario asserts it.** The workflow is the one file in this repository whose behavior
  cannot be observed locally — it only runs on GitHub, on an event nobody triggers on purpose — so
  without a check the declaration can be dropped in a future edit and nothing would notice until the
  next multi-release day.

## Capabilities

### Modified Capabilities

- `keel-validation-runner`: the suite asserts the publish workflow serializes, and asserts the one
  option whose default is wrong for it.

## Impact

- `.github/workflows/publish.yml` — the declaration.
- `scripts/validate_plugin.py` — the assertion.
- **Not adopted**: having the workflow poll the registry to confirm its own publish. That is the read
  side this change exists because of; the `+ @christang/keel@<version>` line `npm publish` already
  prints is the confirmation, and it is emitted by the write path.

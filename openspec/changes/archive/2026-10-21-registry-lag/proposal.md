## Why

Issue #421. Right after each release from 5.171.0 to 5.177.0, `keel --update` reported the Claude plugin `failed` with `Could not resolve @christang/keel@<new> from the npm registry: E404 No match found for version <new>`, and the CLI line read `current <old>`. The publish job had already logged `+ @christang/keel@<new>` and created the release; the owner's machine, which reaches the registry through a proxy, simply did not see the new version yet. On 2026-10-20 `npm view @christang/keel version` returned 5.177.0 about 3 minutes after the release, and a rerun of `keel --update` then updated all three components. A `failed` line that a rerun fixes reads as a defect, and an unattended run counts it as one.

The owner decided on 2026-10-21 (recorded on #421) to do both of the issue's options.

## What Changes

- `keel --update`: when `claude plugin update` fails with `E404 No match found for version X` and `npm view @christang/keel version` answers a version older than X, the Claude line reads `pending`, names X and the registry's latest, and says to rerun `keel --update` in a few minutes. It does not fail the command. Any other failure, including an E404 for a version the registry already serves or an `npm view` that does not answer, stays `failed`.
- `keel --update`: the CLI line names the version the npm registry served as its latest, so `current <old>` is no longer read as "nothing newer exists".
- `publish.yml`: after `npm publish`, the job waits until `npm view @christang/keel@<version>` resolves on registry.npmjs.org, through a new `scripts/await_registry.js`, before it tags and creates the release. A release therefore announces a version the public registry already serves. Mirrors and proxies may still lag, which the first change covers.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-native-plugin-package`: the owner-run update reports registry lag as `pending`, and a release completes only once the registry serves its version.

## Impact

`bin/keel.js` (`updateClaudePlugin`, `updateGlobalCli`, `runGlobalUpdate`), new `scripts/await_registry.js`, `.github/workflows/publish.yml`, `scripts/validate_plugin.py`, the published spec, the changelog.

## Why

Issue #459, approved by the owner on 2026-10-25. Right after 5.197.1 was released, `keel --update` printed `cli: updated 5.196.1 -> 5.197.1`, but `keel --version` and `npm ls -g @christang/keel` both read 5.197.0 immediately afterwards. A second run printed `updated 5.197.0 -> 5.197.1` and took.

The line is built from two assumptions:
- the "from" version is `PACKAGE_JSON.version`, the copy of keel that happens to be running;
- the "to" version is the packed tarball's name, reported whenever `npm install -g` exits 0.

Neither assumption checks what the global prefix actually holds. A false `updated` leaves the CLI a release behind without anyone noticing, and running `keel --update` after every release is the owner's standing habit.

The root cause of that one occurrence could not be established. npm keeps only its last 10 debug logs, so the logs had rotated out, and the install directory's timestamp did not line up with the versions read. The fix does not depend on the cause: the line reports what is installed.

## What Changes

- **Before and after are read from the global prefix.** `keel --update` reads `<npm root -g>/@christang/keel/package.json` before packing and again after installing.
- **A mismatch is a failure.** When `npm install -g` exits 0 but the prefix holds a version other than the packed one, the CLI line reads `failed`, names the file and the version it holds, and the command exits nonzero.
- **Unverified when the prefix cannot be read.** When `npm root -g` or the file cannot be read, the line keeps today's wording, takes "from" from the running copy, and adds that the install was not verified, with the reason.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-native-plugin-package`

## Impact

`bin/keel.js`, `scripts/validation/hosts.py`, `scripts/validation/registry.py`, the published spec, and the changelog.

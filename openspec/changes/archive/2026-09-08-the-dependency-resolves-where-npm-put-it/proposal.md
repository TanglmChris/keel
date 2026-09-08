# The dependency resolves where npm put it

## Why

`keel openspec …` does not resolve on a standard npm install, and `keel --doctor`
reports the dependency as missing while it sits installed and runnable a
directory away (issue #129). Measured against the published 5.57.0 tarball in an
empty project.

`openspecCandidates()` looks in exactly one place inside the package —
`PACKAGE_ROOT/node_modules/.bin/openspec` — and then on PATH. npm hoists: when
Keel is installed as a dependency, the OpenSpec bin lands in the **consumer
project's** `node_modules/.bin`, and `PACKAGE_ROOT/node_modules` does not exist
at all. The one layout where the current lookup works is a checkout of this
repository, which is why 170 scenarios and every release gate stayed green.

The cost is concentrated on what 5.56.0 just shipped: `keel openspec` is the
invocation now written into twelve installed OpenSpec surfaces as the one that
resolves, and `keel --doctor` is the diagnostic those surfaces point at for which
case a given installation is. Both are wrong on the common install, and doctor's
advice — reinstall so npm installs the dependency — cannot help, because npm
already did.

## What Changes

- Keel resolves its OpenSpec dependency the way Node resolves a module: from the
  package root upward through each `node_modules/.bin`, then on PATH.
- Doctor distinguishes a dependency that is absent from one that is present and
  unreachable, and stops advising a reinstall that would change nothing.
- The published tarball is exercised the way a user installs it, so a defect that
  only appears outside a checkout of this repository cannot pass a release again.

## Impact

- Affected specs: `keel-target-surface-diagnostics`
- Affected code: `bin/keel.js`, `scripts/validate_plugin.py`

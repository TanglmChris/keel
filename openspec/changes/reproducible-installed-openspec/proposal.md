## Why
Issue #534 found installed OpenSpec1.17.0 while the shipped lock names1.14.0, changing strict validation behavior. Determine the installation mechanism before choosing a reproducible repair.
## What Changes
- Compare real clean and upgrade installations using the same published tarballs and npm11.19.0.
- Verify tarball lock contents, installed dependency tree, actual public CLI selection and strict behavior.
- Repair the confirmed cause and ship verified matching CLI/plugin artifacts; implementation tasks follow measured diagnosis.
## Capabilities
### New Capabilities
None.
### Modified Capabilities
- `keel-release-artifact`: predictable installed validation dependency behavior.
## Impact
Package distribution, installation validation, dependency resolution and release documentation. No #527 work, #535 architecture decisions or unrelated host/role changes.

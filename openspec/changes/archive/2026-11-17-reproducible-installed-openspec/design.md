## Context
F1 — Keel5.229.2 declares OpenSpec ^1.4.1 and its shrinkwrap locks1.14.0, but the current global installation resolves1.17.0. Basis: source files and actual installed package inspection on2026-11-17; #534.
F2 — npm11 documentation describes a published shrinkwrap as appropriate for globally installed CLIs. Basis: https://docs.npmjs.com/cli/v11/configuring-npm/npm-shrinkwrap-json/ . Current npm is11.19.0; do not infer its behavior from npm12 documentation.
## Goals / Non-Goals
Reproducible supported validation after clean installation and update; prove behavior through installed CLI. No warning suppression, unrelated dependency upgrades, global npm replacement or speculative fallback.
## Decisions
D1 — Diagnose first in isolated temporary prefixes, comparing registry tarballs, direct installs and the actual updater route with native plugins isolated. Record versions, exact commands, installed lock/tree, CLI resolver and strict validation. Basis: owner requests full closure of #534 and issue reproduction contract.
## Hidden Knowledge / Assumptions
None.
## Coupled Iteration Contract
- Coupled artifacts: package dependency declaration and regenerated lock root metadata.
- Invalidation triggers: change to the declared OpenSpec version or lock root dependency.
- Required regeneration: synchronize manifest and lock metadata and rerun real installed-path acceptance as one complete candidate.
- Final assertions: both declare exact1.14.0, locked package entries remain unchanged, clean tarball/update CLI version and strict behavior match the release-tested dependency.
- Conflict authority: existing tested pin in AGENTS.md and source lock; a different tool version or unrelated dependency change returns to authoring.
- Baseline policy: preserve immutable84d7190f dependency entries and baseline native evidence; provisional install/test failures are allowed only inside this candidate until all final assertions pass.
## Risks / Trade-offs
Do not mutate the live global install until a verified candidate exists. Temporary prefixes constrain installation writes. Keep the tested OpenSpec release and newer-surface downgrade protection; align manifest authority once the measured source-path difference establishes the repair.
## Open Questions
None.

## Verified repair decisions
F3 — npm11.19.0 installs the registry package with locked OpenSpec1.14.0 but fresh local tarball and actual updater install1.17.0 despite identical shipped lock. Public strict checks pass37/37 versus10/27. Basis: evidence/native-before.json. This resolves Q1.
D2 — Explicitly declare exact1.14.0 in package.json and lock root metadata, preserving every resolved dependency entry including patched Zod4.6.7. Basis: F3 plus existing AGENTS.md statement that Keel pins1.14 and the committed release-tested lock; this restores the existing tested dependency commitment. Do not upgrade OpenSpec or force a separate global downgrade.
D3 — Add real installed tarball and updater acceptance to Full-gate CI, separate from the existing offline-capable scenario suite. Use real npm in disposable prefixes; disable host plugin commands in the isolated update invocation. Compare public version and strict validation, not only files or npm exit. Basis: the former stand-in update tests could not detect F3.
D4 — Publish5.229.3, update authorized local installations, verify fresh registry and upgrade behavior and notify kaiwu. Basis: owner request to close #534; #527 remains deferred and #535 remains a later discussion.

## Why

A task's `Verify` block names the scenarios its checks will run. When one of those names is not registered, nothing says so until the check is executed — and a regression check that names an unregistered scenario cannot run at all, so the thing it claims to protect is unprotected while the contract reads as if it were covered.

#51 records four authored contracts that named something which did not exist, three of them in two consecutive changes, each corrected only at execution time and each costing a reauthorization cycle. Two of the four are this class: `gate-diagnostics` and `target-surface-doctor`, both written as an `M5 (regression)` check asserting that named scenarios "stay green".

A fifth was found while reproducing, and #51 does not record it. `openspec/changes/archive/2026-08-01-the-name-is-not-the-thing/tasks.md:132` declares:

```
- M3 (regression): `tasks-template-validates` and every other caller of the template filler stay green
```

`git log -S"tasks-template-validates" -- scripts/validate_plugin.py` returns no commit, so that name has never been registered at any point in this repository's history. That check was recorded as passing. It could not have run.

Reproduced 2026-08-03 at 5.21.0: nothing in the suite, the gates, or `keel --check` reads a scenario name out of a `tasks.md` and compares it to the registry.

## What Changes

One validator scenario reads the `tasks.md` of every **active** change and fails when a scenario reference names something the registry does not hold, reporting the file, the line, and the name.

Two reference forms are recognized, and both were measured across the whole archive before being chosen:

- a name following `--scenario` — 113 references, none unregistered;
- a backticked lowercase token in a `Verify` `M<n>` check that asserts something "stays green" — 30 references, one unregistered, which is the fifth occurrence above.

Nothing else in a `tasks.md` is read as a scenario reference. The obvious wider rule — every backticked kebab-case token in a `Verify` check — flags 22 of 55 such tokens across the archive, because gate stages, diagnostic codes, skill names, capability names, and hook events are spelled the same way.

**No gate, no product behavior, and no interface changes.** The whole effect is one scenario in `scripts/validate_plugin.py`.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `keel-validation-runner`: gains the requirement that a scenario name written into an active change's task contract is checked against the registry, in the two forms measured to carry no false positives.

## Impact

- `scripts/validate_plugin.py`: one extractor function, one scenario, one registry entry.
- **Deliberately not done: the `Touch` path check.** #51's other candidate — `keel gate task-start` warning on a `Touch` path that does not exist — is left with the owner as Q1, with the measurement. Its two stated examples cannot both hold: a new file and a mistyped filename are the same shape on disk. Measured over the last 40 commits, the base rule fires on 11 legitimately added files and the refined rule on 5, four of them `openspec/specs/<new-capability>/spec.md` — the most routine new-directory pattern this project has — while neither fires on the one recorded `Touch` mistake, which named a file that exists.
- Risk: the check reads only active changes, so a scenario rename cannot turn archived history red. A reference written in neither recognized form is not checked; that is the price of zero false positives and is stated in the spec rather than hidden.
- No new dependency. No interface, protocol, timing, ordering, permission, or security boundary changes.

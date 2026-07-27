## MODIFIED Requirements

### Requirement: Gate results expose capsule and fingerprint evidence

The versioned machine-readable `task-start` result MUST include the capsule schema, normalized capsule, fingerprint, and diagnostics needed for the current agent to record a durable start anchor. When the caller explicitly passes `--record`, a passing `task-start` MUST write that anchor itself by replacing the selected task's `- Contract:` Evidence line with the compiled fingerprint line, whatever value that line currently holds, and MUST refuse deterministically — writing nothing — only when the selected task has no `- Contract:` line at all. The result MUST report which outcome occurred, and a re-record that replaces a different recorded fingerprint MUST warn that execution evidence produced under the previous contract is stale. Later task gates MUST report recorded-versus-current fingerprint status.

#### Scenario: Passing start exposes recording data
- **WHEN** `task-start` passes
- **THEN** its JSON includes `keel-task-capsule/v1`, the fingerprint algorithm and value, and the complete normalized contract
- **AND THEN** human-readable output identifies the fingerprint without dumping unnecessary capsule detail

#### Scenario: Explicit record replaces only the Contract anchor
- **WHEN** `task-start` passes with `--record` and the selected task's Evidence contains the line `- Contract: pending`
- **THEN** the gate replaces exactly that line with the compiled `keel-task-capsule/v1` fingerprint line consumed by the existing anchor read path, and reports the outcome as `recorded`
- **AND THEN** no other line of `tasks.md` changes, and the recompiled fingerprint is unchanged so any active guard stays valid

#### Scenario: Reauthorization replaces a recorded anchor and warns
- **WHEN** `--record` is passed and the selected task's `- Contract:` line already carries a fingerprint that differs from the freshly compiled one
- **THEN** the gate replaces that line with the new fingerprint line, reports the outcome as `rerecorded`, and carries the replaced value in the result
- **AND THEN** it warns that the previous contract's execution evidence is stale, naming the previous fingerprint, and no other line of `tasks.md` changes

#### Scenario: Re-recording an unchanged contract writes nothing
- **WHEN** `--record` is passed and the selected task's `- Contract:` line already carries exactly the freshly compiled fingerprint line
- **THEN** the gate reports the outcome as `unchanged` and leaves `tasks.md` byte-identical
- **AND THEN** it emits no stale-evidence warning, because the contract did not move

#### Scenario: Record without a Contract anchor refuses
- **WHEN** `--record` is passed but the selected task has no `- Contract:` Evidence line to anchor
- **THEN** `task-start` fails with a deterministic record refusal naming the missing anchor line and the literal form to add
- **AND THEN** it writes nothing, not even the guard manifest, and behavior without `--record` remains byte-identical to the pre-flag gate

#### Scenario: Completion sees contract drift
- **WHEN** the recorded start fingerprint differs from fresh compilation
- **THEN** `task-complete` fails with both values and the authority areas that changed when they can be determined deterministically
- **AND THEN** it does not accept otherwise complete Evidence

#### Scenario: Gates remain read-only
- **WHEN** a gate returns a capsule, fingerprint, or drift result
- **THEN** it stays read-only toward task authority: it does not clear evidence, repair the task, or accept new authority, and it does not write the start anchor unless the caller explicitly passed `--record`
- **AND THEN** the disposable guard manifest and the explicit `--record` anchor replacement, each written only by a passing `task-start`, are the only artifacts any gate may write

### Requirement: Gate execution is deterministic and write-bounded

Core gates MUST run locally without network access or model calls. The only permitted project writes are the disposable `keel-write-guard/v1` manifest written by a passing `task-start` on the Claude target when `--no-guard` is absent, and the single-line replacement of the selected task's `- Contract:` Evidence anchor performed by a passing `task-start` when the caller explicitly passes `--record` and the anchor does not already hold the compiled fingerprint line. `task-complete`, `change-close`, and every failing or `needs-review` outcome MUST NOT write project state. Gates MUST return `pass`, `fail`, or `needs-review` through one versioned machine-readable result.

#### Scenario: Passing gate is process success
- **WHEN** every deterministic requirement for a gate is satisfied
- **THEN** gate status is `pass`
- **AND THEN** the command exits successfully

#### Scenario: Policy non-pass is distinguishable
- **WHEN** a gate detects a contract failure or required semantic review is absent
- **THEN** status is `fail` or `needs-review`
- **AND THEN** the process result is nonzero and distinguishable from an operational error

#### Scenario: Gate does not mutate evidence
- **WHEN** a gate evaluates task or change state
- **THEN** it does not mark tasks complete, write Review evidence, update HANDOFF, or repair artifacts
- **AND THEN** the guard manifest and the explicit `--record` Contract-anchor replacement, each written only by a passing `task-start`, are the sole exceptions to gate write-freedom

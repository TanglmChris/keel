## MODIFIED Requirements

### Requirement: Gate results expose capsule and fingerprint evidence

The versioned machine-readable `task-start` result MUST include the capsule schema, normalized capsule, fingerprint, and diagnostics needed for the current agent to record a durable start anchor. When the caller explicitly passes `--record`, a passing `task-start` MUST write that anchor itself by replacing the selected task's `- Contract:` Evidence line with the compiled fingerprint line, whatever value that line currently holds, and, before anchoring, MUST add to the selected task's Evidence every record slot its compiled capsule implies and the Evidence lacks — `Contract`, each bare `M<n>`, `.red` and `.green` for each red-green check not tagged `(regression)`, `.detects` for each check declaring `Detects:`, a Review block with `Status`, `Acceptance check`, `Scope check`, and `Findings`, `Blocker: none`, and `Reauthorizations: none` — each reading `pending` unless named otherwise, without rewriting an existing line or touching any other task or field. When the task does not compile apart from its missing slots, the gate MUST refuse and write nothing. The result MUST report which outcome occurred, and a re-record that replaces a different recorded fingerprint MUST warn that execution evidence produced under the previous contract is stale. Later task gates MUST report recorded-versus-current fingerprint status.

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
- **WHEN** `--record` is passed for a task that has no `- Contract:` Evidence line and also declares no `Strategy:` in its Verify
- **THEN** `task-start` fails with the strategy diagnostic rather than filling slots around an authoring error
- **AND THEN** it writes nothing, not even the guard manifest, and behavior without `--record` remains byte-identical to the pre-flag gate

#### Scenario: Record fills a task's missing record slots
- **WHEN** `--record` is passed for a valid `vertical-tdd` task with checks `M1` and `M2 (regression)` whose Evidence is absent
- **THEN** the gate adds an Evidence block with the recorded Contract line, `M1`, `M1.red`, `M1.green`, `M2`, a pending Review with its four fields, `Blocker: none`, and `Reauthorizations: none`, and reports the outcome as `recorded`
- **AND THEN** no line outside that task's Evidence changes, and running the same command again leaves `tasks.md` byte-identical

#### Scenario: Record keeps what the author already wrote
- **WHEN** `--record` is passed and the task's Evidence already carries a concrete `M1` result but no `M1.red`
- **THEN** the gate adds only the missing slots and leaves the `M1` line unchanged

#### Scenario: Without record, missing slots are named with the fix
- **WHEN** `task-start` runs without `--record` for a task lacking an `M<n>` Evidence line
- **THEN** it fails with `evidence-label-mismatch`, and the message names `--record` as the way to add the missing slots

#### Scenario: Completion sees contract drift
- **WHEN** the recorded start fingerprint differs from fresh compilation
- **THEN** `task-complete` fails with both values and the authority areas that changed when they can be determined deterministically
- **AND THEN** it does not accept otherwise complete Evidence

#### Scenario: Gates remain read-only
- **WHEN** a gate returns a capsule, fingerprint, or drift result
- **THEN** it stays read-only toward task authority: it does not clear evidence, repair the task, or accept new authority, and it does not write the start anchor unless the caller explicitly passed `--record`
- **AND THEN** the disposable guard manifest and the explicit `--record` anchor replacement, each written only by a passing `task-start`, are the only artifacts any gate may write

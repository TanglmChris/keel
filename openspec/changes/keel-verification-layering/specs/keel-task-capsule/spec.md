## MODIFIED Requirements

### Requirement: Verification strategy and evidence labels are connected
Every executable task capsule MUST contain one supported verification strategy and one or more unique, ordered `M<n>` checks that can prove the resolved Acceptance through a public interface or an explicitly authorized evidence alternative. A check MAY carry an optional `(fast)` or `(full)` verification-layer tag written immediately after its `M<n>` label; an untagged check is `full`. The tag is declarative metadata that records which checks belong to the fast inner loop and MUST NOT change red-green evidence rules or what `change-close` requires — every `M<n>` still needs its Evidence.

#### Scenario: Behavioral strategy requires behavioral proof
- **WHEN** a task uses vertical-tdd, regression-first, characterization, snapshot-characterization, or rendered-behavior
- **THEN** its checks and Evidence identify the behavior exercised and the public interface used
- **AND THEN** build-only, signature-only, collection-shape-only, or self-mocked evidence does not satisfy the capsule

#### Scenario: Red and green evidence use the same check
- **WHEN** the selected strategy requires red-green execution
- **THEN** Evidence records the applicable `M<n>.red` and `M<n>.green` outcomes for the same behavior check
- **AND THEN** the task cannot complete with green-only evidence unless an explicit, authorized characterization rationale applies

#### Scenario: Evidence-first is explicit
- **WHEN** a docs, configuration, diagnosis, or other non-behavioral task cannot use a meaningful red-green loop
- **THEN** the capsule uses `evidence-first`
- **AND THEN** its checks state the observable artifact or diagnosis evidence that proves Acceptance

#### Scenario: Checks may declare a verification layer
- **WHEN** a check is written with a `(fast)` or `(full)` tag after its `M<n>` label
- **THEN** the compiled capsule records that check's verification layer, and a check with no tag compiles as `full`
- **AND THEN** the tag does not alter the check text, its Evidence label mapping, or the red-green and change-close requirements

## ADDED Requirements

### Requirement: Foreground and background preserve owned execution identity
Keel MUST support verified serial foreground and background work on the same owned thread without duplicate writers, replacement identities or lost delivery claims. Explicit thread policy and safe restoration of an owned worktree MUST retain sandbox and approval boundaries. Merely listing a thread MUST NOT count as foreground/background acceptance.

#### Scenario: Desktop work and addressed background delivery alternate
- **WHEN** real foreground input and background delivery target the same owned thread
- **THEN** their accepted work executes serially with retained history and no repeated addressed record

#### Scenario: Foreground changes the owned worktree
- **WHEN** current thread cwd differs from its recorded owned worktree
- **THEN** normal delivery refuses until an explicit verified recovery preserves thread id, history and claims

#### Scenario: Explicit managed thread reviewer is persistent without warm-up
- **WHEN** a caller starts a managed role with an explicit user or auto_review reviewer
- **THEN** Keel persists that reviewer on the owned native thread before success, retains on-request and workspace-write, and preserves it through cold delivery and handover without a hidden model turn or global policy edit
- **AND** invalid policy requests fail before stateful RPCs while persistence failures retain the original pending thread identity without automatic replacement

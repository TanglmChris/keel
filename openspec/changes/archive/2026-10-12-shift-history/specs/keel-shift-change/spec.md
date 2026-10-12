## ADDED Requirements

### Requirement: A cleared shift's conversation stays findable

The chat hooks of a session bound to a role MUST record each transcript file it runs in, `keel shift history` MUST also find the Claude transcripts already kept for the role's bound worktrees, leaving out scheduled runs, with when it started and when the next replaced it, and MUST undo that record for a host-run session. `keel shift history [<role>]` MUST list the role's transcript segments and past shift notes, newest first, and with `--grep <text>` MUST print matching conversation lines per segment and exit 1 when nothing matches. `ready` MUST say the conversation stays findable, and the clear hint MUST say to turn Remote Control off before clearing.

#### Scenario: The previous shift's transcript is found after a clear
- **WHEN** `verify`'s session runs in transcript A, is cleared into transcript B, and a scheduled run starts in transcript C in the same worktree
- **THEN** `keel shift history verify` lists B as current and A as ended, does not list C, and `keel shift history verify --grep <a phrase said in A>` prints that phrase under A

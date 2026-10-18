## MODIFIED Requirements

### Requirement: A cleared shift's conversation stays findable

The chat hooks of a session bound to a role MUST record each transcript file it runs in, `keel shift history` MUST also find the Claude transcripts already kept for the role's bound worktrees, leaving out scheduled runs, with when it started and when the next replaced it, and MUST undo that record for a host-run session. `keel shift history [<role>]` MUST list the role's transcript segments and past shift notes, newest first, and with `--grep <text>` MUST print matching conversation lines per segment, from Claude transcripts and Codex rollouts alike, and exit 1 when nothing matches. When a role's session starts a new transcript, the hook MUST copy each ended segment's transcript that exists and has no up-to-date copy into Keel's store as gzip-compressed bytes under `shift/transcripts/<role>/`, which the chat archive does not sync, and MUST NOT copy the current segment. When a segment's own file is gone, `history` MUST read Keel's copy, mark the segment `(kept)` rather than `(missing)`, and `--grep` MUST search the copy. `ready` MUST say the conversation stays findable, and the clear hint MUST say to turn Remote Control off before clearing.

#### Scenario: The previous shift's transcript is found after a clear
- **WHEN** `verify`'s session runs in transcript A, is cleared into transcript B, and a scheduled run starts in transcript C in the same worktree
- **THEN** `keel shift history verify` lists B as current and A as ended, does not list C, and `keel shift history verify --grep <a phrase said in A>` prints that phrase under A

#### Scenario: A shift's conversation outlives the host's file
- **WHEN** `verify`'s session runs in transcript A, is cleared into transcript B, and A is then deleted
- **THEN** Keel's store holds a gzip copy of A under `shift/transcripts/verify/` and none of B, `keel shift history verify` lists A as `(kept)`, and `keel shift history verify --grep <a phrase said in A>` prints that phrase under A

#### Scenario: A Codex rollout is searched
- **WHEN** a role's segment is a Codex rollout file whose user message contains a phrase
- **THEN** `keel shift history <role> --grep <that phrase>` prints it under that segment

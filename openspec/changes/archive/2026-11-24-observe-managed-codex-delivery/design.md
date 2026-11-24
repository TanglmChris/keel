## Decisions

- D1 — `keel codex status --role <role> --record <id> --observe --json` projects the outcome of the original thread and turn from the local receipt. Read the owned worktree and recorded endpoint, then require matching thread ID and cwd and the exact turn ID. For pending, unrecorded or old receipts without both identities, return unknown without an RPC. Keep existing offline output when the flag is absent.
- D2 — Report usage exhaustion only for a failed turn with native `usageLimitExceeded`. An ordinary failure or generic HTTP 429 remains failed. Bind the terminal inventory to the same native thread and keep present, none observed and unknown distinct. A partial empty inventory or unavailable API yields unknown.
- D3 — The command initiates only read RPCs. Reporting an outcome or an empty inventory does not acknowledge writer release, verify task completion or authorize replay. A full query holds no mutating lock. Observations are a point-in-time read.

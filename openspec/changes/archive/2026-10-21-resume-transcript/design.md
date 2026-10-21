## Decisions

- **D1** — Prefer the existing transcript. `hookLocation` checks that the payload's `transcript_path` exists before using it.
  - If it exists, it works as it does today.
  - If it does not, and `session_id` is a plain id, the hook looks for `<config>/projects/*/<session_id>.jsonl`. `<config>` is `CLAUDE_CONFIG_DIR` or `~/.claude`, the same root `hostTranscript` uses.
  - It uses the first match's project directory.
  - If nothing matches, it falls back to the reported `cwd`, as today.

  `~/.claude/jobs/<id>/state.json` records `worktreePath`, but it is host-internal state. The transcript location is what Keel already reads.
- **D2** — Evidence. `chat-hook-follows-session-worktree` gains a case built from the measured payload:
  - `source: resume`;
  - `cwd` set to rtl's worktree;
  - `transcript_path` pointing into rtl's project directory, where the file does not exist;
  - the real `<id>.jsonl` placed in verify's project directory under a scratch `CLAUDE_CONFIG_DIR`.

  The session must be recorded as verify's and watch verify's signal.
- **D3** — The contract page. `docs/host-contract.md` updates its "Resumed after being started with `claude --bg -w`" row. The row records that both `cwd` and `transcript_path` name the launch directory, and that the transcript file stays in the worktree project. The evidence is the 2026-10-21 probe and the scenario.

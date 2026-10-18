## Context

#343 left five questions; the owner settled them on 2026-10-18: copy when the next segment starts; keep it local; raw JSONL, gzip-compressed; keep everything; cover Codex too.

## Facts

- F1 — `recordSegment` (`src/core/chat/notice.js`) runs on SessionStart and UserPromptSubmit, returns at once while the transcript is the current one, and on a new transcript marks the previous segment `ended` and appends the new one. A host-run session later restores the segments file it replaced (#304 D2).
- F2 — `SYNCED_ROOTS` in `src/core/chat/archive.js` is `groups`, `cursors`, `members`, `presence`; nothing under `shift/` leaves the machine.
- F3 — Measured 2026-10-18: keel-maint has 10 segments, 23.9 MB raw, 0.7–4.7 MB each; one 2.0 MB transcript gzips to 0.4 MB. `cleanupPeriodDays` is not set in `~/.claude/settings.json`.
- F4 — Measured 2026-10-18 with codex-cli 0.163.0: `codex exec` in a scratch repository bound to role `codex-probe` ran Keel's SessionStart and UserPromptSubmit hooks, and the role's segments file recorded `~/.codex/sessions/2026/10/18/rollout-…jsonl` as its transcript. Codex's hook schema types `transcript_path` as a nullable string; its docs call it "Path to the session transcript file, if any".
- F5 — A Codex rollout's messages are `{"type": "response_item", "payload": {"type": "message", "role": "user"|"assistant", "content": [{"type": "input_text"|"output_text", "text": …}]}}`; `grepTranscript` reads only Claude's `{"type": "user"|"assistant", "message": {"content": …}}`.

## Decisions

- D1 — On a segment change, `recordSegment` copies each ended segment whose transcript exists and whose copy is missing or older than the transcript (by size and modification time) to `shift/transcripts/<role>/<basename>.gz`, writing through a temporary file and a rename. The segment entry records `kept: <copy path>`. A failure is swallowed like every other hook convenience. The current segment is not copied: it is still being written.
- D2 — The copy is the transcript's bytes gzip-compressed, nothing removed. No redaction, because nothing leaves the machine (F2).
- D3 — `keel shift history` reports for each segment whether the host's file exists and whether Keel holds a copy; when the host's file is gone it reads the copy, and the line says `(kept)` instead of `(missing)`. `--grep` searches the host's file when present, else the copy.
- D4 — `grepTranscript` also reads Codex rollout message records (F5), user and assistant only.
- D5 — No cap and no pruning; deleting `shift/transcripts/` by hand is the way to reclaim space.

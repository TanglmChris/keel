## Facts

- F1 — `store.writeRecord` appends the record id to `signal/<role>` and to `signal/worktree/<sha16>` for each worktree bound to the role (chat-wake-late-binding D2); SessionStart of a bound session returns both in `watchPaths` (`src/core/chat/notice.js`).
- F2 — `hook()` for `file-changed` exits 2 with the full `noticeText` whenever `store.unread(where, role)` holds a record `store.wakes` accepts; it keeps no memory of what it already announced.
- F3 — Hook payloads carry `session_id` on the host; the existing scenarios (`chat-claude-hooks`) send none, and `sessionFile` already turns a valid id into `sessions/<id>.json`.
- F4 — `rememberSession` rewrites that session file at every SessionStart; `session-end` removes it.

## Decisions

- D1 — The memory is a directory `woken/<session id>/` under the chat store holding one empty file named by each waking record id announced to that session. A record is announced to a session only by the process that creates its file with the exclusive flag (`wx`); an `EEXIST` means someone announced it. Any other error counts as not claimed-by-another: the record is announced (fail open, as the hook does elsewhere), so a broken disk cannot silence a wake.
- D2 — `file-changed` claims each waking unread record in order; those it wins are the new ones. None won: exit 0 with no output. Some won: exit 2 and the notice lists only those, with the header saying how many are new and how many are unread in all.
- D3 — SessionStart removes `woken/<id>/` first (a resumed session has been told nothing) and then claims every waking record its context lists; UserPromptSubmit claims the ones its notice lists; SessionEnd removes the directory. `noticeText` takes an optional list of waking records to show and is unchanged without it.
- D4 — With no valid session id there is nothing to remember against: the hook behaves as before (F3).
- D5 — `keel chat notice` and `check` do not claim anything; they are asked by a person or scheduler, not by the host's watcher.

## Risks

- A session that never reaches SessionEnd leaves its directory; the files are empty and named by record ids, and the next SessionStart of that id clears them. Ids of sessions that never return stay, a few bytes each.

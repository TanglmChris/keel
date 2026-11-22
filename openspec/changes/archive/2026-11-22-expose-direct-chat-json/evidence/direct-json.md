## Public CLI regression evidence

On a fresh Git repository with linked sender and receiver worktrees and no rename map, the published behavior failed the new scenario: `AssertionError: unread lost canonical DM participants: None`. The original DM was present in unread with no mentions and already woke the target through the native wake predicate.

The corrected projection passes on the same ordinary DM, the silent DM and the ordinary group post across `chat unread --json`, direct/group `--peek --json`, and `chat show --json`. The canonical receiver changes from verify to check after the real public rename, and all three surfaces report that same identity. Snapshot comparison verifies prior log bytes and read cursors are unchanged by these reads. No-wake stays ineligible to wake, and a plain group record omits direct metadata.

The command also passed chat-role-rename, chat-core, chat-no-wake-post, chat-no-wake-dm and chat-wakes-without-no-wake. Six public CLI scenarios passed. Kaiwu run-once dedup and actual same-thread acceptance remain with Kaiwu #561 and Keel #552.

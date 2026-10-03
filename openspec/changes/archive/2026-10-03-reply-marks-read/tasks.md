# Tasks

## 1. An answered record stops being unread

- [x] 1.1 A reply or a `done` advances the actor's cursor to the record it answers
  - Covers:
    - keel-cross-host-mailbox / Cursors give every member their own unread state and receipts
    - D1
    - F1
  - Touch:
    - src/core/chat/store.js
    - scripts/validate_plugin.py
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-reply-marks-read` checks, in a scratch repository, that after `rtl` posts two `@verify` records and `verify` replies to the first with `keel chat post --reply-to`, `keel chat unread --json` for `verify` lists the second and not the first, and `keel chat show <first> --json` lists `verify` as a reader. It then checks that `verify` closing a later assigned `todo` record with `keel chat done <id>` removes that record from its unread records, and that a reply to a record behind the cursor leaves later unread records in place. Fails with: `chat-reply-marks-read:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3abe48fa953a7025f41f1b2be28781284def4237a330b43b6e4ffc68f29610ac
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-reply-marks-read` reports `chat-reply-marks-read scenario passed.` In a scratch repository, after `verify` replies to the first of two `@verify` records, `keel chat unread --json` lists only the second, and `keel chat show <first> --json` lists `verify` as a reader. After `verify` closes an assigned `todo` record with `keel chat done`, that record is no longer unread. A later reply to the first record leaves a newer `@verify` record unread.
    - M1.red: fail. Before the store change the scenario reported `chat-reply-marks-read: the replied-to record is still unread for verify: ['20261003T053627745Z-rtl-46f038', '20261003T053627828Z-rtl-a7d273']`, carrying the declared signature `chat-reply-marks-read:`.
    - M1.green: pass. The same scenario passes after `post` and `done` in `src/core/chat/store.js` advance the actor's cursor.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 213 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: M1 drives the public `keel chat post --reply-to`, `keel chat done`, `keel chat unread --json`, and `keel chat show --json` and asserts each clause of the modified requirement and its new scenario: the replied-to record leaves the poster's unread set, a later record stays in it, the poster appears in the receipts, `done` removes the closed `todo` record, and a reply to an older record does not move the cursor back or past newer unread records. Every command that replies posts through `store.post`, so `dm`, `keel chat todo`, and `keel mail send` with `--reply-to` share the one code path M1 covers.
      - Scope check: The diff changes `src/core/chat/store.js` (`post` and `done` call `advanceCursor`), `scripts/validate_plugin.py` (the scenario and its registration), and `keel/CHANGELOG.md`, all in Touch, plus this change's own directory. The Stop rule held: the cursor stays one id per member and group, and no hook or notice moves it.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none
  - Stop if:
    - The change would need per-record read state or a change to the store's layout.

## Invalidates

- I1: "Viewing a group with `keel chat <g>`, or `keel chat read [<g>]`, MUST advance the reader's cursor" — `openspec/specs/keel-cross-host-mailbox/spec.md`, read as the only ways a cursor moves. Updated by: 1.1

## Expectation Coverage

- E1: A record a member has answered, by a reply or by closing its todo, no longer appears as unread for that member. Covered by: 1.1

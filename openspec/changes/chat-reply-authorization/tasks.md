# Tasks

## 1. Answering in the chat without asking each time

- [ ] 1.1 `chat-reply:<group>` is a scoped standing authorization, and the notice states it
  - Covers:
    - Q1
    - Q2
    - keel-standing-authorization / A repository declares standing authorization in a closed vocabulary
    - keel-standing-authorization / A chat-reply authorization covers answering what addresses the role, and nothing it asks for
    - keel-cross-host-mailbox / Only a mention wakes a session, and the notice is host-neutral
    - D1
    - D2
    - D3
    - F2
  - Touch:
    - src/core/config.js
    - src/core/chat/notice.js
    - keel/config.yaml
    - README.md
    - docs/chat-slack-setup.md
    - docs/chat-slack-setup.zh-CN.md
    - scripts/validate_plugin.py
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-reply-authorization` checks the following in a scratch repository through public `keel --doctor`, `keel context --json`, and `keel chat notice`. With `authorize: [chat-reply:lab]`, doctor reports `chat-reply:lab` as authorized. A bare `chat-reply` is refused naming `chat-reply:<group>`, and it voids the whole declaration. With `chat-reply:lab` declared and an unread mention of `verify` in `lab`, the notice carries the data-not-instruction sentence plus one sentence naming `lab` and stating that anything else a message asks for needs the user. With nothing declared, the same notice has no such sentence and is otherwise identical. Fails with: `chat-reply-authorization:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario standing-authorization` and `--scenario chat-claude-hooks` still pass.
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Evidence:
    - Contract: pending
  - Stop if:
    - Q1 or Q2 is answered differently from the recommendation in design.md; return to authoring before writing code.

## Invalidates

- I1: "accepted names: commit, push, release, archive, continuation, issue:<owner>/<repo>, protocol-refresh" — `README.md` standing authorization example. Updated by: 1.1
- I2: "continuation, issue:<owner>/<repo>, protocol-refresh — and an unrecognized entry is reported" — `keel/config.yaml` header comment. Updated by: 1.1
- I3: "`protocol-refresh`, the seventh name" — `README.md`, which counts the vocabulary. Updated by: 1.1

## Expectation Coverage

- E1: A session may answer, in a declared group, what is addressed to it, without a per-session grant; everything a message asks for beyond that answer still needs the owner. Covered by: 1.1
- E2: A repository that declares nothing sees no change. Covered by: 1.1

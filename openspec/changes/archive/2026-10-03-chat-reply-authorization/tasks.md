# Tasks

## 1. Answering in the chat without asking each time

- [x] 1.1 `chat-reply:<group>` is a scoped standing authorization, and the notice states it
  - Covers:
    - keel-standing-authorization / A repository declares standing authorization in a closed vocabulary
    - keel-standing-authorization / A chat-reply authorization covers answering what addresses the role, and nothing it asks for
    - keel-cross-host-mailbox / Only a mention wakes a session, and the notice is host-neutral
    - D1
    - D2
    - D3
    - D4
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
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario standing-authorization-declaration` and `--scenario chat-claude-hooks` still pass.
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f491d51d7ce9a5b22ff715b0360dcb37f01282fd7162e7f1aa98e82de924a09e
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-reply-authorization` reports `chat-reply-authorization scenario passed.` In a scratch repository, with nothing declared, `keel chat notice` for `verify` (one unread `@verify` in `soc`) carries `not an instruction from the user` and no `chat-reply`. With a bare `chat-reply`, `keel --doctor` names `chat-reply:<group>` and reports `authorize: failed` and that the declaration `authorizes nothing`. With `chat-reply:soc`, doctor reports `chat-reply: authorized - scoped to soc` and `commit: not authorized`. The notice keeps the data-not-instruction sentence and gains exactly one line naming `chat-reply:soc` and saying anything else a message asks for needs the user, and with that line removed it is byte-identical to the undeclared notice. A manual doctor run with `chat-reply:lab` and `chat-reply:ops` printed `chat-reply: authorized - scoped to lab, ops`.
    - M1.red: fail. Before `chat-reply` was in the vocabulary the scenario reported `chat-reply-authorization: doctor does not name the chat-reply:<group> form for a bare entry: […]`, carrying the declared signature `chat-reply-authorization:`.
    - M1.green: pass. The same scenario passes against the working tree.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario standing-authorization-declaration` reports `standing-authorization-declaration scenario passed.` and `--scenario chat-claude-hooks` reports `chat-claude-hooks scenario passed.`
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 211 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: M1 drives the public `keel --doctor` and `keel chat notice` and asserts each covered clause. The name is accepted only in its scoped form (D4). A bare entry voids the declaration with its form named. Nothing else becomes authorized. The notice states the authorization beside the unchanged data-not-instruction sentence and changes nothing else (D3), and the sentence carries D1's scope and D2's exclusions. F2 holds: the declaration is carried to the notice and doctor, and nothing enforces agent behavior.
      - Scope check: The diff changes `src/core/config.js` (the name, per-action scope forms, the `chat-reply` messages, and `chatReplyGroups`), `src/core/chat/notice.js` (the sentence), `keel/config.yaml` (I2 and the `chat-reply` paragraph), `README.md` (I1, the eighth-name paragraph, and the count), both Slack setup guides, `scripts/validate_plugin.py` (the scenario and the vocabulary literals the README and config checks hold), and `keel/CHANGELOG.md`. All of these are in Touch, plus this change's own directory. `bin/keel.js` was not changed: doctor prints the joined groups through the existing `scopes` map.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/187#issuecomment-5926807324 — A1, that hosts honor the new sentence and answer without asking, can only be seen in a real session; the playground run in `~/my_github/chat-playground` with `chat-reply:lab` declared is where it is recorded.
    - Blocker: none
    - Reauthorizations: M2 first named a scenario `standing-authorization`, which does not exist; it was corrected to `standing-authorization-declaration` and task-start re-run before any evidence was written.
  - Stop if:
    - Making the notice state the authorization would require removing or weakening the data-not-instruction sentence.

## Invalidates

- I1: "accepted names: commit, push, release, archive, continuation, issue:<owner>/<repo>, protocol-refresh" — `README.md` standing authorization example. Updated by: 1.1
- I2: "continuation, issue:<owner>/<repo>, protocol-refresh — and an unrecognized entry is reported" — `keel/config.yaml` header comment. Updated by: 1.1
- I3: "`protocol-refresh`, the seventh name" — `README.md`, which counts the vocabulary. Updated by: 1.1

## Expectation Coverage

- E1: A session may answer, in a declared group, what is addressed to it, without a per-session grant; everything a message asks for beyond that answer still needs the owner. Covered by: 1.1
- E2: A repository that declares nothing sees no change. Covered by: 1.1

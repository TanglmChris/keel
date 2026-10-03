# Tasks

## 1. A scheduler can ask without paying for a turn

- [x] 1.1 `keel chat notice --check` exits 0 only when something addressed to the role is unread
  - Covers:
    - keel-cross-host-mailbox / A model-free check tells a scheduler whether to start a turn
    - D1
  - Touch:
    - src/core/chat/cli.js
    - src/core/chat/notice.js
    - scripts/validate_plugin.py
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-notice-check` checks, in a scratch repository, that `keel chat notice --check` produces no output on any path and exits with the right code. It exits 1 with nothing unread, 1 when the only unread record is `@all`, 0 with an unread `@verify`, 0 with an assigned `todo` record, and 0 with a direct message. Afterwards `keel chat unread --json` reports the same records. It also exits 1 outside any repository and in a worktree with no role. Fails with: `chat-notice-check:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:01ebd015fba06a362517d8ac2fb6ec2efc14482ff4a7a271eb5fc0443dbed509
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-notice-check` reports `chat-notice-check scenario passed.` In a scratch repository, `keel chat notice --check` writes no stdout or stderr on any path. It exits 1 with nothing unread and 1 when the only unread record is `@all`. It exits 0 with an unread `@verify`, and a second run leaves `keel chat unread --json` and every file under `keel-chat/` byte-identical. It exits 1 after `keel chat read`, 0 with an assigned `todo` record unread, 0 with a direct message unread, 1 outside any repository, and 1 in a repository with no role.
    - M1.red: fail. Before the switch existed the scenario reported `chat-notice-check: --check wrote output with nothing unread: 'keel chat: Unknown option for keel chat: --check'`, carrying the declared signature `chat-notice-check:`.
    - M1.green: pass. The same scenario passes against the working tree.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 211 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: M1 drives the public `keel chat notice --check` and asserts each clause of the requirement: it is silent, writes nothing (the whole store is compared byte for byte), exits 0 for each waking kind and 1 for a broadcast alone, and exits 1 outside a repository and with no role. Q1 was resolved as recommended, so `@all` exits 1.
      - Scope check: The diff changes `src/core/chat/cli.js` (the `--check` switch, routed before migration and presence so nothing is written), `src/core/chat/notice.js` (`check`), `scripts/validate_plugin.py` (the scenario), and `keel/CHANGELOG.md`, all of which are in Touch, plus this change's own directory. The Stop rule held: the check reads the local store only.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none
  - Stop if:
    - The check would need to write any file, or to call anything but the local store.

- [x] 1.2 The documentation steers hosts away from model polling
  - Covers:
    - D2
    - F1
    - F2
  - Touch:
    - docs/chat-slack-setup.md
    - docs/chat-slack-setup.zh-CN.md
    - docs/codex-validation.md
    - README.md
    - README.zh-CN.md
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: evidence-first
    - Reason: the change is guidance prose; its claims are checked against the shipped command and the session-log facts in design.md.
    - M1: each of the five documents states that the chat must not be polled with the model, and names the prompt-time notice as the path for hosts without idle wake. Each also says a schedule, when unavoidable, is gated by `keel chat notice --check` and starts a fresh thread per run, and that the text starting a chat session should say not to set up recurring checks. A one-off script greps each document for those four statements and checks that every `keel chat` command they name exists in `keel chat help`; its output is quoted in Evidence.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a3c170c182918b76d90a5a02568dbf90f293ecce8d5d3a43ce1deecd7ac25af1
    - M1: pass. `python3 openspec/changes/model-free-chat-check/evidence/check_docs.py "$PWD"` printed `checked 5 documents x 5 statements` and `failures: none`. It checks that each of `docs/chat-slack-setup.md`, `docs/chat-slack-setup.zh-CN.md`, `docs/codex-validation.md`, `README.md`, and `README.zh-CN.md` states that the chat must not be polled with the model, names the prompt-time notice, gates any schedule on `keel chat notice --check` with a fresh thread per run, and tells sessions not to set up recurring checks. It also checks that the command it names exists in `keel chat help`. A negative run against a copy with `recurring` removed from `docs/codex-validation.md` reported `docs/codex-validation.md: lacks no recurring checks at start` and exited 1, so the checker does detect a missing statement. Checker: artifact openspec/changes/model-free-chat-check/evidence/check_docs.py sha256:3f4bed1f92b50955ee959bf07081273966d5a608787c4e7c4644110d2d00c6ba
    - Review:
      - Status: pass
      - Acceptance check: D2's four statements appear in all five documents, in each document's language, and the only command they name is the one 1.1 shipped. Each document carries F1's facts (the minutely heartbeat appending to one thread, 1,277 runs, quota exhausted before the mention) in a form a reader can act on. F2's fact appears as the recommendation to rely on the prompt-time notice.
      - Scope check: The diff changes the five documents and `keel/CHANGELOG.md`, all of which are in Touch, plus this change's own directory, which holds the checker.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "每次回答前先运行 keel chat notice" — the kind of session-start text that produced the polling automation; it was given in chat, so no repository file carries it. Discard reason: no file holds this wording; 1.2 adds the guidance that replaces it.

## Expectation Coverage

- E1: A host that cannot wake on its own can learn, without a model turn, whether anything addressed to it is waiting. Covered by: 1.1
- E2: Hosts and people starting chat sessions are told not to poll with the model. Covered by: 1.2

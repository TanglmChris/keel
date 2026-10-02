# Tasks

## 1. A scheduler can ask without paying for a turn

- [ ] 1.1 `keel chat notice --check` exits 0 only when something addressed to the role is unread
  - Covers:
    - Q1
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
    - Contract: pending
  - Stop if:
    - Q1 is answered differently from the recommendation in design.md; return to authoring before writing code.

- [ ] 1.2 The documentation steers hosts away from model polling
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
    - Contract: pending

## Invalidates

- I1: "每次回答前先运行 keel chat notice" — the kind of session-start text that produced the polling automation; it was given in chat, so no repository file carries it. Discard reason: no file holds this wording; 1.2 adds the guidance that replaces it.

## Expectation Coverage

- E1: A host that cannot wake on its own can learn, without a model turn, whether anything addressed to it is waiting. Covered by: 1.1
- E2: Hosts and people starting chat sessions are told not to poll with the model. Covered by: 1.2

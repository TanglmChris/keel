## Context

`plugins/keel/scripts/session-start.js` computes the Keel projection and emits it as
`hookSpecificOutput.additionalContext`. That payload reaches the model only. The script's own
comment states the consequence: the projection "reaches nobody who can catch it being wrong."
Its mitigation is a `DISCLOSURE` phrase on every branch asking the agent to restate the state
in its first reply.

That mitigation has two gaps. It depends on the agent complying, and it produces nothing until
the human sends a first message — a human who opens a session and waits is told nothing. Issue
#32 reports the second gap as the observed failure.

Issue #32 proposes a `keel context --statusline` segment. Its author has since rejected that
direction: a status bar shows state, and the need is to be told the next action. This design
takes the other channel instead.

## Goals / Non-Goals

**Goals:**

- The human is told the Keel state and next action at session start, without sending a message
  and without depending on the agent restating anything.
- Every branch that produces a projection also produces the human line, degraded branches
  included, so a broken hook is visible rather than silent.
- The hook keeps exit 0, never blocks, never writes state.

**Non-Goals:**

- `terminalSequence` (OSC notification or terminal title). Deferred until the plain channel is
  confirmed rendering.
- The `keel context --statusline` segment from issue #32.
- Any change to `keel context` output, `schemaVersion`, or the `additionalContext` payload.
- Removing `DISCLOSURE`. The two channels are complementary: `systemMessage` tells the human,
  `DISCLOSURE` keeps the agent accountable for acting on the same state.

## Decisions

- **F1** — Claude Code 2.1.220's common hook-output schema declares
  `systemMessage: v.string().describe("Warning message shown to the user").optional()`
  alongside `continue`, `suppressOutput`, `stopReason`, `decision`, and `reason`.
  Basis: `grep` of `bin/claude.exe` in the installed
  `@anthropic-ai/claude-code` 2.1.220 package, 2026-07-28.

- **F2** — `systemMessage` and `additionalContext` are consumed by the same generic hook-output
  loop, with no observed gating by hook event: `if (j.systemMessage) { ... yield { message:
  qa({ type: "hook_system_message", ... }) } } if (j.terminalSequence) ... if
  (j.additionalContext) ...`. Since SessionStart already reaches this loop through
  `additionalContext`, `systemMessage` is available to it.
  Basis: same binary read, 2026-07-28.

- **D1** — The human line ships as top-level `systemMessage` on the existing single JSON emit,
  not as a second hook, a second process, or stderr. Basis: F1/F2 make it one field on an
  object the script already writes; no new spawn and no new failure mode.

- **D2** — The human line is one line, independent of the model payload's length, and names the
  state plus the next command. Basis: it renders as a warning-styled system message, not a
  document; a human scanning at session start needs the pointer, and the model already has the
  full projection.

- **D3** — Rendering is confirmed by smoke check in a real session before the specs and
  validator scenarios harden. Basis: F1 and F2 come from a compiled binary, not published
  documentation, and resolve Q1.

- **D4** — The fallback branches carry the human line too. Basis: the reported failure mode is
  a silent hook; a fallback that stays silent to the human reproduces exactly the bug this
  change exists to fix.

- **D5** — The human message opens with a three-line owl mark drawn only from the block-element
  range `U+2580–U+259F`, the same family the host's own startup banner uses:

  ```
  ▙▖▛▀▜  ▛▀▜▗▟
    ▌█▐  ▌█▐
    ▙▄▟▚▞▙▄▟
  ```

  Basis: requested by the user, who selected this form against a reference logo and asked for
  angular rather than rounded shapes. An owl is not decoration here — the keel is the carina,
  the ridge on a bird's sternum, so the animal that literally has a keel is a bird. Restricting
  the charset matters more than the shape: characters in this range are East-Asian-Ambiguous
  width, and the host banner already renders correctly on the target terminal, so reusing that
  exact family is what keeps the mark from misaligning under a CJK locale.

- **D7** — The mark and status sit inside a titled box modelled on the host's own welcome panel:
  a `╭─── Keel ───…───╮` top rule, `│ … │` body rows, and a `╰───╯` bottom rule, with the mark
  centred. Basis: requested by the user, who named that panel as the reference. The box adds a
  second charset, `U+2500–U+257F`; the same evidence that settled D5 covers it, since the host's
  welcome panel draws its own border from that range and renders correctly on the target
  terminal, which task 2.2's M3 confirmed for the block range on the same machine.

- **D8** — The box width is the longest content line, computed per message, and content is never
  truncated. Basis: a fixed width would have to truncate the change name, and the change name is
  the single most useful thing in the projection — truncating the payload to preserve the frame
  inverts what the frame is for. The cost is that the box width varies between sessions, which is
  cosmetic; the cost of the alternative is losing the identifier the user is trying to read.
  A box also converts a one-cell width error from a cosmetic skew into visibly broken output, so
  the width computation is asserted rather than assumed.

- **D9** — The frame and mark are opt-in through `KEEL_SESSION_PANEL`, and the single-line human
  message is what ships on by default. Basis: the user judged the panel's visual effect
  uncertain and asked for it off by default, while the single-line form is the one they
  confirmed solved the reported problem. The split follows what each part earns: the human line
  answers "nobody told me anything at session start" and is the change's reason for existing;
  the panel is presentation, and presentation that appears unbidden in every session of every
  installation should be chosen rather than inherited.

  This gates decoration only, so no requirement changes. The ADDED requirement asks for a
  human-visible message carrying status, selection, and next command, and the default
  single-line form satisfies it exactly as the panel does — which is the practical proof that
  D6 was worth enforcing. The variable is read through an explicit allowlist (`1`, `true`, `on`,
  `yes`) so a typo leaves the default in place rather than silently enabling.

- **D6** — The mark is decorative and MUST NOT be load-bearing. The status, selection, and next
  command stay on their own line, so a host that strips or collapses newlines still yields a
  message that reads correctly. Basis: Q2 is unresolved, and a projection whose meaning depends
  on newline handling would fail exactly where this change is supposed to hold — the degraded
  path.

## Hidden Knowledge / Assumptions

- **A1** — A host that does not recognize `systemMessage` ignores the unknown field and keeps
  today's behavior, rather than rejecting the whole hook output. Basis: the field is optional
  in the host's own schema, and the emit remains valid JSON with the `hookSpecificOutput`
  contract unchanged. Resolve by: task 1 smoke check observes whether the `additionalContext`
  projection still arrives intact when `systemMessage` is present.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- **The channel is read from a compiled binary.** If `systemMessage` does not render on
  SessionStart, the change's premise is void. Mitigated by D3: task 1 is the smoke check, and
  its Touch is one file, so reverting is a single-file revert.
- **Warning styling.** The host describes the field as a warning message, so a routine `idle`
  projection may render with warning affordances. If that reads as alarming, the mitigation is
  wording, not mechanism, and it is decided against what task 1 actually renders.
- **Message fatigue.** A line on every session start, including `idle`, is a cost. Accepted:
  the reported complaint is silence, and an `idle` line is what tells the human the hook ran.

## Open Questions

- **Q1** — Does `systemMessage` render to the human on a SessionStart hook in Claude Code
  2.1.220, and is its styling acceptable for a routine status projection?
  Basis: F1 and F2 establish the schema and the shared handler, but no observed render.
  Resolve by: task 1, whose Acceptance is the observed render in a fresh session. No later
  task may be selected while Q1 is unresolved.
  **Resolved by task 1.1 on 2026-07-28**: it renders, prefixed by `<hookEvent>:<source> says: `,
  with no warning affordance.

- **Q2** — Does the host preserve newlines inside `systemMessage`, so a multi-line mark renders
  as three aligned rows rather than one collapsed line?
  Basis: task 1.1 confirmed only a single-line message. The observed `says: ` prefix means the
  first row would begin mid-line even when newlines survive, so the message must open with a
  newline for the mark to align.
  Resolve by: task 2.2, whose Acceptance is the observed multi-line render. D6 bounds the
  blast radius if the answer is no: the mark is dropped, the message keeps its meaning, and no
  other task is affected.
  **Resolved by task 2.2 on 2026-07-29**: newlines survive, the three rows render aligned, and
  the ear tufts hold their columns on a Chinese-locale terminal — so the ambiguous-width
  reasoning behind D5 is observed rather than argued. The pre-authorized fallback was not
  needed. D9 later made the panel opt-in for a separate reason: the render works, and the user
  judged its effect not worth imposing by default.

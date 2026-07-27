## Context

Keel projects session continuity through one plugin script,
`plugins/keel/scripts/session-start.js`, shared by the Codex and Claude
SessionStart hooks. The script emits its text inside
`hookSpecificOutput.additionalContext`. That field is injected into the
agent's context; the host does not render it in the terminal. The user
therefore never sees the projection, and today nothing asks the agent to
relay it.

This was found by direct observation rather than by reading code. A session
began, the hook fired, the projection landed in context verbatim, and the
user still had to type a question to learn that the repository was idle.

## Goals / Non-Goals

**Goals:**

- The projected context is stated to the user in the agent's first response,
  on every branch the projection can take.
- The rule survives the plugin being absent, in this repository at least.
- The projection keeps its current character: bounded, disposable,
  non-blocking, authority-free.

**Non-Goals:**

- Making the hook write to the terminal. `additionalContext` has no
  user-visible channel, and SessionStart hook stdout is not surfaced as
  output. There is no fix available on the hook side.
- Editing `assets/bootstrap/AGENTS.md`. Its budget is exhausted and that
  wedge is separately owned.
- Any change to what the projection computes. Only the instruction attached
  to the result changes.

## Decisions

F1 — The SessionStart hook runs correctly and its output reaches only the
model. Basis: observed 2026-07-27 in a live Claude Code session; the injected
text matched `session-start.js` lines 138 to 147 verbatim, and the user
reported seeing nothing.

F2 — The consumer bootstrap cannot absorb another sentence. Basis: the
managed block in `assets/bootstrap/AGENTS.md` is 1017 bytes against the hard
sub-1024-byte assertion at `scripts/validate_plugin.py:9978`; the 12-line
budget is not the binding constraint, the byte budget is.

F3 — The projection's branches are the ready branch and one shared
non-ready branch, plus the `fallback` helper for CLI and Core failures.
Basis: `session-start.js` control flow; `fallback` is called for missing or
incompatible CLI, failed or empty `keel context --json`, and malformed
output.

F4 — The resident `AGENTS.md` Session Start section instructs the agent to
run `keel context` and follow its result, and says nothing about telling the
user. Basis: the file's Session Start section as of this change.

F5 — The `native-plugin-session-start` validator scenario already exercises
both the ready branch and the ambiguous branch and asserts on their emitted
text. Basis: `scripts/validate_plugin.py`, `validate_native_plugin_session_start_scenario`.

D1 — The report obligation is delivered through the projection text and this
repository's resident protocol, and not through the consumer bootstrap.
Basis: the projection reaches every repository that has the plugin at the
exact moment the obligation applies and costs no resident budget, while the
bootstrap is byte-wedged per F2; the resident rule covers the case where the
plugin is absent or was not loaded, which has happened here before. Accepted
by the user after being offered the bootstrap-inclusive alternative.

D2 — One short line per branch, not a paragraph. Basis: the projection
competes for attention with the pointer it carries, and a verbose disclosure
rule would crowd out the selection it is meant to disclose.

D3 — Reporting is a disclosure obligation and confers no authority. Basis:
the existing requirement that native projection is one-way and disposable;
an instruction that made the agent act on the projection would convert a
disposable view into input authority, which the capability forbids.

D4 — Consumers without the native plugin do not receive this rule in this
change, and that residue is recorded as a follow-up rather than hidden.
Basis: F2 makes the bootstrap edit a different change with different risk;
stating the gap keeps the spec honest about its reach.

## Hidden Knowledge / Assumptions

A1 — An instruction placed in `additionalContext` is followed reliably
enough to be worth specifying. Basis: it is the same channel through which
the projection's existing `next:` instructions are already honored, and it is
the only channel available at all; the alternative is no rule. Resolve by:
observation in the next fresh session after this ships. Durable owner: the
user, who reported the original gap and will see whether the next session
opens with a status line.

## Coupled Iteration Contract

Not applicable. No task declares `Coupling: required`.

## Risks / Trade-offs

- A projection instruction is advisory, not enforced. Nothing in the gates
  can prove the agent actually spoke. Mitigation: the validator proves the
  instruction is present and reaches both branches, which is the part the
  repository can own; A1 owns the rest.
- Adding text to a context injection has a real cost in attention. Mitigated
  by D2.
- The resident rule and the projection text can drift apart. Mitigation:
  both are asserted in the same validator scenario, so a change to one
  without the other fails the suite.

## Open Questions

None.

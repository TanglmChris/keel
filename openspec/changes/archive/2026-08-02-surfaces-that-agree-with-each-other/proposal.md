# Surfaces that agree with each other

## Why

Keel has several surfaces that answer questions about the environment it runs
in. Measured on this machine, 2026-08-02, three of them are wrong in ways that
each look exactly like working.

**`keel --doctor` calls an interpreter ok that the suite refuses.** It reports
`python3: ok - python3`. That `python3` is macOS system 3.9.6, and
`scripts/run_python.js` refuses it: "no Python 3.10 or newer was found — tried
python3 (3.9.6)". Two Keel surfaces answer the same question with opposite
verdicts, and the one a person runs deliberately to check their environment is
the one that is wrong. 5.11.0 fixed the runner and left the doctor stating a
green it had no basis for.

**The runner refuses while a usable interpreter is on PATH.** It tries `python3`
and `python`, and on macOS `python3` is the system 3.9. `python3.11` is
installed and on PATH; nothing looks for it. The refusal says "install a newer
Python, or point KEEL_PYTHON at one" to a reader who already installed one.

**Nothing can report that the version check is missing.** The SessionStart
version comparison shipped in 5.9.0. The plugin installed here is 5.7.1, so the
check is not present, and its silence is indistinguishable from three versions
agreeing — which is precisely what 5.9.0's D2 designed silence to mean. Measured
here: plugin 5.7.1, CLI 5.7.0, repository protocol 5.12.0, and no session said
anything. The check that reports a stale runtime is part of the stale runtime,
and this is not a defect that can be fixed inside it: an absent mechanism cannot
announce itself. What is always current is the repository — its resident
protocol text is read every session, from the working tree, by whatever runtime
is running.

**Authoring gives no signal when two tasks are one behavior.** Issue #41 records
`the-runtime-says-which-version-it-is`, whose tasks 1.1 and 1.2 declared an
identical Touch and the same red-green strategy, passed `task-start` and the
Slice Start Gate, and were not executable as split: implementing 1.1 alone broke
a shipping scenario, and once it was right, two of 1.2's three checks were
already green, leaving no honest red. They were merged mid-execution at the cost
of a reauthorization cycle the Slice Start Gate exists to make unnecessary.

## What Changes

- `keel --doctor` reports the interpreter it found *and the version it reported*,
  and calls it a problem when the suite would refuse it — the same minimum, read
  from one place so the two surfaces cannot drift apart again.
- The interpreter search tries versioned names (`python3.13` … `python3.10`)
  before giving up, so the refusal is issued only when no usable interpreter is
  installed. `KEEL_PYTHON` still wins outright.
- `keel context` states which Keel produced its answer, and the resident protocol
  instructs the agent to report that version beside the protocol version the
  repository declares. This is deliberately not another check inside the plugin:
  the repository is the only participant that cannot be stale, so the comparison
  that survives a too-old runtime is the one the repository asks for.
- `keel gate task-start` warns when another task in the same change declares an
  identical Touch set and a red-green strategy, naming the other task, and
  `keel-review-checklist` asks the matching question. A warning rather than a
  `needs-review`: the shape is a signal, not a verdict, a genuine vertical split
  can share files, and there is no way to acknowledge a `needs-review` — it
  would leave a legitimate split unstartable, which is worse than the problem.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-target-surface-diagnostics`: the interpreter check reports the version it
  found and agrees with the runner about what is usable; the search covers
  versioned interpreter names.
- `keel-stateless-continuity`: `keel context` names the Keel that produced its
  answer, and the protocol asks for it beside the declared protocol version.
- `keel-core-gates`: `task-start` prompts when two tasks in a change are shaped
  like one behavior.

## Impact

- `bin/keel.js` — the doctor's interpreter line; `keel context` version output.
- `scripts/run_python.js` — the candidate list and the shared minimum.
- `src/core/gates.js` — the identical-Touch prompt.
- `AGENTS.md` — the session-start reporting instruction.
- `scripts/validate_plugin.py` — scenarios for each.
- Risk: `task-start` gaining a `needs-review` path changes an exit code authors
  and any automation depend on. It is a prompt on a shape that is legitimate
  often enough that refusing would be wrong, so it must not block a change that
  has considered it.

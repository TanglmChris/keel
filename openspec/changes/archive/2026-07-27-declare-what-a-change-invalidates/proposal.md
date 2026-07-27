## Why

A change that fixes a behavior invalidates every statement that described the
old behavior, and nothing in Keel asks about it. Follow-up Ownership governs
work left undone; this is the opposite shape — statements left standing by work
that was done. No gate, spec, or checklist covers it.

On 2026-07-27 the repository shipped ten changes and five releases, and the
closing audit found stale statements produced by fixes made that same day. The
asymmetry in what got caught is the point: the misses were all in files that
merely mentioned the behavior, while the catches were files already held in
mind. Recalling by filename cannot work, because the text that rots is the text
you were not thinking about.

The cost grows with lateness. Four of that day's changes re-recorded their
capsule, at least twice because a documentation surface was discovered mid-task
and had to be pulled into Touch. Yet what a change invalidates is knowable while
tasks are being authored — the author already knows which behavior is changing.
It was late because nothing asked, not because it was unknowable.

## What Changes

- tasks.md gains a required `## Invalidates` section, checked by
  `keel gate task-start` so it exists before any task of the change executes
  and the affected paths enter Touch from the start rather than by
  reauthorization.
- Each entry carries a **searchable symptom phrase** — the wording a reader
  would grep for — alongside its location and a closure: `Updated by:` naming
  tasks, a `Durable owner:`, or a `Discard reason:`. The phrase is the load-
  bearing part: it turns "remember to update the docs" into an executable
  search.
- `- None.` remains a first-class answer, so a change that invalidates nothing
  says so in one line.

No breaking change to the capsule: the section lives beside
`## Expectation Coverage`, outside any task body, and does not enter the task
fingerprint.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-expectation-slice-evidence-gates`: the Task Authoring Gate additionally
  requires a change to declare the statements its own work invalidates.

## Impact

- `src/core/gates.js` — a new structural check in `taskStart`.
- `openspec/schemas/keel-spec-driven/templates/tasks.md` and its
  `assets/openspec/...` copy — the authored surface must show the section, or
  every scaffolded change fails its first `task-start`.
- `scripts/validate_plugin.py` — scenario coverage.
- `AGENTS.md` — the resident protocol names the section.
- Risk: a required section that authors cannot answer becomes ritual. Mitigated
  by making `- None.` legitimate and by asking at authoring time, when the
  answer is actually known.
- Explicit non-goal: `assets/bootstrap/AGENTS.md` is untouched. Its managed
  block has roughly seven bytes of headroom, and in a consumer repository that
  block is the only durable protocol carrier, so the gap is real and owned by
  https://github.com/TanglmChris/keel/issues/15 rather than smuggled in.
- Explicit non-goal: native agent memory. Keel's protocol states memory is
  never authority, and this change does not reach outside the repository. The
  same rot shape appears there, which is how it was found, but only repository
  text is in scope.

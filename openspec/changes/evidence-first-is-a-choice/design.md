## Context

Six of Keel's verification strategies are named, and the gates distinguish exactly two classes: red-green (`vertical-tdd`, `regression-first`) and everything else. `characterization`, `snapshot-characterization`, `rendered-behavior`, and `evidence-first` are indistinguishable to `task-complete`. The four differ only in what the author meant, and one of them is also what the compiler supplies when the author meant nothing.

## Goals / Non-Goals

**Goals:**

- The verification strategy is something a task declared, never something the compiler chose for it.
- Choosing the strategy with no red-green requirement is a claim the author states and a reviewer can disagree with.

**Non-Goals:**

- Judging whether a stated reason is true. A gate cannot, and pretending otherwise would make the line a formality.
- Changing what any strategy requires at `task-complete`. Red-green stays red-green; evidence-first stays evidence-first.
- Extending the requirement to `characterization`, `snapshot-characterization`, or `rendered-behavior`.
- Rewriting the historical corpus. The gates run on live changes and already refuse an archived one.

## Decisions

- F1 — `verification()` in `src/core/task-contract.js` resolves an absent `Strategy:` to `evidence-first` (`|| "evidence-first"`), and the compiled capsule reports `"strategy": "evidence-first"` with no problem and no warning. Basis: probed against the real gate through a fixture repository, 2026-09-07; the capsule JSON was read from `contract.capsule.verification`.
- F2 — Omitting the line is how a task opts out of red-green. A fixture with no `Strategy:` passes `task-start` and `task-complete`; the identical fixture declaring `vertical-tdd` fails `task-complete` with `vertical-tdd requires concrete M1.red Evidence`. Basis: same probe, both directions run.
- F3 — The verification strategy is not a documented default. `keel-task-capsule`'s inherited-defaults scenario lists implementation mode, current-agent ownership, base Read context, hard-stop autonomy, no coupling, read-only helper authority, no delegation, standard prohibitions, and derived Acceptance — and not the strategy. Where the capsule does supply a default for autonomy or delegation it MUST name the source; the strategy default names nothing. Basis: `openspec/specs/keel-task-capsule/spec.md`, read 2026-09-07.
- F4 — The scenario is named "Evidence-first is explicit" and scopes the strategy to work that "cannot use a meaningful red-green loop". Basis: same file.
- F5 — Corpus, six repositories, 1,127 tasks declaring a verification form: 961 declare a strategy, 166 do not, all of them in `chip_sec_flow`, the repository superseded by `chip_sec_flow_v2`. `evidence-first` is chosen 299 times of the 961 — 17% in `chip_sec_flow_v2`, 38% in Keel, 50% in `rtl_ppa_prj`, 89% in `dasauto`, 92% in `my_xhs`. Basis: parsed from every `openspec/**/tasks.md` in local clones, 2026-09-07.
- F6 — A `Reason:` line written under `Verify` today fails `task-start` as `Command entry must use an M<n> label`. Basis: probed against the real gate, 2026-09-07.
- D1 — `task-start` refuses a task that declares `Verify` or `Commands` but no `Strategy:`, naming the supported strategies. Basis: F3 makes the current fallback unauthorized by any spec, and F1/F2 make it consequential. The diagnostic reuses the shape of the unsupported-strategy refusal that already exists, so the two failures read alike.
- D2 — `evidence-first` requires a `Reason:` line under `Verify`, and `task-start` refuses one that is absent or a placeholder. Basis: owner decision, 2026-09-07, against F5. What the gate checks is presence and concreteness, never truth — the contract `Discard reason:` already has, and the reason a rote entry is still worth requiring: a sentence a reviewer can disagree with is a different object from a silent default.
- D3 — No exemption, `diagnose-only` included. Basis: owner decision, 2026-09-07. An exemption keyed on a field the same author writes is a second escape hatch — marking a task `diagnose-only` would become the way to skip the reason — and the first one is what this change exists to close.
- D4 — Only `evidence-first` carries the requirement. Basis: the other three non-red-green strategies are positively chosen for a named layer — deterministic output, a rendered interface, a recorded snapshot — and their name states what the evidence is. `evidence-first` is scoped by an absence, and an absence is exactly the claim that has to be stated to be reviewable.
- D5 — `Reason:` compiles as a `Verify` field beside `Strategy:`, not as a check. Basis: F6 — the parser treats every non-`Strategy:` entry under `Verify` as a command, so the field has to be recognized or the line cannot be written at all. It joins the compiled capsule's verification block, so it is inside the contract fingerprint and cannot be edited after `task-start` without reauthorization.

## Hidden Knowledge / Assumptions

- A1 — A live change carrying either refused shape is refused until its author declares what it meant, and the surveyed 465 tasks (299 `evidence-first`, 166 strategy-less) are archived rather than live. Basis: F5 counted archived and live tasks together and did not separate them; the gates refuse an archived change rather than recompiling one, so the archived majority cannot be reached by a gate at all. Durable owner: https://github.com/TanglmChris/keel/issues/112 — if a live change in a consuming repository is blocked by this, the upgrade note is where it is recorded.

## Risks / Trade-offs

- An author writes a rote reason and nothing improves. Accepted, and it is still not the status quo: the rote sentence is visible in the diff and in the Review, where a silent default was visible nowhere. `keel-review-checklist` is where a reader can call one out.
- One more required line on 31% of tasks. That is the intended cost: at 89% and 92%, writing the sentence forty-eight times is the signal.

## Open Questions

None.

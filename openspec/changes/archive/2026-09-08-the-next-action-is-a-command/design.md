## Context

`keel context` exists to answer "what now". It answers with a noun. The command that noun stands for is fully determined by the same result — the stage, the change, the task — and is not printed.

## Goals / Non-Goals

**Goals:**

- The answer to "what now" is something that can be run.
- An agent reading OpenSpec's installed instructions learns, in Keel's own block, which invocation resolves.

**Non-Goals:**

- Running the command. `context` reports and writes nothing.
- Editing OpenSpec-owned text. See D2.
- Translating arguments inside the `keel openspec` proxy. See D4.

## Decisions

- F1 — `context` builds `nextAction: { kind }` and prints `Next action: ${kind}`. The change and task it would apply to are in the same result. Basis: `src/core/context.js`, read 2026-09-08.
- F2 — `keel gate change-close --change x` fails with `change-close requires --action sync or --action archive`, and the usage line shows `[--action sync|archive]` on the line shared by all three gate stages. Basis: run and read, 2026-09-08.
- F3 — The overlay merge appends Keel's block to a file whose body is OpenSpec's; its own comment says "the file it is left in belongs to OpenSpec". Basis: `bin/keel.js`, read 2026-09-08.
- F4 — `keel --doctor` already reports when the resolved openspec is not reachable as a bare command and names `keel openspec` as the working invocation. Basis: doctor output, this repository.
- D1 — `context` reports a command string beside the action kind, in both text and JSON. Basis: F1 — everything needed is already in the result, and the failure the report describes is a wrong attempt Keel had the information to prevent.
- D2 — The invocation guidance goes in the Keel overlay, not in OpenSpec's text. Basis: F3. Editing upstream's body would make every `keel --init` a divergence from the instructions OpenSpec ships, and the next upstream change would collide with it. The overlay is Keel's own block in the same file and is read by the same agent.
- D3 — The guidance states the form and points at `keel --doctor` rather than asserting that bare `openspec` is absent. Basis: F4 — whether it resolves is a property of the installation, and doctor is the check that answers it. `keel openspec` is correct either way, which is why it is the form to print.
- D4 — Do not translate `--change` to a positional argument inside the proxy. Basis: `keel openspec` passes arguments through unaltered, and a proxy that accepted flags the proxied tool rejects would behave differently from it — a divergence a user discovers when a command that works through Keel fails when they run OpenSpec directly. The inconsistency belongs to OpenSpec's CLI.
- D5 — The usage line separates `change-close`'s required `--action`. Basis: F2 — one line covering three stages can only show a per-stage requirement as optional.

## Hidden Knowledge / Assumptions

- A1 — The printed command is what the reader should run, not merely what Keel would run. It therefore names `--change` and `--task` explicitly rather than relying on inference, even where inference produced the selection. Basis: a command that depends on inference reproduces whatever the repository looked like when it was printed, and the reader may run it later or elsewhere. Durable owner: https://github.com/TanglmChris/keel/issues/112

## Risks / Trade-offs

- A printed command can be run without reading the reasons above it. That is true of the action name too, and a wrong command is at least visible in the transcript where a wrong inference is not.
- The overlay grows by a line in five files. It is the block that already exists, and the line is the one thing an agent needs before running anything else in those files.

## Open Questions

None.

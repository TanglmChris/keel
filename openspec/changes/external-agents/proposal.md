## Why

Issue #219. Sessions in rtl_ppa_prj already hand work to the codex CLI, and this machine also has DeepSeek Harness (`dsh`). The general rules for calling an external model CLI live in that project's `docs/toolchain.md`, restating Keel's delegation rules, and every other project would have to restate them again.

The rules restated there are already Keel's: the calling session stays the only owner, a delegate's report is a claim the current agent re-verifies, and a delegate never completes a task (`keel-authorized-delegation`). Three things are missing:
- **The write guard does not reach an external process.** The guard is the host's PreToolUse hook, and a CLI the session launches writes without passing through it. The checkout the agent runs in becomes the write boundary.
- **Calling one sends the repository's content to another provider.** No project-level statement says what may leave.
- **The pitfalls are found once per project.** For example: no stdin hangs codex, a shared branch let one session overwrite another's commits, and a ten-hour autonomous run spent its time packaging 1.9 GB of evidence.

## What Changes

The owner's principle (2026-10-04): keep the model free to call what it wants, including its own subagents. Keel provides the calling interface and the registration, the basic flow and gates, and the pitfalls. A host's own subagents stay outside this change.

- A catalog of external agents. Keel bundles entries for `codex` and `dsh`, and a machine-local `~/.keel/agents.json` adds entries or overrides them by name. An entry records facts only: the command template, the sandbox it offers per mode, where it sends data, and dated pitfalls with their source. It names no task an agent suits.
- `keel agents [name] [--json]` lists the catalog on demand: where each entry came from, whether its executable resolves, and whether this project allows it. Nothing reaches session start.
- A project declares `external_agents:` in `keel/config.yaml`, with `allow:` naming the agents it permits and `egress_deny:` naming, with a reason, the paths that must not be sent. An absent declaration allows nothing.
- `keel agents brief <name> --mode helper|implementation --dir <path> --out <file>` compiles the same brief `keel project --event subagent-start` publishes, refuses it when a Read or Touch path matches `egress_deny`, writes it as a prompt file, and prints the filled command line. Keel spawns nothing; the session runs the command.
- An agent with no sandbox for the mode, and every implementation run, needs `--dir` to be a separate worktree of the same repository.
- The protocol names the command, and the privacy policy names the new channel.

## Capabilities

### New Capabilities
- `keel-external-agents`: the catalog, the project declaration, and the brief compiled for an external model CLI.

## Impact

New `src/core/agents.js` and its bundled catalog, `bin/keel.js` (the `agents` command), `src/core/config.js` (the `external_agents:` reader), `scripts/validate_plugin.py` (scenarios), `keel/config.yaml` header, `assets/bootstrap/AGENTS.md` and the managed protocol copies, both READMEs, `PRIVACY.md`, and the changelog. No gate, contract, or fingerprint changes. Implementation delegation keeps its guard precondition.

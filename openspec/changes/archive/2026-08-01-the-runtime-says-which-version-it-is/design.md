## Context

Keel's answers are worth trusting because its checks are local, deterministic, and reproducible. Which build produced them has never been stated anywhere.

On 2026-08-01 an installed plugin five minor versions behind the working tree enforced the old protocol for an entire session. The SessionStart projection ran, `keel context` ran, several gates ran, and everything looked normal. It surfaced only when a write the newer record layer permits was denied by the older hook — a coincidence, not a check.

## Goals / Non-Goals

**Goals:**
- The person and the agent both learn, at session start, when the runtime enforcing the protocol is not the protocol.
- The signal stays credible: it appears when something is wrong and stays out of the way when nothing is.
- Everything stays local, offline, and deterministic — the properties that make the rest of Keel's output worth reading.

**Non-Goals:**
- Keel does not install, update, pin, or resolve plugin versions. That is the host's, and stays the host's.
- Keel never asks what the newest release is. There is no network call, so there is no answer that differs on a plane and in CI.
- No new hook, event, or channel. This is the seam Keel already owns.
- L1 preflight self-checks, L2 cross-platform decoupling, and L3 alignment mechanisms are out of scope, tracked on issue #38.

## Decisions

**F1** — `plugins/keel/scripts/session-start.js` already runs `keel --version` and regex-matches it, then uses only the major number to reject a CLI older than 3. The full version string is already in hand and discarded. *Basis:* source read, 2026-08-01.

**F2** — The hook already emits both channels: `systemMessage`, rendered to the person without waiting for them to type, and `hookSpecificOutput.additionalContext`, injected into the model. Both already carry status, next action, and reason lines. *Basis:* source read; the human channel was added in 5.4.0 for exactly the reason that applies here.

**F3** — The hook returns 0 early when `openspec/` is absent, so it never speaks in a non-Keel repository. *Basis:* source read.

**F4** — Three versions are comparable in *any* repository: the plugin executing (`.claude-plugin/plugin.json` beside the hook), the CLI it invokes (F1), and the protocol stamped in the repository's managed block (`<!-- keel:start version=X.Y.Z -->`). A package version does not generalise — a consuming project has no Keel `package.json`. *Basis:* inspection of this repository and of the bootstrap `keel --init` writes.

**F5** — The drift observed on this machine was plugin 5.2.1, CLI 5.2.1, protocol 5.7.1. All three on one line would have made it obvious immediately. *Basis:* the session that produced issue #38.

**F6** — A session's hooks are pinned at start. `claude plugin update` reports "Restart to apply changes", so an updated plugin can remain unused for the rest of a session. *Basis:* observed 2026-08-01 — the update succeeded, the record-layer write stayed denied, and the same write succeeded after a restart.

**D1** — Keel **reports and does not manage**. No install, update, or version resolution. *Basis:* the scope rule promoted in 5.8.0 — a capability the target runtime provides natively is not Keel's to build. This change is where that rule is most tempting to break, because the obvious next sentence after "your plugin is stale" is "so let me update it", and the host already has `claude plugin update`.

**D2** — **Silence when aligned.** A matching set produces no line at all. *Basis:* owner decision, 2026-08-01. This diverges from issue #38's own wording, which proposed adding a line naming all three versions every session; the divergence is deliberate and recorded here so the issue is not read later as the authority it no longer is. A line printed every session stops being read within weeks, and this line exists to be noticed. The cost is accepted: confirming which version is running is then a question you ask rather than one already answered, and `keel --version` answers it.

**D3** — **Missing is not mismatched.** A version that cannot be discovered is reported as undiscoverable, and only when something else already requires a line; it never produces one on its own. *Basis:* D2's credibility argument runs both ways. A repository whose `AGENTS.md` carries no managed block is a normal state, not a fault, and a warning every session in that repository would train its reader to ignore the one that matters. The pairs that *are* discoverable are still compared — a missing protocol version does not stop the plugin and CLI being checked against each other.

**D4** — The comparison is **exact string equality on the three version strings**, not semantic version ordering. *Basis:* the question is "is the runtime the protocol", and any difference answers it. Ordering would invite a judgement about which direction is acceptable — newer plugin than protocol, older CLI than plugin — and every such judgement is a rule that has to be right. Equality has no such rule.

**D5** — The added work is one file read and one regex against a file the hook can already reach; the CLI version costs nothing new because F1 already fetches it. *Basis:* the hook runs on every session including post-compaction reinjection, under `KEEL_HOOK_TIMEOUT_MS` (default 8000ms). A second subprocess here would be paid on every session forever to answer a question that is usually "nothing to say".

**D6** — The mismatch is stated on **both** channels. *Basis:* F2 and 5.4.0's finding that a projection reaching only the model is invisible to the person who has to act on it. Updating the plugin is the person's action, so the person has to be told.

**D7** — The report names the **restart requirement** when it names a mismatch. *Basis:* F6. Without it the reader updates the plugin, sees the same warning, and concludes the check is broken.

## Hidden Knowledge / Assumptions

**A1** — The plugin's version is read from `.claude-plugin/plugin.json` relative to the hook's own location rather than from `CLAUDE_PLUGIN_ROOT`. *Basis:* the hook is executed as a path under the plugin root, so its own `__dirname` is the more direct fact and does not depend on the host exporting an environment variable. *Owner:* asserted in the scenario by running the hook with the variable unset.

**A2** — The Codex plugin manifest (`.codex-plugin/plugin.json`) carries the same version as the Claude one. *Basis:* the repository keeps them aligned and `version-alignment` asserts it as of 5.8.0. *Owner:* that existing scenario; this change reads whichever manifest sits beside the running hook rather than assuming which target it is.

## Coupled Iteration Contract

Not required. No task in this change declares `Coupling: required`.

## Risks / Trade-offs

- **A noisy check is worse than no check.** It would train its reader to skim past the one session where it mattered. D2 and D3 are both aimed at this, and the undiscoverable-versus-mismatched distinction is the single thing in this change most worth testing hard.
- **Silence has a cost** (D2): there is no passive confirmation of which build is running. Accepted by the owner; `keel --version` and `claude plugin list` both answer it on demand.
- **The check cannot see everything.** It compares three declared strings. A plugin whose files were edited in place still reports its manifest version, and nothing here detects that.

## Open Questions

None.

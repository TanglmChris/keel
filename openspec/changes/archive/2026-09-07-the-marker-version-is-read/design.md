## Context

`keel --doctor` is the model-free local diagnostic: it runs without a plugin, without a hook, without a model, and it is what a user runs when a repository feels wrong. It already reports a version disagreement of exactly this shape for OpenSpec — which build answered, what the repository pins, and why a green pipeline and a red worktree can both be true. It does not report the same thing for Keel itself.

## Goals / Non-Goals

**Goals:**

- Doctor states the repository's declared protocol version and the running CLI's version, and says plainly when they disagree.
- The report depends on nothing but the working tree and the running process.
- A missing or unreadable declaration is reported as such and never as agreement.

**Non-Goals:**

- Changing the marker format, the installer, `keel --check`, or any gate.
- Fixing the drift. Doctor reports; `keel --init` is what repairs.
- Replacing the SessionStart hook's three-way report. That check keeps its plugin term, which doctor cannot read in a consumer repository.
- Comparing against the newest version published to npm. Doctor is local and offline, and "your install is old" is a different question from "your repository and your install disagree".

## Decisions

- F1 — Neither local marker parser reads the version. `bin/keel.js:1342` and `scripts/install_to_repo.py:18` both match `<!--\s*keel:start(?:\s+[^>]*)?\s*-->`, discarding the attributes. Basis: read in the working tree, 2026-09-07.
- F2 — The only reader is the plugin. `plugins/keel/scripts/session-start.js:148` extracts the marker version and `:163` `versionReport()` compares plugin, CLI, and marker. Basis: read in the working tree, 2026-09-07.
- F3 — Whether that reader runs is unverified on every target. Doctor reports `native plugin runtime: manual` and each capability line repeats that installation, enablement, trust, and activation need runtime evidence. Basis: `node bin/keel.js --doctor` output, 2026-09-07.
- F4 — Four consumer repositories drifted undetected: `chip_sec_flow_v2` 5.14.0, `my_xhs` 5.20.0, `rtl_ppa_prj` 5.39.0, `dasauto` 5.39.0, against 5.47.0. Basis: corpus survey of this account's repositories, 2026-09-06, recorded in the upgrade issue filed on each.
- D1 — Doctor compares two terms, not three: the marker version and the running CLI's version. Basis: both are available in every repository on every target. The plugin's version is the third term of F2's report, but in a consumer repository the plugin lives outside the tree and doctor cannot read it; a report that silently drops a term in the common case is worse than one that never claimed it.
- D2 — Drift is a `warning` and leaves doctor's exit code unchanged. Basis: a drifted install is out of date, not broken, and doctor's exit code is consumed by pipelines; turning them red on release day would make the check something users disable. The standing-authorization surface is the existing precedent for a line that *can* fail the exit code, and it fails because a missing authorization makes a documented action unavailable — drift makes nothing unavailable.
- D3 — The message names the direction and the remedy for that direction. Basis: the two directions have different repairs. CLI ahead of marker means the package was updated and the repository was not — `keel --init --target <target>`. Marker ahead of CLI means the repository carries a protocol this install cannot enforce — update the Keel package. A message that reported only "they differ" would leave the reader to work out which, and the wrong repair is a no-op that looks like a failure.
- D4 — An absent marker, or one with no readable `version=`, reports `not comparable` and names which term was missing. Basis: F2's own comment — "Missing is not mismatched. A version nobody can discover never produces a" mismatch — and the same reasoning applies here. Reporting `ok` for an unreadable declaration is the failure mode this change exists to remove.

## Hidden Knowledge / Assumptions

- A1 — A repository may pin an older protocol on purpose, and will now carry a standing warning. Basis: no such repository is known on this account; all four measured cases were unintentional drift (F4). Accepted rather than resolved: the warning names its cause and its remedy in one line, and suppressing it would require a declaration whose only reader is this check. Durable owner: https://github.com/TanglmChris/keel/issues/112 — if a deliberate pin appears, the suppression is designed there.

## Risks / Trade-offs

- Doctor grows one more line on a command that is already long. Mitigated by placing it in the version block doctor already opens with — `python3`, `openspec`, and now Keel itself, which is the one grouping where a reader is already reading versions — rather than opening a section, and by printing one line whether or not there is drift — a check that is silent when it passes cannot be distinguished from a check that did not run, which is the exact failure this change is about.
- The marker version and the CLI version can agree while both are old. Doctor will say `ok`, correctly: the repository and its install agree. Whether a newer release exists is the non-goal above.

## Open Questions

None.

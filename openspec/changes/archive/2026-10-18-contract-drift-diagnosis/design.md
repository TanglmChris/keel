## Context

Issue #342 asks Keel to tell a compiler-only fingerprint move from a contract edit, instead of asking the author to vouch with `--keep-evidence`. The 5.83-era decision against reconstructing from Git (keel/CHANGELOG.md, "It names where to look and never what changed") held that Git answers for the last commit, not the moment of `task-start`. This design uses the commit that recorded the anchor, and claims a cause only when a check ties that commit to the anchor.

## Facts

- F1 — The capsule compiles from `openspec/changes/<change>/` (tasks, design, specs), `openspec/specs/*/spec.md`, and `keel/config.yaml` (standing authorization, delegation); `resolveCommit` reads Git only for an `equivalence` task's `Base:` (`src/core/task-contract.js`).
- F2 — An inherited standing authorization enters the capsule as one `boundaries.autonomy` entry `Standing authorization (keel/config.yaml): <entries>`, only when the task authored no `Autonomy boundary:`.
- F3 — Measured 2026-10-18 on rtl_ppa_prj: `add-iecc-cbbs#2.1` at `3b63c5e4` compiles to the recorded `c7f56b…` under 5.78.0–5.80.0 and `7da362…` under 5.81.0–5.85.0; `fast-check-waivers#1.1` compiles to `1cd0a8…` at `7859598b` and `567751…` at `aee9fa7d` under both 5.123.0 and 5.125.0, differing only in the F2 entry.
- F4 — `--record` rewrites the anchor line and warns that evidence is stale unless `--keep-evidence` narrows it; it clears nothing itself.

## Decisions

- D1 — `--record` writes `- Contract: keel-task-capsule/v1 sha256:<hex> (keel <version>)`. Every reader keeps extracting the digest as before; the version is optional, so existing anchors stay valid. A re-record that lands the same fingerprint refreshes the version and reports `unchanged`.
- D2 — On drift, the recording commit is the newest commit whose `tasks.md` for the change contains the recorded digest, found with `git log -S`. Its sources (F1 paths only) are read with `git show` into a temporary directory and the task is compiled there by the running compiler, with Git questions answered by the real repository. Call that result O, the recorded digest R, the current compile N.
- D3 — The anchor is linked when O equals R: the committed sources are the ones recorded. It is explained by the compiler when O differs from R, the anchor names a Keel version, and that version is not the running one. Neither ⇒ the diagnosis is unavailable and the existing message stands, claiming nothing — this is the case the earlier decision warned about (a contract edited between recording and commit).
- D4 — Linked or explained, Keel diffs the capsules O and N: no difference ⇒ `compiler` (only possible when explained); only the F2 entry ⇒ `authorization`; otherwise `source`, naming each changed capsule path, e.g. `touch` or `authority[2].text (design.md#D3)`. The message states the commit it compared against and, for `compiler`, both versions.
- D5 — Drift of kind `compiler` still fails every gate (owner, 2026-10-18), naming `task-start --record` and saying no `--keep-evidence` is needed. A `--record` over it warns that the evidence stands, verified against the recording commit, and names no check as stale.
- D6 — `change-close` passes a checked task whose drift is of kind `authorization` (owner, 2026-10-18), with a warning naming the task and the standing-authorization change. `task-complete`, `keel context`, and an unchecked task at `change-close` still treat it as drift: that work continues under the new authorization.
- D7 — Diagnosis runs only on a fingerprint mismatch, so a matching anchor costs nothing; any Git or compile failure yields `unavailable`, never a gate error.

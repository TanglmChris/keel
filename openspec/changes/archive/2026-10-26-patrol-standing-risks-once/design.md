## Facts

- F1 — `runPatrol` in `src/core/patrol.js` pushes `shift.handOffRisks(...)` and `notice.movedSessionRisks(...)` into `result.risks` on every run. With `--notify`, `notifyRisks` sends every entry in `result.risks`. Only the checkout and disk risks come from `sinceLast`, which compares them with the previous snapshot.
- F2 — On 2026-10-26, from 00:15 to 07:15 (+08), the keel-maint tick sent its coordinator 15 identical messages about keel-maint-2's session `375d5fd8` in the removed `my_github/...` directory.
- F3 — `movedSessionRisks` in `src/core/chat/notice.js` does not consult `parkOf`. The `keel chat role` usage says a parked role "is not nudged or reported by the patrol".
- F4 — `keel chat role` offers `--set`, `--alias`, `--prune`, `--park`, `--unpark`, and `--rename`. `--prune` (`drift.pruneBindings`) drops only bindings whose worktree no longer exists. No option removes the binding of a worktree that exists.

## Decisions

- D1 — Under `--since-last`, the hand-off and moved-session risks are standing risks. The snapshot keeps their texts as `standing`. A standing risk goes into the run's risks, and so into `--notify`, only when its text is absent from the previous snapshot's `standing`. That covers a first run, a snapshot written before this change, a risk that appears, a risk whose text changes (a hand-off's error or retry count, for example), and one that returns after clearing. A standing risk that persists unchanged is printed as `risk (sent before): <text>` and kept in the JSON as `standing`. It does not raise the exit status. Nothing reminds the coordinator of a persisting risk later, as with the disk and checkout risks.
- D2 — Without `--since-last`, every standing risk is reported as a risk on every run, as before.
- D3 — `movedSessionRisks` skips a role whose park is in effect (`notice.parkOf`). The patrol and `keel shift status` therefore leave out its session. Hand-off risks still report a parked role, since a failed hand-off is a failure of Keel's own step, not of the role.
- D4 — `keel chat role --unset` removes the binding of the worktree it runs in, or of the one `--repo` names, and prints `Unbound <role> from <worktree>.`. When no role is bound there, it prints that the worktree has no chat role and exits 0. The role's aliases, presence, and other per-role state stay, so binding the role again elsewhere picks them up.

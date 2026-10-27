## Facts

- F1 — `findPushes` (`plugins/keel/scripts/pretooluse-guard.js`) sets `cdBefore` on a `cd` or `pushd` segment and keeps `dir` as the session cwd; `git -C <dir>` alone moves `dir`.
- F2 — `checkPushes` reads the push scope of `rev-parse --show-toplevel` at `push.dir || cwd`. `pushTargets` consults `cdBefore` only through `needsCurrent()`, for a push with no refspec or a `HEAD` destination; an explicit `main:main` is matched against that repository's globs.
- F3 — An undetermined target is denied only when the repository the guard reads declares a push scope. The deny reason ends "Name the branch, as `git push origin <branch>`", which does not help when the branch was named and the directory was the problem.
- F4 — A session running in a repository that declares no push scope is not governed by the guard, `cd` or not. #486 also infers, without a test, a miss from that: `cd` into a governed repository from one that is not.

## Decisions

- D1 — A push with `cdBefore` is undetermined whatever its refspec: the guard cannot tell which repository it pushes.
- D2 — Its deny reason says the directory changes before the push, so the repository it pushes is unknown, and names `` `git -C <directory> push <remote> <branch>` `` as the form to use. Other undetermined reasons keep `` `git push origin <branch>` ``.
- D3 — Not taken, by the owner's choice of the conservative fix: resolving a literal `cd` target to move `dir`. `CDPATH`, `~`, `cd -`, chained `cd`s, and subshells make that target unreliable, and a wrong one would apply another repository's rules. The F4 case stays as it is: the guard governs the repository whose config it reads.

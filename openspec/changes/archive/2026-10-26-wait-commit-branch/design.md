## Facts

- F1 — `store.wait` writes `commit <sha> on <remote>`, with `<remote>` defaulting to `origin`. `conditionHolds` matches `^commit ([0-9a-f]+) on (\S+)$` and holds when `git for-each-ref --contains <sha> refs/remotes/<remote>/` lists any ref.
- F2 — `branches.js` (#469) reads `branches: trunk:` with `config.readBranchesDeclaration`. It counts the remote's default branch, from `refs/remotes/origin/HEAD` with a `main`/`master` fallback, as a trunk beside the declared ones.
- F3 — Given `commit <sha> on origin/main`, the 5.206.0 matcher reads the remote as `origin/main`. It lists refs under `refs/remotes/origin/main/`, finds none, and never holds. Given a condition containing ` or `, its `\S+` does not match, and the wait stays unchecked. So an older Keel sharing the store never meets a new-form wait early.

## Decisions

- D1 — `keel chat wait --commit <sha> --branch <name>` writes `commit <sha> on <remote>/<name>`. `<name>` must be a git ref name without spaces, and `--branch` without `--commit` is refused. The patrol holds such a wait when `refs/remotes/<remote>/<name>` exists and `git merge-base --is-ancestor <sha> <that ref>` succeeds.
- D2 — A commit wait with no `--branch`, in a repository whose `branches:` declares no `trunk:`, keeps the condition `commit <sha> on <remote>` and its any-branch meaning. `keel chat wait`'s echo, `keel chat waits`, and the patrol's `Condition met:` notice render it as `commit <sha> on any branch of <remote>`. `keel chat waits --json` keeps the raw condition.
- D3 — When `branches:` declares at least one `trunk:`, a commit wait with no `--branch` is registered against the trunks. These are the remote's default branch, when it has one, and each declared trunk, in that order without repeats. The condition is `commit <sha> on <remote>/<a> or <remote>/<b> …`. It holds when any listed branch contains the commit, checked as in D1. The list is resolved at registration, so a later change to `branches:` does not move an open wait.
- D4 — F3 makes the new forms safe in a store an older Keel also reads: they are never met early there, only late or never.

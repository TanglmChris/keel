## Facts

- F1 — Each worktree keeps its own HEAD reflog (`git -C <worktree> reflog show HEAD`). Every switch writes `checkout: moving from <a> to <b>` there, including `git switch -c <b>` and `git worktree add -b <b>`.
- F2 — `roles.json` in the chat store binds worktrees to roles. `keel shift resume` already names a worktree on a branch merged into `origin/<default>` (#446) and fetches nothing.
- F3 — `keel gate …` writes no project state beyond the guard manifest (AGENTS.md, Completion gates), so a deletion cannot ride on `change-close`.
- F4 — `authorize:` already has scoped actions with one fixed scope, such as `cleanup:scratch` (`AUTHORIZATION_SCOPES` in `src/core/config.js`), and refuses the whole declaration when it cannot read one entry.
- F5 — The owner's design decisions (2026-10-25, #469):
  - a new command that lists, and deletes only under a standing authorization, with pointers elsewhere;
  - ownership read from the role's worktree having checked the branch out;
  - one word, `delete-branch:merged`, covering local and remote.

## Decisions

- D1 — **Trunks.** The remote default branch (`origin/HEAD`, or else `origin/main`, or else `origin/master`) is always a trunk. `branches: trunk:` adds more by name. Each trunk is read as `refs/remotes/origin/<name>`, and a declared trunk with no such ref is named and skipped.
- D2 — **A branch qualifies** when every condition holds:
  - (a) its tip is an ancestor of at least one trunk ref;
  - (b) it is not itself a trunk;
  - (c) no worktree of the repository has it checked out;
  - (d) the HEAD reflog of a worktree bound to the role names it in a `checkout: moving from … to …` entry;
  - (e) it matches no `branches: keep:` glob. `*` matches within a `/` segment and `**` across them, as Touch globs do.

  The same name is judged separately on each side, so a local branch and its `origin/<name>` qualify independently.
- D3 — **`keel branches [repo] [--role <role>] [--json]`** reads remote-tracking refs as they are, fetches nothing, and says when they were last fetched. The role defaults to the worktree's binding. It exits 0 whether or not anything qualifies.
- D4 — **`keel branches prune`** requires `delete-branch:merged` in the standing authorization. Without it, it prints the list and the declaration that would allow deletion, and exits 3. With it, it runs `git fetch --prune origin` and recomputes, then for each qualifying branch:
  - appends a JSON line `{at, role, side, branch, sha}` to `keel-chat/branches/deleted.jsonl`;
  - deletes the branch: `git branch -D <b>` locally, `git push origin --delete <b>` remotely;
  - prints the restore command: `git branch <b> <sha>`, or `git push origin <sha>:refs/heads/<b>`.

  One failed deletion is reported and the rest go on, and the command exits 1 if any failed. A failed fetch deletes nothing and exits 1.
- D5 — **Pointers.** `keel shift check` prints one informational line, `merged branches: <n> of this role's branches are merged …; keel branches lists them`. It is not a loose item and never changes the exit code. `keel shift resume` appends the same pointer when it already names a merged branch. `keel --doctor` prints `branches: <n> merged task branch(es) of <roles> may be deleted (keel branches)` or `branches: ok`.
- D6 — **Not a gate.** Nothing in `keel gate …` deletes or lists branches (F3).
- D7 — **Configuration.** `branches:` is a new declaration placed after `shift`. It is documented in `keel/config.yaml`'s header and body like every other declaration.

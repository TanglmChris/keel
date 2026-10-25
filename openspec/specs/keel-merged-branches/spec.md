## Purpose

Define how Keel tells a role which of its task branches are merged into a trunk and no longer used: the trunks and kept branches a repository declares, the read-only listing with each branch's sha, deletion only under the `delete-branch:merged` standing authorization with a record that restores each branch, and the pointers at the shift check, resume, and doctor that never delete.

## Requirements

### Requirement: Keel lists a role's merged task branches

`keel branches` MUST list the local and remote branches of the role that are safe to delete, each with its sha and the trunk containing it, and MUST delete nothing and fetch nothing. A branch MUST qualify only when all of the following hold:

- its tip is an ancestor of a trunk's remote-tracking ref, where the trunks are the remote default branch plus those `branches: trunk:` declares;
- it is not a trunk;
- no worktree has it checked out;
- the HEAD reflog of a worktree bound to the role names it in a checkout entry;
- it matches no `branches: keep:` glob.

#### Scenario: Only merged, unused, owned, unkept branches are listed
- **WHEN** verify's worktree has checked out `done-a` (merged into `origin/main`), `done-b` (merged only into the declared trunk `integ`), `wip` (not merged), `kept` (merged, matching `keep: [kept]`), and `busy` (merged, checked out in another worktree), while rtl's worktree alone checked out `rtl-done` (merged), and each of them was pushed
- **THEN** `keel branches` for verify lists `done-a` and `done-b` on both the local and remote sides, each with its sha and trunk, lists none of the others, and changes no ref

### Requirement: Pruning deletes only under the standing authorization

`keel branches prune` MUST delete nothing and exit 3 unless `authorize:` declares `delete-branch:merged`, and it MUST then print what it would delete and name that declaration. With the declaration, it MUST fetch the remote, recompute the list, and for each qualifying branch:

- record the time, role, side, branch, and sha in the chat store before deleting it;
- delete it, locally or on the remote;
- print the command that restores it.

A failed deletion MUST be reported without stopping the others, and the command MUST then exit 1.

#### Scenario: Without the declaration nothing is deleted
- **WHEN** `keel branches prune` runs for verify with no `delete-branch:merged`
- **THEN** it exits 3, names `delete-branch:merged`, lists `done-a`, and every branch still exists locally and on the remote

#### Scenario: With the declaration the merged branches go, with a record
- **WHEN** `keel branches prune` runs for verify with `delete-branch:merged` declared
- **THEN** `done-a` and `done-b` are gone locally and on the remote, every other branch remains, the store's record holds one line per deletion with the branch's sha, and the printed restore command recreates `done-a` at that sha

### Requirement: Merged branches are pointed out, never deleted, elsewhere

`keel shift check` MUST name how many of the role's branches qualify and point at `keel branches`, without counting them as loose or changing its exit code. `keel shift resume` MUST add the same pointer when it names a merged branch. `keel --doctor` MUST report the count per role. No gate MUST list or delete branches.

#### Scenario: The check points without failing
- **WHEN** verify has two qualifying branches and nothing loose, and runs `keel shift check`
- **THEN** it exits 0 and names `keel branches` and the count 2, and `keel --doctor` reports verify's merged branches

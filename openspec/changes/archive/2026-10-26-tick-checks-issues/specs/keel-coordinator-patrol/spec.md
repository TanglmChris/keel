## ADDED Requirements

### Requirement: The tick fetches issue state for the patrol when something needs it

When a patrol is due and `keel/config.yaml` declares a readable `issue_roles:` route, or a chat group holds an open `issue #<n> closed` wait, `keel tick` MUST run `gh issue list --state all --search "sort:updated-desc" --limit 100 --json number,title,state,labels,updatedAt` once in that step, and `gh issue view <n>` with the same fields for each waited issue the list did not return, and MUST pass what it read to every patrol it runs in that step as `--issues`. When neither holds, it MUST run no `gh`. When a `gh` call cannot start, fails, or prints no JSON, the tick MUST still pass what it read and MUST print a line saying issue checks are not run and why when that state differs from its previous one, and not otherwise. `keel --doctor` MUST print an `issue checks` line from the tick's last recorded issue state, naming the reason when the checks are not run.

#### Scenario: A tick routes a labelled issue and meets an issue wait
- **WHEN** `patrol:` lists scoped `pm-a` and `pm-b` with `runner: tick`, `issue_roles:` routes the label `dev` to `dev-b`, `dev-a` waits in `team-a` for issue 42 to close, `gh issue list` returns issue 7 labelled `dev` and not issue 42, `gh issue view 42` returns it `CLOSED`, and `keel tick` runs both patrols
- **THEN** `dev-b` is sent one message naming issue 7, `dev-a` is sent one message that `issue #42 closed` is met, and a second due tick sends neither again

#### Scenario: A failed fetch is said once and shown by the doctor
- **WHEN** `gh` exits 1 for two due ticks of a repository declaring `issue_roles:`
- **THEN** the first tick prints a line saying issue checks are not run that names the failure, the second prints no such line, and `keel --doctor` prints `issue checks` as not checked with that reason

#### Scenario: Nothing needs issues, so no gh runs
- **WHEN** a repository declares no `issue_roles:` and holds no issue wait, and `keel tick` runs a due patrol
- **THEN** no `gh` command runs

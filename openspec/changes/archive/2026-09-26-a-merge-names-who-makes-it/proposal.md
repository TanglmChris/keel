## Why

The owner wants this repository to run fully automatically, merge included (#155). Two guards refuse
the merge step when the *agent* takes it — Claude Code's auto-mode classifier (`[Merge Without Review]`,
and `[Auto-Mode Bypass]` when the agent tried to reconfigure itself around it) and Keel's own
`## Unattended runs`: "It may not merge one." Both are right about the agent.

The shape that satisfies everyone moves the merge out of the agent and into the repository: GitHub
auto-merge behind a required `full-gate` check. The agent opens a pull request and never merges.

That leaves Keel's sentence **literally true and misleading**. A reader of `AGENTS.md` concludes that
every change reaching `main` was looked at by a person, while in fact the suite is the only reviewer.
Keel has nowhere to record who merges, so it cannot say so — the failure shape this repository refuses
everywhere else: a statement that passes on its wording while the thing it describes has changed.

## What Changes

- **`merge:` in `keel/config.yaml` declares how merges reach the default branch**: `human`, or
  `repository:<check>` naming the required check the repository merges on. A bare `repository` is
  refused, the same way a bare `issue` is: the claim that no person reviews is only honest beside the
  check that replaced the person.
- **`keel context` and `keel --doctor` report it.** The projection carries a `Merge:` line when a
  declaration exists, stating plainly for `repository:` that no human reviews before merge. An
  undeclared repository prints nothing new, because an absent declaration changes nothing.
- **An unreadable declaration claims nothing** and is named with the accepted forms.
- **It is not a permission.** `authorize: merge` stays an unknown action. The declaration describes
  the repository; it grants the agent nothing, and both guards keep refusing an agent merge.
- **`AGENTS.md` states the distinction**: the agent never merges; a repository may, by a rule its owner
  declared, and `merge:` says which.

## Capabilities

### New Capabilities

- `keel-merge-declaration`: how a repository declares who merges, how Keel reports it, and why it is
  not an authorization.

## Impact

- `src/core/config.js`, `src/core/context.js`, `bin/keel.js` — the reader, the projection line, the
  doctor surface.
- `keel/config.yaml`, `AGENTS.md`, `README.md` — where a project learns the declaration exists.
- **Not adopted**: Keel checking GitHub's settings to verify the claim. Keel is local and offline and
  never fetches; the declaration is the owner's claim, reported where Review can see it, exactly as
  `Fails with:` is. It also does not set up auto-merge: that one-time configuration is the owner's act,
  because an agent configuring a repository to merge without review is the refused outcome with a
  different executor.

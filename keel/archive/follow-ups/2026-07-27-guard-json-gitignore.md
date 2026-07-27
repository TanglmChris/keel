# keel/guard.json is not covered by any .gitignore

Date: 2026-07-27. Owner task: openspec/changes/retire-follow-up-backlog/tasks.md#1.2.

## Finding

`keel gate task-start` writes `keel/guard.json` (the write guard's contract fingerprint state) into the project. Neither this repository's `.gitignore` nor the `.gitignore` handling in `keel --init` declares it, so every gate run leaves an untracked file:

```
$ keel gate task-start --change retire-follow-up-backlog --task 1.2 --record --json
{ "status": "pass", ... }

$ git status --short
?? keel/guard.json
```

`git log --all -- keel/guard.json` returns nothing, confirming it was never intended to be committed — only never declared. It is local session state, not project content, and it currently sits beside `keel/config.yaml`, which *is* project content that should be committed.

## Durable owner

GitHub issue: https://github.com/TanglmChris/keel/issues/11

That issue carries the full evidence, the impact (it pollutes `git status`, and `task-complete` uses working-tree attribution for its Scope check, so a permanently untracked file forces the author to re-adjudicate it every time), and two candidate fixes — declare it in `.gitignore` on install, or move guard state under `.git/` where no ignore rule is needed.

## Why this file exists rather than a bare issue link

`keel gate task-complete` rejects a GitHub issue URL as a Review Findings owner. `findingOwnerIsDurable` (`src/core/gates.js:417`) accepts only three forms: a `Discard reason:`/`Discard rationale:` prefix, a `keel/archive/…` path, or an existing `openspec/changes/…` artifact.

```
$ keel gate task-complete --change retire-follow-up-backlog --task 1.2 --base HEAD --json
"code": "finding-owner",
"message": "Review Findings must be `none` or carry a durable owner — a
            `Discard reason:`/`Discard rationale:` prefix, a `keel/archive/…`
            path, or an existing `openspec/changes/…` artifact; ..."
```

This is a mismatch with `keel-expectation-slice-evidence-gates`, which requires "a durable follow-up owner" without constraining its form, and with `keel-stateless-continuity / Keel continuity is stateless / Native runtime state is not continuity authority`, whose exclusion list names only native runtime state. Neither spec excludes an issue tracker. The gate does, in effect, by enumerating three accepted forms.

So this file is the gate-recognized pointer, and the issue above is the substantive owner. The mismatch itself is recorded as a separate finding on task 1.3 of the same change.

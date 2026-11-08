---
description: Draft a redacted issue for Keel from this session — version, reproduction, near-duplicates — and create it only after the user agrees
argument-hint: "<one sentence about the problem>"
---

File feedback about Keel itself. The mechanism is `keel feedback`; this command only orders the steps and asks before anything is created. It works from any project, not only Keel's.

## 1. Draft

Take the problem from the arguments: `$ARGUMENTS`, or else ask for one sentence. If a Keel command just failed, pass it and its output so the issue carries them:

```bash
keel feedback "<one sentence>" --command "<the command that failed>" --output-file <file holding its output> --expected "<what should have happened>" --repro "<the steps>" --impact "<what it blocks>"
```

Write the output to a file first and pass the file; do not paste it into the command line. Add `--doctor` only when the problem is about setup, because the doctor output carries local paths (they are redacted, but the user should know it is attached). Nothing is created by this step.

## 2. Show it

Show the user the whole draft as printed: title, sections, the count of redacted values, and any similar issues. Check it yourself for project content that should not be public — a customer name, an unreleased design — that the redaction cannot know, and fix it by rerunning with the text changed.

## 3. Ask

Ask through the structured-choice surface, with the first option recommended:

- **new issue** — create it now.
- **add to #n myself** — when a similar issue exists; print the `gh issue comment` command from the draft for the user to run. Keel runs no comment and edits no issue.
- **cancel** — leave the draft file where it is and stop.

## 4. Create, only on "new issue"

```bash
keel feedback "<the same arguments>" --create --confirmed
```

Drop `--confirmed` only when this project's `keel/config.yaml` declares `issue:TanglmChris/keel`; the declaration is the owner's standing approval, and without it `--create` is refused. Add no label, assignee or milestone, and do not add the issue to any `triage:` list: whether it is worth doing stays the owner's decision.

Report the issue URL the command prints. If `gh` is missing or not logged in the command exits 4 with the draft saved: give the user the saved file and the `gh issue create` command it printed, and do not retry.

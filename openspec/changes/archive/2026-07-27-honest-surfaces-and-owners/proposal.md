## Why

Four small reported defects, all of the same kind: a Keel surface either manufactures work the author did not need to do, or states more than Keel actually knows.

**Issue #12** — the gate refuses an issue tracker as a durable follow-up owner. `keel-expectation-slice-evidence-gates` requires "a durable follow-up owner" without constraining its form, but `findingOwnerIsDurable` enumerates three: a `Discard reason:` prefix, a `keel/archive/…` path, or an existing `openspec/changes/…` artifact. A project whose declared follow-up owner is GitHub issues must therefore write a local note per finding whose only job is to be a shape the gate recognizes. This repository has paid that cost three times.

**Issue #11** — `keel gate task-start` writes `keel/guard.json`, and nothing declares it ignorable. Every gate run leaves an untracked file in the project. Because `task-complete` attributes working-tree paths against Touch, a permanently untracked file is something the author re-adjudicates every completion.

**Issue #14** — `Guard: started` means the manifest was written. Authors read it as "writes are being checked now". The two came apart on 2026-07-27: a session whose plugin state predated a marketplace switch kept the old plugin resident, so `task-start` wrote a valid manifest and no tool call was ever checked against it. Keel's capability probing already refuses to infer activation from a target's name; the guard command's own output does not carry the same caution.

**Issue #13 item 3** — when the repository being worked on *is* Keel, a bare `keel gate …` resolves to the globally installed CLI, so gate changes under test are invisible and the gate reports stale results. One dogfood round was lost to two spurious problems from a stale global CLI. This affects only Keel's own developers, but Keel's development process is dogfooding, so it hits every time.

## What Changes

- Accept an absolute `http(s)` URL as a durable owner, in both the Review `Findings` check and the `## Expectation Coverage` check, and list it among the accepted forms in the rejection message.
- Scaffold `keel/.gitignore` declaring `guard.json` at install, once, never overwriting a project's own file.
- State the enforcement boundary in the guard command's own output: the status describes the manifest, and enforcement depends on a runtime hook Keel cannot observe from the repository.
- Report one `--doctor` line, only in Keel's own source repository, telling the author that gate commands must run through the repository's own CLI when gate code is under change.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-core-gates`: the enumerated durable-owner forms admit an external tracker reference, in both places the rule is applied.
- `keel-touch-write-guard`: the guard manifest is declared ignorable local state, and the guard command states that a written manifest is not observed enforcement.
- `keel-target-surface-diagnostics`: `--doctor` reports the CLI-resolution hazard that exists only in Keel's own repository.

## Impact

- A project that owns follow-ups in an issue tracker stops writing per-finding local notes solely to satisfy a shape check.
- `git status` stays clean across gate runs, so completion-time scope adjudication has one less permanent exception.
- A written guard manifest is no longer readable as proof that writes are being checked.
- Keel's own developers stop losing rounds to a stale global CLI reporting on code they have already changed.
- No change to what a valid task compiles to, and no change to any fingerprint.

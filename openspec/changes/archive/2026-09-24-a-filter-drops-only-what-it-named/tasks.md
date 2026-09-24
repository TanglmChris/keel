# Tasks

## 1. A sanitized PATH removes one file, and a fixture that broke itself says so

- [x] 1.1 One helper builds the sanitized PATH by replacing each directory that holds an `openspec` with a mirror symlinking every entry of it except the `openspec` ones, at the same index; a new scenario proves it on a synthetic directory holding both a fake `node` and a fake `openspec`, asserting from both sides that the runtime survived and that the tool resolves under no extension
  - Covers:
    - keel-validation-runner / A scenario that constructs an environment removes only what it named / A named tool is removed from PATH without removing its neighbours
    - keel-validation-runner / A scenario that constructs an environment removes only what it named / The construction is proven on a fixture carrying the layout, from both sides
    - F1
    - F2
    - D1
    - D2
    - D3
    - D5
    - D6
    - A1
  - Read:
    - scripts/validate_plugin.py
    - openspec/changes/a-filter-drops-only-what-it-named/design.md
  - Touch:
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-filter-drops-only-what-it-named` scenario in `scripts/validate_plugin.py` builds a temporary directory holding a fake `node`, a fake `openspec`, a fake `openspec.cmd`, and one unrelated executable, puts it on a PATH between two other entries, and runs the helper. It asserts that the fake `node` still resolves and resolves to the mirror of that same directory at the same index, that the unrelated executable still resolves, that `shutil.which("openspec", …)` and `shutil.which("openspec.cmd", …)` both return `None`, and that the entry count and order of the returned PATH are unchanged. The surviving-runtime assertion is the regression guard and the tool-is-gone assertion is the positive control, so a mirror that produced an empty directory cannot pass. Fails with: `node did not survive`
    - M2 (regression): a directory on the PATH that holds no `openspec` is returned unchanged — the same string, not a mirror — so the helper's cost and its blast radius are confined to the directories that carry the tool, and the scenario asserts the unchanged entry is byte-identical to the original.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if making the mirror work requires changing `resolve_openspec` or `run_openspec`, because D1 confines this to how the environment is built and those two are the behavior the existing scenarios assert about.
    - Stop if the fixture has to rely on this host having `node` and `openspec` in one directory, because D5 records that a scenario which can only fail on a Homebrew host is a scenario CI never runs.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8674cea7e5d70d12e94f40d8da5364ac532e9ccafe4b8c5d9dedde0039bb5cf1
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-filter-drops-only-what-it-named` reports `a-filter-drops-only-what-it-named scenario passed.` The fixture is a temporary `shared/` holding a fake `node`, `openspec`, `openspec.cmd`, and `unrelated`, on a PATH between `before/` and `after/` which hold neither — the Homebrew layout built rather than relied on, so the check fails on a host where the two binaries never shared a directory. Asserted in behavior-before-shape order: `node` resolves, and from PATH entry 1 rather than some other position; `unrelated` resolves; `openspec` and `openspec.cmd` resolve to `None`; the PATH still has 3 entries in the order given. Both controls were driven to failure rather than assumed live. Mutating the mirror to exclude by exact name instead of stem — the D3 decision — leaks `openspec.cmd`, and the scenario reports `openspec.cmd still resolves on a PATH built to exclude it, at '…/keel-no-openspec-eio6cc7v/1/openspec.cmd'`. Mutating it to symlink nothing, so the mirror is an empty directory, reports `node did not survive …` — which is the precedent `an-assertion-that-never-failed-proves-nothing` applied literally: the tool-is-gone assertion is satisfied perfectly by an empty mirror, so the surviving-runtime assertion is what stops that from passing. Both mutations were reverted and the scenario re-run green.
    - M1.red: fail, for the declared reason. Taken against the helper carrying the predicate it replaces — the directory drop extracted verbatim from the two call sites, so the red is the defect itself and not a missing function. `a-filter-drops-only-what-it-named: node did not survive a filter that was removing openspec. The interpreter shares a directory with the tool, and the whole directory went. sanitized PATH '…/before:…/after'` — the shared directory is absent from the sanitized PATH entirely, which is the shape of the defect. Carries the declared signature `node did not survive`. A first red fired one assertion earlier, on the entry count, and the assertions were reordered to put behavior before shape before this red was taken: an entry count is the symptom, and what the defect destroys is the ability to run the interpreter.
    - M1.green: pass. Same command after the helper's body was replaced by the mirror; same fixture, same assertions.
    - M2: pass. Inside the same scenario run: `before/` and `after/` hold no `openspec` and come back as the identical strings they were passed — compared byte-for-byte against `str(original)`, not merely for resolvability — so only the one directory carrying the tool is mirrored. Measured basis for the cost this bounds: on this host 1 of 17 PATH entries holds an `openspec`, and mirroring it is 131 symlinks in 6 ms.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a PATH built to exclude `openspec` removes it under every extension the host's lookup considers and removes nothing else. M1 proves both halves through `shutil.which` against a real directory tree — the same lookup a child process performs — rather than by inspecting the returned string, and it proves them on a synthetic layout so CI can fail on this defect (D5). The two mutation runs are what distinguish this from a check that agrees with its implementation: each control was made to fire, and each fired with the message naming the property it guards. The red was taken against the real previous behavior, so `node did not survive` is a prediction that the extracted predicate was the defect, not a transcription of whatever an absent function raised. One Covers entry is not proved by a check and should not be read as if it were: A1's Windows fallback — dropping the directory when a symlink is refused — is written in this task and is unreachable on a POSIX runner, so no `M<n>` exercises it. Its disposition is E6's discard, with the reason there, not this task's evidence.
      - Scope check: `git status --short` shows `scripts/validate_plugin.py` — exactly this task's Touch — plus this change's own untracked directory. `keel guard status` reports the fingerprint unchanged from the re-record. `npm test` reports `validation --all failed for: the-dependency-resolves-where-npm-put-it, a-declared-dependency-is-resolved`, the identical set it reported at 955c0ea before this task: the helper exists and is correct, and nothing consumes it yet, which is task 1.2. `task-start` warned that 1.1 and 1.2 declare the same Touch under the same strategy and asked for the two to be compared before implementing. They were: 1.1's subject is the helper's behavior on a synthetic layout, provable anywhere, and 1.2's is the observable outcome on a host that actually has the layout — two different assertions with two different honest reds, not one behavior split so the second half has no red left. The reds bear that out: this task's is a synthetic fixture losing its interpreter, 1.2's is the suite failing on this machine.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: M2 was tagged `(regression)` before any Evidence was recorded, so nothing was invalidated. It asserts that a PATH entry holding no `openspec` comes back byte-identical, which the directory-dropping predicate this task replaces already did — the check has no honest red, and recording one would have meant mutating the helper to break a property it never had. `task-start` prompted for exactly this at the point where the choice was still free.

- [x] 1.2 Both existing call sites build their PATH through that helper instead of dropping directories, and each asserts before asserting the behavior that `node` resolves on the PATH it just built — reporting a fixture that removed its own interpreter as the skip contract naming `node`, never as a failure naming `openspec`
  - Covers:
    - keel-validation-runner / A scenario that constructs an environment removes only what it named / A fixture that removed the interpreter reports a skip that names it
    - F3
    - F4
    - F5
    - F6
    - D4
    - A2
    - I1
  - Read:
    - scripts/validate_plugin.py
    - openspec/changes/a-filter-drops-only-what-it-named/design.md
  - Touch:
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario a-declared-dependency-is-resolved` and `--scenario the-dependency-resolves-where-npm-put-it` both pass on this host, where `command -v node` and `command -v openspec` are the same directory. Fails with: `the resolved openspec did not report a version`
    - M2: the skip path is driven, not read: `a-declared-dependency-is-resolved` is run as a child process under an environment whose PATH contains no `node` at all, and it exits `3` with a message naming `node`; the same run's output contains no failure naming `openspec`. Before this task the same child exits `1` with the misattributed message, which is the negative half the assertion needs. Fails with: `the resolved openspec did not report a version`
    - M3: `npm test` reports no failing scenario and no exception — the full suite is green on this host, where before this change it ended `validation --all failed for: the-dependency-resolves-where-npm-put-it, a-declared-dependency-is-resolved` with every other scenario passing. Fails with: `validation --all failed for`
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the precondition check has to be satisfied by a skip on this host, because D4 records that the skip is the net and the expected outcome here is a pass — a skip here would mean the mirror did not work and the net hid it.
    - Stop if either scenario's assertions about OpenSpec resolution have to change to make M1 pass, because the Non-Goals record that only the environment they build is in scope.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:98b7f4c7693b6c02077d3c7edff3370e38019613d67b25acbf2c3304472aebc6
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-declared-dependency-is-resolved` reports `a-declared-dependency-is-resolved scenario passed.` and `--scenario the-dependency-resolves-where-npm-put-it` reports `the-dependency-resolves-where-npm-put-it scenario passed.` — on this host, where `command -v node` and `command -v openspec` are both `/opt/homebrew/bin`. Both now build their PATH through `path_without_openspec()`. In the second, the context is opened in the same `with` as the fixture's temporary directory rather than inside `clean_env`, because the mirrors have to outlive the last child process and not the call that built the env.
    - M1.red: fail, for the right reason, both scenarios, taken under this contract before the call sites were rewired. `a-declared-dependency-is-resolved: the resolved openspec did not report a version. exit=127 out=''` — 127 is the `#!/usr/bin/env node` shim with no interpreter, reported against `openspec`. `the-dependency-resolves-where-npm-put-it` does not reach a `report()` at all: `FileNotFoundError: [Errno 2] No such file or directory: 'node'` out of `subprocess.run`, because `subprocess` resolves the program from the passed env's PATH. Carries the declared signature `the resolved openspec did not report a version`.
    - M1.green: pass. Same two commands after both call sites were rewired onto the helper; both scenarios report `scenario passed.` on the same host, with their assertions about OpenSpec resolution unchanged.
    - M2: pass. The skip path is driven rather than read. `PATH` stripped of `/opt/homebrew/bin` — the only entry on this host carrying `node` — and the scenario run as a child of that environment through an absolute `python3`: `a-declared-dependency-is-resolved scenario skipped: node does not resolve on the PATH this scenario built, so the openspec shim it resolves would have no interpreter. That is a broken fixture, not a fact about openspec.`, exit `3`. The word `openspec` appears only in the clause denying it is the subject; no failure is reported against it. `the-dependency-resolves-where-npm-put-it` under the same environment reports the matching skip and exit `3`. Both take the `skip_scenario` path that `runner-skip-accounting` already asserts is named, counted apart, and not a run failure.
    - M2.red: fail, for the right reason, under this contract. The same child under the same node-less PATH before the precondition existed: exit `1`, `a-declared-dependency-is-resolved: the resolved openspec did not report a version. exit=127 out=''`. That is the negative half the assertion needs — the scenario failed, and named a tool that was installed, resolvable, and working. Carries the declared signature `the resolved openspec did not report a version`.
    - M2.green: pass. Same command after the precondition was added; exit moved `1` -> `3` and the sentence moved from `openspec` to `node`.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 173 scenarios, 1 skipped: output-survives-the-pipe.` No failing scenario, and no differential against `origin/main` — the first release-bound state in this repository where `npm test` is readable as a plain completion check on this host. The one skip is a platform fact unrelated to this change: `output-survives-the-pipe scenario skipped: this platform refused F_SETPIPE_SZ ([Errno 9] Bad file descriptor), so the pipe buffer cannot be shrunk`. Checked against the unmodified file — `git stash push scripts/validate_plugin.py`, same scenario, identical skip and reason, restored — so it is not an exception this change introduced or hid.
    - M3.red: fail, for the right reason. `npm test` immediately before this task, with 1.1 already complete: `validation --all failed for: the-dependency-resolves-where-npm-put-it, a-declared-dependency-is-resolved` — the identical set the same command reported at 955c0ea before any of this change existed, which is what shows 1.1 did not quietly make it pass. Carries the declared signature `validation --all failed for`.
    - M3.green: pass. Same command after both call sites were rewired.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the two scenarios pass on a host with the shared-bin layout, and that a fixture which removed its own interpreter says so by name. M1 proves the first through the scenarios themselves on the affected host; M3 proves nothing else moved, through the entry point a completion check actually uses. M2 is the half that would be easy to fake: the skip branch is unreachable on this host after the fix, so it is driven by removing `node` from the environment for real and running the scenario as a child, rather than by reading the branch. Its red is the same command producing the misattributed sentence, which makes the green a change of subject — exit 1 naming `openspec` to exit 3 naming `node` — and not merely a new message appearing somewhere. All three reds were taken under this task's recorded contract.
      - Scope check: `git status --short` shows `scripts/validate_plugin.py` — exactly this task's Touch — plus this change's own untracked directory. `keel gate task-complete` compared the worktree against the dirty set recorded at task-start and reported no path outside Touch. The assertions in both scenarios are untouched: the diff is the PATH construction, one skip branch per scenario, and the comment I1 named. `task-start` again warned that 1.1 and 1.2 share a Touch set under the same strategy; by completion the answer is visible rather than predicted. 1.1's minimal implementation was not wrong in the field — the helper it built is the one this task consumes unchanged — and this task had three honest reds of its own, none of which 1.1 had already made pass: M3's red was taken with 1.1 complete and reported the identical failing set as before the change existed.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — the sanitized PATH removes the named tool and keeps its neighbours
    - E2 — a fixture that removed its own interpreter reports a skip naming it
    - E3 — `npm test` is usable as a completion check on this host
    - I1 — the comment that claims nothing else is removed
  - Read:
    - keel/CHANGELOG.md
    - README.md
  - Touch:
    - package.json
    - package-lock.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - scripts/validate_plugin.py
    - openspec/specs/keel-validation-runner/spec.md
    - .claude/commands/opsx/apply.md
    - .claude/commands/opsx/archive.md
    - .claude/commands/opsx/propose.md
    - .claude/commands/opsx/sync.md
    - .claude/skills/openspec-apply-change/SKILL.md
    - .claude/skills/openspec-archive-change/SKILL.md
    - .claude/skills/openspec-propose/SKILL.md
    - .claude/skills/openspec-sync-specs/SKILL.md
    - .codex/skills/openspec-apply-change/SKILL.md
    - .codex/skills/openspec-archive-change/SKILL.md
    - .codex/skills/openspec-propose/SKILL.md
    - .codex/skills/openspec-sync-specs/SKILL.md
  - Verify:
    - Strategy: evidence-first
    - Reason: this task's whole effect is version markers, a changelog entry, and promoted spec text. The behavior was proven red-green in 1.1 and 1.2, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `keel/CHANGELOG.md` carries an entry stating the measured cause from issue #137 — one of seventeen PATH entries dropped, and it is the one holding the interpreter — that the diagnostic named a tool that was installed and working, and that the skip check added beside the fix is a net rather than the fix
    - M3: the spec delta is promoted into `openspec/specs/keel-validation-runner/spec.md`, `node node_modules/.bin/openspec validate a-filter-drops-only-what-it-named --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` reports no failing scenario, so the release moved nothing — and this is the first release in this repository able to state that without a differential against `origin/main`
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
    - Stop if closing issue #137 is treated as part of this task: the standing authorization in `keel/config.yaml` has no tracker entry, which is issue #136's subject, so the close is the user's.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:29d7b0c1af3677b21766bd81ea54805af3a090f150c69b5c03c5836c913ff7ef
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.60.0 to 5.61.0 through `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`. The Stop Rule held: no marker turned up that the scenario does not check.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.61.0 - a filter drops only what it named`. It states the measured cause — 1 of 17 PATH entries dropped and it is the one holding `node`, on the ordinary Homebrew plus `npm install -g` layout; that the printed failure was `the resolved openspec did not report a version. exit=127`, naming a tool that was installed, resolvable, and working, while the scenario carrying `FileNotFoundError: … 'node'` emitted a traceback and was not printed first; that the scenario's own comment anticipated the hazard and guarded only its global form; that exclusion is now by file and by stem, with the 131-symlink/6 ms cost; and that the precondition skip **is a net rather than the fix**, with the one case it exists for named (a Windows symlink refusal falling back to the directory drop). It closes on what the reader gets back: `npm test` readable as a completion check without a differential against `origin/main`.
    - M3: pass. The delta is promoted — `openspec/specs/keel-validation-runner/spec.md` carries `### Requirement: A scenario that constructs an environment removes only what it named` with its three scenarios. `node node_modules/.bin/openspec validate a-filter-drops-only-what-it-named --strict` reports `Change 'a-filter-drops-only-what-it-named' is valid`, and `published-specs-validate-strictly` reports `23 published specs validate strictly against openspec 1.6.0.`
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 173 scenarios, 1 skipped: output-survives-the-pipe.` The release moved nothing, and this is the first release entry in this repository able to state that as a plain result rather than as a differential against `origin/main`. The single skip is the platform refusing `F_SETPIPE_SZ`, verified in 1.2 to be identical against the unmodified file.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every marker through the scenario that checks them all rather than through the bump script's report of what it wrote — the two would agree even about a marker neither knew about, which is what the Stop Rule guards, and none appeared. M3 asserts the promotion through both tools that consume the published store, strict in both. M2 is the prose check, and its job here is that a reader learns what the change did **not** do: the skip is not the fix, the Windows path is the case it exists for, and the mirror is what actually removes the tool. M4 is the one check this release could not have recorded before it: the same command that has ended `failed for:` in every release since 5.59.0 now ends `passed`.
      - Scope check: `git status --short` shows exactly this task's Touch entries — the package and lockfile, both plugin manifests, the three `keel:start` files, `keel/CHANGELOG.md`, the twelve `.claude/`/`.codex/` marker files, `scripts/validate_plugin.py`'s version constants, and the promoted `openspec/specs/keel-validation-runner/spec.md` — plus this change's own untracked directory. `keel gate task-complete` compared the worktree against the dirty set recorded at task-start. `scripts/validate_plugin.py` was already dirty from tasks 1.1 and 1.2; what this task added to it is the two version constants the bump script rewrote, and nothing else.
      - Findings: one, still open and not this task's to close. Issue #137 is fixed by this change and remains open, because closing it is a write to the tracker and `keel/config.yaml` has no standing authorization that covers one — the accepted vocabulary is `commit, push, release, archive, continuation`, and a tracker entry is exactly the gap issue #136 reports. This task's Stop Rule named the boundary in advance rather than discovering it at the close, and the close belongs to the user. The fix and its evidence are recorded here and in `keel/CHANGELOG.md` either way, so nothing is lost by the issue staying open; what would be lost is the guarantee that a repository action happens only where the project declared it may. Durable owner: https://github.com/TanglmChris/keel/issues/137
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "`no openspec on PATH`, and nothing else removed. Emptying PATH outright would also
  remove `node`, and the openspec shim needs it — the scenario would then be asserting that
  a shell without an interpreter fails." — the comment above the filter in
  `scripts/validate_plugin.py`. It states the intent correctly and describes the filter
  beneath it falsely: the filter removes directories, so on the layout this change fixes it
  removes `node` and the scenario does assert exactly what the comment says it must not.
  Updated by: 1.2, 2.1
- I2: "a scenario that cannot run because an external runtime is absent MUST report a skip
  rather than fail" — `keel-validation-runner / The full gate runs on a clean CI runner`. It
  stays true and is not rewritten. What it does not reach is a runtime the scenario's own
  fixture removed, which is a scenario that *can* run and broke itself; the ADDED
  requirement in this change states that case rather than widening this one, so the two do
  not overlap.
  Discard reason: the wording is correct after this change.
- I3: "the set of scenarios `npm test` reports as failing is identical to the set the same
  command reports on unmodified `origin/main`" and the Evidence beneath it — tasks 1.1 and
  2.1 of `openspec/changes/archive/2026-09-14-a-staleness-report-names-its-exception/tasks.md`,
  and the identical differential in `2026-09-14-a-coverage-claim-is-compared`. Those record
  what was observed when they ran, which this change does not make untrue; an archived
  anchor is a historical record and the gates refuse to recompile one.
  Discard reason: archived evidence records an observation, not a standing claim.

## Expectation Coverage

- E1: A PATH built to exclude a named tool removes that tool under every extension the host's lookup considers, and removes nothing else — the interpreter the scenario's own children need included (F1, F2, D1, D3). Covered by: 1.1
- E2: A scenario whose constructed environment left it without its interpreter reports the skip contract naming the missing runtime, and attributes no failure to the tool it was built to assert about (F4, F5, F6, D4). Covered by: 1.2
- E3: `npm test` is usable as a completion check on a host where `node` and a global `openspec` share a bin directory — no failing scenario, no recorded exception, no differential against `origin/main` (F3). Covered by: 1.2, 2.1
- E4: The proof holds on a host where the two binaries never shared a directory, so CI can fail on this defect (D5, D6). Covered by: 1.1
- E5: The published spec and every version marker move with the behavior (I1). Covered by: 2.1
- E6: Whether the mirror behaves on a Windows host, where symlink creation can be refused and the fallback is today's directory drop (A1, A2). Discard reason: deliberately not done rather than deferred. The layout that triggers this defect is not Windows-shaped — `npm install -g` writes its shims to `%APPDATA%\npm` while `node.exe` lives in `C:\Program Files\nodejs` — and where symlinking is refused the fallback is exactly today's behavior plus D4's named skip, so the worst case is strictly better than the status quo and never worse. Filing it as open work would claim a defect that this change cannot produce and no runner here can observe; the thing to re-measure is named in design.md A1, at the moment a Windows runner is added.

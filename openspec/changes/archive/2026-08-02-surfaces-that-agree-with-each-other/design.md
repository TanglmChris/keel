## Context

Keel's answers are worth reading because they are local, deterministic, and reproducible. This change is about a different property: whether two answers to the same question agree, and whether an answer's absence means anything.

Three of the four items here were found by using Keel on itself during 5.11.0 and 5.12.0, not by review. That is the pattern worth naming: an environment surface that is wrong looks exactly like one that is right, because the thing it would have told you is the thing you do not know.

## Goals / Non-Goals

**Goals:**
- Two Keel surfaces answering the same question give the same answer, because they read the same fact from one place.
- A refusal is issued only when the thing it names is actually absent.
- The version comparison survives a runtime too old to contain it.
- The shape that produced a mid-execution task merge is visible at authoring time.

**Non-Goals:**
- Keel still installs, updates, and selects nothing. Every item here reports.
- No new hook and no new event. The version instruction lands in resident text that is already read every session.
- No hard gate failure for the task-shape signal. It is a prompt; the judgment stays with the reviewer.

## Decisions

**F1** — Measured 2026-08-02. `keel --doctor` prints `python3: ok - python3`; `node scripts/run_python.js` on the same machine prints `no Python 3.10 or newer was found — tried python3 (3.9.6)`. Two surfaces, one question, opposite verdicts. *Basis:* ran both.

**F2** — `scripts/run_python.js` builds its candidate list from `python3` and `python` on non-Windows. `/opt/homebrew/bin/python3.11` is on PATH and is never tried, while `/usr/bin/python3` is 3.9.6. *Basis:* read the list, ran `which -a`.

**F3** — Installed plugin 5.7.1, CLI 5.7.0, repository protocol 5.12.0, measured on this machine. The SessionStart version comparison shipped in 5.9.0, so the installed plugin does not contain it, and no session reported anything. *Basis:* read `~/.claude/plugins/cache/keel-marketplace/keel/*/.claude-plugin/plugin.json`, `keel --version`, and the managed block.

**F4** — `keel context` prints status, next action, and reason, and never names the program that produced them. *Basis:* ran it.

**F5** — In `the-runtime-says-which-version-it-is`, tasks 1.1 and 1.2 declared the same two Touch entries and both `Strategy: vertical-tdd`, passed `task-start`, and were merged mid-execution. *Basis:* issue #41 and the archived tasks.md.

**F6** — `keel gate task-start` already emits `Warning:` lines — the re-record warning is one — so a non-blocking channel exists and needs no new output shape. *Basis:* observed during this session's reauthorizations.

**D1** — **The minimum Python version is defined once and read by both surfaces.** *Basis:* F1. The disagreement is not that the doctor had the wrong rule; it is that it had no rule and said ok for "a command that runs". Two independent statements of the same threshold would drift again the next time one moves, so `run_python.js` exports it and the doctor imports it. The doctor also prints the version it found, because `ok` without a number cannot be checked by the reader.

**D2** — **The interpreter search tries versioned names before refusing.** *Basis:* F2. `python3.13` down to `python3.10`, after the unversioned names so an already-correct `python3` is still preferred and no behavior changes for anyone it already worked for. The order is newest-first among the versioned names because a machine with several installed is likelier to want the newest, and any of them satisfies the suite. `KEEL_PYTHON` still short-circuits everything: an explicit choice is not overridden by a search.

**D3** — **The version comparison is asked for by the repository, not only by the plugin.** *Basis:* F3. This is the load-bearing decision. A check inside the plugin cannot report its own absence — silence means "aligned" and "too old to check" equally, and no amount of work inside 5.9.0's mechanism distinguishes them. The repository is the one participant that cannot be stale: the working tree is what everyone reads, and its resident protocol text is loaded every session by whatever runtime is running. So `AGENTS.md` asks the agent to state the Keel version that answered beside the protocol version the file declares. That is not a second implementation of the check; it is the check placed where it survives the failure it is about.

**D4** — **`keel context` names the Keel that produced its answer.** *Basis:* F4 and D3. The instruction in D3 needs a fact to report, and asking the agent to run a second command is a step that will be skipped. Printing it on the surface the protocol already requires costs one line and makes the comparison free. An old CLI will not print it, and that absence is itself informative in a way the plugin's silence is not — the reader is being asked for the number, so its absence is visible rather than indistinguishable from agreement.

**D5** — **The task-shape signal is a warning, not a `needs-review`.** *Basis:* F5, F6. Two tasks sharing an identical Touch set under a red-green strategy is a signal, not a verdict — a genuine vertical split can share files, and #41 says so itself. `needs-review` would be a verdict with no way to acknowledge it, leaving a legitimate split unstartable; there is no override mechanism and inventing one is a larger protocol change than the problem justifies. The warning names the other task, so the author compares two things rather than being told something is wrong.

**D6** — **The same question goes into `keel-review-checklist`.** *Basis:* the warning fires at `task-start`, which is before the author has implemented anything and therefore before the evidence that would settle it exists. The checklist runs at completion, when "did these two tasks turn out to be one behavior" is answerable. Together they cover the moment it is cheap and the moment it is knowable.

## Risks / Trade-offs

- **The identical-Touch warning could become noise.** Measured across this session's changes, no two tasks in one change declared identical Touch sets, so the signal is rare. If it stops being rare the warning stops being read, and the next reader should narrow it rather than leave it firing.
- **D3 puts an instruction where compliance is not enforceable.** The repository can ask; nothing makes an agent report it. That is accepted: the alternative is a mechanism that provably cannot work in the case it exists for, and an instruction that is followed most of the time strictly dominates a check that fires none of the time.
- **The versioned-name search adds up to four `spawnSync` calls** on a machine with no usable interpreter — the path that is about to fail anyway. On a machine where `python3` is already correct, nothing changes.

## Hidden Knowledge / Assumptions

**A1** — `python3.10`–`python3.13` covers what is plausibly installed. *Basis:* 3.10 is the suite's minimum and 3.13 is the newest release as of this change. *Owner:* the list is derived from the minimum rather than written twice, so a raised minimum shortens it automatically, and the scenario asserts a versioned name is found when `python3` is too old.

**A2** — A `Warning:` on `task-start` does not change its exit code or its `status`. *Basis:* F6, and the re-record warning already behaves this way. *Owner:* the scenario asserts `pass` and exit 0 alongside the warning, so a future change that promotes it to a verdict fails here.

## Coupled Iteration Contract

Not required. No task in this change regenerates an artifact that must be verified together with its source.

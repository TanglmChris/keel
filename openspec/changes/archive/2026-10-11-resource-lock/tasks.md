# Tasks

## 1. Allow codex

- [x] 1.1 `keel/config.yaml` allows codex as an external agent
  - Covers:
    - D7
    - F4
    - I1
  - Touch:
    - keel/config.yaml
  - Verify:
    - Strategy: evidence-first
    - Reason: the effect is one declaration and its comment; what proves it is the CLI reading it, and there is no behavior to write a failing test against first.
    - M1: `node bin/keel.js agents` lists `codex` as `allowed here` and `dsh` as `not allowed here`, and reports no problem with the declaration.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f155b714bf98ebd6c9633194ea955be42859cd55f912e5cb88464aa53dcb2e5b
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node bin/keel.js agents` lists `codex [bundled] /Users/my_home_mac/.local/bin/codex — allowed here` and `dsh … — not allowed here`, with no `Problem:` line.
    - Review:
      - Status: pass
      - Acceptance check: the CLI reads the declaration from the working tree and reports the allowance per agent, which is what `keel agents brief` consults.
      - Scope check: `git status --short` lists `keel/config.yaml` and this change's own directory.
      - Findings: none

## 2. Leases

- [x] 2.1 `keel lock acquire|release|list` and the shift check's lease item
  - Covers:
    - keel-resource-lock / A session leases a shared resource with an expiry and a note / A lease is acquired and listed
    - keel-resource-lock / A session leases a shared resource with an expiry and a note / A claim without a bound or a reason is refused
    - keel-resource-lock / A lease is exclusive, and a refused requester waits / A held resource is refused and the requester waits
    - keel-resource-lock / A lease is exclusive, and a refused requester waits / The holder renews
    - keel-resource-lock / A lease ends at release or at its noticed expiry, and waiters are told / Release by the holder tells the waiters
    - keel-resource-lock / A lease ends at release or at its noticed expiry, and waiters are told / An expired lease is freed by the next command
    - keel-shift-change / The readiness check reports what would be lost or left running / Each kind of loose end is reported
    - D1
    - D2
    - D3
    - D4
    - D5
    - D6
    - D8
    - F1
    - F2
    - F3
  - Read:
    - src/core/shift.js
    - src/core/chat/store.js
    - bin/keel.js
    - docs/shift-change.md
  - Touch:
    - src/core/lock.js
    - bin/keel.js
    - src/core/shift.js
    - scripts/validate_plugin.py
    - docs/resource-lock.md
    - README.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario resource-lock` exercises every keel-resource-lock scenario through the real CLI across two worktrees of one repository with roles `integ` and `sweep`: acquire and list from the other worktree; each refused malformed acquire leaving no lease; a refused acquire naming holder, expiry and note with the waiter recorded once after two attempts; renewal; a refused release by the waiter and a release by the holder that leaves a direct message to `sweep`; and an expiry, made by rewriting the lease file's `expires` into the past, freed by `sweep`'s `keel lock list` with a direct message to `integ` and a following acquire by `sweep` that succeeds. Two acquirers racing a free resource leave exactly one winner. It also requires `docs/resource-lock.md` to say the lease enforces nothing. Fails with: `resource-lock:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-change` requires `keel shift check` in `verify` to name a `lock` item for a live lease `verify` holds, and no such item once it is released. Fails with: `shift-change:`
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:538969ff492fee689b365560ef5f3e5ad7d103bcbac02c298c3643a5b08cc6ea
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. Re-run by this session in its own checkout: `node scripts/run_python.js scripts/validate_plugin.py --scenario resource-lock` reports `resource-lock scenario passed.`
    - M1.red: fail. Re-run by this session with `bin/keel.js` and `src/core/shift.js` restored to their committed versions and `src/core/lock.js` moved away: `resource-lock: malformed acquire does not name '--for': keel: repo path was provided more than once`, carrying the declared signature `resource-lock:`. Codex's own red is in its worktree's `runs/2.1/M1.red.log`, a claim this line does not rest on.
    - M1.green: pass. With codex's implementation and this session's review fixes (no direct message from a role to itself, every freed lease printed, a mutex older than 30 seconds removed, with a check that a stale mutex does not block `keel lock list`), the scenario passes. Restoring the stale-mutex code to `if (false)` made it fail with `resource-lock: a stale mutex blocked keel lock list`, so the added check detects its absence.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-change` reports `shift-change scenario passed.`
    - M2.red: fail. In the same restored state: `shift-change: could not acquire the shift fixture lease: keel: repo path was provided more than once`, carrying the declared signature `shift-change:`.
    - M2.green: pass. With the `lock` item in `keel shift check`, the scenario passes.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: both scenarios drive the real CLI across two worktrees sharing one chat store: refusals, waiter recording, renewal, holder-only release with its direct message, expiry by a rewritten lease file freed by the other worktree's command with its message, a two-process race with one winner, the unbound identity, and the shift check's `lock` item.
      - Scope check: `git status --short` lists the six Touch paths and this change's own directory. Codex's worktree changed the same six plus its own `runs/`, which stays there.
      - Findings: Resolved here: M1 — codex's implementation posted an expiry from a role to itself through a self direct group, and the guide said so; the running role is now not messaged and every freed lease is printed, which the scenario checks by the absence of `dm-sweep--sweep`. Resolved here: M1 — a mutex left by a killed command blocked every later lock command until removed by hand; one older than 30 seconds is now removed, and the scenario checks it. Discard reason: codex's report of 19 failing scenarios under `npm test` came from its sandbox, where temporary repositories sat inside this one and its new files were untracked; in this checkout the only failure was `the-tarball-is-the-repository` for the untracked `src/core/lock.js`, resolved by staging it.

## 3. Release

- [x] 3.1 Release and promote the spec
  - Covers:
    - E3
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/marketplace.json
    - .claude-plugin/plugin.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validate_plugin.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-resource-lock/spec.md
    - openspec/specs/keel-shift-change/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the ADDED requirements become `openspec/specs/keel-resource-lock/spec.md` with a Purpose, the MODIFIED readiness requirement is promoted into `openspec/specs/keel-shift-change/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:fed60f91fa6f5e4c8279f99da24b5586ad8ac8a6b5c906b7cd7013b36d06c109
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. After merging `main` (5.99.6, #267), `node scripts/bump_version.js minor` moved every marker to 5.100.0. With the 5.100.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The ADDED requirements became `openspec/specs/keel-resource-lock/spec.md` with a Purpose, and the MODIFIED readiness requirement replaced its published copy in `openspec/specs/keel-shift-change/spec.md`; `published-specs-validate-strictly` reports `32 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the new capability is published with its three requirements and scenarios, the readiness requirement names leases, and the changelog names the issue, the behavior, and the delegation.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and both specs, all in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after merging `main` and the bump to 5.100.0 reports `validation --all passed: baseline plus 240 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- I1: "This repository declares none." — the closing line of the `external_agents` comment in `keel/config.yaml`. Updated by: 1.1

## Expectation Coverage

- E1: Codex may be handed this repository's tasks, as the owner decided on 2026-10-11 (D7). Covered by: 1.1
- E2: Sessions claim a shared resource with a bounded, explained, exclusive lease that every worktree sees, that ends at release or noticed expiry with the waiters told, and that a shift change does not leave behind (D1–D6). Covered by: 2.1
- E3: The release carries it. Covered by: 3.1
- E4: Counted resources such as CPU slots are not leased as a count (D8). Discard reason: a lease is exclusive by design; the guide names one lease per slot as the workaround, and a counted semaphore waits for a project that needs it.

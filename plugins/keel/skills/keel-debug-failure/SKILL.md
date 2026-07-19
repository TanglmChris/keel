---
name: keel-debug-failure
description: Debug Keel agent command or validation failures under Keel's selected OpenSpec task contract. Use when `/opsx:apply` or a selected task reports failed commands, failing tests, validation errors, retry-fuse decisions, or needs an evidence-bound failure report.
---

# keel-debug-failure
## Purpose

Use this skill when a command or validation path fails. Keep the investigation tied to the selected OpenSpec task. This skill owns the retry fuse, the task-contract binding, checkout preservation, and the failure-report shape; generic diagnosis mechanics (how to reproduce, minimise, or instrument) belong to the host runtime and are not restated here.

## Context to read

Read the selected OpenSpec task's Commands, Acceptance, Coupling, Candidate Boundary, Autonomy boundary, Stop Rules, Evidence, Stop if, Read, Touch, and Mode fields. When `Coupling: required`, also read design.md's Coupled Iteration Contract. Read the failed command output and any repository files needed to reproduce or explain the failure.

## Domain lenses

When the change's artifacts or the failing surface signal a domain, consult the matching lens's `Execution and review checks` section from `keel/lenses/` — the lens whose `Applies when:` header matches — before locking a root-cause hypothesis, and load only that one. When no lens matches, load nothing.

## Fuse

Try the same failure at most 2 attempts. If it still fails, stop and report the original key error plus what changed during each attempt.

For `Coupling: required`, an allowed provisional failure inside a candidate does
not count as an attempt. Count one attempt only when the same final assertion
fails at the candidate completion gate. Follow the task's immediate task-stop
rules for scope breach, missing design authority, non-reproducible evidence,
or a baseline or acceptance change during a candidate.

Preserve the current checkout on verification failure or context pressure.
Only roll back to last-green when the selected task or human instruction
explicitly authorizes it, and keep the failure evidence available.

## Report boundary

Follow-ups are limited to directly observed blockers, risks, missing scope, or escalation needs. Do not include roadmap suggestions, new feature suggestions, unrelated architecture critique, or opportunistic refactor suggestions.

When the minimal fix needs files outside Touch, report an Out-of-scope Need with file or area, why needed, consequence if unchanged, minimal proposed change, and evidence. Do not modify those files.

## Standalone use

When used alone, report Summary, Failed command, Failure evidence, Attempts, Current hypothesis, and Required decision.

## Why

When Keel's agent needs a decision from the user, the resident protocol and `keel-align-expectations` say to explain the choice and recommend an answer, but never to offer it as something the user can select. On 2026-09-28 the owner asked that decisions be presented as selectable options wherever the host offers that surface; in the same session two of three decisions were asked in prose and needed a typed reply (issue #174). The skill's remark that presentation is "the host runtime's concern" currently reads as permission to ask in prose.

## What Changes

- The resident protocol's `## User-facing communication` states that a decision with enumerable answers is asked through the host's structured-choice surface when one is offered, recommendation first and marked; prose remains for open questions and for hosts without such a surface.
- `keel-align-expectations`' deep path carries the same rule without naming any host tool, and its Purpose no longer reads as leaving presentation unconstrained.
- No gate judges whether an agent used the surface: that is presentation, which no deterministic check can observe.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-expectation-alignment`: deep-path questions with enumerable answers are offered as selectable options where the host provides that surface.

## Impact

`AGENTS.md`, the `keel-align-expectations` skill in `src/skills` and its shipped copy under `plugins/keel/skills`, one validation scenario, and the expectation-alignment spec. No CLI behavior, dependency, or gate changes.

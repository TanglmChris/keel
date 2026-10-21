## Why

Issue #411. The owner approved this disposition table on 2026-10-21 (https://github.com/TanglmChris/keel/issues/411#issuecomment-6309678324). This change makes the two adopted rows true:

- **Row 7, review-checklist.** "基础清单简短，专项条件按需加载". `src/skills/keel-review-checklist/SKILL.md` is 96 lines, and every activation reads four conditional sections. They apply only when:
  - the task declares `Coupling: required`;
  - a domain lens matches;
  - the change adds or materially expands a skill;
  - the work followed an accepted plan-mode artifact.
- **Row 8, handoff.** "区分任务选择 override 与 shift 运行便条，不产生第二份任务状态权威". `src/skills/keel-handoff/SKILL.md` never mentions the shift note, so the two are easy to confuse. Both are short files written for the next session.

The plugin-copy parity check in `native-plugin-manifests` compares only `SKILL.md` and `guidance.md`. Any other file split out of a skill could drift from the source unseen.

## What Changes

- **review-checklist moves four sections into `conditional-checks.md`, beside its `SKILL.md`.** The sections are the coupled-execution check, domain lenses, skill change review, and the planning artifact funnel. `SKILL.md` gains a short `## Conditional checks` section that names each condition and says to read the file only when one applies. The moved text keeps its criteria word for word. It goes in its own file, not in `guidance.md`, because a guidance file "states no criterion" and these checks are criteria.
- **The handoff skill gains one paragraph.** It says the shift note from `keel shift ready` hands working context to a role's next session and selects no task. HANDOFF overrides which task `keel context` selects. Neither holds task state, which belongs to OpenSpec.
- **The parity check compares every file under each canonical skill directory with the plugin copy,** by file set and by bytes.
- **The checks that pinned the moved text read it where it now lives.**

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-native-plugin-package`

## Impact

The change touches:
- the two skills and their plugin copies;
- `scripts/validation/common.py`, for the skill doc requirements;
- `scripts/validation/hosts.py`, for the parity check;
- `scripts/validation/docs.py`, for the plan-funnel check;
- `scripts/validation/registry.py` and one new scenario;
- the published spec and the changelog.

No product code changes.

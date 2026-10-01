## Why

The owner decided in #190 that Keel must not restrict the model's preference for subagents. Current projection authorization and mandatory delegation declarations impose extra execution permission despite an already authorized task.

## What Changes

- Model-chosen read-only helpers need no extra user activation flag.
- Model-chosen implementation delegates require existing task write authority and a matching active guard, not a mandatory tier declaration.
- Keep optional declared tiers as metadata and preserve legacy CLI behavior; explicitly select helper or implementation posture.
- Align protocol, schemas, skills and specs; native goals still require explicit activation and host policy remains authoritative.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-authorized-delegation`: guarded task authority rather than declaration-based permission.
- `keel-native-runtime-projection`: helper/delegate posture without extra subagent activation.
- `keel-openspec-surface-overlay`: consistent instructions about model choice and boundaries.
- `keel-single-task-goal-execution`: goal activation does not constrain ordinary helpers.

## Impact

Projection CLI and Core, generated surfaces, task templates, skills, configuration documentation and regression scenarios. No scheduler, model selection, host policy bypass, or Keel ownership transfer.

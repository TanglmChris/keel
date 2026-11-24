## Decisions

- D1 — Inventory code and existing specs for roles, Git observation, collaboration and branch leases, standing authorization, task authority, handover, and orchestration. Separate differences of policy from genuinely duplicated inputs. Preserve compatibility and name a durable owner for current remaining work.
- D2 — Reuse the worktree porcelain scanner for the branch inventory's checked-out check. Retain the Git 2.34 text fallback, handling of a failed optional branch lookup, exclusion of checked-out branches, and all role, trunk and authorized prune semantics. No output or interface change.

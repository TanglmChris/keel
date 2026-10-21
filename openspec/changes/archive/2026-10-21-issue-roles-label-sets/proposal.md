## Why

Issue #433, approved by the owner on 2026-10-21. `issue_roles:` maps one label to one role (`readIssueRoles` in `src/core/config.js` keeps a `Map` from label to role). A repository that runs several teams of the same shape cannot route the labels those teams share.

kaiwu-ip declares `design: kaiwu-design-iecc` and is starting a second IP team (`kaiwu-pm-rmw`, later `kaiwu-design-rmw`). An issue of that team carries `design` + `dmc_rmw`, and today every update of it goes to `kaiwu-design-iecc`, the wrong team. The only workarounds are a label spelling per team, which multiplies the label vocabulary the issue templates use, or leaving the second team unrouted.

## What Changes

- **A route may name a set of labels.** A key of the form `<label> + <label>` routes an issue only when it carries every label in the set. A single-label line keeps working unchanged.
- **The most specific route wins.** When an issue matches two routes and one route's labels are a strict subset of the other's, only the larger set's role is sent the update. Routes that are not nested both send, as today, since one issue may concern two teams.
- **A quoted key stays one label.** A label that really contains ` + ` can still be named by quoting the key.
- **A line that is neither shape is still reported and routes nothing.** So is a set with an empty or repeated label.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-coordinator-patrol`

## Impact

`src/core/config.js`, `src/core/patrol.js`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, the README in both languages, the `keel/config.yaml` comment, the published spec, and the changelog.

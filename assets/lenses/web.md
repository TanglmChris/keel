# Web lens

Applies when: the change touches UI, API, routing, auth/session, persistence, migrations, async/loading/error states, accessibility, or backend integration — for example when Touch includes `.tsx`/`.jsx`/`.ts`/`.js`/`.css`/`.html`/`.sql` or the change artifacts describe a route, endpoint, component, or schema.

Domain lens for web frontend/backend work. Use during alignment, execution, and review when UI, API, routing, persistence, or integration behavior may hide product assumptions.

## Material risk surface

Treat these as deep-path candidates when the change touches them: UI-observable behavior, public interface contracts, routing, auth/session behavior, persistence, migrations, async state, loading/error states, accessibility expectations, browser compatibility, and backend integration boundaries. Ask only questions that materially affect Acceptance, verification checks, Touch, specs, design decisions, or non-goals; stop when the task contract can be written without guessing.

## Durable placement

- specs for user-visible behavior, API behavior, error handling, and scenarios.
- design.md for framework choices, data flow, migration notes, auth/session assumptions, and trade-offs.
- tasks.md for Covers, verification, Touch, and stop/autonomy details.

## Evidence expectations

Prefer public interface evidence: UI behavior through a rendered page or component workflow (no self-mocked internals); API behavior through route/client contract checks including user-affecting failure paths; data changes through migration/integration evidence when persistence semantics change; accessibility or responsive checks when Acceptance names them.

## Execution and review checks

While implementing and reviewing, prove behavior through the public interface: exercise UI changes in the rendered page, hit at least one user-affecting failure path (auth expiry, empty, error, slow response), and treat route, status-code, header, and payload shape as contract — a contract change needs a durable spec or task owner before review passes. Run persistence changes through a real forward migration and confirm auth/session boundaries did not silently widen. In review, reject build-only or component-shape evidence, and require explicit evidence for every loading, error, or empty state that Acceptance names.

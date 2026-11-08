## Why

Issue #517 (Keel 5.222.0): a change whose `.openspec.yaml` declares `skip_specs: true` and carries no `specs/` directory is reported by `openspec status` as `specs: skipped` with every other artifact done, yet `keel gate change-close` fails it with `missing-delta-spec` ("archive requires at least one change delta spec"). A tidy-up change that adds or modifies no capability can therefore never be archived without bypassing the gate. `src/` never reads `skip_specs`. Taken up at the owner's standing request on 2026-11-08 ("继续，除 175，其它都要解").

## What Changes

- **`keel gate change-close` honors the marker.** When the change's `.openspec.yaml` declares `skip_specs: true`, a change with no `specs/**/spec.md` no longer gets `missing-delta-spec`, for `--action archive` and `--action sync` alike (a skipped capability has nothing to sync).
- **A self-contradiction fails by name.** A change that declares `skip_specs: true` and still carries any file under `specs/` fails with a new `skip-specs-with-specs` problem naming the file, as OpenSpec's own validate does, instead of passing quietly.
- **Unchanged:** a change without the marker still needs one delta spec; the marker is read as the line `skip_specs: true` in `.openspec.yaml`, anything else (absent, `false`, unreadable file) counts as undeclared and keeps today's behavior.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-core-gates`

## Impact

`src/core/gates.js`, `scripts/validation/skipspecs.py`, `scripts/validation/registry.py`, the published spec, and the changelog.

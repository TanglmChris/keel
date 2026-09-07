## Why

The protocol version written into every managed `AGENTS.md` — `<!-- keel:start version=5.48.0 -->` — is written by the installer and read back by nothing that runs locally. Both marker parsers skip the attributes (`bin/keel.js:1342` and `scripts/install_to_repo.py:18` both match `keel:start(?:\s+[^>]*)?`), so `keel --check` and `keel --doctor` confirm the block is present and never look at what version it claims.

The one place the comparison exists is `plugins/keel/scripts/session-start.js:163`, inside the plugin's SessionStart hook. `AGENTS.md` already states why that is not enough: a plugin too old to contain the check stays silent, and its silence is indistinguishable from agreement. Doctor itself reports `native plugin runtime: manual` — installation, enablement, trust, and activation are never verified — so on any repository the check may simply not be running, with no signal either way. The protocol's current fallback is to ask the agent to compare the two numbers by hand every session.

Four repositories on this account measure the cost: `chip_sec_flow_v2` at 5.14.0, `my_xhs` at 5.20.0, `rtl_ppa_prj` and `dasauto` at 5.39.0, against a 5.47.0 CLI. None of them was told. In `chip_sec_flow_v2` the drift was not cosmetic: 176 durable-owner references had become dead self-pointers under a rule its installed protocol predates.

## What Changes

- `keel --doctor` reads the `version=` attribute of the repository's `keel:start` marker and reports it beside the version of the CLI that is running, naming which is behind and the remedy for that direction.
- The comparison is model-free and depends on no plugin runtime: the marker is read from the working tree, and the CLI's version is its own.
- Drift is reported as a warning and does not change doctor's exit code. It is an out-of-date install, not a broken one, and a release day should not turn every consumer's pipeline red.
- A marker that is absent or carries no readable `version=` is reported as not comparable rather than as agreement — the same distinction `session-start.js` already draws.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-target-surface-diagnostics`: doctor gains a protocol-version-drift report, in the same shape as its existing report distinguishing a keel-resolvable `openspec` from a PATH-reachable one.

## Impact

- `bin/keel.js` — the doctor path only; one new reported line.
- `scripts/validate_plugin.py` — one new scenario.
- No change to `keel --check`, to any gate, to the installer, or to the marker format itself.
- Risk: a repository that deliberately pins an older protocol now sees a standing warning. Accepted, because the warning names the direction and the remedy and costs nothing but a line; and because the alternative — silence — is what the four repositories above got.

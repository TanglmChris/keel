## Why

Keel presents itself as runtime- and domain-agnostic execution discipline that leans on native capabilities rather than reinventing them. The one place it ships opinionated domain content is the bundled `web` / `hardware` / `hardware-dsl` references inside `keel-align-expectations`. Those references:

- duplicate a slice of what host-native domain skills already do (accessibility, frontend, API, testing), contradicting the "lean on native capabilities" positioning;
- cover an arbitrary three domains, which reads as scope creep for a process tool and leaves every other domain unserved;
- add maintenance and validator surface that is tangential to the core engine.

The mechanism is worth keeping — the alignment and verification gates genuinely benefit from a domain-shaped risk lens loaded on demand. The bundled *content* is what does not belong in a pure process tool.

## What Changes

Make the domain layer pluggable. The core keeps the mechanism (detect a domain signal, load the one matching lens, feed alignment/execution/review); the lens content becomes user-authored.

- Lens content lives in the target repo at `keel/lenses/*.md`, authored and owned by the user.
- Lenses are self-describing: each declares an `Applies when:` header, so the core hardcodes no domain list and no extension map.
- The `keel-align-expectations`, `keel-tdd-or-test-first`, `keel-debug-failure`, and `keel-review-checklist` skills stop pointing at `references/` and instead consult `keel/lenses/`, loading only the lens whose `Applies when` matches the change's domain signal.
- The three current references ship as opt-in templates under `assets/lenses/`, not loaded by default. A new `keel lenses` command scaffolds them: `keel lenses add <name>` copies a template into `keel/lenses/`, and `keel lenses list` shows available templates and installed lenses.
- The dead `ALIGNMENT_REFERENCES` constant is removed.

## Capabilities

### New Capabilities

- None as a separate spec. The `keel lenses` CLI is added as a requirement under the existing `keel-domain-profiles` capability, which owns the domain-knowledge surface.

### Modified Capabilities

- `keel-domain-profiles`: domain knowledge changes from references bundled inside `keel-align-expectations` to user-authored, self-describing lenses under `keel/lenses/`. Built-ins become opt-in templates under `assets/lenses/` scaffolded by `keel lenses`. Single-source/byte-identical authority applies to the shipped templates, not to user lenses. Execution and review skills consult the matching lens from `keel/lenses/`.

## Impact

- Skills no longer bundle `references/`; agents consult `keel/lenses/` when a lens's `Applies when` matches. Repos with no lenses fall back to the domain-agnostic path unchanged.
- Migration: `keel lenses add web|hardware|hardware-dsl` restores the prior content into `keel/lenses/` for anyone who relied on it.
- Validator: the `domain-profiles`, `expectation-alignment-skill`, `authoring-continuity`, and `domain-execution-references` assertions shift from "references bundled in the skill" to "pluggable mechanism + opt-in templates + scaffold CLI." The `Execution and review checks` README needle is preserved via the templates.
- CLI gains a `keel lenses` action; `bin/keel.js` loses the dead `ALIGNMENT_REFERENCES`.
- Minor version bump to 5.2.0.

### Non-goals

- Shipping more domains than the three existing templates.
- Auto-installing lenses on `keel --init` (they stay opt-in).
- Changing how domain *signals* are detected from change artifacts / Touch extensions.

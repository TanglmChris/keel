## Context

Keel carries the OpenSpec CLI as a dependency and runs it through
`findOpenSpecCommand()`. That function's candidate list assumes the dependency's
bin sits under Keel's own package root, which is true of a checkout of this
repository and false of every install.

## Goals / Non-Goals

**Goals:**

- `keel openspec` resolves wherever npm actually put the dependency.
- Doctor's advice matches what is wrong.
- A defect that only appears outside this checkout cannot pass a release again.

**Non-Goals:**

- Vendoring OpenSpec, or pinning its location. See D2.
- Translating arguments in the proxy. Refused in 5.56.0 and unchanged.
- Network access in the suite. See D5.

## Decisions

- F1 — `openspecCandidates()` returns `PACKAGE_ROOT/node_modules/.bin/openspec`
  if it exists, then bare `openspec`. Basis: `bin/keel.js`, read 2026-09-08.
- F2 — On `npm install @christang/keel@5.57.0` into an empty project, the bin is
  at `<project>/node_modules/.bin/openspec` (a symlink to
  `../@fission-ai/openspec/bin/openspec.js`, reporting 1.12.0), and
  `<project>/node_modules/@christang/keel/node_modules` does not exist. `keel
  openspec --version` fails with `openspec is not resolvable` at exit 1, and
  `keel --doctor` reports `openspec: missing`. Basis: run against the published
  tarball, 2026-09-08.
- F3 — This repository is a direct consumer of `@fission-ai/openspec`, so its
  `node_modules/.bin/openspec` is under `PACKAGE_ROOT` and F1's first candidate
  hits. Basis: the same lookup passing here while failing in F2.
- D1 — Walk from the package root upward through each ancestor's
  `node_modules/.bin`, then fall back to PATH. Basis: F2 — this is how Node
  resolves a module, and it is the only rule true of the hoisted, nested, and
  workspace layouts at once. The nearest match wins, so a project pinning its own
  OpenSpec is honored over one further up.
- D2 — Do not resolve through `require.resolve` of the dependency's package.
  Basis: it would bind Keel to the dependency's internal bin path, which is the
  dependency's to change; the `.bin` directory is the published contract between
  npm and a consumer, and the walk reads exactly that.
- D3 — Doctor separates "the dependency is not installed" from "it is installed
  and Keel cannot reach it". Basis: F2 — the current advice, reinstall so npm
  installs the dependency, is the one action that cannot help when npm already
  did, and a diagnostic that sends the reader somewhere useless is worse than
  one that says less.
- D4 — A scenario builds the hoisted layout and asserts the proxy and doctor
  against it. Basis: F3 — the bug survived 170 scenarios because every one of
  them runs inside the single layout where the lookup works. The assertion has to
  be about a layout, not about a behavior in this checkout.
- D5 — The scenario constructs the layout from the packed tarball rather than
  installing from the registry. Basis: the defect is about where a file sits, not
  about npm's network behavior, and a suite that reaches the network fails for
  reasons that have nothing to do with the code under test.

## Hidden Knowledge / Assumptions

- A1 — A release gate that only exercises the working tree cannot see a defect
  whose cause is the layout the working tree is not in. The fix is a scenario
  that builds the other layout, not more coverage of this one. Durable owner:
  https://github.com/TanglmChris/keel/issues/129

## Risks / Trade-offs

- Walking to the filesystem root touches a few `existsSync` calls per invocation
  in the worst case. It stops at the first hit, which on a real install is one
  or two levels up.
- A stray `node_modules/.bin/openspec` in an ancestor directory would now be
  found. That is what a developer intends by putting it there, and it is the same
  rule Node applies to every import in the project.

## Open Questions

None.

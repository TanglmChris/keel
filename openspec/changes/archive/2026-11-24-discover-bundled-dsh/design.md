## Decisions

- D1 — Use the historic executable application bundle on macOS when available. Otherwise use the same PATH resolver as the other bare executable names. An explicit machine executable always replaces the bundled default, even when the machine entry points at a missing file.
- D2 — Listing and brief generation use the shared catalog input and executable resolver. Discovery reports local executable availability. Project allowance, worktree checks, provider connectivity and credentials remain independent.

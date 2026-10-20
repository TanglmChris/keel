## Context

The facts come from the 2026-10-20 audit of README.md against the CLI and specs, and of README.zh-CN.md against README.md, re-measured on 902c790 (5.175.0).

## Facts

- F1 — `keel --help` on 5.175.0 lists 16 subcommands and these install flags: `--init`, `--install`, `--clear`, `--uninstall`, `--update`, `--check`, `--doctor`, `--version`, `--help`. `--check` and `--doctor` refuse `--dry-run` with exit 2, and `--clear` runs the uninstall path.
- F2 — Exit codes, measured: an unknown flag exits 2 (`fail()` in `bin/keel.js`), a missing change exits 1, a gate failure exits 3, and `needs-review` exits 4.
- F3 — `STANDING_AUTHORIZATION_ACTIONS` has 13 names, and `SCOPED_AUTHORIZATION_ACTIONS` has 5, `push-protected` among them.
- F4 — `--doctor` reports a repository behind its install with "run keel --install --target <t>".
- F5 — `README.zh-CN.md` has 16 `##`/`###` headings, `README.md` has 29, and three zh sections have no English counterpart: 写入守卫, 一次性投影, 对齐与技能纪律.

## Decisions

- D1 — The English README is the source. Each statement F1–F4 contradicts is rewritten to what the CLI does, and the Commands block mirrors `keel --help`.
- D2 — The Chinese README mirrors the English section by section, in the same order. Content found only in the Chinese version moves into the matching section when it is still true and is dropped when it is not. Identifiers, commands, paths, and code blocks stay as they are.
- D3 — The scenarios derive their lists from the code and the CLI, not from a copy, so a command or name added later without its README line fails:
  - subcommands and flags come from the `keel --help` usage lines;
  - authorization names come from `config.js`;
  - section parity is a count of `##` and `###` headings, the one structural measure that needs no translation table.
- D4 — The README's word for the vocabulary size must equal the count read from `config.js` ("thirteen names").

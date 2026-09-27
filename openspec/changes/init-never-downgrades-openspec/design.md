## Findings

- F1 — `runProjectInit()` runs `openspec init --tools <t> --force`, then the installer, then `openspec update --force`, then the overlay refresh. `keel --install` runs only the installer and the overlay refresh, so the 5.76.0 `protocol-refresh` path never rewrites OpenSpec surfaces.
- F2 — OpenSpec stamps each skill it writes with `generatedBy: "<version>"` in the frontmatter. In `rtl_ppa_prj`, five `.claude/skills/openspec-*/SKILL.md` carry `generatedBy: "1.13.2"`. Keel's OpenSpec is 1.6.0.
- F3 — `openspecReportedVersion(command)` already reads the resolved OpenSpec's version for doctor's `openspec` line.
- F4 — In `rtl_ppa_prj`, `.claude/settings.json` declares `keel-marketplace` `autoUpdate: true` and is untracked (`?? .claude/settings.json`). Doctor reported `plugin auto-update: ok`.

## Decisions

- D1 — **Surface generator version.** It is the highest `generatedBy` across `SKILL.md` files under `.claude/skills/openspec-*`, `.codex/skills/openspec-*`, `.agents/skills/openspec-*`, and `.opencode/skills/openspec-*`. Every root is read, because #169's layout is `.agents/skills` and a repository may carry more than one target. It is compared with the resolved OpenSpec numerically as `X.Y.Z`. No stamp means nothing to protect.
- D2 — **The init guard.** When the surfaces are strictly newer, `runProjectInit()` skips both `openspec init --force` and `openspec update --force` and prints one `keel:` line naming both versions and #168. It still runs the installer and the overlay refresh, so the protocol and Keel's overlays move while OpenSpec's templates stay. A dry run prints the same decision. An equal or older generator changes nothing, so init behaves exactly as before.
- D3 — **Doctor `OpenSpec surfaces` line.** Printed only when a stamp exists. It is `ok - written by X; Keel runs Y`. When the surfaces are newer, it is `warning - written by X, newer than the OpenSpec Keel runs (Y); keel --init leaves them unrewritten rather than downgrading them, and keel --install --target <t> refreshes the protocol without touching them`.
- D4 — **Untracked declaration.** When `pluginAutoUpdateDeclaration()` finds `autoUpdate: true`, the repository is a Git work tree, and `git ls-files --error-unmatch .claude/settings.json` fails, the status is `warning`. The detail says only this checkout declares it and names `git add .claude/settings.json`. Outside a Git work tree the declaration is reported as before.

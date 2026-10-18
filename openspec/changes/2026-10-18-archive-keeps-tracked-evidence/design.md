## Context

#352 suggested `git mv` or re-adding the moved tracked paths, or at least a warning. OpenSpec performs the move itself, so Keel cannot substitute `git mv`; re-adding after the move has the same effect on the index. The archive overlay already directs agents to `keel openspec` (`Keel makes openspec invocable for skill-driven agents`), so the passthrough is where the move happens; an archive done another way still passes `change-close --action archive` first.

## Facts

- F1 — Git ignore rules never untrack a tracked path, but a moved file is a new path: at `openspec/changes/archive/<dir>/evidence/…` the change's own `.gitignore` applies to an untracked file, so `git add -A` stages only the deletion.
- F2 — `git ls-files -c -i --exclude-standard -- <dir>` lists tracked files that an ignore rule matches; these are exactly the files a move would drop.

## Decisions

- D1 — Before forwarding `archive <name>`, the passthrough records the files git tracks under `openspec/changes/<name>/`. After OpenSpec exits 0, it finds the archived directory (`openspec/changes/archive/<name>` or `…/<date>-<name>`), and for each recorded file whose archived path exists and is ignored, runs `git add -f -- <paths>`, then prints `keel: re-added <n> tracked file(s) the archive move left ignored (#352)`. Nothing runs outside a Git work tree, when OpenSpec fails, or when no file is affected.
- D2 — `change-close --action archive` adds a warning, not a problem, listing up to five such files and their count, naming `keel openspec archive` as the archive that keeps them and `git add -f` as the remedy after any other move. A warning leaves the verdict as it was, since the evidence is intact until the move.

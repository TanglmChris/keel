## Context

Issue #175 and its 2026-10-03 comment (5969374155) record the portal and the validation result. Relevant facts already in the repository:
- `package.json`'s `files` list (`bin/`, `scripts/`, `src/core/`, `assets/`, `plugins/`, `README.md`, `npm-shrinkwrap.json`) is what `the-tarball-is-the-repository` checks, at 65 packed files.
- The root `.claude-plugin/plugin.json` declares the skills, the agent, and the hooks, all as paths under `./plugins/keel/`. The hooks run `${CLAUDE_PLUGIN_ROOT}/plugins/keel/scripts/*.js`, and those scripts run the package's own `bin/keel.js`.
- The release job (`.github/workflows/publish.yml`) publishes, then tags and creates the release with `GH_TOKEN`, appending `scripts/official_entry.js` output to the notes.

## Goals / Non-Goals

**Goals:**
- The directory sees a plugin named `keel-openspec` with an icon, small enough to be scanned whole.
- Each release refreshes it without the owner acting.
- Nothing changes for the npm package name, the repository name, or the `keel` plugin id that marketplace installs use.

**Non-Goals:**
- Submitting automatically. The owner submits once, in the portal.
- Changing how the directory reviews or lists the plugin.

## Decisions

- **F1** — The portal (claude.ai/directory/manage, 2026-10-03) takes a GitHub repository with an optional subfolder and branch. It tracks that branch, and new commits there are picked up and scanned. It validates `.claude-plugin/plugin.json` in the chosen folder. Basis: the portal's step 1 text and its validation of `TanglmChris/keel`, recorded on #175.
- **F2** — The holds on `TanglmChris/keel` @ 5ac896a were: brand (`"keel" is the name of directory connector "keel"`); confusable names; a scan limited to the first 512 files; `keel/CHANGELOG.md` over 256 KiB; a lockfile reviewer hold; four credential findings in README and archived records; and no icon. The icon is taken only on the first save or submit. Basis: the same validation.
- **F3** — The files `npm pack` publishes form a complete Claude plugin once a root manifest is added. Every manifest path is under `plugins/keel/`, and `bin/keel.js` resolves `scripts/run_python.js`, which `files` includes. Basis: `package.json` and the root manifest.
- **D1** — `scripts/directory_tree.js <dir>` builds the tree from `npm pack --json --pack-destination <tmp>` and extracts the tarball's `package/` into `<dir>`. It writes `.claude-plugin/plugin.json` as the root manifest with `name` set to `keel-openspec`, and copies `assets/directory/icon.png` to `.claude-plugin/icon.png`. It refuses a `<dir>` that exists and is not empty. Basis: F3, and the owner's choice of name and branch.
- **D2** — `scripts/directory_branch.js <version> <sha> [--no-push]` builds the tree in a temporary directory and checks out `claude-directory` from `origin` into a temporary worktree, or starts it as an orphan branch when the remote has none. It replaces the worktree's contents with the tree. It commits as `github-actions[bot]` with the message `keel-openspec <version> from <sha>`, pushes to `origin claude-directory` unless `--no-push`, and prints the new commit. A tree identical to the branch head commits nothing and prints the head. Basis: F1.
- **D3** — The release step runs `node scripts/directory_branch.js "$VERSION" "$SHA"` after `gh release create`'s inputs are ready. In place of the "Official directory entry" block, the notes say that the directory listing `keel-openspec` tracks branch `claude-directory`, now at the printed commit. `scripts/official_entry.js` is deleted. Basis: F1, because a pinned entry is not what the directory takes.
- **D4** — The icon is the SessionStart block mark rendered as a 24×6 grid: light cells on a dark rounded square, 1024×1024 PNG, 8.7 KB. It sits at `assets/directory/icon.png`, inside the npm `files` list, so the tree builder finds it in the pack. Basis: the portal's icon rule (F2) and the owner's request for a draft.

- **F4** — The portal's first validation of `claude-directory` @ 435ca76 (5.90.0) passed name and publisher checks, scanned all 97 files, and found the icon. Two of its nine holds named development-only scripts: `scripts/validate_plugin.py` (1.5 MB, not fully inspected) and `scripts/directory_tree.js` ("image or font file the plugin's code could run", because it copies the icon). The Links section filled only the repository, because the manifest carries no `homepage`. At runtime the shipped code references only `scripts/run_python.js` and `scripts/install_to_repo.py`. Basis: the portal on 2026-10-03 and a grep of `bin/`, `src/core/`, and `plugins/`.
- **D5** — The directory tree keeps, from `scripts/`, only `run_python.js` and `install_to_repo.py`, the scripts the shipped code runs. Its manifest adds `homepage: https://github.com/TanglmChris/keel`. The npm package is unchanged. Basis: F4 and the owner's choice to trim before the first submission.

## Risks / Trade-offs

- The tree carries `bin/` and `src/`, so the reviewer reads the CLI as part of the plugin. That is the same code the marketplace install already runs.
- A release whose push to `claude-directory` fails still has its npm package and tag. The step fails the job visibly, and the next release's push carries both releases' changes.
- The four credential findings came from README badges and archived records. Archived records are not in the tree. The README badge stays, for a reviewer to confirm.

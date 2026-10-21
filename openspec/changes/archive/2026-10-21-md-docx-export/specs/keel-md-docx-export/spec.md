## ADDED Requirements

### Requirement: Setup lists before it installs

`keel docx setup` MUST print every package it would install with its licence and size, the environment directory, and that nothing was installed, and MUST install nothing and create no environment unless `--yes` is given. With `--yes` it MUST install only into the Keel-managed environment under `$KEEL_HOME/docx/` (default `~/.keel/docx/`), never globally, and MUST mark the environment ready only after every step succeeded.

#### Scenario: Without --yes nothing is installed
- **WHEN** `keel docx setup` runs
- **THEN** it names python-docx, lxml, Pillow, marked, and sharp with their licences, the environment path, and `--yes`, runs no installer, creates no environment directory, and exits 0

#### Scenario: With --yes the packages go into the managed environment
- **WHEN** `keel docx setup --yes` runs
- **THEN** a virtual environment is created under the environment's `python/`, pip installs the pinned requirements with that environment's Python, npm installs the pinned packages with `--prefix` the environment's `node/`, and the environment is marked ready

#### Scenario: A failed step leaves the environment not ready
- **WHEN** a setup step exits nonzero
- **THEN** setup names the step, exits 1, and the environment is not marked ready

### Requirement: Convert refuses rather than overwrites

`keel docx convert` MUST refuse, writing nothing, before setup (naming `keel docx setup`), for a missing input or template, for an output that is the input, and for an existing output without `--replace` (naming `--replace`). Otherwise it MUST run the shipped converter with the environment's Python and the Node module directory, and exit with the converter's status.

#### Scenario: Before setup it names the setup command
- **WHEN** `keel docx convert in.md` runs with no ready environment
- **THEN** it exits nonzero naming `keel docx setup` and writes no output

#### Scenario: An existing output is kept without --replace
- **WHEN** the output exists and `--replace` is not given
- **THEN** it exits nonzero naming `--replace` and the existing output is unchanged

#### Scenario: A ready environment runs the converter
- **WHEN** the environment is ready and the output may be written
- **THEN** the environment's Python runs `md2word.py` with the input, the output, and any template, with `MD2WORD_NODE` and `MD2WORD_NODE_MODULES` set

### Requirement: The export skill loads only when asked

The keel plugin MUST ship a `keel-md-docx` skill whose description triggers on a request to export Markdown with SVG to Word, together with the converter files it runs. The skill MUST walk the user through the setup plan and ask before installing, state the output path and ask before replacing, and state the licences, sizes, limits, and which hosts and platforms are unverified. Nothing in a hook, the session start, or an OpenSpec task MAY load it.

#### Scenario: The plugin carries the skill and its converter
- **WHEN** the plugin's skills are listed
- **THEN** `keel-md-docx` is among them with `scripts/md2word.py`, `scripts/runtime.mjs`, `scripts/requirements.txt`, and `scripts/package.json`, and its description names Markdown, SVG, and Word

#### Scenario: The conversion checks skip without an environment
- **WHEN** the conversion scenario runs with no test environment provided
- **THEN** it reports itself skipped and names the variable that provides one

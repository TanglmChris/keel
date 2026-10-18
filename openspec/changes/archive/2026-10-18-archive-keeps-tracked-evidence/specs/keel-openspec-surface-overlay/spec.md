## ADDED Requirements

### Requirement: An archive keeps the files the change tracked

`keel openspec archive <change>` MUST, after OpenSpec archives the change successfully, re-add to the Git index each file that Git tracked under the change before the move and that an ignore rule matches at its archived path, and MUST report how many it re-added. `keel gate change-close --action archive` MUST warn, without changing its verdict, about tracked files under the change that an ignore rule matches, naming them and `keel openspec archive` as the archive that keeps them.

#### Scenario: Tracked evidence the change ignores survives the archive
- **WHEN** a change's own `.gitignore` ignores `evidence/**`, a file under `evidence/` was force-added and committed, and `keel openspec archive <change>` runs
- **THEN** the file's archived path is in the Git index and the output says one file was re-added

#### Scenario: The close warns before the move
- **WHEN** `keel gate change-close --action archive` runs on that change before it is archived
- **THEN** a warning names the tracked evidence file and `keel openspec archive`

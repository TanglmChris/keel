## ADDED Requirements

### Requirement: Uninstalling removes the overlay it installed

The overlay is written into files OpenSpec owns, and every line of it is about Keel — the gate to run, the checklist to run, how to invoke OpenSpec, where standing authorization is declared. Once Keel is removed those instructions name commands that no longer exist, in files that were never Keel's. `keel --uninstall` and `keel --clear` MUST therefore remove the overlay block from every surface that installing projects it onto, on every target, driven by the same surface list that writes it so that a surface added to one direction cannot be missed by the other.

The removal MUST take the overlay block and the whitespace separating it from the content before it, and nothing else. The file MUST be preserved: the bytes that preceded the overlay MUST be unchanged, and a surface MUST NOT be deleted or emptied because its Keel block was removed. Removing the block is the whole obligation — restoring the file to its pristine upstream state is `openspec update`'s concern, not uninstall's.

A `--dry-run` uninstall MUST report each surface it would clean and MUST write nothing, because a plan that reports nothing for a run that writes is the failure mode this surface has already produced once on the install side.

A surface carrying no overlay, and a surface whose file does not exist, MUST be counted rather than treated as an error, so that uninstalling twice, or uninstalling a repository that never received the overlay, succeeds.

#### Scenario: Uninstalling removes the overlay from every surface installing wrote it to
- **WHEN** a repository is installed and then uninstalled on any target
- **THEN** no surface that received the overlay still carries the marker, including surfaces outside the repository such as the Codex prompt directory
- **AND THEN** the surfaces are the ones the shared surface list names, not a second list written beside it

#### Scenario: The surrounding OpenSpec content survives
- **WHEN** the overlay is removed from a surface
- **THEN** the file still exists and its content is exactly the bytes that preceded the overlay
- **AND THEN** the blank line the install side inserted before the block is removed with it, so the file does not end in trailing blank lines

#### Scenario: A dry run reports the removal without performing it
- **WHEN** `--uninstall` runs with `--dry-run` against an installed repository
- **THEN** each surface that would be cleaned is named in the output
- **AND THEN** every surface still carries its overlay afterwards

#### Scenario: Uninstalling twice is not an error
- **WHEN** uninstall runs against a repository whose surfaces carry no overlay, or whose surface files are absent
- **THEN** it succeeds, reporting nothing removed rather than failing

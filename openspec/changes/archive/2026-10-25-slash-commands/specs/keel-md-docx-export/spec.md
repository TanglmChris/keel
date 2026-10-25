## REMOVED Requirements

### Requirement: Setup lists before it installs

**Reason**: The owner retired Markdown-to-Word export on 2026-10-25: "这不是keel该做的". Exporting documents is not part of keeping an agent on an OpenSpec change (#464).

**Migration**: `keel docx` now prints that it was retired in 5.202.0 and exits nonzero. Anyone who still needs the export can use a general document tool. A `~/.keel/docx` environment that `keel docx setup --yes` created is no longer used and can be deleted.

### Requirement: Convert refuses rather than overwrites

**Reason**: Retired with the export itself (#464).

**Migration**: As for "Setup lists before it installs".

### Requirement: The export skill loads only when asked

**Reason**: The `keel-md-docx` skill is removed from the plugin with the export (#464).

**Migration**: None. The plugin no longer ships the skill.

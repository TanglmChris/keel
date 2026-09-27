## ADDED Requirements

### Requirement: Project init never downgrades OpenSpec surfaces

`keel --init` MUST read the highest `generatedBy` version among the repository's OpenSpec skill surfaces before its OpenSpec rewrite. When that version is strictly newer than the OpenSpec Keel would run, it MUST skip `openspec init --force` and `openspec update --force` and MUST say which version wrote the surfaces and which it declined to run. It MUST still refresh the managed protocol and Keel's overlays. When the surfaces are the same version or older, or carry no stamp, init MUST behave as it did before.

#### Scenario: Newer surfaces are left alone
- **WHEN** the repository's OpenSpec skills carry a `generatedBy` newer than Keel's OpenSpec and `keel --init` runs
- **THEN** those files keep their content, and init reports that it skipped the OpenSpec rewrite and why

#### Scenario: Older surfaces are still refreshed
- **WHEN** the repository's OpenSpec skills carry an older `generatedBy`
- **THEN** `keel --init` rewrites them with Keel's OpenSpec as before

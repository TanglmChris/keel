## ADDED Requirements

### Requirement: Self-update defaults to the published registry package

`keel --update` MUST default its fetch source to the published `@christang/keel`
npm registry package — a registry-type spec — so self-update succeeds in
environments that disable git-type package fetches. An explicit `--source`
argument or the `KEEL_UPDATE_SOURCE` environment variable MAY still select a git
spec for installing an unreleased build, but the shipped default MUST NOT be a
git-type spec.

#### Scenario: Default update packs the registry package
- **WHEN** `keel --update` runs with no explicit `--source` or `KEEL_UPDATE_SOURCE`
- **THEN** the planned pack source is the published registry package `@christang/keel`
- **AND THEN** the default source is not a git-type spec and needs no git-type fetch

#### Scenario: Explicit git source is still honored for development
- **WHEN** a user passes `--source github:TanglmChris/keel` or sets `KEEL_UPDATE_SOURCE` to a git spec
- **THEN** update packs that explicit git spec instead of the registry default
- **AND THEN** the explicit override takes precedence over the registry default

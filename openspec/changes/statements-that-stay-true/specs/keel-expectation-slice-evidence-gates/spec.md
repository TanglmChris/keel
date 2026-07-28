## ADDED Requirements

### Requirement: Shipped version markers agree with the package version

A requirement that names the version being released is true for one release and
false for every release after it, while reading as a standing rule. What the
rule was reaching for is the invariant, not the number: **every version marker
Keel ships MUST agree with the package version**, across npm metadata, both
native plugin manifests, protocol and bootstrap markers, build/install/validation
constants, and the OpenSpec overlay markers of every initialized target.

The invariant MUST be enforced by a check rather than asserted, and that check
MUST derive the markers it compares from what the repository actually ships
rather than from a fixed list, because a fixed list is the next thing to fall
behind. The release bump MUST refresh every initialized target's markers, not
only those of the target it happens to touch: a marker that only a human
remembers to update falls behind by one version per release, silently, because
nothing fails when it does.

#### Scenario: Every shipped marker matches the package version

- **WHEN** the repository's shipped version markers are inspected at any commit
- **THEN** each one reports the package version
- **AND THEN** a marker left behind fails the check and is named with its path

#### Scenario: The release bump reaches every target

- **WHEN** the version is bumped for a release
- **THEN** the overlay markers of every initialized target are refreshed together
- **AND THEN** no target's markers depend on a separate manual step

#### Scenario: The marker list is derived, not fixed

- **WHEN** a new shipped surface carrying a version marker is added
- **THEN** the check covers it without being edited
- **AND THEN** the invariant cannot be satisfied by a list that stopped tracking reality

## REMOVED Requirements

### Requirement: Keel version reflects expectation gate capability

**Reason**: it required release as version `3.0.0` and forbade `2.7.0`, both of
which shipped long before 5.3.4, and one of its scenarios asked for version
markers on the retired `dist/` tree. Its durable half — that versioned surfaces
stay aligned — is carried by "Shipped version markers agree with the package
version" above, without naming a version.

**Migration**: none. The alignment obligation is unchanged and is now checked;
the version literals were already false.

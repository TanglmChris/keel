## ADDED Requirements

### Requirement: The OpenSpec dependency resolves from any install layout

Keel MUST locate its OpenSpec dependency by searching each ancestor of its own
package root for a `node_modules/.bin` entry, nearest first, before falling back
to a bare `openspec` on PATH.

`keel --doctor` MUST distinguish a dependency that is not installed from one that
is installed and unreachable, and MUST NOT advise reinstalling when the
dependency is present.

#### Scenario: A hoisted dependency resolves

- **WHEN** Keel is installed as a dependency and npm placed the OpenSpec bin in the consumer project's `node_modules/.bin`
- **THEN** `keel openspec` runs it
- **AND THEN** `keel --doctor` does not report the dependency as missing

#### Scenario: The nearest dependency wins

- **WHEN** an OpenSpec bin exists both beside Keel and in an ancestor directory
- **THEN** Keel resolves the nearer one

#### Scenario: An absent dependency is named as absent

- **WHEN** no OpenSpec bin exists in any ancestor and none is on PATH
- **THEN** `keel --doctor` reports the dependency as missing and advises reinstalling

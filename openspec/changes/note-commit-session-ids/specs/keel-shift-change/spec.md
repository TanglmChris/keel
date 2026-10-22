## ADDED Requirements

### Requirement: A shift note's session ids are not read as commits

When `keel shift resume` lists the commits a note names, a bare token that is the first segment of a UUID, or that begins a session id Keel records under `sessions/` or keeps under `shift/transcripts/`, MUST NOT be listed; every other token MUST be read as before. The note header `keel shift ready` writes MUST NOT carry a blank line for a session field it leaves empty.

#### Scenario: Session ids in a note are not listed as commits
- **WHEN** a CLI session runs `keel shift ready` with a note naming a landed commit, `deadbee1`, and the first eight digits of another recorded session's id, and `keel shift resume` runs
- **THEN** the landed commit is marked `already in origin/<default>` and `deadbee1` `not found`, neither session id is listed, and the note's header holds no two consecutive blank lines

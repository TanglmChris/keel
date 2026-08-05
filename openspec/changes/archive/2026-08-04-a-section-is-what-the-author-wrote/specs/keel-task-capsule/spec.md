## ADDED Requirements

### Requirement: A change-level section ends at the next heading or the next task
A change-level section of tasks.md — `## Invalidates`, `## Expectation Coverage` — MUST end at the next `##` heading or at the next task, whichever comes first. A tasks file's dominant structure is a list, so a section bounded only by the next heading extends over the task list whenever it is not the file's last section. The task half of this bound MUST be the task list already parsed for the same file, so that it cannot drift from the boundary applied to a task's own body, and both change-level sections MUST be bounded by one shared computation rather than by two that agree today.

The position of a change-level section MUST NOT affect any verdict. Keel MUST NOT require a section to sit in the file's tail, and MUST report the same problems for the same section content wherever the author placed it.

A line inside a task body MUST NOT close, satisfy, or contribute an entry to a change-level section. In particular a task field entry of `none` MUST NOT be read as the section's `- None.`, and an `E<n>` or `I<n>` line a task declares under its `Covers` MUST NOT be read as a section entry.

#### Scenario: A section above the task list is read as written
- **WHEN** `## Expectation Coverage` sits above the task list and every entry it declares is closed
- **THEN** `change-close` returns the same verdict it returns for the identical section in the file's tail
- **AND THEN** no problem names an entry that the section closes

#### Scenario: A task's own Covers entries are not section entries
- **WHEN** `## Expectation Coverage` sits above a task that declares `- E<n>:` lines under its `Covers`
- **THEN** those lines are not judged as coverage entries
- **AND THEN** no problem reports an `E<n>` that the section closes as lacking a closure

#### Scenario: An entry a task body appeared to close is still refused
- **WHEN** a change-level section sits above the task list, declares an entry with no closure, and a task body carries a field entry of `none`
- **THEN** the gate refuses the entry and names it
- **AND THEN** the section is not treated as having declared `- None.`

#### Scenario: Both change-level sections share the boundary
- **WHEN** `## Invalidates` sits above the task list
- **THEN** `task-start` reads only that section's own entries
- **AND THEN** it reports the same problems it reports for the identical section in the file's tail

#### Scenario: The tail position is unchanged
- **WHEN** a change-level section is the file's last section
- **THEN** every verdict, problem code, and message is what it was before the boundary gained its task half

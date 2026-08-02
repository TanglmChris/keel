## ADDED Requirements

### Requirement: Two tasks shaped like one behavior are named at task-start

`keel gate task-start` MUST warn when another task in the same change declares an identical Touch set and the selected task's strategy is red-green, naming the other task so the author compares two things rather than being told something is wrong.

Keel MUST NOT fail or return `needs-review` for this shape. A genuine vertical split can share files, the judgment is semantic, and there is no mechanism to acknowledge a `needs-review` — turning a signal into a verdict would leave a legitimate split unstartable. The warning MUST NOT change the gate's status or exit code.

`keel-review-checklist` MUST ask the same question at completion, when the evidence that settles it exists.

#### Scenario: An identical Touch set under a red-green strategy is named
- **WHEN** `task-start` selects a task whose Touch set matches another task in the same change and whose strategy is red-green
- **THEN** the result carries a warning naming the other task
- **AND THEN** the status is unchanged and the exit code is unchanged, so the task starts normally

#### Scenario: A differing Touch set or a non-red-green strategy is silent
- **WHEN** no other task in the change declares the same Touch set, or the selected task's strategy is not red-green
- **THEN** no warning about task shape is produced

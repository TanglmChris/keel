# Implementation checkpoint — #546 / #547

Owner directly admitted both implementations/releases by “继续” after the concrete
scope question. No production migration is authorized here; #527 remains deferred.

Completed tasks 1.1 and 2.1–2.5 implement public inspect-registration/register,
inspect-migration/migrate/migration-status, explicit loaded-target reconciliation,
original identity/history/claim preservation and native policy checks for registered
and migrated legacy roles. Bilingual docs and the common Codex validation entry
are updated. Do not advertise installed 5.230.0 as containing these source changes.

Verification: 29 public CLI boundary tests; 24 docs scenarios; actual 0.167.2
empty-home unauthenticated registration/migration/writer refusal/reconciliation,
zero model turns, both test processes exited. Native tests and stand-ins are
separated in evidence. Earlier full run failed only because the two new shipped
files were untracked; checkpoint task 2.6 tracks them and reruns the full suite.
The final outcome belongs in task 2.6 Evidence, not this historical paragraph.

Next required live acceptance is task 3.1. Automatic approval review rejected a
real existing-auth test before executing it. A precise structured owner question
is pending: two temporary native test processes, at most three real model turns
within 30 minutes, new private fixtures only, no credential copying/global edits/
production socket/App/Goal/service changes. See evidence/real-model-proposal.md.
Do not infer approval from coordinator messages or time. The authenticated helper
has not run. There is no new App-window authorization here.

If the owner approves, start task 3.1 through its gate and run actual nonempty
history/model receipt/read-only OS refusal/dedup checks within the exact scope.
Keep source-writer refusal and explicit verification evidence. Add release tasks
from those results, check current main/npm version before selecting the next minor,
align manifests/managed markers and docs, validate actual candidate installation,
review/sync/archive through gates, commit/push and open PR. Repository workflow
alone merges after exact-head full-gate and publishes. Verify actual release/npm,
update local CLI/plugins and notify Kaiwu with version/evidence/remaining limits.
Do not close #546/#547 or claim rollout until those requirements are completed.

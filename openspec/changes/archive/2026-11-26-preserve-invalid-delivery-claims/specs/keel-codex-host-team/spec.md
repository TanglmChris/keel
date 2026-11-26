## ADDED Requirements

### Requirement: Preserve invalid delivery claims
Keel SHALL distinguish a missing delivery key from a present unusable claim. Only absence in a valid delivery map or an initial registration without a delivery map permits fresh dispatch. Keel SHALL preserve ambiguous claims and refuse their replay.

#### Scenario: Damaged receipt on an original record
- **WHEN** a prior delivery claim is present but invalid and its original record is queried and resubmitted
- **THEN** the receipt is unknown or explicitly invalid, the registration remains unchanged and the host receives no new work.

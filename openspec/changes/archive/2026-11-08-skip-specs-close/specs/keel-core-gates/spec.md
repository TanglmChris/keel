## ADDED Requirements

### Requirement: change-close honors a declared skip of specs

`keel gate change-close` MUST NOT report `missing-delta-spec` for a change whose `.openspec.yaml` declares `skip_specs: true`, for `--action archive` and `--action sync`. A change that declares it and still carries any file under `specs/` MUST fail with a `skip-specs-with-specs` problem naming that file. A change without the declaration MUST still be required to carry a delta spec.

#### Scenario: A marked change without specs passes the delta-spec check
- **WHEN** a change declares `skip_specs: true`, has no `specs/` directory, and `change-close --action archive` runs
- **THEN** the result carries no `missing-delta-spec` problem

#### Scenario: A marked change that carries a spec fails by name
- **WHEN** a change declares `skip_specs: true` and holds `specs/demo/spec.md`
- **THEN** the result carries a `skip-specs-with-specs` problem naming `specs/demo/spec.md` and no `missing-delta-spec`

#### Scenario: An unmarked change still needs a delta spec
- **WHEN** a change has no `skip_specs` marker, or `skip_specs: false`, and no `specs/**/spec.md`
- **THEN** the result carries `missing-delta-spec`

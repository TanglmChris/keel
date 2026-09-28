## ADDED Requirements

### Requirement: A drift report names an update the host already installed

When the host's local install record names another install of the executing plugin at a different version, the drift report MUST state that the host already installed that version and MUST name only a reload or the next session start as the remedy. It MUST NOT name the host's update command. It MUST judge the `keel` on PATH against the installed version, not the loaded one. An absent or unreadable record MUST leave the report unchanged. Reading the record MUST be local and offline.

#### Scenario: An installed update is named as needing only a reload
- **WHEN** the plugin's install record names this plugin at a newer version than the one executing the hook
- **THEN** the drift report states that the host already installed that version and names `/reload-plugins`
- **AND THEN** it does not name `claude plugin update`

#### Scenario: A PATH copy matching the installed version is not called a shadow
- **WHEN** an installed update is pending and the `keel` on PATH reports the installed version
- **THEN** the drift report does not say the PATH copy shadows the plugin, and does not name a global install at the loaded version

#### Scenario: No install record keeps the current report
- **WHEN** no install record is found beside the plugin
- **THEN** the drift report is identical to the report without this requirement

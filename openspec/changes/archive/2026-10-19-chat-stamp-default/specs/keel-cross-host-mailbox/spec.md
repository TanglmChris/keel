## MODIFIED Requirements

### Requirement: Keel stamps the time and answers --help

`keel chat post` and `keel chat dm`, with `--reply-to` or without, MUST prefix the text with `[MM-DD HH:MM]` in local time from Keel's clock unless `--no-stamp` is given; `--stamp` MUST still be accepted, `--stamp` with `--no-stamp` MUST be refused, and a text that already opens with `[MM-DD HH:MM]` MUST NOT be stamped again. `keel chat --help` and `keel chat -h` MUST print the usage and exit 0.

#### Scenario: A stamped post carries Keel's time
- **WHEN** `rtl` runs `keel chat post soc --stamp "R008 done"`
- **THEN** the stored text starts with `[` followed by the record's own month, day, hour, and minute, then `] R008 done`

#### Scenario: Help is not an error
- **WHEN** `keel chat --help` runs
- **THEN** it exits 0 and prints the usage

#### Scenario: The stamp is the default
- **WHEN** `rtl` posts to `soc`, replies with `--reply-to`, and sends `verify` a direct message, none with `--stamp`
- **THEN** each stored text starts with `[` and the record's own month, day, hour and minute, then `] ` and the text
- **AND THEN** `--no-stamp` stores the text as given, a text opening with `[10-19 11:00]` is stored unchanged, and `--stamp --no-stamp` is refused

## MODIFIED Requirements

### Requirement: Loop guards stop runaway agent traffic

A role other than `owner` MUST be refused, by name, after posting more than the configured limit (default 20 records per 10 minutes) in the project. When the last 8 `message` records of a group since its latest override alternate between the same two non-owner roles, and the first of them is within `limits.pingpong_minutes` (default 10) of the post, the next post there by either MUST be refused. A first such refusal MUST NOT call the owner and MUST name `--not-a-loop "<why>"`; a post with that option MUST then be accepted and record the reason. A refusal after an override that no owner post has followed MUST write one `system` record mentioning `owner` and MUST NOT accept an override; the block MUST clear once the owner, or in a group of more than two members any other member, posts. `limits` in `keel/chat.json` MAY override the thresholds.

#### Scenario: Ping-pong is broken and the owner is called
- **WHEN** `rtl` and `verify` alternate eight messages in `soc` within a minute and `rtl` posts again
- **THEN** the post fails naming the loop guard and `--not-a-loop`, and no `system` record is written
- **AND THEN** `rtl`'s post with `--not-a-loop "new assignment"` is accepted and records the reason, and after eight more quick alternations the next post fails with one `system` record mentioning `owner`, an override is refused, and after `owner` posts in `soc`, `rtl` can post again

#### Scenario: A slow exchange is not a loop
- **WHEN** `rtl` and `verify` have alternated eight messages in `soc` whose first is older than `pingpong_minutes`
- **THEN** `rtl`'s next post there is accepted

## ADDED Requirements

### Requirement: Keel stamps the time and answers --help

`keel chat post` and `keel chat dm` with `--stamp` MUST prefix the text with `[MM-DD HH:MM]` in local time from Keel's clock. `keel chat --help` and `keel chat -h` MUST print the usage and exit 0.

#### Scenario: A stamped post carries Keel's time
- **WHEN** `rtl` runs `keel chat post soc --stamp "R008 done"`
- **THEN** the stored text starts with `[` followed by the record's own month, day, hour, and minute, then `] R008 done`

#### Scenario: Help is not an error
- **WHEN** `keel chat --help` runs
- **THEN** it exits 0 and prints the usage

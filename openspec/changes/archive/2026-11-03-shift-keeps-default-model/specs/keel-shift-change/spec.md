## ADDED Requirements

### Requirement: A CLI hand-over starts the new session on the owner's default model

A CLI hand-over MUST name the model of the session it starts, as `--model <model>` placed after `--permission-mode <mode>` and before the prompt, and MUST NOT leave the choice to the host. The model MUST be the first of these that names one: `shift: model:` in `keel/config.yaml`; the `ANTHROPIC_MODEL` environment variable; `model` in the worktree's `.claude/settings.local.json`; `model` in the worktree's `.claude/settings.json`; `model` in `settings.json` of the Claude config directory (`CLAUDE_CONFIG_DIR`, else `~/.claude`). When none names one, or the one that exists cannot be read, the hand-over MUST pass no `--model` and MUST still start the session. A hand-over MUST pass `--effort <level>` only when `shift: effort:` declares one of `low`, `medium`, `high`, `xhigh` or `max`; a `model:` or `effort:` value Keel cannot read MUST be named in the output of `keel shift status` and ignored. The delivered hand-off MUST record the model it passed and where it came from, and `keel shift status` MUST show both. A resumed session MUST keep the options it was saved with.

#### Scenario: A hand-over passes the model the owner would get
- **WHEN** no `shift: model:` is declared, `ANTHROPIC_MODEL` is unset, and the user's `settings.json` names `opus`
- **THEN** the call that starts the new session is `--bg -n "<role> · <MM-DD HH:MM>" --permission-mode auto --model opus` followed by the prompt, the delivered hand-off records `opus` and the user settings as its source, and `keel shift status` shows both

#### Scenario: The host's own order decides between sources
- **WHEN** the user's `settings.json` names `opus`; the worktree's `.claude/settings.json` additionally names `sonnet`; then its `.claude/settings.local.json` additionally names `haiku`; then `ANTHROPIC_MODEL` is additionally set to `fable`
- **THEN** the model the hand-over passes is, after each addition in turn, `opus`, `sonnet`, `haiku` and `fable`

#### Scenario: A declaration wins over every default
- **WHEN** `shift: model: sonnet` and `shift: effort: high` are declared while the settings and `ANTHROPIC_MODEL` name other models
- **THEN** the call carries `--model sonnet` and `--effort high`

#### Scenario: Nothing to name passes nothing
- **WHEN** no source names a model, or the only settings file that exists is not valid JSON, and no effort is declared
- **THEN** the call carries neither `--model` nor `--effort`, and the hand-off is delivered

#### Scenario: An unreadable declaration is named and ignored
- **WHEN** `shift: effort: extreme` is declared
- **THEN** the call carries no `--effort`, and `keel shift status` names the value and the accepted ones

# Keel privacy policy

Keel is a command-line tool and a Claude Code / Codex plugin that runs on your own machine. The project operates no server, account system, or analytics of its own. Keel itself collects nothing about you.

This page describes what Keel stores, and what leaves your machine and where it goes.

## What Keel stores on your machine

- **In your repository:** the files you ask it to create or update. These are OpenSpec change files, `keel/` configuration, the protocol block in `AGENTS.md` / `CLAUDE.md`, and a write-guard file (`keel/guard.json`) while a task is active.
- **Group chat (optional, `keel chat`):** messages that your sessions, and you, post. They are stored under the repository's git directory (`.git/keel-chat/`). They can contain names, Slack user IDs, and anything people write.
  - The chat history is committed to a local `keel-chat` branch.
  - It is pushed only to a remote you configure. For a public repository, it is pushed only after you explicitly accept that.
- **Per-machine state:** registries and logs for the chat bridge and the Codex waker, under `~/.keel/`.
- **Slack tokens (optional):** only in the macOS Keychain (service `keel-chat-slack`) or in environment variables you set. Keel never writes them to a file, record, status line, or log.

## What leaves your machine

Nothing leaves your machine unless one of the following applies.

- **Slack bridge.** Runs only if you set it up with `keel chat bridge` and your own Slack app. It sends chat messages in Slack-enabled groups to your Slack workspace through Slack's API, and reads replies from it. Slack's own privacy policy then applies to that data.
- **Updates.** These run only when you run them. `keel --update` downloads the Keel package from the npm registry, then runs Claude Code's and Codex's own plugin-update commands, which contact their marketplaces (GitHub).
- **OpenSpec telemetry.** Keel bundles the [OpenSpec](https://github.com/Fission-AI/OpenSpec) CLI. By default, OpenSpec sends anonymous usage statistics: command names and its version, with no arguments, paths, content, or personal data. It is disabled in CI. To turn it off, run `openspec config set telemetry.enabled false`, or set `OPENSPEC_TELEMETRY=0` or `DO_NOT_TRACK=1`. OpenSpec may also check the npm registry for a newer version of itself.
- **External model CLIs.** Only when a session runs one. `keel agents brief` writes a brief for an external model CLI such as codex or dsh, and the session then runs it. That CLI sends the brief, and any file it reads, to its own provider (`keel agents` names where each one sends data). Keel launches none of them. A project allows them, and names paths that must not be handed over, with `external_agents:` in `keel/config.yaml`; with no such declaration, Keel compiles no brief.
- **Your agent host.** Claude Code or Codex sends your conversation, including what Keel's hooks add to it, to its model provider under that provider's terms. Keel adds only local project state, such as the current task and chat notices.

## Data retention

The project receives no data, so it retains none. What Keel stores on your machine stays until you delete it: the repository files, `.git/keel-chat/`, and `~/.keel/`.

## Children

Keel is a developer tool and is not directed at children under 18.

## Contact

Questions or concerns: open an issue at https://github.com/TanglmChris/keel/issues.

Last updated: 2026-10-04.

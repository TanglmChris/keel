#!/usr/bin/env node
"use strict";

// Keel plugin mailbox hook (issue #180), Claude Code only: SessionStart and
// UserPromptSubmit announce unread cross-host mail, and FileChanged — declared
// with `asyncRewake` and watching the role's signal file — wakes an idle
// session when mail arrives. The work is `keel mail hook <event>`; this script
// only finds the CLI the way session-start.js does and relays its stdin,
// output, and exit code, because exit 2 from FileChanged is the wake signal.
//
// Nothing here reads or moves a message, and a worktree with no mail role gets
// no output. A failure to run the CLI exits 0 silently: a missing notice costs
// a late read, while a spurious exit 2 would wake the session for nothing.

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const EVENTS = new Set(["session-start", "user-prompt-submit", "file-changed"]);
const TIMEOUT_MS = Number(process.env.KEEL_HOOK_TIMEOUT_MS || 8000) || 8000;

function readStdin() {
  try {
    return fs.readFileSync(0, "utf8");
  } catch {
    return "";
  }
}

// Same order as session-start.js: an explicit KEEL_CLI, the CLI this plugin
// shipped with, then whatever `keel` is on PATH.
function keelCommand() {
  const explicit = (process.env.KEEL_CLI || "").trim();
  if (explicit) return explicit;
  const root = path.join(__dirname, "..", "..", "..");
  try {
    const pkg = JSON.parse(
      fs.readFileSync(path.join(root, "package.json"), "utf8")
    );
    const cli = path.join(root, "bin", "keel.js");
    if (pkg.name === "@christang/keel" && fs.existsSync(cli)) {
      return `"${process.execPath}" "${cli}"`;
    }
  } catch {
    // No package around this script: the plugin was copied on its own.
  }
  return "keel";
}

function main() {
  const event = process.argv[2];
  if (!EVENTS.has(event)) return 0;
  const input = readStdin();
  let cwd = process.cwd();
  try {
    const parsed = JSON.parse(input || "{}");
    if (parsed && typeof parsed.cwd === "string" && parsed.cwd) cwd = parsed.cwd;
  } catch {
    // Keep the process cwd.
  }
  const result = spawnSync(`${keelCommand()} mail hook ${event}`, {
    cwd,
    shell: true,
    input,
    encoding: "utf8",
    timeout: TIMEOUT_MS,
  });
  if (result.error || (result.status !== 0 && result.status !== 2)) return 0;
  if (result.status === 2 && event !== "file-changed") return 0;
  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr && result.status === 2) process.stderr.write(result.stderr);
  return result.status;
}

process.exitCode = main();

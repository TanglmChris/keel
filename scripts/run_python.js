#!/usr/bin/env node
"use strict";

const { spawnSync } = require("child_process");

function pythonCandidates() {
  if (process.env.KEEL_PYTHON) {
    return [{ command: process.env.KEEL_PYTHON, prefixArgs: [] }];
  }

  if (process.platform === "win32") {
    return [
      { command: "py", prefixArgs: ["-3"] },
      { command: "python", prefixArgs: [] },
      { command: "python3", prefixArgs: [] },
    ];
  }

  return [
    { command: "python3", prefixArgs: [] },
    { command: "python", prefixArgs: [] },
  ];
}

// The suite calls `tempfile.TemporaryDirectory(ignore_cleanup_errors=…)`,
// added in 3.10. Accepting any interpreter whose `--version` exits zero meant
// macOS system Python 3.9 ran the suite and failed ten scenarios with messages
// naming ten unrelated features — the reader is then debugging the suite
// instead of installing an interpreter.
const MINIMUM_PYTHON = [3, 10];

function label(candidate) {
  return [candidate.command, ...candidate.prefixArgs].join(" ");
}

function reportedVersion(candidate) {
  const result = spawnSync(
    candidate.command,
    [...candidate.prefixArgs, "--version"],
    { encoding: "utf8" }
  );
  if (result.error || result.status !== 0) return null;
  // Python 2 wrote `--version` to stderr, so read both streams: an old
  // interpreter should be reported by its version rather than dismissed as
  // unreadable.
  const match = `${result.stdout || ""}${result.stderr || ""}`.match(
    /(\d+)\.(\d+)(?:\.(\d+))?/
  );
  return match ? match[0] : null;
}

function meetsMinimum(version) {
  const parts = String(version || "").split(".").map(Number);
  const [major, minor] = parts;
  if (!Number.isFinite(major) || !Number.isFinite(minor)) return false;
  if (major !== MINIMUM_PYTHON[0]) return major > MINIMUM_PYTHON[0];
  return minor >= MINIMUM_PYTHON[1];
}

function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    process.stderr.write("run_python: expected a Python script path.\n");
    return 2;
  }

  const tried = [];
  let candidate = null;
  for (const option of pythonCandidates()) {
    const version = reportedVersion(option);
    tried.push(`${label(option)} (${version || "not runnable"})`);
    if (version && meetsMinimum(version)) {
      candidate = option;
      break;
    }
  }
  if (!candidate) {
    const minimum = MINIMUM_PYTHON.join(".");
    process.stderr.write(
      `run_python: no Python ${minimum} or newer was found, and the suite `
        + `needs one — tempfile.TemporaryDirectory(ignore_cleanup_errors=…) `
        + `was added in ${minimum}.\n`
        + `run_python: tried ${tried.join(", ") || "nothing"}.\n`
        + "run_python: install a newer Python, or point KEEL_PYTHON at one.\n"
    );
    return 127;
  }

  const result = spawnSync(
    candidate.command,
    [...candidate.prefixArgs, ...args],
    { stdio: "inherit" }
  );

  if (result.error) {
    process.stderr.write(`run_python: ${result.error.message}\n`);
    return 127;
  }

  return result.status ?? 1;
}

process.exit(main());

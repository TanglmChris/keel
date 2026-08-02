#!/usr/bin/env node
"use strict";

const { spawnSync } = require("child_process");

// The suite calls `tempfile.TemporaryDirectory(ignore_cleanup_errors=…)`,
// added in 3.10. Accepting any interpreter whose `--version` exits zero meant
// macOS system Python 3.9 ran the suite and failed ten scenarios with messages
// naming ten unrelated features — the reader is then debugging the suite
// instead of installing an interpreter.
//
// This is the one definition. `bin/keel.js` used to carry its own candidate
// list that asked only whether a command runs, so `keel --doctor` reported
// `python3: ok` for the same 3.9.6 this file refuses — two Keel surfaces
// answering one question with opposite verdicts, and the one a person runs
// deliberately to check their environment was the wrong one.
const MINIMUM_PYTHON = [3, 10];

// The newest minor worth looking for under a versioned name. Names are
// generated from MINIMUM_PYTHON up to this, newest first, so raising the
// minimum drops the names below it with no second edit; only this bound moves
// when a new Python is released.
const NEWEST_KNOWN_PYTHON_MINOR = 13;

// Versioned names matter because the unversioned one is often not the usable
// one. On macOS `python3` is the system 3.9 while Homebrew installs
// `python3.11` beside it, so a search that stops at `python3` refuses with
// "install a newer Python" addressed to someone who already did.
function versionedPythonNames() {
  const names = [];
  for (let minor = NEWEST_KNOWN_PYTHON_MINOR; minor >= MINIMUM_PYTHON[1]; minor -= 1) {
    names.push({ command: `python${MINIMUM_PYTHON[0]}.${minor}`, prefixArgs: [] });
  }
  return names;
}

function pythonCandidates() {
  // An explicit choice is not overridden by discovery.
  if (process.env.KEEL_PYTHON) {
    return [{ command: process.env.KEEL_PYTHON, prefixArgs: [] }];
  }

  // Unversioned names first, so a machine where the default interpreter
  // already satisfies the minimum behaves exactly as it did before.
  if (process.platform === "win32") {
    return [
      { command: "py", prefixArgs: ["-3"] },
      { command: "python", prefixArgs: [] },
      { command: "python3", prefixArgs: [] },
      ...versionedPythonNames(),
    ];
  }

  return [
    { command: "python3", prefixArgs: [] },
    { command: "python", prefixArgs: [] },
    ...versionedPythonNames(),
  ];
}

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

// Resolve the interpreter both surfaces should agree about. Returns the chosen
// candidate and every candidate tried with the version it reported, so the
// caller can either run it or report why there is nothing to run.
function resolveInterpreter() {
  const tried = [];
  for (const option of pythonCandidates()) {
    const version = reportedVersion(option);
    tried.push({ label: label(option), version });
    if (version && meetsMinimum(version)) {
      return { candidate: option, version, tried };
    }
  }
  return { candidate: null, version: null, tried };
}

function describeTried(tried) {
  return tried
    .map((entry) => `${entry.label} (${entry.version || "not runnable"})`)
    .join(", ");
}

function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    process.stderr.write("run_python: expected a Python script path.\n");
    return 2;
  }

  const { candidate, tried } = resolveInterpreter();
  if (!candidate) {
    const minimum = MINIMUM_PYTHON.join(".");
    process.stderr.write(
      `run_python: no Python ${minimum} or newer was found, and the suite `
        + `needs one — tempfile.TemporaryDirectory(ignore_cleanup_errors=…) `
        + `was added in ${minimum}.\n`
        + `run_python: tried ${describeTried(tried) || "nothing"}.\n`
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

// `bin/keel.js` requires this file for the definitions above, so the script
// only runs when it is the entry point. Two copies of the interpreter rule is
// what this change exists to remove; importing is what keeps it at one.
module.exports = {
  MINIMUM_PYTHON,
  pythonCandidates,
  versionedPythonNames,
  reportedVersion,
  meetsMinimum,
  resolveInterpreter,
  describeTried,
};

if (require.main === module) {
  process.exit(main());
}

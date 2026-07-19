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

function commandExists(candidate) {
  const result = spawnSync(
    candidate.command,
    [...candidate.prefixArgs, "--version"],
    { encoding: "utf8" }
  );
  return !result.error && result.status === 0;
}

function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    process.stderr.write("run_python: expected a Python script path.\n");
    return 2;
  }

  const candidate = pythonCandidates().find(commandExists);
  if (!candidate) {
    process.stderr.write(
      "run_python: could not find Python. Install python3/python or set KEEL_PYTHON.\n"
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

#!/usr/bin/env node
"use strict";

// Waits until the npm registry serves a published version (#421).
//
// `npm publish` returning is the write side saying the version exists; the
// read side that `npm install` and `claude plugin update` resolve against has
// lagged it by minutes (#153, #421). The publish job runs this between the
// publish and the release, so a release announces a version the registry
// already serves. A nonzero `npm view` is npm's E404 for a version it cannot
// see yet, and counts as not served. Mirrors and proxies may lag further;
// `keel --update` reports that case as `pending`.
//
// Usage:
//   node scripts/await_registry.js <package> <version> [--interval-seconds N] [--timeout-seconds N]
//
// KEEL_AWAIT_NPM names the npm executable (default `npm`).

const { spawnSync } = require("child_process");

function fail(message) {
  process.stderr.write(`await_registry: ${message}\n`);
  process.exit(1);
}

function option(args, name, fallback) {
  const index = args.indexOf(name);
  if (index < 0) return fallback;
  const value = Number(args[index + 1]);
  if (!Number.isFinite(value) || value < 0) fail(`${name} needs a number of seconds`);
  args.splice(index, 2);
  return value;
}

function served(npm, spec, version) {
  const result = spawnSync(npm, ["view", spec, "version", "--prefer-online"], {
    encoding: "utf8",
    shell: process.platform === "win32",
    timeout: 60 * 1000,
  });
  return !result.error && result.status === 0 && String(result.stdout || "").trim() === version;
}

function sleep(seconds) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, seconds * 1000);
}

function main() {
  const args = process.argv.slice(2);
  const interval = option(args, "--interval-seconds", 15);
  const limit = option(args, "--timeout-seconds", 15 * 60);
  if (args.length !== 2) {
    fail("usage: node scripts/await_registry.js <package> <version> [--interval-seconds N] [--timeout-seconds N]");
  }
  const [name, version] = args;
  const spec = `${name}@${version}`;
  const npm = process.env.KEEL_AWAIT_NPM || "npm";
  const started = Date.now();
  for (let polls = 1; ; polls += 1) {
    if (served(npm, spec, version)) {
      const seconds = Math.round((Date.now() - started) / 1000);
      process.stdout.write(`await_registry: the registry serves ${spec} after ${seconds} s and ${polls} poll(s)\n`);
      return;
    }
    if ((Date.now() - started) / 1000 + interval > limit) {
      fail(`the registry did not serve ${spec} within ${limit} s (${polls} poll(s)); re-run the job to wait again`);
    }
    sleep(interval);
  }
}

main();

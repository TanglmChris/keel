#!/usr/bin/env node
"use strict";

// The entry Anthropic's official plugin directory would list for a release.
//
// The directory pins every third-party plugin to a commit of its git
// repository, so the entry is only useful pinned to the commit the release
// tag points at. The release job appends this output to the release notes;
// submitting it, or asking the directory to move its pin, is the owner's act.
// This script reads the root manifest and nothing else, and runs nothing.
//
// Usage:
//   node scripts/official_entry.js <X.Y.Z> <40-character commit sha>

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const REPOSITORY = "https://github.com/TanglmChris/keel";

const [version, sha] = process.argv.slice(2);
// A pin the directory could not use prints nothing, so a pipe into the notes
// cannot carry a half-formed entry.
if (!/^\d+\.\d+\.\d+$/.test(version || "") || !/^[0-9a-f]{40}$/.test(sha || "")) {
  process.stderr.write(
    "official-entry: usage: node scripts/official_entry.js <X.Y.Z> <40-hex commit sha>\n"
  );
  process.exit(1);
}
const manifest = JSON.parse(
  fs.readFileSync(path.join(ROOT, ".claude-plugin", "plugin.json"), "utf8")
);
const entry = {
  name: manifest.name,
  description: manifest.description,
  category: "development",
  source: { source: "url", url: `${REPOSITORY}.git`, sha },
  homepage: REPOSITORY,
};
process.stdout.write(`${JSON.stringify(entry, null, 2)}\n`);

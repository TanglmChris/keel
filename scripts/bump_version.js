#!/usr/bin/env node
"use strict";

// One-shot version bump across every place Keel pins its version.
//
// The Keel validation suite requires the same version in package.json,
// package-lock.json, both native plugin manifests, the validator constants,
// the protocol docs, and the changelog. This script updates all of them
// together so a release never ships half-aligned.
//
// Usage:
//   node scripts/bump_version.js <patch|minor|major|explicit-version>
//
// After running: fill in the CHANGELOG entry, then `npm test`, commit,
// tag `vX.Y.Z`, push, and publish a GitHub Release.

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const PKG_PATH = path.join(ROOT, "package.json");
const LOCK_PATH = path.join(ROOT, "package-lock.json");
const CHANGELOG_PATH = path.join(ROOT, "keel", "CHANGELOG.md");
const CHANGELOG_HEADER = "# Keel Changelog\n\n";
const SEMVER_RE = /^(\d+)\.(\d+)\.(\d+)$/;

function fail(message) {
  process.stderr.write(`bump-version: ${message}\n`);
  process.exit(1);
}

function resolveNewVersion(current, target) {
  if (target === "patch" || target === "minor" || target === "major") {
    const [, major, minor, patch] = current.match(SEMVER_RE).map(Number);
    if (target === "major") return `${major + 1}.0.0`;
    if (target === "minor") return `${major}.${minor + 1}.0`;
    return `${major}.${minor}.${patch + 1}`;
  }
  if (!SEMVER_RE.test(target)) {
    fail(`not a patch|minor|major keyword or an X.Y.Z version: ${target}`);
  }
  return target;
}

function writeJson(filePath, data) {
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`);
}

function bumpPackageFiles(newVersion) {
  const pkg = JSON.parse(fs.readFileSync(PKG_PATH, "utf8"));
  pkg.version = newVersion;
  writeJson(PKG_PATH, pkg);
  process.stdout.write("  updated package.json\n");

  const lock = JSON.parse(fs.readFileSync(LOCK_PATH, "utf8"));
  lock.version = newVersion;
  if (lock.packages && lock.packages[""]) {
    lock.packages[""].version = newVersion;
  }
  writeJson(LOCK_PATH, lock);
  process.stdout.write("  updated package-lock.json\n");
}

function replaceInFile(relPath, replacements) {
  const filePath = path.join(ROOT, relPath);
  let content = fs.readFileSync(filePath, "utf8");
  for (const [from, to] of replacements) {
    if (!content.includes(from)) {
      fail(`expected to find ${JSON.stringify(from)} in ${relPath}`);
    }
    content = content.split(from).join(to);
  }
  fs.writeFileSync(filePath, content);
  process.stdout.write(`  updated ${relPath}\n`);
}

// Every Keel marker carrying `version=` is a shipped claim about which version
// this is, and they must all move together. Sweeping for the markers that exist
// is what keeps a target from falling behind: the `.codex/` overlays sat four
// versions back because only the surfaces something happened to touch got
// refreshed, and nothing failed while they drifted.
const MARKER_SKIP_PREFIXES = [
  "node_modules",
  ".git",
  path.join("openspec", "changes", "archive"),
  path.join("keel", "archive"),
];

function sweepVersionMarkers(dir, oldVersion, newVersion, touched) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    const relative = path.relative(ROOT, full);
    if (MARKER_SKIP_PREFIXES.some((prefix) => relative.startsWith(prefix))) continue;
    if (entry.isDirectory()) {
      sweepVersionMarkers(full, oldVersion, newVersion, touched);
      continue;
    }
    if (!/\.(md|json)$/.test(entry.name)) continue;
    const content = fs.readFileSync(full, "utf8");
    const updated = content.replace(
      new RegExp(`(keel:[a-z-]+(?::end)?\\s+version=)${oldVersion.replace(/\./g, "\\.")}\\b`, "g"),
      `$1${newVersion}`
    );
    if (updated !== content) {
      fs.writeFileSync(full, updated);
      touched.push(relative.split(path.sep).join("/"));
    }
  }
}

function prependChangelogEntry(newVersion) {
  // Read line endings as the file has them: a CRLF checkout made the header
  // comparison below fail after every version marker had already been written,
  // leaving the repository half-bumped.
  let content = fs.readFileSync(CHANGELOG_PATH, "utf8").replace(/\r\n/g, "\n");
  if (content.includes(`## ${newVersion} `) || content.includes(`## ${newVersion}\n`)) {
    process.stdout.write(`  keel/CHANGELOG.md already has a ${newVersion} entry\n`);
    return;
  }
  if (!content.startsWith(CHANGELOG_HEADER)) {
    fail("keel/CHANGELOG.md does not start with the expected header");
  }
  const entry =
    `## ${newVersion} - TODO: summarize this release\n\n` +
    "- TODO: describe the change.\n" +
    "- Version alignment: the npm package, both native plugin manifests, " +
    `protocol docs, and this changelog share Keel ${newVersion}; the OpenSpec ` +
    "dependency pin stays `^1.4.1`.\n\n";
  content = CHANGELOG_HEADER + entry + content.slice(CHANGELOG_HEADER.length);
  fs.writeFileSync(CHANGELOG_PATH, content);
  process.stdout.write("  updated keel/CHANGELOG.md (fill in the TODO lines)\n");
}

function main() {
  const target = process.argv[2];
  if (!target) {
    fail("usage: node scripts/bump_version.js <patch|minor|major|explicit-version>");
  }

  const oldVersion = JSON.parse(fs.readFileSync(PKG_PATH, "utf8")).version;
  if (!SEMVER_RE.test(oldVersion)) {
    fail(`current package.json version is not X.Y.Z: ${oldVersion}`);
  }
  const newVersion = resolveNewVersion(oldVersion, target);
  process.stdout.write(`Bumping ${oldVersion} -> ${newVersion}\n`);

  bumpPackageFiles(newVersion);
  replaceInFile("plugins/keel/.claude-plugin/plugin.json", [
    [`"version": "${oldVersion}"`, `"version": "${newVersion}"`],
  ]);
  replaceInFile("plugins/keel/.codex-plugin/plugin.json", [
    [`"version": "${oldVersion}"`, `"version": "${newVersion}"`],
  ]);
  replaceInFile("scripts/validate_plugin.py", [
    [`PACKAGE_VERSION = "${oldVersion}"`, `PACKAGE_VERSION = "${newVersion}"`],
    [`PROTOCOL_VERSION = "${oldVersion}"`, `PROTOCOL_VERSION = "${newVersion}"`],
  ]);
  replaceInFile("AGENTS.md", [[`v${oldVersion}`, `v${newVersion}`]]);

  const touched = [];
  sweepVersionMarkers(ROOT, oldVersion, newVersion, touched);
  for (const relative of touched) {
    process.stdout.write(`  updated marker ${relative}\n`);
  }

  prependChangelogEntry(newVersion);

  process.stdout.write(
    `\nDone. Next:\n` +
      `  1. Edit keel/CHANGELOG.md ${newVersion} entry.\n` +
      `  2. npm test\n` +
      `  3. git commit -am "${newVersion}"\n` +
      `  4. git tag v${newVersion} && git push --follow-tags && git push origin v${newVersion}\n` +
      `  5. gh release create v${newVersion} --title v${newVersion} --notes "..."\n`
  );
}

main();

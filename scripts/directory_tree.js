#!/usr/bin/env node
"use strict";

// The plugin tree Anthropic's plugin directory lists (#175).
//
// It is the npm package less the scripts only development uses, with the
// manifest renamed and given a homepage, plus an icon.
//
// The directory reads `.claude-plugin/plugin.json` from a branch of a GitHub
// repository and scans every file it finds there. The name `keel` belongs to
// another directory listing, and the whole repository is more than the
// directory scans, so the tree is the files the npm package publishes, which
// already form a complete plugin carrying its own CLI, plus the root manifest
// renamed `keel-openspec` and an icon. The repository's own manifest keeps
// `keel`, which is what marketplace installs use.
//
// Builds locally and submits nothing.
//
// Usage:
//   node scripts/directory_tree.js <empty or absent output directory>

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..");
const DIRECTORY_NAME = "keel-openspec";
const HOMEPAGE = "https://github.com/TanglmChris/keel";
// The scripts the shipped code runs. The rest of `scripts/` is for developing
// Keel — the test suite, the release helpers, this builder — and only adds
// files a reviewer must read for a plugin that never runs them.
const RUNTIME_SCRIPTS = new Set(["run_python.js", "install_to_repo.py"]);
const ICON = path.join(ROOT, "assets", "directory", "icon.png");

function fail(message) {
  process.stderr.write(`directory-tree: ${message}\n`);
  process.exit(1);
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    encoding: "utf8",
    shell: process.platform === "win32",
    ...options,
  });
  if (result.error || result.status !== 0) {
    fail(`${command} ${args.join(" ")} failed: ${result.error ? result.error.message : result.stderr}`);
  }
  return result.stdout;
}

function build(out) {
  const target = path.resolve(out);
  if (fs.existsSync(target) && fs.readdirSync(target).length > 0) {
    fail(`${target} is not empty; build into an empty or absent directory.`);
  }
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "keel-directory-tree-"));
  try {
    const npm = process.platform === "win32" ? "npm.cmd" : "npm";
    const packed = JSON.parse(run(npm, ["pack", "--json", "--pack-destination", temp], { cwd: ROOT }));
    const tarball = path.join(temp, packed[0].filename);
    run("tar", ["-xzf", tarball, "-C", temp]);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.cpSync(path.join(temp, "package"), target, { recursive: true });
  } finally {
    fs.rmSync(temp, { recursive: true, force: true });
  }
  for (const entry of fs.readdirSync(path.join(target, "scripts"))) {
    if (!RUNTIME_SCRIPTS.has(entry)) {
      fs.rmSync(path.join(target, "scripts", entry), { recursive: true, force: true });
    }
  }
  const manifest = JSON.parse(
    fs.readFileSync(path.join(ROOT, ".claude-plugin", "plugin.json"), "utf8")
  );
  manifest.name = DIRECTORY_NAME;
  manifest.homepage = HOMEPAGE;
  fs.mkdirSync(path.join(target, ".claude-plugin"), { recursive: true });
  fs.writeFileSync(
    path.join(target, ".claude-plugin", "plugin.json"),
    `${JSON.stringify(manifest, null, 2)}\n`
  );
  fs.copyFileSync(ICON, path.join(target, ".claude-plugin", "icon.png"));
  return target;
}

if (require.main === module) {
  const [out] = process.argv.slice(2);
  if (!out) fail("usage: node scripts/directory_tree.js <output directory>");
  process.stdout.write(`${build(out)}\n`);
}

module.exports = { build, DIRECTORY_NAME };

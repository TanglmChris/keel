#!/usr/bin/env node
"use strict";

// Advances the branch Anthropic's plugin directory tracks (#175).
//
// The directory follows a branch of the repository, picking up and scanning
// each new commit, so a release publishes to it by committing the directory
// tree (scripts/directory_tree.js) as the next commit of `claude-directory`
// on `origin` and pushing. The branch is started as an orphan the first time.
// A tree identical to the branch head commits nothing, so re-running a
// release adds no commit. Prints the branch head it leaves.
//
// Run from the repository whose `origin` receives the branch; the tree is
// built from the package this script belongs to unless `--tree` names one.
//
// Usage:
//   node scripts/directory_branch.js <X.Y.Z> <40-hex sha> [--tree <dir>] [--no-push]

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");
const { build } = require("./directory_tree");

const BRANCH = "claude-directory";
const IDENTITY = [
  "-c", "user.name=github-actions[bot]",
  "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
];

function fail(message) {
  process.stderr.write(`directory-branch: ${message}\n`);
  process.exit(1);
}

function git(cwd, args, { allowFailure = false } = {}) {
  const result = spawnSync("git", args, { cwd, encoding: "utf8" });
  if (!allowFailure && (result.error || result.status !== 0)) {
    fail(`git ${args.join(" ")} failed: ${result.error ? result.error.message : result.stderr.trim()}`);
  }
  return result;
}

function main() {
  const args = process.argv.slice(2);
  const [version, sha] = args;
  if (!/^\d+\.\d+\.\d+$/.test(version || "") || !/^[0-9a-f]{40}$/.test(sha || "")) {
    fail("usage: node scripts/directory_branch.js <X.Y.Z> <40-hex sha> [--tree <dir>] [--no-push]");
  }
  const treeIndex = args.indexOf("--tree");
  const push = !args.includes("--no-push");
  const repo = process.cwd();
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "keel-directory-branch-"));
  const worktree = path.join(temp, "branch");
  try {
    const tree = treeIndex >= 0 ? path.resolve(args[treeIndex + 1] || "") : build(path.join(temp, "tree"));
    if (!fs.existsSync(path.join(tree, ".claude-plugin", "plugin.json"))) {
      fail(`${tree} is not a directory tree`);
    }
    const remote = git(repo, ["ls-remote", "--heads", "origin", BRANCH]).stdout.trim();
    if (remote) {
      git(repo, ["fetch", "-q", "origin", `refs/heads/${BRANCH}:refs/remotes/origin/${BRANCH}`]);
      git(repo, ["worktree", "add", "-q", "--detach", worktree, `origin/${BRANCH}`]);
    } else {
      git(repo, ["worktree", "add", "-q", "--detach", worktree]);
      git(worktree, ["checkout", "-q", "--orphan", BRANCH]);
    }
    // Replace the worktree's contents with the tree, keeping only `.git`.
    for (const entry of fs.readdirSync(worktree)) {
      if (entry !== ".git") fs.rmSync(path.join(worktree, entry), { recursive: true, force: true });
    }
    fs.cpSync(tree, worktree, { recursive: true });
    git(worktree, ["add", "-A"]);
    const unchanged = remote
      && git(worktree, ["diff", "--cached", "--quiet"], { allowFailure: true }).status === 0;
    if (!unchanged) {
      git(worktree, [...IDENTITY, "commit", "-q", "-m", `keel-openspec ${version} from ${sha}`]);
      if (push) git(worktree, ["push", "-q", "origin", `HEAD:refs/heads/${BRANCH}`]);
    }
    process.stdout.write(`${git(worktree, ["rev-parse", "HEAD"]).stdout.trim()}\n`);
  } finally {
    git(repo, ["worktree", "remove", "--force", worktree], { allowFailure: true });
    fs.rmSync(temp, { recursive: true, force: true });
  }
}

main();

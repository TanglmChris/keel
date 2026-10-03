"use strict";

// The chat's long-term home (issue #187, design D19). Slack's free plan shows
// 90 days and deletes after a year; the project's own repository keeps
// everything, on an orphan branch `keel-chat` that never meets `main`.
//
// Only the synced layer is archived — records, cursors, aliases, presence —
// the files that are written by one writer and never rewritten in place, so
// two machines' archives merge by the union of their paths. The commit is
// made with plumbing and a temporary index: the worktree, the real index, and
// every other branch stay exactly as they were.
//
// A public repository is not pushed unless the project says so, because a
// group's conversation is not something to publish by default.

const fs = require("fs");
const os = require("os");
const path = require("path");
const crypto = require("crypto");
const { spawnSync } = require("child_process");
const store = require("./store");
const { loadChatConfig } = require("./config");

const { ChatError } = store;
const BRANCH = "refs/heads/keel-chat";
const SYNCED_ROOTS = ["groups", "cursors", "members", "presence"];

function git(where, args, { env = {}, input = null, allowFail = false } = {}) {
  const result = spawnSync("git", args, {
    cwd: where.worktree,
    encoding: input !== null && Buffer.isBuffer(input) ? undefined : "utf8",
    env: { ...process.env, ...env },
    input: input === null ? undefined : input,
    maxBuffer: 256 * 1024 * 1024,
  });
  if (result.status !== 0 && !allowFail) {
    throw new ChatError(`git ${args[0]} failed: ${String(result.stderr || "").trim()}`);
  }
  return { ok: result.status === 0, stdout: String(result.stdout || "").trim(), stderr: String(result.stderr || "").trim() };
}

// `archive`: absent or "auto" archives when Slack is on; "off" never does on
// its own; `{ "remote": <name> }` names where to push. `archive_public:
// "accept"` allows pushing a public repository.
function archiveSettings(worktree) {
  const { config } = loadChatConfig(worktree);
  const archive = config.archive === undefined ? "auto" : config.archive;
  const slackOn = Boolean(config.slack && config.slack.enabled === true);
  const declaredRemote = archive && typeof archive === "object" && typeof archive.remote === "string" ? archive.remote : null;
  return {
    automatic: archive === "auto" ? slackOn : archive !== "off" && archive !== false,
    declaredRemote,
    publicAccepted: config.archive_public === "accept",
  };
}

function listSynced(where) {
  const files = [];
  const walk = (relative) => {
    const absolute = path.join(where.root, relative);
    let entries = [];
    try {
      entries = fs.readdirSync(absolute, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries) {
      const child = path.posix.join(relative, entry.name);
      if (entry.isDirectory()) walk(child);
      else if (entry.isFile()) files.push(child);
    }
  };
  for (const root of SYNCED_ROOTS) walk(root);
  return files.sort();
}

function remoteName(where, settings) {
  if (settings.declaredRemote) return settings.declaredRemote;
  const remotes = git(where, ["remote"], { allowFail: true }).stdout.split(/\s+/).filter(Boolean);
  return remotes.includes("origin") ? "origin" : remotes[0] || null;
}

function fetchRemote(where, remote) {
  if (!remote) return null;
  // Into FETCH_HEAD only: no ref, branch, or worktree file changes.
  const fetched = git(where, ["fetch", "--quiet", remote, BRANCH], { allowFail: true });
  if (!fetched.ok) return null;
  const tip = git(where, ["rev-parse", "--verify", "--quiet", "FETCH_HEAD^{commit}"], { allowFail: true });
  return tip.ok ? tip.stdout : null;
}

function treeEntries(where, commit) {
  if (!commit) return new Map();
  const listed = git(where, ["ls-tree", "-r", "-z", commit], { allowFail: true });
  const entries = new Map();
  for (const line of listed.stdout.split("\0").filter(Boolean)) {
    const match = line.match(/^\d+ blob ([0-9a-f]+)\t(.+)$/);
    if (match) entries.set(match[2], match[1]);
  }
  return entries;
}

// Writes into the local store every archived file it lacks. Existing files
// are never overwritten: a record is immutable, and a cursor, alias, or
// presence file belongs to the one role that writes it.
function importMissing(where, entries) {
  let imported = 0;
  for (const [file, blob] of entries) {
    if (!SYNCED_ROOTS.includes(file.split("/")[0])) continue;
    const target = path.join(where.root, ...file.split("/"));
    if (fs.existsSync(target)) continue;
    const content = spawnSync("git", ["cat-file", "blob", blob], { cwd: where.worktree, maxBuffer: 64 * 1024 * 1024 });
    if (content.status !== 0) continue;
    fs.mkdirSync(path.dirname(target), { recursive: true });
    const temp = path.join(where.root, ".tmp", `${process.pid}-${crypto.randomBytes(6).toString("hex")}`);
    fs.mkdirSync(path.dirname(temp), { recursive: true });
    fs.writeFileSync(temp, content.stdout);
    fs.renameSync(temp, target);
    imported += 1;
  }
  return imported;
}

function visibility(where) {
  const gh = process.env.KEEL_CHAT_GH || "gh";
  const result = spawnSync(gh, ["repo", "view", "--json", "visibility", "-q", ".visibility"], {
    cwd: where.worktree, encoding: "utf8", timeout: 20000,
  });
  if (result.status !== 0) return null;
  return String(result.stdout || "").trim().toUpperCase() || null;
}

const IDENTITY = {
  GIT_AUTHOR_NAME: "keel chat archive",
  GIT_AUTHOR_EMAIL: "keel-chat@localhost",
  GIT_COMMITTER_NAME: "keel chat archive",
  GIT_COMMITTER_EMAIL: "keel-chat@localhost",
};

function commitArchive(where, localTip, remoteTip) {
  const index = path.join(os.tmpdir(), `keel-chat-index-${process.pid}-${crypto.randomBytes(4).toString("hex")}`);
  const env = { GIT_INDEX_FILE: index };
  const conflicts = [];
  try {
    if (localTip) git(where, ["read-tree", localTip], { env });
    else git(where, ["read-tree", "--empty"], { env });
    const present = treeEntries(where, localTip);
    for (const [file, blob] of treeEntries(where, remoteTip)) {
      if (!present.has(file)) {
        git(where, ["update-index", "--add", "--cacheinfo", `100644,${blob},${file}`], { env });
        present.set(file, blob);
      }
    }
    for (const file of listSynced(where)) {
      const blob = git(where, ["hash-object", "-w", path.join(where.root, ...file.split("/"))]).stdout;
      const archived = present.get(file);
      if (archived === blob) continue;
      // A record is immutable, so one id with two contents is worth saying;
      // cursors and presence legitimately move on.
      if (archived && file.startsWith("groups/")) conflicts.push(file);
      git(where, ["update-index", "--add", "--cacheinfo", `100644,${blob},${file}`], { env });
    }
    const tree = git(where, ["write-tree"], { env }).stdout;
    const parents = [localTip, remoteTip].filter((tip, i, all) => tip && all.indexOf(tip) === i);
    const localTree = localTip ? git(where, ["rev-parse", `${localTip}^{tree}`]).stdout : null;
    if (localTip && tree === localTree && (!remoteTip || parents.length === 1 || isAncestor(where, remoteTip, localTip))) {
      return { commit: localTip, changed: false, conflicts };
    }
    const count = listSynced(where).filter((file) => file.startsWith("groups/")).length;
    const args = ["commit-tree", tree, "-m", `keel chat archive: ${count} records`];
    for (const parent of parents) args.push("-p", parent);
    const commit = git(where, args, { env: IDENTITY }).stdout;
    git(where, ["update-ref", BRANCH, commit, ...(localTip ? [localTip] : [])]);
    return { commit, changed: true, conflicts };
  } finally {
    fs.rmSync(index, { force: true });
  }
}

function isAncestor(where, ancestor, descendant) {
  return git(where, ["merge-base", "--is-ancestor", ancestor, descendant], { allowFail: true }).ok;
}

function pushDecision(where, settings, remote) {
  if (!remote) return { push: false, reason: "this repository has no remote" };
  if (settings.declaredRemote) return { push: true };
  if (settings.publicAccepted) return { push: true };
  const seen = visibility(where);
  if (seen === "PRIVATE" || seen === "INTERNAL") return { push: true };
  const why = seen === "PUBLIC" ? "this repository is public" : "this repository's visibility could not be confirmed";
  return {
    push: false,
    reason: `${why}, so the chat archive was committed locally and not pushed. To push it, name a private remote `
      + 'with `"archive": { "remote": "<name>" }` (archive.remote) in keel/chat.json, or publish it deliberately '
      + 'with `"archive_public": "accept"` (archive_public).',
  };
}

function sync(where) {
  const settings = archiveSettings(where.worktree);
  const remote = remoteName(where, settings);
  const remoteTip = fetchRemote(where, remote);
  const imported = importMissing(where, treeEntries(where, remoteTip));
  const localTip = git(where, ["rev-parse", "--verify", "--quiet", BRANCH], { allowFail: true }).stdout || null;
  const { commit, changed, conflicts } = commitArchive(where, localTip, remoteTip);
  const decision = pushDecision(where, settings, remote);
  let pushed = false;
  if (decision.push && commit && commit !== remoteTip) {
    const result = git(where, ["push", "--quiet", remote, `${BRANCH}:${BRANCH}`], { allowFail: true });
    if (!result.ok) throw new ChatError(`git push of the chat archive to ${remote} failed: ${result.stderr}`);
    pushed = true;
  }
  return { commit, changed, imported, pushed, remote, refused: decision.push ? null : decision.reason, conflicts };
}

function pull(where) {
  const settings = archiveSettings(where.worktree);
  const remote = remoteName(where, settings);
  const remoteTip = fetchRemote(where, remote);
  const localTip = git(where, ["rev-parse", "--verify", "--quiet", BRANCH], { allowFail: true }).stdout || null;
  let imported = importMissing(where, treeEntries(where, remoteTip));
  imported += importMissing(where, treeEntries(where, localTip));
  if (!remoteTip && !localTip) {
    throw new ChatError(`No chat archive found: neither ${remote ? `${remote}'s` : "a remote"} keel-chat branch nor a local one exists.`);
  }
  return { imported, remote };
}

module.exports = {
  BRANCH,
  archiveSettings,
  pull,
  sync,
};

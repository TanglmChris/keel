"use strict";

// Binding drift (#301). `roles.json` binds roles to worktrees, but sessions
// move: a role can stay bound to a removed worktree, or to one no session runs
// in while its session runs elsewhere, and then nothing wakes it. This reports
// both; `keel chat role --prune` removes the first.

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const store = require("./store");

const UNATTENDED_MS = 2 * 60 * 60 * 1000;

function realpath(file) {
  try {
    return fs.realpathSync(file);
  } catch {
    return path.resolve(file);
  }
}

function liveWorktrees(where) {
  const result = spawnSync("git", ["worktree", "list", "--porcelain"], { cwd: where.worktree, encoding: "utf8" });
  if (result.status !== 0) return null;
  return new Set(String(result.stdout).split("\n").filter((line) => line.startsWith("worktree ")).map((line) => realpath(line.slice(9))));
}

// Bindings whose worktree is neither listed by git nor a directory (D1).
function removedBindings(where) {
  const live = liveWorktrees(where);
  if (!live) return [];
  return Object.entries(store.readJsonFile(path.join(where.root, "roles.json")))
    .filter(([worktree, role]) => role && !live.has(realpath(worktree)) && !fs.existsSync(worktree))
    .map(([worktree, role]) => ({ role, worktree }))
    .sort((a, b) => (a.role < b.role ? -1 : 1));
}

function roleDrift(where, now = Date.now()) {
  const { presenceFile, parkOf } = require("./notice");
  const roles = [...new Set(Object.values(store.readJsonFile(path.join(where.root, "roles.json"))).filter(Boolean))].sort();
  const unattended = [];
  for (const role of roles) {
    // A role parked on purpose is not unattended (#316 D4).
    if (parkOf(where, role)) continue;
    const waiting = [];
    let unread = [];
    try {
      unread = store.unread(where, role).filter((record) => store.wakes(record, role));
    } catch {
      unread = [];
    }
    if (unread.length) waiting.push(`${unread.length} unread addressed record${unread.length === 1 ? "" : "s"}`);
    const note = path.join(where.root, "shift", `${role}.md`);
    if (fs.existsSync(note)) waiting.push(`shift note waiting since ${store.isoLocal(fs.statSync(note).mtime)}`);
    if (!waiting.length) continue;
    const lastActive = store.readJsonFile(presenceFile(where, role)).last_active || null;
    const last = Date.parse(lastActive || "");
    if (!Number.isNaN(last) && now - last <= UNATTENDED_MS) continue;
    unattended.push({ role, waiting, lastActive });
  }
  return { removed: removedBindings(where), unattended };
}

function driftLines(drift) {
  return [
    ...drift.removed.map((entry) => ({
      key: `drift ${entry.role} ${entry.worktree}`,
      text: `${entry.role} is bound to ${entry.worktree}, which no longer exists; \`keel chat role --prune\` drops it`,
    })),
    ...drift.unattended.map((entry) => ({
      key: `drift ${entry.role}`,
      text: `${entry.role} has ${entry.waiting.join(" and ")} and no session active since ${entry.lastActive || "ever"}; `
        + `if its session runs in another worktree, bind ${entry.role} there, since nothing wakes it where it is bound`,
    })),
  ];
}

// Removes the bindings to removed worktrees (D4).
function pruneBindings(where) {
  const removed = removedBindings(where);
  if (!removed.length) return [];
  const roles = store.readJsonFile(path.join(where.root, "roles.json"));
  for (const entry of removed) delete roles[entry.worktree];
  store.writeRoles(where, roles);
  return removed;
}

module.exports = { driftLines, pruneBindings, roleDrift };

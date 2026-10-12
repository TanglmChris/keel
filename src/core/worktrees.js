"use strict";

// Worktree-overview D1-D5: local Git and chat reads only. In particular,
// status must not refresh the index, and role overrides belong to the caller,
// not to every worktree it is inspecting.
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const store = require("./chat/store");
const notice = require("./chat/notice");

const USAGE = "keel worktrees [--repo <path>] [--issues <file>] [--json]";
class WorktreesError extends Error {}

function git(cwd, args, optional = false) {
  const result = spawnSync("git", args, {
    cwd, encoding: "utf8", maxBuffer: 16 * 1024 * 1024,
    env: { ...process.env, GIT_OPTIONAL_LOCKS: "0" },
  });
  if (result.status !== 0) {
    if (optional) return null;
    throw new WorktreesError(`git ${args.join(" ")} in ${cwd}: ${result.error ? result.error.message : String(result.stderr || "failed").trim()}`);
  }
  return String(result.stdout || "").replace(/\n$/, "");
}

// NUL delimiters preserve spaces, quotes and newlines in worktree paths.
function listWorktrees(repo) {
  const rows = [];
  let row = null;
  for (const field of git(repo, ["worktree", "list", "--porcelain", "-z"]).split("\0")) {
    if (field.startsWith("worktree ")) {
      row = { path: field.slice(9), branch: null, head: null, locked: null, prunable: null };
      rows.push(row);
    } else if (row) {
      if (field.startsWith("HEAD ")) row.head = field.slice(5);
      else if (field.startsWith("branch ")) row.branch = field.slice(7).replace(/^refs\/heads\//, "");
      else if (field === "locked") row.locked = true;
      else if (field.startsWith("locked ")) row.locked = field.slice(7);
      else if (field === "prunable") row.prunable = true;
      else if (field.startsWith("prunable ")) row.prunable = field.slice(9);
    }
  }
  return rows;
}

function defaultBranch(repo) {
  const remote = git(repo, ["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"], true);
  if (remote) return remote.replace(/^refs\/remotes\//, "");
  for (const branch of ["main", "master"]) {
    if (git(repo, ["show-ref", "--verify", `refs/heads/${branch}`], true) !== null) return branch;
  }
  return null;
}

// The issues a branch's commits beyond `base` reference as `#<n>`, newest
// commit first and without repeats (#278 D1); `limit` caps the list.
function branchIssues(cwd, base, limit = Infinity) {
  if (!base) return [];
  const log = git(cwd, ["log", "--format=%s%n%b%x00", `${base}..HEAD`, "--"], true);
  if (!log) return [];
  const seen = [];
  for (const message of log.split("\0")) {
    for (const match of message.matchAll(/#(\d+)/g)) {
      const number = Number(match[1]);
      if (Number.isSafeInteger(number) && number > 0 && !seen.includes(number)) seen.push(number);
    }
  }
  return seen.slice(0, limit);
}

function readIssues(file) {
  if (file === null) return null;
  try {
    const rows = JSON.parse(fs.readFileSync(file, "utf8"));
    if (!Array.isArray(rows)) throw new Error("expected a JSON array of objects with number and updatedAt");
    const times = new Map();
    for (const row of rows) {
      if (!row || !Number.isSafeInteger(row.number) || row.number <= 0
          || !(typeof row.updatedAt === "string" || row.updatedAt === null)) {
        throw new Error("expected each issue to have a positive integer number and updatedAt (string or null)");
      }
      times.set(row.number, row.updatedAt);
    }
    return times;
  } catch (error) {
    throw new WorktreesError(`Cannot read --issues ${file}: ${error.message}`);
  }
}

function inspect(where, row, base, roles, times) {
  if (!fs.existsSync(row.path)) {
    return { path: row.path, missing: true, locked: row.locked, prunable: row.prunable };
  }
  const head = git(row.path, ["rev-parse", "--short", "HEAD"], true);
  const upstream = row.branch
    ? git(row.path, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], true)
    : null;
  let ahead = null;
  let behind = null;
  if (upstream) {
    const counts = git(row.path, ["rev-list", "--left-right", "--count", `${upstream}...HEAD`]).trim().split(/\s+/).map(Number);
    [behind, ahead] = counts;
  }
  let lastCommit = null;
  if (head) {
    const last = git(row.path, ["log", "-1", "--format=%s%x00%cI", "HEAD"]).split("\0");
    lastCommit = { subject: last[0], time: last[1] };
  }
  const dirty = git(row.path, ["status", "--porcelain"]).split("\n").filter(Boolean).length;
  const bound = roles[fs.realpathSync(row.path)];
  const role = typeof bound === "string" && new RegExp(store.NAME_PATTERN_TEXT).test(bound) ? bound : null;
  const issues = head ? branchIssues(row.path, base).sort((a, b) => a - b) : [];
  const result = {
    ...row, head, missing: false, upstream, ahead, behind, lastCommit, dirty,
    role, presence: role ? notice.presenceOf(where, role) : null, issues,
  };
  if (times) result.issueUpdates = issues.map((number) => ({ number, updatedAt: times.get(number) ?? null }));
  return result;
}

function render(result) {
  const lines = [
    `keel worktrees: default branch ${result.defaultBranch || "unknown (no origin/HEAD, main or master)"}`,
    "Ahead/behind counts are as of the last fetch; Keel does not fetch.",
  ];
  for (const row of result.worktrees) {
    const markers = [row.locked ? `locked${row.locked === true ? "" : `: ${row.locked}`}` : null,
      row.prunable ? `prunable${row.prunable === true ? "" : `: ${row.prunable}`}` : null].filter(Boolean);
    lines.push(`${row.path}${markers.length ? ` (${markers.join("; ")})` : ""}`);
    if (row.missing) {
      lines.push("  missing");
      continue;
    }
    lines.push(`  ${row.branch || "detached"} ${row.head || "(no commits)"}; ${row.upstream ? `upstream ${row.upstream}, ahead ${row.ahead}, behind ${row.behind}` : "no upstream"}; dirty ${row.dirty}`);
    if (row.lastCommit) lines.push(`  last commit: ${row.lastCommit.subject} (${row.lastCommit.time})`);
    lines.push(`  role: ${row.role ? `${row.role}, ${row.presence.state}, last active ${row.presence.last_active || "unknown"}` : "none"}`);
    const updates = new Map((row.issueUpdates || []).map((issue) => [issue.number, issue.updatedAt]));
    lines.push(`  issues: ${row.issues.length ? row.issues.map((number) => `#${number}${row.issueUpdates ? ` (updatedAt: ${updates.get(number) || "unknown"})` : ""}`).join(", ") : "none"}`);
  }
  return lines.join("\n");
}

function runWorktrees(argv) {
  const options = { repo: process.cwd(), issues: null, json: false };
  try {
    for (let index = 0; index < argv.length; index += 1) {
      const arg = argv[index];
      if (arg === "--json") options.json = true;
      else if (arg === "--help" || arg === "-h") {
        process.stdout.write(`${USAGE}\nIssue times come only from --issues (a JSON array with number and updatedAt).\n`);
        return 0;
      } else if (arg === "--repo" || arg === "--issues") {
        const value = argv[++index];
        if (!value || value.startsWith("--")) throw new WorktreesError(`${arg} needs a value.`);
        options[arg === "--repo" ? "repo" : "issues"] = value;
      } else throw new WorktreesError(`Unknown argument ${arg}. ${USAGE}`);
    }
    // Refuse a bad file before collecting or printing any repository state.
    const times = readIssues(options.issues);
    const where = store.locate(options.repo);
    if (!where) throw new WorktreesError(`Not a git repository: ${options.repo}`);
    const base = defaultBranch(where.worktree);
    const roles = store.readJsonFile(path.join(where.root, "roles.json"));
    const result = {
      defaultBranch: base,
      worktrees: listWorktrees(where.worktree).map((row) => inspect(where, row, base, roles, times)),
    };
    process.stdout.write(`${options.json ? JSON.stringify(result, null, 2) : render(result)}\n`);
    return 0;
  } catch (error) {
    if (error instanceof WorktreesError) {
      process.stderr.write(`keel worktrees: ${error.message}\n`);
      return 1;
    }
    throw error;
  }
}

module.exports = { WorktreesError, runWorktrees, branchIssues, defaultBranch };

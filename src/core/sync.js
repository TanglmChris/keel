"use strict";

// What exists only on this machine (#526 D1-D4): every worktree, local branch
// and stash entry of the repository that is not on the remote, read from local
// refs. It reuses the worktree listing of `keel worktrees` and its git reader,
// which never takes an optional lock, so it is safe beside a running session
// and from the tick's `/` (#524): every read names its repository.

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const worktrees = require("./worktrees");

const USAGE = "keel sync status [--repo <path>] [--verify] [--remote <name>] [--json]";
const LOOKUP_TIMEOUT_MS = 30000;
const { git, WorktreesError } = worktrees;

class SyncError extends Error {
  constructor(message, code = 2) {
    super(message);
    this.code = code;
  }
}

function read(cwd, args) {
  return git(cwd, args, true);
}

// The repository's common directory and its main worktree, whatever worktree
// or subdirectory the caller names.
function locate(repo) {
  if (!fs.existsSync(repo)) throw new SyncError(`No such directory: ${repo}`);
  const top = read(repo, ["rev-parse", "--show-toplevel"]);
  if (!top) throw new SyncError(`Not a git repository: ${repo}`);
  const common = read(top, ["rev-parse", "--path-format=absolute", "--git-common-dir"]);
  const rows = worktrees.listWorktrees(top);
  return { worktree: top, common, main: rows.length ? rows[0].path : top, rows };
}

// When the remote-tracking refs were last refreshed: the newest FETCH_HEAD of
// the repository or any of its worktrees, or null when none was ever fetched.
function lastFetch(common) {
  const candidates = [path.join(common, "FETCH_HEAD")];
  const linked = path.join(common, "worktrees");
  try {
    for (const name of fs.readdirSync(linked)) candidates.push(path.join(linked, name, "FETCH_HEAD"));
  } catch {
    // no linked worktrees
  }
  let newest = null;
  for (const file of candidates) {
    try {
      const time = fs.statSync(file).mtime;
      if (!newest || time > newest) newest = time;
    } catch {
      // never fetched there
    }
  }
  return newest ? newest.toISOString() : null;
}

function remotes(cwd) {
  return (read(cwd, ["remote"]) || "").split("\n").filter(Boolean);
}

// Commits reachable from `sha` that no remote-tracking ref contains.
function unpushedCount(cwd, sha) {
  const out = read(cwd, ["rev-list", "--count", sha, "--not", "--remotes"]);
  return out === null ? 0 : Number(out.trim()) || 0;
}

function localBranches(cwd) {
  return allBranches(cwd).filter((row) => row.unpushed > 0).map(({ branch, head, upstream, remote, unpushed, remoteName }) =>
    ({ branch, head, upstream, remote, unpushed, remoteName }));
}

// Every local branch, with the remote it belongs to: its upstream's remote,
// else `origin` (#526 A4), and the remote-tracking ref that counterpart is.
function allBranches(cwd, override = null) {
  const out = read(cwd, ["for-each-ref", "--format=%(refname:short)%00%(objectname)%00%(upstream:short)%00%(upstream:remotename)", "refs/heads/"]) || "";
  const rows = [];
  for (const line of out.split("\n").filter(Boolean)) {
    const [branch, sha, upstream, upstreamRemote] = line.split("\0");
    const remoteName = override || upstreamRemote || "origin";
    const remoteRef = upstream || (read(cwd, ["rev-parse", "--verify", "--quiet", `refs/remotes/${remoteName}/${branch}`]) ? `${remoteName}/${branch}` : null);
    rows.push({ branch, head: sha, upstream: upstream || null, remote: remoteRef, remoteName, unpushed: unpushedCount(cwd, sha) });
  }
  return rows;
}

// One `git ls-remote --heads` per remote (#526 D3), limited in time and never
// prompting; it writes no ref. A failure is returned, never thrown.
function lookup(cwd, remote) {
  const env = { ...process.env, GIT_TERMINAL_PROMPT: "0", GIT_OPTIONAL_LOCKS: "0" };
  if (!env.GIT_SSH_COMMAND) env.GIT_SSH_COMMAND = "ssh -o BatchMode=yes";
  const ran = spawnSync("git", ["ls-remote", remote, "refs/heads/*", "refs/keel/lock/*"], { cwd, encoding: "utf8", env, timeout: LOOKUP_TIMEOUT_MS });
  if (ran.error || ran.status !== 0) {
    const why = ran.error ? (ran.error.code === "ETIMEDOUT" ? `timed out after ${LOOKUP_TIMEOUT_MS / 1000} s` : ran.error.message)
      : String(ran.stderr || "").trim().split("\n").pop() || `git ls-remote exited ${ran.status}`;
    return { error: why };
  }
  const heads = new Map();
  const locks = new Map();
  for (const line of String(ran.stdout || "").split("\n").filter(Boolean)) {
    const [sha, ref] = line.split("\t");
    if (ref && ref.startsWith("refs/heads/")) heads.set(ref.slice("refs/heads/".length), sha);
    if (ref && ref.startsWith("refs/keel/lock/")) locks.set(ref.slice("refs/keel/lock/".length), sha);
  }
  return { heads, locks };
}

function ancestor(cwd, older, newer) {
  return read(cwd, ["merge-base", "--is-ancestor", older, newer]) !== null;
}

// How a local tip stands against the sha the remote itself reports.
function classify(cwd, local, remote) {
  if (!remote) return "not-on-remote";
  if (remote === local) return "same";
  if (read(cwd, ["cat-file", "-e", `${remote}^{commit}`]) === null) return "unknown-to-local";
  if (ancestor(cwd, remote, local)) return "remote-behind";
  if (ancestor(cwd, local, remote)) return "remote-ahead";
  return "diverged";
}

const SETTLED = new Set(["same", "remote-ahead"]);

function verify(cwd, override) {
  const branches = allBranches(cwd, override);
  const answers = new Map();
  for (const name of [...new Set(branches.map((row) => row.remoteName))]) answers.set(name, lookup(cwd, name));
  return {
    remotes: [...answers.keys()],
    branches: branches.map((row) => {
      const answer = answers.get(row.remoteName);
      if (answer.error) return { branch: row.branch, remote: row.remoteName, local: row.head, state: "cannot verify", error: answer.error };
      const remoteSha = answer.heads.get(row.branch) || null;
      const lockSha = answer.locks.get(row.branch) || null;
      const fetchedLock = read(cwd, ["rev-parse", "--verify", "--quiet", `refs/keel/lock/${row.branch}`]) || null;
      return {
        branch: row.branch, remote: row.remoteName, local: row.head, remoteSha, state: classify(cwd, row.head, remoteSha),
        lockSha, lockMoved: lockSha !== fetchedLock,
      };
    }),
  };
}

function dirtyCount(cwd) {
  const out = read(cwd, ["status", "--porcelain=v1", "-z", "--untracked-files=all"]);
  if (!out) return 0;
  const fields = out.split("\0").filter(Boolean);
  let count = 0;
  for (let index = 0; index < fields.length; index += 1) {
    count += 1;
    if (fields[index][0] === "R" || fields[index][0] === "C") index += 1;
  }
  return count;
}

function localWorktrees(rows, localOnly) {
  const listed = [];
  for (const row of rows) {
    if (!fs.existsSync(row.path)) {
      listed.push({ path: row.path, missing: true, branch: row.branch });
      continue;
    }
    const dirty = dirtyCount(row.path);
    const detachedUnpushed = !row.branch && row.head ? unpushedCount(row.path, row.head) : 0;
    const branchLocal = row.branch ? localOnly.has(row.branch) : false;
    if (!dirty && !detachedUnpushed && !branchLocal) continue;
    listed.push({
      path: row.path, missing: false, branch: row.branch, head: row.head,
      dirty, detachedUnpushed, localBranch: branchLocal,
    });
  }
  return listed;
}

function stashes(cwd) {
  const out = read(cwd, ["stash", "list", "--format=%gd%x00%gs%x00%ct"]) || "";
  return out.split("\n").filter(Boolean).map((line) => {
    const [ref, subject, time] = line.split("\0");
    const match = subject.match(/^(?:WIP on|On) ([^:]+):/);
    return { ref, subject, branch: match ? match[1] : null, time: new Date(Number(time) * 1000).toISOString() };
  });
}

// Stable standing risks for the patrol: age decides eligibility but never
// enters the text, so the existing since-last mechanism sends each item once.
function oldLocalOnlyRisks(where, covered, repositoryWide, now = Date.now()) {
  const rows = worktrees.listWorktrees(where.worktree);
  const roles = JSON.parse(fs.existsSync(path.join(where.common, "keel-chat", "roles.json"))
    ? fs.readFileSync(path.join(where.common, "keel-chat", "roles.json"), "utf8") : "{}");
  const risks = [];
  const old = (sha) => {
    const times = (read(where.worktree, ["log", "--format=%ct", sha, "--not", "--remotes"]) || "")
      .split("\n").filter(Boolean).map(Number).filter(Number.isFinite);
    return times.length && Math.min(...times) * 1000 < now - 24 * 3600000;
  };
  if (remotes(where.worktree).length) {
    for (const row of rows) {
      const role = roles[row.path];
      if (!role || !covered(role) || !row.head || !old(row.head)) continue;
      risks.push(`${role}: local-only ${row.branch ? `branch ${row.branch}` : `detached head in ${row.path}`} has work only on this machine; run \`keel sync status\`.`);
    }
    if (repositoryWide) {
      const checkedOut = new Set(rows.map((row) => row.branch).filter(Boolean));
      for (const branch of localBranches(where.worktree)) {
        if (!checkedOut.has(branch.branch) && old(branch.head)) {
          risks.push(`local-only branch ${branch.branch} has work only on this machine; run \`keel sync status\`.`);
        }
      }
    }
  }
  if (repositoryWide) {
    for (const stash of stashes(where.worktree)) {
      if (Date.parse(stash.time) < now - 24 * 3600000) risks.push(`local-only stash ${stash.ref} (${stash.subject}) has work only on this machine; run \`keel sync status\`.`);
    }
  }
  return risks;
}

// The whole report, from local refs only.
function status(repo, options = {}) {
  const where = locate(repo);
  const hasRemote = remotes(where.worktree).length > 0;
  const branches = hasRemote ? localBranches(where.worktree) : [];
  const localOnly = new Set(branches.map((row) => row.branch));
  const result = {
    repository: where.main,
    hasRemote,
    lastFetch: lastFetch(where.common),
    branches,
    worktrees: localWorktrees(where.rows, localOnly),
    stashes: stashes(where.worktree),
    locks: require("./lock").branchLocks({ root: path.join(where.common, "keel-chat") }, where.worktree)
      .map(({ branch, state, holder, expires, head, sha }) => ({ branch, state, holder, expires, head, sha })),
  };
  result.localOnly = result.branches.length + result.worktrees.length + result.stashes.length > 0;
  if (options.verify && hasRemote) {
    result.verify = verify(where.worktree, options.remote || null);
    result.unverified = result.verify.branches.some((row) => !SETTLED.has(row.state));
  } else {
    result.unverified = false;
  }
  attachFixes(where.worktree, result);
  return result;
}

// The fix for each local-only item and the `authorize:` entry that covers it
// (#526 D5). Printed, never run.
function attachFixes(cwd, result) {
  let declared = [];
  let globs = [];
  try {
    const authorization = require("./config").readStandingAuthorization(cwd);
    declared = authorization.declared || [];
    globs = authorization.pushGlobs || [];
  } catch {
    // an unreadable declaration authorizes nothing
  }
  const { globRegExp } = require("./branches");
  const pushCover = (branch) => {
    if (declared.includes("push")) return "push";
    const glob = globs.find((pattern) => globRegExp(pattern).test(branch));
    return glob ? `push:${glob}` : null;
  };
  for (const row of result.branches) {
    const remote = row.remoteName || "origin";
    const command = row.upstream ? `git push ${remote} ${row.branch}` : `git push -u ${remote} ${row.branch}`;
    const cover = pushCover(row.branch);
    row.fix = { command, authorizedBy: cover, declare: cover ? null : `push or push:${row.branch}` };
  }
  for (const row of result.worktrees) {
    if (row.missing || !row.dirty) continue;
    const commit = declared.includes("commit") ? "commit" : null;
    row.fix = { command: `commit in ${row.path}, then push its branch`, authorizedBy: commit, declare: commit ? null : "commit" };
  }
  for (const row of result.stashes) {
    row.fix = { command: `git stash pop ${row.ref} on ${row.branch || "its branch"}, then commit and push`, authorizedBy: null, declare: null };
  }
}

function describeFix(fix) {
  if (!fix) return [];
  const cover = fix.authorizedBy ? `authorized by \`${fix.authorizedBy}\`` : fix.declare ? `not authorized; declare \`${fix.declare.replace(" or ", "` or `")}\` in keel/config.yaml authorize:` : "a person's step";
  return [`  fix: ${fix.command} (${cover})`];
}

function describeWorktree(row) {
  if (row.missing) return `worktree ${row.path}: missing`;
  const parts = [];
  if (row.dirty) parts.push(`${row.dirty} uncommitted or untracked path${row.dirty === 1 ? "" : "s"}`);
  if (row.detachedUnpushed) parts.push(`detached head with ${row.detachedUnpushed} commit${row.detachedUnpushed === 1 ? "" : "s"} on no remote`);
  if (row.localBranch) parts.push(`on branch ${row.branch}, listed above`);
  return `worktree ${row.path} (${row.branch || "detached"}): ${parts.join("; ")}`;
}

function render(result) {
  const lines = [
    `keel sync status: ${result.repository}`,
    `Remote-tracking refs are read as of the last fetch (${result.lastFetch || "never fetched"}); Keel does not fetch.`,
  ];
  if (!result.hasRemote) lines.push("This repository has no remote, so unpushed commits were not checked.");
  if (!result.localOnly) {
    lines.push("Nothing is only on this machine.");
  } else {
    lines.push("Only on this machine:");
    for (const row of result.branches) {
      lines.push(`branch ${row.branch}: ${row.remote
        ? `${row.unpushed} unpushed commit${row.unpushed === 1 ? "" : "s"} (remote ${row.remote})`
        : `no remote counterpart, ${row.unpushed} commit${row.unpushed === 1 ? "" : "s"}`}`);
      lines.push(...describeFix(row.fix));
    }
    for (const row of result.worktrees) {
      lines.push(describeWorktree(row));
      lines.push(...describeFix(row.fix));
    }
    for (const row of result.stashes) {
      lines.push(`stash ${row.ref}: ${row.subject} (${row.time})`);
      lines.push(...describeFix(row.fix));
    }
  }
  if (result.locks.length) {
    lines.push("Branch locks, as last fetched:");
    for (const lock of result.locks) {
      lines.push(`lock ${lock.branch}: ${lock.state} by ${lock.holder}, expires ${lock.expires || "unknown"}, head ${lock.head ? lock.head.slice(0, 8) : "none"}`);
    }
  }
  if (result.verify) {
    lines.push(`Verified against the remote itself (git ls-remote ${result.verify.remotes.join(", ")}):`);
    for (const row of result.verify.branches) {
      const shas = row.state === "cannot verify" ? row.error
        : `local ${row.local.slice(0, 8)}, remote ${row.remoteSha ? row.remoteSha.slice(0, 8) : "none"}`;
      lines.push(`verify ${row.branch}: ${row.state} (${shas})${row.lockMoved ? `; its lock on the remote is ${row.lockSha ? row.lockSha.slice(0, 8) : "gone"}, not the one last fetched` : ""}`);
    }
  }
  return lines.join("\n");
}

function runSync(argv) {
  const options = { repo: process.cwd(), json: false, verify: false, remote: null };
  try {
    const [command, ...rest] = argv;
    if (command === "--help" || command === "-h" || command === undefined) {
      process.stdout.write(`${USAGE}\nLists what exists only on this machine, from local refs; --verify asks the remote for its real sha. Exit 0 when nothing, 1 when something, 2 on error.\n`);
      return command === undefined ? 2 : 0;
    }
    if (command !== "status") throw new SyncError(`Unknown subcommand ${command}. ${USAGE}`);
    for (let index = 0; index < rest.length; index += 1) {
      const arg = rest[index];
      if (arg === "--json") options.json = true;
      else if (arg === "--verify") options.verify = true;
      else if (arg === "--repo" || arg === "--remote") {
        const value = rest[++index];
        if (!value || value.startsWith("--")) throw new SyncError(`${arg} needs a value.`);
        if (arg === "--repo") options.repo = path.resolve(value);
        else options.remote = value;
      } else throw new SyncError(`Unknown argument ${arg}. ${USAGE}`);
    }
    if (options.remote && !options.verify) throw new SyncError("--remote names the remote --verify asks; pass --verify too.");
    const result = status(options.repo, options);
    process.stdout.write(`${options.json ? JSON.stringify(result, null, 2) : render(result)}\n`);
    return result.localOnly || result.unverified ? 1 : 0;
  } catch (error) {
    if (error instanceof SyncError || error instanceof WorktreesError) {
      process.stderr.write(`keel sync: ${error.message}\n`);
      return 2;
    }
    throw error;
  }
}

module.exports = { oldLocalOnlyRisks, SyncError, status, render, runSync, stashes, lastFetch, verify, lookup, classify, USAGE };

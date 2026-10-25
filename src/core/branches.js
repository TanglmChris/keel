"use strict";

// A role's merged task branches (#469): listed with their sha and the trunk
// that contains them, deleted only under `delete-branch:merged`, with a record
// that restores each one. Keel lists without fetching; prune fetches first,
// because it acts on what it finds.

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const REMOTE = "origin";

class BranchesError extends Error {
  constructor(message, code = 1) {
    super(message);
    this.code = code;
  }
}

function git(cwd, args) {
  const result = spawnSync("git", args, { cwd, encoding: "utf8" });
  return { ok: result.status === 0, out: String(result.stdout || "").replace(/\s+$/, ""), err: String(result.stderr || "").trim() };
}

function realpath(file) {
  try {
    return fs.realpathSync(file);
  } catch {
    return path.resolve(file);
  }
}

// `*` within a `/` segment and `**` across them, as Touch globs read (D2 e).
function globRegExp(glob) {
  let source = "";
  for (let i = 0; i < glob.length; i += 1) {
    if (glob[i] === "*" && glob[i + 1] === "*") {
      source += ".*";
      i += 1;
    } else if (glob[i] === "*") {
      source += "[^/]*";
    } else {
      source += glob[i].replace(/[.+?^${}()|[\]\\]/g, "\\$&");
    }
  }
  return new RegExp(`^${source}$`);
}

const { readBranchesDeclaration } = require("./config");

function remoteDefault(cwd) {
  const head = git(cwd, ["symbolic-ref", "--quiet", "--short", `refs/remotes/${REMOTE}/HEAD`]);
  if (head.ok && head.out) return head.out.slice(REMOTE.length + 1);
  for (const name of ["main", "master"]) {
    if (git(cwd, ["rev-parse", "--verify", "--quiet", `refs/remotes/${REMOTE}/${name}`]).ok) return name;
  }
  return null;
}

// The trunks as remote-tracking refs, and the declared ones that have none.
function trunks(cwd, declared) {
  const names = [...new Set([remoteDefault(cwd), ...declared.trunk].filter(Boolean))];
  const found = [];
  const missing = [];
  for (const name of names) {
    const ref = `refs/remotes/${REMOTE}/${name}`;
    if (git(cwd, ["rev-parse", "--verify", "--quiet", ref]).ok) found.push({ name, ref });
    else missing.push(name);
  }
  return { found, missing };
}

function refs(cwd, prefix) {
  const listed = git(cwd, ["for-each-ref", "--format=%(refname)\t%(objectname)", prefix]);
  return listed.out.split("\n").filter(Boolean).map((line) => {
    const [ref, sha] = line.split("\t");
    return { ref, sha };
  });
}

function checkedOut(cwd) {
  const listed = git(cwd, ["worktree", "list", "--porcelain"]);
  return new Set(listed.out.split("\n").filter((line) => line.startsWith("branch refs/heads/"))
    .map((line) => line.slice("branch refs/heads/".length)));
}

// Branches a worktree bound to the role has checked out, from its own HEAD
// reflog (D2 d, F1).
function owned(where, role) {
  const roles = JSON.parse(fs.readFileSync(path.join(where.root, "roles.json"), "utf8"));
  const names = new Set();
  for (const [worktree, name] of Object.entries(roles)) {
    if (name !== role || !fs.existsSync(worktree)) continue;
    const reflog = git(worktree, ["reflog", "show", "--format=%gs", "HEAD"]);
    for (const line of reflog.out.split("\n")) {
      const moved = line.match(/^checkout: moving from (\S+) to (\S+)$/);
      if (moved) {
        names.add(moved[1]);
        names.add(moved[2]);
      }
    }
  }
  return names;
}

function lastFetch(cwd) {
  const file = git(cwd, ["rev-parse", "--git-path", "FETCH_HEAD"]);
  if (!file.ok) return null;
  try {
    return fs.statSync(path.resolve(cwd, file.out)).mtime.toISOString();
  } catch {
    return null;
  }
}

// The role's qualifying branches on each side (D2).
function merged(where, role) {
  const cwd = where.worktree;
  const declared = readBranchesDeclaration(cwd);
  const { found, missing } = trunks(cwd, declared);
  const trunkNames = new Set([...found.map((t) => t.name), ...missing]);
  const busy = checkedOut(cwd);
  const mine = owned(where, role);
  const kept = declared.keep.map(globRegExp);
  const containing = (sha) => found.find((trunk) => git(cwd, ["merge-base", "--is-ancestor", sha, trunk.ref]).ok);
  const branches = [];
  const sides = [
    { side: "local", prefix: "refs/heads/", list: refs(cwd, "refs/heads/") },
    { side: "remote", prefix: `refs/remotes/${REMOTE}/`, list: refs(cwd, `refs/remotes/${REMOTE}/`) },
  ];
  for (const { side, prefix, list } of sides) {
    for (const { ref, sha } of list) {
      const name = ref.slice(prefix.length);
      if (name === "HEAD" || trunkNames.has(name) || !mine.has(name) || kept.some((re) => re.test(name))) continue;
      if (side === "local" && busy.has(name)) continue;
      if (side === "remote" && busy.has(name)) continue;
      const trunk = containing(sha);
      if (trunk) branches.push({ side, branch: name, sha, trunk: `${REMOTE}/${trunk.name}` });
    }
  }
  return {
    role,
    trunks: found.map((t) => `${REMOTE}/${t.name}`),
    missingTrunks: missing,
    branches,
    fetched: lastFetch(cwd),
    message: declared.message,
  };
}

function describe(result) {
  const lines = [];
  if (result.message) lines.push(result.message);
  for (const name of result.missingTrunks) lines.push(`Trunk ${name} has no ${REMOTE}/${name} here, so nothing is judged against it.`);
  if (!result.branches.length) {
    lines.push(`No merged task branch of ${result.role} to delete (trunks: ${result.trunks.join(", ") || "none"}; refs as last fetched ${result.fetched || "never"}).`);
    return lines.join("\n");
  }
  lines.push(`Merged task branches of ${result.role} (trunks: ${result.trunks.join(", ")}; refs as last fetched ${result.fetched || "never"}):`);
  for (const b of result.branches) lines.push(`- ${b.side === "remote" ? `${REMOTE}/` : ""}${b.branch} ${b.sha.slice(0, 12)} (in ${b.trunk})`);
  return lines.join("\n");
}

const USAGE = [
  "keel branches [repo] [--role <role>] [--json]   a role's merged task branches, with their sha; fetches and deletes nothing",
].join("\n");

function parse(argv) {
  const options = { json: false, role: null, positionals: [], help: false, unknown: null };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--json") options.json = true;
    else if (arg === "--role") options.role = argv[++i] || null;
    else if (arg === "--repo") options.positionals.push(argv[++i]);
    else if (arg === "--help" || arg === "-h") options.help = true;
    else if (arg.startsWith("-")) options.unknown = arg;
    else options.positionals.push(arg);
  }
  return options;
}

function runBranches(argv) {
  const options = parse(argv);
  if (options.help) {
    process.stdout.write(`${USAGE}\n`);
    return 0;
  }
  if (options.unknown) {
    process.stderr.write(`keel branches: unknown option ${options.unknown}\n${USAGE}\n`);
    return 2;
  }
  const store = require("./chat/store");
  try {
    const where = store.requireLocation(path.resolve(options.positionals[0] || process.cwd()));
    const role = options.role || store.currentRole(where);
    if (!role) throw new BranchesError("This worktree is bound to no role; name one with --role.", 2);
    const result = merged(where, role);
    process.stdout.write(options.json ? `${JSON.stringify(result)}\n` : `${describe(result)}\n`);
    return 0;
  } catch (error) {
    if (error instanceof BranchesError || error instanceof store.ChatError) {
      process.stderr.write(`keel branches: ${error.message}\n`);
      return error.code || 1;
    }
    throw error;
  }
}

module.exports = { BranchesError, readBranchesDeclaration, merged, describe, runBranches, globRegExp, REMOTE, USAGE };

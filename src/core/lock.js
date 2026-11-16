"use strict";

// Resource-lock D1-D6: cooperative leases in the git common chat store.
// These records never guard Git operations or access to the named resource.
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const store = require("./chat/store");

const RESOURCE = /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/;
const USAGE = [
  "keel lock acquire <resource> --for <n>s|m|h|d --note <why>   acquire or renew",
  "keel lock release <resource>                              holder only",
  "keel lock acquire --branch <b> [--for <d>] [--note <why>] [--break <reason>] [--push]",
  "                                                          a branch lock kept on the remote (#526)",
  "keel lock release --branch <b>                            after the branch is pushed",
  "keel lock list [--json]                                   live leases and fetched branch locks",
  "Options: --repo <path>, --json. See docs/resource-lock.md.",
  "A local lease enforces nothing on Git or the filesystem.",
].join("\n");
const { spawnSync } = require("child_process");
const os = require("os");

const GRACE_MS = 5 * 60 * 1000;
const LOCK_PREFIX = "refs/keel/lock/";
const LOOKUP_TIMEOUT_MS = 30000;

class LockError extends Error {}

function lockDir(where) {
  return path.join(where.root, "locks");
}

function identity(where) {
  const role = store.currentRole(where);
  const id = crypto.createHash("sha256").update(where.worktree).digest("hex").slice(0, 8);
  return { holder: role || "worktree:" + path.basename(where.worktree) + "-" + id, role: role || null, worktree: where.worktree };
}

function checkResource(resource) {
  if (!RESOURCE.test(resource || "")) {
    throw new LockError("Invalid resource " + JSON.stringify(resource) + ': use 1–64 letters, digits, ".", "_" or "-", starting with a letter or digit.');
  }
}

function expiry(duration, now) {
  const match = String(duration || "").match(/^(\d+)([smhd])$/);
  const amount = match ? Number(match[1]) : 0;
  const unit = match ? { s: 1000, m: 60000, h: 3600000, d: 86400000 }[match[2]] : 0;
  const date = new Date(now.getTime() + amount * unit);
  if (!match || !Number.isSafeInteger(amount) || amount <= 0 || !Number.isFinite(date.getTime()) || date.getFullYear() > 9999) {
    throw new LockError("Invalid --for duration " + JSON.stringify(duration) + ": use a positive integer followed by s, m, h or d.");
  }
  return store.isoLocal(date);
}

function readLeases(where) {
  let files;
  try {
    files = fs.readdirSync(lockDir(where));
  } catch (error) {
    if (error.code === "ENOENT") return [];
    throw error;
  }
  const leases = [];
  for (const name of files.sort()) {
    if (!name.endsWith(".json")) continue;
    const file = path.join(lockDir(where), name);
    let lease;
    try {
      lease = JSON.parse(fs.readFileSync(file, "utf8"));
    } catch (error) {
      if (error.code === "ENOENT") continue; // Concurrent release.
      throw new LockError("Cannot read lease " + file + ": " + error.message);
    }
    if (!lease || !RESOURCE.test(lease.resource || "") || name !== lease.resource + ".json"
        || typeof lease.holder !== "string" || typeof lease.worktree !== "string"
        || !Number.isFinite(Date.parse(lease.expires)) || !Array.isArray(lease.waiters)) {
      throw new LockError("Malformed lease " + file + ".");
    }
    leases.push(lease);
  }
  return leases;
}

// Pure read for shift check: never reap expiry or post chat records.
function liveLeases(where, now = Date.now()) {
  return readLeases(where).filter((lease) => Date.parse(lease.expires) > now);
}

function describe(lease) {
  return lease.resource + ": held by " + lease.holder + " (" + lease.worktree + "), expires " + lease.expires + ": " + lease.note;
}

// Serialize read/modify/write and expiry notifications across worktrees.
// The lease itself still uses exclusive creation. A bounded wait fails closed
// rather than deleting another command's mutex or stealing a lease.
function withMutation(where, action) {
  fs.mkdirSync(lockDir(where), { recursive: true });
  const mutex = path.join(lockDir(where), ".mutation");
  const deadline = Date.now() + 5000;
  while (true) {
    try {
      fs.mkdirSync(mutex);
      break;
    } catch (error) {
      if (error.code !== "EEXIST") throw error;
      // A mutex left by a crashed command would block every later one; no
      // command holds it for more than a moment, so one older than 30s is stale.
      try {
        if (Date.now() - fs.statSync(mutex).mtimeMs > 30000) {
          fs.rmdirSync(mutex);
          continue;
        }
      } catch {
        continue;
      }
      if (Date.now() >= deadline) throw new LockError("Lease store busy at " + mutex + "; retry after the other lock command finishes.");
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 10);
    }
  }
  try {
    return action();
  } finally {
    fs.rmdirSync(mutex);
  }
}

// Posts from the running worktree's role to every other role among the
// targets. The running role is not messaged: it is the one reading the output.
// A message that cannot be posted is returned as a warning (#403): the lease
// is already freed, and a failed notice must not undo that.
function notify(where, targets, text) {
  const from = store.currentRole(where);
  if (!from) return [];
  const warnings = [];
  for (const role of new Set(targets.map((target) => target.role).filter(Boolean))) {
    if (role === from) continue;
    try {
      store.directPost(where, role, text);
    } catch (error) {
      if (!(error instanceof store.ChatError)) throw error;
      warnings.push("warning: could not tell " + role + " that " + text + ": " + error.message);
    }
  }
  return warnings;
}

// Every freed lease is printed, whether or not anyone was messaged (D4).
function reap(where) {
  const freed = [];
  const warnings = [];
  for (const lease of readLeases(where)) {
    if (Date.parse(lease.expires) > Date.now()) continue;
    const text = "lock " + lease.resource + " expired at " + lease.expires + " (held by " + lease.holder + ": " + lease.note + ")";
    fs.unlinkSync(path.join(lockDir(where), lease.resource + ".json"));
    freed.push(text);
    warnings.push(...notify(where, [lease, ...lease.waiters], text));
  }
  return { freed, warnings };
}

function acquire(where, resource, expires, note) {
  const who = identity(where);
  const file = path.join(lockDir(where), resource + ".json");
  const existing = readLeases(where).find((lease) => lease.resource === resource);
  if (existing) {
    if (existing.holder !== who.holder) {
      if (!existing.waiters.some((waiter) => waiter.holder === who.holder)) {
        existing.waiters.push(who);
        store.writeJsonAtomic(where, file, existing);
      }
      throw new LockError(describe(existing));
    }
    const renewed = { ...existing, expires, note };
    store.writeJsonAtomic(where, file, renewed);
    return renewed;
  }
  const lease = { resource, ...who, acquired: store.isoLocal(new Date()), expires, note, waiters: [] };
  fs.writeFileSync(file, JSON.stringify(lease, null, 2) + "\n", { flag: "wx" });
  return lease;
}

function release(where, resource) {
  const lease = readLeases(where).find((row) => row.resource === resource);
  if (!lease) throw new LockError("No live lease for " + resource + ".");
  if (lease.holder !== identity(where).holder) throw new LockError("Only " + lease.holder + " can release " + resource + " (" + lease.worktree + ").");
  fs.unlinkSync(path.join(lockDir(where), resource + ".json"));
  return { lease, warnings: notify(where, lease.waiters, "lock " + resource + " released by " + lease.holder) };
}


// --- the branch lock (#526 D6-D10, D19, D22) ----------------------------------------------
//
// A lease kept as the ref refs/keel/lock/<branch> on the branch's remote. Every
// update is a commit whose parent is the lock commit this device observed,
// pushed without force, so git's own fast-forward rule lets exactly one of two
// devices acting on the same observation win. Exit 3 is "not authorized".

class LockRefused extends LockError {
  constructor(message, code = 1) {
    super(message);
    this.code = code;
  }
}

const LOCK_IDENTITY = {
  GIT_AUTHOR_NAME: "keel lock", GIT_AUTHOR_EMAIL: "keel-lock@localhost",
  GIT_COMMITTER_NAME: "keel lock", GIT_COMMITTER_EMAIL: "keel-lock@localhost",
};

function run(cwd, args, extraEnv = {}) {
  const env = { ...process.env, GIT_OPTIONAL_LOCKS: "0", GIT_TERMINAL_PROMPT: "0", ...extraEnv };
  if (!env.GIT_SSH_COMMAND) env.GIT_SSH_COMMAND = "ssh -o BatchMode=yes";
  const result = spawnSync("git", args, { cwd, encoding: "utf8", env, timeout: LOOKUP_TIMEOUT_MS, maxBuffer: 16 * 1024 * 1024 });
  return {
    ok: !result.error && result.status === 0,
    out: String(result.stdout || "").trim(),
    err: result.error ? (result.error.code === "ETIMEDOUT" ? `timed out after ${LOOKUP_TIMEOUT_MS / 1000} s` : result.error.message)
      : String(result.stderr || "").trim(),
  };
}

// This machine's name in a lock (D22): written once to the chat store, or named
// by KEEL_DEVICE where several devices share one store.
function deviceId(where) {
  if (process.env.KEEL_DEVICE && /^[A-Za-z0-9._-]{1,64}$/.test(process.env.KEEL_DEVICE)) return process.env.KEEL_DEVICE;
  const file = path.join(where.root, "device.json");
  try {
    const saved = JSON.parse(fs.readFileSync(file, "utf8"));
    if (saved && typeof saved.id === "string" && saved.id) return saved.id;
  } catch {
    // first use on this machine
  }
  const host = (os.hostname().split(".")[0] || "host").toLowerCase().replace(/[^a-z0-9-]/g, "-").slice(0, 24) || "host";
  const id = `${host}-${crypto.randomBytes(4).toString("hex")}`;
  fs.mkdirSync(where.root, { recursive: true });
  try {
    fs.writeFileSync(file, `${JSON.stringify({ id, host: os.hostname() }, null, 2)}\n`, { flag: "wx" });
    return id;
  } catch (error) {
    if (error.code !== "EEXIST") throw error;
    return JSON.parse(fs.readFileSync(file, "utf8")).id;
  }
}

function checkBranch(cwd, branch) {
  if (!branch || !run(cwd, ["check-ref-format", "--branch", branch]).ok) {
    throw new LockRefused(`Invalid branch ${JSON.stringify(branch)}.`, 2);
  }
}

function branchRemote(cwd, branch) {
  const configured = run(cwd, ["config", "--get", `branch.${branch}.remote`]);
  return configured.ok && configured.out && configured.out !== "." ? configured.out : "origin";
}

function parseLock(cwd, sha) {
  if (!sha) return null;
  const body = run(cwd, ["log", "-1", "--format=%B", sha]);
  if (!body.ok) return null;
  const fields = {};
  for (const line of body.out.split("\n")) {
    const match = line.match(/^([A-Za-z-]+): (.*)$/);
    if (match && !(match[1] in fields)) fields[match[1]] = match[2];
  }
  return {
    sha, state: fields["keel-lock"] || "unknown", holder: fields.Holder || "unknown", device: fields.Device || null,
    seq: Number(fields.Seq) || 0, expires: fields.Expires || null, head: fields.Head && fields.Head !== "none" ? fields.Head : null,
    reason: fields.Reason || null, note: fields.Note || null, tookOver: fields["Took-over"] || null, broke: fields.Broke || null,
  };
}

// One ls-remote for the branch and its lock, then a fetch of whatever the
// local objects lack, into refs/keel/lock/<b> and refs/remotes/<r>/<b>.
function observe(cwd, remote, branch) {
  const asked = run(cwd, ["ls-remote", remote, `refs/heads/${branch}`, `${LOCK_PREFIX}${branch}`]);
  if (!asked.ok) throw new LockRefused(`cannot verify ${remote}: ${asked.err.split("\n").pop()}`);
  let lockSha = null;
  let branchSha = null;
  for (const line of asked.out.split("\n").filter(Boolean)) {
    const [sha, ref] = line.split("\t");
    if (ref === `${LOCK_PREFIX}${branch}`) lockSha = sha;
    if (ref === `refs/heads/${branch}`) branchSha = sha;
  }
  const specs = [];
  if (lockSha) specs.push(`+${LOCK_PREFIX}${branch}:${LOCK_PREFIX}${branch}`);
  if (branchSha) specs.push(`+refs/heads/${branch}:refs/remotes/${remote}/${branch}`);
  if (specs.length) {
    const fetched = run(cwd, ["fetch", "--no-tags", "-q", remote, ...specs]);
    if (!fetched.ok) throw new LockRefused(`cannot fetch ${remote}: ${fetched.err.split("\n").pop()}`);
  } else {
    run(cwd, ["update-ref", "-d", `${LOCK_PREFIX}${branch}`]);
  }
  return { lockSha, branchSha, lock: parseLock(cwd, lockSha) };
}

function isAncestor(cwd, older, newer) {
  return run(cwd, ["merge-base", "--is-ancestor", older, newer]).ok;
}

function contains(cwd, tip, sha) {
  return !sha || (Boolean(tip) && (tip === sha || isAncestor(cwd, sha, tip)));
}

function short(sha) {
  return sha ? sha.slice(0, 8) : "none";
}

function describeBranchLock(branch, lock) {
  return `${branch}: ${lock.state} by ${lock.holder}, expires ${lock.expires || "unknown"}, head ${short(lock.head)}`;
}

function liveFor(lock, now, grace) {
  const expires = Date.parse(lock.expires || "");
  return Number.isFinite(expires) && now <= expires + grace;
}

function authorization(cwd) {
  const config = require("./config");
  const read = config.readStandingAuthorization(cwd);
  return { declared: read.declared || [], globs: read.pushGlobs || [], protectedGlobs: read.protectedPushes || [] };
}

function requireDeviceSync(cwd) {
  if (!authorization(cwd).declared.includes("device-sync")) {
    throw new LockRefused("pushing a branch lock needs `device-sync` in keel/config.yaml authorize:; nothing was pushed.", 3);
  }
}

function ttlSeconds(cwd, duration) {
  if (duration) {
    const match = String(duration).match(/^(\d+)([smhd])$/);
    if (!match || Number(match[1]) <= 0) throw new LockRefused(`Invalid --for duration ${JSON.stringify(duration)}: use a positive integer followed by s, m, h or d.`, 2);
    return Number(match[1]) * { s: 1, m: 60, h: 3600, d: 86400 }[match[2]];
  }
  return require("./config").readSyncDeclaration(cwd).ttlSeconds;
}

function lockMessage(fields) {
  const lines = [`keel-lock: ${fields.state}`, "", `Holder: ${fields.holder}`, `Device: ${fields.device}`, `Seq: ${fields.seq}`,
    `Expires: ${fields.expires}`, `Head: ${fields.head || "none"}`];
  if (fields.reason) lines.push(`Reason: ${fields.reason}`);
  if (fields.note) lines.push(`Note: ${fields.note}`);
  if (fields.tookOver) lines.push(`Took-over: ${fields.tookOver}`);
  if (fields.broke) lines.push(`Broke: ${fields.broke}`);
  return `${lines.join("\n")}\n`;
}

function pushLock(cwd, remote, branch, parent, fields) {
  const empty = run(cwd, ["hash-object", "-t", "tree", "/dev/null"]).out;
  const args = ["commit-tree", empty, "-m", lockMessage(fields)];
  if (parent) args.push("-p", parent);
  const commit = run(cwd, args, LOCK_IDENTITY);
  if (!commit.ok) throw new LockError(`cannot write the lock commit: ${commit.err}`);
  const pushed = run(cwd, ["push", "--porcelain", remote, `${commit.out}:${LOCK_PREFIX}${branch}`]);
  if (!pushed.ok) {
    if (/rejected|non-fast-forward|fetch first|stale/i.test(pushed.out + pushed.err)) {
      const now = observe(cwd, remote, branch);
      throw new LockRefused(`the lock of ${branch} was taken by another device first${now.lock ? `: ${describeBranchLock(branch, now.lock)}` : ""}; nothing was changed.`);
    }
    throw new LockRefused(`cannot push the lock of ${branch} to ${remote}: ${(pushed.err || pushed.out).split("\n").pop()}`);
  }
  run(cwd, ["update-ref", `${LOCK_PREFIX}${branch}`, commit.out]);
  return commit.out;
}

function waitersFile(where, branch) {
  return path.join(lockDir(where), "branches", `${encodeURIComponent(branch)}.json`);
}

function readWaiters(where, branch) {
  try {
    const rows = JSON.parse(fs.readFileSync(waitersFile(where, branch), "utf8"));
    return Array.isArray(rows) ? rows : [];
  } catch {
    return [];
  }
}

function writeWaiters(where, branch, rows) {
  fs.mkdirSync(path.dirname(waitersFile(where, branch)), { recursive: true });
  if (rows.length) store.writeJsonAtomic(where, waitersFile(where, branch), rows);
  else fs.rmSync(waitersFile(where, branch), { force: true });
}

function roleOf(holder) {
  const name = String(holder || "").split("@")[0];
  return name && !name.startsWith("worktree:") && new RegExp(store.NAME_PATTERN_TEXT).test(name) ? name : null;
}

// Pushes the branch itself, fast-forward only, where `push` allows it and it
// is not push-protected (D10). The repository's hooks run; a failure is said.
function pushBranch(cwd, remote, branch) {
  const { declared, globs, protectedGlobs } = authorization(cwd);
  const { globRegExp } = require("./branches");
  if (protectedGlobs.some((glob) => globRegExp(String(glob).split("@")[0]).test(branch))) {
    return { pushed: false, text: `${branch} is push-protected, which needs a person's answer; not pushed.` };
  }
  const cover = declared.includes("push") ? "push" : (globs.find((glob) => globRegExp(glob).test(branch)) ? `push:${globs.find((glob) => globRegExp(glob).test(branch))}` : null);
  if (!cover) {
    const named = globs.length ? globs.map((glob) => `push:${glob}`).join(", ") : "no push entry";
    return { pushed: false, text: `${branch} is not covered by ${named}; not pushed. Declare push or push:${branch} to let Keel push it.` };
  }
  const pushed = run(cwd, ["push", remote, `refs/heads/${branch}:refs/heads/${branch}`]);
  if (!pushed.ok) return { pushed: false, text: `pushing ${branch} failed: ${pushed.err || pushed.out}` };
  return { pushed: true, text: `pushed ${branch} to ${remote} (${cover}).` };
}

function acquireBranch(where, cwd, branch, options) {
  checkBranch(cwd, branch);
  if (options.break !== undefined && options.break !== null && !String(options.break).trim()) {
    throw new LockRefused("--break needs a reason.", 2);
  }
  requireDeviceSync(cwd);
  const seconds = ttlSeconds(cwd, options.duration);
  const device = deviceId(where);
  const holder = `${identity(where).holder}@${device}`;
  const remote = branchRemote(cwd, branch);
  const lines = [];
  if (options.renewOnly) {
    const seen = observe(cwd, remote, branch);
    const lock = seen.lock;
    if (!lock || lock.state !== "held" || lock.device !== device || !liveFor(lock, Date.now(), 0)) {
      throw new LockRefused(`cannot renew ${branch}: ${lock ? describeBranchLock(branch, lock) : "no lock"}; lease left to lapse.`);
    }
  }
  if (options.push) {
    const local = run(cwd, ["rev-parse", "--verify", "--quiet", `refs/heads/${branch}`]).out;
    if (local) {
      const pushed = pushBranch(cwd, remote, branch);
      if (options.renewOnly && !pushed.pushed && pushed.text.includes("failed:")) throw new LockRefused(pushed.text);
      lines.push(pushed.text);
    }
  }
  const seen = observe(cwd, remote, branch);
  const tip = run(cwd, ["rev-parse", "--verify", "--quiet", `refs/heads/${branch}`]).out || null;
  const lock = seen.lock;
  const now = Date.now();
  const ours = lock && lock.state === "held" && lock.device === device;
  if (options.renewOnly && (!ours || !liveFor(lock, now, 0))) {
    throw new LockRefused(`cannot renew ${branch}: ${lock ? describeBranchLock(branch, lock) : "no lock"}; lease left to lapse.`);
  }
  const fields = {
    state: "held", holder, device, seq: (lock ? lock.seq : 0) + 1,
    expires: new Date(now + seconds * 1000).toISOString(), head: seen.branchSha,
    reason: options.note || `work on ${branch}`,
  };
  const others = [];
  if (!ours) {
    if (lock && lock.state === "held" && liveFor(lock, now, GRACE_MS)) {
      if (!options.break) {
        const waiters = readWaiters(where, branch);
        const me = identity(where);
        if (!waiters.some((row) => row.holder === holder)) writeWaiters(where, branch, [...waiters, { holder, role: me.role, worktree: me.worktree }]);
        const told = notify(where, [{ role: roleOf(lock.holder) }], `${holder} waits for branch ${branch}`);
        throw new LockRefused(`branch ${branch} is held by ${lock.holder}, expires ${lock.expires}, head ${short(lock.head)}; `
          + `you are recorded as a waiter. Take it only with --break "<reason>".${told.length ? ` ${told.join(" ")}` : ""}`);
      }
      fields.broke = `${lock.holder} — ${String(options.break).trim()}`;
    } else if (lock && lock.state === "held") {
      fields.tookOver = lock.holder;
      others.push(`took over ${branch} from ${lock.holder}, whose lease expired ${lock.expires}: it last recorded head ${short(lock.head)}; `
        + `the remote ${branch} is at ${short(seen.branchSha)}.`);
    }
    if (!tip) throw new LockRefused(`there is no local branch ${branch}; fetch it and check it out, then acquire.`);
    const needed = [lock && lock.state === "released" ? lock.head : null, seen.branchSha].filter(Boolean);
    const missing = needed.find((sha) => !contains(cwd, tip, sha));
    if (missing) {
      throw new LockRefused(`local ${branch} at ${short(tip)} does not contain ${short(missing)}, where the previous holder finished; `
        + `fetch and integrate first (git pull --ff-only ${remote} ${branch}).`);
    }
  }
  let sha;
  try {
    sha = pushLock(cwd, remote, branch, seen.lockSha, fields);
  } catch (error) {
    // What was already said about the branch push (a failing hook's output
    // included) is said once, ahead of why the lock push failed too.
    if (error instanceof LockRefused && lines.length) error.message = `${lines.join("\n")}\n${error.message}`;
    throw error;
  }
  writeWaiters(where, branch, readWaiters(where, branch).filter((row) => row.holder !== holder));
  const result = { branch, remote, lock: { ...fields, sha }, renewed: Boolean(ours), messages: [...lines, ...others] };
  if (lock && !ours) {
    const text = fields.broke ? `branch ${branch} lock broken by ${holder}: ${fields.broke}`
      : fields.tookOver ? `branch ${branch} taken over by ${holder} from ${lock.holder}; last head ${short(lock.head)}, remote ${short(seen.branchSha)}`
        : `branch ${branch} acquired by ${holder}`;
    result.warnings = notify(where, [{ role: roleOf(lock.holder) }], text);
  }
  return result;
}

function releaseBranch(where, cwd, branch, options = {}) {
  checkBranch(cwd, branch);
  requireDeviceSync(cwd);
  const device = deviceId(where);
  const remote = branchRemote(cwd, branch);
  const seen = observe(cwd, remote, branch);
  const lock = seen.lock;
  if (!lock || lock.state !== "held" || lock.device !== device) {
    throw new LockRefused(`branch ${branch} is not held by this device${lock ? `: ${describeBranchLock(branch, lock)}` : ": it has no lock"}; nothing was released.`);
  }
  if (Date.now() > Date.parse(lock.expires || "")) {
    throw new LockRefused(`this device's lease on ${branch} expired at ${lock.expires}; acquire it again before releasing.`);
  }
  const tip = run(cwd, ["rev-parse", "--verify", "--quiet", `refs/heads/${branch}`]).out || null;
  const checked = require("./worktrees").listWorktrees(cwd).find((row) => row.branch === branch && fs.existsSync(row.path));
  if (checked) {
    const status = run(checked.path, ["status", "--porcelain=v1", "--untracked-files=all"]);
    const dirty = status.out.split("\n").filter(Boolean).map((line) => line.slice(3));
    if (dirty.length) throw new LockRefused(`${checked.path} has uncommitted or untracked paths: ${dirty.join(", ")}; commit and push them first.`);
  }
  if (tip && !(seen.branchSha && contains(cwd, seen.branchSha, tip))) {
    throw new LockRefused(`local ${branch} at ${short(tip)} is not on the remote (remote ${short(seen.branchSha)}); run git push ${remote} ${branch} first.`);
  }
  const fields = {
    state: "released", holder: lock.holder, device, seq: lock.seq + 1, expires: new Date().toISOString(),
    head: seen.branchSha, reason: lock.reason, note: options.notePath || null,
  };
  const sha = pushLock(cwd, remote, branch, seen.lockSha, fields);
  const waiters = readWaiters(where, branch);
  writeWaiters(where, branch, []);
  return { branch, remote, lock: { ...fields, sha }, warnings: notify(where, waiters, `branch ${branch} released by ${lock.holder} at head ${short(seen.branchSha)}`) };
}

// The branch locks as last fetched, with the waiters this machine recorded.
function branchLocks(where, cwd) {
  const out = run(cwd, ["for-each-ref", "--format=%(refname)%00%(objectname)", LOCK_PREFIX]).out;
  return out.split("\n").filter(Boolean).map((line) => {
    const [ref, sha] = line.split("\0");
    const branch = ref.slice(LOCK_PREFIX.length);
    return { branch, ...parseLock(cwd, sha), waiters: readWaiters(where, branch) };
  });
}


// Automatic renewal never acquires a free, released, expired or foreign lock.
// Failed attempts are throttled too, so an unreachable remote cannot stall every prompt.
function renewHeld(where, { prompt = false, now = Date.now() } = {}) {
  const config = require("./config").readSyncDeclaration(where.worktree);
  if (!config.lock || !authorization(where.worktree).declared.includes("device-sync")) return [];
  const device = existingDeviceId(where);
  if (!device) return [];
  const file = path.join(where.root, "lock-renewals.json");
  const state = store.readJsonFile(file);
  const worktrees = prompt ? [{ path: where.worktree, branch: run(where.worktree, ["symbolic-ref", "--quiet", "--short", "HEAD"]).out }]
    : require("./worktrees").listWorktrees(where.worktree);
  const messages = [];
  for (const lock of branchLocks(where, where.worktree)) {
    if (lock.state !== "held" || lock.device !== device || !liveFor(lock, now, 0)) continue;
    const worktree = worktrees.find((row) => row.branch === lock.branch && fs.existsSync(row.path));
    if (!worktree) continue;
    const own = store.requireLocation(worktree.path);
    const declaration = require("./config").readSyncDeclaration(worktree.path);
    if (!declaration.lock || !authorization(worktree.path).declared.includes("device-sync")) continue;
    const before = state[lock.branch] || {};
    const renewedAt = Date.parse(lock.expires) - declaration.ttlSeconds * 1000;
    if (prompt && now - Math.max(renewedAt, before.at || 0) <= declaration.ttlSeconds * 1000 / 3) continue;
    let text;
    try {
      const result = acquireBranch(own, worktree.path, lock.branch, { renewOnly: true, push: !prompt });
      text = result.messages.join("\n");
      state[lock.branch] = { at: now };
    } catch (error) {
      text = error.message;
      state[lock.branch] = { at: now, error: text };
    }
    if (!prompt && text && text !== before.error) messages.push(text);
  }
  store.writeJsonAtomic(where, file, state);
  return messages;
}

// The completion gates' read (#526 D12): one ls-remote for the branch and its
// lock, no fetch, no write. Returns problems as { code, message } and warnings.
// The device id is read, never created: a gate writes nothing.
function existingDeviceId(where) {
  if (process.env.KEEL_DEVICE && /^[A-Za-z0-9._-]{1,64}$/.test(process.env.KEEL_DEVICE)) return process.env.KEEL_DEVICE;
  try {
    return JSON.parse(fs.readFileSync(path.join(where.root, "device.json"), "utf8")).id || null;
  } catch {
    return null;
  }
}

function gateSyncCheck(repo, stage) {
  const problems = [];
  const warnings = [];
  const add = (code, message) => problems.push({ code, message });
  const remotes = run(repo, ["remote"]).out.split("\n").filter(Boolean);
  if (!remotes.length) {
    warnings.push("sync: lock is declared but this repository has no remote, so nothing was checked.");
    return { problems, warnings };
  }
  const branch = run(repo, ["symbolic-ref", "--quiet", "--short", "HEAD"]).out;
  if (!branch) {
    add("sync-detached", "HEAD is detached, so no branch lock can cover this work; check out the branch and `keel lock acquire --branch <b>`.");
    return { problems, warnings };
  }
  const head = run(repo, ["rev-parse", "HEAD"]).out;
  const remote = branchRemote(repo, branch);
  const asked = run(repo, ["ls-remote", remote, `refs/heads/${branch}`, `${LOCK_PREFIX}${branch}`]);
  if (!asked.ok) {
    add("sync-cannot-verify", `cannot verify ${remote}: ${asked.err.split("\n").pop()}; the branch lock and pushed state are unproven, so this gate does not pass.`);
    return { problems, warnings };
  }
  let lockSha = null;
  let remoteSha = null;
  for (const line of asked.out.split("\n").filter(Boolean)) {
    const [sha, ref] = line.split("\t");
    if (ref === `${LOCK_PREFIX}${branch}`) lockSha = sha;
    if (ref === `refs/heads/${branch}`) remoteSha = sha;
  }
  let where = null;
  try {
    where = store.locate(repo);
  } catch {
    where = null;
  }
  const device = where ? existingDeviceId(where) : null;
  const local = run(repo, ["rev-parse", "--verify", "--quiet", `${LOCK_PREFIX}${branch}`]).out || null;
  const acquire = `\`keel lock acquire --branch ${branch}\``;
  if (!lockSha) {
    add("sync-no-lock", `branch ${branch} has no lock on ${remote}; run ${acquire} first.`);
  } else if (lockSha !== local) {
    const now = parseLock(repo, lockSha);
    add("sync-lock-not-held", `the lock of ${branch} on ${remote} is ${short(lockSha)}${now ? ` (${now.state} by ${now.holder})` : ""}, not the one this device last pushed (${short(local)}); `
      + `another device has it. Run \`keel shift resume\` or ${acquire}.`);
  } else {
    const lock = parseLock(repo, lockSha);
    if (!lock || lock.state !== "held" || !device || lock.device !== device) {
      add("sync-lock-not-held", `branch ${branch} is ${lock ? `${lock.state} by ${lock.holder}` : "locked"}, not held by this device; run ${acquire} or \`keel shift resume\`.`);
    } else if (Date.now() > Date.parse(lock.expires || "")) {
      add("sync-lease-expired", `this device's lease on ${branch} expired at ${lock.expires}; run ${acquire} to renew it.`);
    }
  }
  if (!remoteSha) {
    add("sync-unpushed", `branch ${branch} is not on ${remote}; run git push -u ${remote} ${branch}.`);
  } else if (remoteSha !== head) {
    if (!run(repo, ["cat-file", "-e", `${remoteSha}^{commit}`]).ok) {
      add("sync-remote-unknown", `${remote}/${branch} is at ${short(remoteSha)}, a commit this clone does not have, while HEAD is ${short(head)}; run git fetch ${remote} and integrate.`);
    } else if (isAncestor(repo, remoteSha, head)) {
      const count = run(repo, ["rev-list", "--count", `${remoteSha}..${head}`]).out;
      add("sync-unpushed", `HEAD ${short(head)} has ${count} commit(s) ${remote} lacks (remote ${short(remoteSha)}); run git push ${remote} ${branch}.`);
    } else if (isAncestor(repo, head, remoteSha)) {
      if (stage === "change-close") add("sync-not-at-remote", `${remote}/${branch} is at ${short(remoteSha)}, ahead of HEAD ${short(head)}; pull before closing.`);
    } else {
      add("sync-remote-diverged", `HEAD ${short(head)} and ${remote}/${branch} ${short(remoteSha)} have diverged; integrate them first.`);
    }
  }
  if (stage === "change-close") {
    const status = run(repo, ["status", "--porcelain=v1", "--untracked-files=all"]).out;
    const dirty = status.split("\n").filter(Boolean).map((line) => line.slice(3));
    if (dirty.length) add("sync-uncommitted", `uncommitted or untracked paths are not on ${remote}: ${dirty.join(", ")}.`);
  }
  return { problems, warnings };
}

function runLock(argv) {
  const options = { repo: process.cwd(), json: false, positionals: [], duration: null, note: null, branch: null, break: null, push: false };
  try {
    for (let index = 0; index < argv.length; index += 1) {
      const arg = argv[index];
      if (arg === "--json") options.json = true;
      else if (arg === "--help" || arg === "-h") {
        process.stdout.write(USAGE + "\n");
        return 0;
      } else if (arg === "--push") options.push = true;
      else if (arg === "--break") {
        const value = argv[index + 1];
        if (!value || value.startsWith("--")) throw new LockRefused("--break needs a reason.", 2);
        options.break = value;
        index += 1;
      } else if (["--repo", "--for", "--note", "--branch"].includes(arg)) {
        const value = argv[++index];
        if (!value || value.startsWith("--")) throw new LockError(arg + " needs a value.");
        options[{ "--repo": "repo", "--for": "duration", "--note": "note", "--branch": "branch" }[arg]] = value;
      } else if (arg.startsWith("-")) throw new LockError("Unknown option " + arg + ".");
      else options.positionals.push(arg);
    }
    const [action, resource, ...extra] = options.positionals;
    if (!["acquire", "release", "list"].includes(action)) {
      process.stderr.write((action ? "keel lock: unknown action " + action + "\n" : "") + USAGE + "\n");
      return 2;
    }
    const where = store.requireLocation(options.repo);
    if (options.branch !== null) return runBranchLock(where, action, resource, extra, options);
    if (options.break !== null || options.push) throw new LockError("--break and --push are only valid with --branch.");
    return withMutation(where, () => {
      const reaped = reap(where);
      for (const text of reaped.freed) {
        // Keep --json parseable, including when a command is later refused.
        (options.json ? process.stderr : process.stdout).write(text + "\n");
      }
      for (const warning of reaped.warnings) process.stderr.write("keel lock: " + warning + "\n");
      if (extra.length || (action === "list" && resource)) throw new LockError("Unexpected argument for " + action + ".");
      if (action !== "acquire" && (options.duration !== null || options.note !== null)) throw new LockError("--for and --note are only valid for acquire.");
      const out = (data, text) => process.stdout.write((options.json ? JSON.stringify(data, null, 2) : text) + "\n");
      if (action === "list") {
        const leases = liveLeases(where);
        const locks = branchLocks(where, where.worktree);
        const text = [leases.length ? leases.map(describe).join("\n") : "No live leases."];
        if (locks.length) {
          text.push("Branch locks, as last fetched:");
          for (const lock of locks) text.push(describeBranchLock(lock.branch, lock) + (lock.waiters.length ? `; waiting here: ${lock.waiters.map((w) => w.holder).join(", ")}` : ""));
        }
        out({ leases, branchLocks: locks }, text.join("\n"));
      } else {
        checkResource(resource);
        if (action === "release") {
          const { lease, warnings } = release(where, resource);
          out({ released: lease }, "lock " + resource + " released by " + lease.holder);
          for (const warning of warnings) process.stderr.write("keel lock: " + warning + "\n");
        } else {
          if (options.duration === null) throw new LockError("acquire requires --for <duration>.");
          if (!options.note || !options.note.trim()) throw new LockError("acquire requires a non-empty --note <why>.");
          const expires = expiry(options.duration, new Date());
          const lease = acquire(where, resource, expires, options.note.trim());
          const notice = "The lease enforces nothing on Git or the filesystem.";
          out({ lease, notice }, describe(lease) + "\n" + notice);
        }
      }
      return 0;
    });
  } catch (error) {
    if (error instanceof LockError || error instanceof store.ChatError) {
      process.stderr.write("keel lock: " + error.message + "\n");
      return error instanceof LockRefused ? error.code : 1;
    }
    throw error;
  }
}

function runBranchLock(where, action, resource, extra, options) {
  if (resource !== undefined || extra.length) throw new LockRefused(`--branch names the lock; ${action} takes no resource then.`, 2);
  if (!["acquire", "release"].includes(action)) throw new LockRefused(`--branch is for acquire and release; \`keel lock list\` shows branch locks.`, 2);
  const cwd = where.worktree;
  const result = action === "acquire" ? acquireBranch(where, cwd, options.branch, options) : releaseBranch(where, cwd, options.branch);
  const text = [
    action === "acquire" ? `${result.renewed ? "renewed" : "acquired"} branch lock ${describeBranchLock(result.branch, { ...result.lock, state: "held" })}`
      : `released branch lock ${result.branch} at head ${short(result.lock.head)}`,
    ...(result.messages || []),
  ];
  process.stdout.write(`${options.json ? JSON.stringify(result, null, 2) : text.join("\n")}\n`);
  for (const warning of result.warnings || []) process.stderr.write("keel lock: " + warning + "\n");
  return 0;
}

module.exports = { renewHeld, gateSyncCheck, existingDeviceId, roleOf, LockError, liveLeases, describe, runLock, acquireBranch, releaseBranch, branchLocks, deviceId, parseLock, observe, describeBranchLock, liveFor, GRACE_MS, LOCK_PREFIX };

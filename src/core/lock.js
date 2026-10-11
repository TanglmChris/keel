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
  "keel lock list [--json]                                   live leases",
  "Options: --repo <path>, --json. See docs/resource-lock.md.",
  "A lease enforces nothing on Git or the filesystem.",
].join("\n");

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
function notify(where, targets, text) {
  const from = store.currentRole(where);
  if (!from) return;
  for (const role of new Set(targets.map((target) => target.role).filter(Boolean))) {
    if (role !== from) store.directPost(where, role, text);
  }
}

// Every freed lease is printed, whether or not anyone was messaged (D4).
function reap(where) {
  const freed = [];
  for (const lease of readLeases(where)) {
    if (Date.parse(lease.expires) > Date.now()) continue;
    const text = "lock " + lease.resource + " expired at " + lease.expires + " (held by " + lease.holder + ": " + lease.note + ")";
    notify(where, [lease, ...lease.waiters], text);
    freed.push(text);
    fs.unlinkSync(path.join(lockDir(where), lease.resource + ".json"));
  }
  return freed;
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
  notify(where, lease.waiters, "lock " + resource + " released by " + lease.holder);
  fs.unlinkSync(path.join(lockDir(where), resource + ".json"));
  return lease;
}

function runLock(argv) {
  const options = { repo: process.cwd(), json: false, positionals: [], duration: null, note: null };
  try {
    for (let index = 0; index < argv.length; index += 1) {
      const arg = argv[index];
      if (arg === "--json") options.json = true;
      else if (arg === "--help" || arg === "-h") {
        process.stdout.write(USAGE + "\n");
        return 0;
      } else if (["--repo", "--for", "--note"].includes(arg)) {
        const value = argv[++index];
        if (!value || value.startsWith("--")) throw new LockError(arg + " needs a value.");
        options[{ "--repo": "repo", "--for": "duration", "--note": "note" }[arg]] = value;
      } else if (arg.startsWith("-")) throw new LockError("Unknown option " + arg + ".");
      else options.positionals.push(arg);
    }
    const [action, resource, ...extra] = options.positionals;
    if (!["acquire", "release", "list"].includes(action)) {
      process.stderr.write((action ? "keel lock: unknown action " + action + "\n" : "") + USAGE + "\n");
      return 2;
    }
    const where = store.requireLocation(options.repo);
    return withMutation(where, () => {
      for (const text of reap(where)) {
        // Keep --json parseable, including when a command is later refused.
        (options.json ? process.stderr : process.stdout).write(text + "\n");
      }
      if (extra.length || (action === "list" && resource)) throw new LockError("Unexpected argument for " + action + ".");
      if (action !== "acquire" && (options.duration !== null || options.note !== null)) throw new LockError("--for and --note are only valid for acquire.");
      const out = (data, text) => process.stdout.write((options.json ? JSON.stringify(data, null, 2) : text) + "\n");
      if (action === "list") {
        const leases = liveLeases(where);
        out({ leases }, leases.length ? leases.map(describe).join("\n") : "No live leases.");
      } else {
        checkResource(resource);
        if (action === "release") {
          const lease = release(where, resource);
          out({ released: lease }, "lock " + resource + " released by " + lease.holder);
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
      return 1;
    }
    throw error;
  }
}

module.exports = { LockError, liveLeases, describe, runLock };

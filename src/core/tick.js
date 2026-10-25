"use strict";

// `keel tick` (the owner's CLI waker, 2026-10-19; #356): one model-free step a
// host scheduler such as launchd calls every few minutes. It runs the patrol
// only once the last run's recommended `next_at` has passed. The recurrence is
// the host's: Keel registers nothing, and `keel tick task` prints the job.
const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");
const store = require("./chat/store");
const { stableNode, launchdPath } = require("./launchd");

const USAGE = "keel tick [--repo <path>] [--json]   one model-free step: run the patrol when it is due\n"
  + "       keel tick task [--json] [--repo <path>]   print the launchd job that calls it";
const INTERVAL_SECONDS = 300;
const KEEL = path.resolve(__dirname, "..", "..", "bin", "keel.js");

class TickError extends Error {}

function stateFile(where) {
  return path.join(where.root, "tick", "state.json");
}

function readState(where) {
  const state = store.readJsonFile(stateFile(where));
  return state && typeof state === "object" ? state : {};
}

// Each declared patrol runs in the worktree bound to its role, whichever
// worktree called (#434 D7); a list's first role is the one a bare
// `patrolWorktree` answers for.
function patrolWorktrees(where) {
  const all = require("./config").readPatrolDeclarations(where.worktree);
  if (!all.declarations.length) {
    return [{ declaration: null, worktree: null, why: all.messages.join(" ") || "keel/config.yaml declares no `patrol:` with role and every." }];
  }
  const roles = Object.entries(store.readJsonFile(path.join(where.root, "roles.json")));
  return all.declarations.map((declaration) => {
    const bound = roles.filter(([, role]) => role === declaration.role).map(([worktree]) => worktree).sort();
    if (!bound.length) {
      return { declaration, worktree: null, why: `No worktree is bound to role ${declaration.role}; bind one with \`keel chat role --set ${declaration.role}\` there first.` };
    }
    return { declaration, worktree: bound[0], why: null };
  });
}

// Free space on a worktree's filesystem in GiB, as `df -g` reports it (#456 D1).
function freeDiskGb(dir) {
  try {
    const stats = fs.statfsSync(dir);
    return { gb: Math.floor((Number(stats.bavail) * Number(stats.bsize)) / 2 ** 30), error: null };
  } catch (error) {
    return { gb: null, error: error.message };
  }
}

const QUOTA_MAX_AGE_MS = 6 * 3600 * 1000;

function readQuota(where, declared, now) {
  if (!declared) return { state: "unchecked", percent: null, text: "quota is not checked: no `patrol:` item declares quota_file" };
  const file = path.resolve(where.worktree, declared.replace(/^~(?=\/|$)/, os.homedir()));
  let stat;
  let body;
  try {
    stat = fs.statSync(file);
    body = fs.readFileSync(file, "utf8");
  } catch (error) {
    return { state: "unreadable", percent: null, text: `quota file ${file} cannot be read (${error.code || error.message}), so quota is not checked` };
  }
  if (now.getTime() - stat.mtimeMs > QUOTA_MAX_AGE_MS) {
    return { state: "stale", percent: null, text: `quota file ${file} is stale, last written ${store.isoLocal(stat.mtime)}, so quota is not checked` };
  }
  const number = body.match(/\d+(?:\.\d+)?/);
  if (!number) return { state: "unreadable", percent: null, text: `quota file ${file} holds no number, so quota is not checked` };
  const percent = Math.round(Number(number[0]));
  return { state: "read", percent, text: `quota is read from ${file} (${percent}%)` };
}

function patrolWorktree(where) {
  const all = patrolWorktrees(where);
  return all.find((found) => found.worktree) || all[0];
}

// Roles whose CLI session ended while a record addressed to them waits are
// resumed once per new record (#348 D4); a parked role is left alone.
function wakeEnded(where, state) {
  const notice = require("./chat/notice");
  const roles = [...new Set(Object.values(store.readJsonFile(path.join(where.root, "roles.json"))).filter(Boolean))].sort();
  state.woken = state.woken || {};
  const woken = [];
  for (const role of roles) {
    if (notice.parkOf(where, role)) continue;
    const entry = notice.asleep(where, role);
    if (!entry || !entry.cli) continue;
    const waiting = store.unread(where, role).filter((record) => store.wakes(record, role)).map((record) => record.id).sort();
    const newest = waiting[waiting.length - 1];
    if (!newest || (state.woken[role] && state.woken[role] >= newest)) continue;
    const resumed = notice.resumeCli(entry);
    // Marked woken only once it worked, the session is gone, or three tries
    // failed for this record (#408 D3); a newer record starts the count again.
    const before = (state.wake_attempts || {})[role];
    const count = before && before.record === newest ? before.count + 1 : 1;
    state.wake_attempts = { ...(state.wake_attempts || {}), [role]: { record: newest, count } };
    if (resumed.ok || resumed.removed || count >= 3) state.woken[role] = newest;
    woken.push({ role, session: entry.session, record: newest, ok: resumed.ok, output: resumed.output });
  }
  return woken;
}

function tick(where, now = new Date()) {
  const result = { patrol: null, woken: [] };
  const wakeState = readState(where);
  result.woken = wakeEnded(where, wakeState);
  result.handedOver = require("./shift").handOver(where);
  if (result.woken.length) {
    store.writeJsonAtomic(where, stateFile(where), { ...readState(where), woken: wakeState.woken, wake_attempts: wakeState.wake_attempts });
  }
  // A single mapping keeps its due time at `patrol`; a list keeps each role's
  // under `patrols`, the first falling back to `patrol` when it was a mapping.
  const all = patrolWorktrees(where);
  const listed = all.length > 1;
  const state = readState(where);
  // Repository-wide settings come from the first item declaring each (#456 D2);
  // every run gets them, and the patrol decides who reports (#434 D4).
  const declared = all.map((found) => found.declaration).filter(Boolean);
  const diskMinGb = (declared.find((d) => d.diskMinGb) || {}).diskMinGb || null;
  // Quota comes from a file the repository names, never from a command Keel
  // runs (#456 D3, D4); its state is said when it changes, not every tick.
  const quota = declared.length
    ? readQuota(where, (declared.find((d) => d.quotaFile) || {}).quotaFile || null, now)
    : { state: null, percent: null };
  if (quota.state && quota.state !== state.quota_state) {
    result.quota = quota;
    state.quota_state = quota.state;
    store.writeJsonAtomic(where, stateFile(where), state);
  }
  result.patrols = all.map((found) => {
    if (!found.worktree) return { role: found.declaration ? found.declaration.role : null, ran: false, why: found.why };
    const role = found.declaration.role;
    const own = listed ? ((state.patrols || {})[role] || (role === all[0].declaration.role ? state.patrol : null)) : state.patrol;
    const due = own && own.next_at ? Date.parse(own.next_at) : NaN;
    if (!Number.isNaN(due) && due > now.getTime()) {
      return { role, ran: false, why: `${listed ? `${role}'s ` : ""}patrol not due until ${own.next_at}`, next_at: own.next_at };
    }
    // The host task this replaces fetched first (F1); a failed fetch is reported
    // and the patrol still runs on the refs it has.
    const fetched = spawnSync("git", ["-C", found.worktree, "fetch", "-q", "origin"], { encoding: "utf8" });
    const fetchError = fetched.status === 0 ? null : String(fetched.stderr || fetched.error || "fetch failed").trim();
    const args = [KEEL, "patrol", "--repo", found.worktree, "--since-last", "--notify", "--json"];
    const disk = freeDiskGb(found.worktree);
    if (disk.gb !== null) args.push("--disk-free-gb", String(disk.gb));
    if (diskMinGb) args.push("--disk-min-gb", String(diskMinGb));
    if (quota.percent !== null) args.push("--quota", String(quota.percent));
    const ran = spawnSync(process.execPath, args, { cwd: found.worktree, encoding: "utf8" });
    let payload = {};
    try {
      payload = JSON.parse(ran.stdout);
    } catch {
      payload = {};
    }
    const next = payload.next_at || null;
    const record = { next_at: next, last_run: store.isoLocal(now), last_exit: ran.status };
    if (listed) state.patrols = { ...(state.patrols || {}), [role]: record };
    else state.patrol = record;
    store.writeJsonAtomic(where, stateFile(where), state);
    return {
      role, listed, ran: true, exit: ran.status, next_at: next, rule: payload.next_rule || null,
      fetchError, diskError: disk.error, error: ran.status === 1 ? String(ran.stderr || "").trim() : null,
    };
  });
  result.patrol = result.patrols[0];
  return result;
}

function render(result) {
  const woke = (result.woken || []).map((w) => `keel tick: ${w.ok ? "resumed" : "could not resume"} ${w.role}'s CLI session ${w.session} for ${w.record}`);
  const handed = (result.handedOver || []).map((h) => `keel tick: ${h.role}'s hand-off ${h.state}${h.new_session ? ` as session ${h.new_session}` : ""}${h.error ? `: ${h.error}` : ""}`);
  const quota = result.quota ? [`keel tick: ${result.quota.text}`] : [];
  return [...handed, ...woke, ...quota, ...(result.patrols || [result.patrol]).map(renderPatrol)].join("\n");
}

function renderPatrol(p) {
  if (!p.ran) return `keel tick: ${p.why}`;
  const lines = [`keel tick: ran ${p.listed ? `${p.role}'s` : "the"} patrol (exit ${p.exit})${p.next_at ? `; next ${p.next_at} (${p.rule})` : ""}`];
  if (p.fetchError) lines.push(`fetch failed: ${p.fetchError}`);
  if (p.diskError) lines.push(`free disk not measured: ${p.diskError}`);
  if (p.error) lines.push(`patrol failed: ${p.error}`);
  return lines.join("\n");
}

function xml(text) {
  return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function task(where) {
  const found = patrolWorktree(where);
  if (!found.worktree) throw new TickError(found.why);
  const label = `dev.keel.tick.${where.project.replace(/[^A-Za-z0-9.-]/g, "-")}`;
  const logs = path.join(where.root, "tick");
  const args = [stableNode(), KEEL, "tick", "--repo", found.worktree];
  const plist = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">',
    '<plist version="1.0">',
    "<dict>",
    "  <key>Label</key>", `  <string>${xml(label)}</string>`,
    "  <key>ProgramArguments</key>", "  <array>", ...args.map((arg) => `    <string>${xml(arg)}</string>`), "  </array>",
    "  <key>WorkingDirectory</key>", `  <string>${xml(found.worktree)}</string>`,
    "  <key>EnvironmentVariables</key>", "  <dict>", "    <key>PATH</key>", `    <string>${xml(launchdPath(process.env.PATH))}</string>`, "  </dict>",
    "  <key>StartInterval</key>", `  <integer>${INTERVAL_SECONDS}</integer>`,
    "  <key>StandardOutPath</key>", `  <string>${xml(path.join(logs, "tick.log"))}</string>`,
    "  <key>StandardErrorPath</key>", `  <string>${xml(path.join(logs, "tick.err"))}</string>`,
    "</dict>",
    "</plist>",
  ].join("\n");
  const target = path.join(os.homedir(), "Library", "LaunchAgents", `${label}.plist`);
  return { label, interval: INTERVAL_SECONDS, worktree: found.worktree, plist, target,
    install: [`mkdir -p ${path.dirname(target)} && cat > ${target} <<'PLIST'\n${plist}\nPLIST`, `launchctl bootstrap gui/${process.getuid ? process.getuid() : "<uid>"} ${target}`] };
}

function renderTask(job) {
  return [
    `launchd job for \`keel tick\` (label ${job.label}): it calls \`keel tick\` every ${job.interval} s, and the tick runs the patrol of the worktree ${job.worktree} when due. Keel creates nothing: install it with the two commands below.`,
    "",
    job.plist,
    "",
    "Install:",
    ...job.install,
    "",
    `Remove: launchctl bootout gui/${process.getuid ? process.getuid() : "<uid>"}/${job.label} && rm ${job.target}`,
  ].join("\n");
}

function runTick(argv) {
  try {
    const options = { repo: process.cwd(), json: false };
    const rest = [];
    for (let index = 0; index < argv.length; index += 1) {
      const arg = argv[index];
      if (arg === "--json") options.json = true;
      else if (arg === "--help" || arg === "-h") {
        process.stdout.write(`${USAGE}\n`);
        return 0;
      } else if (arg === "--repo") {
        const value = argv[++index];
        if (!value || value.startsWith("--")) throw new TickError("--repo needs a path.");
        options.repo = value;
      } else if (arg.startsWith("--")) throw new TickError(`Unknown argument ${arg}. ${USAGE}`);
      else rest.push(arg);
    }
    const where = store.requireLocation(path.resolve(options.repo));
    if (rest[0] === "task") {
      const job = task(where);
      process.stdout.write(`${options.json ? JSON.stringify(job, null, 2) : renderTask(job)}\n`);
      return 0;
    }
    if (rest.length) throw new TickError(`Unknown subcommand ${rest[0]}. ${USAGE}`);
    const result = tick(where);
    process.stdout.write(`${options.json ? JSON.stringify(result, null, 2) : render(result)}\n`);
    return 0;
  } catch (error) {
    if (error instanceof TickError || error instanceof store.ChatError) {
      process.stderr.write(`keel tick: ${error.message}\n`);
      return 1;
    }
    throw error;
  }
}

module.exports = { runTick, tick, TickError };

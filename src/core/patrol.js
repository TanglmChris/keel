"use strict";

// `keel patrol` (#260, #242): run by the coordinator's role on a host schedule.
// It marks each declared wait whose condition now holds as met and tells the
// waiting role, routes labelled issue updates to the roles `issue_roles:`
// names, and lists every role's presence. Keel fetches nothing and schedules
// nothing (F4): the caller fetches, passes `gh` output, and runs it.
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const store = require("./chat/store");
const notice = require("./chat/notice");
const { parseSince } = require("./chat/view");

const USAGE = "keel patrol [--issues <file>] [--idle <90s|15m|2h|3d>] [--since-last [--notify]] [--json] [--repo <path>]\n       keel patrol task [--json] [--repo <path>]   print the host scheduled task for `patrol:`";
const NOTIFY_SENDER = "keel-patrol";
const EXIT_QUIET = 0;
const EXIT_ERROR = 1;
const EXIT_WROTE = 2;

class PatrolError extends Error {}

function git(cwd, args) {
  const result = spawnSync("git", args, { cwd, encoding: "utf8", env: { ...process.env, GIT_OPTIONAL_LOCKS: "0" } });
  return result.status === 0 ? String(result.stdout || "").trim() : null;
}

// `gh issue list --json number,title,state,labels,updatedAt`, refused by name
// when it is not that shape.
function readIssues(file) {
  if (!file) return null;
  let parsed;
  try {
    parsed = JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (error) {
    throw new PatrolError(`--issues ${file} is not readable JSON: ${error.message}`);
  }
  if (!Array.isArray(parsed) || parsed.some((issue) => !issue || !Number.isInteger(issue.number))) {
    throw new PatrolError(`--issues ${file} must be the JSON array \`gh issue list --json number,title,state,labels,updatedAt\` prints.`);
  }
  return parsed;
}

// D3: a commit condition holds when a `refs/remotes/<remote>/` ref contains it.
function conditionHolds(where, condition, issues) {
  const commit = condition.match(/^commit ([0-9a-f]+) on (\S+)$/);
  if (commit) {
    if (git(where.worktree, ["cat-file", "-e", `${commit[1]}^{commit}`]) === null) return { holds: false };
    const refs = git(where.worktree, ["for-each-ref", "--contains", commit[1], "--format=%(refname)", `refs/remotes/${commit[2]}/`]);
    return { holds: Boolean(refs) };
  }
  const issue = condition.match(/^issue #(\d+) closed$/);
  if (issue) {
    if (!issues) return { unchecked: true };
    const found = issues.find((entry) => entry.number === Number(issue[1]));
    return { holds: Boolean(found && String(found.state).toUpperCase() === "CLOSED") };
  }
  return { unchecked: true };
}

function patrol(where, role, options) {
  const result = { role, notices: [], held: [], unchecked: [], roles: [], warnings: [] };
  for (const waitRecord of store.openWaits(where, role)) {
    const check = conditionHolds(where, waitRecord.condition, options.issues);
    if (check.unchecked) {
      result.unchecked.push({ id: waitRecord.id, from: waitRecord.from, condition: waitRecord.condition });
      continue;
    }
    if (!check.holds) continue;
    store.markMet(where, waitRecord, role);
    result.held.push({ id: waitRecord.id, from: waitRecord.from, condition: waitRecord.condition });
    if (waitRecord.from !== role) {
      const text = `Condition met: ${waitRecord.condition} (wait ${waitRecord.id}${waitRecord.text ? `: ${waitRecord.text}` : ""}).`;
      const posted = store.directPost(where, waitRecord.from, text, { refs: [`wait:${waitRecord.id}`] });
      result.notices.push({ to: waitRecord.from, id: posted.id, text });
    }
  }
  const routed = routeIssues(where, role, options);
  result.notices.push(...routed.notices);
  result.warnings.push(...routed.warnings);
  // D6: presence is reported, never acted on.
  const roles = [...new Set(Object.values(store.readJsonFile(path.join(where.root, "roles.json"))).filter(Boolean))].sort();
  // Bindings that drifted from where sessions run (#301 D2): reported, never acted on.
  result.drift = require("./chat/drift").driftLines(require("./chat/drift").roleDrift(where));
  const threshold = parseSince(options.idle);
  for (const name of roles) {
    const presence = notice.presenceOf(where, name);
    const last = Date.parse(presence.last_active || "");
    result.roles.push({
      role: name,
      presence: presence.state,
      lastActive: presence.last_active,
      idle: Number.isNaN(last) || last < threshold,
      openTodos: store.openTodos(where, { assignee: name }).length,
    });
  }
  return result;
}

// D5 (#242): each role a label of an issue maps to gets one direct message
// per `updatedAt`, deduped by its ref against the direct group's records.
function routeIssues(where, role, options) {
  const { routes, unreadable } = require("./config").readIssueRoles(where.worktree);
  const warnings = unreadable.map(
    (line) => `keel/config.yaml issue_roles line \`${line}\` is not \`<label>: <role>\`; it routes nothing.`
  );
  const notices = [];
  if (!options.issues || !routes.size) return { notices, warnings };
  for (const issue of options.issues) {
    const labels = (issue.labels || []).map((entry) => (typeof entry === "string" ? entry : entry && entry.name)).filter(Boolean);
    const targets = [...new Set(labels.map((name) => routes.get(name)).filter(Boolean))];
    for (const target of targets) {
      if (target === role) continue;
      const ref = `issue:#${issue.number}@${issue.updatedAt || "unknown"}`;
      const group = store.directName(role, target);
      if (store.readLog(where, group).some((record) => (record.refs || []).includes(ref))) continue;
      const when = issue.updatedAt ? ` at ${issue.updatedAt}` : "";
      const title = issue.title ? `: ${issue.title}` : "";
      const text = `Issue #${issue.number} changed${when}${title} (its label routes it to ${target}).`;
      const posted = store.directPost(where, target, text, { refs: [ref] });
      notices.push({ to: target, id: posted.id, text });
    }
  }
  return { notices, warnings };
}

// --- what changed since the last run (#295 D1, D2) ------------------------------------

function snapshotFile(where, role) {
  return path.join(where.root, "patrol", `${role}.json`);
}

function primaryWorktree(where) {
  const list = git(where.worktree, ["worktree", "list", "--porcelain"]);
  const first = list && list.split("\n").find((line) => line.startsWith("worktree "));
  return first ? first.slice("worktree ".length) : null;
}

// The entries a scheduled run compares, keyed so a change names its subject.
function currentSnapshot(where, role, result, options) {
  const shift = require("./shift");
  const entries = {};
  for (const row of shift.shiftStatus(where)) entries[`shift ${row.role}`] = shift.describe(row);
  const base = require("./worktrees").defaultBranch(where.worktree);
  if (base) {
    const ref = `refs/remotes/origin/${base.replace(/^origin\//, "")}`;
    entries[`remote ${ref.replace(/^refs\/remotes\//, "")}`] = git(where.worktree, ["rev-parse", "--verify", "--quiet", ref]) || "none";
  }
  const primary = primaryWorktree(where);
  if (primary) {
    const status = git(primary, ["status", "--porcelain"]);
    if (status !== null) entries[`checkout ${primary}`] = `${status ? status.split("\n").length : 0} uncommitted paths`;
  }
  for (const line of result.drift) entries[line.key] = line.text;
  for (const row of result.roles) {
    entries[`role ${row.role}`] = `${row.idle ? "idle" : "active"}, ${row.openTodos} open todo${row.openTodos === 1 ? "" : "s"}`;
  }
  const threshold = parseSince(options.idle);
  const unread = store.unread(where, role)
    .filter((record) => store.wakes(record, role) && Date.parse(record.created || "") < threshold)
    .map((record) => ({ id: record.id, from: record.from, created: record.created }));
  return { entries, unread };
}

function sinceLast(where, role, result, options) {
  const file = snapshotFile(where, role);
  const previous = fs.existsSync(file) ? store.readJsonFile(file) : null;
  const now = currentSnapshot(where, role, result, options);
  store.writeJsonAtomic(where, file, now);
  if (!previous || !previous.entries) return { baseline: true, changes: [] };
  const changes = [];
  const keys = [...new Set([...Object.keys(previous.entries), ...Object.keys(now.entries)])].sort();
  for (const key of keys) {
    const before = previous.entries[key] ?? "(none)";
    const after = now.entries[key] ?? "(none)";
    if (before !== after) changes.push(`${key}: ${before} -> ${after}`);
  }
  const seen = new Set((previous.unread || []).map((record) => record.id));
  for (const record of now.unread) {
    if (!seen.has(record.id)) changes.push(`unread: ${record.id} from ${record.from}, unanswered since ${record.created}`);
  }
  return { baseline: false, changes };
}

function notifyChanges(where, role, changes) {
  const group = store.directName(NOTIFY_SENDER, role);
  if (!store.groupState(store.readLog(where, group)).exists) {
    store.createGroup(where, NOTIFY_SENDER, group, [role], { direct: true });
  }
  const text = [`Patrol ${store.isoLocal(new Date())}: what changed since the last run:`, ...changes.map((line) => `- changed: ${line}`)].join("\n");
  return store.writeRecord(where, { group, kind: "message", from: NOTIFY_SENDER, refs: [NOTIFY_SENDER], text });
}

function render(result) {
  const lines = [];
  const changes = result.sinceLast ? result.sinceLast.changes : [];
  if (result.sinceLast && result.sinceLast.baseline) lines.push("keel patrol: baseline recorded.");
  else if (!result.notices.length && !result.held.length && !changes.length) lines.push("keel patrol: nothing new.");
  for (const change of changes) lines.push(`changed: ${change}`);
  for (const held of result.held) lines.push(`met: ${held.from} waited for ${held.condition} (${held.id})`);
  for (const sent of result.notices) lines.push(`notified ${sent.to}: ${sent.text}`);
  for (const wait of result.unchecked) lines.push(`unchecked: ${wait.from} waits for ${wait.condition}; pass --issues to check it`);
  for (const warning of result.warnings) lines.push(`warning: ${warning}`);
  for (const line of result.sinceLast ? [] : result.drift) lines.push(`drift: ${line.text}`);
  // A scheduled run reports roles only through what changed (D1).
  for (const row of result.sinceLast ? [] : result.roles) {
    lines.push(`role ${row.role}: ${row.presence}${row.idle ? " (idle)" : ""}, last active ${row.lastActive || "unknown"}, ${row.openTodos} open todo${row.openTodos === 1 ? "" : "s"}`);
  }
  return lines.join("\n");
}

// --- the host task (#295 D4) ---------------------------------------------------------
//
// Keel renders the task and creates nothing: a host's schedule is set through
// its own tool, which the session's model calls (F1).

function suggestCron(every) {
  const match = String(every).match(/^(\d+)([smhd])$/);
  const n = match ? Number(match[1]) : 0;
  const unit = match ? match[2] : "";
  if ((unit === "m" && n === 60) || (unit === "h" && n === 1)) return { cron: "0 * * * *" };
  if (unit === "m" && n > 0 && n < 60 && 60 % n === 0) return { cron: `*/${n} * * * *` };
  if (unit === "h" && n > 1 && 24 % n === 0) return { cron: `0 */${n} * * *` };
  if (unit === "d" && n === 1) return { cron: "0 9 * * *" };
  return { cron: null, why: `every: ${every} has no plain cron form; choose a schedule near it` };
}

function shellPath(file) {
  return /[\s"'$`\\]/.test(file) ? JSON.stringify(file) : file;
}

function hostTask(where) {
  const config = require("./config");
  const declaration = config.readPatrolDeclaration(where.worktree);
  if (!declaration.role) {
    throw new PatrolError(declaration.message || "keel/config.yaml declares no `patrol:` with role and every, so there is no patrol task to render.");
  }
  const bound = Object.entries(store.readJsonFile(path.join(where.root, "roles.json")))
    .filter(([, role]) => role === declaration.role).map(([worktree]) => worktree).sort();
  if (!bound.length) {
    throw new PatrolError(`No worktree is bound to role ${declaration.role}; bind one with \`keel chat role --set ${declaration.role}\` there first.`);
  }
  const worktree = bound[0];
  const role = declaration.role;
  const at = shellPath(worktree);
  const schedule = suggestCron(declaration.every);
  const prompt = [
    `You run the Keel patrol for chat role ${role} of the repository at ${worktree}. Do exactly the steps below and nothing else.`,
    "",
    `Do not change into that directory: run every command with the paths given, so this session does not act as ${role} (Keel's session hooks follow the working directory). `
      + "Do not edit files, commit, push, close or comment on issues, or message anyone yourself: `keel patrol` sends the coordinator what changed.",
    "",
    `1. Run \`git -C ${at} fetch -q origin\`. If it fails, keep its error and continue.`,
    `2. Run \`keel patrol --repo ${at} --since-last --notify\`.`,
    `3. Exit 0: nothing changed. Exit 2: keel has already told ${role}. In both cases end without output. `
      + "Exit 1: end with one line, `keel patrol failed: <its error output>`, adding the fetch error from step 1 if there was one.",
  ].join("\n");
  return {
    taskId: declaration.hostTask || `keel-patrol-${role}`,
    description: `Keel patrol for role ${role}: tells it what changed since the last run`,
    cronExpression: schedule.cron,
    cronNote: schedule.why || null,
    every: declaration.every,
    model: declaration.model,
    worktree,
    prompt,
  };
}

function renderTask(task) {
  return [
    `Host scheduled task for the patrol of role ${task.prompt.match(/chat role (\S+)/)[1]}. Keel creates nothing: install it with the host's scheduled-task tool.`,
    `task id: ${task.taskId}`,
    `schedule: ${task.cronExpression ? `${task.cronExpression} (from every: ${task.every}; hosts may add jitter)` : task.cronNote}`,
    `model: ${task.model || "no model is declared: choose a small model; Keel names none"}`,
    `description: ${task.description}`,
    "prompt:",
    task.prompt,
  ].join("\n");
}

function runPatrol(argv) {
  if (argv[0] === "task") {
    const json = argv.includes("--json");
    const at = argv.indexOf("--repo");
    try {
      const where = store.requireLocation(path.resolve(at >= 0 ? argv[at + 1] || "" : process.cwd()));
      const task = hostTask(where);
      process.stdout.write(`${json ? JSON.stringify(task, null, 2) : renderTask(task)}\n`);
      return EXIT_QUIET;
    } catch (error) {
      if (error instanceof PatrolError || error instanceof store.ChatError) {
        process.stderr.write(`keel patrol task: ${error.message}\n`);
        return EXIT_ERROR;
      }
      throw error;
    }
  }
  const options = { repo: process.cwd(), issues: null, idle: "30m", json: false, sinceLast: false, notify: false };
  try {
    for (let index = 0; index < argv.length; index += 1) {
      const arg = argv[index];
      if (arg === "--json") options.json = true;
      else if (arg === "--since-last") options.sinceLast = true;
      else if (arg === "--notify") options.notify = true;
      else if (arg === "--help" || arg === "-h") {
        process.stdout.write(`${USAGE}\nExit 0: wrote nothing. 2: sent a notice or marked a wait met. 1: error.\n`);
        return EXIT_QUIET;
      } else if (["--repo", "--issues", "--idle"].includes(arg)) {
        const value = argv[++index];
        if (!value || value.startsWith("--")) throw new PatrolError(`${arg} needs a value.`);
        options[arg.slice(2)] = value;
      } else throw new PatrolError(`Unknown argument ${arg}. ${USAGE}`);
    }
    if (options.notify && !options.sinceLast) throw new PatrolError("--notify sends what changed, so it needs --since-last.");
    if (parseSince(options.idle) === null) throw new PatrolError(`--idle ${JSON.stringify(options.idle)} is not a duration; use 90s, 15m, 2h, or 3d.`);
    options.issues = readIssues(options.issues);
    const where = store.requireLocation(path.resolve(options.repo));
    const role = store.requireRole(where);
    const result = patrol(where, role, options);
    if (options.sinceLast) {
      result.sinceLast = sinceLast(where, role, result, options);
      if (options.notify && result.sinceLast.changes.length) result.notified = notifyChanges(where, role, result.sinceLast.changes).id;
    }
    process.stdout.write(`${options.json ? JSON.stringify(result, null, 2) : render(result)}\n`);
    const changed = result.sinceLast && result.sinceLast.changes.length;
    return result.notices.length || result.held.length || changed ? EXIT_WROTE : EXIT_QUIET;
  } catch (error) {
    if (error instanceof PatrolError || error instanceof store.ChatError) {
      process.stderr.write(`keel patrol: ${error.message}\n`);
      return EXIT_ERROR;
    }
    throw error;
  }
}

module.exports = { PatrolError, runPatrol, patrol };

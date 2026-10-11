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

const USAGE = "keel patrol [--issues <file>] [--idle <90s|15m|2h|3d>] [--json] [--repo <path>]";
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

function render(result) {
  const lines = [];
  if (!result.notices.length && !result.held.length) lines.push("keel patrol: nothing new.");
  for (const held of result.held) lines.push(`met: ${held.from} waited for ${held.condition} (${held.id})`);
  for (const sent of result.notices) lines.push(`notified ${sent.to}: ${sent.text}`);
  for (const wait of result.unchecked) lines.push(`unchecked: ${wait.from} waits for ${wait.condition}; pass --issues to check it`);
  for (const warning of result.warnings) lines.push(`warning: ${warning}`);
  for (const row of result.roles) {
    lines.push(`role ${row.role}: ${row.presence}${row.idle ? " (idle)" : ""}, last active ${row.lastActive || "unknown"}, ${row.openTodos} open todo${row.openTodos === 1 ? "" : "s"}`);
  }
  return lines.join("\n");
}

function runPatrol(argv) {
  const options = { repo: process.cwd(), issues: null, idle: "30m", json: false };
  try {
    for (let index = 0; index < argv.length; index += 1) {
      const arg = argv[index];
      if (arg === "--json") options.json = true;
      else if (arg === "--help" || arg === "-h") {
        process.stdout.write(`${USAGE}\nExit 0: wrote nothing. 2: sent a notice or marked a wait met. 1: error.\n`);
        return EXIT_QUIET;
      } else if (["--repo", "--issues", "--idle"].includes(arg)) {
        const value = argv[++index];
        if (!value || value.startsWith("--")) throw new PatrolError(`${arg} needs a value.`);
        options[arg.slice(2)] = value;
      } else throw new PatrolError(`Unknown argument ${arg}. ${USAGE}`);
    }
    if (parseSince(options.idle) === null) throw new PatrolError(`--idle ${JSON.stringify(options.idle)} is not a duration; use 90s, 15m, 2h, or 3d.`);
    options.issues = readIssues(options.issues);
    const where = store.requireLocation(path.resolve(options.repo));
    const role = store.requireRole(where);
    const result = patrol(where, role, options);
    process.stdout.write(`${options.json ? JSON.stringify(result, null, 2) : render(result)}\n`);
    return result.notices.length || result.held.length ? EXIT_WROTE : EXIT_QUIET;
  } catch (error) {
    if (error instanceof PatrolError || error instanceof store.ChatError) {
      process.stderr.write(`keel patrol: ${error.message}\n`);
      return EXIT_ERROR;
    }
    throw error;
  }
}

module.exports = { PatrolError, runPatrol, patrol };

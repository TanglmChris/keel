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

const USAGE = "keel patrol [--issues <file>] [--idle <90s|15m|2h|3d>] [--since-last [--notify]] [--nudge] [--json] [--repo <path>]\n       keel patrol task [--role <role>] [--json] [--repo <path>]   print the host scheduled task for `patrol:`";
const NOTIFY_SENDER = "keel-patrol";
// 2 asks the coordinator to act — a risk, or a wait of its own now met — and
// 3 says patrol recorded or delivered something only other roles need: a
// coordinator's schedule wakes its model on 2, so a run that merely moved
// state no longer costs a turn (#350).
const EXIT_QUIET = 0;
const EXIT_ERROR = 1;
const EXIT_ACT = 2;
const EXIT_RECORDED = 3;

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

// What a patrolling role covers (#434 D3, D4, D9, D10): a scoped declaration
// its group's members, the unscoped one the roles in no declared scope, and a
// role `patrol:` does not declare every role. The repository-wide items belong
// to the unscoped declaration, or to the first declared when all are scoped.
function coverageOf(where, role) {
  const { declarations } = require("./config").readPatrolDeclarations(where.worktree);
  const own = declarations.find((declaration) => declaration.role === role);
  if (!own) return { covers: (name) => name !== role, repositoryWide: true, warnings: [] };
  const membersOf = (group) => store.groupState(store.readLog(where, group)).members;
  const warnings = [];
  let inside;
  if (own.scope) {
    const members = membersOf(own.scope);
    if (!members.size) warnings.push(`patrol scope group:${own.scope} has no members, so ${role} covers no role.`);
    inside = (name) => members.has(name);
  } else {
    const scoped = new Set(declarations.filter((declaration) => declaration.scope).flatMap((declaration) => [...membersOf(declaration.scope)]));
    inside = (name) => !scoped.has(name);
  }
  const owner = declarations.find((declaration) => !declaration.scope) || declarations[0];
  return { covers: (name) => name !== role && inside(name), repositoryWide: owner.role === role, warnings };
}

function patrol(where, role, options) {
  const result = { role, notices: [], held: [], unchecked: [], roles: [], warnings: [] };
  if (!options.coverage) options = { ...options, coverage: coverageOf(where, role) };
  const { coverage } = options;
  result.warnings.push(...coverage.warnings);
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
  // D6: presence is reported, never acted on, for the patroller and the roles it covers.
  const roles = [...new Set(Object.values(store.readJsonFile(path.join(where.root, "roles.json"))).filter(Boolean))]
    .filter((name) => name === role || coverage.covers(name)).sort();
  // Bindings that drifted from where sessions run (#301 D2): reported, never acted on.
  result.drift = coverage.repositoryWide ? require("./chat/drift").driftLines(require("./chat/drift").roleDrift(where)) : [];
  const threshold = parseSince(options.idle);
  for (const name of roles) {
    const presence = notice.presenceOf(where, name);
    const last = Date.parse(presence.last_active || "");
    result.roles.push({
      role: name,
      presence: presence.state,
      lastActive: presence.last_active,
      idle: Number.isNaN(last) || last < threshold,
      parked: Boolean(notice.parkOf(where, name)),
      openTodos: store.openTodos(where, { assignee: name }).length,
    });
  }
  return result;
}

// D5 (#242): each role a matching route names gets one direct message per
// `updatedAt`, deduped by its ref against the direct group's records. A route
// whose labels are a strict subset of another matching route's is refined by
// it and sends nothing (#433).
function routeIssues(where, role, options) {
  const { routes, unreadable } = require("./config").readIssueRoles(where.worktree);
  const warnings = unreadable.map(
    (line) => `keel/config.yaml issue_roles line \`${line}\` is not \`<label>: <role>\` or \`<label> + <label>: <role>\`; it routes nothing.`
  );
  const notices = [];
  if (!options.issues || !routes.length) return { notices, warnings };
  // A role covered by two coordinators hears of an update once (#434 D5).
  const patrollers = [...new Set([role, ...require("./config").readPatrolDeclarations(where.worktree).declarations.map((d) => d.role)])];
  const covers = options.coverage ? options.coverage.covers : () => true;
  for (const issue of options.issues) {
    const labels = new Set((issue.labels || []).map((entry) => (typeof entry === "string" ? entry : entry && entry.name)).filter(Boolean));
    const matching = routes.filter((route) => route.labels.every((name) => labels.has(name)));
    const refined = (route) => matching.some(
      (other) => other.labels.length > route.labels.length && route.labels.every((name) => other.labels.includes(name))
    );
    const targets = [...new Set(matching.filter((route) => !refined(route)).map((route) => route.role))];
    for (const target of targets) {
      if (target === role || !covers(target)) continue;
      const ref = `issue:#${issue.number}@${issue.updatedAt || "unknown"}`;
      const sent = patrollers.filter((patroller) => patroller !== target)
        .some((patroller) => store.readLog(where, store.directName(patroller, target)).some((record) => (record.refs || []).includes(ref)));
      if (sent) continue;
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
  const coverage = options.coverage || { covers: () => true, repositoryWide: true };
  for (const row of shift.shiftStatus(where)) {
    if (row.role === role || coverage.covers(row.role)) entries[`shift ${row.role}`] = shift.describe(row);
  }
  const base = coverage.repositoryWide ? require("./worktrees").defaultBranch(where.worktree) : null;
  if (base) {
    const ref = `refs/remotes/origin/${base.replace(/^origin\//, "")}`;
    entries[`remote ${ref.replace(/^refs\/remotes\//, "")}`] = git(where.worktree, ["rev-parse", "--verify", "--quiet", ref]) || "none";
  }
  const primary = coverage.repositoryWide ? primaryWorktree(where) : null;
  if (primary) {
    const status = git(primary, ["status", "--porcelain"]);
    if (status !== null) entries[`checkout ${primary}`] = `${status ? status.split("\n").length : 0} uncommitted paths`;
  }
  for (const line of result.drift) entries[line.key] = line.text;
  // Free disk as the host measured it (#307 part 3 D1).
  if (options.diskFreeGb !== null && coverage.repositoryWide) entries.disk = options.diskFreeGb < options.diskMinGb ? "low" : "ok";
  for (const row of result.roles) {
    entries[`role ${row.role}`] = `${row.parked ? "parked" : row.idle ? "idle" : "active"}, ${row.openTodos} open todo${row.openTodos === 1 ? "" : "s"}`;
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
  now.standing = result.standing || [];
  store.writeJsonAtomic(where, file, now);
  // A standing risk is a risk on the run its text first appears (#476 D1).
  const sent = new Set((previous && previous.standing) || []);
  const fresh = now.standing.filter((text) => !sent.has(text));
  result.sentBefore = now.standing.filter((text) => sent.has(text));
  if (!previous || !previous.entries) return { baseline: true, changes: [], risks: fresh };
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
  // What the coordinator must hear (#307 part 3 D1): a clean checkout turned
  // dirty, and free disk turned low; the rest of the changes are only printed.
  const risks = [];
  for (const key of Object.keys(now.entries).filter((entry) => entry.startsWith("checkout "))) {
    const count = Number.parseInt(now.entries[key], 10);
    if (previous.entries[key] === "0 uncommitted paths" && count > 0) {
      risks.push(`the shared checkout ${key.slice("checkout ".length)} has ${count} uncommitted paths`);
    }
  }
  if (now.entries.disk === "low" && previous.entries.disk !== "low") {
    risks.push(`free disk is ${options.diskFreeGb} GB, below ${options.diskMinGb} GB`);
  }
  risks.push(...fresh);
  return { baseline: false, changes, risks };
}

// --- nudges (#307 part 1) -----------------------------------------------------------
//
// The patrol nudges an idle role itself, with one direct message from
// `keel-patrol` that wakes its session (D1-D5). Keel's own records never count
// as waiting, so a nudge cannot cause the next one.

const KEEL_SENDERS = new Set([NOTIFY_SENDER, "keel-shift", "keel"]);
const UNREAD_EVERY_MS = Number(process.env.KEEL_PATROL_UNREAD_EVERY_MS) > 0 ? Number(process.env.KEEL_PATROL_UNREAD_EVERY_MS) : 2 * 60 * 60 * 1000;
const SELF_INITIATED = "Self-initiated: this shift armed `keel shift ready --wake`.";

function sendNudge(where, role, kind, text) {
  const group = store.directName(NOTIFY_SENDER, role);
  if (!store.groupState(store.readLog(where, group)).exists) {
    store.createGroup(where, NOTIFY_SENDER, group, [role], { direct: true });
  }
  store.writeRecord(where, { group, kind: "message", from: NOTIFY_SENDER, refs: ["keel-patrol-nudge"], text });
  return { role, kind, text };
}

// Closed todos per assignee: each `done` record and the todo it closes.
function closedTodos(where) {
  const byRole = new Map();
  for (const name of store.listGroupNames(where)) {
    const records = store.readLog(where, name);
    const todos = new Map(records.filter((r) => r.kind === "todo").map((r) => [r.id, r]));
    for (const record of records) {
      if (record.kind !== "done" || !todos.has(record.target)) continue;
      const todo = todos.get(record.target);
      if (!todo.assignee) continue;
      if (!byRole.has(todo.assignee)) byRole.set(todo.assignee, []);
      byRole.get(todo.assignee).push({ done: record.id, todo: todo.id, title: String(todo.text || "").split("\n")[0].slice(0, 80) });
    }
  }
  for (const list of byRole.values()) list.sort((a, b) => (a.done < b.done ? -1 : 1));
  return byRole;
}

function nudgeRoles(where, patroller, options) {
  const stateFile = path.join(where.root, "patrol", "nudges.json");
  const state = store.readJsonFile(stateFile);
  const now = Date.now();
  const idleBefore = parseSince(options.idle);
  const sent = [];
  const escalations = [];
  const covers = options.coverage ? options.coverage.covers : (role) => role !== patroller;
  const roles = [...new Set(Object.values(store.readJsonFile(path.join(where.root, "roles.json"))).filter(Boolean))]
    .filter((role) => role !== patroller && covers(role)).sort();
  const closures = closedTodos(where);
  for (const role of roles) {
    // A role parked on purpose is left alone, its state kept (#316 D4).
    if (notice.parkOf(where, role)) continue;
    // The first look only records the tasks already closed (#313 D1).
    if (!state[role] || !Array.isArray(state[role].closedSeen)) {
      state[role] = { ...(state[role] || {}), closedSeen: (closures.get(role) || []).map((entry) => entry.done) };
    }
    const last = Date.parse(notice.presenceOf(where, role).last_active || "");
    if (!Number.isNaN(last) && last >= idleBefore) continue;
    const mine = state[role] || {};
    const waiting = store.unread(where, role)
      .filter((record) => store.wakes(record, role) && !KEEL_SENDERS.has(record.from))
      .sort((a, b) => (a.id < b.id ? -1 : 1));
    const note = path.join(where.root, "shift", `${role}.md`);
    const noteText = fs.existsSync(note) ? fs.readFileSync(note, "utf8") : null;
    if (waiting.length) {
      const oldest = Date.parse(waiting[0].created || "");
      const recent = Date.parse(mine.unread || "");
      if (!Number.isNaN(oldest) && oldest < idleBefore && (Number.isNaN(recent) || now - recent >= UNREAD_EVERY_MS)) {
        sent.push(sendNudge(where, role, "unread",
          `${role}: ${waiting.length} record(s) addressed to you have waited since ${waiting[0].created}; read them with \`keel chat unread\`.`));
        // A nudge over work older than the last one is a nudge left unanswered (D2).
        mine.unanswered = !Number.isNaN(recent) && oldest < recent ? (mine.unanswered || 0) + 1 : 1;
        if (mine.unanswered === 2) {
          escalations.push(`${role} has not answered 2 nudges; ${waiting.length} record(s) addressed to it have waited since ${waiting[0].created}`);
        }
        mine.unread = new Date(now).toISOString();
      }
    } else {
      mine.unanswered = 0;
    }
    // A finished task is the shift boundary (#313 D2); within a task the host compacts.
    const fresh = (closures.get(role) || []).filter((entry) => !mine.closedSeen.includes(entry.done));
    if (fresh.length && !noteText) {
      const task = fresh[fresh.length - 1];
      const open = store.openTodos(where, { assignee: role }).length;
      const next = open
        ? `\`keel shift ready --wake "<note>"\` — you still hold ${open} open todo(s)`
        : "`keel shift ready \"<note>\"`, and wait for the coordinator to start you with new work";
      sent.push(sendNudge(where, role, "shift",
        `${role}: your task ${task.todo} ("${task.title}") was closed. Change shift at this task boundary: `
        + `\`keel shift check\`, then ${next}, then clear this session (a session serving Remote Control cannot be `
        + "cleared: turn it off, clear, then turn it back on)."));
      mine.closedSeen = [...mine.closedSeen, ...fresh.map((entry) => entry.done)];
    }
    if (noteText && noteText.includes(SELF_INITIATED)) {
      const written = fs.statSync(note).mtime;
      const woken = store.readLog(where, store.directName("keel-shift", role))
        .some((record) => record.from === "keel-shift" && Date.parse(record.created || "") >= written.getTime() - 1000);
      const stamp = store.isoLocal(written);
      if (written.getTime() < idleBefore && !woken && mine.resume !== stamp) {
        sent.push(sendNudge(where, role, "resume",
          `${role}: your previous shift left a note at ${stamp}; run \`keel context\`, then \`keel shift resume\`.`));
        mine.resume = stamp;
      }
    }
    // A nudge to a desktop session with no running process wakes nothing,
    // so the coordinator hears it on the first one (#331 D4).
    const sleeping = sent.some((entry) => entry.role === role) ? notice.asleep(where, role) : null;
    if (sleeping && sleeping.cli) {
      // An ended CLI session is resumed in one step (#348 D5).
      escalations.push(`${role}'s CLI session ${sleeping.session} has no running process, so the nudge wakes nothing: `
        + `resume it with \`keel chat wake now ${role}\`.`);
    } else if (sleeping) {
      escalations.push(`${role}'s desktop session ${sleeping.session} has no running process, so the nudge wakes nothing: `
        + notice.wakeStep(sleeping.session, "You have unread keel chat records; run `keel chat unread`."));
    }
    state[role] = mine;
  }
  store.writeJsonAtomic(where, stateFile, state);
  return { sent, escalations };
}

// --- quota thresholds (#307 part 2) ---------------------------------------------------
//
// The host reports the weekly quota's percent used; each threshold is a risk
// once per period, and a drop in the figure starts a new period (D2).
function quotaRisk(where, options) {
  if (options.quota === null) return null;
  const file = path.join(where.root, "patrol", "quota.json");
  const state = store.readJsonFile(file);
  let reported = Array.isArray(state.reported) ? state.reported : [];
  if (typeof state.last === "number" && options.quota < state.last) reported = [];
  const reached = options.quotaAlerts.filter((threshold) => threshold <= options.quota && !reported.includes(threshold));
  store.writeJsonAtomic(where, file, { last: options.quota, reported: [...reported, ...reached].sort((a, b) => a - b) });
  if (!reached.length) return null;
  return `weekly quota is at ${options.quota}%, past ${Math.max(...reached)}%`;
}

function notifyRisks(where, role, risks) {
  const group = store.directName(NOTIFY_SENDER, role);
  if (!store.groupState(store.readLog(where, group)).exists) {
    store.createGroup(where, NOTIFY_SENDER, group, [role], { direct: true });
  }
  const text = [`Patrol ${store.isoLocal(new Date())}: risks for the coordinator:`, ...risks.map((line) => `- risk: ${line}`)].join("\n");
  return store.writeRecord(where, { group, kind: "message", from: NOTIFY_SENDER, refs: [NOTIFY_SENDER], text });
}

function render(result) {
  const lines = [];
  const changes = result.sinceLast ? result.sinceLast.changes : [];
  if (result.sinceLast && result.sinceLast.baseline) lines.push("keel patrol: baseline recorded.");
  else if (!result.notices.length && !result.held.length && !changes.length) lines.push("keel patrol: nothing new.");
  for (const change of changes) lines.push(`changed: ${change}`);
  for (const sent of result.nudges || []) lines.push(`nudged ${sent.role}: ${sent.kind}`);
  for (const risk of result.risks || []) lines.push(`risk: ${risk}`);
  for (const risk of result.sentBefore || []) lines.push(`risk (sent before): ${risk}`);
  if (result.paused) lines.push(result.paused);
  for (const held of result.held) lines.push(`met: ${held.from} waited for ${held.condition} (${held.id})`);
  for (const sent of result.notices) lines.push(`notified ${sent.to}: ${sent.text}`);
  for (const wait of result.unchecked) lines.push(`unchecked: ${wait.from} waits for ${wait.condition}; pass --issues to check it`);
  for (const warning of result.warnings) lines.push(`warning: ${warning}`);
  for (const line of result.sinceLast ? [] : result.drift) lines.push(`drift: ${line.text}`);
  // A scheduled run reports roles only through what changed (D1).
  for (const row of result.sinceLast ? [] : result.roles) {
    lines.push(`role ${row.role}: ${row.presence}${row.idle ? " (idle)" : ""}${row.parked ? ", parked" : ""}, last active ${row.lastActive || "unknown"}, ${row.openTodos} open todo${row.openTodos === 1 ? "" : "s"}`);
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

// Whose task (#434 D6): `--role`'s, else the calling worktree's role's, else
// the only declaration; between several it refuses rather than guess.
function chooseDeclaration(where, requested) {
  const all = require("./config").readPatrolDeclarations(where.worktree);
  const { declarations } = all;
  if (!declarations.length) {
    throw new PatrolError(all.messages.join(" ") || "keel/config.yaml declares no `patrol:` with role and every, so there is no patrol task to render.");
  }
  if (requested) {
    const named = declarations.find((declaration) => declaration.role === requested);
    if (!named) throw new PatrolError(`keel/config.yaml patrol: declares no role ${requested}; it declares ${declarations.map((d) => d.role).join(", ")}.`);
    return named;
  }
  const own = declarations.find((declaration) => declaration.role === store.currentRole(where));
  if (own) return own;
  if (declarations.length === 1) return declarations[0];
  throw new PatrolError(`keel/config.yaml patrol: declares ${declarations.map((d) => d.role).join(", ")}, and this worktree's role is none of them; `
    + "name one with `--role <role>`.");
}

function hostTask(where, requested = null) {
  const declaration = chooseDeclaration(where, requested);
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
    "Run every command with the paths given. "
      + "Do not edit files, commit, push, close or comment on issues, or message anyone yourself: `keel patrol` sends the coordinator what changed.",
    "",
    `1. Run \`git -C ${at} fetch -q origin\`. If it fails, keep its error and continue.`,
    `2. Run \`keel patrol --repo ${at} --since-last --notify\`.`,
    `3. Exit 0: nothing changed. Exit 2: keel has already told ${role} what to act on. Exit 3: keel recorded or told other roles only. In these cases end without output. `
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
    "Create it from a session whose folder is bound to no role: a host task starts its runs in the folder it was created from, "
      + "and Keel recognizes such a run only once its prompt arrives (#300).",
    `description: ${task.description}`,
    "prompt:",
    task.prompt,
  ].join("\n");
}

function runPatrol(argv) {
  if (argv[0] === "task") {
    const json = argv.includes("--json");
    const at = argv.indexOf("--repo");
    const roleAt = argv.indexOf("--role");
    try {
      if (roleAt >= 0 && !argv[roleAt + 1]) throw new PatrolError("--role needs a role name.");
      const where = store.requireLocation(path.resolve(at >= 0 ? argv[at + 1] || "" : process.cwd()));
      const task = hostTask(where, roleAt >= 0 ? argv[roleAt + 1] : null);
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
  const options = { repo: process.cwd(), issues: null, idle: "30m", json: false, sinceLast: false, notify: false, nudge: false, diskFreeGb: null, diskMinGb: 20, quota: null, quotaAlerts: [90, 95, 99], quotaQuietAt: 90 };
  try {
    for (let index = 0; index < argv.length; index += 1) {
      const arg = argv[index];
      if (arg === "--json") options.json = true;
      else if (arg === "--since-last") options.sinceLast = true;
      else if (arg === "--notify") options.notify = true;
      else if (arg === "--nudge") options.nudge = true;
      else if (arg === "--context" || arg === "--shift-at") {
        throw new PatrolError(`${arg}: --context and --shift-at were retired in 5.125.0 (#313): a shift follows a task's close, and compaction within a task stays the host's.`);
      }
      else if (arg === "--disk-free-gb") options.diskFreeGb = Number(argv[++index]);
      else if (arg === "--disk-min-gb") options.diskMinGb = Number(argv[++index]);
      else if (arg === "--quota") options.quota = Number(argv[++index]);
      else if (arg === "--quota-alerts") options.quotaAlerts = String(argv[++index] || "").split(",").map(Number);
      else if (arg === "--quota-quiet-at") options.quotaQuietAt = Number(argv[++index]);
      else if (arg === "--help" || arg === "-h") {
        process.stdout.write(`${USAGE}\nExit 0: wrote nothing. 2: something for you to act on (a risk, or your own wait met). 3: recorded or told other roles only. 1: error.\n`);
        return EXIT_QUIET;
      } else if (["--repo", "--issues", "--idle"].includes(arg)) {
        const value = argv[++index];
        if (!value || value.startsWith("--")) throw new PatrolError(`${arg} needs a value.`);
        options[arg.slice(2)] = value;
      } else throw new PatrolError(`Unknown argument ${arg}. ${USAGE}`);
    }
    if (options.notify && !options.sinceLast) throw new PatrolError("--notify sends the risks found since the last run, so it needs --since-last.");
    if (options.diskFreeGb !== null && !(options.diskFreeGb >= 0)) throw new PatrolError("--disk-free-gb needs a number of gigabytes.");
    if (!(options.diskMinGb > 0)) throw new PatrolError("--disk-min-gb needs a positive number of gigabytes.");
    const percent = (value) => Number.isFinite(value) && value >= 0 && value <= 100;
    if (options.quota !== null && !percent(options.quota)) throw new PatrolError("--quota needs the percent used, from 0 to 100.");
    if (!options.quotaAlerts.length || !options.quotaAlerts.every(percent)) throw new PatrolError("--quota-alerts needs percentages separated by commas, such as 90,95,99.");
    if (!percent(options.quotaQuietAt)) throw new PatrolError("--quota-quiet-at needs a percentage from 0 to 100.");
    if (parseSince(options.idle) === null) throw new PatrolError(`--idle ${JSON.stringify(options.idle)} is not a duration; use 90s, 15m, 2h, or 3d.`);
    options.issues = readIssues(options.issues);
    const where = store.requireLocation(path.resolve(options.repo));
    const role = store.requireRole(where);
    options.coverage = coverageOf(where, role);
    const result = patrol(where, role, options);
    result.risks = [];
    const quota = options.coverage.repositoryWide ? quotaRisk(where, options) : null;
    if (quota) result.risks.push(quota);
    // A CLI hand-off that failed or hangs (#357 D4), and an ended CLI session
    // whose worktree is gone (#465 D4), of the roles this patrol covers. They
    // stand until resolved, so `--since-last` sends each once (#476 D1, D2).
    const covered = (name) => name === role || options.coverage.covers(name);
    result.standing = [
      ...require("./shift").handOffRisks(where, Date.now(), covered),
      ...require("./chat/notice").movedSessionRisks(where, covered),
    ];
    if (!options.sinceLast) result.risks.push(...result.standing);
    // Near the limit nudges stop, since each wakes a large session (D3).
    const quiet = options.quota !== null && options.quota >= options.quotaQuietAt;
    if (options.nudge && quiet) result.paused = `nudges paused: quota at ${options.quota}%`;
    if (options.nudge && !quiet) {
      const nudged = nudgeRoles(where, role, options);
      result.nudges = nudged.sent;
      result.risks.push(...nudged.escalations);
    }
    if (options.sinceLast) {
      result.sinceLast = sinceLast(where, role, result, options);
      result.risks.unshift(...result.sinceLast.risks);
      // Only risks reach the coordinator (#307 part 3 D3).
      if (options.notify && result.risks.length) result.notified = notifyRisks(where, role, result.risks).id;
    }
    const next = recommendNext(where, role, result, options);
    result.next_after_s = next.seconds;
    result.next_rule = next.rule;
    result.next_at = store.isoLocal(new Date(Date.now() + next.seconds * 1000));
    process.stdout.write(`${options.json ? JSON.stringify(result, null, 2) : `${render(result)}\nnext: ${formatDuration(next.seconds)} (${next.rule})`}\n`);
    const changed = result.sinceLast && result.sinceLast.changes.length;
    const own = result.held.some((held) => held.from === role);
    const recorded = result.notices.length || result.held.length || changed || (result.nudges || []).length;
    const code = result.risks.length || own ? EXIT_ACT : recorded ? EXIT_RECORDED : EXIT_QUIET;
    appendRunLog(where, role, code, result);
    return code;
  } catch (error) {
    if (error instanceof PatrolError || error instanceof store.ChatError) {
      process.stderr.write(`keel patrol: ${error.message}\n`);
      return EXIT_ERROR;
    }
    throw error;
  }
}

// When to run next (#356): `every:` as a fixed cadence, or with
// `cadence: adaptive` the first matching rule. The runner that re-arms on it
// is the caller's; this only recommends.
function recommendNext(where, role, result, options, now = new Date()) {
  const { readPatrolDeclaration, durationSeconds } = require("./config");
  const declaration = readPatrolDeclaration(where.worktree, { role });
  const cadence = declaration.cadence;
  if (!cadence || !cadence.adaptive) {
    const every = durationSeconds(declaration.every) || 3600;
    return { seconds: every, rule: "fixed" };
  }
  const active = new Set(result.roles.filter((r) => !r.idle).map((r) => r.role));
  const assigned = [
    ...store.openTodos(where, {}).map((todo) => todo.assignee),
    ...store.openWaits(where, role).map((waitRecord) => waitRecord.from),
  ];
  let pick;
  if (result.risks.length) pick = { seconds: cadence.risk, rule: "risk" };
  else if (options.quota !== null && options.quota >= 90) pick = { seconds: cadence.quota, rule: "quota" };
  else if (cadence.quiet && inWindow(cadence.quiet, now)) {
    return { seconds: untilWindowEnd(cadence.quiet, now), rule: "night" };
  } else if ([...active].some((name) => name !== role) || assigned.some((name) => active.has(name))) pick = { seconds: cadence.busy, rule: "busy" };
  else pick = { seconds: cadence.idle, rule: "idle" };
  if (cadence.min !== null) pick.seconds = Math.max(pick.seconds, cadence.min);
  if (cadence.max !== null) pick.seconds = Math.min(pick.seconds, cadence.max);
  return pick;
}

function minuteOfDay(now) {
  return now.getHours() * 60 + now.getMinutes();
}

function inWindow(window, now) {
  const minute = minuteOfDay(now);
  return window.start <= window.end
    ? minute >= window.start && minute < window.end
    : minute >= window.start || minute < window.end;
}

function untilWindowEnd(window, now) {
  const minutes = (window.end - minuteOfDay(now) + 1440) % 1440 || 1440;
  return minutes * 60 - now.getSeconds();
}

function formatDuration(seconds) {
  if (seconds % 3600 === 0) return `${seconds / 3600}h`;
  if (seconds % 60 === 0) return `${seconds / 60}m`;
  return `${Math.round(seconds / 60)}m`;
}

// One line per run, so a silent run can be audited (#307 part 3 D4).
function appendRunLog(where, role, code, result) {
  try {
    const file = path.join(where.root, "patrol", "log", `${role}.log`);
    fs.mkdirSync(path.dirname(file), { recursive: true });
    const changes = result.sinceLast ? result.sinceLast.changes.length : 0;
    fs.appendFileSync(file, `${store.isoLocal(new Date())} exit=${code} changes=${changes} nudges=${(result.nudges || []).length} `
      + `risks=${result.risks.length} notified=${result.notified ? "yes" : "no"}`
      + `${result.next_rule ? ` next=${formatDuration(result.next_after_s)} (${result.next_rule})` : ""}\n`);
  } catch {
    // The log is for audit; failing to write it never fails the patrol.
  }
}

module.exports = { PatrolError, runPatrol, patrol };

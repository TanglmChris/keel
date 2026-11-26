"use strict";
const fs = require("node:fs");
const path = require("node:path");
const store = require("./chat/store");

// Eligibility is derived from durable state. A text argument, role environment
// variable or model-supplied identity cannot designate a different assignment.
function currentTodo(where, role, id) {
  if (!id || path.basename(id) !== id) return false;
  const todo = store.findRecord(where, id);
  if (!todo || todo.id !== id || todo.kind !== "todo" || todo.assignee !== role.role) return false;
  const bindings = Object.entries(store.readRoles(where.root)).filter(([, name]) => name === role.role);
  if (bindings.length !== 1 || bindings[0][0] !== role.worktree) return false;
  const log = store.readLog(where, todo.group);
  const group = store.groupState(log);
  return !group.archived && group.members.has(role.role) && !group.listeners.has(role.role)
    && !log.some(record => record.supersedes === id ||
      (record.target === id && ["done", "edit", "retract"].includes(record.kind)));
}

function migrationPending(where, role) {
  const dir = path.join(where.root, "codex-transitions");
  if (!fs.existsSync(dir)) return false;
  return fs.readdirSync(dir).filter(name => name.endsWith(".json")).some(name => {
    const journal = JSON.parse(fs.readFileSync(path.join(dir, name), "utf8"));
    return journal.plan.role === role && journal.state !== "committed";
  });
}

async function readFinalResult(client, receipt) {
  const page = await client.call("thread/items/list", {
    threadId: receipt.thread, turnId: receipt.turn, sortDirection: "desc", limit: 1,
  });
  const entry = page?.data?.[0];
  const item = entry?.item;
  if (page?.data?.length !== 1 || entry.turnId !== receipt.turn || item?.type !== "agentMessage" ||
      item.phase !== "final_answer" || typeof item.text !== "string") throw Error("no designated final answer");
  let envelope;
  try { envelope = JSON.parse(item.text); } catch { throw Error("no task result envelope"); }
  if (envelope?.taskId !== receipt.record || typeof envelope.result !== "string" || !envelope.result.trim()) {
    throw Error("result envelope does not match this task");
  }
  return {text: envelope.result, role: receipt.role, thread: receipt.thread, turn: receipt.turn};
}

module.exports = {currentTodo, migrationPending, readFinalResult};

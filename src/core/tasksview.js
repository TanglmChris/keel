"use strict";

// Keel 4.2 disposable native tasks view.
//
// Compiles the selected change's tasks.md checklist into an ephemeral
// `keel-native-tasks/v1` payload for the current agent to mirror into
// host-native task tools. The view is compiled fresh on every invocation,
// never persisted, and never a second writer of OpenSpec state; host-side
// disagreement is projection evidence only.

const fs = require("fs");
const path = require("path");
const { resolveContext } = require("./context");
const { parseTasks } = require("./task-contract");

const TASKS_VIEW_VERSION = "keel-native-tasks/v1";

function blockedView(target, reasons, warnings = []) {
  return {
    version: TASKS_VIEW_VERSION,
    status: "blocked",
    target,
    source: null,
    view: null,
    reasons,
    warnings,
  };
}

function compileTasksView(repo, options) {
  const target = options.target;
  if (target !== "claude") {
    return blockedView(
      target,
      [
        `The native tasks view supports the claude target only; `
          + `${target || "<missing>"} remains manual/compatibility-only.`,
      ]
    );
  }

  const context = resolveContext(repo, { change: options.change });
  if (!context.selection || !context.selection.change) {
    return blockedView(
      target,
      context.reasons.length > 0
        ? context.reasons
        : ["Current OpenSpec context selects no change."],
      context.warnings
    );
  }

  const change = context.selection.change;
  const tasksPath = path.join(repo, "openspec", "changes", change, "tasks.md");
  if (!fs.existsSync(tasksPath)) {
    return blockedView(
      target,
      [`Selected change has no tasks artifact: ${change}.`],
      context.warnings
    );
  }
  const records = parseTasks(fs.readFileSync(tasksPath, "utf8"));
  if (records.length === 0) {
    return blockedView(
      target,
      [`Selected change has no checklist task to project: ${change}.`],
      context.warnings
    );
  }

  const view = {
    version: TASKS_VIEW_VERSION,
    change,
    tasks: records.map((record) => ({
      id: record.id,
      title: record.title,
      checked: record.checked,
    })),
    defaultTask: context.selection.task || null,
    fingerprint: context.contract ? context.contract.fingerprint : null,
    mirroring: "current-agent-manual",
  };

  return {
    version: TASKS_VIEW_VERSION,
    status: "ready",
    target,
    source: {
      authority: "OpenSpec",
      owner: `openspec/changes/${change}/tasks.md`,
      change,
    },
    view,
    reasons: [],
    warnings: context.warnings,
  };
}

function renderTasksView(result) {
  const lines = [
    `Keel native tasks view: ${result.status}`,
    `Target: ${result.target}`,
  ];
  if (result.source) lines.push(`Owner: ${result.source.owner}`);
  if (result.view) {
    for (const task of result.view.tasks) {
      const box = task.checked ? "x" : " ";
      const marker = task.id === result.view.defaultTask ? " <- default" : "";
      lines.push(`- [${box}] ${task.id} ${task.title}${marker}`);
    }
    lines.push("Mirroring: the current agent reflects this view manually; "
      + "host-side task state never writes back to OpenSpec.");
  }
  for (const reason of result.reasons) lines.push(`Reason: ${reason}`);
  for (const warning of result.warnings) lines.push(`Warning: ${warning}`);
  return `${lines.join("\n")}\n`;
}

module.exports = {
  TASKS_VIEW_VERSION,
  compileTasksView,
  renderTasksView,
};

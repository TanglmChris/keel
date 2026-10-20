"use strict";

// Keel 4.1.0 one-way native projection contract. Since 5.173.0 (#414) it covers
// continuity and worktree views only: native goals, subagents, and task lists
// need no Keel projection.

const { resolveContext } = require("./context");
const { loadTaskContract } = require("./task-contract");
const { probeCapabilities } = require("./capabilities");

const EVENTS = new Set([
  "startup",
  "resume",
  "compaction",
  "worktree",
]);

function blocked(target, event, reason, warnings = []) {
  return {
    schemaVersion: 1,
    status: "blocked",
    target,
    event,
    source: null,
    capability: {
      level: "manual",
      command: "keel context --json",
    },
    projection: null,
    reasons: [reason],
    warnings,
  };
}

function capabilityKey(event) {
  if (event === "startup") return "continuity.start";
  if (["resume", "compaction"].includes(event)) return "continuity.reinject";
  return "execution.worktree";
}

// The selected task's compiled contract, or the reason there is none. Shared
// with `keel agents brief`, which hands the same task to an external CLI.
function selectTaskContract(repo, options) {
  const context = resolveContext(repo, {
    change: options.change,
    task: options.task,
  });
  if (context.status !== "ready" || !context.selection) {
    return {
      reason: context.reasons.join(" ") || "Current OpenSpec context is not ready.",
      warnings: context.warnings,
    };
  }
  const change = context.selection.change;
  const taskId = context.selection.task;
  if (!taskId) {
    return { reason: "Projection requires one selected executable task.", warnings: context.warnings };
  }
  const loaded = loadTaskContract(repo, change, taskId);
  if (!loaded || loaded.task.checked) {
    return { reason: "Selected durable task owner is missing or already complete.", warnings: context.warnings };
  }
  if (loaded.contract.diagnostics.length > 0) {
    return {
      reason: loaded.contract.diagnostics.map((item) => item.message).join(" "),
      warnings: context.warnings,
    };
  }
  return {
    context,
    change,
    taskId,
    contract: loaded.contract,
    owner: `openspec/changes/${change}/tasks.md#${taskId}`,
    warnings: context.warnings,
  };
}

function projectRuntime(repo, options) {
  const event = options.projectionEvent;
  if (!EVENTS.has(event)) {
    throw new Error(`unsupported projection event: ${event || "<missing>"}`);
  }
  if (!["claude", "codex", "opencode"].includes(options.target)) {
    throw new Error(`unsupported target: ${options.target}`);
  }

  const selected = selectTaskContract(repo, options);
  if (selected.reason) {
    return blocked(options.target, event, selected.reason, selected.warnings);
  }
  const { context, change, taskId, contract, owner } = selected;
  if (
    event === "worktree"
    && (!options.expectedOwner || options.expectedOwner !== owner)
  ) {
    return blocked(
      options.target,
      event,
      `Current checkout owner ${owner} does not match the explicit expected owner.`,
      context.warnings
    );
  }

  const capsule = contract.capsule;
  const capabilities = probeCapabilities(repo, options.target);
  const capability = capabilities.capabilities[capabilityKey(event)];
  const projection = {
    objective: capsule.task.title,
    acceptance: capsule.acceptance,
    stopBoundary: [
      ...capsule.boundaries.stop,
      ...capsule.boundaries.autonomy,
    ],
    nextAction: context.nextAction,
    read: capsule.read,
    touch: capsule.touch,
    verification: capsule.verification,
    evidenceContract: capsule.verification.commands.map(
      (item) => `${item.label}: ${item.check}`
    ),
    owner: capsule.owner,
    fingerprint: contract.fingerprint,
    prohibitions: capsule.prohibitions,
  };

  return {
    schemaVersion: 1,
    status: "ready",
    target: options.target,
    event,
    source: {
      authority: "OpenSpec",
      owner,
      change,
      task: taskId,
    },
    capability,
    contract,
    projection,
    reasons: [],
    warnings: [...context.warnings],
  };
}

function renderProjection(result) {
  const lines = [
    `Keel projection: ${result.status}`,
    `Target: ${result.target}`,
    `Event: ${result.event}`,
  ];
  if (result.source) lines.push(`Owner: ${result.source.owner}`);
  for (const reason of result.reasons) lines.push(`Reason: ${reason}`);
  for (const warning of result.warnings) lines.push(`Warning: ${warning}`);
  return `${lines.join("\n")}\n`;
}

module.exports = {
  projectRuntime,
  renderProjection,
  selectTaskContract,
};

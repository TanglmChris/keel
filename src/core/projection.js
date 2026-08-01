"use strict";

// Keel 4.1.0 one-way native projection contract.

const fs = require("fs");
const path = require("path");

const { readDelegationPolicy } = require("./config");
const { resolveContext } = require("./context");
const { loadTaskContract } = require("./task-contract");
const { probeCapabilities } = require("./capabilities");

const EVENTS = new Set([
  "startup",
  "resume",
  "compaction",
  "goal",
  "task-view",
  "worktree",
  "subagent-start",
  "subagent-stop",
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

// Both refusals are decided before a delegate starts, never inferred from what
// it did. An absent manifest passes every write through silently, so a delegate
// that wrote successfully under one proves nothing about having been checked —
// there is no observable difference afterwards, which is why the condition has
// to be answered here.
function delegationRefusal(repo, delegation) {
  // The policy is read directly rather than through the capsule, because the
  // capsule cannot express the difference this refusal turns on. A tier outside
  // the vocabulary fails closed at the config layer and reaches the capsule as
  // no delegation at all — identical to a repository that declared nothing. One
  // of those should proceed silently and the other must be reported, so the
  // unresolved declaration has to be seen where it still exists.
  const { unknown, accepted } = readDelegationPolicy(repo);
  if (unknown.length > 0) {
    return (
      `Delegation declares tier "${unknown.join(", ")}", which this target `
      + `does not provide. Accepted: ${accepted.join(", ")}. Keel refuses `
      + "rather than substituting a tier, because work would otherwise run at "
      + "a capability nobody declared while reporting success."
    );
  }
  if (!delegation) return null;
  if (!fs.existsSync(path.join(repo, "keel", "guard.json"))) {
    return (
      "Delegation requires an active write guard, and keel/guard.json is "
      + "absent. Without it every write passes through unchecked and looks "
      + "identical to a write the guard allowed. Run `keel gate task-start` "
      + "for the selected task, then delegate."
    );
  }
  return null;
}

function capabilityKey(event) {
  if (event === "startup") return "continuity.start";
  if (["resume", "compaction"].includes(event)) return "continuity.reinject";
  if (event === "goal") return "execution.goal";
  if (event === "task-view") return "execution.task-view";
  if (event === "worktree") return "execution.worktree";
  if (event === "subagent-start") return "delegation.context";
  return "delegation.return";
}

function projectRuntime(repo, options) {
  const event = options.projectionEvent;
  if (!EVENTS.has(event)) {
    throw new Error(`unsupported projection event: ${event || "<missing>"}`);
  }
  if (!["claude", "codex", "opencode"].includes(options.target)) {
    throw new Error(`unsupported target: ${options.target}`);
  }

  const context = resolveContext(repo, {
    change: options.change,
    task: options.task,
  });
  if (context.status !== "ready" || !context.selection) {
    return blocked(
      options.target,
      event,
      context.reasons.join(" ") || "Current OpenSpec context is not ready.",
      context.warnings
    );
  }
  const change = context.selection.change;
  const taskId = context.selection.task;
  if (!taskId) {
    return blocked(
      options.target,
      event,
      "Projection requires one selected executable task.",
      context.warnings
    );
  }
  const loaded = loadTaskContract(repo, change, taskId);
  if (!loaded || loaded.task.checked) {
    return blocked(
      options.target,
      event,
      "Selected durable task owner is missing or already complete.",
      context.warnings
    );
  }
  if (loaded.contract.diagnostics.length > 0) {
    return blocked(
      options.target,
      event,
      loaded.contract.diagnostics.map((item) => item.message).join(" "),
      context.warnings
    );
  }

  const owner = `openspec/changes/${change}/tasks.md#${taskId}`;
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

  const authorization = new Set(options.authorizations || []);
  const requiredAuthorization =
    event === "goal"
      ? "goal"
      : event === "task-view"
        ? "task-view"
        : event.startsWith("subagent-")
          ? "subagent"
          : null;
  if (requiredAuthorization && !authorization.has(requiredAuthorization)) {
    return blocked(
      options.target,
      event,
      `${event} projection requires explicit ${requiredAuthorization} authorization.`,
      context.warnings
    );
  }

  const contract = loaded.contract;
  const capsule = contract.capsule;
  const capabilities = probeCapabilities(repo, options.target);
  const capability = capabilities.capabilities[capabilityKey(event)];
  const warnings = [...context.warnings];
  if (options.nativeComplete) {
    warnings.push(
      "Native completion was ignored; only task-complete plus current-agent "
        + "durable updates can complete OpenSpec work."
    );
  }
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
    helperAuthority: capsule.helperAuthority,
    fingerprint: contract.fingerprint,
    prohibitions: capsule.prohibitions,
  };
  if (event === "subagent-stop") {
    projection.returnAuthority = "report-and-evidence-only";
  }
  // Delegation extends the brief Keel already publishes rather than adding a
  // carrier beside the host's own agent interface. The host spawns; this is the
  // one-way view of OpenSpec it is handed.
  if (event === "subagent-start") {
    const refusal = delegationRefusal(repo, capsule.delegation);
    if (refusal) return blocked(options.target, event, refusal, warnings);
  }
  if (event === "subagent-start" && capsule.delegation) {
    projection.delegation = {
      tier: capsule.delegation.tier,
      source: capsule.delegation.source,
      writeBoundary: capsule.touch,
      note:
        "Keel carries the declared tier and does not select a model; the "
        + "target resolves it. Keel cannot observe which model executed, so "
        + "the tier is what is recorded and never a claim about what ran.",
    };
  }

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
    warnings,
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
};

"use strict";

// Keel 4.1.0 single-task native goal projection contract.
//
// Compiles one passing `keel-task-capsule/v1` into an ephemeral
// `keel-native-goal/v1` projection for a supported native runtime. The
// projection is never written as Keel-owned state; OpenSpec, Git, the capsule
// fingerprint, and deterministic gates remain durable authority.

const { resolveContext } = require("./context");
const { loadTaskContract } = require("./task-contract");
const { probeCapabilities } = require("./capabilities");

const GOAL_VERSION = "keel-native-goal/v1";
const CLAUDE_CONDITION_LIMIT = 4000;
const SUPPORTED_GOAL_TARGETS = new Set(["codex", "claude"]);
const TERMINAL_STATES = ["complete", "blocked", "paused"];
const EVIDENCE_PRESENTATION = [
  "Surface every Command result and gate outcome in the transcript before any success claim.",
  "Native evaluator success alone never marks or reports the OpenSpec task complete.",
  "Achievement requires matching change/task/fingerprint, Acceptance demonstrated by the named Commands, passing Review, passing task-complete, and the durably checked task checkbox.",
];

function blockedGoal(target, reason, warnings = [], extra = {}) {
  return {
    version: GOAL_VERSION,
    status: "blocked",
    target,
    source: null,
    capability: null,
    goal: null,
    reasons: [reason],
    warnings,
    ...extra,
  };
}

function renderCondition(goal) {
  const lines = [
    `Goal: complete exactly one OpenSpec task — ${goal.owner} (fingerprint ${goal.fingerprint.value}).`,
    `Objective: ${goal.objective}`,
    "Acceptance (all must be demonstrated by the named Commands):",
    ...goal.acceptance.map((item) => `- ${item}`),
    "Commands:",
    ...goal.commands.map((item) => `- ${item}`),
    `Verification strategy: ${goal.verificationStrategy}.`,
    `Write boundary (Touch): ${goal.touch.join(", ")}.`,
    "Stop/Autonomy boundary:",
    ...goal.stopBoundary.map((item) => `- ${item}`),
    "Ownership: the current agent is the sole writer and owns Review, gate invocation, the task checkbox, and completion.",
    "Done only when: task-complete passes and the current agent has durably checked the task; then stop and require a new explicit authorization before any next task.",
  ];
  return lines.join("\n");
}

function compileGoalProjection(repo, options) {
  const target = options.target;
  if (!SUPPORTED_GOAL_TARGETS.has(target)) {
    return blockedGoal(
      target,
      `Native single-task goal execution supports codex and claude only; `
        + `${target || "<missing>"} remains manual/compatibility-only.`
    );
  }
  if (!options.change || !options.task) {
    return blockedGoal(
      target,
      "Native goal activation requires one explicit --change and --task "
        + "selection; ambiguous, multiple, or task-group activation is rejected."
    );
  }

  const context = resolveContext(repo, {
    change: options.change,
    task: options.task,
  });
  if (context.status !== "ready" || !context.selection) {
    return blockedGoal(
      target,
      context.reasons.join(" ") || "Current OpenSpec context is not ready.",
      context.warnings
    );
  }
  const change = context.selection.change;
  const taskId = context.selection.task;
  if (!taskId) {
    return blockedGoal(
      target,
      "Native goal activation requires one selected executable task, not a "
        + "change backlog or contiguous task group.",
      context.warnings
    );
  }

  const loaded = loadTaskContract(repo, change, taskId);
  if (!loaded) {
    return blockedGoal(
      target,
      `Selected durable task owner openspec/changes/${change}/tasks.md#${taskId} `
        + "is missing.",
      context.warnings
    );
  }
  if (loaded.task.checked) {
    return blockedGoal(
      target,
      "Selected task is already complete; a later task requires a new explicit "
        + "user authorization and a new start fingerprint.",
      context.warnings
    );
  }
  if (loaded.contract.diagnostics.length > 0) {
    return blockedGoal(
      target,
      loaded.contract.diagnostics.map((item) => item.message).join(" "),
      context.warnings
    );
  }

  const contract = loaded.contract;
  const capsule = contract.capsule;
  const owner = `openspec/changes/${change}/tasks.md#${taskId}`;

  // Continuity is reconstructed from durable OpenSpec/Git authority, never a
  // Keel cursor or cache: a resume passes the previously recorded owner and
  // fingerprint, and any divergence hard-stops rather than silently rebinding.
  if (options.expectedOwner && options.expectedOwner !== owner) {
    return blockedGoal(
      target,
      `Recorded authorization owns ${options.expectedOwner}, but the current `
        + `OpenSpec selection is ${owner}; checkout divergence requires new `
        + "explicit authorization, not automatic rebinding.",
      context.warnings
    );
  }
  if (
    options.expectedFingerprint
    && options.expectedFingerprint !== contract.fingerprint.value
  ) {
    return blockedGoal(
      target,
      `Recompiled capsule fingerprint ${contract.fingerprint.value} does not `
        + `match the recorded authorization ${options.expectedFingerprint}; `
        + "fingerprint drift requires reauthorization before any product write.",
      context.warnings
    );
  }

  const capabilities = probeCapabilities(repo, target);
  const capability = capabilities.capabilities["execution.goal"];

  const goal = {
    version: GOAL_VERSION,
    target,
    change,
    task: taskId,
    fingerprint: contract.fingerprint,
    objective: capsule.task.title,
    acceptance: capsule.acceptance,
    commands: capsule.verification.commands.map(
      (item) => `${item.label}: ${item.check}`
    ),
    verificationStrategy: capsule.verification.strategy,
    touch: capsule.touch,
    stopBoundary: [...capsule.boundaries.stop, ...capsule.boundaries.autonomy],
    owner: capsule.owner,
    ownership: "current-agent-sole-writer",
    helperPolicy: capsule.helperAuthority,
    terminalStates: TERMINAL_STATES,
    evidencePresentation: EVIDENCE_PRESENTATION,
    authorizationEvidence: {
      field: "Automation authorization: single-task",
      target,
      change,
      task: taskId,
      fingerprint: contract.fingerprint.value,
    },
    prohibitions: capsule.prohibitions,
  };
  goal.owner = owner;
  const conditionText = renderCondition(goal);
  goal.condition = conditionText;
  goal.conditionLength = conditionText.length;

  if (target === "claude" && conditionText.length > CLAUDE_CONDITION_LIMIT) {
    return blockedGoal(
      target,
      `Compiled goal condition is ${conditionText.length} characters, above the `
        + `Claude ${CLAUDE_CONDITION_LIMIT}-character limit; refusing native `
        + "activation rather than omitting Acceptance, fingerprint, or stop "
        + "authority. Use the manual current-agent loop instead.",
      context.warnings,
      { conditionLength: conditionText.length }
    );
  }

  return {
    version: GOAL_VERSION,
    status: "ready",
    target,
    source: { authority: "OpenSpec", owner, change, task: taskId },
    capability,
    goal,
    reasons: [],
    warnings: context.warnings,
  };
}

function renderGoalProjection(result) {
  const lines = [
    `Keel native goal: ${result.status}`,
    `Target: ${result.target}`,
  ];
  if (result.source) lines.push(`Owner: ${result.source.owner}`);
  if (result.goal) {
    lines.push(`Fingerprint: ${result.goal.fingerprint.value}`);
    lines.push(`Condition length: ${result.goal.conditionLength}`);
  }
  for (const reason of result.reasons || []) lines.push(`Reason: ${reason}`);
  for (const warning of result.warnings || []) lines.push(`Warning: ${warning}`);
  return `${lines.join("\n")}\n`;
}

module.exports = {
  GOAL_VERSION,
  CLAUDE_CONDITION_LIMIT,
  SUPPORTED_GOAL_TARGETS,
  compileGoalProjection,
  renderGoalProjection,
};

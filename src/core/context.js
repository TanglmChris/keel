"use strict";

// Keel 4.1.0 stateless continuity contract.

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const {
  ACCEPTED_REVIEW_STATUSES,
  compileTaskContract,
  field,
  parseTasks,
} = require("./task-contract");

const NEXT_ACTIONS = new Set([
  "discuss",
  "author",
  "task-start",
  "task-complete",
  "change-close",
  "none",
]);

function taskRecords(tasksPath) {
  return parseTasks(fs.readFileSync(tasksPath, "utf8")).map((task) => ({
    ...task,
    complete: task.checked,
  }));
}

function result(status, selection, nextAction, read, reasons = [], contract = null) {
  const context = {
    schemaVersion: 1,
    status,
    selection,
    nextAction: { kind: nextAction },
    read,
    reasons,
    warnings: [],
  };
  if (contract) {
    Object.defineProperty(context, "contract", {
      value: contract,
      enumerable: false,
    });
  }
  return context;
}

function blocked(reason, read = []) {
  return result("blocked", null, "none", read, [reason]);
}

function relativePath(repo, target) {
  return path.relative(repo, target).split(path.sep).join("/");
}

function recordedFingerprint(record) {
  const evidence = field(record, "Evidence");
  const match = evidence.match(
    /^\s*-\s*Contract:\s*.*?keel-task-capsule\/v1.*?sha-?256[\s:`]*([a-f0-9]{64})/im
  );
  return match ? match[1].toLowerCase() : null;
}

function taskHasCompletionEvidence(record, contract) {
  const evidence = field(record, "Evidence");
  const commandIds = contract.capsule.verification.commands.map(
    (command) => command.label
  );
  const evidenceIds = new Set(
    [...evidence.matchAll(/^\s*-\s*(M\d+):\s+(?!pending\b)\S.*$/gim)].map(
      (match) => match[1]
    )
  );
  const reviewPassed = new RegExp(
    `^\\s*-\\s*Status:\\s*(?:${ACCEPTED_REVIEW_STATUSES.join("|")})\\s*$`,
    "im"
  ).test(evidence);
  return (
    commandIds.length > 0
    && commandIds.every((commandId) => evidenceIds.has(commandId))
    && reviewPassed
  );
}

function taskSelection(repo, change, record, source, requestedAction = null) {
  const tasksPath = path.join(repo, "openspec", "changes", change, "tasks.md");
  const contract = compileTaskContract(repo, change, record);
  if (contract.diagnostics.length > 0) {
    return blocked(
      `Task contract is invalid for ${change}#${record.id}: ${contract.diagnostics
        .map((item) => item.message)
        .join(" ")}`,
      [relativePath(repo, tasksPath)]
    );
  }
  const anchor = recordedFingerprint(record);
  if (anchor && anchor !== contract.fingerprint.value) {
    return blocked(
      `Task contract fingerprint drift for ${change}#${record.id}: recorded `
        + `sha256:${anchor}, current sha256:${contract.fingerprint.value}.`,
      [relativePath(repo, tasksPath)]
    );
  }
  return result(
    "ready",
    { source, change, task: record.id },
    requestedAction || (
      taskHasCompletionEvidence(record, contract)
        ? "task-complete"
        : "task-start"
    ),
    [relativePath(repo, tasksPath)],
    [],
    contract
  );
}

function changeArtifacts(changePath) {
  const proposalPath = path.join(changePath, "proposal.md");
  const designPath = path.join(changePath, "design.md");
  const specsPath = path.join(changePath, "specs");
  return {
    proposal: fs.existsSync(proposalPath),
    design: fs.existsSync(designPath),
    specs: fs.existsSync(specsPath),
  };
}

function storageOnly(context) {
  Object.defineProperty(context, "storageOnly", {
    value: true,
    enumerable: false,
  });
  return context;
}

function selectionForChange(repo, change, source) {
  const tasksPath = path.join(repo, "openspec", "changes", change, "tasks.md");
  if (!fs.existsSync(tasksPath)) {
    const changePath = path.dirname(tasksPath);
    if (!fs.existsSync(changePath)) {
      return blocked(`Change does not exist: ${change}`);
    }
    const artifacts = changeArtifacts(changePath);
    if (artifacts.proposal && artifacts.design && artifacts.specs) {
      return blocked(
        `Authored change has no tasks artifact: ${change}.`,
        [relativePath(repo, changePath)]
      );
    }
    return result(
      "ready",
      { source, change, task: null },
      artifacts.proposal || artifacts.design || artifacts.specs ? "author" : "discuss",
      [relativePath(repo, changePath)]
    );
  }

  const records = taskRecords(tasksPath);
  if (records.length === 0) {
    const artifacts = changeArtifacts(path.dirname(tasksPath));
    if (!artifacts.proposal && !artifacts.design && !artifacts.specs) {
      return storageOnly(result(
        "ready",
        { source, change, task: null },
        "none",
        [relativePath(repo, tasksPath)],
        [`Storage-only backlog has no executable task: ${change}.`]
      ));
    }
    if (artifacts.proposal && artifacts.design && artifacts.specs) {
      return blocked(
        `Authored change has an invalid tasks artifact with no executable task: ${change}.`,
        [relativePath(repo, tasksPath)]
      );
    }
    return result(
      "ready",
      { source, change, task: null },
      "author",
      [relativePath(repo, tasksPath)]
    );
  }
  const next = records.find((candidate) => !candidate.complete);
  if (!next) {
    return result(
      "ready",
      { source, change, task: null },
      "change-close",
      [relativePath(repo, tasksPath)]
    );
  }
  return taskSelection(repo, change, next, source);
}

function resolveExplicit(repo, change, task) {
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(change)) {
    return blocked(`Invalid explicit change: ${change}`);
  }
  if (task && !/^\d+(?:\.\d+)+$/.test(task)) {
    return blocked(`Invalid explicit task: ${task}`);
  }
  if (!task) {
    return selectionForChange(repo, change, "explicit");
  }

  const tasksPath = path.join(repo, "openspec", "changes", change, "tasks.md");
  if (!fs.existsSync(tasksPath)) {
    return blocked(`Explicit change does not exist: ${change}`);
  }
  const records = taskRecords(tasksPath);
  const record = records.find((candidate) => candidate.id === task);
  if (!record) {
    return blocked(`Explicit task does not exist: ${change}#${task}`);
  }
  if (record.complete) {
    return blocked(`Explicit task is already complete: ${change}#${task}`);
  }
  return taskSelection(repo, change, record, "explicit");
}

function activeChanges(repo) {
  const changesPath = path.join(repo, "openspec", "changes");
  if (!fs.existsSync(changesPath)) return [];
  return fs
    .readdirSync(changesPath, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name !== "archive")
    .map((entry) => entry.name)
    .sort();
}

function inferContext(repo) {
  const changes = activeChanges(repo);
  if (changes.length === 0) {
    return result(
      "idle",
      null,
      "none",
      [],
      ["No active OpenSpec change was found."]
    );
  }
  const contexts = changes.map((change) => selectionForChange(repo, change, "inferred"));
  const storage = contexts.filter((context) => context.storageOnly);
  const candidates = contexts.filter((context) => !context.storageOnly);
  const warnings = storage.map(
    (context) =>
      `Storage-only backlog ignored during inference: ${context.selection.change}.`
  );
  if (candidates.length === 0) {
    return result(
      "idle",
      null,
      "none",
      storage.flatMap((context) => context.read),
      ["No actionable OpenSpec change was found."]
    );
  }
  if (candidates.length > 1) {
    return result(
      "ambiguous",
      null,
      "none",
      candidates.flatMap((context) => context.read),
      [
        "Multiple active OpenSpec changes are plausible: "
          + candidates
            .map((context) => context.selection?.change || context.read[0])
            .join(", "),
      ]
    );
  }
  const context = candidates[0];
  context.warnings.push(...warnings);
  return context;
}

function parseScalar(value) {
  const trimmed = value.trim();
  if (
    (trimmed.startsWith('"') && trimmed.endsWith('"'))
    || (trimmed.startsWith("'") && trimmed.endsWith("'"))
  ) {
    return trimmed.slice(1, -1);
  }
  return trimmed;
}

function readHandoff(repo) {
  const handoffPath = path.join(repo, "keel", "HANDOFF.md");
  if (!fs.existsSync(handoffPath)) return null;

  const buffer = fs.readFileSync(handoffPath);
  let content;
  try {
    content = new TextDecoder("utf-8", { fatal: true }).decode(buffer);
  } catch {
    throw new Error("keel/HANDOFF.md is not valid UTF-8.");
  }
  if (!content.startsWith("---\n") && !content.startsWith("---\r\n")) {
    return { kind: "legacy", path: handoffPath };
  }

  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)([\s\S]*)$/);
  if (!match) {
    throw new Error("keel/HANDOFF.md has unterminated YAML front matter.");
  }
  if (match[2].trim()) {
    return {
      kind: "invalid",
      path: handoffPath,
      reason: "HANDOFF v1 must not contain body content.",
    };
  }

  const fields = {};
  for (const line of match[1].split(/\r?\n/)) {
    if (!line.trim()) continue;
    const field = line.match(/^([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*$/);
    if (!field) {
      throw new Error("keel/HANDOFF.md contains invalid YAML front matter.");
    }
    if (Object.prototype.hasOwnProperty.call(fields, field[1])) {
      return {
        kind: "invalid",
        path: handoffPath,
        reason: `HANDOFF v1 repeats field: ${field[1]}`,
      };
    }
    fields[field[1]] = parseScalar(field[2]);
  }

  if (fields.schema !== "keel-handoff/v1") {
    return fields.schema
      ? {
          kind: "invalid",
          path: handoffPath,
          reason: `Unsupported HANDOFF schema: ${fields.schema}`,
        }
      : { kind: "legacy", path: handoffPath };
  }
  const expected = ["schema", "owner", "action", "reason"];
  const extras = Object.keys(fields).filter((key) => !expected.includes(key));
  const missing = expected.filter((key) => !fields[key]);
  if (extras.length > 0 || missing.length > 0) {
    const details = [];
    if (missing.length > 0) details.push(`missing ${missing.join(", ")}`);
    if (extras.length > 0) details.push(`unexpected ${extras.join(", ")}`);
    return {
      kind: "invalid",
      path: handoffPath,
      reason: `Invalid HANDOFF v1 fields: ${details.join("; ")}`,
    };
  }
  if (!NEXT_ACTIONS.has(fields.action) || fields.action === "none") {
    return {
      kind: "invalid",
      path: handoffPath,
      reason: `Unsupported HANDOFF action: ${fields.action}`,
    };
  }
  return { kind: "v1", path: handoffPath, fields };
}

function resolveHandoff(repo, handoff) {
  const read = [relativePath(repo, handoff.path)];
  if (handoff.kind === "legacy") {
    return result(
      "blocked",
      null,
      "none",
      read,
      [
        "Legacy HANDOFF is preserved; migrate it explicitly to keel-handoff/v1 "
          + "or clear it with keel context --clear-handoff.",
      ]
    );
  }
  if (handoff.kind === "invalid") {
    return result("blocked", null, "none", read, [handoff.reason]);
  }

  const owner = handoff.fields.owner.match(
    /^openspec\/changes\/([A-Za-z0-9][A-Za-z0-9._-]*)\/(proposal|design|tasks)\.md(?:#(.+))?$/
  );
  if (!owner) {
    return result(
      "blocked",
      null,
      "none",
      read,
      [`HANDOFF owner is not a supported OpenSpec pointer: ${handoff.fields.owner}`]
    );
  }
  const [, change, artifact, anchor] = owner;
  const ownerPath = path.join(
    repo,
    "openspec",
    "changes",
    change,
    `${artifact}.md`
  );
  if (!fs.existsSync(ownerPath)) {
    return result(
      "blocked",
      null,
      "none",
      read,
      [`HANDOFF owner is missing: ${handoff.fields.owner}`]
    );
  }

  let task = null;
  if (artifact === "tasks" && anchor && /^\d+(?:\.\d+)+$/.test(anchor)) {
    task = anchor;
    const record = taskRecords(ownerPath).find((candidate) => candidate.id === task);
    if (!record) {
      return result(
        "blocked",
        null,
        "none",
        read,
        [`HANDOFF task owner is missing: ${handoff.fields.owner}`]
      );
    }
    if (record.complete) {
      return result(
        "blocked",
        null,
        "none",
        read,
        [`HANDOFF task owner is already complete: ${handoff.fields.owner}`]
      );
    }
    const selection = taskSelection(
      repo,
      change,
      record,
      "handoff",
      handoff.fields.action
    );
    selection.read = [...selection.read, ...read];
    if (selection.status !== "ready") {
      return selection;
    }
    selection.reasons.push(handoff.fields.reason);
    return selection;
  }
  if (
    ["task-start", "task-complete"].includes(handoff.fields.action)
    && task === null
  ) {
    return result(
      "blocked",
      null,
      "none",
      read,
      [`HANDOFF action ${handoff.fields.action} requires a numeric task anchor.`]
    );
  }

  return result(
    "ready",
    { source: "handoff", change, task },
    handoff.fields.action,
    [relativePath(repo, ownerPath), ...read],
    [handoff.fields.reason]
  );
}

function gitWarnings(repo) {
  const git = spawnSync(
    "git",
    ["status", "--short", "--untracked-files=all"],
    { cwd: repo, encoding: "utf8" }
  );
  if (git.error || git.status !== 0 || !git.stdout.trim()) return [];
  const paths = git.stdout
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => line.slice(3).trim());
  return paths.length > 0
    ? [`Working tree has uncommitted paths (selection-neutral): ${paths.join(", ")}`]
    : [];
}

function resolveContext(repo, options) {
  let context;
  if (options.change) {
    context = resolveExplicit(repo, options.change, options.task);
  } else {
    const handoff = readHandoff(repo);
    context = handoff ? resolveHandoff(repo, handoff) : inferContext(repo);
  }
  context.warnings.push(...gitWarnings(repo));
  return context;
}

function renderContext(result) {
  const lines = [
    `Keel context: ${result.status}`,
    `Next action: ${result.nextAction.kind}`,
  ];
  if (result.selection) {
    lines.push(
      `Selection: ${result.selection.change}`
        + (result.selection.task ? `#${result.selection.task}` : "")
        + ` (${result.selection.source})`
    );
  }
  for (const reason of result.reasons) lines.push(`Reason: ${reason}`);
  for (const warning of result.warnings) lines.push(`Warning: ${warning}`);
  return `${lines.join("\n")}\n`;
}

module.exports = {
  renderContext,
  resolveContext,
};

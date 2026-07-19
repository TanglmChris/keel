"use strict";

// Keel 4.x write-guard contract: an explicit, fingerprinted, disposable
// enforcement manifest for exactly one task. The manifest is never selection,
// continuity, or completion authority; only its presence authorizes the
// plugin PreToolUse hook to deny out-of-Touch file edits, and every broken
// state fails closed through guard status while absence changes nothing.

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const { loadTaskContract } = require("./task-contract");

const MANIFEST_SCHEMA = "keel-write-guard/v1";

class GuardInputError extends Error {}

function manifestFile(repo) {
  return path.join(repo, "keel", "guard.json");
}

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function guardResult(subcommand, status, extra = {}) {
  return {
    schemaVersion: 1,
    command: "guard",
    subcommand,
    status,
    manifestPath: "keel/guard.json",
    problems: [],
    warnings: [
      "The guard manifest is a disposable enforcement pointer; OpenSpec and "
        + "Git remain the only durable authority and selection never derives "
        + "from it.",
    ],
    ...extra,
  };
}

function authorityPaths(repo, change, contract) {
  const paths = new Set([`openspec/changes/${change}/tasks.md`]);
  for (const item of contract.capsule.authority) {
    const source = String(item.source || "").split("#")[0].trim();
    if (source && fs.existsSync(path.join(repo, source))) {
      paths.add(source.replace(/\\/g, "/"));
    }
  }
  return [...paths].sort();
}

function hashAuthority(repo, paths) {
  return paths.map((relative) => ({
    path: relative,
    sha256: sha256(fs.readFileSync(path.join(repo, relative))),
  }));
}

function readManifest(repo) {
  const file = manifestFile(repo);
  if (!fs.existsSync(file)) return { state: "absent" };
  let manifest;
  try {
    manifest = JSON.parse(fs.readFileSync(file, "utf8"));
  } catch {
    return {
      state: "invalid",
      problems: [
        {
          code: "invalid-manifest",
          message:
            "keel/guard.json is unreadable or not JSON; run `keel guard "
            + "clear` and reauthorize with `keel guard start`.",
        },
      ],
    };
  }
  const shapeErrors = [];
  if (manifest.schema !== MANIFEST_SCHEMA) {
    shapeErrors.push(`schema must be ${MANIFEST_SCHEMA}`);
  }
  if (typeof manifest.change !== "string" || !manifest.change) {
    shapeErrors.push("change must be a non-empty string");
  }
  if (typeof manifest.task !== "string" || !manifest.task) {
    shapeErrors.push("task must be a non-empty string");
  }
  if (
    !manifest.fingerprint
    || manifest.fingerprint.algorithm !== "sha256"
    || !/^[0-9a-f]{64}$/.test(String(manifest.fingerprint.value || ""))
  ) {
    shapeErrors.push("fingerprint must record a sha256 value");
  }
  if (
    !Array.isArray(manifest.touch)
    || manifest.touch.length === 0
    || manifest.touch.some((item) => typeof item !== "string" || !item)
  ) {
    shapeErrors.push("touch must be a non-empty string list");
  }
  if (
    !Array.isArray(manifest.authority)
    || manifest.authority.length === 0
    || manifest.authority.some(
      (item) =>
        !item
        || typeof item.path !== "string"
        || !/^[0-9a-f]{64}$/.test(String(item.sha256 || ""))
    )
  ) {
    shapeErrors.push("authority must list hashed source files");
  }
  if (shapeErrors.length > 0) {
    return {
      state: "invalid",
      problems: shapeErrors.map((message) => ({
        code: "invalid-manifest",
        message:
          `keel/guard.json is invalid (${message}); run \`keel guard clear\` `
          + "and reauthorize with `keel guard start`.",
      })),
    };
  }
  return { state: "ok", manifest };
}

function startGuard(repo, options) {
  if (!options.change || !options.task) {
    throw new GuardInputError("guard start requires --change and --task");
  }
  const loaded = loadTaskContract(repo, options.change, options.task);
  if (!loaded) {
    throw new GuardInputError(
      `task ${options.change}#${options.task} does not exist`
    );
  }
  const problems = [];
  if (loaded.task.checked) {
    problems.push({
      code: "task-completed",
      message:
        `Task ${options.change}#${options.task} is already checked complete; `
        + "a completed task cannot be guarded. Run `keel guard clear` and "
        + "authorize a new task explicitly.",
    });
  }
  problems.push(...loaded.contract.diagnostics);

  const existing = readManifest(repo);
  if (
    problems.length === 0
    && existing.state === "ok"
    && (
      existing.manifest.change !== options.change
      || existing.manifest.task !== options.task
    )
    && !options.force
  ) {
    problems.push({
      code: "guard-active",
      message:
        `An active guard already covers ${existing.manifest.change}#`
        + `${existing.manifest.task}; run \`keel guard clear\` first or pass `
        + "--force to replace it.",
    });
  }
  if (problems.length > 0) {
    const refused = guardResult("start", "refused");
    refused.problems = problems;
    return refused;
  }

  const paths = authorityPaths(repo, options.change, loaded.contract);
  const manifest = {
    schema: MANIFEST_SCHEMA,
    change: options.change,
    task: options.task,
    fingerprint: loaded.contract.fingerprint,
    touch: loaded.contract.capsule.touch,
    authority: hashAuthority(repo, paths),
  };
  fs.mkdirSync(path.join(repo, "keel"), { recursive: true });
  fs.writeFileSync(
    manifestFile(repo),
    `${JSON.stringify(manifest, null, 2)}\n`,
    "utf8"
  );
  return guardResult("start", "started", { manifest });
}

function guardStatus(repo) {
  const existing = readManifest(repo);
  if (existing.state === "absent") {
    return guardResult("status", "absent");
  }
  if (existing.state === "invalid") {
    const invalid = guardResult("status", "invalid");
    invalid.problems = existing.problems;
    return invalid;
  }
  const manifest = existing.manifest;
  const problems = [];
  const loaded = loadTaskContract(repo, manifest.change, manifest.task);
  if (!loaded) {
    problems.push({
      code: "authority-drift",
      message:
        `Guarded task ${manifest.change}#${manifest.task} no longer resolves; `
        + "reauthorize through `keel gate task-start` and `keel guard start`.",
    });
    const drifted = guardResult("status", "drifted", { manifest });
    drifted.problems = problems;
    return drifted;
  }
  if (loaded.task.checked) {
    const completed = guardResult("status", "completed", { manifest });
    completed.problems = [
      {
        code: "task-completed",
        message:
          `Guarded task ${manifest.change}#${manifest.task} is checked `
          + "complete; run `keel guard clear` before authorizing new work.",
      },
    ];
    return completed;
  }
  if (loaded.contract.diagnostics.length > 0) {
    problems.push(...loaded.contract.diagnostics);
  } else if (
    loaded.contract.fingerprint.value !== manifest.fingerprint.value
  ) {
    problems.push({
      code: "fingerprint-drift",
      message:
        "The recompiled capsule fingerprint no longer matches the guard; "
        + "reauthorize through `keel gate task-start` and `keel guard start`.",
    });
  }
  for (const entry of manifest.authority) {
    const file = path.join(repo, entry.path);
    if (!fs.existsSync(file) || sha256(fs.readFileSync(file)) !== entry.sha256) {
      problems.push({
        code: "authority-drift",
        message:
          `Recorded authority hash for ${entry.path} no longer matches; `
          + "reauthorize through `keel gate task-start` and `keel guard start`.",
      });
    }
  }
  if (problems.length > 0) {
    const drifted = guardResult("status", "drifted", { manifest });
    drifted.problems = problems;
    return drifted;
  }
  return guardResult("status", "active", { manifest });
}

function clearGuard(repo) {
  const file = manifestFile(repo);
  if (!fs.existsSync(file)) {
    return guardResult("clear", "absent");
  }
  fs.rmSync(file, { force: true });
  return guardResult("clear", "cleared");
}

function renderGuard(result) {
  const lines = [
    `Keel guard: ${result.subcommand}`,
    `Status: ${result.status}`,
  ];
  if (result.manifest) {
    lines.push(
      `Selection: ${result.manifest.change}#${result.manifest.task}`,
      `Fingerprint: ${result.manifest.fingerprint.algorithm}:`
        + result.manifest.fingerprint.value
    );
  }
  for (const item of result.problems) lines.push(`Problem: ${item.message}`);
  for (const warning of result.warnings) lines.push(`Warning: ${warning}`);
  return `${lines.join("\n")}\n`;
}

module.exports = {
  GuardInputError,
  MANIFEST_SCHEMA,
  clearGuard,
  guardStatus,
  readManifest,
  renderGuard,
  startGuard,
};

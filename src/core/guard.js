"use strict";

// Keel 4.x write-guard contract: an explicit, fingerprinted, disposable
// enforcement manifest for exactly one task. The manifest is never selection,
// continuity, or completion authority; only its presence authorizes the
// plugin PreToolUse hook to deny out-of-Touch file edits, and every broken
// state fails closed through guard status while absence changes nothing.

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const { loadTaskContract } = require("./task-contract");

// Nothing rewrites backslashes here. Git emits forward slashes on every
// platform, so the rewrite normalized a separator that never arrives while
// turning `\346` into `/346`, which is how a path declared on the first line
// of Touch was reported as outside Touch (issue #40).
//
// This lives here rather than in gates.js because both the task-start record
// and the completion comparison read it, and gates.js already requires this
// module. One implementation is the point: a baseline and a comparison that
// disagreed about what "dirty" means, or about how a rename is represented,
// would attribute a path nobody wrote.
function gitPaths(repo) {
  const status = spawnSync(
    "git",
    ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
    { cwd: repo, encoding: "utf8" }
  );
  if (status.error || status.status !== 0) return [];
  // Each record is `XY <path>`, NUL-terminated. A rename or copy is followed
  // by a second bare field holding its other endpoint — the new path first in
  // `-z`, the reverse of the ` -> ` line format. The order is immaterial:
  // both endpoints are attributed, so a rename whose paths are both in Touch
  // is not a false outside-Touch failure.
  const fields = status.stdout.split("\0").filter(Boolean);
  const paths = [];
  for (let index = 0; index < fields.length; index += 1) {
    const record = fields[index];
    paths.push(record.slice(3));
    if (record[0] === "R" || record[0] === "C") {
      index += 1;
      if (index < fields.length) paths.push(fields[index]);
    }
  }
  return paths;
}

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
      // The status describes a file Keel wrote. Whether anything reads that
      // file is a target-side fact: enforcement runs as a runtime hook the
      // host loads, and a host that loaded different plugins keeps them for
      // the life of its session. Reporting `started` as though it were a probe
      // result is the same inference `--doctor` already refuses to make.
      "This status describes the manifest only. Enforcement runs as a runtime "
        + "hook in the host, which Keel cannot observe from the repository, so "
        + "a written manifest is not evidence that any write was checked.",
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
  // Optional on purpose. A manifest written before this field existed, and one
  // written by a Keel that omits it, are both valid; what they are not is
  // evidence that nothing was dirty. The consumer distinguishes absent from
  // empty, so an empty list means "nothing was dirty" and an absent one means
  // "nobody looked".
  if (
    manifest.startedDirty !== undefined
    && (!Array.isArray(manifest.startedDirty)
      || manifest.startedDirty.some((item) => typeof item !== "string"))
  ) {
    shapeErrors.push("startedDirty must be a string list when present");
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
  // Read before the manifest is written, so the manifest is never in its own
  // record and cannot be attributed to the task it authorizes.
  const startedDirty = gitPaths(repo);
  const manifest = {
    schema: MANIFEST_SCHEMA,
    change: options.change,
    task: options.task,
    fingerprint: loaded.contract.fingerprint,
    touch: loaded.contract.capsule.touch,
    authority: hashAuthority(repo, paths),
    startedDirty,
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
    // `loadTaskContract` returns null for two unrelated reasons — the tasks
    // file is not there, or the task id is not in it — and only one of them
    // has a reauthorization to perform. Telling the reader to reauthorize a
    // change that has been archived sends them to `keel gate task-start`,
    // which reports a missing tasks file, and to `keel guard start`, which
    // reports that the task does not exist; neither names `keel guard clear`,
    // which is the only action that resolves it.
    //
    // The change *directory* is the test, not the tasks file, and it is the
    // same object `plugins/keel/scripts/pretooluse-guard.js` tests for the
    // same question. Two surfaces deciding it by different means would
    // eventually disagree about a state a reader is looking at from both. It
    // also leaves a live change whose tasks.md is absent — mid-authoring — on
    // the reauthorize path, where reauthorizing genuinely is the way out.
    const changeDir = path.join(repo, "openspec", "changes", manifest.change);
    problems.push(
      fs.existsSync(changeDir)
        ? {
          code: "authority-drift",
          message:
            `Guarded task ${manifest.change}#${manifest.task} no longer `
            + "resolves; reauthorize through `keel gate task-start` and "
            + "`keel guard start`.",
        }
        : {
          code: "stale-manifest",
          message:
            `This manifest is stale: it guards ${manifest.change}`
            + `#${manifest.task}, but openspec/changes/${manifest.change} no `
            + "longer exists, so the task it names cannot be reauthorized and "
            + "its Touch list authorizes nothing. Run `keel guard clear`, then "
            + "start the task you are actually working on.",
        }
    );
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
  // Bytes under the guarded change's own directory are records the task
  // produces — checkbox, Evidence, Review — not authority it must not touch.
  // The fingerprint comparison above already covers every part of that file
  // the capsule reads, so hashing it here only reported progress as drift.
  const recordPrefix = `openspec/changes/${manifest.change}/`;
  for (const entry of manifest.authority) {
    if (entry.path.replace(/\\/g, "/").startsWith(recordPrefix)) continue;
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
  gitPaths,
  guardStatus,
  readManifest,
  renderGuard,
  startGuard,
};

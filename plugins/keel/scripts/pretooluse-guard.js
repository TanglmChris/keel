#!/usr/bin/env node
"use strict";

// Keel plugin PreToolUse write guard: deterministic denial of out-of-Touch
// file edits while an explicit keel/guard.json manifest is active. Absence of
// the manifest allows everything silently; a present-but-untrusted manifest
// fails closed. The hook never writes state, never spawns the keel CLI, and
// always exits 0 — denial is expressed only through hook output. Paths that
// resolve outside the repository root are not product writes and pass through.

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const MANIFEST_SCHEMA = "keel-write-guard/v1";
const FILE_EDIT_TOOLS = new Map([
  ["Edit", "file_path"],
  ["Write", "file_path"],
  ["NotebookEdit", "notebook_path"],
]);

function readStdin() {
  try {
    return fs.readFileSync(0, "utf8");
  } catch {
    return "";
  }
}

function deny(reason) {
  process.stdout.write(
    `${JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: reason,
      },
    })}\n`
  );
}

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function manifestShapeValid(manifest) {
  return (
    manifest
    && manifest.schema === MANIFEST_SCHEMA
    && typeof manifest.change === "string"
    && manifest.change !== ""
    && typeof manifest.task === "string"
    && manifest.task !== ""
    && Array.isArray(manifest.touch)
    && manifest.touch.length > 0
    && manifest.touch.every((item) => typeof item === "string" && item !== "")
    && Array.isArray(manifest.authority)
    && manifest.authority.length > 0
    && manifest.authority.every(
      (item) =>
        item
        && typeof item.path === "string"
        && /^[0-9a-f]{64}$/.test(String(item.sha256 || ""))
    )
  );
}

function globPattern(value) {
  const escaped = value.replace(/[.+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(
    `^${escaped
      .replace(/\*\*/g, "\u0000")
      .replace(/\*/g, "[^/]*")
      .replace(/\u0000/g, ".*")}$`
  );
}

function pathAllowed(candidate, touch) {
  return touch.some((entry) => {
    const normalized = entry.replace(/\\/g, "/").replace(/^\.\//, "");
    if (normalized.endsWith("/")) return candidate.startsWith(normalized);
    if (normalized.includes("*")) return globPattern(normalized).test(candidate);
    return candidate === normalized;
  });
}

function main() {
  let event = {};
  try {
    event = JSON.parse(readStdin() || "{}");
  } catch {
    event = {};
  }
  const repo =
    typeof event.cwd === "string" && event.cwd ? event.cwd : process.cwd();
  const manifestPath = path.join(repo, "keel", "guard.json");
  if (!fs.existsSync(manifestPath)) return 0;

  const pathField = FILE_EDIT_TOOLS.get(event.tool_name);
  if (!pathField) return 0;

  let manifest = null;
  try {
    manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  } catch {
    manifest = null;
  }
  if (!manifestShapeValid(manifest)) {
    deny(
      "Keel write guard: keel/guard.json is present but invalid, so file "
        + "edits fail closed. Run `keel guard clear`, then `keel gate "
        + "task-start` and `keel guard start` to reauthorize."
    );
    return 0;
  }
  const pointer = `${manifest.change}#${manifest.task}`;

  for (const entry of manifest.authority) {
    const file = path.join(repo, entry.path);
    let fresh = null;
    try {
      fresh = sha256(fs.readFileSync(file));
    } catch {
      fresh = null;
    }
    if (fresh !== entry.sha256) {
      deny(
        `Keel write guard: task authority drift detected for ${pointer} `
          + `(${entry.path} changed since guard start), so file edits fail `
          + "closed. Re-run `keel gate task-start` and `keel guard start` to "
          + "reauthorize, or `keel guard clear` to stop enforcement."
      );
      return 0;
    }
  }

  const target = event.tool_input ? event.tool_input[pathField] : null;
  if (typeof target !== "string" || !target) return 0;
  const relative = path.relative(repo, path.resolve(repo, target));
  if (!relative || relative.startsWith("..") || path.isAbsolute(relative)) {
    return 0;
  }
  const candidate = relative.replace(/\\/g, "/");
  if (pathAllowed(candidate, manifest.touch)) return 0;

  deny(
    `Keel write guard: ${candidate} is outside Touch for ${pointer}. `
      + `Touch allows: ${manifest.touch.join(", ")}. Stop and report an `
      + "Out-of-scope Need, update the task authority and reauthorize via "
      + "`keel gate task-start` and `keel guard start`, or run "
      + "`keel guard clear` to stop enforcement."
  );
  return 0;
}

process.exit(main());

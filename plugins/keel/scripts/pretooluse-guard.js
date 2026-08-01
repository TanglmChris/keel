#!/usr/bin/env node
"use strict";

// Keel plugin PreToolUse write guard: deterministic denial of out-of-Touch
// file edits while an explicit keel/guard.json manifest is active. Absence of
// the manifest allows everything silently; a present-but-untrusted manifest
// fails closed. The hook never writes state, never spawns the keel CLI, and
// always exits 0 — denial is expressed only through hook output. The
// repository is the guard's scope: a path resolving outside it is not a product
// write and passes through, decided before the manifest is read so that no
// manifest state can reach it.

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

// A checked task keeps its records writable so it can finish the Evidence its
// completion gate requires, but earns no further product authorization. Byte
// hashing used to enforce this by accident, since ticking the box changed
// tasks.md; now it is stated. An unreadable or unmatched tasks.md is not read as
// checked — every gate that compiles the capsule catches that, and denying
// product writes on a parse miss would trade a real capability for a guess.
function taskIsChecked(repo, manifest) {
  const file = path.join(
    repo, "openspec", "changes", manifest.change, "tasks.md"
  );
  let content = "";
  try {
    content = fs.readFileSync(file, "utf8");
  } catch {
    return false;
  }
  const id = manifest.task.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = content.match(
    new RegExp(`^\\s*-\\s*\\[([ xX])\\]\\s*${id}(?![0-9.])`, "m")
  );
  return Boolean(match && match[1].toLowerCase() === "x");
}

// A path is not the file it names. `path.resolve` never follows a symbolic
// link, while the `cwd` the operating system reports usually already has, so
// one file could be spelled two ways and get two containment answers: measured
// as a write denied by its resolved path and allowed through a link to the
// same directory, which walked straight past the manifest. The guarded target
// is usually a file about to be created, so what can be resolved is its
// nearest existing ancestor; when nothing resolves, the unresolved path is
// what remains, which is exactly the comparison that shipped.
//
// `src/core/helper.js` answers the same question and must keep answering it
// the same way. It is deliberately not shared as an import: this hook is a
// standalone script the host executes, and depending on `src/core` would make
// the guard fail wherever the package layout differs from this repository's.
function realPathOrNearest(target) {
  let current = path.resolve(target);
  const trailing = [];
  for (;;) {
    try {
      return path.join(fs.realpathSync(current), ...trailing);
    } catch {
      const parent = path.dirname(current);
      if (parent === current) return path.resolve(target);
      trailing.unshift(path.basename(current));
      current = parent;
    }
  }
}

function repoRelative(repo, target) {
  return path.relative(
    realPathOrNearest(repo),
    realPathOrNearest(path.resolve(repo, target))
  );
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

  const pathField = FILE_EDIT_TOOLS.get(event.tool_name);
  if (!pathField) return 0;

  // The repository is the guard's scope, so this boundary is settled before the
  // manifest is read at all. It needs only the event's cwd and target, so no
  // manifest state — absent, invalid, drifted, or completed — has anything to
  // say about a path outside it. Deciding it here rather than further down is
  // what stops a branch added to the manifest section from denying a file the
  // guard never protected; that ordering has already failed twice.
  const target = event.tool_input ? event.tool_input[pathField] : null;
  if (typeof target !== "string" || !target) return 0;
  const relative = repoRelative(repo, target);
  if (
    !relative
    || relative === ".."
    || relative.startsWith(`..${path.sep}`)
    || path.isAbsolute(relative)
  ) {
    return 0;
  }
  const candidate = relative.replace(/\\/g, "/");

  const manifestPath = path.join(repo, "keel", "guard.json");
  if (!fs.existsSync(manifestPath)) return 0;

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
  // The record layer: the guarded change's own directory holds the records the
  // task produces — its checkbox, Evidence, and Review — not the product it
  // changes. `keel gate task-complete` already refuses to attribute this
  // directory as an outside-Touch failure, so denying it here made the guard
  // stop the one thing the completion gate is waiting for. Derived from the
  // manifest's existing `change` field, so no manifest shape changes.
  const recordPrefix = `openspec/changes/${manifest.change}/`;
  if (candidate.startsWith(recordPrefix)) return 0;

  for (const entry of manifest.authority) {
    // Same boundary: bytes under the guarded change's own directory are
    // records, and the capsule fingerprint — which carries no checkbox state
    // and no Evidence values — is what separates a record write from a
    // contract change. `keel guard status` and `keel gate task-complete`
    // compile the capsule and compare it; this hook cannot, and must not guess.
    if (entry.path.replace(/\\/g, "/").startsWith(recordPrefix)) continue;
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

  if (taskIsChecked(repo, manifest)) {
    deny(
      `Keel write guard: ${pointer} is checked complete, so it authorizes no `
        + `further product writes — ${candidate} is denied. Its own `
        + `${recordPrefix} records stay writable so the task can finish its `
        + "Evidence. Run `keel guard clear`, then authorize the next task "
        + "explicitly with `keel gate task-start`."
    );
    return 0;
  }

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

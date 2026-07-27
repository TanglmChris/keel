#!/usr/bin/env node
"use strict";

// Keel plugin SessionStart projection: disposable context only.
// OpenSpec and Git stay the durable authority; this script never writes
// state, selects an ambiguous owner, records a fingerprint, creates a goal,
// or blocks the session. It always exits 0.
//
// The projection is source-aware: a compact start reinjects the recomputed
// task pointer (selection, recorded Contract fingerprint, next command) that
// a summary is most likely to lose, a resume start reinjects the selection,
// and startup, clear, or any unknown source falls back to the generic view.

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

// This text is injected into the agent and never rendered for the human, so
// without an explicit instruction the projection reaches nobody who can catch
// it being wrong. Every branch carries the same phrase, degraded ones included.
const DISCLOSURE = "to the user in your first reply";

const TIMEOUT_MS = Number(process.env.KEEL_HOOK_TIMEOUT_MS || 8000) || 8000;
const MAX_REASONS = 3;
const MAX_REASON_LENGTH = 300;

function readStdin() {
  try {
    return fs.readFileSync(0, "utf8");
  } catch {
    return "";
  }
}

function emit(context) {
  process.stdout.write(
    `${JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "SessionStart",
        additionalContext: context,
      },
    })}\n`
  );
}

function runKeel(cwd, args) {
  const cli = (process.env.KEEL_CLI || "keel").trim();
  return spawnSync(`${cli} ${args.join(" ")}`, {
    cwd,
    shell: true,
    encoding: "utf8",
    timeout: TIMEOUT_MS,
  });
}

function fallback(reason) {
  emit(
    `Keel hook fallback: ${reason} Run \`keel context\` manually; `
      + "OpenSpec and Git remain the durable authority. Report this failure "
      + `and that command ${DISCLOSURE}.`
  );
}

function main() {
  let event = {};
  try {
    event = JSON.parse(readStdin() || "{}");
  } catch {
    event = {};
  }
  const cwd =
    typeof event.cwd === "string" && event.cwd ? event.cwd : process.cwd();

  if (!fs.existsSync(path.join(cwd, "openspec"))) {
    return 0;
  }

  const version = runKeel(cwd, ["--version"]);
  const versionMatch = String(version.stdout || "").match(/(\d+)\.\d+\.\d+/);
  if (
    version.error
    || version.status !== 0
    || !versionMatch
    || Number(versionMatch[1]) < 3
  ) {
    fallback(
      "the keel CLI is missing or incompatible with this plugin; install "
        + "@christang/keel (npm install -g @christang/keel)."
    );
    return 0;
  }

  const result = runKeel(cwd, ["context", "--json"]);
  if (result.error || result.status !== 0 || !String(result.stdout || "").trim()) {
    fallback("`keel context --json` failed or timed out.");
    return 0;
  }
  let context;
  try {
    context = JSON.parse(result.stdout);
  } catch {
    fallback("keel produced malformed context output.");
    return 0;
  }

  const source = typeof event.source === "string" ? event.source : "";
  const reinject = source === "compact" || source === "resume";
  const header = source === "compact"
    ? "Keel post-compaction reinjection (disposable; recomputed from OpenSpec and Git):"
    : source === "resume"
      ? "Keel resume reinjection (disposable; recomputed from OpenSpec and Git):"
      : "Keel session projection (disposable; OpenSpec and Git are the durable authority):";

  const lines = [header];
  if (context.status === "ready" && context.selection) {
    const task = context.selection.task ? `#${context.selection.task}` : "";
    lines.push(
      `- context ready: ${context.selection.change}${task} `
        + `(${context.selection.source}); next action: `
        + `${context.nextAction ? context.nextAction.kind : "unknown"}.`
    );
    if (reinject) {
      const recorded = recordedContract(cwd, context.selection);
      if (recorded) {
        lines.push(
          `- recorded Contract fingerprint: ${recorded} (recorded, not `
            + "verified; gates recompile and compare before any write)."
        );
      }
      lines.push(
        "- next: re-run `keel context --json`, then `keel gate task-start` "
          + "before continuing implementation; nothing was selected or "
          + "recorded by this projection."
      );
    } else {
      if (Array.isArray(context.read) && context.read.length > 0) {
        lines.push(`- read first: ${context.read.slice(0, 5).join(", ")}.`);
      }
      lines.push(
        "- run `keel gate task-start` before implementation; this projection "
          + "selects nothing and records nothing."
      );
    }
  } else {
    lines.push(`- context status: ${context.status || "unknown"}.`);
    for (const reason of (context.reasons || []).slice(0, MAX_REASONS)) {
      lines.push(`- reason: ${String(reason).slice(0, MAX_REASON_LENGTH)}`);
    }
    lines.push(
      "- next: run `keel context` and select an owner explicitly; this hook "
        + "does not guess among candidates."
    );
  }
  lines.push(`- report this state ${DISCLOSURE}; it authorizes nothing.`);
  emit(lines.join("\n"));
  return 0;
}

function recordedContract(repo, selection) {
  if (!selection || !selection.change || !selection.task) return null;
  const tasksPath = path.join(
    repo,
    "openspec",
    "changes",
    selection.change,
    "tasks.md"
  );
  let content = "";
  try {
    content = fs.readFileSync(tasksPath, "utf8");
  } catch {
    return null;
  }
  const wanted = String(selection.task);
  let inTask = false;
  for (const line of content.split(/\r?\n/)) {
    const heading = line.match(/^\s*-\s+\[[ xX]\]\s+(\d+(?:\.\d+)+)\s+/);
    if (heading) {
      inTask = heading[1] === wanted;
      continue;
    }
    if (!inTask) continue;
    const contract = line.match(/^\s*-\s*Contract:\s*(sha256:[0-9a-f]{64})\b/);
    if (contract) return contract[1];
  }
  return null;
}

process.exit(main());

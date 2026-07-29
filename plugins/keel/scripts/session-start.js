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

// This text is injected into the agent; the human reads the `systemMessage`
// line instead. Both channels ship on every branch, degraded ones included,
// and neither makes the other redundant: the host's line says what the state
// is, and this instruction is what surfaces the state the agent actually
// worked from, which is the one a user can catch being wrong.
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

// The human line rides the host's `systemMessage` field, which is rendered to
// the person at session start without waiting for them to type. It is a second
// channel, not a replacement: `additionalContext` still carries the full
// projection to the agent, and a host that does not recognize the field simply
// ignores it and leaves today's behavior intact.
function emit(context, humanMessage) {
  const payload = {};
  if (humanMessage) payload.systemMessage = humanMessage;
  payload.hookSpecificOutput = {
    hookEventName: "SessionStart",
    additionalContext: context,
  };
  process.stdout.write(`${JSON.stringify(payload)}\n`);
}

// Stated on the human line as well as the model payload: the person reading it
// at session start is the one who must not mistake a projection for authority.
const DISPOSABLE = "Disposable projection; OpenSpec and Git are the authority.";

// The Keel mark. A keel is the carina, the ridge on a bird's sternum, so the
// animal that literally has one is a bird. Every cell is drawn from
// U+2580–U+259F — the same block-element family as the host's own startup
// banner — because those code points are East-Asian-Ambiguous width: pinning
// the charset is what keeps the rows aligned under a CJK locale, and matters
// more than the shape. The rows are padded to equal width so that a future
// edit which breaks the rectangle is caught rather than silently skewed.
const MARK = [
  "▙▖▛▀▜  ▛▀▜▗▟",
  "  ▌█▐  ▌█▐  ",
  "  ▙▄▟▚▞▙▄▟  ",
].join("\n");

// The frame is modelled on the host's own welcome panel and draws from
// U+2500–U+257F, a different range than the mark. Its width is the longest
// content row, so a long change name widens the panel instead of being cut:
// the identifier is the most useful thing in the projection, and truncating
// the payload to preserve the frame would invert what the frame is for.
// Leads with a newline because the host prefixes the message with
// `<hookEvent>:<source> says: `, which would otherwise push the top rule out
// of line with the rows beneath it.
// Opt-in. The single line is what answers the reported problem — nobody is
// told anything at session start — and it ships on. The panel is presentation,
// and presentation that appears unbidden in every session of every install
// should be chosen rather than inherited. The allowlist is explicit so a typo
// leaves the default in place instead of quietly switching it on.
const PANEL_TITLE = "Keel";
const PANEL_ENABLED = /^(1|true|on|yes)$/i.test(
  String(process.env.KEEL_SESSION_PANEL || "").trim()
);

function panel(lines) {
  if (!PANEL_ENABLED) return lines.join(" ");
  const rows = [...MARK.split("\n"), "", ...lines];
  const width = Math.max(
    ...rows.map((row) => row.length),
    PANEL_TITLE.length + 8
  );
  const centred = rows.map((row) => {
    if (!row) return "";
    const isMark = /^[▀-▟ ]+$/.test(row);
    if (!isMark) return row;
    const pad = Math.floor((width - row.length) / 2);
    return " ".repeat(pad) + row;
  });
  const head = `─── ${PANEL_TITLE} `;
  return [
    "",
    `╭${head}${"─".repeat(width + 2 - head.length)}╮`,
    ...centred.map((row) => `│ ${row.padEnd(width)} │`),
    `╰${"─".repeat(width + 2)}╯`,
  ].join("\n");
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

// A degraded projection needs the human line most: a hook that fails silently
// is indistinguishable from a hook that never ran, which is how this whole
// failure mode was reported in the first place.
function fallback(reason) {
  emit(
    `Keel hook fallback: ${reason} Run \`keel context\` manually; `
      + "OpenSpec and Git remain the durable authority. Report this failure "
      + `and that command ${DISCLOSURE}.`,
    panel([
      `Keel: projection unavailable — ${reason} Next: keel context.`,
      DISPOSABLE,
    ])
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
  let human = [];
  if (context.status === "ready" && context.selection) {
    const task = context.selection.task ? `#${context.selection.task}` : "";
    human = [
      `Keel: ${context.selection.change}${task} — next: `
        + `${context.nextAction ? context.nextAction.kind : "unknown"}.`,
      DISPOSABLE,
    ];
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
    const status = context.status || "unknown";
    const reasons = (context.reasons || []).slice(0, MAX_REASONS);
    human = [
      `Keel: ${status}`
        + (reasons.length > 0
          ? ` — ${String(reasons[0]).slice(0, MAX_REASON_LENGTH)}`
          : "")
        + " Next: keel context.",
      DISPOSABLE,
    ];
    lines.push(`- context status: ${status}.`);
    for (const reason of reasons) {
      lines.push(`- reason: ${String(reason).slice(0, MAX_REASON_LENGTH)}`);
    }
    lines.push(
      "- next: run `keel context` and select an owner explicitly; this hook "
        + "does not guess among candidates."
    );
  }
  lines.push(`- report this state ${DISCLOSURE}; it authorizes nothing.`);
  emit(lines.join("\n"), panel(human));
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

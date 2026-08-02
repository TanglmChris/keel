"use strict";

// Keel 4.1.0 bounded read-only helper contract.
//
// A helper is never a second writer. `keel project helper` compiles one
// bounded read-only question or one exact repository-byte-stable verification
// command into a `keel-helper-brief/v1` evidence contract, and verifies a
// helper's return only after proving the repository bytes are unchanged. The
// current agent stays the sole writer, owner of Acceptance, Review, gates, and
// completion; helper absence never disables current-agent goal execution.

const fs = require("fs");
const os = require("os");
const path = require("path");
const crypto = require("crypto");

const BRIEF_VERSION = "keel-helper-brief/v1";
const BASELINE_VERSION = "keel-helper-baseline/v1";
const VERIFY_VERSION = "keel-helper-verification/v1";
const SUPPORTED_HELPER_TARGETS = new Set(["codex", "claude"]);

// Any mutation, delegation, or ownership request disqualifies a read-only brief.
const FORBIDDEN_INTENT = new RegExp(
  "\\b(implement|write|edit|modify|create|refactor|delete|remove|fix|apply|"
    + "generate|install|commit|push|sync|archive|mark|check off|rewrite|"
    + "update the task|change the acceptance|use the fallback|use a fallback)\\b",
  "i"
);
const DELEGATION_INTENT = new RegExp(
  "\\b(subagent|sub-agent|delegate|delegation|spawn|agent team|another agent|"
    + "helper)\\b",
  "i"
);
// Shell tokens that would create or move repository artifacts.
const ARTIFACT_TOKENS = [
  ">", ">>", "|&", "tee ", "git commit", "git add", "git push", "git checkout",
  "git reset", "git restore", "git rm", "git mv", "npm install", "npm i ",
  "npm ci", "mkdir", "touch ", "rm ", "mv ", "cp ", "rmdir",
];
const REPORT_SCHEMA = [
  "question-or-command",
  "reads-performed",
  "observed-evidence",
  "byte-stability: verified|rejected|unverifiable",
  "no-writes-no-delegation-no-completion-authority",
];

function blockedBrief(target, reason, extra = {}) {
  return {
    version: BRIEF_VERSION,
    status: "blocked",
    target,
    brief: null,
    reasons: [reason],
    ...extra,
  };
}

// Symbolic links are resolved on both sides, because `process.cwd()` comes
// back already resolved while `path.resolve` never follows a link — on macOS,
// where `/tmp` is a link to `/private/tmp`, that made a path inside the
// worktree look external and let the helper write its baseline into the
// repository it had just promised not to touch. The baseline usually does not
// exist yet, so the nearest existing ancestor is what resolves. The write
// guard hook answers the same question and keeps its own copy of this rule,
// because it is a standalone script that cannot import from here.
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

function isExternal(repo, candidate) {
  const rel = path.relative(
    realPathOrNearest(repo),
    realPathOrNearest(candidate)
  );
  return (
    rel === ".."
    || rel.startsWith(`..${path.sep}`)
    || path.isAbsolute(rel)
  );
}

function compileHelperBrief(repo, options) {
  const target = options.target;
  if (!SUPPORTED_HELPER_TARGETS.has(target)) {
    return blockedBrief(
      target,
      `Bounded read-only helpers support codex and claude only; `
        + `${target || "missing"} remains manual/compatibility-only.`
    );
  }

  const question = (options.helperQuestion || "").trim();
  const command = (options.helperCommand || "").trim();
  if ((question && command) || (!question && !command)) {
    return blockedBrief(
      target,
      "A helper brief needs exactly one bounded read-only question or one exact "
        + "repository-byte-stable verification command, not both and not neither."
    );
  }

  const external = options.helperExternal || [];
  for (const declared of external) {
    if (!isExternal(repo, declared)) {
      return blockedBrief(
        target,
        `Declared helper output path is inside the repository: ${declared}; `
          + "helper temporaries must live outside the worktree."
      );
    }
  }

  if (question) {
    if (/\?[\s\S]*\?/.test(question)) {
      return blockedBrief(
        target,
        "A helper brief carries one bounded question; multiple unrelated "
          + "questions must be split into separate read-only briefs."
      );
    }
    if (DELEGATION_INTENT.test(question)) {
      return blockedBrief(
        target,
        "A helper cannot delegate or spawn nested helpers; the brief must be a "
          + "single read-only question the helper answers itself."
      );
    }
    if (FORBIDDEN_INTENT.test(question)) {
      return blockedBrief(
        target,
        "A helper is read-only and owns no completion authority; it cannot be "
          + "asked to implement, write, mark, sync, archive, commit, push, or "
          + "change Acceptance."
      );
    }
  } else {
    if (DELEGATION_INTENT.test(command)) {
      return blockedBrief(
        target,
        "A helper verification command cannot delegate or nest further helpers."
      );
    }
    const lowered = command.toLowerCase();
    const artifact = ARTIFACT_TOKENS.find((token) => lowered.includes(token));
    if (artifact) {
      return blockedBrief(
        target,
        `Helper command would generate or move repository artifacts (${artifact.trim()}); `
          + "only repository-byte-stable verification commands are allowed."
      );
    }
    if (FORBIDDEN_INTENT.test(command)) {
      return blockedBrief(
        target,
        "A helper verification command cannot mark, sync, archive, commit, push, "
          + "or otherwise assume completion authority."
      );
    }
  }

  const brief = {
    version: BRIEF_VERSION,
    target,
    mode: question ? "question" : "verification-command",
    request: question || command,
    reads: options.helperReads || [],
    externalPaths: external,
    authority: "read-only-evidence-only",
    writesProducts: false,
    delegates: false,
    completionAuthority: false,
    reportSchema: REPORT_SCHEMA,
  };
  return {
    version: BRIEF_VERSION,
    status: "ready",
    target,
    brief,
    reasons: [],
  };
}

function snapshotRepo(repo) {
  const snapshot = {};
  const walk = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (entry.name === ".git") continue;
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(full);
      } else if (entry.isFile()) {
        const rel = path.relative(repo, full).replace(/\\/g, "/");
        const bytes = fs.readFileSync(full);
        const hash = crypto.createHash("sha256").update(bytes).digest("hex");
        const mode = fs.statSync(full).mode & 0o777;
        snapshot[rel] = `${hash}:${mode.toString(8)}`;
      }
    }
  };
  walk(repo);
  return snapshot;
}

function captureHelperBaseline(repo, options) {
  const outPath = options.helperBaseline;
  if (!outPath) {
    throw new Error("helper baseline capture requires --baseline");
  }
  if (!isExternal(repo, outPath)) {
    throw new Error(
      "helper baseline must be written outside the repository worktree"
    );
  }
  const snapshot = snapshotRepo(repo);
  fs.mkdirSync(path.dirname(path.resolve(outPath)), { recursive: true });
  fs.writeFileSync(
    path.resolve(outPath),
    `${JSON.stringify({ version: BASELINE_VERSION, snapshot }, null, 2)}\n`,
    "utf8"
  );
  return {
    version: BASELINE_VERSION,
    status: "captured",
    path: path.resolve(outPath),
    count: Object.keys(snapshot).length,
  };
}

function classifyChanges(before, after) {
  const changes = [];
  for (const [rel, value] of Object.entries(after)) {
    if (!(rel in before)) {
      changes.push({ path: rel, kind: "added" });
    } else if (before[rel] !== after[rel]) {
      const [beforeHash, beforeMode] = before[rel].split(":");
      const [afterHash] = value.split(":");
      changes.push({
        path: rel,
        kind: beforeHash === afterHash ? "permission-changed" : "modified",
      });
      void beforeMode;
    }
  }
  for (const rel of Object.keys(before)) {
    if (!(rel in after)) {
      changes.push({ path: rel, kind: "removed" });
    }
  }
  return changes.sort((a, b) => a.path.localeCompare(b.path));
}

function verifyHelperEvidence(repo, options) {
  const baselinePath = options.helperBaseline;
  if (!baselinePath || !fs.existsSync(path.resolve(baselinePath))) {
    return {
      version: VERIFY_VERSION,
      status: "unverifiable",
      target: options.target,
      changes: [],
      cleanup: "none",
      reasons: [
        "Byte stability cannot be established without a recorded baseline; the "
          + "verification remains current-agent work.",
      ],
    };
  }
  let baseline;
  try {
    baseline = JSON.parse(fs.readFileSync(path.resolve(baselinePath), "utf8"));
  } catch {
    return {
      version: VERIFY_VERSION,
      status: "unverifiable",
      target: options.target,
      changes: [],
      cleanup: "none",
      reasons: [
        "Recorded helper baseline is unreadable; byte stability cannot be "
          + "established and the verification remains current-agent work.",
      ],
    };
  }
  const before = baseline.snapshot || {};
  const after = snapshotRepo(repo);
  const changes = classifyChanges(before, after);
  if (changes.length === 0) {
    return {
      version: VERIFY_VERSION,
      status: "verified",
      target: options.target,
      changes: [],
      cleanup: "none",
      reasons: [],
    };
  }
  return {
    version: VERIFY_VERSION,
    status: "rejected",
    target: options.target,
    changes,
    // The helper never restores, deletes, or attributes; it reports exact paths.
    cleanup: "none",
    reasons: [
      "Helper evidence rejected: repository bytes changed at "
        + changes.map((item) => `${item.path} (${item.kind})`).join(", ")
        + "; the current agent owns these paths and no cleanup is performed.",
    ],
  };
}

function renderHelper(result) {
  const lines = [
    `Keel helper: ${result.status}`,
    `Version: ${result.version}`,
  ];
  if (result.target) lines.push(`Target: ${result.target}`);
  for (const change of result.changes || []) {
    lines.push(`Changed: ${change.path} (${change.kind})`);
  }
  for (const reason of result.reasons || []) lines.push(`Reason: ${reason}`);
  return `${lines.join("\n")}\n`;
}

module.exports = {
  BRIEF_VERSION,
  BASELINE_VERSION,
  VERIFY_VERSION,
  SUPPORTED_HELPER_TARGETS,
  compileHelperBrief,
  captureHelperBaseline,
  verifyHelperEvidence,
  renderHelper,
};

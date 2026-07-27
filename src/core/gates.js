"use strict";

// Keel 4.1.0 deterministic gate contract.

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const {
  ACCEPTED_REVIEW_STATUSES,
  RED_GREEN_VERIFICATION_STRATEGIES,
  compileTaskContract,
  field,
  isConcrete,
  isPassingReviewStatus,
  parseTasks,
} = require("./task-contract");
const { startGuard } = require("./guard");

const GATE_STAGES = new Set(["task-start", "task-complete", "change-close"]);

class GateInputError extends Error {}

function problem(code, message) {
  return { code, message };
}

function gateResult(
  gate,
  status,
  change,
  taskIds,
  problems = [],
  warnings = [],
  contract = null,
  contracts = null
) {
  const result = {
    schemaVersion: 1,
    gate,
    status,
    selection: {
      change,
      tasks: taskIds,
    },
    problems,
    warnings,
  };
  if (contract) result.contract = contract;
  if (contracts) result.contracts = contracts;
  return result;
}

function changeNames(repo) {
  const root = path.join(repo, "openspec", "changes");
  if (!fs.existsSync(root)) return [];
  return fs
    .readdirSync(root, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name !== "archive")
    .map((entry) => entry.name)
    .sort();
}

function selectChange(repo, explicit) {
  if (explicit) {
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(explicit)) {
      throw new GateInputError(`invalid change name: ${explicit}`);
    }
    return explicit;
  }
  const changes = changeNames(repo);
  if (changes.length !== 1) {
    throw new GateInputError(
      changes.length === 0
        ? "no active OpenSpec change is available"
        : `multiple active OpenSpec changes require --change: ${changes.join(", ")}`
    );
  }
  return changes[0];
}

function loadSelection(repo, options, requireTask = true) {
  const change = selectChange(repo, options.change);
  const tasksPath = path.join(repo, "openspec", "changes", change, "tasks.md");
  if (!fs.existsSync(tasksPath)) {
    throw new GateInputError(`missing OpenSpec tasks file: ${tasksPath}`);
  }
  const content = fs.readFileSync(tasksPath, "utf8");
  const tasks = parseTasks(content);
  if (!requireTask) return { change, tasksPath, content, tasks, selected: [] };

  let selected;
  if (options.task) {
    selected = tasks.find((task) => task.id === options.task);
    if (!selected) {
      throw new GateInputError(`task ${change}#${options.task} does not exist`);
    }
  } else {
    selected = tasks.find((task) => !task.checked);
    if (!selected) {
      throw new GateInputError(`change ${change} has no unchecked task`);
    }
  }
  return { change, tasksPath, content, tasks, selected: [selected] };
}

function contractAnchorPlan(selection, task) {
  const lines = selection.content.split("\n");
  const index = selection.tasks.findIndex((item) => item.id === task.id);
  const end =
    index + 1 < selection.tasks.length
      ? selection.tasks[index + 1].line
      : lines.length;
  for (let cursor = task.line; cursor < end; cursor += 1) {
    const match = lines[cursor].match(/^(\s*)-\s*Contract:\s*(.*?)(\r?)$/);
    if (match) {
      return {
        lines,
        cursor,
        indent: match[1],
        previous: match[2].trim(),
        cr: match[3],
      };
    }
  }
  return null;
}

function anchoredFingerprint(previous) {
  const match = previous.match(/sha-?256[\s:`]*([a-f0-9]{64})/i);
  return match ? match[1].toLowerCase() : null;
}

function taskStart(repo, options) {
  const selection = loadSelection(repo, options);
  const task = selection.selected[0];
  const compiled = compileTaskContract(repo, selection.change, task);
  const problems = [...compiled.diagnostics];
  // Recording the current fingerprint is idempotent: --record replaces the
  // selected task's Contract anchor whatever it holds, so reauthorizing a task
  // whose authority changed — the path the guard's own drift messages direct
  // authors to — needs no manual edit. Refusal is kept only for a task with no
  // anchor at all, which is a malformed capsule rather than a reauthorization,
  // and it writes nothing, guard manifest included.
  let anchorPlan = null;
  if (options.record && problems.length === 0) {
    anchorPlan = contractAnchorPlan(selection, task);
    if (!anchorPlan) {
      problems.push(
        problem(
          "record-refused",
          "--record needs a \"- Contract:\" Evidence line on the selected "
            + "task to anchor, and this task has none, so nothing was "
            + 'written. Add "- Contract: pending" to its Evidence.'
        )
      );
    }
  }
  const result = gateResult(
    "task-start",
    problems.length > 0 ? "fail" : "pass",
    selection.change,
    [task.id],
    problems,
    [],
    problems.length === 0
      ? compiled
      : null
  );
  // The disposable guard manifest and the explicit --record anchor
  // replacement are the only permitted gate writes: each happens only on a
  // passing task-start (guard: Claude target without --no-guard, replacing
  // any previous task's manifest in the one-shot single-task model).
  if (
    result.status === "pass"
    && (options.target || "claude") === "claude"
    && !options.noGuard
  ) {
    const guard = startGuard(repo, {
      change: selection.change,
      task: task.id,
      force: true,
    });
    result.guard = {
      status: guard.status,
      manifestPath: guard.manifestPath,
    };
    if (guard.status !== "started") {
      result.warnings.push(...guard.problems.map((item) => item.message));
    }
  }
  if (result.status === "pass" && anchorPlan) {
    const anchorLine =
      `${anchorPlan.indent}- Contract: keel-task-capsule/v1 `
      + `sha256:${compiled.fingerprint.value}${anchorPlan.cr}`;
    const unchanged = anchorPlan.lines[anchorPlan.cursor] === anchorLine;
    if (!unchanged) {
      anchorPlan.lines[anchorPlan.cursor] = anchorLine;
      fs.writeFileSync(
        selection.tasksPath,
        anchorPlan.lines.join("\n"),
        "utf8"
      );
    }
    const wasPending = /^pending$/i.test(anchorPlan.previous);
    result.record = {
      status: unchanged ? "unchanged" : wasPending ? "recorded" : "rerecorded",
      path: `openspec/changes/${selection.change}/tasks.md`,
      line: anchorPlan.cursor + 1,
      previous: anchorPlan.previous,
    };
    // A re-record that lands a different fingerprint is a contract change, so
    // any Evidence already produced under the previous one is stale. The gate
    // cannot judge which Evidence survives; it names the change and leaves the
    // call to the current agent's Review.
    const replaced = anchoredFingerprint(anchorPlan.previous);
    if (replaced && replaced !== compiled.fingerprint.value) {
      result.warnings.push(
        `Re-recorded over a different contract: was sha256:${replaced}, now `
          + `sha256:${compiled.fingerprint.value}. Execution evidence produced `
          + "under the previous contract is stale; clear or re-verify it "
          + "before completing this task."
      );
    }
  }
  return result;
}

function commandLabels(task) {
  return [
    ...field(task, "Commands").matchAll(/^\s*-\s*(M\d+):\s+\S.*$/gim),
  ].map((match) => match[1]);
}

function evidenceValue(task, label) {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = field(task, "Evidence").match(
    new RegExp(`^\\s*-\\s*${escaped}:\\s*(.*)$`, "im")
  );
  return match ? match[1] : "";
}

function reviewValue(task, label) {
  const match = field(task, "Evidence").match(
    new RegExp(`^\\s*-\\s*${label}:\\s*(.*)$`, "im")
  );
  return match ? match[1].trim() : "";
}

function findingOwnerIsDurable(repo, findings) {
  if (/keel\/HANDOFF\.md/i.test(findings)) return false;
  if (/\b(?:explicit\s+)?discard (?:reason|rationale)\s*:/i.test(findings)) {
    return true;
  }
  if (/\bkeel\/archive\/[A-Za-z0-9._/-]+/i.test(findings)) return true;
  const owner = findings.match(
    /\b(openspec\/changes\/[A-Za-z0-9][A-Za-z0-9._-]*\/(?:proposal|design|tasks)\.md)(?:#\d+(?:\.\d+)*)?/i
  );
  return Boolean(owner && fs.existsSync(path.join(repo, owner[1])));
}

function gitPaths(repo) {
  const status = spawnSync(
    "git",
    ["status", "--short", "--untracked-files=all"],
    { cwd: repo, encoding: "utf8" }
  );
  if (status.error || status.status !== 0) return [];
  return status.stdout
    .split(/\r?\n/)
    .filter(Boolean)
    .flatMap((line) => {
      // A staged rename/copy is one porcelain line, `R  old -> new`; attribute
      // both endpoints so a rename whose old and new paths are in Touch is not
      // a false outside-Touch failure. Every other line carries one path.
      const entry = line.slice(3).trim().replace(/\\/g, "/");
      const arrow = entry.indexOf(" -> ");
      return arrow === -1
        ? [entry]
        : [entry.slice(0, arrow), entry.slice(arrow + 4)];
    });
}

function touchEntries(task, contract = null) {
  if (contract) return contract.capsule.touch;
  return field(task, "Touch")
    .split(/\r?\n/)
    .map((line) => line.replace(/^\s*-\s*/, "").trim().replace(/^`|`$/g, ""))
    .filter((line) => isConcrete(line));
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

function scopeEvidence(repo, task, base, contract = null, change = null) {
  const dirtyPaths = gitPaths(repo);
  if (!base) {
    return {
      problems: [],
      warnings:
        dirtyPaths.length > 0
          ? [
              "Working-tree paths are dirty but not attributed without an "
                + `explicit base: ${dirtyPaths.join(", ")}`,
            ]
          : [],
    };
  }

  const verified = spawnSync(
    "git",
    ["rev-parse", "--verify", `${base}^{commit}`],
    { cwd: repo, encoding: "utf8" }
  );
  if (verified.error || verified.status !== 0) {
    throw new GateInputError(`invalid trustworthy Git base: ${base}`);
  }
  const diff = spawnSync(
    "git",
    ["diff", "--name-only", base, "--"],
    { cwd: repo, encoding: "utf8" }
  );
  if (diff.error || diff.status !== 0) {
    throw new GateInputError(`could not compare Git base: ${base}`);
  }
  const changed = new Set([
    ...diff.stdout.split(/\r?\n/).filter(Boolean),
    ...dirtyPaths,
  ]);
  const touch = touchEntries(task, contract);
  // The disposable guard manifest is the one artifact the gate contract itself
  // permits a gate to write, and the selected change's own authoring artifacts
  // are the working state the gate is completing against, so neither is
  // attributed as outside Touch. Other changes' directories, the archive tree,
  // and the specs/schemas trees stay attributable.
  const authoringPrefix = change ? `openspec/changes/${change}/` : null;
  const outside = [...changed]
    .map((item) => item.replace(/\\/g, "/"))
    .filter((item) => item !== "keel/guard.json")
    .filter((item) => !(authoringPrefix && item.startsWith(authoringPrefix)))
    .filter((item) => !pathAllowed(item, touch))
    .sort();
  return {
    problems: outside.map((item) =>
      problem("outside-touch", `Changed path is outside Touch: ${item}`)
    ),
    warnings: [],
  };
}

function completionChecks(repo, task, contract = null) {
  const problems = [];
  const commands = contract
    ? contract.capsule.verification.commands.map((item) => item.label)
    : commandLabels(task);
  if (commands.length === 0) {
    problems.push(problem("missing-commands", "Commands must define at least one M<n>."));
  }
  for (const label of commands) {
    if (!isConcrete(evidenceValue(task, label))) {
      problems.push(
        problem("missing-evidence", `Missing concrete Evidence for ${label}.`)
      );
    }
  }
  const strategy = contract
    ? contract.capsule.verification.strategy.toLowerCase()
    : "";
  if (RED_GREEN_VERIFICATION_STRATEGIES.has(strategy)) {
    for (const label of commands) {
      for (const phase of ["red", "green"]) {
        if (!isConcrete(evidenceValue(task, `${label}.${phase}`))) {
          problems.push(
            problem(
              "missing-strategy-evidence",
              `${strategy} requires concrete ${label}.${phase} Evidence for `
                + "the same behavior check."
            )
          );
        }
      }
    }
  }
  const blocker = evidenceValue(task, "Blocker");
  if (isConcrete(blocker)) {
    problems.push(problem("blocker", `Task records a blocker: ${blocker}`));
  }

  const reviewFields = {
    Status: reviewValue(task, "Status"),
    "Acceptance check": reviewValue(task, "Acceptance check"),
    "Scope check": reviewValue(task, "Scope check"),
    Findings: reviewValue(task, "Findings"),
  };
  const reviewMissing = [
    ...Object.entries(reviewFields)
      .filter(([name]) => name !== "Findings")
      .filter(([, value]) => !isConcrete(value)),
    ...(
      /^none\.?$/i.test(reviewFields.Findings)
      || isConcrete(reviewFields.Findings)
        ? []
        : [["Findings", reviewFields.Findings]]
    ),
  ];
  const reviewPassed = isPassingReviewStatus(reviewFields.Status);
  const reviewProblems = [];
  if (reviewMissing.length > 0 || !reviewPassed) {
    const details = [];
    if (!reviewPassed) {
      const got = isConcrete(reviewFields.Status)
        ? ` (got "${String(reviewFields.Status).trim()}")`
        : "";
      details.push(
        `Status must be one of ${ACCEPTED_REVIEW_STATUSES.join(", ")}${got}`
      );
    }
    const otherMissing = reviewMissing.filter(([name]) => name !== "Status");
    if (otherMissing.length > 0) {
      details.push(
        "these Review fields need concrete Evidence: "
          + otherMissing.map(([name]) => name).join(", ")
      );
    }
    reviewProblems.push(
      problem(
        "semantic-review",
        `Current-agent Review is incomplete — ${details.join("; ")}.`
      )
    );
  } else if (
    !/^none\.?$/i.test(reviewFields.Findings)
    && !findingOwnerIsDurable(repo, reviewFields.Findings)
  ) {
    problems.push(
      problem(
        "finding-owner",
        "Review Findings must be `none` or carry a durable owner — a "
          + "`Discard reason:`/`Discard rationale:` prefix, a `keel/archive/…` "
          + "path, or an existing `openspec/changes/…` artifact; "
          + "`keel/HANDOFF.md` is not an owner."
      )
    );
  }
  return { problems, reviewProblems };
}

function taskComplete(repo, options) {
  const selection = loadSelection(repo, options);
  const task = selection.selected[0];
  const contract = compileTaskContract(repo, selection.change, task);
  const usableContract = contract.diagnostics.length === 0 ? contract : null;
  const checks = completionChecks(repo, task, usableContract);
  checks.problems.push(...contract.diagnostics);
  const scope = scopeEvidence(
    repo,
    task,
    options.base,
    usableContract,
    selection.change
  );
  checks.problems.push(...scope.problems);
  const status =
    checks.problems.length > 0
      ? "fail"
      : checks.reviewProblems.length > 0
        ? "needs-review"
        : "pass";
  return gateResult(
    "task-complete",
    status,
    selection.change,
    [task.id],
    [...checks.problems, ...checks.reviewProblems],
    scope.warnings,
    usableContract
  );
}

function expectationProblems(content, tasks) {
  const heading = content.search(/^## Expectation Coverage\s*$/m);
  if (heading < 0) {
    return [
      problem(
        "expectation-coverage",
        "tasks.md requires a `## Expectation Coverage` section: one "
          + "`- E<n>: <expectation> Covered by: <task ids>` line per "
          + "expectation, or `- None.`."
      ),
    ];
  }
  const bodyStart = content.indexOf("\n", heading);
  const remainder = bodyStart < 0 ? "" : content.slice(bodyStart + 1);
  const nextHeading = remainder.search(/^##\s+/m);
  const section = nextHeading < 0 ? remainder : remainder.slice(0, nextHeading);
  if (/^\s*-\s+None\.?\s*$/im.test(section)) return [];
  const entries = [
    ...section.matchAll(
      /^\s*-\s+(E\d+)\s*:\s*([\s\S]*?)(?=^\s*-\s+E\d+\s*:|(?![\s\S]))/gm
    ),
  ];
  if (entries.length === 0) {
    return [
      problem(
        "expectation-coverage",
        "Expectation Coverage must declare each `E<n>` closure — "
          + "`- E<n>: <expectation> Covered by: <task ids>`, a `Durable owner:` "
          + "path, or a `Discard reason:` — or `- None.`."
      ),
    ];
  }
  const problems = [];
  for (const entry of entries) {
    const [, id, body] = entry;
    const covered = body.match(/Covered by:\s*([0-9.,\s-]+)/i);
    const hasDurableOwner =
      /Durable owner:\s*(?:openspec\/changes\/|keel\/archive\/)/i.test(body);
    const discarded = /Discard(?:ed)? (?:reason|rationale):\s*\S/i.test(body);
    if (!covered && !hasDurableOwner && !discarded) {
      problems.push(
        problem(
          "expectation-closure",
          `${id} lacks behavior coverage, durable owner, or discard rationale.`
        )
      );
      continue;
    }
    if (covered) {
      const ids = covered[1].match(/\d+(?:\.\d+)+/g) || [];
      for (const taskId of ids) {
        const owner = tasks.find((task) => task.id === taskId);
        if (!owner || !owner.checked) {
          problems.push(
            problem(
              "expectation-owner",
              `${id} references incomplete or missing task ${taskId}.`
            )
          );
        }
      }
    }
  }
  return problems;
}

function hasDeltaSpec(changePath) {
  const specsPath = path.join(changePath, "specs");
  if (!fs.existsSync(specsPath)) return false;
  const queue = [specsPath];
  while (queue.length > 0) {
    const current = queue.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const candidate = path.join(current, entry.name);
      if (entry.isDirectory()) queue.push(candidate);
      if (entry.isFile() && entry.name === "spec.md") return true;
    }
  }
  return false;
}

function changeClose(repo, options) {
  if (!["sync", "archive"].includes(options.closeAction)) {
    throw new GateInputError(
      "change-close requires --action sync or --action archive"
    );
  }
  const selection = loadSelection(repo, options, false);
  const problems = [];
  const reviewProblems = [];
  const contracts = [];
  if (selection.tasks.length === 0) {
    problems.push(problem("missing-tasks", "Change has no executable tasks."));
  }
  for (const task of selection.tasks) {
    const contract = compileTaskContract(repo, selection.change, task);
    contracts.push({
      task: task.id,
      contract: contract.diagnostics.length === 0 ? contract : null,
    });
    problems.push(
      ...contract.diagnostics.map((item) =>
        problem(item.code, `Task ${task.id}: ${item.message}`)
      )
    );
    if (!task.checked) {
      problems.push(
        problem("incomplete-task", `Task ${task.id} is not checked complete.`)
      );
      continue;
    }
    const checks = completionChecks(
      repo,
      task,
      contract.diagnostics.length === 0 ? contract : null
    );
    problems.push(
      ...checks.problems.map((item) =>
        problem(item.code, `Task ${task.id}: ${item.message}`)
      )
    );
    reviewProblems.push(
      ...checks.reviewProblems.map((item) =>
        problem(item.code, `Task ${task.id}: ${item.message}`)
      )
    );
  }
  problems.push(...expectationProblems(selection.content, selection.tasks));

  const changePath = path.dirname(selection.tasksPath);
  if (!hasDeltaSpec(changePath)) {
    problems.push(
      problem(
        "missing-delta-spec",
        `${options.closeAction} requires at least one change delta spec.`
      )
    );
  }
  if (options.closeAction === "archive") {
    for (const artifact of ["proposal.md", "design.md"]) {
      if (!fs.existsSync(path.join(changePath, artifact))) {
        problems.push(
          problem("missing-artifact", `archive requires ${artifact}.`)
        );
      }
    }
  }

  const status =
    problems.length > 0
      ? "fail"
      : reviewProblems.length > 0
        ? "needs-review"
        : "pass";
  return gateResult(
    "change-close",
    status,
    selection.change,
    selection.tasks.map((task) => task.id),
    [...problems, ...reviewProblems],
    [],
    null,
    contracts
  );
}

function runGate(repo, stage, options) {
  if (!GATE_STAGES.has(stage)) {
    throw new GateInputError(`unsupported gate stage: ${stage}`);
  }
  if (stage === "task-start") return taskStart(repo, options);
  if (stage === "task-complete") return taskComplete(repo, options);
  return changeClose(repo, options);
}

function renderGate(result) {
  const lines = [
    `Keel gate: ${result.gate}`,
    `Status: ${result.status}`,
    `Selection: ${result.selection.change}`
      + (result.selection.tasks.length
        ? `#${result.selection.tasks.join(",")}`
        : ""),
  ];
  for (const item of result.problems) lines.push(`Problem: ${item.message}`);
  for (const warning of result.warnings) lines.push(`Warning: ${warning}`);
  if (result.contract) {
    lines.push(
      `Fingerprint: ${result.contract.fingerprint.algorithm}:`
        + result.contract.fingerprint.value
    );
  }
  if (result.guard) {
    lines.push(`Guard: ${result.guard.status} (${result.guard.manifestPath})`);
  }
  if (result.record) {
    lines.push(
      `Contract anchor ${result.record.status}: ${result.record.path}:`
        + result.record.line
    );
  }
  return `${lines.join("\n")}\n`;
}

module.exports = {
  GateInputError,
  field,
  parseTasks,
  renderGate,
  runGate,
};

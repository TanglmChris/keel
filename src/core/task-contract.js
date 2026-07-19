"use strict";

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const SUPPORTED_MODES = new Set([
  "implementation",
  "diagnose-only",
  "plan-first",
]);

function isConcrete(value) {
  const normalized = String(value || "")
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/^\s*-\s*/gm, "")
    .trim();
  if (!normalized || /^(?:none|pending)\.?$/i.test(normalized)) return false;
  return !/(<[^>]+>|\bTODO\b|\bTBD\b|\bplaceholder\b)/i.test(normalized);
}

function parseTasks(content) {
  const lines = content.split(/\r?\n/);
  const tasks = [];
  for (let index = 0; index < lines.length; index += 1) {
    const match = lines[index].match(
      /^\s*-\s+\[([ xX])\]\s+(\d+(?:\.\d+)+)\s+(.+?)\s*$/
    );
    if (!match) continue;
    tasks.push({
      checked: match[1].toLowerCase() === "x",
      id: match[2],
      title: match[3],
      line: index,
    });
  }
  for (let index = 0; index < tasks.length; index += 1) {
    const end = index + 1 < tasks.length ? tasks[index + 1].line : lines.length;
    const bodyLines = lines.slice(tasks[index].line, end);
    tasks[index].body = bodyLines.join("\n");
    tasks[index].fields = new Map();
    let current = null;
    for (const line of bodyLines.slice(1)) {
      const fieldMatch = line.match(/^ {2}- ([A-Za-z][A-Za-z /-]+):\s*(.*)$/);
      if (fieldMatch) {
        current = fieldMatch[1];
        tasks[index].fields.set(current, [fieldMatch[2]]);
      } else if (current) {
        tasks[index].fields.get(current).push(line);
      }
    }
  }
  return tasks;
}

function field(task, name) {
  return (task.fields.get(name) || []).join("\n");
}

function fieldValues(task, name) {
  return field(task, name)
    .split(/\r?\n/)
    .map((line) => line.replace(/^\s*-\s*/, "").trim())
    .filter(Boolean);
}

function normalizedValues(task, name, { ordered = false } = {}) {
  const values = fieldValues(task, name)
    .map((value) =>
      value
        .replace(/<!--[\s\S]*?-->/g, "")
        .replace(/\s+/g, " ")
        .trim()
    )
    .filter(Boolean);
  return ordered ? values : [...new Set(values)].sort();
}

function normalizeText(value) {
  return String(value || "")
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

const SUPPORTED_VERIFICATION_STRATEGIES = [
  "vertical-tdd",
  "regression-first",
  "characterization",
  "snapshot-characterization",
  "rendered-behavior",
  "evidence-first",
];

const RED_GREEN_VERIFICATION_STRATEGIES = new Set([
  "vertical-tdd",
  "regression-first",
]);

function verification(task) {
  const compact = fieldValues(task, "Verify");
  const strategyEntry = compact.find((entry) => /^Strategy:\s*/i.test(entry));
  const commandSource = compact.length > 0
    ? compact.filter((entry) => !/^Strategy:\s*/i.test(entry))
    : fieldValues(task, "Commands");
  const commands = commandSource.map((entry) => {
    const match = entry.match(/^(M[1-9]\d*):\s*(.*)$/);
    return match
      ? { label: match[1], check: normalizeText(match[2]) }
      : { label: null, check: entry };
  });
  return {
    compact: compact.length > 0,
    strategy: normalizeText(
      strategyEntry
        ? strategyEntry.replace(/^Strategy:\s*/i, "")
        : field(task, "Verification Strategy")
    ) || "evidence-first",
    commands,
  };
}

function commandLabelProblems(task) {
  const problems = [];
  const seen = new Set();
  const labels = [];
  let malformed = false;
  let duplicate = false;
  const entries = verification(task).commands.map((entry) =>
    entry.label ? `${entry.label}: ${entry.check}` : entry.check
  );
  for (const entry of entries) {
    const command = entry.match(/^(M[1-9]\d*):\s*(.*)$/);
    if (!command) {
      malformed = true;
      problems.push({
        code: "invalid-command-label",
        message: `Command entry must use an M<n> label: ${entry}`,
      });
      continue;
    }
    if (seen.has(command[1])) {
      duplicate = true;
      problems.push({
        code: "duplicate-command-label",
        message: `Command label is duplicated: ${command[1]}.`,
      });
    }
    seen.add(command[1]);
    labels.push(command[1]);
    if (!isConcrete(command[2])) {
      problems.push({
        code: "missing-command-check",
        message: `${command[1]} must define a concrete public check.`,
      });
    }
  }
  if (!malformed && !duplicate) {
    const expected = labels.map((_, index) => `M${index + 1}`);
    if (labels.some((label, index) => label !== expected[index])) {
      problems.push({
        code: "noncontiguous-command-label",
        message:
          `Command labels must be contiguous and ordered: expected `
          + `${expected.join(", ") || "M1"}; found ${labels.join(", ") || "none"}.`,
      });
    }
    const evidenceLabels = [
      ...field(task, "Evidence").matchAll(/^\s*-\s*(M[1-9]\d*):/gim),
    ].map((match) => match[1]);
    const missing = labels.filter((label) => !evidenceLabels.includes(label));
    const unexpected = evidenceLabels.filter(
      (label, index) =>
        !labels.includes(label) || evidenceLabels.indexOf(label) !== index
    );
    if (missing.length > 0 || unexpected.length > 0) {
      problems.push({
        code: "evidence-label-mismatch",
        message:
          `Evidence labels must map one-to-one to Commands; missing: `
          + `${missing.join(", ") || "none"}; unexpected or duplicate: `
          + `${unexpected.join(", ") || "none"}.`,
      });
    }
  }
  return problems;
}

function taskStartContractProblems(task) {
  const mode = normalizeText(field(task, "Mode")).toLowerCase()
    || "implementation";
  const touch = fieldValues(task, "Touch");
  if (mode && !SUPPORTED_MODES.has(mode)) {
    return [
      {
        code: "unsupported-mode",
        message:
          `Unsupported Mode \`${mode}\`; expected implementation, `
          + "diagnose-only, or plan-first.",
      },
    ];
  }
  if (mode === "diagnose-only") {
    if (touch.length !== 1 || touch[0].toLowerCase() !== "none") {
      return [
        {
          code: "invalid-touch",
          message: "diagnose-only requires `Touch: none`.",
        },
      ];
    }
    return commandLabelProblems(task);
  }
  if (!touch.some((entry) => isConcrete(entry))) {
    return [
      {
        code: "invalid-touch",
        message: "implementation and plan-first require a concrete Touch path.",
      },
      ...commandLabelProblems(task),
    ];
  }
  return commandLabelProblems(task);
}

function requiredFieldProblems(task) {
  const compact = isConcrete(field(task, "Verify"));
  const required = compact
    ? ["Covers", "Verify", "Evidence"]
    : [
        "Owner",
        "Mode",
        "Covers",
        "Read",
        "Commands",
        "Acceptance",
        "Candidate Boundary",
        "Stop Rules",
        "Evidence",
        "Report",
      ];
  const problems = required
    .filter((name) => !isConcrete(field(task, name)))
    .map((name) => ({
      code: "missing-field",
      message: `${name} must be concrete.`,
    }));
  if (
    !compact
    && !isConcrete(field(task, "Autonomy boundary"))
    && !isConcrete(field(task, "Stop if"))
  ) {
    problems.push({
      code: "missing-boundary",
      message: "Stop if or Autonomy boundary must be concrete.",
    });
  }
  return problems;
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.keys(value)
      .sort()
      .map((key) => [key, canonical(value[key])])
  );
}

function headingSections(content, pattern) {
  const lines = content.split(/\r?\n/);
  const starts = [];
  for (let index = 0; index < lines.length; index += 1) {
    const match = lines[index].match(pattern);
    if (match) starts.push({ title: match[1].trim(), line: index });
  }
  return starts.map((item, index) => {
    const end = index + 1 < starts.length ? starts[index + 1].line : lines.length;
    return {
      title: item.title,
      content: lines.slice(item.line, end).join("\n"),
    };
  });
}

function scenarioOutcomes(content) {
  return [
    ...content.matchAll(
      /^\s*-\s*\*\*(?:THEN|AND THEN)\*\*\s*(.+?)\s*$/gim
    ),
  ].map((match) => normalizeText(match[1]));
}

function specAuthority(repo, change, reference) {
  const parts = reference.split("/").map((part) => part.trim());
  if (parts.length < 2 || parts.length > 3) return null;
  const [capability, requirementName, scenarioName] = parts;
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(capability)) return null;
  const candidates = [
    path.join(
      repo,
      "openspec",
      "changes",
      change,
      "specs",
      capability,
      "spec.md"
    ),
    path.join(repo, "openspec", "specs", capability, "spec.md"),
  ];
  for (const specPath of candidates) {
    if (!fs.existsSync(specPath)) continue;
    const content = fs.readFileSync(specPath, "utf8");
    const requirements = headingSections(
      content,
      /^### Requirement:\s*(.+?)\s*$/
    ).filter((item) => item.title === requirementName);
    if (requirements.length === 0) continue;
    if (requirements.length > 1) {
      return {
        diagnostic: {
          code: "ambiguous-covers",
          message: `Covers reference is duplicated: ${reference}.`,
        },
      };
    }
    const requirement = requirements[0];
    let selected = requirement;
    let kind = "requirement";
    let anchor = `Requirement:${requirementName}`;
    if (scenarioName) {
      const scenarios = headingSections(
        requirement.content,
        /^#### Scenario:\s*(.+?)\s*$/
      ).filter((item) => item.title === scenarioName);
      if (scenarios.length !== 1) {
        return {
          diagnostic: {
            code: scenarios.length > 1 ? "ambiguous-covers" : "unresolved-covers",
            message:
              `${scenarios.length > 1 ? "Duplicated" : "Missing"} Covers `
              + `scenario: ${reference}.`,
          },
        };
      }
      selected = scenarios[0];
      kind = "scenario";
      anchor = `Scenario:${scenarioName}`;
    }
    return {
      authority: {
        kind,
        reference,
        source:
          `${path.relative(repo, specPath).replace(/\\/g, "/")}#${anchor}`,
        text: normalizeText(selected.content),
        acceptance: scenarioOutcomes(selected.content),
      },
    };
  }
  return {
    diagnostic: {
      code: "unresolved-covers",
      message: `Covers reference could not be resolved: ${reference}.`,
    },
  };
}

function criticalAuthority(repo, change, reference) {
  if (!/^[DFAQ]\d+$/.test(reference)) return null;
  const designPath = path.join(
    repo,
    "openspec",
    "changes",
    change,
    "design.md"
  );
  if (!fs.existsSync(designPath)) {
    return {
      diagnostic: {
        code: "unresolved-covers",
        message: `Covers critical statement is missing: ${reference}.`,
      },
    };
  }
  const content = fs.readFileSync(designPath, "utf8");
  const matches = [
    ...content.matchAll(
      new RegExp(`^\\s*${reference}\\s*[—-]\\s*(.+?)\\s*$`, "gmi")
    ),
  ];
  if (matches.length !== 1) {
    return {
      diagnostic: {
        code: matches.length > 1 ? "ambiguous-covers" : "unresolved-covers",
        message:
          `${matches.length > 1 ? "Duplicated" : "Missing"} Covers critical `
          + `statement: ${reference}.`,
      },
    };
  }
  return {
    authority: {
      kind: "critical-statement",
      reference,
      source:
        `${path.relative(repo, designPath).replace(/\\/g, "/")}#${reference}`,
      text: normalizeText(matches[0][1]),
      acceptance: [],
    },
  };
}

function resolveAuthority(repo, change, task) {
  const authority = [];
  const diagnostics = [];
  const source = `openspec/changes/${change}/tasks.md#${task.id}`;
  const expanded = fieldValues(task, "Covers")
    .map(normalizeText)
    .filter(Boolean)
    .flatMap((entry) =>
      /^(?:[DFAQ]\d+)(?:\s*,\s*[DFAQ]\d+)*$/.test(entry)
        ? entry.split(",").map((item) => item.trim())
        : [entry]
    );
  const seen = new Set();
  for (const entry of expanded) {
    if (seen.has(entry)) {
      diagnostics.push({
        code: "duplicate-covers",
        message: `Covers reference is duplicated: ${entry}.`,
      });
    }
    seen.add(entry);
  }
  const entries = [...seen].sort();
  for (const entry of entries) {
    const critical = criticalAuthority(repo, change, entry);
    if (critical) {
      if (critical.diagnostic) diagnostics.push(critical.diagnostic);
      if (critical.authority) authority.push(critical.authority);
      continue;
    }
    const spec = specAuthority(repo, change, entry);
    if (spec) {
      if (spec.diagnostic) diagnostics.push(spec.diagnostic);
      if (spec.authority) authority.push(spec.authority);
      continue;
    }
    const match = entry.match(/^([A-Za-z]\d+)\s*:\s*(.+)$/);
    authority.push({
      kind: "legacy-task-reference",
      reference: match ? match[1] : entry,
      source,
      text: match ? match[2] : entry,
      acceptance: match && /^E\d+$/i.test(match[1]) ? [match[2]] : [],
    });
  }
  authority.sort((left, right) => left.reference.localeCompare(right.reference));
  return { authority, diagnostics };
}

function coupledDesignContract(repo, change) {
  const designPath = path.join(
    repo,
    "openspec",
    "changes",
    change,
    "design.md"
  );
  if (!fs.existsSync(designPath)) return "";
  const content = fs.readFileSync(designPath, "utf8");
  const match = content.match(
    /^## Coupled Iteration Contract\s*$([\s\S]*?)(?=^##\s+|$(?![\s\S]))/m
  );
  return match ? normalizeText(match[1]) : "";
}

function couplingProblems(task, mode, designContract, compact) {
  if (!/^(?:none|required)$/.test(mode)) {
    return [{
      code: "invalid-coupling",
      message: "Coupling must be `none` or `required`.",
    }];
  }
  const candidateBoundary = normalizedValues(task, "Candidate Boundary", {
    ordered: true,
  });
  if (
    mode === "none"
    && compact
    && candidateBoundary.some((item) => !/^not applicable\b/i.test(item))
  ) {
    return [{
      code: "contradictory-coupling-authority",
      message: "Coupling none cannot define a coupled Candidate Boundary.",
    }];
  }
  if (mode === "none") return [];

  const requiredLabels = [
    "Coupled artifacts",
    "Invalidation triggers",
    "Required regeneration",
    "Final assertions",
    "Conflict authority",
    "Baseline policy",
  ];
  const missingLabels = requiredLabels.filter(
    (label) =>
      !new RegExp(`(?:^| )- ${label}:\\s+\\S`, "i").test(designContract)
  );
  const problems = [];
  if (
    !candidateBoundary.some(
      (item) => isConcrete(item) && !/^not applicable\b/i.test(item)
    )
  ) {
    problems.push({
      code: "missing-coupling-authority",
      message: "Coupling required needs a concrete Candidate Boundary.",
    });
  }
  if (!designContract || missingLabels.length > 0) {
    problems.push({
      code: "missing-coupled-contract",
      message:
        "Coupling required needs a complete Coupled Iteration Contract"
        + (missingLabels.length > 0 ? ` (${missingLabels.join(", ")}).` : "."),
    });
  }
  if (
    !normalizedValues(task, "Stop Rules", { ordered: true }).some(isConcrete)
    && !normalizedValues(task, "Stop if", { ordered: true }).some(isConcrete)
  ) {
    problems.push({
      code: "missing-coupling-authority",
      message: "Coupling required needs concrete task Stop Rules.",
    });
  }
  return problems;
}

function compileTaskContract(repo, change, task) {
  const mode = normalizeText(field(task, "Mode")).toLowerCase()
    || "implementation";
  const resolved = resolveAuthority(repo, change, task);
  resolved.diagnostics.push(
    ...requiredFieldProblems(task),
    ...taskStartContractProblems(task)
  );
  const authority = resolved.authority;
  const taskVerification = verification(task);
  const explicitAcceptance = normalizedValues(task, "Acceptance", {
    ordered: true,
  });
  const derivedAcceptance =
    !taskVerification.compact && explicitAcceptance.length > 0
      ? []
      : authority.flatMap((item) => item.acceptance || []);
  if (taskVerification.compact) {
    const legacyStrategy = normalizeText(field(task, "Verification Strategy"));
    const legacyCommands = fieldValues(task, "Commands").map(normalizeText);
    const compactCommands = taskVerification.commands.map((item) =>
      item.label ? `${item.label}: ${item.check}` : item.check
    );
    if (
      (legacyStrategy && legacyStrategy !== taskVerification.strategy)
      || (
        legacyCommands.length > 0
        && JSON.stringify(legacyCommands) !== JSON.stringify(compactCommands)
      )
    ) {
      resolved.diagnostics.push({
        code: "legacy-field-conflict",
        message:
          "Expanded Verification Strategy or Commands conflict with compact Verify.",
      });
    }
  }
  if (
    !SUPPORTED_VERIFICATION_STRATEGIES.includes(
      taskVerification.strategy.toLowerCase()
    )
  ) {
    resolved.diagnostics.push({
      code: "unsupported-verification-strategy",
      message:
        `Verification strategy is unsupported: ${taskVerification.strategy}; `
        + `supported: ${SUPPORTED_VERIFICATION_STRATEGIES.join(", ")}.`,
    });
  }
  const couplingMode = normalizeText(field(task, "Coupling")).toLowerCase()
    || "none";
  const candidateBoundary = normalizedValues(task, "Candidate Boundary", {
    ordered: true,
  });
  const coupledContract = couplingMode === "required"
    ? coupledDesignContract(repo, change)
    : "";
  resolved.diagnostics.push(
    ...couplingProblems(
      task,
      couplingMode,
      coupledContract,
      taskVerification.compact
    )
  );
  const baseRead = [
    `openspec/changes/${change}/design.md`,
    `openspec/changes/${change}/proposal.md`,
    `openspec/changes/${change}/specs/**/*.md`,
    `openspec/changes/${change}/tasks.md`,
  ];
  const read = [
    ...new Set([...baseRead, ...normalizedValues(task, "Read")]),
  ].sort();
  const explicitAutonomy = normalizedValues(task, "Autonomy boundary", {
    ordered: true,
  });
  const autonomy = [...explicitAutonomy];
  if (!autonomy.some((item) => /^Default:/i.test(item))) {
    autonomy.unshift("Default: hard-stop");
  }
  if (!autonomy.some((item) => /^Pre-authorized fallback:/i.test(item))) {
    autonomy.push("Pre-authorized fallback: none");
  }
  const questionIds = [
    ...new Set(field(task, "Covers").match(/\bQ\d+\b/g) || []),
  ];
  const fallback = autonomy.find((item) =>
    /^Pre-authorized fallback:/i.test(item)
  ) || "";
  if (
    questionIds.length > 0
    && !isConcrete(fallback.replace(/^Pre-authorized fallback:\s*/i, ""))
  ) {
    resolved.diagnostics.push(...questionIds.map((questionId) => ({
      code: "unresolved-authority",
      message:
        `${questionId} requires documented design authority and an authorized `
        + "fallback before implementation.",
    })));
  }
  const capsule = {
    schema: "keel-task-capsule/v1",
    defaultsVersion: 1,
    task: {
      change,
      id: task.id,
      title: normalizeText(task.title),
    },
    owner: normalizeText(field(task, "Owner")) || "keel-agent",
    mode,
    authority,
    read,
    touch: normalizedValues(task, "Touch"),
    acceptance: [...new Set([...derivedAcceptance, ...explicitAcceptance])],
    verification: {
      strategy: taskVerification.strategy,
      commands: taskVerification.commands.filter((entry) => entry.label),
    },
    boundaries: {
      autonomy,
      stop: [
        ...normalizedValues(task, "Stop Rules", { ordered: true }),
        ...normalizedValues(task, "Stop if", { ordered: true }),
      ],
    },
    coupling: {
      mode: couplingMode,
      candidateBoundary:
        couplingMode === "required" ? candidateBoundary : [],
      designContract: coupledContract,
    },
    helperAuthority: "read-only-evidence-only",
    prohibitions: [
      "must not change Acceptance",
      "must not commit",
      "must not continue to another task",
      "must not mark tasks complete",
      "must not push",
      "must not sync or archive",
      "must not transfer Keel ownership",
      ...(mode === "diagnose-only" ? ["must not write product files"] : []),
    ],
  };
  if (resolved.diagnostics.length > 0) {
    return {
      schema: capsule.schema,
      capsule: null,
      fingerprint: null,
      diagnostics: resolved.diagnostics,
    };
  }
  const serialized = JSON.stringify(canonical(capsule));
  const fingerprint = crypto
    .createHash("sha256")
    .update(serialized, "utf8")
    .digest("hex");
  return {
    schema: capsule.schema,
    capsule,
    fingerprint: {
      algorithm: "sha256",
      value: fingerprint,
    },
    diagnostics: resolved.diagnostics,
  };
}

function loadTaskContract(repo, change, taskId) {
  const tasksPath = path.join(repo, "openspec", "changes", change, "tasks.md");
  if (!fs.existsSync(tasksPath)) return null;
  const task = parseTasks(fs.readFileSync(tasksPath, "utf8")).find(
    (candidate) => candidate.id === taskId
  );
  if (!task) return null;
  return {
    task,
    tasksPath,
    contract: compileTaskContract(repo, change, task),
  };
}

module.exports = {
  RED_GREEN_VERIFICATION_STRATEGIES,
  SUPPORTED_VERIFICATION_STRATEGIES,
  compileTaskContract,
  field,
  isConcrete,
  loadTaskContract,
  parseTasks,
  taskStartContractProblems,
};

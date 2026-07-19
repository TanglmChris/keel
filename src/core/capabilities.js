"use strict";

// Keel 4.1.0 capability contract.

const fs = require("fs");
const os = require("os");
const path = require("path");
const { guardStatus } = require("./guard");

const CAPABILITY_COMMANDS = {
  "continuity.start": "keel project --target <target> --event startup --json",
  "continuity.reinject":
    "keel project --target <target> --event resume --json",
  "gate.task-start": "keel gate task-start --change <change> --task <task> --json",
  "gate.task-complete":
    "keel gate task-complete --change <change> --task <task> --json",
  "gate.change-close":
    "keel gate change-close --change <change> --action <sync|archive> --json",
  "execution.goal":
    "keel project --target <target> --event goal --authorize goal --json",
  "execution.task-view":
    "keel project --target <target> --event task-view --authorize task-view --json",
  "execution.worktree":
    "keel project --target <target> --event worktree --expected-owner <owner> --json",
  "delegation.context":
    "keel project --target <target> --event subagent-start --authorize subagent --json",
  "delegation.return":
    "keel project --target <target> --event subagent-stop --authorize subagent --json",
};

const SUPPORTED_TARGETS = new Set(["claude", "codex", "opencode"]);

function codexHome() {
  const configured = (process.env.CODEX_HOME || "").trim();
  return path.resolve(configured || path.join(os.homedir(), ".codex"));
}

function pluginObservation(repo, target) {
  if (target === "opencode") {
    return "OpenCode has no v4 native plugin surface; manual CLI compatibility only";
  }
  const manifestRelative = path.join(
    "plugins",
    "keel",
    target === "codex" ? ".codex-plugin" : ".claude-plugin",
    "plugin.json"
  );
  const manifestPath = path.join(repo, manifestRelative);
  let sourceState = `plugin source absent at ${manifestRelative}`;
  if (fs.existsSync(manifestPath)) {
    try {
      const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
      sourceState =
        manifest.name === "keel" && manifest.version
          ? `plugin source valid at ${manifestRelative} (version ${manifest.version})`
          : `plugin source invalid at ${manifestRelative}`;
    } catch {
      sourceState = `plugin source unreadable at ${manifestRelative}`;
    }
  }
  return (
    `${sourceState}; installed/enabled/trusted/active/behavior-verified plugin `
      + "states need native runtime evidence and remain advisory or manual "
      + "until probed"
  );
}

function targetObservation(repo, target) {
  const observations = [];
  observations.push(pluginObservation(repo, target));

  if (target === "claude") {
    const hook = path.join(
      repo,
      ".claude",
      "hooks",
      "keel-gate",
      "keel-gate.js"
    );
    const settings = path.join(repo, ".claude", "settings.json");
    if (fs.existsSync(hook) && fs.existsSync(settings)) {
      observations.push(
        "Claude hook files and project settings are present; runtime trust, "
          + "activation, and reliable blocking are not verifiable"
      );
    } else {
      observations.push("Claude hook activation evidence is incomplete");
    }
  } else if (target === "codex") {
    const hooks = path.join(codexHome(), "hooks.json");
    observations.push(
      fs.existsSync(hooks)
        ? "Codex hook-like state exists but enablement, trust, version, and "
            + "blocking behavior are unverified"
        : "Codex activation evidence is unavailable"
    );
  } else {
    const plugins = path.join(repo, ".opencode", "plugins");
    observations.push(
      fs.existsSync(plugins)
        ? "OpenCode plugin state exists but enablement, version, and blocking "
            + "behavior are unverified"
        : "OpenCode activation evidence is unavailable"
    );
  }
  return observations.join("; ");
}

function probeCapabilities(repo, target) {
  if (!SUPPORTED_TARGETS.has(target)) {
    throw new Error(`unsupported target: ${target}`);
  }
  const observation = targetObservation(repo, target);
  const capabilities = {};
  for (const [key, command] of Object.entries(CAPABILITY_COMMANDS)) {
    capabilities[key] = {
      level: "manual",
      surface: "explicit Keel Core command",
      evidence: observation,
      command,
    };
  }
  return {
    schemaVersion: 1,
    target,
    capabilities,
    helper: helperDiagnostics(repo, target, observation),
    guard: guardDiagnostics(repo, target),
    compaction: compactionDiagnostics(target),
    warnings: [
      "No capability is promoted above manual without verifiable runtime "
        + "activation, trust, version, and behavior evidence.",
      "Helper absence never disables current-agent goal execution; goal, "
        + "gates, and the manual loop stay usable without any helper.",
    ],
  };
}

function helperDiagnostics(repo, target, observation) {
  // Each dimension is reported separately with its own enforced/advisory/manual
  // level: byte-stability and nested-delegation prevention are enforced by Keel
  // Core deterministically, native tool restriction and discovery stay advisory
  // until runtime-probed, and actual native helper execution stays manual.
  return {
    discovery: {
      level: "advisory",
      evidence: observation,
    },
    toolRestriction: {
      level: "advisory",
      evidence:
        "Native helper tool allowlists are runtime-configured and cannot be "
          + "verified from Keel Core.",
    },
    nestedDelegationPrevention: {
      level: "enforced",
      evidence:
        "keel project helper compiles a non-delegating brief and refuses "
          + "nested helpers or spawned agents.",
    },
    byteStability: {
      level: "enforced",
      evidence:
        "keel project helper --verify accepts a return only after before/after "
          + "repository byte identity and never cleans up.",
    },
    execution: {
      level: "manual",
      evidence:
        "Native bounded-helper execution stays manual until runtime activation, "
          + "trust, and tool restriction are probed.",
    },
  };
}

function guardDiagnostics(repo, target) {
  // The write guard is Claude-only in v4: the plugin ships a deterministic
  // manifest-gated PreToolUse denial, but runtime activation, trust, and
  // reliable blocking cannot be verified from Keel Core, so the shipped
  // level stays advisory until behaviorally probed. Other targets have no
  // verified guard hook surface and stay manual.
  if (target !== "claude") {
    return {
      enforcement: {
        level: "manual",
        evidence:
          `${target} has no verified native guard hook surface; the Touch `
          + "write boundary stays disciplinary via the resident protocol.",
      },
    };
  }
  const manifestState = guardStatus(repo).status;
  return {
    hookDelivery: {
      level: "advisory",
      evidence:
        "The keel plugin ships a manifest-gated PreToolUse hook; runtime "
        + "activation, trust, and enablement need native runtime evidence.",
    },
    manifest: {
      level: "advisory",
      evidence: `keel/guard.json state observed as ${manifestState}.`,
    },
    enforcement: {
      level: "advisory",
      evidence:
        "Out-of-Touch denial is deterministic in the shipped hook; promotion "
        + "above advisory requires behavioral runtime probe evidence of an "
        + "actual blocked call.",
    },
    boundary: {
      level: "advisory",
      evidence:
        "The guard covers file-edit tools only (Edit, Write, NotebookEdit); "
        + "Bash and other indirect writes stay disciplinary, and paths outside "
        + "the repository are not product writes.",
    },
  };
}

function compactionDiagnostics(target) {
  // Pre-compaction preservation is probed, not assumed: no pre-compaction
  // hook is registered anywhere until a behavioral probe proves the contract,
  // so the shipped behavior is post-compact reinjection on Claude and the
  // manual `keel project --event compaction` command elsewhere.
  if (target === "claude") {
    return {
      postCompactReinjection: {
        level: "advisory",
        evidence:
          "The plugin SessionStart hook reinjects the recomputed task pointer "
          + "after a compact-source start; delivery of the compact source "
          + "needs native runtime evidence.",
      },
      preCompaction: {
        level: "manual",
        evidence:
          "No pre-compaction hook is registered; the pre-compaction "
          + "preservation contract stays unverified until behaviorally "
          + "probed, and post-compact reinjection is the shipped fallback.",
      },
    };
  }
  return {
    postCompactReinjection: {
      level: "manual",
      evidence:
        `${target} has no verified compaction hook surface; reinject manually `
        + `with keel project --target ${target} --event compaction --json.`,
    },
    preCompaction: {
      level: "manual",
      evidence:
        "No verified pre-compaction surface; manual post-compaction "
        + "reinjection is the declared fallback.",
    },
  };
}

function renderCapabilities(result) {
  const lines = [`Target capabilities (${result.target}):`];
  for (const [key, capability] of Object.entries(result.capabilities)) {
    lines.push(
      `${key}: ${capability.level} - ${capability.evidence}; `
        + `command: ${capability.command}`
    );
  }
  if (result.helper) {
    for (const [dimension, entry] of Object.entries(result.helper)) {
      lines.push(`helper ${dimension}: ${entry.level} - ${entry.evidence}`);
    }
  }
  if (result.guard) {
    for (const [dimension, entry] of Object.entries(result.guard)) {
      lines.push(`guard ${dimension}: ${entry.level} - ${entry.evidence}`);
    }
  }
  if (result.compaction) {
    for (const [dimension, entry] of Object.entries(result.compaction)) {
      lines.push(`compaction ${dimension}: ${entry.level} - ${entry.evidence}`);
    }
  }
  for (const warning of result.warnings) lines.push(`capability warning: ${warning}`);
  return `${lines.join("\n")}\n`;
}

module.exports = {
  CAPABILITY_COMMANDS,
  probeCapabilities,
  renderCapabilities,
};

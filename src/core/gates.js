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

// The documented order is gate-then-checkbox, so first-unchecked is the right
// inference for task-start and stays. The hazard is narrower: completing without
// an explicit task infers a task that has not started, then reports its
// readiness problems under a selection heading the author reads as the failure
// of the task they just finished. A task that has started records a fingerprint
// in its Evidence `Contract` anchor, so that anchor is what makes the inference
// safe — and without one there is nothing for completion to compare against.
function recordedAnchor(selection, task) {
  const plan = contractAnchorPlan(selection, task);
  return plan ? anchoredFingerprint(plan.previous) : null;
}

function hasRecordedAnchor(selection, task) {
  return Boolean(recordedAnchor(selection, task));
}

// The anchor was parsed, shape-checked, and then discarded: completion asked
// whether sixty-four hex characters were present and never whether they were
// the ones this task compiles to. `keel context` and `keel guard status` both
// already compared, and two shipped requirements already described completion
// as comparing, so this is the one surface that did not do what was written
// down about it. A digest that matches can only have come from the schema that
// produced it, so the `keel-task-capsule/v1` prefix is diagnostic detail here
// rather than a second thing to require.
function contractDriftProblem(recorded, contract) {
  if (!recorded || recorded === contract.fingerprint.value) return null;
  return problem(
    "contract-drift",
    `The Evidence \`Contract\` anchor records sha256:${recorded}, but this `
      + `task now compiles to ${contract.fingerprint.algorithm}:`
      + `${contract.fingerprint.value} under ${contract.schema}. The contract `
      + "changed after the anchor was recorded, so the authority this task was "
      + "implemented under is not the authority it is being judged against. "
      + "Reauthorize with `keel gate task-start --record`, which rewrites the "
      + "anchor in place; execution evidence produced under the previous "
      + "contract is stale and has to be cleared or re-verified first."
  );
}

// A task that recorded no anchor has no drift detection at all while presenting
// as fully gated: completion skipped the comparison rather than reporting that
// it had nothing to compare. Recording is already the documented step; this is
// what makes the guarantee unconditional instead of aspirational.
function missingAnchorProblem(selection, task) {
  if (hasRecordedAnchor(selection, task)) return null;
  return problem(
    "missing-contract-anchor",
    `${selection.change}#${task.id} records no compiled fingerprint in its `
      + "Evidence `Contract` anchor, so completion has nothing to compare and "
      + "the task has no drift detection. Run `keel gate task-start --record` "
      + "for this task, which rewrites the anchor in place, then complete it."
  );
}

function unstartedInferenceProblem(selection) {
  const task = selection.selected[0];
  if (hasRecordedAnchor(selection, task)) return null;
  const checked = [...selection.tasks].filter((item) => item.checked).pop();
  return problem(
    "ambiguous-completion-selection",
    `task-complete inferred ${selection.change}#${task.id}, the first unchecked `
      + "task, but that task records no start fingerprint in its Evidence "
      + "`Contract` anchor, so it has not started and there is nothing to "
      + `compare. ${
        checked
          ? `The most recently checked task is ${checked.id}. `
          : ""
      }Name the task you mean with \`--task\`, or run \`task-start --record\` `
      + "first."
  );
}

function contractAnchorPlan(selection, task) {
  const lines = selection.content.split("\n");
  // The task carries its own extent, so the anchor search cannot reach a
  // `- Contract:` line sitting in a trailing change-level section.
  const end = task.endLine !== undefined ? task.endLine : lines.length;
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

// Two tasks in one change declaring the same Touch set, both driven red-green,
// are shaped like one behavior split in half. Issue #41 records the case that
// produced this: a split that passed task-start and the Slice Start Gate and
// was not executable — implementing the first alone broke a shipping scenario,
// and once it was right the second had no honest red left.
//
// A warning, deliberately, not a `needs-review`. A genuine vertical split can
// share files, so the shape is a signal rather than a verdict; and there is no
// way to acknowledge a `needs-review`, so making it one would leave a
// legitimate split unstartable. The reader is given the other task's id and
// compares two things, rather than being told something is wrong.
function taskShapeWarnings(repo, selection, task, compiled) {
  if (!compiled || compiled.diagnostics.length > 0) return [];
  const strategy = compiled.capsule.verification.strategy.toLowerCase();
  if (!RED_GREEN_VERIFICATION_STRATEGIES.has(strategy)) return [];
  const touch = [...compiled.capsule.touch].sort().join("\n");
  if (!touch) return [];
  const matches = [];
  for (const sibling of selection.tasks) {
    if (sibling.id === task.id) continue;
    const other = compileTaskContract(repo, selection.change, sibling);
    if (other.diagnostics.length > 0) continue;
    if ([...other.capsule.touch].sort().join("\n") !== touch) continue;
    matches.push(sibling.id);
  }
  if (matches.length === 0) return [];
  return [
    `Task ${task.id} declares the same Touch set as `
      + `${matches.join(", ")} and both are driven ${strategy}. Two tasks over `
      + "the same files under a red-green strategy are often one behavior "
      + "split in half, where the first half is wrong on its own and the "
      + "second has no honest red left. This is a prompt, not a verdict — a "
      + "genuine vertical split can share files. Compare them before "
      + "implementing.",
  ];
}

function taskStart(repo, options) {
  const selection = loadSelection(repo, options);
  const task = selection.selected[0];
  const compiled = compileTaskContract(repo, selection.change, task);
  const problems = [
    ...compiled.diagnostics,
    ...invalidationProblems(repo, selection.content, selection.tasks),
  ];
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
    taskShapeWarnings(repo, selection, task, compiled),
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

// The durable-owner forms that are pure shape checks, shared by the Review
// Findings check and the Expectation Coverage check so a form added to one is
// never missing from the other. Gates run without network and have never
// confirmed that an archive path resolves either, so an external tracker
// reference is no less checkable than what was already accepted; whether the
// owner is real stays a Review judgment.
const TRACKER_REFERENCE = /\bhttps?:\/\/\S/i;

// The owner forms, stated once so every refusal that lists them agrees with
// every other and with what the checks below actually accept.
const DURABLE_OWNER_FORMS =
  "an absolute `https://…` tracker reference, or any repo-relative path that "
  + "exists — `keel/archive/…`, an `openspec/changes/…` artifact, or the "
  + "repository's own ledger; `keel/HANDOFF.md` is a pointer override rather "
  + "than an owner";

// Classify a declared `Durable owner:` value. A gate runs without network, so a
// URL is accepted on shape alone; a path is the one form it can actually check,
// and checking it is stricter than the prefix whitelist this replaced.
function durableOwnerVerdict(repo, value) {
  const owner = String(value || "").trim();
  if (!owner) return { ok: false, reason: "unrecognized" };
  if (/keel\/HANDOFF\.md/i.test(owner)) return { ok: false, reason: "handoff" };
  if (TRACKER_REFERENCE.test(owner)) return { ok: true };
  const candidate = owner.match(/[A-Za-z0-9._-]+(?:\/[A-Za-z0-9._-]+)+/);
  if (!candidate) return { ok: false, reason: "unrecognized" };
  if (fs.existsSync(path.join(repo, candidate[0]))) return { ok: true };
  return { ok: false, reason: "missing", path: candidate[0] };
}

// A finding has three dispositions and the gate recognized two. One found and
// fixed inside the task recording it has no owner to name and nothing to
// discard, so the only text that passed was `Discard reason:` — filing a repair
// as a dismissal. This capability and `keel-review-checklist` both already
// scoped the ownership requirement to an *unresolved* finding; only the
// implementation applied it to all of them. `## Invalidates` has carried the
// same third slot since it shipped, where `Updated by:` names tasks of this
// change.
// The capture is the single token after the marker, not the rest of the line.
// Findings is one line of free prose that normally holds several findings with
// different dispositions, so a capture reaching to the newline swallows every
// marker after it — a block recording one fix and one tracker-owned follow-up
// was refused because the *follow-up's* URL was read as the *fix's* evidence.
// Measured on this change's own task 1.3. The match is global because each
// resolved claim owes its own evidence; checking only the first would let a
// second one assert itself for free.
const RESOLVED_HERE = /\bresolved here\s*:[ \t]*(\S*)/gi;

// Resolution evidence is deliberately narrower than a durable owner. An
// `http`/`https` reference says someone else will do the work later, which is
// exactly the durable-owner state; what proves a fix is the check that covers
// it or the artifact that shows it. A bare marker is refused because a
// disposition that asserts its own conclusion would be a way out of the other
// two, and the third state would decay into the easiest exit.
function resolutionEvidenceVerdict(repo, value, commands) {
  const evidence = String(value || "").trim();
  if (!evidence) return { ok: false, reason: "empty" };
  // The tracker form is tested before the path form: a URL contains something
  // shaped like a path, so leaving it to fall through would refuse
  // `https://…/issues/43` by reporting that `github.com/…/issues/43` is not a
  // file — a true sentence about the wrong thing.
  if (TRACKER_REFERENCE.test(evidence)) return { ok: false, reason: "tracker" };
  const cited = evidence.match(/\bM\d+\b/);
  if (cited) {
    if (commands.includes(cited[0])) return { ok: true };
    return { ok: false, reason: "unknown-check", label: cited[0] };
  }
  const candidate = evidence.match(/[A-Za-z0-9._-]+(?:\/[A-Za-z0-9._-]+)+/);
  if (!candidate) return { ok: false, reason: "unrecognized" };
  if (fs.existsSync(path.join(repo, candidate[0]))) return { ok: true };
  return { ok: false, reason: "missing", path: candidate[0] };
}

function resolutionEvidenceMessage(verdict) {
  const lead = "Review Findings records a finding as resolved here, but its "
    + "evidence is not usable — ";
  const tail = " Resolution evidence is an `M<n>` check this task declares, or "
    + "a repo-relative path that exists.";
  if (verdict.reason === "empty") {
    return `${lead}the marker names nothing at all.${tail}`;
  }
  if (verdict.reason === "tracker") {
    return `${lead}a tracker reference says the work is owned elsewhere, which `
      + "is the durable-owner state, not a proof that this task fixed it. Write "
      + `\`Durable owner:\` instead, or name what proves the fix.${tail}`;
  }
  if (verdict.reason === "unknown-check") {
    return `${lead}${verdict.label} is not a check this task declares.${tail}`;
  }
  if (verdict.reason === "missing") {
    return `${lead}\`${verdict.path}\` does not exist.${tail}`;
  }
  return `${lead}it names neither a check nor a path.${tail}`;
}

function findingOwnerIsDurable(repo, findings) {
  if (/keel\/HANDOFF\.md/i.test(findings)) return false;
  if (/\b(?:explicit\s+)?discard (?:reason|rationale)\s*:/i.test(findings)) {
    return true;
  }
  if (TRACKER_REFERENCE.test(findings)) return true;
  // A path counts here only when it is named as the owner. Findings is free
  // prose, and a finding that merely mentions the source file it concerns has
  // not thereby given that finding an owner.
  const declared = findings.match(/Durable owner:\s*(\S[^\n]*)/i);
  if (declared) return durableOwnerVerdict(repo, declared[1]).ok;
  const artifact = findings.match(
    /\b(openspec\/changes\/[A-Za-z0-9][A-Za-z0-9._-]*\/(?:proposal|design|tasks)\.md)(?:#\d+(?:\.\d+)*)?/i
  );
  if (artifact && fs.existsSync(path.join(repo, artifact[1]))) return true;
  return /\bkeel\/archive\/[A-Za-z0-9._/-]+/i.test(findings)
    && fs.existsSync(
      path.join(
        repo,
        findings.match(/\bkeel\/archive\/[A-Za-z0-9._/-]+/i)[0]
      )
    );
}

// Read in `-z` form, because every other form escapes. Git octal-escapes any
// path holding a non-ASCII byte and quotes it; `core.quotepath=false` removes
// the octal and still quotes a space, a quote, or a backslash; and `status`
// and `diff` do not agree on which cases they quote. `-z` emits raw bytes in
// all of them, which deletes the decoding problem rather than adding a
// decoder — and it is a flag rather than a repository setting, so the answer
// does not depend on how the repository happens to be configured.
//
// Nothing rewrites backslashes here any more. Git emits forward slashes on
// every platform, so the rewrite normalized a separator that never arrives
// while turning `\346` into `/346`, which is how a path declared on the first
// line of Touch was reported as outside Touch (issue #40).
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

// No separator rewriting on either side. Git emits forward slashes on every
// platform, so rewriting backslashes normalized a separator that never
// arrives — and it did so on the Touch entry and on the candidate, two wrongs
// that cancelled for a filename holding a literal backslash while making
// `src/back/slash.js` in Touch match a changed `src/back\slash.js`, a file the
// task never declared.
function pathAllowed(candidate, touch) {
  return touch.some((entry) => {
    const normalized = entry.replace(/^\.\//, "");
    if (normalized.endsWith("/")) return candidate.startsWith(normalized);
    if (normalized.includes("*")) return globPattern(normalized).test(candidate);
    return candidate === normalized;
  });
}

// A base comparison shows that a path changed, never who changed it. When a
// task of the same change is already checked complete and declares the path in
// its own Touch, blaming the selected task is a guess — and the wrong one often
// enough that the per-task commit habit became an implicit requirement whose
// diagnostic named a file the author never touched. Only a checked sibling
// counts: an unchecked task's Touch is a plan, not a record.
function completedSiblingOwners(tasks, selected) {
  const owners = [];
  for (const item of tasks || []) {
    if (item.id === selected.id || !item.checked) continue;
    const declared = touchEntries(item);
    if (declared.length > 0) owners.push({ id: item.id, touch: declared });
  }
  return owners;
}

function scopeEvidence(
  repo,
  task,
  base,
  contract = null,
  change = null,
  tasks = null
) {
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
  // `-z` for the same reason as `gitPaths`: `--name-only` escapes a non-ASCII
  // path to octal, and it does not quote the same cases `status` quotes.
  const diff = spawnSync(
    "git",
    ["diff", "--name-only", "-z", base, "--"],
    { cwd: repo, encoding: "utf8" }
  );
  if (diff.error || diff.status !== 0) {
    throw new GateInputError(`could not compare Git base: ${base}`);
  }
  const changed = new Set([
    ...diff.stdout.split("\0").filter(Boolean),
    ...dirtyPaths,
  ]);
  const touch = touchEntries(task, contract);
  // The disposable guard manifest is the one artifact the gate contract itself
  // permits a gate to write, and the selected change's own authoring artifacts
  // are the working state the gate is completing against, so neither is
  // attributed as outside Touch. Other changes' directories, the archive tree,
  // and the specs/schemas trees stay attributable.
  const authoringPrefix = change ? `openspec/changes/${change}/` : null;
  const owners = completedSiblingOwners(tasks, task);
  const warnings = [];
  const outside = [];
  const candidates = [...changed]
    .filter((item) => item !== "keel/guard.json")
    .filter((item) => !(authoringPrefix && item.startsWith(authoringPrefix)))
    .filter((item) => !pathAllowed(item, touch))
    .sort();
  for (const item of candidates) {
    const owner = owners.find((entry) => pathAllowed(item, entry.touch));
    if (owner) {
      // Reported, not silent: the comparison could not establish authorship,
      // and resolving that in the selected task's favour is a judgment the
      // author should see rather than a fact the gate discovered.
      warnings.push(
        `${item} is not attributed to this task: task ${owner.id} of the same `
          + "change is checked complete and declares it in Touch. A base "
          + "comparison cannot establish which task wrote it."
      );
      continue;
    }
    outside.push(item);
  }
  return {
    problems: outside.map((item) =>
      problem("outside-touch", `Changed path is outside Touch: ${item}`)
    ),
    warnings,
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
    // A `(regression)` check asserts that something already green is still
    // green, so it has no honest red. It is exempt from red-green but not from
    // evidence: the bare-label check above still applies to it.
    const exempt = new Set(
      (contract ? contract.capsule.verification.commands : [])
        .filter((entry) => entry.regression)
        .map((entry) => entry.label)
    );
    for (const label of commands) {
      if (exempt.has(label)) continue;
      for (const phase of ["red", "green"]) {
        if (!isConcrete(evidenceValue(task, `${label}.${phase}`))) {
          problems.push(
            problem(
              "missing-strategy-evidence",
              `${strategy} requires concrete ${label}.${phase} Evidence for `
                + "the same behavior check. Tag the check `(regression)` if it "
                + "asserts that something already green stays green."
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
  } else if (!/^none\.?$/i.test(reviewFields.Findings)) {
    // `Resolved here:` is evaluated on its own terms rather than falling
    // through to the owner forms. Otherwise `Resolved here: https://…` would
    // pass as a tracker owner, which is the one reading this disposition must
    // not have: a link to work someone else will do is not evidence that this
    // task did it.
    const resolved = [...reviewFields.Findings.matchAll(RESOLVED_HERE)];
    if (resolved.length > 0) {
      for (const claim of resolved) {
        const verdict = resolutionEvidenceVerdict(repo, claim[1], commands);
        if (verdict.ok) continue;
        problems.push(
          problem("finding-resolution-evidence", resolutionEvidenceMessage(verdict))
        );
        break;
      }
    } else if (!findingOwnerIsDurable(repo, reviewFields.Findings)) {
      problems.push(
        problem(
          "finding-owner",
          "Review Findings must be `none` or carry a disposition. A finding "
            + "fixed in this task is `Resolved here:` naming an `M<n>` check "
            + "this task declares or a repo-relative path that exists; one "
            + "someone must still do is `Durable owner:` naming "
            + `${DURABLE_OWNER_FORMS}; one deliberately not being done is a `
            + "`Discard reason:`/`Discard rationale:` prefix. Name a path after "
            + "`Durable owner:` so it reads as the owner rather than a file the "
            + "finding mentions."
        )
      );
    }
  }
  return { problems, reviewProblems };
}

function taskComplete(repo, options) {
  const selection = loadSelection(repo, options);
  const task = selection.selected[0];
  // Selection ambiguity short-circuits, because the gate does not know which
  // task the caller meant and evaluating the wrong one is the defect. A named
  // task is not ambiguous: its missing anchor is one problem among however many
  // else it has, so it joins the list rather than hiding the rest.
  if (!options.task) {
    const ambiguous = unstartedInferenceProblem(selection);
    if (ambiguous) {
      return gateResult(
        "task-complete",
        "fail",
        selection.change,
        [task.id],
        [ambiguous],
        [],
        null
      );
    }
  }
  const contract = compileTaskContract(repo, selection.change, task);
  const usableContract = contract.diagnostics.length === 0 ? contract : null;
  const checks = completionChecks(repo, task, usableContract);
  checks.problems.push(...contract.diagnostics);
  const missingAnchor = missingAnchorProblem(selection, task);
  if (missingAnchor) {
    checks.problems.push(missingAnchor);
  } else if (usableContract) {
    // Only when an anchor exists: a missing one is already its own problem, and
    // reporting drift on top of it would name a comparison that never ran.
    const drift = contractDriftProblem(
      recordedAnchor(selection, task),
      usableContract
    );
    if (drift) checks.problems.push(drift);
  }
  const scope = scopeEvidence(
    repo,
    task,
    options.base,
    usableContract,
    selection.change,
    selection.tasks
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

// Follow-up Ownership governs work a change left undone. This is the opposite
// shape: statements left standing by work the change completed. It is asked at
// task-start rather than change-close because the whole value is that the
// affected paths enter Touch before implementation — asking at the close finds
// the same facts after the reauthorization it was meant to prevent.
//
// A location list is refused on purpose. The text that goes stale is the text
// the author was not already holding in mind, so a list of remembered files
// reproduces the failure; a searchable phrase is what turns the declaration
// into a grep. What the phrase says is the agent's judgment, not the gate's.
function invalidationProblems(repo, content, tasks) {
  const heading = content.search(/^## Invalidates\s*$/m);
  if (heading < 0) {
    return [
      problem(
        "invalidation-declaration",
        "tasks.md requires a `## Invalidates` section before its tasks are "
          + "executable: one `- I<n>: \"searchable phrase\" — where it lives. "
          + "Updated by: <task ids>` line per statement this change makes "
          + "stale, using `Durable owner:` or `Discard reason:` instead when "
          + "no task of this change updates it, or `- None.`."
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
      /^\s*-\s+(I\d+)\s*:\s*([\s\S]*?)(?=^\s*-\s+I\d+\s*:|(?![\s\S]))/gm
    ),
  ];
  if (entries.length === 0) {
    return [
      problem(
        "invalidation-declaration",
        "Invalidates must declare each `I<n>` entry — a quoted searchable "
          + "phrase, where it lives, and a closure (`Updated by:`, "
          + "`Durable owner:`, or `Discard reason:`) — or `- None.`."
      ),
    ];
  }
  const problems = [];
  for (const entry of entries) {
    const [, id, body] = entry;
    if (!/"[^"\n]{3,}"/.test(body)) {
      problems.push(
        problem(
          "invalidation-phrase",
          `${id} names where to look but not what to look for. Quote the `
            + "wording a reader would search for, so the entry is a search "
            + "rather than a reminder."
        )
      );
      continue;
    }
    const updated = body.match(/Updated by:\s*([0-9.,\s-]+)/i);
    const declaredOwner = body.match(/Durable owner:\s*(\S[^\n]*)/i);
    const verdict = declaredOwner
      ? durableOwnerVerdict(repo, declaredOwner[1])
      : { ok: false, reason: "absent" };
    const discarded = /Discard(?:ed)? (?:reason|rationale):\s*\S/i.test(body);
    if (!updated && !verdict.ok && !discarded) {
      if (verdict.reason === "missing") {
        problems.push(
          problem(
            "invalidation-owner-missing",
            `${id} names \`${verdict.path}\` as its durable owner, but no such `
              + "file exists in this repository."
          )
        );
      } else if (verdict.reason === "handoff") {
        problems.push(
          problem(
            "invalidation-closure",
            `${id} names keel/HANDOFF.md, which is a pointer override rather `
              + `than a durable owner. Accepted forms: ${DURABLE_OWNER_FORMS}.`
          )
        );
      } else {
        problems.push(
          problem(
            "invalidation-closure",
            `${id} lacks an updating task, a durable owner, or a discard `
              + "rationale. Close it with `Updated by: <task ids>` naming tasks "
              + "of this change, a `Discard reason:`, or a `Durable owner:` "
              + `naming ${DURABLE_OWNER_FORMS}.`
          )
        );
      }
      continue;
    }
    // Deliberately weaker than Expectation Coverage, which requires a checked
    // task: at authoring time the updater has not run yet, so existence is the
    // only honest assertion. Completion is then structural — the named task
    // carries the paths in its Touch and passes its own gate.
    if (updated) {
      const ids = updated[1].match(/\d+(?:\.\d+)+/g) || [];
      for (const taskId of ids) {
        if (!tasks.some((task) => task.id === taskId)) {
          problems.push(
            problem(
              "invalidation-owner",
              `${id} names task ${taskId}, which this change does not define.`
            )
          );
        }
      }
    }
  }
  return problems;
}

function expectationProblems(repo, content, tasks) {
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
          + "path or `https://…` tracker reference, or a `Discard reason:` — "
          + "or `- None.`."
      ),
    ];
  }
  const problems = [];
  for (const entry of entries) {
    const [, id, body] = entry;
    const covered = body.match(/Covered by:\s*([0-9.,\s-]+)/i);
    const declaredOwner = body.match(/Durable owner:\s*(\S[^\n]*)/i);
    const verdict = declaredOwner
      ? durableOwnerVerdict(repo, declaredOwner[1])
      : { ok: false, reason: "absent" };
    const discarded = /Discard(?:ed)? (?:reason|rationale):\s*\S/i.test(body);
    if (!covered && !verdict.ok && !discarded) {
      if (verdict.reason === "missing") {
        problems.push(
          problem(
            "expectation-owner-missing",
            `${id} names \`${verdict.path}\` as its durable owner, but no such `
              + "file exists in this repository."
          )
        );
      } else {
        problems.push(
          problem(
            "expectation-closure",
            `${id} lacks behavior coverage, durable owner, or discard `
              + "rationale. Close it with `Covered by: <task ids>`, a "
              + "`Discard reason:`, or a `Durable owner:` naming "
              + `${DURABLE_OWNER_FORMS}.`
          )
        );
      }
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
    // Completion is not the last moment a live change's contract can move. The
    // window between the final checkbox and the archive was unguarded, at the
    // one gate whose job is closing that window — and the loop already compiled
    // every task's capsule, so the comparison costs nothing here either.
    const anchor = recordedAnchor(selection, task);
    if (!anchor) {
      problems.push(
        problem(
          "missing-contract-anchor",
          `Task ${task.id} is checked complete but its Evidence \`Contract\` `
            + "anchor holds no compiled fingerprint, so the close has nothing "
            + "to compare and cannot verify the contract this task was "
            + "completed under. Return it through `keel gate task-start "
            + "--record` and `keel gate task-complete` before closing."
        )
      );
    } else if (contract.diagnostics.length === 0) {
      const drift = contractDriftProblem(anchor, contract);
      if (drift) {
        problems.push(problem(drift.code, `Task ${task.id}: ${drift.message}`));
      }
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
  problems.push(...expectationProblems(repo, selection.content, selection.tasks));

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

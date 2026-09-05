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
  unfilledToken,
} = require("./task-contract");
const { contentSignature, gitPaths, readManifest, startGuard } = require("./guard");

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
    ...invalidationProblems(repo, selection.content, selection.tasks, selection.change),
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

// A Review entry is the text the author wrote under its label, not its first
// line. `parseTasks()` already gathers the whole Evidence body, so the
// continuation lines arrive here; a line-anchored `(.*)` used to drop them
// before any check saw them. That failed in both directions: a `Findings` whose
// `Durable owner:` sat on the fourth line was refused with the owner present
// and the path existing, and a `Findings` reading `none` above three lines of
// real findings passed, because the check tested the word and never saw them
// (issue #49).
//
// The entry ends at the next entry at the same or shallower indentation.
// Without that bound `Findings` — always the last of the four — would run to
// the end of Evidence and read `- Blocker:` as its own text, trading a
// fail-closed defect for a fail-open one. A deeper-indented `- ` line is a
// continuation, which is what makes a Findings written as a sub-list one entry.
const REVIEW_SIBLING = /^(\s*)-\s*[^\s:][^:\n]*:/;

function reviewValue(task, label) {
  const lines = field(task, "Evidence").split(/\r?\n/);
  const opener = new RegExp(`^(\\s*)-\\s*${label}:\\s*(.*)$`, "i");
  for (let index = 0; index < lines.length; index += 1) {
    const match = lines[index].match(opener);
    if (!match) continue;
    const indent = match[1].length;
    const value = [match[2]];
    for (let cursor = index + 1; cursor < lines.length; cursor += 1) {
      const sibling = lines[cursor].match(REVIEW_SIBLING);
      if (sibling && sibling[1].length <= indent) break;
      value.push(lines[cursor]);
    }
    return value.join("\n").trim();
  }
  return "";
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
//
// What each form is worth is part of the sentence, because a list of accepted
// spellings reads as a list of verified guarantees. A path is checked for
// existence at the moment it is cited and never again; a tracker reference is
// accepted on its shape, because a gate that fetched one would stop being
// local and offline, which is the property its verdict rests on. Leaving that
// unsaid is how an author comes to believe a check ran that did not (#100).
const DURABLE_OWNER_FORMS =
  "an absolute `https://…` tracker reference, or any repo-relative path that "
  + "exists and outlives this change — an archived `openspec/changes/archive/…` "
  + "artifact, `keel/archive/…`, or the repository's own ledger; "
  + "`keel/HANDOFF.md` is a pointer override rather than an owner. A path is "
  + "checked for existence when it is cited and is not re-checked afterwards, "
  + "and a tracker reference is accepted on its shape because a gate runs "
  + "offline and never fetches one";

// Trailing punctuation a declared path can abut in prose. ASCII sentence marks
// and their CJK counterparts both belong here: once the extractor stops
// assuming ASCII, its terminators cannot assume ASCII either. A Chinese
// sentence ends in `。`, which is not whitespace, so a non-whitespace run
// swallows it and the gate looks for a file that cannot exist.
const DECLARED_PATH_TRAILING = /[.,;:!?)\]}"'\u2019\u201d\u3002\uff0c\u3001\uff1b\uff1a\uff01\uff1f\uff09\u3011\u300b\u300d\u300f]+$/;

// A file at the repository root carries no separator, and nine of them sit at
// this repository's root — `AGENTS.md`, `README.md`, `package.json` among them
// — every one a legitimate owner. Requiring a separator refused them with "it
// names neither a check nor a path", for a path whose file exists, and left
// the author only `./AGENTS.md`: a concession to this function rather than a
// path anyone meant (issue #107).
//
// The shape is a trailing extension beginning with a letter. That is what
// keeps a bare word unrecognized — `Durable owner: pending` reported as a
// missing file would send the author to create one — and what keeps a version
// string out, since `5.44.0` would otherwise read as `44` with extension `0`,
// and authors write versions in prose beside an owner.
const ROOT_FILE_NAME = /^[^\s`]+\.[A-Za-z][A-Za-z0-9]{0,7}$/;

// A declared path is a run of non-whitespace. What ends a path is whitespace;
// what a path is *made of* is the filesystem's business, and answering the
// first question with the second is what refused
// `notes/note-006-转岗最难的不是流程/note.md` by reporting that
// `notes/note-006-` does not exist — a path nobody wrote (issue #60). It is the
// same class as #40 on the worktree-reading side, which survived because that
// fix repaired one reader rather than how paths are extracted; this is the one
// extractor every gate reader of a declared path now uses.
//
// The backtick form wins when present. It is the only way to write a path
// containing whitespace, and `touchEntries` already strips backticks from a
// Touch entry, so one authorship stops being spelled two ways depending on
// which reader will read it.
function declaredPath(value) {
  const text = String(value || "");
  const quoted = text.match(/`([^`\n]*\/[^`\n]*)`/);
  if (quoted) return quoted[1].trim() || null;
  const bare = text.match(/[^\s`]+\/[^\s`]+/);
  if (bare) return bare[0].replace(DECLARED_PATH_TRAILING, "") || null;
  // The separator form is tried first and is unchanged, so nothing that
  // resolves today resolves differently. The trim runs before the shape is
  // judged, so a root file ending a sentence is still a root file.
  for (const token of text.split(/\s+/)) {
    const trimmed = token.replace(DECLARED_PATH_TRAILING, "");
    if (trimmed && ROOT_FILE_NAME.test(trimmed)) return trimmed;
  }
  return null;
}

// A path inside the selected change's own directory exists now and cannot
// exist later: archiving moves `openspec/changes/<name>/` under
// `openspec/changes/archive/`, so the one guarantee the gate offers expires in
// the next step of the workflow that accepted it. Measured in this repository,
// 10 declarations name such a path and all 10 are dead; the field report
// measured 35 of 36 (issue #100). Existence is necessary and not sufficient —
// the same line `keel/HANDOFF.md` already sits on.
//
// The rule is the directory, not the file: every file under it moves together,
// and naming `design.md` would refuse one spelling of one instance. And it is
// *this* change's directory, not change directories in general — the protocol
// names a new OpenSpec change as a legitimate owner of deferred work, and no
// measured pointer has that shape.
function insideOwnChangeDirectory(candidate, change) {
  if (!change || !candidate) return false;
  const prefix = `openspec/changes/${change}/`;
  return String(candidate).replace(/^\.\//, "").startsWith(prefix);
}

// Classify a declared `Durable owner:` value. A gate runs without network, so a
// URL is accepted on shape alone; a path is the one form it can actually check,
// and checking it is stricter than the prefix whitelist this replaced — for as
// long as the path outlives the change, which `insideOwnChangeDirectory` is
// there to decide.
function durableOwnerVerdict(repo, value, change) {
  const owner = String(value || "").trim();
  if (!owner) return { ok: false, reason: "unrecognized" };
  if (/keel\/HANDOFF\.md/i.test(owner)) return { ok: false, reason: "handoff" };
  if (TRACKER_REFERENCE.test(owner)) return { ok: true };
  const candidate = declaredPath(owner);
  if (!candidate) return { ok: false, reason: "unrecognized" };
  if (insideOwnChangeDirectory(candidate, change)) {
    return { ok: false, reason: "transient", path: candidate };
  }
  if (fs.existsSync(path.join(repo, candidate))) return { ok: true };
  return { ok: false, reason: "missing", path: candidate };
}

// The one sentence every transient refusal makes, so the three consumers say
// it the same way. It names the cause (the directory moves) rather than the
// symptom, because the author cannot repair a spelling problem they do not
// have.
function transientOwnerMessage(candidate) {
  return `\`${candidate}\` is inside this change's own directory, which moves `
    + "to `openspec/changes/archive/` when the change is archived — the file "
    + "exists now and the pointer is guaranteed to break. Name something that "
    + `outlives the change: ${DURABLE_OWNER_FORMS}.`;
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
// Findings is free prose that normally holds several findings with different
// dispositions, so a capture reaching to the newline swallows every marker
// after it — a block recording one fix and one tracker-owned follow-up was
// refused because the *follow-up's* URL was read as the *fix's* evidence.
// Measured on this change's own task 1.3. That block used to be one line and
// may now wrap across several, which widens what a greedy capture would
// swallow and changes nothing about why this one is narrow. The match is
// global because each resolved claim owes its own evidence; checking only the
// first would let a second one assert itself for free.
const RESOLVED_HERE = /\bresolved here\s*:[ \t]*(\S*)/gi;

// Resolution evidence is deliberately narrower than a durable owner. An
// `http`/`https` reference says someone else will do the work later, which is
// exactly the durable-owner state; what proves a fix is the check that covers
// it or the artifact that shows it. A bare marker is refused because a
// disposition that asserts its own conclusion would be a way out of the other
// two, and the third state would decay into the easiest exit.
function resolutionEvidenceVerdict(repo, value, commands, change) {
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
  const candidate = declaredPath(evidence);
  if (!candidate) return { ok: false, reason: "unrecognized" };
  // Resolution evidence is a file like any other and moves with the directory
  // holding it, so it earns the same verdict rather than a second answer to
  // the same question.
  if (insideOwnChangeDirectory(candidate, change)) {
    return { ok: false, reason: "transient", path: candidate };
  }
  if (fs.existsSync(path.join(repo, candidate))) return { ok: true };
  return { ok: false, reason: "missing", path: candidate };
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
  if (verdict.reason === "transient") {
    return `${lead}${transientOwnerMessage(verdict.path)}${tail}`;
  }
  if (verdict.reason === "missing") {
    return `${lead}\`${verdict.path}\` does not exist.${tail}`;
  }
  return `${lead}it names neither a check nor a path.${tail}`;
}

function findingOwnerIsDurable(repo, findings, change) {
  if (/keel\/HANDOFF\.md/i.test(findings)) return false;
  if (/\b(?:explicit\s+)?discard (?:reason|rationale)\s*:/i.test(findings)) {
    return true;
  }
  if (TRACKER_REFERENCE.test(findings)) return true;
  // A path counts here only when it is named as the owner. Findings is free
  // prose, and a finding that merely mentions the source file it concerns has
  // not thereby given that finding an owner.
  const declared = findings.match(/Durable owner:\s*(\S[^\n]*)/i);
  if (declared) return durableOwnerVerdict(repo, declared[1], change).ok;
  const artifact = findings.match(
    /\b(openspec\/changes\/[A-Za-z0-9][A-Za-z0-9._-]*\/(?:proposal|design|tasks)\.md)(?:#\d+(?:\.\d+)*)?/i
  );
  if (
    artifact
    && !insideOwnChangeDirectory(artifact[1], change)
    && fs.existsSync(path.join(repo, artifact[1]))
  ) {
    return true;
  }
  // Same extractor, scoped to the archive prefix: the segment after
  // `keel/archive/` is a path like any other and was equally ASCII-bound.
  const archive = findings.match(/keel\/archive\/[^\s`]*/i);
  if (!archive) return false;
  const archivePath = declaredPath(archive[0]);
  return Boolean(archivePath) && fs.existsSync(path.join(repo, archivePath));
}

// Read in `-z` form, because every other form escapes. Git octal-escapes any
// path holding a non-ASCII byte and quotes it; `core.quotepath=false` removes
// the octal and still quotes a space, a quote, or a backslash; and `status`
// and `diff` do not agree on which cases they quote. `-z` emits raw bytes in
// all of them, which deletes the decoding problem rather than adding a
// decoder — and it is a flag rather than a repository setting, so the answer
// does not depend on how the repository happens to be configured.
//
// `gitPaths` moved to guard.js, which owns the worktree reading now that the
// task-start record and this comparison must use the same one.

// The dirty set recorded when this task was authorized, or null when nobody
// recorded one. Null and empty are different answers: an empty list says
// nothing was dirty at task start, and null says no record exists, which is
// what a manifest written before this field, a cleared guard, or a
// `--no-guard` start all produce. Reading null as empty would attribute the
// whole worktree to the task and fail every completion in a dirty repository.
// Each entry is `{ path, sha256 }`, the content signature `contentSignature`
// read at that same moment — the record of *what* was dirty, not only that a
// path was.
function recordedBaseline(repo, change, task) {
  const loaded = readManifest(repo);
  if (loaded.state !== "ok") return null;
  const manifest = loaded.manifest;
  if (manifest.change !== change || manifest.task !== task) return null;
  return Array.isArray(manifest.startedDirty) ? manifest.startedDirty : null;
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
  // An explicit base wins. It asks a broader question than the record does —
  // everything since that commit, not only since this task started — and
  // substituting the narrower answer would make `--base` mean something other
  // than what it says.
  const baseline = base ? null : recordedBaseline(repo, change, task.id);
  if (!base && !baseline) {
    // No base and no record: the original conservatism, and the reason for it
    // is unchanged. Git alone cannot say which task of a half-finished change
    // wrote a given path, so the dirty state stays semantic review evidence.
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

  if (!base) {
    // Dirty now and not dirty when the task started, or dirty now with
    // content that no longer matches what was there at task start. Either
    // answers "did this task write it", which is the question the boundary
    // actually asks; it does not answer "which task wrote it", which is why
    // the completed-sibling exclusion below still applies and still reports
    // itself.
    //
    // A path already dirty at task start is exempt only while its content
    // stays the one recorded then — recording a hash instead of only a name
    // is what lets that hold without falling back to subtracting the whole
    // path, which exempted every later write to it, not just the one that
    // predated the task (#72).
    const unchangedSinceStart = new Set(
      baseline
        .filter((entry) => contentSignature(repo, entry.path) === entry.sha256)
        .map((entry) => entry.path)
    );
    return attributeChanged(
      repo,
      task,
      dirtyPaths.filter((item) => !unchangedSinceStart.has(item)),
      contract,
      change,
      tasks
    );
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
  return attributeChanged(
    repo,
    task,
    [...diff.stdout.split("\0").filter(Boolean), ...dirtyPaths],
    contract,
    change,
    tasks
  );
}

// The one place a candidate path becomes a problem, whichever comparison
// produced it. Both callers reach it: the recorded-baseline path and the
// explicit-base path differ only in how they decide which paths are
// candidates, and a second copy of this would be a second definition of what
// Touch means.
function attributeChanged(repo, task, changedList, contract, change, tasks) {
  const changed = new Set(changedList);
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

function completionChecks(repo, task, contract = null, changeVerify = null, change = null) {
  const problems = [];
  const commands = contract
    ? contract.capsule.verification.commands.map((item) => item.label)
    : commandLabels(task);
  // With no contract, the labels came from the expanded v3 `Commands` field,
  // which a compact task never declares — so their absence is a fact about the
  // fallback, not about the task. The compiler's own diagnostics are already in
  // `problems` (the caller pushes them unconditionally, and an unusable
  // contract has at least one), so this cannot turn a refusal into a pass. The
  // per-label evidence checks below stay: a genuine v3 task yields real labels.
  if (contract && commands.length === 0) {
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
  // A `(regression)` check's bare Evidence may defer to a change-level `C<n>`
  // check instead of recording its own result (issue #95). The regression
  // flag comes from the compiled contract, the same source the exemption
  // above already trusts, so this cannot disagree with what `(regression)`
  // itself decided. Resolution only — whether the reference is declared, not
  // whether it has run yet — because at task-complete time it legitimately
  // may not have; `changeVerifyProblems` requires it answered by close.
  if (contract) {
    const declaredLabels = new Set(
      (changeVerify ? changeVerify.checks : []).map((entry) => entry.label)
    );
    for (const entry of contract.capsule.verification.commands) {
      const deferred = deferredChangeCheck(evidenceValue(task, entry.label));
      if (!deferred) continue;
      if (!entry.regression) {
        problems.push(
          problem(
            "deferred-evidence-not-regression",
            `${entry.label} Evidence defers to ${deferred}, but ${entry.label} `
              + "is not tagged `(regression)`; only a `(regression)`-tagged "
              + "check may defer to a change-level check."
          )
        );
        continue;
      }
      if (!declaredLabels.has(deferred)) {
        problems.push(
          problem(
            "deferred-check-unresolved",
            `${entry.label} defers to ${deferred}, but tasks.md's \`## `
              + `Change Verify\` does not declare it. Declare it there, or `
              + `record concrete Evidence for ${entry.label} directly.`
          )
        );
      }
    }
  }
  const blocker = evidenceValue(task, "Blocker");
  if (isConcrete(blocker)) {
    problems.push(problem("blocker", `Task records a blocker: ${blocker}`));
  }

  // Reauthorizations (#70) is a log, not a stop condition: absent, `none`, and
  // concrete text all pass. Only an abandoned `<slot>` token — real content
  // the author started and never finished — is refused, the same distinction
  // `unfilledToken()` already draws for every other field that uses it.
  const reauthorizationsToken = unfilledToken(reviewValue(task, "Reauthorizations"));
  if (reauthorizationsToken) {
    problems.push(
      problem(
        "reauthorizations-shape",
        `Reauthorizations carries the unfilled slot \`${reauthorizationsToken}\`, `
          + "so it is not concrete. Replace that slot with the value it stands "
          + "for, or fence it in inline code when it is literal text rather "
          + "than a slot left to fill."
      )
    );
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
        const verdict = resolutionEvidenceVerdict(repo, claim[1], commands, change);
        if (verdict.ok) continue;
        problems.push(
          problem("finding-resolution-evidence", resolutionEvidenceMessage(verdict))
        );
        break;
      }
    } else if (!findingOwnerIsDurable(repo, reviewFields.Findings, change)) {
      problems.push(
        problem(
          "finding-owner",
          "Review Findings must be `none` or carry a disposition — name a "
            + "path after `Durable owner:` so it reads as the owner rather "
            + "than a file the finding mentions. A finding fixed in this "
            + "task is `Resolved here:` naming an `M<n>` check this task "
            + "declares or a repo-relative path that exists; one someone "
            + "must still do is `Durable owner:` naming "
            + `${DURABLE_OWNER_FORMS}; one deliberately not being done is a `
            + "`Discard reason:`/`Discard rationale:` prefix."
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
  const changeVerify = changeVerifyChecks(selection.content, selection.tasks);
  const checks = completionChecks(
    repo,
    task,
    usableContract,
    changeVerify,
    selection.change
  );
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

// The body of a change-level section — `## Invalidates`, `## Expectation
// Coverage` — ending at the next `##` heading or at the next task, whichever
// comes first. The heading half alone is the right bound for a document made of
// headings, and a tasks file is not one: its dominant structure is a list, so a
// section that is not the file's last one ran over the whole task list and read
// what the tasks had declared. An `E<n>` line under a task's `Covers` was
// judged as a coverage entry and reported unclosed; a `repo-action` task's
// `Touch` of a bare `- none` was read as the section's `- None.` and closed a
// declaration that closed nothing. The first failed loudly and named an entry
// that was fine, the second failed silently, and which one an author met
// depended only on where they had put the section — a position no template,
// diagnostic, or document has ever stated.
//
// The task half is the task list already parsed for this file rather than a
// second checkbox pattern, so it cannot drift from the boundary `parseTasks()`
// applies to a task's own body. The heading half stays as it was: the two
// spellings are not interchangeable, and unifying them truncates a tail-position
// section at an indented `##` line inside its own body, which is this same
// defect pointed the other way.
function sectionBody(content, headingOffset, tasks) {
  const lines = content.split(/\r?\n/);
  const headingLine = content.slice(0, headingOffset).split(/\r?\n/).length - 1;
  let end = lines.length;
  for (const task of tasks) {
    if (task.line > headingLine && task.line < end) end = task.line;
  }
  for (let cursor = headingLine + 1; cursor < end; cursor += 1) {
    if (/^##\s+/.test(lines[cursor])) {
      end = cursor;
      break;
    }
  }
  return lines.slice(headingLine + 1, end).join("\n");
}

// A `(regression)` check's bare Evidence may point at a change-level check
// instead of recording its own result — issue #95. `deferred to C<n>` is
// matched at the front of the value, the same way `Resolved here:`/`Durable
// owner:` prefixes are read elsewhere in this file, so a real result that
// happens to mention "deferred" mid-sentence is not misread as one.
function deferredChangeCheck(value) {
  const match = String(value || "").trim().match(/^deferred to (C[1-9]\d*)\b/i);
  return match ? match[1] : null;
}

// `## Change Verify` is a change-level section a `(regression)` check's
// Evidence can defer to — a check that only needs to run once for the whole
// change instead of once per task. Parsed the same way as `## Invalidates`/
// `## Expectation Coverage`: located by heading, bounded by `sectionBody()`.
// Absent by default; a change that no task defers in never needs it.
function changeVerifyChecks(content, tasks) {
  const heading = content.search(/^## Change Verify\s*$/m);
  if (heading < 0) return null;
  const section = sectionBody(content, heading, tasks);
  const strategyEntry = section.match(/^\s*-\s*Strategy:\s*(.*)$/im);
  const checks = [
    ...section.matchAll(/^\s*-\s*(C[1-9]\d*):\s*(.*)$/gim),
  ].map((match) => ({ label: match[1], check: match[2].trim() }));
  return {
    strategy: strategyEntry ? strategyEntry[1].trim() : "",
    checks,
  };
}

// The `## Change Evidence` counterpart to `changeVerifyChecks` — one `C<n>:`
// result per declared check, read the same way a task's own `M<n>` Evidence
// already is.
function changeEvidenceValue(content, tasks, label) {
  const heading = content.search(/^## Change Evidence\s*$/m);
  if (heading < 0) return "";
  const section = sectionBody(content, heading, tasks);
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = section.match(new RegExp(`^\\s*-\\s*${escaped}:\\s*(.*)$`, "im"));
  return match ? match[1].trim() : "";
}

// `change-close`-only: `## Change Verify`'s own shape, and completeness of
// `## Change Evidence` for every check it declares — whether or not any task
// actually defers to it, because a declared check still owes its own result.
// Per-task resolution (does a deferred reference resolve at all) runs inside
// `completionChecks`, shared by `task-complete` and this loop's own call to
// it, so it is not repeated here.
function changeVerifyProblems(content, tasks) {
  const changeVerify = changeVerifyChecks(content, tasks);
  if (!changeVerify) return [];
  const problems = [];
  const labels = changeVerify.checks.map((entry) => entry.label);
  const expected = labels.map((_, index) => `C${index + 1}`);
  if (labels.length === 0 || !isConcrete(changeVerify.strategy)) {
    problems.push(
      problem(
        "change-verify-shape",
        "`## Change Verify` requires a concrete `Strategy:` line and at "
          + "least one `C<n>:` check."
      )
    );
  } else if (labels.some((label, index) => label !== expected[index])) {
    problems.push(
      problem(
        "change-verify-shape",
        "`## Change Verify` labels must be contiguous and ordered: "
          + `expected ${expected.join(", ")}; found ${labels.join(", ")}.`
      )
    );
  }
  for (const entry of changeVerify.checks) {
    if (!isConcrete(entry.check)) {
      problems.push(
        problem("change-verify-shape", `${entry.label} must define a concrete check.`)
      );
    }
  }
  for (const entry of changeVerify.checks) {
    if (!isConcrete(changeEvidenceValue(content, tasks, entry.label))) {
      problems.push(
        problem(
          "change-evidence-missing",
          `Missing concrete \`## Change Evidence\` for ${entry.label}.`
        )
      );
    }
  }
  return problems;
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
function invalidationProblems(repo, content, tasks, change) {
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
  const section = sectionBody(content, heading, tasks);
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
    // The quotation is read across the entry, not one line of it. An entry
    // carries a quotation, a location, and a closure, and wraps as often as it
    // needs to — 42 of this repository's 194 archived entries span more than
    // one line. Requiring the quotation to fit on one refused entries that had
    // named exactly what was asked for, and offered no repair but reflowing
    // the text (issue #108). The bound is the entry: `entries` above splits on
    // the next `I<n>`, so a quotation cannot reach past its own. `Findings` in
    // this same file is already read as wrapping.
    if (!/"[^"]{3,}"/.test(body)) {
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
      ? durableOwnerVerdict(repo, declaredOwner[1], change)
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
      } else if (verdict.reason === "transient") {
        problems.push(
          problem(
            "invalidation-owner-transient",
            `${id} names ${transientOwnerMessage(verdict.path)}`
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

function expectationProblems(repo, content, tasks, change) {
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
  const section = sectionBody(content, heading, tasks);
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
      ? durableOwnerVerdict(repo, declaredOwner[1], change)
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
      } else if (verdict.reason === "transient") {
        problems.push(
          problem(
            "expectation-owner-transient",
            `${id} names ${transientOwnerMessage(verdict.path)}`
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
  const changeVerify = changeVerifyChecks(selection.content, selection.tasks);
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
      contract.diagnostics.length === 0 ? contract : null,
      changeVerify,
      selection.change
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
  problems.push(
    ...expectationProblems(repo, selection.content, selection.tasks, selection.change)
  );
  problems.push(...changeVerifyProblems(selection.content, selection.tasks));

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

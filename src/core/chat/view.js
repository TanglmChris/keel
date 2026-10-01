"use strict";

// How chat records read to a person or an agent (issue #187, design D8, D20).
// Stored times carry the writer's UTC offset; every display converts to the
// viewer's local time and never prints the raw stamp. Edits and retractions
// are records of their own: a view applies them to the message they target
// and leaves the original file untouched.

function pad(value) {
  return String(value).padStart(2, "0");
}

function parseTime(created) {
  const time = Date.parse(created);
  return Number.isNaN(time) ? null : new Date(time);
}

// `YYYY-MM-DD HH:MM` in the viewer's local time zone.
function localStamp(created) {
  const date = parseTime(created);
  if (!date) return "????-??-?? ??:??";
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} `
    + `${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function localDay(created) {
  return localStamp(created).slice(0, 10);
}

function localClock(created) {
  return localStamp(created).slice(11);
}

// `3h ago`, for agent notices, where the absolute time costs a reader a
// conversion it does not need.
function relativeAge(created, now = Date.now()) {
  const date = parseTime(created);
  if (!date) return "at an unknown time";
  const seconds = Math.max(0, Math.round((now - date.getTime()) / 1000));
  if (seconds < 60) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

// The records a reader sees: edits and retractions applied to their targets
// and dropped as lines of their own; a todo knows whether it was closed.
function displayRecords(records) {
  const byId = new Map();
  const shown = [];
  for (const record of records) {
    if (record.kind === "edit" || record.kind === "retract") {
      const target = byId.get(record.target);
      if (!target || target.from !== record.from) continue;
      if (record.kind === "edit") {
        target.text = record.text;
        target.edited = true;
      } else {
        target.retracted = true;
      }
      continue;
    }
    const copy = { ...record };
    if (copy.kind === "done") {
      const todo = byId.get(copy.target);
      if (todo) todo.done = true;
    }
    byId.set(copy.id, copy);
    shown.push(copy);
  }
  return shown;
}

function markers(record) {
  const parts = [];
  if (record.kind === "todo") {
    parts.push(`[todo → ${record.assignee || "?"}${record.issue ? ` ${record.issue}` : ""}${record.done ? ", done" : ""}]`);
  }
  if (record.reply_to) parts.push(`↳ ${record.reply_to}`);
  if (record.mentions && record.mentions.length) parts.push(record.mentions.map((m) => `@${m}`).join(" "));
  if (record.edited) parts.push("(edited)");
  return parts.length ? ` ${parts.join(" ")}` : "";
}

function describe(record) {
  switch (record.kind) {
    case "join":
      return `${record.from} added ${record.target}`;
    case "leave":
      return `${record.from} removed ${record.target}`;
    case "archive":
      return `${record.from} archived the group`;
    case "done":
      return `${record.from} closed todo ${record.target}`;
    default:
      if (record.retracted) return `${record.from}: (retracted)`;
      return `${record.from}:${markers(record)} ${record.text}`;
  }
}

function formatLine(record, { clock = false } = {}) {
  const when = clock ? localClock(record.created) : localStamp(record.created);
  return `${when} ${describe(record)}  [${record.id}]`;
}

module.exports = {
  describe,
  displayRecords,
  formatLine,
  localClock,
  localDay,
  localStamp,
  relativeAge,
};

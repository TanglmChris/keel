"use strict";

// Secrets never leave the machine through the Slack bridge (issue #187,
// design D15). A message an agent writes can quote a log, an environment, or
// a config file; before any text is sent to Slack, these shapes are replaced
// with `[redacted]`. The local record keeps the original: it never left.
//
// This is a net for accidents, not a guarantee. It recognizes common token
// formats and `name = value` assignments of obviously secret names, and it
// cannot recognize a secret with no shape.

const REDACTED = "[redacted]";

const PATTERNS = [
  /-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z0-9 ]*PRIVATE KEY-----/g,
  /\bxox[abeoprs]-[A-Za-z0-9-]{6,}/g,
  /\bxapp-[A-Za-z0-9-]{6,}/g,
  /\bgithub_pat_[A-Za-z0-9_]{20,}/g,
  /\bgh[opsur]_[A-Za-z0-9]{16,}/g,
  /\bsk-[A-Za-z0-9_-]{16,}/g,
  /\b(?:AKIA|ASIA)[0-9A-Z]{16}\b/g,
];

const ASSIGNMENT = /\b(password|passwd|pwd|token|secret|api[_-]?key|access[_-]?key|private[_-]?key)(\s*[:=]\s*)("[^"]*"|'[^']*'|[^\s,;]+)/gi;

function redact(text) {
  let result = String(text || "");
  for (const pattern of PATTERNS) result = result.replace(pattern, REDACTED);
  return result.replace(ASSIGNMENT, (match, name, separator, value) => (
    value === REDACTED ? match : `${name}${separator}${REDACTED}`
  ));
}

module.exports = {
  REDACTED,
  redact,
};

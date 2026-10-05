"use strict";

// Formatting between the store's Markdown and Slack's mrkdwn (issue #187,
// chat-slack-format D2, D3). Sessions write Markdown; Slack renders its own
// dialect, so the bridge translates on the way out and back on the way in.
// Code spans and fenced blocks are escaped but otherwise left alone in both
// directions. The round trip keeps meaning, not the exact markers: a heading
// comes back as a bold line and a bullet as a `•` line.

const FENCE = /```[\s\S]*?```/g;
const SPAN = /`[^`\n]*`/g;
// A placeholder for a bold marker, so a later italic pass cannot read it.
const BOLD = "\u0001";
// Slack renders `*x*` only between word boundaries, and CJK text or
// full-width punctuation right beside a marker is not one: a zero-width space
// on each side of every marker pair supplies the boundary, checked against
// real Slack on 2026-10-05 (#187). Inbound text drops them again.
const ZWSP = "\u200b";
// An issue reference at a word boundary, `owner/repo#N` or a bare `#N`, and
// any Slack link already made, which is matched first so that a reference
// inside one is left alone (chat-issue-links D3).
const ISSUE = /(<[^>\n]*>)|(?<![\w#/;&.-])((?:([\w.-]+\/[\w.-]+))?#(\d{1,7}))(?![\w#])/g;
const ISSUE_LINK = /<https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/(?:issues|pull)\/\d+\|((?:[\w.-]+\/[\w.-]+)?#\d+)>/g;

// Calls `prose` on the text outside code and `code` on the code itself.
function byCode(text, prose, code) {
  const outside = (part) => {
    let result = "";
    let last = 0;
    for (const match of part.matchAll(SPAN)) {
      result += prose(part.slice(last, match.index)) + code(match[0]);
      last = match.index + match[0].length;
    }
    return result + prose(part.slice(last));
  };
  let result = "";
  let last = 0;
  for (const match of text.matchAll(FENCE)) {
    result += outside(text.slice(last, match.index)) + code(match[0]);
    last = match.index + match[0].length;
  }
  return result + outside(text.slice(last));
}

function escape(text) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function unescape(text) {
  return text.replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
}

// `owner/repo#N` links to that repository; a bare `#N` to `repo`, the
// project's own GitHub repository, and stays text without one (D1, D2).
function linkIssues(text, repo) {
  return text.replace(ISSUE, (match, link, ref, named, number) => {
    if (link) return link;
    const target = named || repo;
    if (!target) return match;
    return `<https://github.com/${target}/issues/${number}|${ref}>`;
  });
}

function proseToSlack(text, repo) {
  return linkIssues(escape(text)
    .replace(/\[([^\]\n]+)\]\((https?:\/\/[^)\s]+|mailto:[^)\s]+)\)/g, (match, label, url) => `<${url}|${label}>`), repo)
    .replace(/^(\s*)[-*+][ \t]+/gm, "$1• ")
    .replace(/^#{1,6}[ \t]+(.+?)[ \t]*#*[ \t]*$/gm, `${BOLD}$1${BOLD}`)
    .replace(/\*\*(?!\s)([^\n]+?)\*\*/g, `${BOLD}$1${BOLD}`)
    .replace(/__(?!\s)([^\n]+?)__/g, `${BOLD}$1${BOLD}`)
    .replace(/(^|[^\w*])\*(?![\s*])([^*\n]+?)\*(?![\w*])/g, `$1${ZWSP}_$2_${ZWSP}`)
    .replace(/~~(?!\s)([^\n]+?)~~/g, `${ZWSP}~$1~${ZWSP}`)
    .replace(new RegExp(`${BOLD}([^${BOLD}]+)${BOLD}`, "g"), `${ZWSP}*$1*${ZWSP}`);
}

function proseFromSlack(text) {
  return unescape(text.split(ZWSP).join("")
    .replace(ISSUE_LINK, "$1")
    .replace(/<((?:https?:\/\/|mailto:)[^|>\s]+)\|([^>]+)>/g, "[$2]($1)")
    .replace(/<((?:https?:\/\/|mailto:)[^|>\s]+)>/g, "$1")
    .replace(/(^|[^\w*])\*(?![\s*])([^*\n]+?)\*(?![\w*])/g, `$1${BOLD}${BOLD}$2${BOLD}${BOLD}`)
    .replace(/(^|[^\w_])_(?![\s_])([^_\n]+?)_(?![\w_])/g, "$1*$2*")
    .replace(/(^|[^\w~])~(?![\s~])([^~\n]+?)~(?![\w~])/g, "$1~~$2~~")
    .split(BOLD).join("*"));
}

function toSlack(text, { repo = null } = {}) {
  return byCode(String(text || ""), (prose) => proseToSlack(prose, repo), escape);
}

function fromSlack(text) {
  return byCode(String(text || ""), proseFromSlack, unescape);
}

module.exports = { fromSlack, toSlack };

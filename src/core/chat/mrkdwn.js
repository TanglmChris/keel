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

function proseToSlack(text) {
  return escape(text)
    .replace(/\[([^\]\n]+)\]\((https?:\/\/[^)\s]+|mailto:[^)\s]+)\)/g, (match, label, url) => `<${url}|${label}>`)
    .replace(/^(\s*)[-*+][ \t]+/gm, "$1• ")
    .replace(/^#{1,6}[ \t]+(.+?)[ \t]*#*[ \t]*$/gm, `${BOLD}$1${BOLD}`)
    .replace(/\*\*(?!\s)([^\n]+?)\*\*/g, `${BOLD}$1${BOLD}`)
    .replace(/__(?!\s)([^\n]+?)__/g, `${BOLD}$1${BOLD}`)
    .replace(/(^|[^\w*])\*(?![\s*])([^*\n]+?)\*(?![\w*])/g, "$1_$2_")
    .replace(/~~(?!\s)([^\n]+?)~~/g, "~$1~")
    .split(BOLD).join("*");
}

function proseFromSlack(text) {
  return unescape(text
    .replace(/<((?:https?:\/\/|mailto:)[^|>\s]+)\|([^>]+)>/g, "[$2]($1)")
    .replace(/<((?:https?:\/\/|mailto:)[^|>\s]+)>/g, "$1")
    .replace(/(^|[^\w*])\*(?![\s*])([^*\n]+?)\*(?![\w*])/g, `$1${BOLD}${BOLD}$2${BOLD}${BOLD}`)
    .replace(/(^|[^\w_])_(?![\s_])([^_\n]+?)_(?![\w_])/g, "$1*$2*")
    .replace(/(^|[^\w~])~(?![\s~])([^~\n]+?)~(?![\w~])/g, "$1~~$2~~")
    .split(BOLD).join("*"));
}

function toSlack(text) {
  return byCode(String(text || ""), proseToSlack, escape);
}

function fromSlack(text) {
  return byCode(String(text || ""), proseFromSlack, unescape);
}

module.exports = { fromSlack, toSlack };

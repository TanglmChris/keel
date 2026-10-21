# keel-md-docx v1 — skill evidence

Date: 2026-10-21
Owner task: openspec/changes/md-docx-export/tasks.md#1.1
Source issue: https://github.com/TanglmChris/keel/issues/405

## Provenance

The converter files ship unchanged from the prototype attached to #405, written with AI assistance for the requesting user and published in the issue body with SHA-256 sums. On 2026-10-21 each file was extracted from the issue body and its digest matched the stated one: `md2word.py` `73331af5…`, `runtime.mjs` `7fa52c33…`, `fonts-macos.conf`, `requirements.txt`, and `package.json`. The prototype's shell launcher, which probed a Codex runtime cache under `~/.cache/codex-runtimes`, its unittest file, demo, and README are not shipped; `keel docx convert` supplies what the launcher supplied. The issue states no company code and no user document is included.

## Licences and sizes

Read from the PyPI and npm registries on 2026-10-21; nothing was installed. Sizes are macOS arm64 downloads (Python wheels for CPython 3.11) or npm unpacked sizes.

- python-docx 1.2.0 — MIT — 0.25 MB wheel (`python_docx-1.2.0-py3-none-any.whl`).
- lxml 6.0.2 — BSD-3-Clause — 8.6 MB wheel (`lxml-6.0.2-cp311-cp311-macosx_10_9_universal2.whl`).
- Pillow 12.0.0, the newest below the prototype's `<13` bound — MIT-CMU — 4.65 MB wheel (`pillow-12.0.0-cp311-cp311-macosx_11_0_arm64.whl`).
- marked 17.0.5 — MIT — 0.44 MB unpacked.
- sharp 0.35.5 — Apache-2.0 — 0.96 MB unpacked, plus `@img/sharp-darwin-arm64` 0.35.5 (Apache-2.0, 0.29 MB) and `@img/sharp-libvips-darwin-arm64` 1.3.4 (LGPL-3.0-or-later, 18.2 MB), which npm fetches as optional platform dependencies.

None of these is bundled with Keel. They are installed only by `keel docx setup --yes`, into `~/.keel/docx/`.

## Trigger evaluation

Evaluation integrity: a fresh read-only subagent received only the eleven skill descriptions a Keel-managed Claude session lists (the six `keel-*` skills and five `openspec-*` workflows) and each raw prompt, used no tools, and did not receive intended answers. It was asked which one skill it would load first, or none.

## Positive case P1 — Chinese request, keep SVG diagrams

Raw prompt: 把 docs/architecture.md 导出成 Word 给客户，里面的 SVG 框图要保留。
Triggered: keel-md-docx.
Verdict: pass.

## Positive case P2 — English request naming inline SVG and a table

Raw prompt: Convert notes/flow.md to a .docx — it has a couple of inline <svg> diagrams and a table.
Triggered: keel-md-docx.
Verdict: pass.

## Positive case P3 — informal Chinese request for a docx version

Raw prompt: 这份 markdown 有几张 svg 图，帮我出一个 docx 版本发给领导。
Triggered: keel-md-docx.
Verdict: pass.

## Negative control N1 — another output format

Raw prompt: 把 report.md 转成 PDF。
Triggered: none; the evaluator noted the description excludes other formats.
Verdict: pass.

## Negative control N2 — editing an SVG, no export

Raw prompt: diagram.svg 里那个箭头画歪了，帮我修一下。
Triggered: none.
Verdict: pass.

## Negative control N3 — editing an existing Word file

Raw prompt: Open budget.docx and fix the typos in section 2.
Triggered: none; the description excludes editing an existing Word file.
Verdict: pass.

## Negative control N4 — Markdown to HTML

Raw prompt: Render this Markdown table as HTML for the wiki.
Triggered: none.
Verdict: pass.

## Mixed case M1 — authoring first, export later

Raw prompt: 帮我写一份新功能的提案，然后把设计文档导出成 Word。
Triggered: keel-align-expectations first, with keel-md-docx named for the later export step.
Verdict: pass; the export skill did not displace the authoring workflow.

## Real-task evidence

Not run in Keel. The owner decided on 2026-10-21 (#405 comment 6311576442) that no dependency is installed for this change. The setup plan, the consent flow, the refusals, and the hand-off to the converter are tested with stand-in installers (`docx-setup-asks-first`, `docx-convert-refuses-first`). The prototype's own evidence, outside Keel: six integration checks passed on macOS arm64 with Python 3.12, marked 17.0.5, and sharp 0.35.5 on 2026-10-20, and a two-page Chinese example was rendered with LibreOffice and inspected by eye.

## Unresolved findings:

- Real conversion of every supported SVG form, each failure case against real SVG, and the page-by-page rendering of a Chinese mixed-text example are unverified in Keel. `docx-converts-markdown-with-svg` runs them against an environment named by `KEEL_DOCX_TEST_ENV` and reports itself skipped without one.
- Linux, Windows, Codex as the host, and Microsoft Word itself are unverified.

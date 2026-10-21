---
name: keel-md-docx
description: Export a local Markdown file that contains SVG diagrams to one Word (.docx) document, keeping the SVG as vector images with PNG fallbacks. Use when the user asks to export, convert, or deliver Markdown with SVG as Word or .docx. Do not use for other document formats, for Markdown without a Word request, or for editing an existing Word file.
---

# keel-md-docx

## Purpose

Turn one local Markdown file into one `.docx`: headings, paragraphs, inline formatting, lists, quotes, code blocks, and tables stay editable; every SVG becomes a vector image with an embedded PNG fallback, scaled to fit the page; every image ends up inside the document. The converter is `scripts/md2word.py` with the helper `scripts/runtime.mjs`, run by `keel docx convert` in an environment Keel manages. Nothing here runs unless the user asks for this export.

## Steps

1. **Check the environment.** Run `keel docx setup`. Without `--yes` it installs nothing: it prints each package, its licence and size, and where the environment would go (`~/.keel/docx/`, or `$KEEL_HOME/docx/`). If it reports the environment ready, go to step 3.
2. **Ask before installing.** Show the user that list in plain terms and ask whether to install. Only after they agree, run `keel docx setup --yes`. It installs into the Keel-managed environment, never into system Python or Node, and downloads no fonts or runtimes. If the user declines, stop and say the export needs it.
3. **State the output path.** Tell the user where the document will be written: by default the input's name with `.docx`, or the path they gave. If a file is already there, ask whether to replace it; `keel docx convert` refuses an existing output unless `--replace` is given.
4. **Convert.** Run `keel docx convert <input.md> [-o <output.docx>] [--template <template.docx>] [--replace]`. A template contributes its styles, headers, and page settings; its body is discarded.
5. **Report the result.** Relay the output path and image count on success, and every `Warning:` line. On failure relay the `Conversion failed:` reason; the previous output, if any, is untouched.

## What converts

- A standalone `<svg>…</svg>` block, a fenced code block labelled `svg`, and image references to local `.svg` files, resolved relative to the Markdown file. SVG inside ordinary code stays code.
- Local raster images (PNG, JPEG) and `data:` URIs.
- Headings, paragraphs, bold, italic, strikethrough, links, lists, quotes, code blocks, and tables.

## Limits

- An SVG stays an image; it is not split into editable Word shapes.
- `foreignObject`, scripts, external fonts, external images, and external stylesheets inside an SVG fail the conversion with the reason; use SVG `text` and `path`, and embed bitmaps as `data:` URIs.
- A remote image fails the conversion: save it locally first. Nothing is downloaded during conversion.
- Mermaid, math, footnotes, a table of contents, internal bookmark links, and HTML/CSS page layout are not converted. Lists use explicit numbers and bullets, not Word numbering. A tall diagram is scaled down rather than split across pages; a wide table may need a template or a landscape page.
- Inline HTML styling is dropped with a warning; an unsupported Markdown block stops the conversion.
- The default page is A4 with 2 cm margins, Arial with Heiti SC for Chinese. On macOS Keel points the SVG renderer at the system font folders for this process only; on other systems install the fonts the document needs or supply a template.

## Dependencies

Installed only by `keel docx setup --yes`, into `~/.keel/docx/` (`python/` is a virtual environment, `node/` holds the npm packages). Sizes are from the registries on 2026-10-21 for macOS arm64, not measured from an install.

| Package | Version | Licence | Size |
| --- | --- | --- | --- |
| python-docx | `>=1.1,<2` (1.2.0) | MIT | 0.25 MB wheel |
| lxml | `>=5,<7` (6.0.2) | BSD-3-Clause | 8.6 MB wheel |
| Pillow | `>=10,<13` (12.0.0) | MIT-CMU | 4.65 MB wheel |
| marked | 17.0.5 | MIT | 0.44 MB |
| sharp | 0.35.5 | Apache-2.0 | 0.96 MB, plus its platform binary (0.29 MB, Apache-2.0) and libvips 1.3.4 (18.2 MB, LGPL-3.0-or-later) |

The version lists are `scripts/requirements.txt` and `scripts/package.json`. Python 3.10 or newer and the Node that runs `keel` are used.

## Verification status

As of the release that added this skill (#405), the setup plan, the consent flow, the refusals, and the hand-off to the converter are tested with stand-in installers. The real conversion, every failure case against real SVG, and the page-by-page rendering of a Chinese mixed-text example are **unverified** in Keel: the converter was verified as the #405 prototype on macOS arm64 only (Python 3.12, marked 17.0.5, sharp 0.35.5), outside Keel. Linux, Windows, Codex, and Microsoft Word itself are unverified.

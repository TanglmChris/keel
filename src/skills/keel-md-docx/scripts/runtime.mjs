// Markdown parsing and SVG raster fallback, using local dependencies only.
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
const root = process.env.MD2WORD_NODE_MODULES;
const req = root ? createRequire(path.join(root, '__md2word.cjs')) : createRequire(import.meta.url);
const input = JSON.parse(await new Promise((resolve) => {
  let data = ''; process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => data += chunk);
  process.stdin.on('end', () => resolve(data));
}));
try {
  if (input.action === 'parse') {
    const { marked } = await import(pathToFileURL(req.resolve('marked')).href);
    process.stdout.write(JSON.stringify(marked.lexer(input.markdown, { gfm: true })));
  } else if (input.action === 'svg') {
    const sharp = req('sharp');
    if (/<(?:\w+:)?foreignObject\b/i.test(input.svg)) {
      throw new Error('SVG contains foreignObject HTML labels; convert these labels to SVG text or paths first.');
    }
    const output = await sharp(Buffer.from(input.svg), { density: 192, limitInputPixels: 64000000 })
      .resize({ width: 2000, height: 2200, fit: 'inside', withoutEnlargement: false })
      .png().toBuffer();
    await fs.writeFile(input.output, output);
    const metadata = await sharp(output).metadata();
    process.stdout.write(JSON.stringify({ width: metadata.width, height: metadata.height }));
  } else throw new Error('Unknown action');
} catch (error) {
  console.error(error.message); process.exitCode = 1;
}

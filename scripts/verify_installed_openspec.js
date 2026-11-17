#!/usr/bin/env node
'use strict';

// Native release acceptance (#534). Registry and local-tarball installs do not
// treat nested shrinkwrap metadata identically on npm 11. Keep this networked
// test separate from the ordinary scenario suite, and run it in Full-gate CI.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const assert = require('node:assert/strict');
const {spawnSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const expected = JSON.parse(fs.readFileSync(path.join(root, 'npm-shrinkwrap.json'), 'utf8'))
  .packages['node_modules/@fission-ai/openspec'].version;
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'keel-installed-openspec-'));

function run(command, args, env = process.env, cwd = root, allowFailure = false) {
  const result = spawnSync(command, args, {
    env, cwd, encoding: 'utf8', timeout: 180000,
    shell: process.platform === 'win32' && command === npm,
  });
  if (!allowFailure && (result.error || result.status !== 0)) {
    throw Error(`${path.basename(command)} ${args[0]} failed: ${result.error?.message || result.stderr || result.stdout}`);
  }
  return result;
}

try {
  const project = path.join(temp, 'project');
  fs.mkdirSync(path.join(project, 'openspec'), {recursive: true});
  fs.cpSync(path.join(root, 'openspec', 'specs'), path.join(project, 'openspec', 'specs'), {recursive: true});
  const packed = JSON.parse(run(npm, ['pack', root, '--pack-destination', temp, '--json']).stdout)[0];
  const tarball = path.join(temp, packed.filename);
  console.log(`installed-openspec: node ${process.version}; npm ${run(npm, ['--version']).stdout.trim()}; expected ${expected}`);
  for (const kind of ['clean-tarball', 'updater']) {
    const env = {
      ...process.env,
      npm_config_prefix: path.join(temp, kind),
      KEEL_UPDATE_CLAUDE: path.join(temp, 'absent-claude'),
      KEEL_UPDATE_CODEX: path.join(temp, 'absent-codex'),
    };
    // This immutable old release has the broad range that exposed #534. Only
    // this disposable prefix is upgraded; host plugin commands stay absent.
    run(npm, ['install', '-g', kind === 'updater' ? '@christang/keel@5.229.2' : tarball], env);
    if (kind === 'updater') {
      run(process.execPath, [path.join(root, 'bin', 'keel.js'), '--update', '--source', tarball], env, project);
    }
    const globalRoot = run(npm, ['root', '-g'], env).stdout.trim();
    const cli = path.join(globalRoot, '@christang', 'keel', 'bin', 'keel.js');
    const version = run(process.execPath, [cli, 'openspec', '--version'], env, project).stdout.trim();
    const strict = run(process.execPath, [cli, 'openspec', 'validate', '--specs', '--strict'], env, project, true);
    console.log(JSON.stringify({case: kind, version, expected, strictExit: strict.status,
      totals: (strict.stdout + strict.stderr).split('\n').filter(line => line.includes('Totals:'))}));
    assert.equal(version, expected, `installed OpenSpec ${version} differs from locked ${expected}`);
    assert.equal(strict.status, 0, `installed strict validation failed: ${(strict.stdout + strict.stderr).slice(-1200)}`);
  }
  console.log('installed-openspec: clean tarball and updater acceptance passed');
} catch (error) {
  console.error(`installed-openspec: ${error.message}`);
  process.exitCode = 1;
} finally {
  fs.rmSync(temp, {recursive: true, force: true});
}

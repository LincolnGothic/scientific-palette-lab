'use strict';

const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

async function main() {
  const sourcePath = process.argv[2] || path.join(__dirname, '..', 'palette_lab', 'web', 'app.js');
  const source = fs.readFileSync(sourcePath, 'utf8');
  const startMarker = 'async function downloadCode(row)';
  const endMarker = "document.addEventListener('click'";
  for (const marker of [startMarker, endMarker]) {
    if (source.split(marker).length !== 2) {
      throw new Error(`Expected exactly one export boundary marker: ${marker}`);
    }
  }
  const start = source.indexOf(startMarker);
  const end = source.indexOf(endMarker);
  if (end <= start) throw new Error('Export boundary markers are out of order');
  const body = source.slice(start, end);
  const input = JSON.parse(fs.readFileSync(0, 'utf8'));
  const exports = [];
  for (const item of input.cases) {
    let blob, link, clicked = false, revoked = false;
    class Blob {
      constructor(parts) { this.content = parts.join(''); }
    }
    const context = vm.createContext({
      kind: item.kind,
      dataset: item.dataset,
      recOptions: item.recOptions,
      row: item.row,
      Blob,
      URL: {
        createObjectURL(value) { blob = value; return 'blob:export-fixture'; },
        revokeObjectURL(value) {
          if (value !== 'blob:export-fixture') throw new Error('Unexpected revoked URL');
          revoked = true;
        }
      },
      document: {
        createElement(tag) {
          if (tag !== 'a') throw new Error('Expected a download link');
          link = { click() { clicked = true; } };
          return link;
        }
      },
      setTimeout(callback) { callback(); }
    });
    vm.runInContext(body, context, { timeout: 1000, filename: sourcePath });
    await vm.runInContext('downloadCode(row)', context, { timeout: 1000 });
    if (!blob || !link || !clicked || !revoked || link.href !== 'blob:export-fixture') {
      throw new Error(`Incomplete download for case ${item.name}`);
    }
    exports.push({ case: item.name, content: blob.content, filename: link.download });
  }
  process.stdout.write(JSON.stringify({ exports }));
}

main().catch(error => {
  process.stderr.write(`${error.stack}\n`);
  process.exitCode = 1;
});

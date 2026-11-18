const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const cswData = require('../src/site/_data/csw');

test('landing formats visible event dates but preserves exact wiki targets', () => {
  const source = fs.readFileSync('src/site/notes/Home.md', 'utf8');
  const panel = cswData().panels.find(p => p.title.includes('letzten Events'));
  const targets = [...source.matchAll(/\[\[(Events\/[^\]|]+?)(?:\\?\|)/g)].map(m => m[1].replace(/\\$/, ''));
  assert(targets.length > 0);
  for (const target of targets) assert(panel.markdown.includes(target), target);
  assert.match(panel.markdown, /^\| \d{2}\.\d{2}\.\d{2} \|/m);
  assert.doesNotMatch(panel.markdown, /^\| \d{4}-\d{2}-\d{2} \|/m);
});

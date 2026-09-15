const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { splitWikiLink } = require('../src/helpers/wikilinkUtils');

test('splits escaped pipes used inside raw HTML tables', () => {
  assert.deepEqual(
    splitWikiLink("Events/2021-05-10 - Don't_Stop!\\|Event title"),
    ["Events/2021-05-10 - Don't_Stop!", 'Event title']
  );
});

test('splits ordinary pipes without changing the target', () => {
  assert.deepEqual(splitWikiLink('Events/Show|Title'), ['Events/Show', 'Title']);
});

test('team cards have compact responsive desktop and mobile rules', () => {
  const scss = fs.readFileSync(
    path.join(__dirname, '../src/site/styles/custom-style.scss'),
    'utf8'
  );
  assert.match(scss, /\.team-roster-grid\{[^}]*minmax\(132px,1fr\)/);
  assert.match(scss, /\.team-member-card img\{[^}]*height:120px/);
  assert.match(scss, /@media\(max-width:520px\)[^\n]*grid-template-columns:repeat\(2,minmax\(0,1fr\)\)/);
  assert.match(scss, /@media\(max-width:520px\)[^\n]*\.team-member-card img\{height:104px\}/);
});

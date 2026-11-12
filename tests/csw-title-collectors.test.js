const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { collect, holdersOf } = require('../src/helpers/cswTitleCollectors');
const { enhanceContent } = require('../src/helpers/cswDesign');

const note = rows => `---\ntitle: x\n---\n## Title History\n<table><tbody>\n${rows.map(([who, start]) => `<tr><td>${who}</td><td>${start}</td><td></td></tr>`).join('\n')}\n</tbody></table>\n`;
const link = name => `[[Wrestler/${name}\\|${name}]]`;

test('escaped wikilinks yield each partner once', () => {
  assert.deepStrictEqual(holdersOf(`${link('Bret Hart')} & ${link('Owen Hart')}`), ['Bret Hart', 'Owen Hart']);
});

test('distinct titles count once, partners individually, repeat reigns noted', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'csw-titles-'));
  fs.mkdirSync(path.join(dir, 'Championships'));
  fs.writeFileSync(path.join(dir, 'Championships/choke-slam-world-championship.md'), note([[link('A'), '2024-01-01'], [link('A'), '2025-01-01']]));
  fs.writeFileSync(path.join(dir, 'Championships/choke-slam-tag-team-championship.md'), note([[`${link('A')} & ${link('B')}`, '2024-05-01']]));
  fs.writeFileSync(path.join(dir, 'Championships/choke-slam-trios-championship.md'), note([[`${link('B')} & ${link('C')} & ${link('D')}`, '2024-06-01']]));
  const result = collect(dir);
  assert.strictEqual(result.total, 2);
  const [a, b] = result.groups[0].wrestlers;
  assert.deepStrictEqual([a.name, a.titles.map(t => t.title), a.titles[0].reigns], ['A', ['World', 'Tag Team'], 2]);
  assert.deepStrictEqual([b.name, b.titles.map(t => t.title)], ['B', ['Tag Team', 'Trios']]);
});

test('wrestler profile table becomes fact card with CSV fallback', () => {
  const html = enhanceContent('<table><tr><td><img src="x.png" width="280"></td><td><b>Height:</b> 6\'0"<br><b>Weight:</b> N/A<br><b>Finisher:</b> N/A</td></tr></table>', '/wrestler/csw-test-nobody/');
  assert.match(html, /class="wrestler-profile"/);
  assert.match(html, /<dt>Größe<\/dt><dd>6'0"<\/dd>/);
  assert.match(html, /<dt>Gewicht<\/dt><dd>–<\/dd>/);
  assert.doesNotMatch(html, /table-scroll/);
});

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { parse } = require('node-html-parser');
const { sections, sectionFor, enhanceContent } = require('../src/helpers/cswDesign');

test('section/banner and current navigation are server-resolved, including descendants', () => {
  assert.equal(sections.length, 8);
  for (const section of sections) {
    assert.equal(sectionFor(section.href).key, section.key);
    if (section.path) assert.equal(sectionFor(`/${section.path}/example/`).key, section.key);
  }
  assert.equal(sectionFor('/home/').key, 'home');
  assert.equal(sectionFor('/').key, 'home');
  assert.match(sectionFor('/highlights/').banner, /CSW_Highlights_Banner.png$/);
});

test('generated tables gain keyboard-scroll regions without destroying links/media/order', () => {
  const input = '<h1>🏆 Event</h1><p>Date: 2026-09-14</p><p>Venue</p><img src="poster.png"><video controls><source src="vod.mp4"></video><h2>Matches</h2><table><tr><td><a href="/wrestler/test/">Test</a></td></tr></table>';
  const result = enhanceContent(input);
  const root = parse(result);
  assert.equal(root.querySelector('h1').text, 'Event');
  assert.equal(root.querySelector('.table-scroll').getAttribute('tabindex'), '0');
  assert.equal(root.querySelector('.table-scroll a').getAttribute('href'), '/wrestler/test/');
  assert.equal(root.querySelector('source').getAttribute('src'), 'vod.mp4');
  assert(result.indexOf('Venue') < result.indexOf('poster.png'));
  assert(result.indexOf('poster.png') < result.indexOf('vod.mp4'));
  assert(result.indexOf('vod.mp4') < result.indexOf('Matches'));
  assert.equal(enhanceContent(result), result);
});

test('legacy season themes are replaced by shared CSS, not cascade overrides', () => {
  const output = enhanceContent('<style>:root{--card:#1a1025}</style><div class="s08-hero"><h1>S08</h1></div>');
  assert(!output.includes('<style>'));
  const css = fs.readFileSync('src/site/styles/custom-style.scss', 'utf8');
  assert(!/#(?:1a1025|2a1540|2d0a3d|251535|7c3aed)/i.test(css));
  assert.match(css, /prefers-reduced-motion/);
  assert.match(css, /focus-visible/);
});

test('masthead is valid body content and no longer swaps images using JS', () => {
  const header = fs.readFileSync('src/site/_includes/components/pageheader.njk', 'utf8');
  const layout = fs.readFileSync('src/site/_includes/layouts/note.njk', 'utf8');
  assert(!header.includes('<script>'));
  assert(header.includes('aria-current="page"'));
  assert(header.includes('aria-expanded="false"'));
  assert(layout.indexOf('<body') < layout.indexOf('include "components/pageheader.njk"'));
  assert(layout.includes('components/landing.njk'));
});

test('legacy event HTML retains a real Matches heading and uses its existing poster for VODs', () => {
  const output = enhanceContent('<img src="existing-poster.png" width="300" style="float:left"><div style="background:#1a1a2e"><video poster="/img/posters/full_event_video.png"><source src="vod.mp4"></video></div>\n## Matches\n<table></table>', '/events/example/');
  const root = parse(output);
  assert.equal(root.querySelector('h2#matches').text, 'Matches');
  assert.equal(root.querySelector('video').getAttribute('poster'), 'existing-poster.png');
  assert.equal(root.querySelector('.event-poster').getAttribute('style'), undefined);
  assert.equal(root.querySelector('source').getAttribute('src'), 'vod.mp4');
});

test('landing reads regenerated Home tables instead of hard-coded champions or event counts', () => {
  const load = require('../src/site/_data/csw');
  const read = fs.readFileSync;
  try {
    fs.readFileSync = (file, ...args) => file === 'src/site/notes/Home.md'
      ? '---\ntitle: Home\n---\n## Other section\nIgnore\n## Die letzten Events\n| Datum | Show |\n|---|---|\n| 2026-10-16 | Fixture Show |\n## Aktuelle Champions\n| Titel | Champion |\n|---|---|\n| Fixture Title | Fixture Champion |\n'
      : read(file, ...args);
    const data = load();
    assert.equal(data.panels.length, 2);
    assert(data.panels[0].markdown.includes('16.10.26'));
    assert(data.panels[0].markdown.includes('Fixture Show'));
    assert(data.panels[1].markdown.includes('Fixture Champion'));
    assert(!data.panels.some(panel => panel.markdown.includes('Kazuchika Okada')));
  } finally {
    fs.readFileSync = read;
  }
});

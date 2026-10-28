const test = require('node:test');
const assert = require('node:assert/strict');
const { parse } = require('node-html-parser');
const { enhanceContent } = require('../src/helpers/cswDesign');
const { seasonFor } = require('../src/helpers/cswHighlightSeasons');

test('classification ignores date and stale attributes, and refuses conflicting explicit seasons', () => {
  assert.equal(seasonFor(parse('<article data-season="s05"><video src="misc_2023-05-19.mp4"></video></article>').firstChild), 'misc');
  assert.equal(seasonFor(parse('<article><video src="S05E03_clip.mp4"></video><a href="/events/2023-05-19-s06e02-other/">Event</a></article>').firstChild), 'misc');
  assert.equal(seasonFor(parse('<article><video src="unknown.mp4"></video><div class="title">S5E03 — Clip</div></article>').firstChild), 's05');
});

const card = (source, title = 'Clip', meta = '2023-05-19') => `<div class="hl-card" data-type="clip" data-season="s05"><video controls poster="logo.png"><source src="${source}"></video><div class="info"><div class="title">${title}</div><div class="meta">${meta}</div></div></div>`;
const render = cards => parse(enhanceContent(`<div class="hl-filter"><button class="active" onclick="filter('all')">All</button><button onclick="filter('s05')">Season 5</button></div><div class="hl-season" data-season="s05"><h2>Season 5</h2><div class="hl-grid">${cards}</div></div>`, '/highlights/'));

test('unknown dated clip is never Season 5 and has consistent cross-season group, badge and filter', () => {
  const root = render(card('misc_2023-05-19_unknown.mp4'));
  const clip = root.querySelector('source[src="misc_2023-05-19_unknown.mp4"]').closest('.hl-card');
  assert.equal(clip.getAttribute('data-season'), 'misc');
  assert.equal(clip.closest('.hl-season').getAttribute('data-season'), 'misc');
  assert.equal(clip.closest('.hl-season').querySelector('h2').text, 'Saisonübergreifende Highlights');
  assert.equal(clip.querySelector('.hl-season-label').text, 'Saisonübergreifende Highlights');
  assert.match(clip.getAttribute('aria-label'), /Saisonübergreifende Highlights/);
  assert.match(clip.querySelector('video').getAttribute('aria-label'), /Saisonübergreifende Highlights/);
  assert.equal(root.querySelector('button[data-filter="misc"]').text, 'Saisonübergreifende Highlights');
  assert.equal(root.querySelector('.hl-season[data-season="s05"]'), null);
});

test('explicit S05 clip stays Season 5 while incorrect legacy data-season is not authoritative', () => {
  const root = render(card('S05E03_Hogan.mp4') + card('S06E02_other.mp4'));
  for (const [source, season, label] of [['S05E03_Hogan.mp4', 's05', 'Season 5'], ['S06E02_other.mp4', 's06', 'Season 6']]) {
    const clip = root.querySelector(`source[src="${source}"]`).closest('.hl-card');
    assert.equal(clip.getAttribute('data-season'), season);
    assert.equal(clip.closest('.hl-season').getAttribute('data-season'), season);
    assert.equal(clip.querySelector('.hl-season-label').text, label);
  }
});

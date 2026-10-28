// Classify only explicit episode identities, never legacy data-season or dates.
const { parse } = require('node-html-parser');
const crossSeason = 'Saisonübergreifende Highlights';
const labelFor = key => key === 'misc' ? crossSeason : `Season ${Number(key.slice(1))}`;
const escape = value => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));

function seasonFor(card) {
  const evidence = [
    ...card.querySelectorAll('video[src], source[src]').map(node => node.getAttribute('src').split(/[?#]/)[0].split('/').pop()),
    ...card.querySelectorAll('a[href]').map(node => node.getAttribute('href').split(/[?#]/)[0]),
    card.querySelector('.title')?.text || '',
    card.querySelector('.meta')?.text || '',
  ];
  const seasons = new Set(evidence.flatMap(value => [...value.matchAll(/(?:^|[^a-z0-9])s(\d+)e\d+(?=$|[^0-9])/gi)].map(match => Number(match[1]))));
  return seasons.size === 1 ? `s${String([...seasons][0]).padStart(2, '0')}` : 'misc';
}

function normalizeHighlights(root) {
  for (const card of root.querySelectorAll('.hl-card')) {
    const key = seasonFor(card);
    const label = labelFor(key);
    card.setAttribute('data-season', key);
    const title = card.querySelector('.title')?.text || 'Video';
    card.setAttribute('aria-label', `${title} — ${label}`);
    for (const video of card.querySelectorAll('video')) video.setAttribute('aria-label', `${title} — ${label}`);
    const info = card.querySelector('.info');
    if (info) {
      let badge = info.querySelector('.hl-season-label');
      if (!badge) {
        info.appendChild(parse('<div class="hl-season-label"></div>').firstChild);
        badge = info.querySelector('.hl-season-label');
      }
      badge.set_content(escape(label));
    }
    // Standalone fixtures/cards without a section still get correct labels.
    const parent = card.closest('.hl-season');
    if (!parent || parent.getAttribute('data-season') === key) continue;
    let grid = root.querySelector(`.hl-season[data-season="${key}"] .hl-grid`);
    if (!grid) {
      root.insertAdjacentHTML('beforeend', `<section class="hl-season" data-season="${key}"><h2>${label === crossSeason ? label : `${label} — Videos`}</h2><div class="hl-grid"></div></section>`);
      grid = root.querySelector(`.hl-season[data-season="${key}"] .hl-grid`);
    }
    card.remove();
    grid.appendChild(card);
  }
  for (const section of root.querySelectorAll('.hl-season')) {
    if (!section.querySelector('.hl-card')) { section.remove(); continue; }
    const label = labelFor(section.getAttribute('data-season'));
    section.setAttribute('aria-label', label);
    if (label === crossSeason) section.querySelector('h2')?.set_content(crossSeason);
  }
  const filters = root.querySelector('.hl-filter');
  if (filters) {
    filters.setAttribute('role', 'group');
    filters.setAttribute('aria-label', 'Videos nach Staffel oder Typ filtern');
    for (const section of root.querySelectorAll('.hl-season')) {
      const key = section.getAttribute('data-season');
      const buttons = filters.querySelectorAll('button');
      let button = buttons.find(node => node.getAttribute('data-filter') === key || node.getAttribute('onclick') === `filter('${key}')`);
      if (!button) {
        filters.insertAdjacentHTML('beforeend', `<button type="button" data-filter="${key}">${labelFor(key)}</button>`);
      } else if (key === 'misc') button.set_content(crossSeason);
    }
  }
  const subtitle = root.querySelector('.hl-hero p');
  if (subtitle) subtitle.set_content(`Full Events · Match Clips · ${crossSeason}`);
}

module.exports = { seasonFor, normalizeHighlights };

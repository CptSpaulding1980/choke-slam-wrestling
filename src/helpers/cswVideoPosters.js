const fs = require('node:fs');
const path = require('node:path');
const matter = require('gray-matter');
const { parse } = require('node-html-parser');
const fallback = 'https://github.com/CptSpaulding1980/choke-slam-wrestling/releases/download/images/ChokeSlam.png';
const eventPath = value => String(value || '').replace(/^https?:\/\/[^/]+/, '').replace(/^\/choke-slam-wrestling/, '').split(/[?#]/)[0];
const isPoster = value => Boolean(value && !/(?:^|\/)(?:ChokeSlam\.png|full_event_video\.png)(?:[?#]|$)/i.test(value));

// Read maintained event notes at build time: no sheet sync or network required.
function loadEvents(directory = path.join(__dirname, '../site/notes/Events')) {
  return fs.readdirSync(directory).filter(file => file.endsWith('.md')).sort().map(file => {
    const { data, content } = matter(fs.readFileSync(path.join(directory, file), 'utf8'));
    const root = parse(content);
    const image = root.querySelector('img[width="300"]')?.getAttribute('src');
    const poster = isPoster(data.image) ? data.image : isPoster(image) ? image : null;
    const videos = root.querySelectorAll('video').map(video => ({
      source: video.getAttribute('src') || video.querySelector('source')?.getAttribute('src'),
      poster: isPoster(video.getAttribute('poster')) ? video.getAttribute('poster') : poster,
    }));
    return { href: eventPath(data.permalink), title: String(data.title || path.basename(file, '.md')), date: String(data.date || ''), poster, videos };
  });
}

function resolvePoster(href, source, events) {
  const exact = events.filter(event => event.href === eventPath(href));
  // The card's exact event permalink is authoritative. Legacy notes can embed
  // another day's VOD; do not let that cross-association steal the card's poster.
  // Within that event, an explicit source-specific poster preserves multipart art.
  // With no exact event link, accept only an unambiguous exact source match.
  const scope = exact.length ? exact : events;
  const candidates = scope.flatMap(event => (event.videos || [])
    .filter(video => source && video.source === source)
    .map(video => ({ event, poster: isPoster(video.poster) ? video.poster : event.poster })));
  if (candidates.length) {
    const posters = [...new Set(candidates.map(match => match.poster))];
    return posters.length === 1 && isPoster(posters[0]) ? posters[0] : fallback;
  }
  return exact.length === 1 && isPoster(exact[0].poster) ? exact[0].poster : fallback;
}

const escape = value => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));

function reconcileHighlights(root, events) {
  const present = new Set(root.querySelectorAll('video').map(video => video.getAttribute('src') || video.querySelector('source')?.getAttribute('src')));
  const bySource = new Map();
  for (const event of events) {
    if (!/^\/events\/.+\/$/.test(event.href)) continue;
    for (const video of event.videos) {
      if (!video.source) continue;
      if (!bySource.has(video.source)) bySource.set(video.source, []);
      bySource.get(video.source).push(event);
    }
  }
  for (const [source, candidates] of bySource) {
    if (present.has(source)) continue;
    // A legacy note can repeat an earlier day's source. Prefer the exact date
    // only to disambiguate those associations, never as the official event date.
    const matching = candidates.filter(event => event.date && source.includes(event.date));
    const event = matching.length === 1 ? matching[0] : candidates[0];
    const season = event.title.match(/S(\d+)E\d+/i)?.[1];
    if (!season) continue;
    const key = `s${season}`;
    let grid = root.querySelector(`.hl-season[data-season="${key}"] .hl-grid`);
    if (!grid) {
      root.insertAdjacentHTML('beforeend', `<section class="hl-season" data-season="${key}"><h2>Season ${Number(season)} — Videos</h2><div class="hl-grid"></div></section>`);
      grid = root.querySelector(`.hl-season[data-season="${key}"] .hl-grid`);
    }
    const type = /full_event/i.test(source) ? 'full' : 'clip';
    grid.insertAdjacentHTML('beforeend', `<article class="hl-card" data-type="${type}" data-season="${key}"><video controls preload="none" poster="${escape(resolvePoster(event.href, source, events))}"><source src="${escape(source)}" type="video/mp4"></video><div class="info"><div class="title">${escape(event.title.replace('_', ' — '))}</div><div class="meta">${escape(event.date)}</div><a href="/choke-slam-wrestling${escape(event.href)}">→ Event Page</a></div></article>`);
    present.add(source);
  }
}

function enhanceHighlights(root) {
  const events = loadEvents();
  reconcileHighlights(root, events);
  const cards = root.querySelectorAll('.hl-card');
  for (const card of cards) {
    const href = card.querySelector('a[href]')?.getAttribute('href');
    for (const video of card.querySelectorAll('video')) {
      const source = video.getAttribute('src') || video.querySelector('source')?.getAttribute('src');
      video.setAttribute('poster', resolvePoster(href, source, events));
    }
  }
  require('./cswHighlightSeasons').normalizeHighlights(root);
}
module.exports = { fallback, loadEvents, resolvePoster, enhanceHighlights };

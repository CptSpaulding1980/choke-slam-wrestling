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
    return { href: eventPath(data.permalink), poster, videos };
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

function enhanceHighlights(root) {
  const cards = root.querySelectorAll('.hl-card');
  if (!cards.length) return;
  const events = loadEvents();
  for (const card of cards) {
    const href = card.querySelector('a[href]')?.getAttribute('href');
    for (const video of card.querySelectorAll('video')) {
      const source = video.getAttribute('src') || video.querySelector('source')?.getAttribute('src');
      video.setAttribute('poster', resolvePoster(href, source, events));
    }
  }
}
module.exports = { fallback, loadEvents, resolvePoster, enhanceHighlights };

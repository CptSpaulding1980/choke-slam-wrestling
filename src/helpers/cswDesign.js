const { parse } = require('node-html-parser');

const base = '/choke-slam-wrestling';
const fs = require('node:fs');
const path = require('node:path');
const images = `${base}/img/banners/`;
const sections = [
  ['home', '', 'Start', 'CSW_Header_Banner.png'],
  ['events', 'events', 'Events', 'CSW_Events_Banner.png'],
  ['roster', 'wrestler', 'Roster', 'CSW_Roster_Banner.png'],
  ['titles', 'championships', 'Titel', 'CSW_Championships_Banner.png'],
  ['teams', 'teams', 'Teams', 'CSW_Teams_Banner.png'],
  ['stats', 'statistiken', 'Statistiken', 'CSW_Header_Banner.png'],
  ['highlights', 'highlights', 'Highlights', 'CSW_Highlights_Banner.png'],
  ['s08', 's08', 'Season 8', 'CSW_Header_Banner.png'],
].map(([key, path, label, banner]) => ({ key, path, label, banner: images + banner, href: `${base}/${path ? path + '/' : ''}` }));

function sectionFor(url = '/') {
  const path = url.replace(base, '').replace(/^\//, '').split('/')[0];
  return sections.find(section => section.path === path) || sections[0];
}

// Presentation-only enhancement: generated notes and historical results stay intact.
function displayTitle(title, url = '') {
  return url.includes('/teams/') && title === 'Saint Rebel Radicalz' ? 'Special Response Rangers' : title;
}

function enhanceContent(content, url = '') {
  // Legacy generators omit the blank line after raw video HTML. Markdown-it
  // leaves this heading as text; repair presentation without rewriting notes.
  const html = url.startsWith('/events/')
    ? (content || '').replace(/(^|\n)## Matches(?=\n|$)/g, '$1<h2 id="matches">Matches</h2>')
    : content || '';
  const root = parse(html);
  if (url.startsWith('/highlights/')) require('./cswVideoPosters').enhanceHighlights(root);
  // Only the known decorative duplicate, never posters/portraits/content images.
  for (const image of root.querySelectorAll('.hl-hero img')) {
    if ((image.getAttribute('src') || '').endsWith('CSW_Highlights_Banner.png')) image.remove();
  }
  // Hundreds of megabytes of VODs must not be fetched until playback is requested.
  for (const video of root.querySelectorAll('video')) video.setAttribute('preload', 'none');
  // These maintained sections now use the shared stylesheet, not embedded themes.
  if (root.querySelector('.hl-filter, .s08-hero')) {
    for (const style of root.querySelectorAll('style')) style.remove();
  }
  const filters = root.querySelector('.hl-filter');
  if (filters) {
    filters.setAttribute('hidden', '');
    for (const button of filters.querySelectorAll('button')) {
      const match = (button.getAttribute('onclick') || '').match(/filter\('([^']+)'\)/);
      if (match) button.setAttribute('data-filter', match[1]);
      button.removeAttribute('onclick');
      button.setAttribute('type', 'button');
      button.setAttribute('aria-pressed', String(button.classList.contains('active')));
      if (button.text === 'All') button.set_content('Alle');
    }
    for (const script of root.querySelectorAll('script')) {
      if (script.text.includes('function filter(type)')) script.remove();
    }
  }
  for (const element of root.querySelectorAll('[style]')) {
    element.setAttribute('style', element.getAttribute('style')
      .replace(/#(?:1a1025|1a0a30|251535|2d0a3d)/gi, '#191b1f')
      .replace(/#2a1540/gi, '#34373e'));
  }
  if (url.startsWith('/events/')) {
    for (const link of root.querySelectorAll('a[href]')) {
      if (/\.(mp4|webm|ogv)(?:[?#]|$)|^https?:\/\/(?:www\.)?(?:youtu\.be\/|youtube\.com\/watch\?|vimeo\.com\/\d)/i.test(link.getAttribute('href'))) {
        for (const image of link.querySelectorAll('img')) image.classList.add('event-video-preview');
      }
    }
    for (const image of root.querySelectorAll('img[width="300"]')) {
      if (image.classList.contains('event-video-preview')) continue;
      image.removeAttribute('style');
      image.classList.add('event-poster');
      image.setAttribute('alt', 'Eventposter');
    }
    for (const video of root.querySelectorAll('video')) {
      video.classList.add('event-video-preview');
      video.setAttribute('preload', 'none');
      const poster = root.querySelector('.event-poster');
      if (poster && video.getAttribute('poster') === '/img/posters/full_event_video.png') {
        video.setAttribute('poster', poster.getAttribute('src'));
      }
      if (video.parentNode.tagName === 'DIV') {
        video.parentNode.removeAttribute('style');
        video.parentNode.classList.add('event-video');
      }
    }
    if (/^\/events\/[^/]+\/$/.test(url)) enhanceEventProfile(root, url);
  }
  if (url.startsWith('/teams/')) {
    for (const element of root.querySelectorAll('h1, .champ-card span')) {
      if (element.text.trim() === 'Saint Rebel Radicalz') element.set_content('Special Response Rangers');
    }
    for (const image of root.querySelectorAll('img[alt]')) {
      image.setAttribute('alt', image.getAttribute('alt').replace('Saint Rebel Radicalz', 'Special Response Rangers'));
    }
  }
  if (/^\/wrestler\/[^/]+\/$/.test(url)) enhanceWrestlerProfile(root, url.split('/')[2]);
  for (const table of root.querySelectorAll('table')) {
    if (table.parentNode.classList?.contains('table-scroll')) continue;
    table.replaceWith(`<div class="table-scroll" role="region" aria-label="Datentabelle, horizontal scrollbar" tabindex="0">${table.outerHTML}</div>`);
  }
  for (const heading of root.querySelectorAll('h1, h2, h3')) {
    heading.innerHTML = heading.innerHTML.replace(/[\p{Extended_Pictographic}\uFE0F\u200D]/gu, '').trim();
  }
  return root.toString();
}

// Web-sourced profile facts (scripts/csw_wrestler_profiles.py). The manager's
// legacy CSV values are only a fallback when no web value exists.
let profileCache;
function wrestlerProfiles() {
  if (!profileCache) {
    const file = path.join(__dirname, '../../data/wrestler_profiles.json');
    try { profileCache = JSON.parse(fs.readFileSync(file, 'utf8')); } catch { profileCache = {}; }
  }
  return profileCache;
}
const escapeHtml = value => String(value).replace(/[&<>"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[char]);

function enhanceWrestlerProfile(root, slug) {
  const table = root.querySelector('table');
  const image = table?.querySelector('td img');
  if (!image) return;
  const cells = table.querySelectorAll('td');
  const legacy = {};
  for (const [, key, value] of (cells[1]?.innerHTML || '').matchAll(/<b>\s*(Height|Weight|Finisher):\s*<\/b>\s*([^<]*)/gi)) {
    if (value.trim() && value.trim() !== 'N/A') legacy[key.toLowerCase()] = value.trim();
  }
  const profile = wrestlerProfiles()[slug] || {};
  const facts = [['Größe', 'height'], ['Gewicht', 'weight'], ['Nationalität', 'nationality'], ['Finisher', 'finisher']]
    .map(([label, key]) => `<div><dt>${label}</dt><dd>${profile[key] ? escapeHtml(profile[key]) : legacy[key] || '–'}</dd></div>`).join('');
  const sources = Object.entries(profile.sources || {})
    .map(([name, href]) => `<a href="${escapeHtml(href)}" rel="noopener" target="_blank">${escapeHtml(name)}</a>`).join(' · ');
  image.setAttribute('alt', profile.name || slug);
  image.setAttribute('width', '280');
  table.replaceWith(`<div class="wrestler-profile"><figure class="wrestler-portrait">${image.toString()}</figure>`
    + `<div class="wrestler-facts-wrap"><dl class="wrestler-facts">${facts}</dl>`
    + (sources ? `<p class="wrestler-sources">Quelle: ${sources}</p>` : '') + '</div></div>');
}

// Event header as a card like the wrestler profile: poster left, key facts
// right. Rebuilt at render time from the manager's header (logo line,
// Date/Venue) and any legacy poster markup, so duplicated or stray poster
// blocks in generated notes collapse into one consistent layout.
const LOGO_URL = 'https://github.com/CptSpaulding1980/choke-slam-wrestling/releases/download/images/ChokeSlam.png';
const isHeaderLogo = image => image.getAttribute('width') === '40';
const isEmpty = element => !/^(IMG|VIDEO|IFRAME|AUDIO|A|SOURCE)$/.test(element.tagName) && !element.querySelector('img, video, iframe, audio, a') && !element.text.trim();

function enhanceEventProfile(root, url) {
  if (root.querySelector('.event-profile')) return;
  const nodes = root.childNodes;
  const matchesAt = nodes.findIndex(node => node.nodeType === 1 && (node.id === 'matches' || /^Matches$/.test(node.text.trim()) && node.tagName === 'H2'));
  if (matchesAt < 0) return;
  const before = nodes.slice(0, matchesAt).filter(node => node.nodeType === 1);
  let date = '';
  let venue = '';
  const posters = [];
  for (const element of before) {
    const text = element.text;
    if (element.tagName === 'P' && element.querySelector('img') && [...element.querySelectorAll('img')].every(isHeaderLogo)) {
      element.remove();
      continue;
    }
    if (/^(Date|Venue):/m.test(text.trim()) || /\bDate:\s*\d{4}-\d{2}-\d{2}/.test(text)) {
      date = date || (text.match(/Date:\s*(\d{4}-\d{2}-\d{2})/) || [])[1] || '';
      venue = venue || ((text.match(/Venue:\s*([^\n]+)/) || [])[1] || '').trim();
      element.remove();
      continue;
    }
    if (/^H[2-4]$/.test(element.tagName) && /^Poster$/i.test(text.trim())) { element.remove(); continue; }
    const images = element.tagName === 'IMG' ? [element] : element.querySelectorAll('img');
    for (const image of images) {
      if (isHeaderLogo(image) || image.classList.contains('event-video-preview') || image.closest('a, .event-video')) continue;
      const src = image.getAttribute('src');
      if (!posters.includes(src)) posters.push(src);
      image.remove();
    }
    if (element.tagName !== 'IMG' && isEmpty(element)) element.remove();
  }
  for (const heading of root.querySelectorAll('h2, h3, h4')) {
    if (/^Poster$/i.test(heading.text.trim()) && !heading.closest('table')) heading.remove();
  }

  const slug = url.split('/')[2];
  date = date || (slug.match(/^(\d{4}-\d{2}-\d{2})/) || [])[1] || '';
  const [arena, ...place] = venue.split(' - ');
  const episode = slug.match(/-s(\d+)e(\d+)/i);
  const table = nodes.slice(matchesAt + 1).find(node => node.nodeType === 1 && (node.tagName === 'TABLE' || node.querySelector?.('table')));
  const rows = table ? table.querySelectorAll('tbody tr') : [];
  const headers = table ? table.querySelectorAll('th').map(th => th.text.trim()) : [];
  const matchColumn = headers.indexOf('Match');
  const mainEvent = rows.length && matchColumn >= 0 ? rows[rows.length - 1].querySelectorAll('td')[matchColumn]?.innerHTML.trim() : '';
  const day = date ? new Date(`${date}T12:00:00Z`).toLocaleDateString('de-DE', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }) : '';
  const facts = [
    ['Datum', day && escapeHtml(day)],
    ['Arena', arena && escapeHtml(arena.trim())],
    ['Ort', place.length && escapeHtml(place.join(' - ').trim())],
    ['Matches', rows.length ? String(rows.length) : ''],
    ['Main Event', mainEvent],
  ].filter(([, value]) => value).map(([label, value]) => `<div${label === 'Main Event' ? ' class="event-main"' : ''}><dt>${label}</dt><dd>${value}</dd></div>`).join('');
  const [main, ...more] = posters;
  const poster = main
    ? `<img class="event-poster" src="${escapeHtml(main)}" alt="Eventposter" width="300" loading="eager">`
    : `<img class="event-poster event-poster--logo" src="${LOGO_URL}" alt="" width="300">`;
  const extra = more.length
    ? `<div class="event-more-posters">${more.map(src => `<img src="${escapeHtml(src)}" alt="Weiteres Eventposter" width="120" loading="lazy">`).join('')}</div>` : '';
  const eyebrow = episode ? `<p class="eyebrow">Season ${Number(episode[1])} · Episode ${Number(episode[2])}</p>` : '';
  const card = `<section class="event-profile" aria-label="Eventdaten"><figure class="event-portrait">${poster}</figure>`
    + `<div class="event-facts-wrap">${eyebrow}<dl class="event-facts">${facts}</dl>${extra}</div></section>`;
  const first = root.childNodes.find(node => node.nodeType === 1);
  if (first) first.insertAdjacentHTML('beforebegin', card); else root.insertAdjacentHTML('afterbegin', card);
}

// Only checked-in, existing image assets are accepted; invalid overrides use
// the shared fallback. Configure via headerImage/headerPosition in frontmatter
// or directory data, never by modifying a generated note's body.
function headerFor(url = '/', { headerImage, headerPosition } = {}) {
  const fallback = sections[0].banner;
  const candidate = headerImage === undefined ? sectionFor(url).banner : headerImage;
  const relative = typeof candidate === 'string' ? candidate.replace(new RegExp(`^${base}`), '') : '';
  const valid = /^\/img\/[\w/.-]+\.(png|jpe?g|webp|avif)$/i.test(relative)
    && !relative.split('/').includes('..')
    && fs.existsSync(path.join(__dirname, '../site', relative));
  const position = /^(left|center|right)( (top|center|bottom))?$/.test(headerPosition || '')
    ? headerPosition : 'center';
  return { image: valid ? `${base}${relative}` : fallback, position };
}

module.exports = { base, sections, sectionFor, headerFor, enhanceContent, displayTitle };

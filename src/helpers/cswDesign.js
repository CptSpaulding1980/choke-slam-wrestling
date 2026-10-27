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
  ['teams', 'teams', 'Teams', 'CSW_Header_Banner.png'],
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
    for (const image of root.querySelectorAll('img[width="300"]')) {
      image.removeAttribute('style');
      image.classList.add('event-poster');
      image.setAttribute('alt', 'Eventposter');
    }
    for (const video of root.querySelectorAll('video')) {
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
  }
  if (url.startsWith('/teams/')) {
    for (const element of root.querySelectorAll('h1, .champ-card span')) {
      if (element.text.trim() === 'Saint Rebel Radicalz') element.set_content('Special Response Rangers');
    }
    for (const image of root.querySelectorAll('img[alt]')) {
      image.setAttribute('alt', image.getAttribute('alt').replace('Saint Rebel Radicalz', 'Special Response Rangers'));
    }
  }
  for (const table of root.querySelectorAll('table')) {
    if (table.parentNode.classList?.contains('table-scroll')) continue;
    table.replaceWith(`<div class="table-scroll" role="region" aria-label="Datentabelle, horizontal scrollbar" tabindex="0">${table.outerHTML}</div>`);
  }
  for (const heading of root.querySelectorAll('h1, h2, h3')) {
    heading.innerHTML = heading.innerHTML.replace(/[\p{Extended_Pictographic}\uFE0F\u200D]/gu, '').trim();
  }
  return root.toString();
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

// Builds the "Titelsammler" statistic from the manager's championship notes.
// Read at build time, so every regenerated Title History updates it.
const fs = require('node:fs');
const path = require('node:path');

const TITLES = [
  { slug: 'choke-slam-world-championship', short: 'World' },
  { slug: 'choke-slam-womens-championship', short: 'Womens' },
  { slug: 'choke-slam-international-championship', short: 'International' },
  { slug: 'choke-slam-tag-team-championship', short: 'Tag Team' },
  { slug: 'choke-slam-trios-championship', short: 'Trios' },
];
const base = '/choke-slam-wrestling';
const wrestlerSlug = name => name.toLowerCase().replace(/[\s_]+/g, '-').replace(/[^a-z0-9-]/g, '');

// Wikilinks inside raw HTML tables use an escaped separator: [[Wrestler/X\|X]].
function holdersOf(cell) {
  return [...cell.matchAll(/\[\[Wrestler\/([^\]|\\]+?)(?:\\?\|[^\]]*)?\]\]/g)].map(match => match[1].trim());
}

function titleHistory(markdown) {
  const section = markdown.split(/^## Title History\s*$/m)[1];
  if (!section) return [];
  const body = section.split(/<\/tbody>/)[0];
  return [...body.matchAll(/<tr>(.*?)<\/tr>/gs)].map(row => {
    const cells = [...row[1].matchAll(/<td>(.*?)<\/td>/gs)].map(cell => cell[1]);
    return { holders: holdersOf(cells[0] || ''), start: (cells[1] || '').trim() };
  }).filter(reign => reign.holders.length);
}

function collect(notesDir) {
  const wrestlers = new Map();
  for (const title of TITLES) {
    const file = path.join(notesDir, 'Championships', `${title.slug}.md`);
    if (!fs.existsSync(file)) continue;
    for (const reign of titleHistory(fs.readFileSync(file, 'utf8'))) {
      for (const name of new Set(reign.holders)) {
        if (!wrestlers.has(name)) wrestlers.set(name, new Map());
        const held = wrestlers.get(name);
        const entry = held.get(title.short) || { title: title.short, href: `${base}/championships/${title.slug}/`, reigns: 0, first: reign.start };
        entry.reigns += 1;
        if (reign.start && reign.start < entry.first) entry.first = reign.start;
        held.set(title.short, entry);
      }
    }
  }
  const order = TITLES.map(title => title.short);
  const rows = [...wrestlers].map(([name, held]) => ({
    name,
    href: `${base}/wrestler/${wrestlerSlug(name)}/`,
    titles: [...held.values()].sort((a, b) => order.indexOf(a.title) - order.indexOf(b.title)),
  })).map(row => ({ ...row, count: row.titles.length, reigns: row.titles.reduce((sum, t) => sum + t.reigns, 0) }));
  const multi = rows.filter(row => row.count >= 2)
    .sort((a, b) => b.count - a.count || b.reigns - a.reigns || a.name.localeCompare(b.name, 'de'));
  const groups = [...new Set(multi.map(row => row.count))].map(count => ({ count, wrestlers: multi.filter(row => row.count === count) }));
  return { groups, total: multi.length, champions: rows.length, titles: TITLES.length };
}

module.exports = { collect, titleHistory, holdersOf, TITLES };

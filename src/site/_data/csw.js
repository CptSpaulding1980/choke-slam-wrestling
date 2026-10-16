const fs = require('fs');
const matter = require('gray-matter');
const { sections } = require('../../helpers/cswDesign');

module.exports = () => {
  const home = matter(fs.readFileSync('src/site/notes/Home.md', 'utf8')).content;
  // Read the manager's current tables at build time, never duplicate champions/results.
  const panels = home.split(/^## /m).slice(1).filter(section => /letzten Events|Aktuelle Champions/.test(section.split('\n')[0])).map(section => {
    const lines = section.split('\n');
    const title = lines.shift().replace(/[\p{Extended_Pictographic}\uFE0F]/gu, '').trim();
    return { title, markdown: lines.join('\n').replace(/\b(\d{4})-(\d{2})-(\d{2})\b/g, (_, year, month, day) => `${day}.${month}.${year.slice(2)}`) };
  });
  return {
    sections, panels,
    teams: [
      { name: 'Militanter Mummenschanz', manager: 'Philipp Brunkovic', slug: 'militanter-mummenschanz', logo: 'militanter-mummenschanz-20261016.jpg' },
      { name: 'Special Response Rangers', manager: 'Pascal LePas', slug: 'saint-rebel-radicalz', logo: 'special-response-rangers-20261016.jpg' },
      { name: "Sweet 'n Sour Elite", manager: 'Hendrique Delafuente', slug: 'sweet-n-sour-elite', logo: 'sweet-n-sour-elite-20261016.png' },
    ],
  };
};

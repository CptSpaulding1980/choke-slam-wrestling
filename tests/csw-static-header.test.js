const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const matter = require('gray-matter');
const nunjucks = require('nunjucks');
const { parse } = require('node-html-parser');
const design = require('../src/helpers/cswDesign');

test('all independent HTML families use the shared shell and scoped content styles', () => {
  const env = new nunjucks.Environment(new nunjucks.FileSystemLoader('src/site/_includes'));
  env.addFilter('cswSection', design.sectionFor);
  env.addFilter('cswHeader', design.headerFor);
  for (const [file, url] of [
    ['s08/draft/index.njk', '/s08/draft/'],
    ['wrestling_map_northamerica.njk', '/wrestling_map_northamerica.html'],
    ['wrestling_map_northamerica/index.njk', '/wrestling_map_northamerica/'],
    ['404.njk', '/404.html'],
  ]) {
    const source = matter(fs.readFileSync('src/site/' + file, 'utf8'));
    const content = env.renderString(source.content);
    const root = parse(env.render(source.data.layout, { ...source.data, content, page: { url }, csw: { sections: design.sections, teams: [] } }));
    assert.equal(root.querySelectorAll('header.csw-masthead').length, 1, file);
    assert(root.querySelector('.csw-masthead .brand-logo'), file);
    assert(root.querySelector('main#main-content'), file);
    assert.equal(root.querySelectorAll('.csw-navigation').length, 1, file);
    assert(root.querySelector('script[src$="csw-navigation.js"]'), file);
    assert(root.querySelector('link[href$="custom-style.css"]'), file);
    if (source.data.staticClass) {
      const css = fs.readFileSync(`src/site/styles/${source.data.staticClass}.scss`, 'utf8');
      assert(css.startsWith(`.${source.data.staticClass} {`));
      assert.equal(root.querySelectorAll('.legacy-content').length, 1);
    }
  }
});

const test = require('node:test');
const assert = require('node:assert/strict');
const nunjucks = require('nunjucks');
const { parse } = require('node-html-parser');
const design = require('../src/helpers/cswDesign');
const fs = require('node:fs');
const env = new nunjucks.Environment(new nunjucks.FileSystemLoader('src/site/_includes'));
env.addFilter('cswSection', design.sectionFor);
// Register the production resolver when implemented; old rendering still exercises the real template.
env.addFilter('cswHeader', (...args) => design.headerFor?.(...args));

test('single banner masthead contains the prominent authentic logo, menu remains its next sibling', () => {
  const root = parse(env.render('components/pageheader.njk', { page: { url: '/wrestler/big-van-vader/' }, csw: { sections: design.sections } }));
  const header = root.querySelector('header.csw-masthead');
  assert(header.querySelector('.csw-banner .csw-brand .brand-logo'), 'logo must overlay the banner, not occupy a separate brand row');
  assert.equal(header.querySelectorAll('.brand-row').length, 0);
  assert.equal(header.querySelectorAll('.csw-banner').length, 1);
  assert.equal(header.querySelectorAll('nav').length, 0);
  assert.equal(header.nextElementSibling.getAttribute('class'), 'csw-navigation');
  assert.equal(header.querySelector('.brand-logo').getAttribute('src'), '/choke-slam-wrestling/img/csw-official-logo.jpg');
  assert.equal(root.querySelectorAll('.csw-menu a').length, 8);
});

test('header resolves existing local section art, explicit image/crop, and safe global fallback', () => {
  const fs = require('node:fs');
  for (const section of design.sections) {
    const result = design.headerFor(section.href);
    assert(result.image.startsWith('/choke-slam-wrestling/img/banners/'));
    assert(fs.existsSync('src/site/' + result.image.replace('/choke-slam-wrestling/', '')));
  }
  const fallback = design.headerFor('/unknown/').image;
  assert.notEqual(design.headerFor('/events/').image, design.headerFor('/wrestler/').image);
  assert.equal(design.headerFor('/events/', { headerImage: '/img/banners/CSW_Roster_Banner.png', headerPosition: 'right top' }).image, design.headerFor('/wrestler/').image);
  assert.equal(design.headerFor('/events/', { headerPosition: 'right top' }).position, 'right top');
  for (const headerImage of ['/img/missing.png', '/img/../notes/Home.md', 'https://invalid.example/banner.png']) {
    assert.equal(design.headerFor('/events/', { headerImage }).image, fallback);
  }
  assert.equal(design.headerFor('/', { headerPosition: 'url(evil)' }).position, 'center');
});

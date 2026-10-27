const test = require('node:test');
const assert = require('node:assert/strict');
const { parse } = require('node-html-parser');
const { enhanceContent } = require('../src/helpers/cswDesign');

test('remove only duplicate decorative highlight art, preserving titles, posters and portraits', () => {
  const html = '<div class="hl-hero"><img src="CSW_Highlights_Banner.png"><h1>Highlights</h1><p>Videos</p></div><img src="portrait.png"><img src="poster.png"><video poster="poster.png"></video>';
  const root = parse(enhanceContent(html, '/highlights/'));
  assert.equal(root.querySelector('.hl-hero img'), null);
  assert.equal(root.querySelector('h1').text, 'Highlights');
  assert.deepEqual(root.querySelectorAll('img').map(img => img.getAttribute('src')), ['portrait.png', 'poster.png']);
  assert.equal(root.querySelector('video').getAttribute('poster'), 'poster.png');
});

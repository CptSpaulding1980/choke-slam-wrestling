const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { parse } = require('node-html-parser');
const { enhanceContent } = require('../src/helpers/cswDesign');

test('event cards use the measured Highlights width and share its uncropped 16:9 media rule', () => {
  const sass = require('sass');
  const css = sass.compileString(fs.readFileSync('src/site/styles/custom-style.scss', 'utf8')).css;
  assert.match(css, /\.event-video\s*\{[^}]*max-width: 392px/);
  assert.match(css, /\.hl-card video,\s*\.event-video-preview\s*\{[^}]*aspect-ratio: 16\/9;[^}]*object-fit: contain/);
  assert.match(css, /\.event-video-preview\s*\{[^}]*max-width: 390px/);
});

test('linked video thumbnails are compact, while poster links and plain download links remain intact', () => {
  const input = '<a href="movie.mp4"><img src="thumb.png" width="300"></a><a href="poster.png"><img width="300" src="poster.png"></a><a href="movie.mp4">Download</a>';
  const root = parse(enhanceContent(input, '/events/test/'));
  assert(!root.querySelector('a img').classList.contains('event-poster'));
  assert(root.querySelector('a img').classList.contains('event-video-preview'));
  assert.equal(root.querySelectorAll('.event-video-preview').length, 1);
  assert.equal(root.querySelectorAll('a').length, 3);
  assert.equal(root.querySelector('a').getAttribute('href'), 'movie.mp4');
});

test('all event players, including bare players, receive the compact preview contract without changing media', () => {
  const input = '<img width="300" src="poster.png"><div style="max-width:800px"><video controls poster="portrait.png"><source src="full.mp4" type="video/mp4"></video><a href="full.mp4">Download MP4</a></div><video controls src="highlight.mp4" poster="thumb.png"></video><h2>Matches</h2>';
  const output = enhanceContent(input, '/events/example/');
  const root = parse(output);
  assert.equal(root.querySelectorAll('video.event-video-preview').length, 2);
  assert.equal(root.querySelector('video').getAttribute('poster'), 'portrait.png');
  assert.equal(root.querySelector('source').getAttribute('src'), 'full.mp4');
  assert.equal(root.querySelector('video[src]').getAttribute('src'), 'highlight.mp4');
  assert.equal(root.querySelector('a').getAttribute('href'), 'full.mp4');
  for (const video of root.querySelectorAll('video')) {
    assert(video.hasAttribute('controls'));
    assert.equal(video.getAttribute('preload'), 'none');
    assert(!video.hasAttribute('autoplay'));
  }
  assert(!root.querySelector('.event-poster').classList.contains('event-video-preview'));
  assert.equal(enhanceContent(output, '/events/example/'), output);
  assert.equal(parse(enhanceContent(input, '/highlights/')).querySelectorAll('.event-video-preview').length, 0);
});

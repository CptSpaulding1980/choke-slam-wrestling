const test = require('node:test');
const assert = require('node:assert/strict');
const { parse } = require('node-html-parser');
const { enhanceContent } = require('../src/helpers/cswDesign');
const { resolvePoster, fallback, loadEvents } = require('../src/helpers/cswVideoPosters');

test('multipart resolution respects exact event links and selects source-specific posters within that event', () => {
  const events = [
    { href: '/events/day-one/', poster: 'day1.png', videos: [{ source: 'part1.mp4', poster: 'day1.png' }] },
    { href: '/events/day-two/', poster: 'day2.png', videos: [{ source: 'part2.mp4', poster: 'special-part2.png' }] },
  ];
  assert.equal(resolvePoster('/events/day-one/', 'part2.mp4', events), 'day1.png');
  assert.equal(resolvePoster('/events/day-two/', 'part2.mp4', events), 'special-part2.png');
  const actualEvents = loadEvents();
  assert.match(resolvePoster('/events/2026-06-08-s07e11-tanztderknighstlaune/', 'https://github.com/CptSpaulding1980/choke-slam-wrestling/releases/download/video/S07E11_2026-06-08_full_event.mp4', actualEvents), /2026-06-08-s07e11-tanzt-der-koenig-hat-laune_poster.png$/);
  assert.equal(resolvePoster('/events/day-two/', 'clip.mp4', events), 'day2.png');
  assert.equal(resolvePoster('/events/', 'part1.mp4', events), 'day1.png');
  assert.equal(resolvePoster('/events/unknown/', 'unknown.mp4', events), fallback);
  assert.equal(resolvePoster('/events/unknown/', 'part.mp4', [
    { ...events[0], videos: [{ source: 'part.mp4', poster: 'day1.png' }] },
    { ...events[1], videos: [{ source: 'part.mp4', poster: 'day2.png' }] },
  ]), fallback);
});

test('Highlights always includes every unique event video, especially S08E03, with official event date and poster', () => {
  const root = parse(enhanceContent('<div class="hl-season" data-season="s08"><div class="hl-grid"></div></div>', '/highlights/'));
  const sources = root.querySelectorAll('video source').map(source => source.getAttribute('src'));
  const events = loadEvents();
  const expected = [...new Set(events.flatMap(event => event.videos.map(video => video.source)))];
  assert.deepEqual([...new Set(sources)].sort(), expected.sort());
  assert.equal(sources.length, expected.length);
  const dayOneVideo = root.querySelectorAll('video').find(v => v.querySelector('source').getAttribute('src').includes('S07E11_2791888211_'));
  assert.match(dayOneVideo.parentNode.querySelector('a').getAttribute('href'), /2026-06-08-s07e11/);
  assert.match(dayOneVideo.getAttribute('poster'), /2026-06-08-s07e11/);
  const video = root.querySelectorAll('video').find(v => v.querySelector('source').getAttribute('src').includes('S08E03_'));
  assert.match(video.getAttribute('poster'), /S08E03_Tribute_to_the_Bastard_poster.png$/);
  assert.match(video.parentNode.text, /2026-10-26/);
  assert(!video.parentNode.text.includes('2026-10-03'));
  assert.equal(video.parentNode.querySelector('a').getAttribute('href'), '/choke-slam-wrestling/events/2026-10-26-s08e03-tribute-to-the-bastard/');
  const input = root.toString();
  assert.equal(enhanceContent(input, '/highlights/'), input);
});

test('Highlights build resolver uses restored exact-event posters and keeps absent posters as logo fallback', () => {
  const input = '<div class="hl-card"><video controls poster="logo.png"><source src="clip.mp4"></video><a href="/choke-slam-wrestling/events/2026-07-31-s08e01-genesis/">Event</a></div><div class="hl-card"><video controls poster="logo.png"><source src="unknown.mp4"></video><a href="/events/unknown/">Event</a></div>';
  const root = parse(enhanceContent(input, '/highlights/'));
  assert.match(root.querySelector('video').getAttribute('poster'), /S08E01_Genesis_poster.png$/);
  assert.match(root.querySelectorAll('video')[1].getAttribute('poster'), /ChokeSlam.png$/);
  assert.equal(root.querySelector('source').getAttribute('src'), 'clip.mp4');
  assert(root.querySelector('video').hasAttribute('controls'));
});

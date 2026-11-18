"""Historical identity regression: one confirmed Card84, not two event parts."""
import hashlib
import re
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from csw_poster_preflight import event_poster

ROOT = Path(__file__).resolve().parents[1]
TITLE = 'S08E03_Tribute to the Bastard'
POSTER = 'https://github.com/CptSpaulding1980/choke-slam-wrestling/releases/download/images/S08E03_Tribute_to_the_Bastard_poster.png'

class S08E03IdentityTests(unittest.TestCase):
    def test_exact_21_result_identity_date_poster_and_video_survive(self):
        events = list((ROOT/'src/site/notes/Events').glob('*S08E03*.md'))
        self.assertEqual([p.name for p in events], ['2026-10-26 - '+TITLE+'.md'])
        text = events[0].read_text()
        self.assertIn('date: "2026-10-26"', text)
        self.assertIn(f'image: "{POSTER}"', text)
        self.assertEqual(event_poster(text, 'S08E03'), POSTER)
        self.assertIn(f'<img src="{POSTER}" width="300"', text)
        self.assertIn('releases/download/video/S08E03_2891048502_2026-10-03_full_event.mp4', text)
        rows = [line for line in text.splitlines() if re.match(r'^\| \d+ \|', line)]
        self.assertEqual(len(rows), 21)
        self.assertEqual(hashlib.sha256('\n'.join(rows).encode()).hexdigest(), '048399f622333b5ee565293810c46904a2be1940c23acbf4b95b20a24efeaf8c')

    def test_all_maintained_backlinks_use_official_date(self):
        notes = ROOT/'src/site/notes'
        for path in notes.rglob('*.md'):
            text = path.read_text()
            self.assertNotIn('2026-09-14 - '+TITLE, text, str(path))
            self.assertNotIn('/events/2026-09-14-s08e03-tribute-to-the-bastard/', text, str(path))
        index = (notes/'Events.md').read_text()
        lines = [l for l in index.splitlines() if TITLE in l]
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith('| 2026-10-26 |'))
        self.assertTrue(lines[0].endswith('| 21 |'))
        self.assertIn('| S08 | 47 |', (notes/'Statistiken/Globale Statistiken.md').read_text())
        redirect = (ROOT/'src/site/redirects/s08e03-september.njk').read_text()
        self.assertIn('eleventyExcludeFromCollections: true', redirect)
        self.assertIn('content="0; url=/choke-slam-wrestling/events/2026-10-26-s08e03-tribute-to-the-bastard/"', redirect)

if __name__ == '__main__': unittest.main()

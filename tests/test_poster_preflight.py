import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import csw_poster_preflight as preflight

POSTER = 'https://github.com/CptSpaulding1980/choke-slam-wrestling/releases/download/images/S08E03_Tribute_to_the_Bastard_poster.png'
LOGO = POSTER.rsplit('/', 1)[0] + '/ChokeSlam.png'

class PosterPreflightTests(unittest.TestCase):
    def test_body_poster_does_not_depend_on_display_width(self):
        for width in ('250', '300', '375', None):
            attr = f' width="{width}"' if width else ''
            page = f'---\nimage: "{LOGO}"\n---\n<img src="{POSTER}"{attr}>\n## Matches\n'
            self.assertEqual(preflight.event_poster(page, 'S08E03'), POSTER)
        self.assertIsNone(preflight.event_poster(f'---\nimage: "{LOGO}"\n---\n', 'S08E03'))
        self.assertIsNone(preflight.event_poster(f'---\nimage: "{POSTER}"\n---\n', 'S08E04'))

    def test_identical_card_date_variants_are_blocked_not_combined(self):
        a = dict(title='S08E03_Tribute', venue='Arena', location='City',
                 date='2026-09-14', matches=[{'nr': str(i), 'finish': str(i)} for i in range(1, 22)])
        b = dict(a, date='2026-10-26')
        self.assertTrue(preflight.has_duplicate_cards([a, b]))
        self.assertFalse(preflight.has_duplicate_cards([a]))
        self.assertFalse(preflight.has_duplicate_cards([a, dict(b, title='S08E03_Tribute - Night 2')]))
        self.assertFalse(preflight.has_duplicate_cards([a, dict(b, matches=[{'nr': '1', 'finish': 'different'}])]))
        self.assertFalse(preflight.has_duplicate_cards([dict(a, matches=[]), dict(b, matches=[])]))
        # Literal wiki pipes can make legacy parsed fields lossy: compare full rows.
        self.assertFalse(preflight.has_duplicate_cards([
            dict(a, match_identity=['| 1 | [[Wrestler/A\\|A]] | result one |']),
            dict(b, match_identity=['| 1 | [[Wrestler/A\\|A]] | result two |'])]))

    def test_refresh_preserves_verified_exact_event_prefix_and_vod(self):
        prefix = f'''---
title: "S08E03_Tribute"
date: "2026-10-26"
image: "{POSTER}"
---
<img src="{POSTER}" width="300">
<video controls><source src="https://example.org/vod.mp4"></video>

'''
        page = prefix + '## Matches\n| original results |'
        self.assertEqual(preflight.preserved_event_prefix(page, '2026-10-26', 'S08E03_Tribute'), prefix)
        self.assertIsNone(preflight.preserved_event_prefix(page, '2026-09-14', 'S08E03_Tribute'))
        self.assertIsNone(preflight.preserved_event_prefix(page, '2026-10-26', 'S08E04_Other'))
        self.assertIsNone(preflight.preserved_event_prefix(page.replace(POSTER, LOGO), '2026-10-26', 'S08E03_Tribute'))

if __name__ == '__main__':
    unittest.main()

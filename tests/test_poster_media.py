import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from csw_poster_media import attach_posters

LOGO = 'https://github.com/example/repo/releases/download/images/ChokeSlam.png'
POSTER = 'https://github.com/example/repo/releases/download/images/event_poster.png'
PAGE = f'''---
title: "S08E03_Exact title"
date: "2026-10-26"
venue: "Arena"
location: "City"
image: "{LOGO}"
---

<img src="{LOGO}" width="40">**S08E03_Exact title**

**Date:** 2026-10-26
**Venue:** Arena - City

<video controls><source src="https://example.org/video.mp4"></video>
<img src="https://example.org/unrelated.png">

## Matches
| 1 | [[Wrestler/Megumi Kudo\\|Megumi Kudo]] vs. [[Wrestler/Pac\\|Pac]] | Original result |
'''

class PosterMediaTests(unittest.TestCase):
    def test_logo_frontmatter_is_replaced_without_losing_media_or_results(self):
        self.assertIsNotNone(attach_posters, 'explicit non-destructive poster attachment is missing')
        result = attach_posters(PAGE, [POSTER])
        self.assertIn(f'image: "{POSTER}"', result)
        self.assertIn(f'<img src="{LOGO}" width="40">', result)
        for block in ['<video controls><source src="https://example.org/video.mp4"></video>', '<img src="https://example.org/unrelated.png">']:
            self.assertIn(block, result)
        self.assertEqual(result.split('## Matches')[1], PAGE.split('## Matches')[1])
        self.assertLess(result.index('**Venue:**'), result.index(f'<img src="{POSTER}"'))
        self.assertLess(result.index(f'<img src="{POSTER}"'), result.index('<video'))
        self.assertEqual(attach_posters(result, [POSTER]), result)

    def test_legacy_media_before_title_moves_after_metadata_without_deletion(self):
        legacy = PAGE.replace('\n\n<img src="' + LOGO, '\n\n## Poster\n\n<img src="' + POSTER + '" width="250">\n\n<img src="' + LOGO, 1)
        result = attach_posters(legacy, [POSTER])
        self.assertLess(result.index('**S08E03_Exact title**'), result.index('## Poster'))
        self.assertLess(result.index('**Venue:**'), result.index('## Poster'))
        self.assertEqual(result.count('<img src="' + POSTER + '"'), 1)
        self.assertIn('<img src="' + POSTER + '" width="250">', result)
        self.assertEqual(result.split('## Matches')[1], PAGE.split('## Matches')[1])

    def test_distinct_existing_part_artwork_and_escaped_links_survive(self):
        other = 'https://github.com/example/repo/releases/download/images/day2_poster.jpg'
        page = PAGE.replace('<video', '<img src="' + other + '" width="250">\n\n<video', 1)
        result = attach_posters(page, [POSTER, other])
        self.assertIn('<img src="' + other + '" width="250">', result)
        self.assertEqual(result.count('<img src="' + other + '"'), 1)
        self.assertIn('[[Wrestler/Megumi Kudo\\|Megumi Kudo]]', result)
        self.assertEqual(attach_posters(result, [POSTER, other]), result)

    def test_empty_selection_and_missing_identity_metadata_fail_closed(self):
        with self.assertRaises(ValueError):
            attach_posters(PAGE, [])
        with self.assertRaises(ValueError):
            attach_posters(PAGE.replace('**Venue:** Arena - City', ''), [POSTER])
        with self.assertRaises(ValueError):
            attach_posters(PAGE.replace('## Matches', '## Other'), [POSTER])

    def test_existing_poster_after_video_moves_without_replacing_its_attributes(self):
        original_tag = '<img src="' + POSTER + '" width="250" class="part-two">'
        page = PAGE.replace('## Matches', original_tag + '\n\n## Matches')
        result = attach_posters(page, [POSTER])
        self.assertIn(original_tag, result)
        self.assertEqual(result.count(original_tag), 1)
        self.assertLess(result.index(original_tag), result.index('<video'))
        self.assertEqual(result.split('## Matches')[1], PAGE.split('## Matches')[1])

    def test_already_correct_media_keeps_original_blank_lines_exactly(self):
        page = PAGE.replace('image: "' + LOGO + '"', 'image: "' + POSTER + '"').replace('<video', '<img src="' + POSTER + '" width="300">\n\n<video', 1)
        self.assertEqual(attach_posters(page, [POSTER]), page)

if __name__ == '__main__':
    unittest.main()

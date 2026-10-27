"""Guard the reported background pocket without eroding the official crest."""
import hashlib
from pathlib import Path
import unittest
from typing import cast
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

class OfficialLogoTests(unittest.TestCase):
    def test_la_background_gap_is_transparent(self):
        with Image.open(ROOT / 'src/site/img/csw-official-logo.png') as logo:
            self.assertEqual(logo.mode, 'RGBA')
            for xy in [(170, 12), (170, 20), (170, 28), (170, 35)]:
                self.assertLessEqual(cast(int, logo.getchannel('A').getpixel(xy)), 4, f'L/A background remains at {xy}')

    def test_original_colors_and_unaffected_alpha_are_exactly_preserved(self):
        with Image.open(ROOT / 'src/site/img/csw-official-logo.png') as logo, Image.open(ROOT / 'src/site/img/csw-official-logo.jpg') as original:
            self.assertEqual(logo.size, original.size)
            self.assertEqual(logo.convert('RGB').tobytes(), original.convert('RGB').tobytes())
            outside = logo.getchannel('A')
            outside.paste(0, (163, 6, 180, 40))
            self.assertEqual(hashlib.sha256(outside.tobytes()).hexdigest(), 'f793f67ff7be32ba2b475c260dfe4fb1feb5d793d9fc792aebf6441c893b3617')
            # Letter faces, black vertical outlines and the bottom bridge of the gap.
            for xy in [(158,20), (160,30), (164,20), (175,20), (180,20), (186,40), (164,38), (168,39)]:
                self.assertEqual(logo.getchannel('A').getpixel(xy), 255, f'Letter/outline damaged at {xy}')

if __name__ == '__main__':
    unittest.main()

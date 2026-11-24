"""Match-type wikilink regression: stipulation/match types must stay plain text.

Only Championship/Title/Belt names are linked. Stipulation/match types such as
"Royal Rumble", "Steel Cage" or "Hell in a Cell" are not wiki pages and must not
become [[...]] links (they otherwise resolve to dead/404 wikilinks).
"""
import importlib.util
from pathlib import Path
import os
import unittest

SCRIPTS = Path(os.environ.get(
    'CSW_RESULTS_SCRIPTS',
    Path(__file__).resolve().parents[1] / 'scripts/result_pipeline',
))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


manager = load('choke_slam_manager')


class MatchTypeLinkingTests(unittest.TestCase):
    def link(self, text, participants=''):
        return manager.enhanced_smart_link(text, participants)

    def assert_plain(self, text, participants=''):
        result = self.link(text, participants)
        self.assertNotIn('[[', result)
        self.assertNotIn(']]', result)
        self.assertEqual(result, text)

    def test_rumble_is_not_linked(self):
        self.assert_plain('Royal Rumble')

    def test_steel_cage_is_not_linked(self):
        self.assert_plain('Steel Cage')

    def test_other_stipulations_are_not_linked(self):
        for t in ['Hell in a Cell', 'Ladder', 'Tables', 'Iron Man',
                  'Battle Royal', 'Extreme Rules', 'No DQ', 'Street Fight']:
            self.assert_plain(t)

    def test_championships_are_linked(self):
        self.assertEqual(
            self.link('Choke Slam World Championship'),
            '[[Choke Slam World Championship]]',
        )
        self.assertEqual(
            self.link('Choke Slam Trios Championship'),
            '[[Choke Slam Trios Championship]]',
        )

    def test_match_type_plain_even_with_participants(self):
        result = self.link('John Cena Royal Rumble', 'John Cena')
        self.assertNotIn('[[Royal Rumble]]', result)
        # Participants are still enriched into wrestler links.
        self.assertIn('[[Wrestler/John Cena\\|John Cena]]', result)


if __name__ == '__main__':
    unittest.main()

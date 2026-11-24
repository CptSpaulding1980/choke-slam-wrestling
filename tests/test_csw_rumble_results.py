"""Real installed importer and PWI regression: external Rumble roster slots are stale."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import pandas as pd

import os
SCRIPTS = Path(os.environ.get('CSW_RESULTS_SCRIPTS', Path(__file__).resolve().parents[1] / 'scripts/result_pipeline'))
def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
manager = load('choke_slam_manager')
pwi = load('chokeslam_pwi500')

class RumbleResultsTests(unittest.TestCase):
    def export(self, rumble=True, winner='John Cena', loser='29 other wrestlers'):
        cards = ET.fromstring('''<Cards><Card><Name>S08E04_Test</Name><Status>Finished</Status><Date>11/23/2026</Date><Matches><Match><Name>Test</Name><RoyalRumble>false</RoyalRumble><WinnerString/><LoserString/><FinishString>John Cena won.</FinishString><WrestlerInfo><Slot>1</Slot><Name>Roderick Strong</Name></WrestlerInfo><WrestlerInfo><Slot>2</Slot><Name>Kenta Kobashi</Name></WrestlerInfo><Winners><int>1</int></Winners><Losers><int>2</int></Losers></Match></Matches></Card></Cards>''')
        match = cards.find('.//Match')
        match.find('RoyalRumble').text = str(rumble).lower()
        match.find('WinnerString').text = winner
        match.find('LoserString').text = loser
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp)/'source.xml', Path(tmp)/'out.xlsx'
            source.write_bytes(ET.tostring(cards))
            before = source.read_bytes()
            with patch.object(manager, 'PFAD_XML_SOURCE', str(source)), patch.object(manager, 'PFAD_EXCEL_OUTPUT', str(output)), patch('shutil.copy2'):
                self.assertTrue(manager.part1_xml_to_excel())
            self.assertEqual(source.read_bytes(), before)
            return pd.read_excel(output).fillna('')

    def test_authoritative_rumble_winner_without_invented_losers(self):
        df = self.export()
        self.assertEqual(df.iloc[0]['Winner'], 'John Cena')
        self.assertEqual(df.iloc[0]['Loser'], '')
        self.assertEqual(df.iloc[0]['Teilnehmer'], 'John Cena')
        stats, _ = pwi.compute_stats(df)
        self.assertEqual(set(stats), {'John Cena'})
        self.assertEqual(stats['John Cena']['wins'], 1)

    def test_normal_team_labels_keep_structural_members(self):
        df = self.export(False, 'Team A', 'Team B')
        self.assertEqual(df.iloc[0]['Winner'], 'Roderick Strong')
        self.assertEqual(df.iloc[0]['Loser'], 'Kenta Kobashi')

    def test_missing_rumble_winner_fails_closed_not_stale_slot(self):
        df = self.export(winner='')
        self.assertEqual(df.iloc[0]['Winner'], '')
        self.assertEqual(df.iloc[0]['Loser'], '')
        self.assertEqual(df.iloc[0]['Teilnehmer'], '')

    def test_rumble_winner_alias_is_canonical(self):
        self.assertEqual(self.export(winner=' Vader ').iloc[0]['Winner'], 'Big Van Vader')

    def test_known_named_rumble_losers_are_retained(self):
        df = self.export(loser='Opponent A & Opponent B')
        self.assertEqual(df.iloc[0]['Loser'], 'Opponent A, Opponent B')
        self.assertEqual(df.iloc[0]['Teilnehmer'], 'John Cena, Opponent A, Opponent B')

if __name__ == '__main__':
    unittest.main()

import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("profiles", Path(__file__).resolve().parents[1] / "scripts/csw_wrestler_profiles.py")
profiles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profiles)


class ParsingTest(unittest.TestCase):
    def test_metric_units(self):
        self.assertEqual(profiles.metric("6 ft 1 in (1.85 m)", "m"), "1,85 m (6 ft 1 in)")
        self.assertEqual(profiles.metric("234 lbs (106 kg)", "kg"), "106 kg (234 lbs)")
        self.assertEqual(profiles.metric("275 lbs", "kg"), "125 kg (275 lbs)")

    def test_current_finishers_first_and_cleaned(self):
        text = ("==In wrestling==\n*'''Finishing moves'''\n**Bridging [[Suplex#German suplex|German suplex]] (2004–2011)\n"
                "**[[Ripcord lariat|Rainmaker]] (2012–present)\n**The Accolade (Camel clutch\n\n*'''Signature moves'''\n**DDT\n")
        self.assertEqual(profiles.finishers(text), "Rainmaker, Bridging German suplex")

    def test_colon_bullets(self):
        text = "*'''Finishing moves'''\n:*[[Running leg drop|Leg drop]]\n:*[[Crooked arm lariat|Axe Bomber]]\n\n*'''Nicknames'''\n"
        self.assertEqual(profiles.finishers(text), "Leg drop, Axe Bomber")

    def test_gimmick_groups_prefer_matching_name(self):
        text = ("*'''Finishers '''\n**'''As Bayley'''\n*** [[Suplex|Bayley to Belly]]\n***[[Diving elbow drop]]\n"
                "***Scissored armbar – 2015\n**'''As Davina Rose'''\n***[[Headlock Driver|Rose Plant]]\n\n*'''Signature moves'''\n**DDT\n")
        self.assertEqual(profiles.finishers(text, "Bayley"), "Bayley to Belly, Diving elbow drop")
        self.assertEqual(profiles.finishers(text, "Davina Rose"), "Rose Plant")

    def test_infobox_fields(self):
        box = profiles.infobox("{{Infobox Wrestler\n|name = X\n|height = 6 ft (1.83 m)\n|weight = {{nowrap|220 lbs (100 kg)}}\n}}\nText")
        self.assertEqual(box["height"], "6 ft (1.83 m)")
        self.assertEqual(profiles.metric(box["weight"], "kg"), "100 kg (220 lbs)")


if __name__ == "__main__":
    unittest.main()

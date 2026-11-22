import unittest
from face_model import read_face, state, visible

class ChargingTests(unittest.TestCase):
    def test_coffee_and_charging_scene_are_mutually_exclusive(self):
        face = read_face()
        for charging in (False, True):
            for ambient in (False, True):
                nodes = visible(face, state(charging=charging), ambient)
                self.assertEqual(any(n.tag == 'Image' and n.get('resource') == 'coffee' for n in nodes), not charging)
                self.assertEqual(any(n.tag == 'Compare' and n.get('expression') == 'charging' for n in nodes), charging)

    def test_exactly_one_charging_status_at_boundaries(self):
        face = read_face()
        for battery in (0, 49, 50, 54, 55, 89, 90, 94, 95, 99, 100):
            for second in range(120):
                nodes = visible(face, state(second, True, battery))
                labels = [n for n in nodes if n.tag == 'PartText' and n.get('y') == '245']
                self.assertEqual(len(labels), 1, (battery, second))
                if battery == 100:
                    self.assertIn('Fully charged.', ''.join(labels[0].itertext()))

    def test_recharge_bar_tracks_real_battery(self):
        for battery in range(101):
            nodes = visible(read_face(), state(charging=True, battery=battery))
            bars = [n for n in nodes if n.tag == 'PartDraw' and n.get('y') == '406']
            self.assertEqual(len(bars), battery // 5)

    def test_motion_stops_in_ambient_and_spark_stops_at_full(self):
        for second in range(60):
            for battery in (65, 100):
                nodes = visible(read_face(), state(second, True, battery), ambient=True)
                self.assertFalse(any(n.get('name') == 'charging_motion' for n in nodes))
            nodes = visible(read_face(), state(second, True, 100))
            self.assertFalse(any(n.tag == 'Compare' and n.get('expression', '').startswith('spark_') for n in nodes))

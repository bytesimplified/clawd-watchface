import unittest
from face_model import RES, read_face, state, visible

class FaceTests(unittest.TestCase):
    def test_asset_references_resolve(self):
        for node in read_face().iter():
            if node.tag == 'Image':
                self.assertTrue((RES / 'drawable' / (node.get('resource') + '.png')).is_file())
            if node.tag == 'Font':
                self.assertTrue((RES / 'font' / (node.get('family') + '.ttf')).is_file())

    def test_pose_and_word_cadence_across_minute_boundary(self):
        face = read_face()
        for second in range(120):
            nodes = visible(face, state(second))
            poses = [n.get('resource') for n in nodes if n.tag == 'Image' and n.get('resource', '').startswith('pose_')]
            self.assertEqual(poses, ['pose_' + str(second % 20)])
            words = [n.get('expression') for n in nodes if n.tag == 'Compare' and n.get('expression', '').startswith('v')]
            self.assertEqual(words, ['v' + str(second // 5 % 20)])

    def test_ambient_has_one_static_pose(self):
        for second in (0, 1, 7, 19, 59):
            nodes = visible(read_face(), state(second), ambient=True)
            poses = [n.get('resource') for n in nodes if n.tag == 'Image' and n.get('resource', '').startswith('pose_')]
            self.assertEqual(poses, ['pose_0'])

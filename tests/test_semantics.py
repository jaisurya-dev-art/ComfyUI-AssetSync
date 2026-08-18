import unittest

from assetsync.adapters.common import semantic_from_name


class SemanticTests(unittest.TestCase):
    def test_short_normal_alias_does_not_match_arbitrary_name(self):
        self.assertEqual(semantic_from_name("wooden.png"), "unknown")
        self.assertEqual(semantic_from_name("Robot_N.png"), "normal")

    def test_common_pbr_names(self):
        self.assertEqual(semantic_from_name("Robot_BaseColor.png"), "base_color")
        self.assertEqual(semantic_from_name("Robot_Metalness.jpg"), "metallic")
        self.assertEqual(semantic_from_name("Robot_AO.png"), "ao")


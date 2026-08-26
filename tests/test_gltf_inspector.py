import json
import tempfile
import unittest
from pathlib import Path

from assetsync.conversion.gltf_inspector import inspect_gltf


class GltfInspectorTests(unittest.TestCase):
    def test_reports_skeleton_animation_duration_and_channels(self):
        document = {
            "asset": {"version": "2.0"},
            "accessors": [{"type": "SCALAR", "min": [0.25], "max": [1.75]}],
            "animations": [{
                "name": "Walk",
                "samplers": [{"input": 0, "output": 1}],
                "channels": [
                    {"sampler": 0, "target": {"node": 0, "path": "translation"}},
                    {"sampler": 0, "target": {"node": 0, "path": "rotation"}},
                ],
            }],
            "skins": [{"joints": [0]}],
            "materials": [{"doubleSided": True}],
        }
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "animated.gltf"
            path.write_text(json.dumps(document), encoding="utf-8")
            result = inspect_gltf(path)
        self.assertTrue(result["has_animation"])
        self.assertTrue(result["has_skeleton"])
        self.assertTrue(result["double_sided"])
        self.assertEqual(result["animation_clips"][0]["name"], "Walk")
        self.assertEqual(result["animation_clips"][0]["duration_seconds"], 1.5)
        self.assertEqual(result["animation_clips"][0]["target_paths"], ["rotation", "translation"])


if __name__ == "__main__":
    unittest.main()

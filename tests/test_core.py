import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from assetsync.core.asset_descriptor import AssetDescriptor
from assetsync.core.capabilities import conversion_target, get_destination
from assetsync.core.errors import ValidationError
from assetsync.core.normalization import normalize_asset
from assetsync.core.protocol import ImportOptions, import_request, validate_request
from assetsync.core.validation import validate_asset


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "Röbot asset.glb"
        self.path.write_bytes(b"glTF-test")

    def tearDown(self):
        self.temp.cleanup()

    def test_normalizes_common_mapping(self):
        asset = normalize_asset({"result": {"glb_path": str(self.path)}}, name="Robot", asset_id="stable")
        self.assertEqual(asset.asset_id, "stable")
        self.assertEqual(asset.mesh_format, "glb")
        self.assertEqual(asset.name, "Robot")

    def test_normalizes_comfyui_annotated_file(self):
        fake = type("FolderPaths", (), {
            "get_output_directory": staticmethod(lambda: self.temp.name),
            "get_temp_directory": staticmethod(lambda: self.temp.name),
            "get_input_directory": staticmethod(lambda: self.temp.name),
        })
        import sys
        with patch.dict(sys.modules, {"folder_paths": fake}):
            asset = normalize_asset({"filename": self.path.name, "subfolder": "", "type": "output"})
        self.assertEqual(Path(asset.mesh_path), self.path)

    def test_validation_accepts_unicode_and_spaces(self):
        asset = AssetDescriptor.from_path(self.path)
        validate_asset(asset)
        self.assertTrue(Path(asset.mesh_path).is_absolute())

    def test_validation_rejects_empty(self):
        empty = Path(self.temp.name) / "empty.obj"
        empty.touch()
        with self.assertRaises(ValidationError):
            validate_asset(AssetDescriptor.from_path(empty))

    def test_capability_conversion(self):
        self.assertIsNone(conversion_target("glb", get_destination("Blender")))
        self.assertEqual(conversion_target("glb", get_destination("Maya")), "fbx")
        with self.assertRaises(ValidationError):
            conversion_target("obj", get_destination("Unreal Engine"))

    def test_protocol_round_trip(self):
        options = ImportOptions(True, True, True, True, True, "Walk")
        payload = import_request(AssetDescriptor.from_path(self.path, asset_id="id"), "blender", options)
        validate_request(json.loads(json.dumps(payload)))
        self.assertEqual(payload["asset"]["id"], "id")
        self.assertEqual(payload["version"], 2)
        self.assertTrue(payload["options"]["motion_only"])
        self.assertEqual(payload["options"]["animation_clip"], "Walk")

    def test_resolved_asset_preserves_original_format(self):
        asset = AssetDescriptor.from_path(self.path, asset_id="id")
        resolved = asset.with_resolved_mesh("converted.fbx", "fbx", [], {"double_sided": True})
        self.assertEqual(resolved.metadata["original_format"], "glb")
        self.assertEqual(resolved.metadata["conversion_target_format"], "fbx")
        self.assertTrue(resolved.metadata["double_sided"])


if __name__ == "__main__":
    unittest.main()

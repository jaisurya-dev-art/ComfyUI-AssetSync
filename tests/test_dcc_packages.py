import json
import unittest
import zipfile
from pathlib import Path


class DccPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]

    def test_blender_addon_is_installable_zip(self):
        archive_path = self.root / "BlenderAssetSync.zip"
        self.assertTrue(archive_path.is_file(), "Run packaging/build_dcc_packages.ps1")
        with zipfile.ZipFile(archive_path) as archive:
            names = set(archive.namelist())
        normalized = {name.replace("\\", "/") for name in names}
        self.assertIn("BlenderAssetSync/__init__.py", normalized)
        self.assertIn("BlenderAssetSync/assetsync/adapters/blender/receiver.py", normalized)
        self.assertFalse(any("__pycache__" in name or name.endswith(".pyc") for name in normalized))

    def test_unreal_plugin_has_auto_start_and_dependencies(self):
        plugin = self.root / "UnrealAssetSync"
        manifest = json.loads((plugin / "UnrealAssetSync.uplugin").read_text(encoding="utf-8"))
        dependencies = {item["Name"] for item in manifest["Plugins"]}
        self.assertIn("PythonScriptPlugin", dependencies)
        self.assertIn("InterchangeEditor", dependencies)
        self.assertTrue((plugin / "Content" / "Python" / "init_unreal.py").is_file())
        self.assertTrue((plugin / "assetsync" / "adapters" / "unreal" / "receiver.py").is_file())

    def test_maya_has_double_click_installer_and_plugin_loader(self):
        self.assertTrue((self.root / "maya_assetsync_setup.bat").is_file())
        self.assertTrue((self.root / "dcc" / "maya" / "MayaAssetSync_plugin.py").is_file())
        installer = (self.root / "dcc" / "maya" / "install_maya_plugin.bat").read_text(encoding="utf-8")
        self.assertIn("Auto load", installer)
        self.assertIn("18952", installer)


if __name__ == "__main__":
    unittest.main()

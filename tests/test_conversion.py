import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from assetsync.conversion.blender_converter import discover_blender, source_fingerprint


class ConversionTests(unittest.TestCase):
    def test_configured_blender_has_priority(self):
        with tempfile.TemporaryDirectory() as folder:
            executable = Path(folder) / "blender.exe"
            executable.write_bytes(b"fake")
            self.assertEqual(discover_blender(str(executable)), executable.resolve())

    def test_fingerprint_changes_with_content(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "asset.glb"
            source.write_bytes(b"one")
            first = source_fingerprint(source)
            source.write_bytes(b"two")
            second = source_fingerprint(source)
            self.assertNotEqual(first["source_hash"], second["source_hash"])


if __name__ == "__main__":
    unittest.main()

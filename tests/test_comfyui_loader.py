import importlib.util
import os
import sys
import unittest
from pathlib import Path


class ComfyUILoaderTests(unittest.TestCase):
    def test_loads_as_isolated_custom_node_package(self):
        root = Path(__file__).resolve().parents[1]
        module_name = "ComfyUI_AssetSync_test"
        spec = importlib.util.spec_from_file_location(
            module_name, root / "__init__.py", submodule_search_locations=[str(root)]
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
            self.assertIn("AssetSync", module.NODE_CLASS_MAPPINGS)
            self.assertIn("MotionSync", module.NODE_CLASS_MAPPINGS)
            self.assertEqual(module.NODE_DISPLAY_NAME_MAPPINGS["AssetSync"], "AssetSync")
            self.assertEqual(module.NODE_DISPLAY_NAME_MAPPINGS["MotionSync"], "MotionSync to Maya")
        finally:
            for name in list(sys.modules):
                if name == module_name or name.startswith(module_name + "."):
                    sys.modules.pop(name, None)


if __name__ == "__main__":
    unittest.main()

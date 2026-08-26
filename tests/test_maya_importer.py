import unittest
from unittest.mock import Mock

from assetsync.adapters.maya.importer import _enable_double_sided_viewport, _take_index


class MayaImporterTests(unittest.TestCase):
    def test_double_sided_asset_enables_shape_and_viewport_lighting(self):
        cmds = Mock()
        cmds.getPanel.return_value = ["modelPanel1", "modelPanel4"]

        _enable_double_sided_viewport(cmds, ["|asset|shape"])

        cmds.setAttr.assert_any_call("|asset|shape.doubleSided", True)
        cmds.setAttr.assert_any_call("|asset|shape.opposite", False)
        cmds.modelEditor.assert_any_call("modelPanel1", edit=True, twoSidedLighting=True)
        cmds.modelEditor.assert_any_call("modelPanel4", edit=True, twoSidedLighting=True)

    def test_take_selection_accepts_full_or_short_fbx_name(self):
        takes = ["Rig|Idle", "Rig|Walk"]
        self.assertEqual(_take_index(takes, ""), 1)
        self.assertEqual(_take_index(takes, "Rig|Walk"), 2)
        self.assertEqual(_take_index(takes, "walk"), 2)
        with self.assertRaises(RuntimeError):
            _take_index(takes, "Run")


if __name__ == "__main__":
    unittest.main()

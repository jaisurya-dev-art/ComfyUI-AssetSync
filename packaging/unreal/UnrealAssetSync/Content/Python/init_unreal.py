"""Automatically start AssetSync when Unreal Editor loads this plugin."""

import sys
from pathlib import Path

PLUGIN_PARENT = Path(__file__).resolve().parents[3]
if str(PLUGIN_PARENT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_PARENT))

import UnrealAssetSync

UnrealAssetSync.startup()


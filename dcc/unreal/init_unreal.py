"""Unreal Editor startup script for the AssetSync receiver."""

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(os.environ.get("ASSETSYNC_ROOT", Path(__file__).resolve().parents[2])).resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from assetsync.adapters.unreal import receiver


server = receiver.start(18953)
print("AssetSync Receiver - Status: Running - Port: {0}".format(server.port))

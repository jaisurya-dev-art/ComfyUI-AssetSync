"""Run this file from Maya's Script Editor or place its call in userSetup.py."""

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(os.environ.get("ASSETSYNC_ROOT", Path(__file__).resolve().parents[2])).resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from assetsync.adapters.maya import receiver


def start(port=18952):
    server = receiver.start(port)
    print("AssetSync Receiver - Status: Running - Port: {0}".format(server.port))
    return server


if __name__ == "__main__":
    start()

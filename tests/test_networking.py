import unittest

from assetsync.core.networking import AssetSyncClient, ReceiverServer


class NetworkingTests(unittest.TestCase):
    def test_local_json_round_trip_and_status(self):
        server = ReceiverServer(lambda payload: {"success": True, "message": payload["hello"]}, 0).start()
        try:
            result = AssetSyncClient(timeout=2).send(server.port, {"hello": "world"})
            self.assertEqual(result["message"], "world")
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()


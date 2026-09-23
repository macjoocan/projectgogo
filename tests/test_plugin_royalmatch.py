import unittest

from levelscope.plugins import royalmatch


class RoyalMatchPluginTests(unittest.TestCase):
    def test_version_38174_bathtub_tiles_are_named(self):
        self.assertEqual(royalmatch.tile_name(401), "BathtubL")
        self.assertEqual(royalmatch.tile_name(402), "BathtubR")
        self.assertTrue(royalmatch.is_gimmick(401))
        self.assertTrue(royalmatch.is_gimmick(402))


if __name__ == "__main__":
    unittest.main()

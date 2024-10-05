import os
import unittest

from beets import util

from test.helper import MUSLY_AVAILABLE, PluginTest


class TestJukeboxCommand(PluginTest):
    def setUp(self):
        self.setup_beets()

    def tearDown(self):
        self.teardown_beets()

    @unittest.skipIf(not MUSLY_AVAILABLE, "libmusly not available")
    def test_analyze(self):
        self.config.set({
            "beetmatch": {
                "auto": True,
                "jukeboxes": [{
                    "name": "test",
                    "query": ""
                }]
            }
        })

        item = self.add_item_fixture()
        self.run_command("beetmatch-jukebox", "-w")

        item.load()
        self.assertIsNotNone(item["musly_track"])
        self.assertEqual(item["musly_method"], "timbre")

    @unittest.skipIf(not MUSLY_AVAILABLE, "libmusly not available")
    def test_update(self):
        self.config.set({
            "beetmatch": {
                "musly": {
                    "data_dir": "musly_data"
                },
                "jukeboxes": [{
                    "name": "test",
                    "query": ""
                }]
            }
        })

        item = self.add_item_fixture()

        self.run_command("beetmatch-jukebox", "-w", "-u")

        jukebox_file = os.path.join(
            self.beets_dir,
            util.bytestring_path("musly_data"),
            util.bytestring_path("test.jukebox")
        )

        self.assertTrue(os.path.exists(jukebox_file))


# class AutoImportTest(unittest.TestCase, TestHelper):
#     def setUp(self):
#         self.setup_beets(disk=True)
#         self.config.set({
#             "beetmatch": {
#                 "auto": True,
#
#                 "musly": {
#                     "enabled": True
#                 }
#             },
#         })
#
#         try:
#             self.load_plugins("beetmatch")
#         except:
#             self.tearDown()
#
#         self.importer = self.create_importer()
#
#     def tearDown(self):
#         self.unload_plugins()
#         self.teardown_beets()
#
#     @unittest.skipIf(not MUSLY_AVAILABLE, "libmusly not available")
#     def test_import_analyzed(self):
#         self.importer.run()
#         for item in self.lib.items():
#             self.assertIsNotNone(item.musly_track)
#             self.assertIsNotNone(item.musly_method)
#

if __name__ == '__main__':
    unittest.main()

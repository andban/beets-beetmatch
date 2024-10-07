import os

import pytest
from beets import util

from tests.helper import MUSLY_AVAILABLE, PluginTest


class TestJukeboxCommand(PluginTest):

    @pytest.fixture(autouse=True, name="lib")
    def fixture_lib(self):
        self.setup_beets()
        yield self.lib
        self.teardown_beets()

    @pytest.mark.skipif(not MUSLY_AVAILABLE, reason="libmusly not available")
    def test_analyze(self):
        self.config.set(
            {"beetmatch": {"auto": True, "jukeboxes": [{"name": "test", "query": ""}]}}
        )

        item = self.add_item_fixture()
        self.run_command("beetmatch-jukebox", "-w")

        item.load()
        assert item["musly_track"] is not None
        assert item["musly_method"] == "timbre"

    @pytest.mark.skipif(not MUSLY_AVAILABLE, reason="libmusly not available")
    def test_update(self):
        self.config.set(
            {
                "beetmatch": {
                    "musly": {"data_dir": "musly_data"},
                    "jukeboxes": [{"name": "test", "query": ""}],
                }
            }
        )

        self.add_item_fixture()

        self.run_command("beetmatch-jukebox", "-w", "-u")

        jukebox_file = os.path.join(
            self.beets_dir,
            util.bytestring_path("musly_data"),
            util.bytestring_path("test.jukebox"),
        )

        assert os.path.exists(jukebox_file)

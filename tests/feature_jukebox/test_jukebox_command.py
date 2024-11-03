import os

import pytest
from beets import util
from beets.util import bytestring_path

from tests.helper import MUSLY_AVAILABLE, PluginTest, FIXTURE_DIR


class TestJukeboxCommand(PluginTest):
    @pytest.fixture(autouse=True, name="lib")
    def fixture_lib(self):
        self.setup_beets()
        yield self.lib
        self.teardown_beets()

    @pytest.mark.skipif(not MUSLY_AVAILABLE, reason="libmusly not available")
    def test_analyze(self):
        self.config.set({"beetmatch": {"auto": True}})

        item = self.add_item_fixture()
        self.run_command("beetmatch-musly", "-w")

        item.load()
        assert item["musly_track"] is not None
        assert item["musly_method"] == "timbre"

    @pytest.mark.skipif(not MUSLY_AVAILABLE, reason="libmusly not available")
    def test_update(self):
        self.config.set({"beetmatch": {"musly": {"data_dir": "musly_data"}}})

        self.add_item_fixture()
        self.add_item_fixture(
            path=os.path.join(FIXTURE_DIR, bytestring_path("sample-12s.mp3"))
        )
        self.add_item_fixture(
            path=os.path.join(FIXTURE_DIR, bytestring_path("sample-15s.mp3"))
        )
        self.add_item_fixture(
            path=os.path.join(FIXTURE_DIR, bytestring_path("full.mp3"))
        )

        self.run_command("beetmatch-musly", "-w", "-u", "all")

        jukebox_file = os.path.join(
            self.beets_dir,
            util.bytestring_path("musly_data"),
            util.bytestring_path("all.jukebox"),
        )

        assert os.path.exists(jukebox_file)

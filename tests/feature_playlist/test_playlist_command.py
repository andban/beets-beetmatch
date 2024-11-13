import os.path
import stat
import sys

import pytest
from beets.util import bytestring_path

from tests.helper import PluginTest, FIXTURE_DIR
from tests.io_helper import control_stdin


class TestJukeboxCommand(PluginTest):
    @pytest.fixture(autouse=True, name="lib")
    def fixture_lib(self):
        self.setup_beets()
        yield self.lib
        self.teardown_beets()

    def test_playlist_with_distinct_seed_query(self, lib):
        self.config.set(
            {
                "beetmatch": {
                    "jukeboxes": [
                        {
                            "name": "test_jukebox",
                            "query": "",
                        }
                    ],
                    "playlist": {
                        "cooldown": {"artist": 0, "album": 0},
                        "attributes": {"genre": {"type": "ListDistance", "weight": 1}},
                    },
                }
            }
        )

        self.add_item(genre=["Electronic"], title="Seed Track")
        self.add_item(genre=["Rock"])
        self.add_item(genre=["Electronic", "Rock"])

        self.run_command(
            "beetmatch-generate",
            "-j",
            "test_jukebox",
            "-t",
            "3",
            "title:'Seed Track'",
        )

    def test_playlist_with_not_distinct_seed_query(self):
        self.config.set(
            {
                "beetmatch": {
                    "jukeboxes": [
                        {
                            "name": "test_jukebox",
                            "query": "",
                        }
                    ],
                    "playlist": {
                        "cooldown": {"artist": 0, "album": 0},
                        "attributes": {"genre": {"type": "ListDistance", "weight": 1}},
                    },
                }
            }
        )

        self.add_item(genre=["Electronic"], title="Seed Track")
        self.add_item(genre=["Rock"])
        self.add_item(genre=["Electronic", "Rock"])

        with control_stdin("1\n"):
            self.run_command(
                "beetmatch-generate",
                "-j",
                "test_jukebox",
                "-t",
                "3",
                "artist:'The Artist'",
            )

    def test_playlist_with_random_seed(self):
        self.config.set(
            {
                "beetmatch": {
                    "jukeboxes": [
                        {
                            "name": "test_jukebox",
                            "query": "",
                        }
                    ],
                    "playlist": {
                        "cooldown": {"artist": 1, "album": 0},
                        "attributes": {"genre": {"type": "ListDistance", "weight": 1}},
                    },
                }
            }
        )

        self.add_item(genre=["Electronic"], title="Seed Track")
        self.add_item(genre=["Rock"])
        self.add_item(genre=["Electronic", "Rock"])

        self.run_command("beetmatch-generate", "-j", "test_jukebox", "-t", "3")

    @pytest.mark.skipif(sys.platform == "win32", reason="win32")
    def test_execute_default_script(self):
        script_path = os.path.join(self.beets_dir, b"playlist-script.sh")
        with open(script_path, "w") as fh:
            fh.write(f"#!/bin/sh\ntouch ${self.beets_dir}/$1.m3u")
        os.chmod(script_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

        self.config.set(
            {
                "beetmatch": {
                    "jukeboxes": [
                        {
                            "name": "test_jukebox",
                            "query": "",
                        }
                    ],
                    "playlist": {
                        "default_script": "playlist-script.sh",
                        "cooldown": {"artist": 0, "album": 0},
                        "attributes": {"genre": {"type": "ListDistance", "weight": 1}},
                    },
                }
            }
        )

        self.add_item(
            genre=["Electronic"],
            title="Seed Track",
            path=os.path.join(FIXTURE_DIR, bytestring_path("sample-12s.mp3")),
        )
        self.add_item(
            genre=["Rock"],
            path=os.path.join(FIXTURE_DIR, bytestring_path("sample-15s.mp3")),
        )
        self.add_item(genre=["Electronic", "Rock"])

        self.run_command("beetmatch-generate", "-j", "test_jukebox", "-t", "3")

        assert (
            os.path.exists(
                os.fsdecode(os.path.join(self.beets_dir, b"test_jukebox.m3u"))
            )
            is True
        )

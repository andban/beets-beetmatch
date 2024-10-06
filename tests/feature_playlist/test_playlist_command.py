from tests.helper import PluginTest
from tests.io_helper import control_stdin


class TestJukeboxCommand(PluginTest):

    def setUp(self):
        self.setup_beets()

    def tearDown(self):
        self.teardown_beets()

    def test_playlist_with_distinct_seed_query(self):
        self.config.set({
            "beetmatch": {
                "jukeboxes": [
                    {
                        "name": "test_jukebox",
                        "query": "",
                    }
                ],
                "playlist": {
                    "cooldown": {
                        "artist": 0,
                        "album": 0
                    },
                    "attributes": {
                        "genre": {
                            "type": "ListDistance",
                            "weight": 1
                        }
                    }
                }
            }
        })

        self.add_item(genre=["Electronic"], title="Seed Track")
        self.add_item(genre=["Rock"])
        self.add_item(genre=["Electronic", "Rock"])

        self.run_command("beetmatch-generate", "-j", "test_jukebox", "-t", "3", "-q", "title:'Seed Track'")

    def test_playlist_with_not_distinct_seed_query(self):
        self.config.set({
            "beetmatch": {
                "jukeboxes": [
                    {
                        "name": "test_jukebox",
                        "query": "",
                    }
                ],
                "playlist": {
                    "cooldown": {
                        "artist": 0,
                        "album": 0
                    },
                    "attributes": {
                        "genre": {
                            "type": "ListDistance",
                            "weight": 1
                        }
                    }
                }
            }
        })

        self.add_item(genre=["Electronic"], title="Seed Track")
        self.add_item(genre=["Rock"])
        self.add_item(genre=["Electronic", "Rock"])

        with control_stdin("1\n"):
            self.run_command("beetmatch-generate", "-j", "test_jukebox", "-t", "3", "-q", "artist:'The Artist'")

    def test_playlist_with_random_seed(self):
        self.config.set({
            "beetmatch": {
                "jukeboxes": [
                    {
                        "name": "test_jukebox",
                        "query": "",
                    }
                ],
                "playlist": {
                    "cooldown": {
                        "artist": 0,
                        "album": 0
                    },
                    "attributes": {
                        "genre": {
                            "type": "ListDistance",
                            "weight": 1
                        }
                    }
                }
            }
        })

        self.add_item(genre=["Electronic"], title="Seed Track")
        self.add_item(genre=["Rock"])
        self.add_item(genre=["Electronic", "Rock"])

        self.run_command("beetmatch-generate", "-j", "test_jukebox", "-t", "3")

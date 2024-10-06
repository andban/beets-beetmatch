import os
import shutil
import sys
import unittest
from tempfile import mkdtemp
from unittest.mock import patch

import beets
import beets.plugins
import beets.ui
from beets.library import Library, Item, Album
from beets.util import bytestring_path, syspath, arg_encoding, MoveOperation, normpath
from confuse import LazyConfig

from beetsplug.beetmatch.musly import libmusly

MUSLY_AVAILABLE = libmusly.library_present()

_test_dir = bytestring_path(os.path.dirname(__file__))
_fixture_dir = bytestring_path(
    os.path.abspath(
        os.path.join(
            _test_dir,
            b"fixtures"
        )
    )
)


class Assertions:
    pass


class PluginTest(unittest.TestCase, Assertions):
    beets_dir: bytes
    media_dir: bytes

    config: LazyConfig
    lib: Library

    _item_count = 0

    def _get_next_item_number(self):
        count = self._item_count
        self._item_count += 1
        return count

    def setup_beets(self):
        # create temporary BEETSDIR
        self.beets_dir = bytestring_path(mkdtemp())

        self.media_dir = os.path.join(self.beets_dir, b"media")
        os.mkdir(syspath(self.media_dir))

        self._env_patcher = patch.dict(
            "os.environ",
            {
                "BEETSDIR": os.fsdecode(self.beets_dir),
                "HOME": os.fsdecode(self.beets_dir)
            },
        )
        self._env_patcher.start()

        # create initial configuration
        self.config = beets.config
        self.config.sources = []
        self.config.read(user=False, defaults=True)

        self.config["plugins"] = ["beetmatch"]
        self.config["verbose"] = 1
        self.config["ui"]["color"] = False
        self.config["threaded"] = False

        self.config["directory"] = os.fsdecode(self.media_dir)

        dbpath = bytestring_path(self.config["library"].as_filename())
        self.lib = Library(dbpath, self.media_dir)

        beets.plugins.load_plugins(self.config["plugins"].get(list))
        beets.plugins.find_plugins()

        # Take a backup of the original _types and _queries to restore
        # when unloading.
        Item._original_types = dict(Item._types)
        Album._original_types = dict(Album._types)
        Item._types.update(beets.plugins.types(Item))
        Album._types.update(beets.plugins.types(Album))

        Item._original_queries = dict(Item._queries)
        Album._original_queries = dict(Album._queries)
        Item._queries.update(beets.plugins.named_queries(Item))
        Album._queries.update(beets.plugins.named_queries(Album))

    def teardown_beets(self):
        self._env_patcher.stop()
        self.lib._close()
        shutil.rmtree(self.beets_dir)
        beets.config.clear()
        beets.config._materialized = False

        for plugin_class in beets.plugins._instances:
            plugin_class.listeners = None
        beets.config["plugins"] = []
        beets.plugins._classes = set()
        beets.plugins._instances = {}

        Item._types = getattr(Item, "_original_types", {})
        Album._types = getattr(Album, "_original_types", {})
        Item._queries = getattr(Item, "_original_queries", {})
        Album._queries = getattr(Album, "_original_queries", {})

    def run_command(self, *args, **kwargs):
        sys.argv = ["beet"]
        lib = self.lib
        beets.ui._raw_main(_convert_args(list(args)), lib)

    #
    # fixtures
    #
    def create_item(self, **attributes):
        item_count = self._get_next_item_number()
        values = {
            "title": "Song #{0}",
            "artist": "The Artist",
            "album": "An Album of Songs",
            "track": item_count,
            "format": "MP3",
            "length": 123
        }
        values.update(attributes)
        values["title"] = values["title"].format(item_count)
        values["db"] = self.lib
        item = Item(**values)
        if "path" not in values:
            item["path"] = os.path.join(
                _fixture_dir, bytestring_path("dummy-audio." + item["format"].lower())
            )
        item.mtime = 123456
        return item

    def add_item(self, **attributes):
        if "path" in attributes:
            attributes["path"] = normpath(attributes["path"])

        item = self.create_item(**attributes)
        item.add(self.lib)

        if "path" not in attributes:
            item["path"] = item.destination()
            item.store()

        return item

    def add_item_fixture(self, **attributes):
        item = self.create_item(**attributes)
        extension = item["format"].lower()
        item["path"] = os.path.join(
            _fixture_dir, bytestring_path("audio." + extension)
        )
        item.add(self.lib)
        item.move(operation=MoveOperation.COPY)
        item.store()
        return item


def _convert_args(args):
    for i, arg in enumerate(args):
        if isinstance(arg, bytes):
            args[i] = arg.decode(arg_encoding())

    return args

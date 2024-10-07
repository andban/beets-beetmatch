import os
import shutil
import sys
from functools import cached_property
from pathlib import Path
from tempfile import mkdtemp
from typing import Union
from unittest.mock import patch

import beets
import beets.plugins
import beets.ui
from beets.importer import ImportSession
from beets.library import Library, Item, Album
from beets.util import bytestring_path, syspath, arg_encoding, MoveOperation, normpath
from confuse import LazyConfig
from mediafile import MediaFile

from beetsplug.beetmatch.musly import libmusly

MUSLY_AVAILABLE = libmusly.library_present()

_test_dir = bytestring_path(os.path.dirname(__file__))
FIXTURE_DIR = bytestring_path(os.path.abspath(os.path.join(_test_dir, b"fixtures")))


class PluginTest:
    beets_dir: bytes
    media_dir: bytes

    config: LazyConfig
    lib: Library

    _item_count = 0

    def _get_next_item_number(self):
        count = self._item_count
        self._item_count += 1
        return count

    def setup_beets(self, load_plugin=True):
        # create temporary BEETSDIR
        self.beets_dir = bytestring_path(mkdtemp())

        self.media_dir = os.path.join(self.beets_dir, b"media")
        os.mkdir(syspath(self.media_dir))

        self._env_patcher = patch.dict(
            "os.environ",
            {
                "BEETSDIR": os.fsdecode(self.beets_dir),
                "HOME": os.fsdecode(self.beets_dir),
            },
        )
        self._env_patcher.start()

        # create initial configuration
        self.config = beets.config
        self.config.sources = []
        self.config.read(user=False, defaults=True)

        self.config["plugins"] = []
        self.config["verbose"] = 1
        self.config["ui"]["color"] = False
        self.config["threaded"] = False

        self.config["directory"] = os.fsdecode(self.media_dir)

        dbpath = bytestring_path(self.config["library"].as_filename())
        self.lib = Library(dbpath, self.media_dir)

        if load_plugin:
            self.load_plugins()

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

    def load_plugins(self):
        self.config["plugins"] = ["beetmatch"]

        beets.plugins.load_plugins(self.config["plugins"].get(list))
        beets.plugins.find_plugins()

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
            "length": 123,
        }
        values.update(attributes)
        values["title"] = values["title"].format(item_count)
        values["db"] = self.lib
        item = Item(**values)
        if "path" not in values:
            item["path"] = os.path.join(
                FIXTURE_DIR, bytestring_path("dummy-audio." + item["format"].lower())
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
        item["path"] = os.path.join(FIXTURE_DIR, bytestring_path("audio." + extension))
        item.add(self.lib)
        item.move(operation=MoveOperation.COPY)
        item.store()
        return item


def _convert_args(args):
    for i, arg in enumerate(args):
        if isinstance(arg, bytes):
            args[i] = arg.decode(arg_encoding())

    return args


class ImportTest(PluginTest):
    _default_import_config = {
        "autotag": False,
        "copy": True,
        "hardlink": False,
        "link": False,
        "move": False,
        "resume": False,
        "singletons": False,
        "timid": True
    }
    _resource_path = syspath(os.path.join(FIXTURE_DIR, b"sample-12s.mp3"))

    importer: ImportSession

    @cached_property
    def import_path(self) -> Path:
        import_path = Path(os.fsdecode(os.path.join(self.beets_dir, b"import")))
        import_path.mkdir(exist_ok=True)
        return import_path

    @cached_property
    def import_dir(self) -> bytes:
        return bytestring_path(str(self.import_path))

    def setup_import(self):
        self.import_media = []
        self.lib.path_formats = [
            ("default", os.path.join("$artist", "$album", "$title")),
        ]

    def prepare_track_for_import(self,
                                 track_id: int,
                                 album_path: Union[Path, None] = None,
                                 album_id: Union[int, None] = None) -> Path:
        if not album_path:
            album_dir = f"album_{album_id}" if album_id else "album"
            album_path = self.import_path / album_dir

        album_path.mkdir(exist_ok=True)

        track_path = album_path / f"track_{track_id}.mp3"
        shutil.copy(self._resource_path, track_path)

        medium = MediaFile(track_path)
        medium.update({
            "album": "The Album" + (f" {album_id}" if album_id else ""),
            "albumartist": None,
            "mb_albumid": None,
            "comp": None,
            "artist": "The Artist",
            "title": f"Song #{track_id}",
            "track": track_id,
            "mb_trackid": None,
        })
        medium.save()
        self.import_media.append(medium)

        return track_path

    def prepare_importer(self, import_dir: Union[bytes, None] = None, **kwargs) -> ImportSession:
        self.config["import"].set_args({**self._default_import_config, **kwargs})
        self.importer = self._get_import_session(import_dir or self.import_dir)
        return self.importer

    def _get_import_session(self, import_dir: bytes) -> ImportSession:
        return ImportSession(self.lib, loghandler=None, query=None, paths=[import_dir])

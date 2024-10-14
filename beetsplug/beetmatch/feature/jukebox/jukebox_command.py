from base64 import b64encode
from concurrent import futures
from logging import Logger
from optparse import OptionParser

from beets import dbcore
from beets.dbcore import Query
from beets.library import Library, Item
from beets.ui import Subcommand
from confuse import Subview

import beetsplug.beetmatch.musly as musly
from beetsplug.beetmatch.feature.jukebox.jukebox_updater import JukeboxUpdater
from .jukebox_config import JukeboxConfig
from ...common import default_logger
from ...musly import MuslyError


class JukeboxCommand(Subcommand):
    _config: JukeboxConfig

    def __init__(self, config: Subview, log: Logger = default_logger):
        self._config = JukeboxConfig(config)
        self._log = log

        self.parser = OptionParser(usage="%prog")
        self.parser.add_option(
            "-u",
            "--update",
            action="store_true",
            dest="update",
            default=False,
            help="Update jukeboxes with new musly data"
        )
        self.parser.add_option(
            "-w",
            "--write",
            action="store_true",
            dest="write",
            default=False,
            help="Write analysis results to meta data database",
        )
        self.parser.add_option(
            "-f",
            "--force",
            action="store_true",
            dest="force",
            default=False,
            help="[default: {}] force analysis of previously analyzed items".format(
                False
            ),
        )
        self.parser.add_option(
            "-t",
            "--threads",
            type="int",
            dest="threads",
            default=self._config.musly_threads,
            help="[default: {}] number of threads to use for analysis".format(
                self._config.musly_threads
            ),
        )
        super(JukeboxCommand, self).__init__(
            parser=self.parser,
            name="beetmatch-musly",
            aliases=["bmm"],
            help="Analyze tracks and update Musly jukeboxes",
        )

    def func(self, lib: Library, options, arguments):
        if not musly.libmusly.library_present():
            return

        jukebox_names = arguments if len(arguments) else self._config.jukebox_names

        for name in jukebox_names:
            self._analyze_jukebox(
                name=name,
                lib=lib,
                threads=options.threads,
                force=options.force,
                write=options.write,
                update=options.update
            )

    def _update_musly_jukebox(self, name, lib, write=False):
        updater = JukeboxUpdater(lib, self._log)
        jukebox = self._config.get_jukebox(name)

        if not jukebox.musly_jukebox:
            return

        updater.update(jukebox=jukebox.musly_jukebox, query=jukebox.get_query())
        if write:
            jukebox.save_musly_jukebox()

    def _analyze_jukebox(self, name, lib, threads=1, update=False, force=False, write=False):
        jukebox = self._config.get_jukebox(name)

        analysis_jukebox = self._config.get_musly_jukebox()
        items = _find_items_to_analyze(
            lib, analysis_jukebox.method(), query=jukebox.get_query(), force=force
        )
        self._log.info("found %d items to analyze", len(items))

        items_processed = 0
        if len(items) > 0:
            with futures.ThreadPoolExecutor(max_workers=threads) as worker:
                def worker_fn(item):
                    self.analyze_track(item, jukebox=analysis_jukebox, write=write)

                for _ in worker.map(worker_fn, items):
                    items_processed += 1

        if update:
            self._update_musly_jukebox(name, lib, write=write)

        return items_processed

    def analyze_track(self, item: Item, jukebox=None, write=False):
        if not jukebox:
            jukebox = self._config.get_jukebox()
            if not jukebox:
                return

        duration = item.length
        if not duration:
            self._log.warning("Skipping item because it has no duration")
            return

        path = item.get("path").decode("utf-8")
        if not path:
            self._log.warning("Skipping item because its path does not exist (%s)", path)
            return

        try:
            self._log.info("Analyzing item %s...", path)

            excerpt_start = -min(48, int(duration))
            excerpt_length = min(int(duration), 30)

            track = jukebox.track_from_audio_file(path, excerpt_start, excerpt_length)
            track_buffer = jukebox.track_to_buffer(track)

            if write:
                setattr(item, "musly_track", b64encode(track_buffer).decode("ascii"))
                setattr(item, "musly_method", jukebox.method())
                item.store()

        except MuslyError as error:
            self._log.exception("Analyzing item failed: %s", error)


def _find_items_to_analyze(
        lib: Library, required_method: str, query: Query, force=False):
    combined_query = query
    # exclude already analyzed items
    if not force:
        unprocessed_query = dbcore.OrQuery(
            [
                dbcore.query.NoneQuery(
                    "musly_track", fast="musly_track" in Item._fields
                ),
                dbcore.query.NotQuery(
                    dbcore.MatchQuery(
                        "musly_method",
                        required_method,
                        fast="musly_method" in Item._fields,
                    )
                ),
            ]
        )
        combined_query = dbcore.AndQuery([combined_query, unprocessed_query])

    return lib.items(combined_query)

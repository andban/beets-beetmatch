import logging
import string
import subprocess
from optparse import OptionParser, Values
from sys import stderr, stdout

import confuse
from beets import ui
from beets.library import Library
from beets.ui import Subcommand, UserError

from beetsplug.beetmatch.common import select_item_from_list
from .library import select_item_random, select_item_interactive, select_items
from .playlist_config import PlaylistConfig
from .playlist_generator import PlaylistGenerator
from ..jukebox import Jukebox, JukeboxConfig

__logger__ = logging.getLogger("beets.beetmatch")


class PlaylistCommand(Subcommand):
    playlist_config: PlaylistConfig
    jukebox_config: JukeboxConfig

    def __init__(self, config: confuse.Subview):
        self.playlist_config = PlaylistConfig(config)
        self.jukebox_config = JukeboxConfig(config)

        self.parser = OptionParser(usage="%prog")
        self.parser.add_option(
            "-j",
            "--jukebox",
            type="string",
            dest="jukebox_name",
            default="all",
            help="[default: 'all'] Name of the jukebox to generate playlist from"
        )
        self.parser.add_option(
            "-t",
            "--num-tracks",
            type="int",
            dest="numtracks",
            default=None,
            help="Maximum number of tracks",
        )
        self.parser.add_option(
            "-d",
            "--duration",
            type="float",
            dest="duration",
            default=None,
            help="Duration of playlist in minutes (its not a hard limit)",
        )
        self.parser.add_option(
            "-s",
            "--script",
            type="string",
            dest="script",
            default=None,
            help="Call script after playlist was generated",
        )
        self.parser.add_option(
            "-q",
            "--query",
            type="string",
            dest="query",
            default=None,
            help="The first track to base playlist on",
        )

        super(PlaylistCommand, self).__init__(
            parser=self.parser,
            name="beetmatch-generate",
            aliases=["bmg"],
            help="Generate playlist",
        )

    def func(self, lib: Library, options: Values, arguments: list):
        if not options.jukebox_name:
            raise UserError("one jukebox name expected")

        jukebox = self.jukebox_config.get_jukebox(options.jukebox_name)
        if not jukebox:
            raise UserError(
                'no jukebox configuration with the name "%s" found', options.jukebox_name
            )

        if options.query:
            seed_item = select_item_interactive(lib, jukebox.get_query(options.query))
        else:
            seed_item = select_item_random(lib, jukebox.get_query())

        if not seed_item:
            raise UserError("no seed item found")

        items = select_items(lib, jukebox.get_query(f"^id:{seed_item.id}"))

        generator = PlaylistGenerator(
            config=self.playlist_config,
            jukebox=jukebox,
            items=items,
            seed_item=seed_item,
            log=__logger__
        )

        playlist = [seed_item]
        duration = 0
        for item, distance in generator:
            playlist.append(item)
            duration += item.length

            if options.duration and duration >= options.duration:
                break
            if options.numtracks and len(playlist) >= options.numtracks:
                break

        track_fmt = PartialFormatter()

        ui.print_("\nGenerated playlist:")
        for i, item in enumerate(playlist):
            ui.print_(
                track_fmt.format("{idx:>3}. {item.title} - {item.artist} - {item.album}\n"
                                 "     [Year: {item.year}] [BPM: {item.bpm:>3}] [Key: {item.key}/{item.key_scale}]\n"
                                 "     [{item.genre}: {item.style}]",
                                 idx=i + 1, item=item
                                 )
            )

        self.execute_script(
            jukebox.name,
            playlist,
            script_override=options.script,
        )

    def execute_script(self, playlist_name: str, items, script_override: str = None):
        script_path = script_override or self.playlist_config.playlist_script
        if not script_path:
            return

        __logger__.debug(
            "executing script '{script}'...".format(script=script_path))

        try:
            cmd = [script_path, playlist_name]
            cmd.extend([item.path for item in items])
            subprocess.run(cmd, stderr=stderr, stdout=stdout, check=True)
        except subprocess.CalledProcessError as error:
            __logger__.error(
                "Error while running script '%s'", script_path, exc_info=error
            )


def _find_seed_item(
        lib: Library,
        jukebox_config: Jukebox,
        query: str = None,
):
    seed_item_candidates = list(lib.items(jukebox_config.get_query(additional_query=query)))
    if not seed_item_candidates:
        return None

    _, seed_item = select_item_from_list(
        seed_item_candidates,
        pick_random=not query,
        title="The query matched more than one track, please select one:",
    )

    return seed_item


class PartialFormatter(string.Formatter):
    def __init__(self, missing='-', bad_fmt='!!'):
        self.missing, self.bad_fmt = missing, bad_fmt

    def get_field(self, field_name, args, kwargs):
        # Handle a key not found
        try:
            val = super(PartialFormatter, self).get_field(field_name, args, kwargs)
            # Python 3, 'super().get_field(field_name, args, kwargs)' works
        except (KeyError, AttributeError):
            val = None, field_name
        return val

    def format_field(self, value, spec):
        # handle an invalid format
        if value is None:
            return self.missing
        try:
            return super(PartialFormatter, self).format_field(value, spec)
        except ValueError:
            if self.bad_fmt is not None:
                return self.bad_fmt
            else:
                raise

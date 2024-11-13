import logging
import string
from optparse import OptionParser
from typing import List, NamedTuple, Union

import confuse
from beets import ui
from beets.library import Library
from beets.ui import Subcommand, UserError

from beetsplug.beetmatch.common import select_item_from_list
from .library import select_item_interactive, select_items, select_item_random
from .playlist_config import PlaylistConfig
from .playlist_generator import PlaylistGenerator
from .playlist_script import PlaylistScript
from ..jukebox import Jukebox, JukeboxConfig

__logger__ = logging.getLogger("beets.beetmatch")


class PlaylistOptions(NamedTuple):
    jukebox_name: str
    numtracks: Union[int, None]
    duration: Union[float, None]
    script: Union[str, None]


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
            help="[default: 'all'] Name of the jukebox to generate playlist from",
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

        super(PlaylistCommand, self).__init__(
            parser=self.parser,
            name="beetmatch-generate",
            aliases=["bmg"],
            help="Generate playlist",
        )

        self.parser.usage += (
            "\n" "Example: %prog --jukebox=all --duration 60 'artist:Air'"
        )

    def func(self, lib: Library, options: PlaylistOptions, arguments: List[str]):
        if not options.jukebox_name:
            raise UserError("one jukebox name expected")

        if not options.numtracks and not options.duration:
            raise ValueError("expected one of --duration or --num-tracks parameters")

        jukebox = self.jukebox_config.get_jukebox(options.jukebox_name)
        if not jukebox:
            raise UserError(
                'no jukebox configuration with the name "%s" found',
                options.jukebox_name,
            )

        track_selector = self.playlist_config.playlist_selector

        playlist_script_path = options.script or self.playlist_config.playlist_script
        playlist_script = (
            PlaylistScript(playlist_script_path, log=__logger__)
            if playlist_script_path
            else None
        )

        seed_query = " ".join(arguments) if arguments else None
        if seed_query:
            seed_item = select_item_interactive(lib, jukebox.get_query(seed_query))
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
            candidate_chooser=track_selector,
            log=__logger__,
        )

        track_fmt = PartialFormatter()
        playlist = [seed_item]
        duration = 0

        ui.print_(track_fmt.format("\nGenerated playlist:"))
        ui.print_(
            track_fmt.format(
                "{idx:>3}. {item.title} - {item.artist}", idx=1, item=seed_item
            )
        )

        for item, similarity in generator:
            playlist.append(item)
            duration += item.length / 60

            ui.print_(
                track_fmt.format(
                    "{idx:>3}. {item.title} - {item.artist} (similarity: {similarity:.3f})",
                    idx=len(playlist),
                    item=item,
                    similarity=similarity,
                )
            )

            if options.duration and duration >= options.duration:
                break
            if options.numtracks and len(playlist) >= options.numtracks:
                break

        if playlist_script:
            playlist_script.execute(jukebox.name, playlist)


def _find_seed_item(
    lib: Library,
    jukebox_config: Jukebox,
    query: str = None,
):
    seed_item_candidates = list(
        lib.items(jukebox_config.get_query(additional_query=query))
    )
    if not seed_item_candidates:
        return None

    _, seed_item = select_item_from_list(
        seed_item_candidates,
        pick_random=not query,
        title="The query matched more than one track, please select one:",
    )

    return seed_item


class PartialFormatter(string.Formatter):
    def __init__(self, missing="-", bad_fmt="!!"):
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

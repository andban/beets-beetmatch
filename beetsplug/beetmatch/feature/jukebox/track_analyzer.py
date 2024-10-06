from base64 import b64encode
from logging import Logger
from os.path import isfile

from beets.library import Item

from ...common import default_logger
from ...musly import MuslyJukebox, MuslyError


def _check_path(path: str):
    if not isfile(path):
        return None
    return path


def analyze_track(item: Item, jukebox: MuslyJukebox, log: Logger = default_logger):
    duration = item.length
    if not duration:
        log.warning("Skipping item because it has no duration")
        return None, None

    path = item.get("path").decode("utf-8")
    if not path:
        log.warning("Skipping item because its path does not exist (%s)", path)
        return None, None

    try:
        log.info("Analyzing item %s...", path)

        excerpt_start = -min(48, int(duration))
        excerpt_length = min(int(duration), 30)

        track = jukebox.track_from_audio_file(path, excerpt_start, excerpt_length)
        track_buffer = jukebox.track_to_buffer(track)

        return b64encode(track_buffer).decode("ascii"), jukebox.method()

    except MuslyError as error:
        log.exception("Analyzing item failed: %s", error)

    return None, None

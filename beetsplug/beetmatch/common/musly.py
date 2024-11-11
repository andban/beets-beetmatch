from os.path import exists
from typing import TypedDict

from beetsplug.beetmatch.common.helpers import import_optional

_musly = import_optional("pymusly", error=None)

MuslyJukebox = _musly.MuslyJukebox if _musly is not None else None
MuslyError = _musly.MuslyError if _musly is not None else None
MuslyTrack = _musly.MuslyTrack if _musly is not None else None


class MuslyJukeboxConfig(TypedDict):
    method: str
    decoder: str


def is_musly_present():
    return _musly is not None


def set_musly_loglevel(level: int):
    _musly.set_musly_loglevel(level)


def get_musly_methods():
    return _musly.get_musly_methods() if is_musly_present() else []


def get_musly_decoders():
    return _musly.get_musly_decoders() if is_musly_present() else []


def create_musly_jukebox(config: MuslyJukeboxConfig = None):
    if config is None:
        config = {"method": None, "decoder": None}

    if not is_musly_present():
        raise RuntimeError("cannot create musly jukebox: pymusly not present")

    return MuslyJukebox(**config)


def load_musly_jukebox(filename: str, config: MuslyJukeboxConfig = None, create=False):
    if not is_musly_present():
        raise RuntimeError("cannot load musly jukebox: pymusly not present")

    if not exists(filename):
        if not create:
            raise FileNotFoundError(f"no jukebox found at {filename}")
        return create_musly_jukebox(config)

    try:
        with open(filename, "rb") as fh:
            return MuslyJukebox.create_from_stream(input_stream=fh, ignore_decoder=True)
    except MuslyError as e:
        raise RuntimeError(
            f"could not load musly jukebox from '{filename}': file seems to be corrupted ({e})"
        )
    except Exception as e:
        raise RuntimeError(
            f"could not load musly jukebox from '{filename}': unexpected error ({e})"
        )


def save_musly_jukebox(filename: str, jukebox: MuslyJukebox):
    if not is_musly_present():
        raise RuntimeError("cannot save musly jukebox: pymusly not present")

    try:
        with open(filename, "wb") as fh:
            jukebox.serialize_to_stream(fh)
    except MuslyError as e:
        raise RuntimeError(f"could not save musly jukebox to '{filename}': {e}")

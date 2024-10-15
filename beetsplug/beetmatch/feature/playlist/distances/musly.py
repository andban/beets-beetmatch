from base64 import b64decode
from math import isnan
from typing import Union

from beetsplug.beetmatch.musly import MuslyJukebox, MuslyTrack

_CACHE = dict()


class MuslyDistance:
    jukebox: MuslyJukebox
    key: str

    def __init__(self, jukebox=None, key="musly_track", **kwargs):
        self.jukebox = jukebox
        self.key = key

    def get_value(self, item) -> Union[MuslyTrack, None]:
        if self.jukebox is None:
            return None

        item_id = item.get("id")

        if item_id in _CACHE:
            return _CACHE.get(item_id)

        base64_track = item.get(self.key, None)
        if base64_track is None:
            return None

        track = self.jukebox.track_from_bytearray(b64decode(base64_track))
        _CACHE[item_id] = track

        return track

    def distance(self, a, b) -> float:
        if self.jukebox is None:
            return 0

        a_track = self.get_value(a)
        b_track = self.get_value(b)
        if a_track is None or b_track is None:
            return float("inf")

        return self.jukebox.compute_similarity(a_track, a.id, [b_track], [b.id])[0]

    def similarity(self, a, b) -> float:
        distance = self.distance(a, b)
        if isnan(distance):
            return -float("inf")

        return 1 - distance

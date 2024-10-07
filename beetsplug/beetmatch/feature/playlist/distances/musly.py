from base64 import b64decode

from beetsplug.beetmatch.musly import MuslyJukebox


class MuslyDistance:
    jukebox: MuslyJukebox
    key: str

    def __init__(self, jukebox=None, key="musly_track", **kwargs):
        self.jukebox = jukebox
        self.key = key

    def distance(self, a, b):
        if self.jukebox is None:
            return 0

        a_track_raw = a.get(self.key)
        b_track_raw = b.get(self.key)

        if not a_track_raw or not b_track_raw:
            return float("inf")

        a_track = self.jukebox.track_from_bytearray(b64decode(a_track_raw))
        b_track = self.jukebox.track_from_bytearray(b64decode(b_track_raw))
        ret = self.jukebox.compute_similarity(a_track, a.id, [b_track], [b.id])

        return ret[0]

    def similarity(self, a, b):
        distance = self.distance(a, b)
        if distance == float("inf"):
            return 0.0

        return 1 - distance

import weakref
from io import BytesIO
from typing import BinaryIO, List

from . import libmusly
from .track import MuslyTrack


class MuslyJukebox(object):
    def __init__(self, ctx=None, method=None, decoder=None):
        """Create new Jukebox instance.
        You can override default method and decoder using the 'method' and 'decoder' parameters.
        """
        if ctx:
            self._ctx = ctx
        else:
            self._ctx = libmusly.jukebox_create(method, decoder)

        self._finalizer = weakref.finalize(
            self, libmusly.jukebox_free, self._ctx
        )

    def close(self):
        self._finalizer()

    def method(self):
        """Return method used for similarity computations."""
        return self._ctx.contents.method_name.decode("utf-8")

    def decoder(self):
        """Return decoder for automatic audio file decoding."""
        return self._ctx.contents.decoder_name.decode("utf-8")

    def method_description(self):
        """Return description of the used similarity measure"""
        return libmusly.jukebox_method_info(self._ctx)

    def track_size(self):
        """Return the size of a jukebox track in bytes"""
        return libmusly.jukebox_track_size(self._ctx)

    def track_count(self):
        """Return number of tracks registered with the jukebox."""
        return libmusly.jukebox_track_count(self._ctx)

    def largest_track_id(self):
        """Return the largest track id registered.
        This can be used for generating a version for the jukebox:
        (maxtrackid+1).(maxtrackid+1-track_count).
        """
        return libmusly.jukebox_max_track_id(self._ctx)

    def track_ids(self):
        """Return list of all track ids registered with the jukebox."""
        return libmusly.jukebox_get_track_ids(self._ctx)

    def write_to(self, dest: BinaryIO):
        """Serializes jukebox state into `dest` using `buffer_size` bytes at a time.
        This writes only the ids of the tracks added to the jukebox using the
        `add_track` and `set_style` methods.
        """
        libmusly.jukebox_serialize(jukebox=self._ctx, dest=dest)

    @staticmethod
    def load_from(src: BytesIO, ignore_decoder=True):
        """Loads jukebox state from `src` using `buffer_size` bytes at a time."""
        musly_jukebox = libmusly.jukebox_deserialize(src, ignore_decoder)
        return MuslyJukebox(ctx=musly_jukebox)

    def add_tracks(self, tracks: List[MuslyTrack], track_ids=None):
        """Add all items of the `tracks` list to the jukebox.
        When `track_ids` is a list, each entry of `tracks` is assigned the id found at the same index in `track_ids`.
        When `track_ids` is `None`, track ids are automatically generated.
        """
        return libmusly.jukebox_add_tracks(self._ctx, [t.track_ptr for t in tracks], track_ids)

    def remove_tracks(self, track_ids: list):
        """Remove tracks of `track_ids` from the jukebox."""
        libmusly.jukebox_remove_tracks(self._ctx, track_ids)

    def track_to_string(self, track: MuslyTrack):
        """Return a string representation of the feature vector of given `track`."""
        return libmusly.jukebox_track_to_string(self._ctx, track.track_ptr)

    def track_to_buffer(self, track: MuslyTrack):
        """Convert the given `track` into a binary representration`."""
        return libmusly.jukebox_track_to_bytearray(self._ctx, track.track_ptr)

    def track_from_bytearray(self, ba):
        track_ptr = libmusly.jukebox_track_from_bytearray(self._ctx, ba)

        return MuslyTrack(track_ptr)

    def track_from_audio_file(self, filename, start, length):
        track_ptr = libmusly.jukebox_track_from_audio_file(self._ctx, filename, start, length)

        return MuslyTrack(track_ptr)

    def set_style(self, tracks):
        libmusly.jukebox_set_style(self._ctx, [t.track_ptr for t in tracks if t.track_ptr])

    def compute_similarity(self, seed_track, seed_track_id, tracks, track_ids):
        return libmusly.jukebox_compute_similarities(
            self._ctx,
            seed_track.track_ptr,
            seed_track_id,
            [t.track_ptr for t in tracks],
            track_ids
        )

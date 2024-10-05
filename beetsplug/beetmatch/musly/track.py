import weakref

import beetsplug.beetmatch.musly.libmusly as libmusly


class MuslyTrack(object):
    def __init__(self, track_ptr: libmusly.TrackStruct):
        self._track_ptr = track_ptr

        self._finalizer = weakref.finalize(
            self, libmusly.track_free, self._track_ptr
        )

    @property
    def track_ptr(self) -> libmusly.TrackStruct:
        return self._track_ptr

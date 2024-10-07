import os.path
from base64 import b64encode

import pytest
from beets.library import Item

from beetsplug.beetmatch.feature.playlist.distances import MuslyDistance
from beetsplug.beetmatch.musly import MuslyJukebox
from tests.assert_helper import assert_greater_than, assert_almost_equal
from tests.helper import FIXTURE_DIR, MUSLY_AVAILABLE


@pytest.mark.skipif(not MUSLY_AVAILABLE, reason="libmusly not available")
class TestMuslyDistance:
    def test_musly_similarity_when_analyzed_tracks(self):
        jukebox, a, b = _create_jukebox()
        measure = MuslyDistance(jukebox=jukebox)

        dist = measure.distance(a, b)
        assert_greater_than(round(dist, 7), 0.0)
        assert_almost_equal(measure.similarity(a, b), round(1 - dist, 7))

    def test_always_same_when_no_jukebox(self):
        a = {"musly_track": b64encode(b"a")}
        b = {"musly_track": b64encode(b"b")}

        measure = MuslyDistance()

        assert_almost_equal(measure.distance(a, b), 0.0)
        assert_almost_equal(measure.similarity(a, b), 1.0)

    def test_max_when_both_not_analyzed(self):
        a = {}
        b = {}
        jukebox, _, _ = _create_jukebox()

        measure = MuslyDistance(jukebox=jukebox)

        assert measure.distance(a, b) == float("inf")
        assert_almost_equal(measure.similarity(a, b), 0.0)

    def test_max_when_one_not_analyzed(self):
        a = {}
        jukebox, _, b = _create_jukebox()

        measure = MuslyDistance(jukebox=jukebox)

        assert measure.distance(a, b) == float("inf")
        assert_almost_equal(measure.similarity(a, b), 0.0)


def _create_jukebox():
    jukebox = MuslyJukebox(method="timbre")
    track_a = jukebox.track_from_audio_file(
        os.path.join(FIXTURE_DIR, b"sample-12s.mp3"), -12, 12
    )
    track_b = jukebox.track_from_audio_file(
        os.path.join(FIXTURE_DIR, b"sample-15s.mp3"), -15, 15
    )

    jukebox.set_style([track_a, track_b])
    jukebox.add_tracks([track_a, track_b], [1, 2])

    item_a = Item(
        id=1, musly_track=b64encode(jukebox.track_to_buffer(track_a)).decode("ascii")
    )
    item_b = Item(
        id=2, musly_track=b64encode(jukebox.track_to_buffer(track_b)).decode("ascii")
    )

    return jukebox, item_a, item_b

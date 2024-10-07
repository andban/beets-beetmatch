import pytest

from beetsplug.beetmatch.feature.playlist.distances import BpmDistance
from tests.assert_helper import assert_almost_equal


class TestBpmDistance:
    @pytest.mark.parametrize(
        "bpm_a,bpm_b,tolerance",
        [
            (100, 100, 0.0),
            (100, 110, 0.1),
            (100, 90, 0.1),
            (90, 99, 0.1),
            (150, 120, 0.2),
        ],
    )
    def test_bpm_diff_within_tolerance(self, bpm_a, bpm_b, tolerance):
        a = {"bpm": bpm_a}
        b = {"bpm": bpm_b}

        measure = BpmDistance(key="bpm", tolerance=tolerance)

        assert_almost_equal(measure.distance(a, b), 0.0)
        assert_almost_equal(measure.similarity(a, b), 1.0)

    @pytest.mark.parametrize(
        "bpm_a,bpm_b,tolerance",
        [
            (100, 111, 0.1),
            (90, 100, 0.1),
            (100, 79, 0.2),
            (150, 119, 0.2),
            (None, 100, 0.1),
            (100, None, 0.1),
            (None, None, 0.1),
        ],
    )
    def test_bpm_diff_over_tolerance(self, bpm_a, bpm_b, tolerance):
        a = {"bpm": bpm_a}
        b = {"bpm": bpm_b}

        measure = BpmDistance(key="bpm", tolerance=tolerance)

        assert_almost_equal(measure.distance(a, b), 1.0)
        assert_almost_equal(measure.similarity(a, b), 0.0)

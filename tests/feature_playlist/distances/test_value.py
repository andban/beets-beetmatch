import pytest

from beetsplug.beetmatch.feature.playlist.distances import NumberDistance
from tests.assert_helper import assert_almost_equal


class TestNumberDistance:
    @pytest.fixture(autouse=True)
    def measure(self):
        return NumberDistance("danceability", min_value=-1, max_value=1)

    def test_diff_within_range(self, measure):
        a = {"danceability": 0.5}
        b = {"danceability": -0.3}

        assert_almost_equal(measure.distance(a, b), 0.4)
        assert_almost_equal(measure.similarity(a, b), 0.6)

    def test_diff_out_of_range(self, measure):
        a = {"danceability": -1.0}
        b = {"danceability": 12.0}

        assert_almost_equal(measure.distance(a, b), 1.0)
        assert_almost_equal(measure.similarity(a, b), 0.0)

    @pytest.mark.parametrize(
        "value_a,value_b", [(None, 0.5), (0.25, None), (None, None)]
    )
    def test_nax_if_values_not_set(self, measure, value_a, value_b):
        a = {"danceability": value_a}
        b = {"danceability": value_b}

        assert_almost_equal(measure.distance(a, b), 1.0)
        assert_almost_equal(measure.similarity(a, b), 0.0)

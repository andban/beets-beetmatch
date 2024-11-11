import pytest

from beetsplug.beetmatch.feature.playlist.distances import YearDistance
from tests.assert_helper import assert_almost_equal


class TestYearDistance:
    @pytest.fixture
    def measure(self):
        return YearDistance(key="year", max_diff=5)

    def test_year_within_range(self, measure):
        a = {"year": "1990"}
        b = {"year": "1995"}

        assert_almost_equal(measure.distance(a, b), 0.0)
        assert_almost_equal(measure.similarity(a, b), 1.0)

    def test_year_out_of_range(self, measure):
        a = {"year": "2006"}
        b = {"year": "2000"}

        assert_almost_equal(measure.distance(a, b), 1.0)
        assert_almost_equal(measure.similarity(a, b), 0.0)

    @pytest.mark.parametrize(
        "value_a,value_b", [(None, 2000), (2024, None), (None, None)]
    )
    def test_year_not_set(self, measure, value_a, value_b):
        a = {"year": value_a}
        b = {"year": value_b}

        assert_almost_equal(measure.distance(a, b), 1.0)
        assert_almost_equal(measure.similarity(a, b), 0.0)

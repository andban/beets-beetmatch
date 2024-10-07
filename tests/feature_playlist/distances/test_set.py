import pytest

from beetsplug.beetmatch.feature.playlist.distances import ListDistance
from tests.assert_helper import assert_almost_equal


class TestListDistance:
    @pytest.fixture(autouse=True)
    def measure(self):
        return ListDistance(key="style")

    def test_list_full_match(self, measure):
        a = {"style": "trance, acid"}
        b = {"style": "trance, acid"}

        assert_almost_equal(measure.distance(a, b), 0.0)
        assert_almost_equal(measure.similarity(a, b), 1.0)

    def test_list_partial_match(self, measure):
        a = {"style": "trance, ambient"}
        b = {"style": "trance, acid"}

        assert_almost_equal(measure.distance(a, b), 0.667, 3)
        assert_almost_equal(measure.similarity(a, b), 0.333, 3)

    def test_list_no_match(self, measure):
        a = {"style": "trance, ambient"}
        b = {"style": "techno, ebm"}

        assert_almost_equal(measure.distance(a, b), 1.0)
        assert_almost_equal(measure.similarity(a, b), 0.0)

    @pytest.mark.parametrize(
        "style_a,style_b",
        [("Vegetarian Progressive Grindcore", None), (None, "Lounge"), (None, None)],
    )
    def test_list_not_present(self, measure, style_a, style_b):
        a = {"style": style_a}
        b = {"style": style_b}

        assert_almost_equal(measure.distance(a, b), 1.0)
        assert_almost_equal(measure.similarity(a, b), 0.0)

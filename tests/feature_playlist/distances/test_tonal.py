import pytest

from beetsplug.beetmatch.feature.playlist.distances import TonalDistance
from tests.assert_helper import assert_almost_equal


class TestTonalDistance:
    @pytest.mark.parametrize(
        "value,config",
        [
            ({"key": "C"}, {"notation": "standard"}),
            ({"key": "Gm"}, {"notation": "standard"}),
            (
                {"key": "C", "scale": "major"},
                {"notation": "essentia", "key_scale": "scale"},
            ),
            (
                {"key": "G", "scale": "minor"},
                {"notation": "essentia", "key_scale": "scale"},
            ),
        ],
    )
    def test_key_is_same(self, value, config):
        tonal = TonalDistance(key="key", **config)

        assert round(tonal.distance(value, value), 7) == 0.0
        assert round(tonal.similarity(value, value), 7) == 1.0

    @pytest.mark.parametrize(
        "key_a,key_b",
        [
            ("A", "D"),
            ("A", "F#m"),
            ("A", "E"),
        ],
    )
    def test_key_is_close(self, key_a, key_b):
        a = {"key": key_a}
        b = {"key": key_b}

        measure = TonalDistance(key="key", notation="standard")

        assert round(measure.distance(a, b), 7) == 0.0
        assert round(measure.similarity(a, b), 7) == 1.0

    @pytest.mark.parametrize(
        "key_a,key_b", [("D#", "Em"), (None, "C"), ("D", None), (None, None)]
    )
    def test_key_not_close(self, key_a, key_b):
        a = {"key": key_a}
        b = {"key": key_b}

        measure = TonalDistance(key="key", notation="standard")

        assert_almost_equal(measure.distance(a, b), 1.0)
        assert_almost_equal(measure.similarity(a, b), 0.0)

import unittest

import pytest

from beetsplug.beetmatch.feature.playlist.distances import TonalDistance


class TestTonalDistance:

    @pytest.mark.parametrize(
        "value,config",
        [
            ({}, {"notation": "standard"}),
            ({"key": "C"}, {"notation": "standard"}),
            ({"key": "Gm"}, {"notation": "standard"}),
            ({}, {"notation": "essentia", "key_scale": "scale"}),
            ({"key": "C", "scale": "major"}, {"notation": "essentia", "key_scale": "scale"}),
            ({"key": "G", "scale": "minor"}, {"notation": "essentia", "key_scale": "scale"}),
        ]
    )
    def test_key_is_same(self, value, config):
        tonal = TonalDistance(key="key", **config)

        assert round(tonal.distance(value, value), 7) == 0.0
        assert round(tonal.similarity(value, value), 7) == 1.0

    @pytest.mark.parametrize(
        "key_a,key_b",
        [
            ({"key": "A"}, {"key": "D"}),
            ({"key": "A"}, {"key": "F#m"}),
            ({"key": "A"}, {"key": "E"})
        ]
    )
    def test_key_is_close(self, key_a, key_b):
        tonal = TonalDistance(key="key", notation="standard")

        assert round(tonal.distance(key_a, key_b), 7) == 0.0
        assert round(tonal.similarity(key_a, key_b), 7) == 1.0

    def test_key_not_close(self):
        key_a = {"key": "D#"}
        key_b = {"key": "Em"}
        tonal = TonalDistance(key="key", notation="standard")

        assert round(tonal.distance(key_a, key_b), 7) == 1.0
        assert round(tonal.similarity(key_a, key_b), 7) == 0.0


if __name__ == "__main__":
    unittest.main()
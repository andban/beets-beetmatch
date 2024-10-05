import unittest

from beetsplug.beetmatch.feature.playlist.distances import TonalDistance


class TonalDistanceTest(unittest.TestCase):

    def test_key_is_same(self):
        cases = [
            {"value": {}, "config": {"notation": "standard"}},
            {"value": {"key": "Z"}, "config": {"notation": "standard"}},
            {"value": {"key": "C"}, "config": {"notation": "standard"}},
            {"value": {"key": "C", "scale": "major"}, "config": {"notation": "essentia", "key_scale": "scale"}},
            {"value": {"key": "Z", "scale": "grande"}, "config": {"notation": "essentia", "key_scale": "scale"}},
            {"value": {}, "config": {"notation": "essentia", "key_scale": "scale"}}
        ]
        for case in cases:
            with self.subTest(case):
                tonal = TonalDistance(key="key", **case["config"])

                self.assertAlmostEqual(tonal.distance(case["value"], case["value"]), 0.0)
                self.assertAlmostEqual(tonal.similarity(case["value"], case["value"]), 1.0)

    def test_key_is_close(self):
        pass


if __name__ == "__main__":
    unittest.main()

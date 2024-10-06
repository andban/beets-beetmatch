import unittest

from beetsplug.beetmatch.feature.playlist.distances import NumberDistance


class NumberDistanceTest(unittest.TestCase):
    def test_danceability_within_range(self):
        dance = NumberDistance("danceability")
        a = {"danceability": 0.5}
        b = {"danceability": 0.3}

        self.assertAlmostEqual(dance.distance(a, b), 0.2)
        self.assertAlmostEqual(dance.similarity(a, b), 0.8)

    def test_danceability_out_of_range(self):
        dance = NumberDistance("danceability")
        a = {"danceability": -1.0}
        b = {"danceability": 12.0}

        self.assertAlmostEqual(dance.distance(a, b), 1.0)
        self.assertAlmostEqual(dance.similarity(a, b), 0.0)


if __name__ == "__main__":
    unittest.main()

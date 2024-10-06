import unittest

from beetsplug.beetmatch.feature.playlist.distances import YearDistance


class YearDistanceTest(unittest.TestCase):
    def test_year_within_range(self):
        year = YearDistance(key="year", max_diff=5)
        a = {"year": "1990"}
        b = {"year": "1995"}

        self.assertAlmostEqual(year.distance(a, b), 0.0)
        self.assertAlmostEqual(year.similarity(a, b), 1.0)

    def test_year_out_of_range(self):
        year = YearDistance(key="year", max_diff=3)
        a = {"year": "2000"}
        b = {"year": "2004"}

        self.assertAlmostEqual(year.distance(a, b), 1.0)
        self.assertAlmostEqual(year.similarity(a, b), 0.0)


if __name__ == "__main__":
    unittest.main()

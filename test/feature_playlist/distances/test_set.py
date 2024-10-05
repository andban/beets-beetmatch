import unittest

from beetsplug.beetmatch.feature.playlist.distances import ListDistance


class ListDistanceTest(unittest.TestCase):
    set_measure: ListDistance

    def setUp(self):
        self.set_measure = ListDistance(key="style")

    def test_style_full_match(self):
        a = {"style": "trance, acid"}
        b = {"style": "trance, acid"}

        self.assertAlmostEqual(self.set_measure.distance(a, b), 0.0)
        self.assertAlmostEqual(self.set_measure.similarity(a, b), 1.0)

    def test_style_partial_match(self):
        a = {"style": "trance, ambient"}
        b = {"style": "trance, acid"}

        self.assertAlmostEqual(self.set_measure.distance(a, b), 0.666, 2)
        self.assertAlmostEqual(self.set_measure.similarity(a, b), 0.333, 2)

    def test_style_no_match(self):
        a = {"style": "trance, ambient"}
        b = {"style": "techno, ebm"}

        self.assertAlmostEqual(self.set_measure.distance(a, b), 1.0)
        self.assertAlmostEqual(self.set_measure.similarity(a, b), 0.0)


if __name__ == "__main__":
    unittest.main()

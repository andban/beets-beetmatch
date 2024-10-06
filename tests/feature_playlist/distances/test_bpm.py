import unittest

from beetsplug.beetmatch.feature.playlist.distances import BpmDistance


class BpmDistanceTest(unittest.TestCase):
    def test_bpm_in_tolerance(self):
        bpm = BpmDistance(key="bpm", tolerance=0.1)
        a = {"bpm": 100}
        b = {"bpm": 110}

        self.assertAlmostEqual(bpm.distance(a, b), 0.0)
        self.assertAlmostEqual(bpm.similarity(a, b), 1.0)

    def test_bpm_over_tolerance(self):
        bpm = BpmDistance(key="bpm", tolerance=0.1)
        a = {"bpm": 100}
        b = {"bpm": 111}

        self.assertAlmostEqual(bpm.distance(a, b), 1.0)
        self.assertAlmostEqual(bpm.similarity(a, b), 0.0)


if __name__ == "__main__":
    unittest.main()

import unittest

import beetsplug.beetmatch.musly as musly
from test.helper import MUSLY_AVAILABLE


@unittest.skipIf(not MUSLY_AVAILABLE, "libmusly not available")
class MuslyTest(unittest.TestCase):
    def test_jukebox_method(self):
        methods = musly.libmusly.list_methods()
        self.assertGreaterEqual(len(methods), 1)

        for method in methods:
            jukebox = musly.MuslyJukebox(method=method)

            self.assertEqual(jukebox.method(), method)
            self.assertIsNotNone(jukebox.method_description())
            self.assertGreater(jukebox.track_size(), 0)
            self.assertEqual(jukebox.track_count(), 0)

            jukebox.close()


if __name__ == "__main__":
    unittest.main()

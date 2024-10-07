import pytest

from tests.helper import ImportTest, MUSLY_AVAILABLE


class TestBeetmatchPlugin(ImportTest):
    @pytest.fixture(name="lib")
    def fixture_lib(self):
        self.setup_beets(load_plugin=False)
        yield self.lib
        self.teardown_beets()

    @pytest.fixture(name="importer")
    def fixture_importer(self, lib):
        self.setup_import()
        self.prepare_track_for_import(1)
        track = self.import_media[0]
        setattr(track, "musly_track", None)
        setattr(track, "musly_method", None)
        track.save()
        yield self.prepare_importer()
        lib.get_item(1).remove(True)

    @pytest.mark.skipif(not MUSLY_AVAILABLE, reason="libmusly not available")
    def test_auto_import(self, lib, importer):
        self.config.set({
            "beetmatch": {"auto": True}
        })
        self.load_plugins()

        importer.run()

        item = lib.get_item(1)

        assert item.get("musly_track") is not None
        assert item.get("musly_method") == "timbre"

    def test_disable_auto_import(self, lib, importer):
        self.config.set({
            "beetmatch": {"auto": False}
        })
        self.load_plugins()

        importer.run()

        item = lib.get_item(1)

        assert "musly_track" not in item
        assert "musly_method" not in item

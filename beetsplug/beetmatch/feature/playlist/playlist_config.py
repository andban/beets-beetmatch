import confuse

from . import distances
from .cooldown import Cooldown
from .track_attribute import TrackAttribute

_DEFAULT_CONFIG = {
    "playlist": {
        "default_script": None,

        "cooldown": {
            "artist": 0,
            "album": 0,
        },

        "attributes": {
            "genre": {
                "type": "SetDistance",
                "weight": 0.34
            },
            "year": {
                "type": "YearDistance",
                "weight": 0.33,
                "config": {
                    "max_diff": 5
                }
            },
            "bpm": {
                "type": "BpmDistance",
                "weight": 0.33,
                "config": {
                    "tolerance": 0.1
                }
            }
        }
    }
}


class PlaylistConfig:
    _config: confuse.Subview

    def __init__(self, config: confuse.Subview):
        self._config = config
        self._config.add(_DEFAULT_CONFIG)

    @property
    def _config_root(self):
        return self._config["playlist"]

    @property
    def playlist_cooldown(self):
        cooldown_config = self._config_root["cooldown"].get(dict)
        return Cooldown(cooldown_config)

    @property
    def playlist_script(self):
        script = self._config_root["default_script"].get(
            confuse.Optional(confuse.Path(in_app_dir=True)))

        return script.resolve() if script else None

    def create_similarity_measure(self, **config: dict):
        attributes = [TrackAttribute(key=key, **a) for key, a in self._config_root["attributes"].get(dict).items()]
        measures = [(a.get_measure(**config), a.weight) for a in attributes]
        agg_measure = distances.EuclideanDistance(measures)

        return lambda a, b: agg_measure.similarity(a, b)

import inspect
import sys

from beetsplug.beetmatch.musly import MuslyJukebox
from .distance import Distance

clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)

valid_classes = [
    'BpmDistance',
    'DanceabilityDistance',
    'GenreDistance',
    'MuslyDistance',
    'NumberDistance',
    'SetDistance',
    'TonalDistance',
    'YearDistance'
]


class Attribute:
    key: str
    dist_func: Distance
    weight: float

    def __init__(self, jukebox: MuslyJukebox, key: str, type: str, weight: float = 0.0, config=None, **_):
        if config is None:
            config = {}

        if type not in valid_classes:
            raise KeyError("unknown distance type {}".format(type))

        dist_class = getattr(distances, type)

        self.dist_func = dist_class(jukebox=jukebox, key=key, **config)
        self.key = key
        self.weight = weight

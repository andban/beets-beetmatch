from . import distances


class TrackAttribute:
    _key: str
    _weight: float
    _config: dict
    _measure_class: any

    def __init__(self, key: str, type: str, weight: float = 0.0, config=None, **kwargs):
        self._measure_class = getattr(distances, type)

        self._key = key
        self._weight = weight
        self._config = config if config is not None else {}

    @property
    def key(self):
        return self._key

    @property
    def weight(self):
        return self._weight

    def get_measure(self, **kwargs) -> distances.Distance:
        return self._measure_class(key=self.key, **self._config, **kwargs)

from .distance import Distance


class NumberDistance(Distance):
    min_value: float
    max_value: float

    def __init__(self, key, min_value=0.0, max_value=1.0, **kwargs):
        super().__init__(key)
        self.min_value = min_value
        self.max_value = max_value

    def get_value(self, item):
        raw_value = item.get(self.key, None)
        if raw_value is None:
            return None

        try:
            return min(max(self.min_value, float(raw_value)), self.max_value)
        except TypeError:
            return None

    def similarity(self, a, b):
        return 1 - self.distance(a, b)

    def distance(self, a: dict, b: dict):
        a_value = self.get_value(a)
        b_value = self.get_value(b)
        if a_value is None or b_value is None:
            return 1.0

        return abs(a_value - b_value) / (self.max_value - self.min_value)

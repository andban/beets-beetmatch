from .distance import Distance


class NumberDistance(Distance):
    min_value: float
    max_value: float

    def __init__(self, key, min_value=0.0, max_value=1.0, **kwargs):
        super().__init__(key)
        self.min_value = min_value
        self.max_value = max_value

    def similarity(self, a, b):
        return 1 - self.distance(a, b)

    def distance(self, a: dict, b: dict):
        a_value = None
        try:
            a_value = min(max(self.min_value, float(
                a.get(self.key))), self.max_value)
        except TypeError:
            pass

        b_value = None
        try:
            b_value = min(max(self.min_value, float(
                b.get(self.key))), self.max_value)
        except TypeError:
            pass

        if a_value is None and b_value is None:
            return 1.0

        if a_value is None or b_value is None:
            return 0.0

        return abs(a_value - b_value) / (self.max_value - self.min_value)


class DanceabilityDistance(NumberDistance):
    def __init__(self):
        super().__init__("danceability")

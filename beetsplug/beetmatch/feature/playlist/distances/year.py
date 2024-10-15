from .distance import Distance


class YearDistance(Distance):
    max_diff: int

    def __init__(self, key="year", max_diff=5, **kwargs):
        super().__init__(key)
        self.max_diff = abs(max_diff)

    def get_value(self, item):
        raw_value = item.get(self.key, None)
        if raw_value is None:
            return None

        return int(raw_value)

    def similarity(self, a, b):
        a_year = self.get_value(a)
        b_year = self.get_value(b)

        if a_year is None or b_year is None:
            return 0.0

        return 1.0 if abs(int(a_year) - int(b_year)) <= self.max_diff else 0.0

    def distance(self, a, b):
        return 1.0 - self.similarity(a, b)

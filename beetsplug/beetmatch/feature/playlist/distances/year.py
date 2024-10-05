from .distance import Distance


class YearDistance(Distance):
    max_diff: int

    def __init__(self, key="year", max_diff=5, **kwargs):
        super().__init__(key)
        self.max_diff = abs(max_diff)

    def similarity(self, a, b):
        a_year = a.get(self.key, None)
        b_year = b.get(self.key, None)

        if a_year is None or b_year is None:
            return 1.0 if a_year == b_year else 0.0

        return 1.0 if abs(int(a_year) - int(b_year)) <= self.max_diff else 0.0

    def distance(self, a, b):
        return 1.0 - self.similarity(a, b)

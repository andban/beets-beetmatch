from .distance import Distance


class BpmDistance(Distance):
    tolerance: float

    def __init__(self, key="bpm", tolerance=0.1, **kwargs):
        super().__init__(key)
        self.tolerance = tolerance

    def similarity(self, a, b):
        a_bpm = a.get(self.key, None)
        b_bpm = b.get(self.key, None)

        if a_bpm is None or b_bpm is None:
            return 0.0

        threshold = a_bpm * self.tolerance
        return 1.0 if abs(int(a_bpm) - int(b_bpm)) <= threshold else 0.0

    def distance(self, a, b):
        return 1.0 - self.similarity(a, b)

from typing import Union

from .distance import Distance


class BpmDistance(Distance):
    tolerance: float

    def __init__(self, key="bpm", tolerance=0.1, **kwargs):
        super().__init__(key)
        self.tolerance = tolerance

    def get_value(self, item) -> Union[int, None]:
        return item.get(self.key, None)

    def similarity(self, a, b):
        a_bpm = self.get_value(a)
        b_bpm = self.get_value(b)

        if not a_bpm or not b_bpm:
            return 0.0

        threshold = a_bpm * self.tolerance
        return 1.0 if abs(a_bpm - b_bpm) <= threshold else 0.0

    def distance(self, a, b):
        return 1.0 - self.similarity(a, b)

from typing import Any, Callable, Set, Union

from .distance import Distance


class SetDistance(Distance):
    """Distance between two sets using Jaccard Index."""

    transformer: Callable[[Any], Set]
    ignore: Set[str]

    def __init__(
            self,
            key,
            ignore=None,
            transformer: Callable[[Any], Set] = lambda v: set(v),
            **kwargs,
    ):
        super().__init__(key)

        if ignore is None:
            ignore = []

        self.transformer = transformer
        self.ignore = set(ignore)

    def get_value(self, item) -> Union[set, None]:
        value = item.get(self.key, set())
        return self.transformer(value) - self.ignore

    def similarity(self, a, b):
        a_values = self.get_value(a)
        b_values = self.get_value(b)

        if not a_values or not b_values:
            return 0.0

        union_values = a_values | b_values
        matched_values = a_values & b_values

        return len(matched_values) / len(union_values)

    def distance(self, a, b):
        return 1.0 - self.similarity(a, b)


class ListDistance(SetDistance):
    def __init__(self, key, **kwargs):
        super().__init__(
            key,
            **kwargs,
            transformer=lambda v: set(v.split(", ") if isinstance(v, str) else []),
        )

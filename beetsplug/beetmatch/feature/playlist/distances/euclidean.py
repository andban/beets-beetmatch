from functools import reduce
from math import sqrt


class EuclideanDistance:
    dimensions: list
    sum_weight: float

    def __init__(self, dimensions=None, **kwargs):
        if dimensions is None:
            dimensions = []

        self.dimensions = list(dimensions)
        self.sum_weight = reduce(lambda sum, d: sum + d[1], self.dimensions, 0.0)

    def add(self, dimension, weight=1.0):
        if weight < 0.0:
            raise TypeError("weight must be >= 0")

        if weight > 0:
            self.dimensions.append(
                (
                    dimension,
                    weight,
                )
            )

    def distance(self, a, b):
        def reducer(sum, dimension):
            dist_fn, weight = dimension
            return sum + pow(dist_fn.distance(a, b), 2) * weight

        sum = (
            reduce(
                reducer,
                self.dimensions,
                0.0,
            )
            / self.sum_weight
        )

        return sqrt(sum)

    def similarity(self, a, b):
        return 1 - self.distance(a, b)

from abc import ABC, abstractmethod


class Distance(ABC):
    key: str

    def __init__(self, key, **kwargs):
        self.key = key

    def get_key(self):
        return self.key

    def get_value(self, item):
        pass

    @abstractmethod
    def distance(self, a, b):
        """Compute the distance between two items `a` and `b`"""
        pass

    @abstractmethod
    def similarity(self, a, b):
        """Compute the similarity of two items `a` and `b`"""
        pass

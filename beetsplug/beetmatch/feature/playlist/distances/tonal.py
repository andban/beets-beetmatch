from typing import Union

from .distance import Distance

_CIRCLE_OF_FITHS_INDEX = {
    "B": 0,
    "G#m": 0,
    "F#": 1,
    "D#m": 1,
    "C#": 2,
    "A#m": 2,
    "G#": 3,
    "Fm": 3,
    "D#": 4,
    "Cm": 4,
    "A#": 5,
    "Gm": 5,
    "F": 6,
    "Dm": 6,
    "C": 7,
    "Am": 7,
    "G": 8,
    "Em": 8,
    "D": 9,
    "Bm": 9,
    "A": 10,
    "F#m": 10,
    "E": 11,
    "C#m": 11,
}


def standard_mapper(key: str, **kwargs):
    def mapper(item):
        return item.get(key, None)

    return mapper


def essentia_mapper(key: str, key_scale: str, **kwargs):
    def mapper(item):
        key_value = item.get(key, None)
        scale_value = item.get(key_scale, None)
        if not key_value or not scale_value:
            return None

        return key_value if scale_value == "major" else f"{key_value}m"

    return mapper


class TonalDistance(Distance):
    """Distance for musical keys using neighborhood in the circle of fifths."""

    def __init__(self, key="key", notation="standard", **kwargs):
        super().__init__(key)

        if notation == "standard":
            self.mapper = standard_mapper(key)
        elif notation == "essentia":
            self.mapper = essentia_mapper(key, **kwargs)
        else:
            raise Exception(
                "tonal distance '%s': invalid notation option '%s'", key, notation
            )

    def get_value(self, item) -> Union[str, None]:
        return self.mapper(item)

    def similarity(self, a, b):
        a_scale = self.get_value(a)
        b_scale = self.get_value(b)

        a_position = _CIRCLE_OF_FITHS_INDEX.get(a_scale, None)
        b_position = _CIRCLE_OF_FITHS_INDEX.get(b_scale, None)

        if a_position is None or b_position is None:
            return 0.0

        if a_scale == b_scale or a_position == b_position:
            return 1.0

        a_minor = a_scale[-1] == "m"
        b_minor = b_scale[-1] == "m"
        if a_minor == b_minor:
            diff = abs(a_position - b_position)
            return 1.0 if diff <= 1 or diff == 11 else 0.0

        return 0.0

    def distance(self, a, b):
        return 1.0 - self.similarity(a, b)

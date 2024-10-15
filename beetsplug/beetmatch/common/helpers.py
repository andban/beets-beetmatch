import random
from types import ModuleType
from typing import Optional, Union, Tuple

from beets import ui


def pick_random_item(items: list):
    if not items:
        return None, -1

    if len(items) == 1:
        return items[0], 0

    index = random.randint(0, len(items) - 1)
    return items[index], index


def select_item_from_list(
        items: list,
        pick_random=False,
        title="Select one of the following items:",
        prompt="Enter item number:",
        item_format="{index:>3}. {item}",
) -> Union[Tuple[int, any], Tuple[int, None]]:
    """Select one item from a given list of `items`. If `items` contains only one item, this item
    is returned. When `items` contains more than one entry and `pick_random` is `False`, the user
    is prompted to select one item from the list. If `items` is empty, `(-1, None)` is returned."""
    # @todo: throw ValueError?
    if not items:
        return -1, None

    if len(items) == 1:
        return 0, items[0]

    if pick_random:
        index = random.randint(0, len(items) - 1)
        return index, items[index]

    ui.print_(title)
    for i, item in enumerate(items):
        ui.print_(item_format.format(index=i + 1, item=item))

    while True:
        input = ui.input_(prompt)
        try:
            input = int(input)
        except ValueError:
            pass
        else:
            if 1 <= input <= len(items):
                return input - 1, items[input - 1]


def import_optional(
        module: str,
        symbol: str = None,
        package: str = None,
        error: str = "raise"
) -> Optional[ModuleType]:
    import importlib
    import warnings

    try:
        module = importlib.import_module(module)
        return module if symbol is None else getattr(module, symbol)
    except ImportError as e:
        if package is None:
            package = module

        msg = f"package '{package}' not found"

        if error == "raise":
            raise ImportError(msg) from e
        elif error == "warn":
            warnings.warn(msg, UserWarning, stacklevel=2)

        return None


def normalize(value, low, high):
    if high == low:
        return 1
    return (value - low) / (high - low)


def bisect_left(a, x, key=lambda v: v):
    return next(i[0] for i in enumerate(a) if key(i[1]) >= x)

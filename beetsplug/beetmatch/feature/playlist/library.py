from beets.dbcore import Query
from beets.library import Library

from beetsplug.beetmatch.common import select_item_from_list


def select_item_random(lib: Library, query: Query):
    items = list(lib.items(query))
    if not items:
        return None

    _, item = select_item_from_list(items, pick_random=True)
    return item


def select_item_interactive(lib: Library, query: Query):
    items = list(lib.items(query))
    if not items:
        return None

    _, item = select_item_from_list(items,
                                    pick_random=False,
                                    title="The query matched more than one track, please select one:")
    return item


def select_items(lib: Library, query: Query):
    return list(lib.items(query))

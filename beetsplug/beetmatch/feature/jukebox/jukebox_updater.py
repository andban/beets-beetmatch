import logging
from base64 import b64decode
from math import isnan
from random import choice, sample
from typing import Callable, List

from beets.dbcore import AndQuery
from beets.dbcore.query import NoneQuery, NotQuery, Query, MatchQuery
from beets.library import Library, Item

from beetsplug.beetmatch.common import default_logger
from beetsplug.beetmatch.common.musly import MuslyJukebox


class JukeboxUpdater(object):
    log: logging.Logger
    lib: Library

    def __init__(
        self,
        library: Library,
        log: logging.Logger = logging.getLogger("beetmatch:updater"),
    ):
        self.lib = library
        self.log = log

    def update(self, jukebox: MuslyJukebox, query=None):
        if query is None:
            query = list()

        items = _select_analyzed_items(self.lib, jukebox.method, query)
        sample_size = min(999, len(items))

        while True:
            # seed_items = _stratified_sample(items, sample_size, lambda item: item.get("style").split(", "))
            seed_items = _random_sample(items, sample_size)

            self.log.info(
                "found %d items from which %d will be used as sample",
                len(items),
                len(seed_items),
            )

            tracks = [
                jukebox.deserialize_track(b64decode(item.get("musly_track")))
                for item in seed_items
            ]
            jukebox.set_style(tracks)

            if _verify_jukebox(items, jukebox):
                break

            self.log.debug("musly jukebox not valid. retrying...")


def _verify_jukebox(items: List[Item], jukebox: MuslyJukebox):
    item_sample = sample(items, k=min(100, len(items)))

    tracks = [
        (item.id, jukebox.deserialize_track(b64decode(item.get("musly_track"))))
        for item in item_sample
    ]

    jukebox.add_tracks(tracks)
    similarities = jukebox.compute_similarity(tracks[0], tracks[1:])

    jukebox.remove_tracks([track[0] for track in tracks])

    if len(set(similarities)) == 1:
        default_logger.info("all same")
        return False
    if all(isnan(s) for s in similarities):
        default_logger.info("inf")
        return False

    return True


def _select_analyzed_items(lib: Library, method: str, query: Query = None):
    all_queries = [
        query,
        AndQuery(
            [
                NotQuery(NoneQuery("musly_track", fast="musly_track" in Item._fields)),
                MatchQuery("musly_method", method, fast="musly_method" in Item._fields),
            ]
        ),
    ]

    return list(lib.items(AndQuery(all_queries)))


def _random_sample(items, k: int):
    return sample(items, k=k)


def _stratified_sample(items, k: int, categorizer: Callable[[dict], list]):
    if k >= len(items):
        return items

    all_categories = {}
    for item in items:
        item_categories = categorizer(item)
        if not item_categories:
            continue

        item_category = choice(item_categories)
        if item_category not in all_categories:
            all_categories[item_category] = {item}
        else:
            all_categories[item_category].add(item)

    categories_sorted = sorted(
        all_categories, key=lambda key: len(all_categories[key]), reverse=True
    )

    items_sampled = set()
    for item_category in categories_sorted:
        if k <= len(items_sampled):
            break

        category_items = list(
            filter(lambda i: i not in items_sampled, all_categories[item_category])
        )
        if not category_items:
            continue

        f = k * (len(category_items) / len(items))
        n = min(k - len(items_sampled), max(1, int(f)))
        choices = sample(category_items, k=n)
        for c in choices:
            items_sampled.add(c)

    return list(items_sampled)

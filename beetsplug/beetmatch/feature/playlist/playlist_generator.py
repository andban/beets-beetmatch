import logging
import math
from random import sample
from typing import List

from beets.library import Item

from beetsplug.beetmatch.musly import MuslyJukebox
from .cooldown import Cooldown
from .playlist_config import PlaylistConfig
from ..jukebox import Jukebox

TOP_N = 5


class MatchItem:
    def __init__(self, item, index, distance):
        self.item = item
        self.index = index
        self.distance = distance


class PlaylistGenerator(object):
    log: logging.Logger
    jukebox: MuslyJukebox
    items: List[Item]
    seed_item: Item
    cooldown: Cooldown

    def __init__(self,
                 jukebox: Jukebox,
                 config: PlaylistConfig,
                 items: List[Item],
                 seed_item: Item,
                 log: logging.Logger = logging.getLogger("beetmatch:generator")):
        self.log = log
        self.items = list(items)
        self.distance_measure = config.create_playlist_distance(jukebox=jukebox.musly_jukebox)
        self.cooldown = config.playlist_cooldown
        self.seed_item = seed_item

        jukebox.init_musly_jukebox(items + [seed_item])

    def __iter__(self):
        return self

    def __next__(self):
        if not self.items:
            raise StopIteration

        self.cooldown.update(self.seed_item)

        most_similar_items = []
        for index, item in enumerate(self.items):
            if self.cooldown.should_skip(item):
                continue

            distance = self.distance_measure(self.seed_item, item)
            if not math.isnan(distance):
                most_similar_items.append(MatchItem(item, index, distance))

        if not most_similar_items:
            raise StopIteration

        selected = _pick_random_match_with_bias(most_similar_items)

        del self.items[selected.index]

        self.seed_item = selected.item
        return selected.item, selected.distance


def _pick_random_match_with_bias(items: list[MatchItem]):
    if len(items) == 1:
        return items[0]

    items.sort(key=lambda i: i.distance, reverse=True)

    top_n = max(TOP_N, len(items))
    max_distance = max(items[-top_n].distance, percentile(items, 0.99))

    selection_pool = sorted([item for item in items if item.distance <= max_distance], key=lambda i: i.distance,
                            reverse=True)

    counts_by_distance = [max(1, int(100 * (1 - (item.distance / max_distance)))) for item in selection_pool]
    pick = sample(selection_pool, counts=counts_by_distance, k=1)

    return pick[0]


def percentile(items, p, key=lambda i: i.distance):
    if not items:
        return None

    k = (len(items) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)

    if f == c:
        return key(items[int(k)])

    d0 = key(items[int(f)])
    d1 = key(items[int(c)])
    return (d0 + d1) / 2

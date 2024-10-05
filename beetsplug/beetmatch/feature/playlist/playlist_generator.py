import logging

from beets.library import Item

from beetsplug.beetmatch.common import pick_random_item
from beetsplug.beetmatch.musly import MuslyJukebox
from .cooldown import Cooldown
from .playlist_config import PlaylistConfig
from ..jukebox import Jukebox

TOP_N = 10


class MatchItem:
    def __init__(self, item, index, distance):
        self.item = item
        self.index = index
        self.distance = distance


class PlaylistGenerator(object):
    log: logging.Logger
    jukebox: MuslyJukebox
    items: list[Item]
    seed_item: Item
    cooldown: Cooldown

    def __init__(self,
                 jukebox: Jukebox,
                 config: PlaylistConfig,
                 items: list[Item],
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
            if len(most_similar_items) < TOP_N or distance <= most_similar_items[-1].distance:
                most_similar_items.append(MatchItem(item, index, distance))
                most_similar_items.sort(key=lambda m: m.distance)
                max_distance = most_similar_items[min(len(most_similar_items), TOP_N) - 1].distance
                most_similar_items = [m for m in most_similar_items if m.distance <= max_distance]

        if not most_similar_items:
            raise StopIteration

        selected, _ = pick_random_item(most_similar_items)
        del self.items[selected.index]

        self.seed_item = selected.item
        return self.seed_item, selected.distance

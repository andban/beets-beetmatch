from typing import List, Dict

from beets.library import Item


class Cooldown(object):
    last_seen: List[Dict[str, any]] = []
    attr_cooldowns: Dict[str, int]
    max_cooldown: int

    def __init__(self, attr_cooldowns: Dict[str, int]):
        self.max_cooldown = max(attr_cooldowns.values())
        self.attr_cooldowns = dict(attr_cooldowns)

    def should_skip(self, item: Item):
        if self.max_cooldown == 0:
            return False

        last_seen_count = len(self.last_seen)
        if not last_seen_count:
            return False

        for attr, cooldown in self.attr_cooldowns.items():
            n = min(cooldown, last_seen_count)
            last_values = [seen.get(attr) for seen in self.last_seen[-n:]]
            if item.get(attr) in last_values:
                return True

        return False

    def update(self, last_item: Item):
        if self.max_cooldown == 0:
            return

        values = dict([(attr, last_item.get(attr)) for attr in self.attr_cooldowns.keys()])

        self.last_seen.append(values)
        if len(self.last_seen) > self.max_cooldown:
            self.last_seen = self.last_seen[-self.max_cooldown:]

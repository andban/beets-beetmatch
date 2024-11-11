import logging
import math
from typing import List

from beets.library import Item

from .cooldown import Cooldown
from .playlist_config import PlaylistConfig
from .track_selector import TrackSelector, TrackCandidate
from ..jukebox import Jukebox


class PlaylistGenerator(object):
    log: logging.Logger
    items: List[Item]
    seed_item: Item
    cooldown: Cooldown
    candidate_chooser: TrackSelector

    def __init__(
            self,
            jukebox: Jukebox,
            config: PlaylistConfig,
            items: List[Item],
            seed_item: Item,
            candidate_chooser: TrackSelector,
            log: logging.Logger = logging.getLogger("beetmatch:generator"),
    ):
        self.log = log
        self.items = list(items)
        self.similarity_measure = config.create_similarity_measure(
            jukebox=jukebox.musly_jukebox
        )
        self.cooldown = config.playlist_cooldown
        self.seed_item = seed_item
        self.candidate_chooser = candidate_chooser

        jukebox.init_musly_jukebox(items + [seed_item])

    def __iter__(self):
        return self

    def __next__(self):
        if not self.items:
            raise StopIteration

        self.cooldown.update(self.seed_item)

        candidates = []
        for index, item in enumerate(self.items):
            if self.cooldown.should_skip(item):
                continue

            similarity = self.similarity_measure(self.seed_item, item)
            if not math.isnan(similarity):
                candidates.append(
                    TrackCandidate(index=index, item=item, similarity=similarity)
                )

        if not candidates:
            raise StopIteration

        selected_candidate = self.candidate_chooser.choose_from(candidates)

        del self.items[selected_candidate.index]

        self.seed_item = selected_candidate.item
        return selected_candidate.item, selected_candidate.similarity

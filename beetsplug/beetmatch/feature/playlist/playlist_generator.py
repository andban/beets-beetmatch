import logging
import math
from abc import abstractmethod
from random import sample
from typing import List, NamedTuple

from beets.library import Item

from beetsplug.beetmatch.musly import MuslyJukebox
from .cooldown import Cooldown
from .playlist_config import PlaylistConfig
from ..jukebox import Jukebox
from ...common import default_logger, normalize, bisect_left

TOP_N = 5


class PlaylistCandidate(NamedTuple):
    index: int
    item: Item
    similarity: float


class PlaylistChooser:
    @abstractmethod
    def choose_candidate(self, candidates: List[PlaylistCandidate], **kwargs):
        pass


class BiasedPlaylistChooser(PlaylistChooser):
    def __init__(self, log=default_logger):
        self.log = log

    def choose_candidate(self, candidates: List[PlaylistCandidate], min_value=None, max_value=None):
        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        min_value = min_value if min_value is not None else min(candidates, key=lambda c: c.similarity).similarity
        max_value = max_value if max_value is not None else max(candidates, key=lambda c: c.similarity).similarity

        candidates_ranked = [(c, normalize(c.similarity, low=min_value, high=max_value)) for c in candidates]
        candidates_ranked.sort(key=lambda p: p[1])

        rank_threshold = 0.8
        first_candidate_index = len(candidates_ranked)
        while len(candidates_ranked) - first_candidate_index < 10 and first_candidate_index > 0:
            first_candidate_index = bisect_left(candidates_ranked, rank_threshold, key=lambda cr: cr[1])
            rank_threshold -= 0.02

        if first_candidate_index < 1:
            first_candidate_index = 1

        similar_candidates, similar_ranks = zip(*candidates_ranked[first_candidate_index:])

        min_rank = candidates_ranked[first_candidate_index - 1][1]
        max_rank = similar_ranks[-1]

        counts = [int(99 * normalize(c, low=min_rank, high=max_rank)) + 1 for c in similar_ranks]

        return sample(similar_candidates, counts=counts, k=1)[0]


class PlaylistGenerator(object):
    log: logging.Logger
    jukebox: MuslyJukebox
    items: List[Item]
    seed_item: Item
    cooldown: Cooldown
    candidate_chooser: PlaylistChooser

    def __init__(self,
                 jukebox: Jukebox,
                 config: PlaylistConfig,
                 items: List[Item],
                 seed_item: Item,
                 log: logging.Logger = logging.getLogger("beetmatch:generator")):
        self.log = log
        self.items = list(items)
        self.similarity_measure = config.create_similarity_measure(jukebox=jukebox.musly_jukebox)
        self.cooldown = config.playlist_cooldown
        self.seed_item = seed_item

        jukebox.init_musly_jukebox(items + [seed_item])

        self.candidate_chooser = BiasedPlaylistChooser()

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
                candidates.append(PlaylistCandidate(index=index, item=item, similarity=similarity))

        if not candidates:
            raise StopIteration

        selected_candidate = self.candidate_chooser.choose_candidate(candidates)

        del self.items[selected_candidate.index]

        self.seed_item = selected_candidate.item
        return selected_candidate.item, selected_candidate.similarity

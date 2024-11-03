from logging import Logger
from operator import itemgetter
from random import sample
from typing import List

from beets.library import Item
from more_itertools.more import first
from typing_extensions import TypedDict, NamedTuple

from beetsplug.beetmatch.common import default_logger, bisect_left
from beetsplug.beetmatch.common.helpers import extent, normalize


class TrackSelectorConfig(TypedDict):
    pickiness: float
    minimum_pool_size: int


class TrackCandidate(NamedTuple):
    index: int
    item: Item
    similarity: float


class TrackSelector:
    _pickiness: float
    _min_pool_size: int
    _log: Logger

    def __init__(self, config: TrackSelectorConfig, log=default_logger):
        self._pickiness = config.get("pickiness", 0.9)
        self._min_pool_size = config.get("minimum_pool_size", 1)
        self._log = log

    def choose_from(self, candidates: List[TrackCandidate]):
        self._log.debug("selecting next track from a list of %d candidates...", len(candidates))

        if not candidates:
            self._log.debug("no candidates to select, returning None")
            return None

        if len(candidates) == 1:
            self._log.debug("only one candidate left, selecting that one")
            return candidates[0]

        min_similarity, max_similarity = extent([c.similarity for c in candidates])
        normed_candidates = [
            (c, normalize(c.similarity, low=min_similarity, high=max_similarity))
            for c in candidates
        ]
        normed_candidates.sort(key=itemgetter(1))

        self._log.debug("candidate similarity range: [%.3f, %.3f]", min_similarity, max_similarity)

        # pick only candidates with normalized similarity >= _pickiness,
        # but if that means less candidates than _min_pool_size, get a bit less picky
        adjusted_pickiness = self._pickiness
        first_relevant_index = len(normed_candidates) - 1
        while first_relevant_index > 0:
            if len(normed_candidates) - first_relevant_index >= self._min_pool_size:
                break

            first_relevant_index = bisect_left(normed_candidates, adjusted_pickiness, key=itemgetter(1))
            if len(normed_candidates) - first_relevant_index < self._min_pool_size:
                adjusted_pickiness -= 0.01

        if first_relevant_index < 1:
            first_relevant_index = 1

        candidate_pool, candidate_probability = zip(*normed_candidates[first_relevant_index:])
        min_pool_probability = normed_candidates[first_relevant_index - 1][1]
        sample_biases = [
            int(99 * normalize(p, low=min_pool_probability, high=1.0)) + 1
            for p in candidate_probability
        ]

        self._log.debug(
            "selected a pool of %d candidates (minimum is %d) with a pickiness of %.2f (requested was %.2f) "
            "with similarity in range [%.3f, %.3f]",
            len(candidate_pool), self._min_pool_size, adjusted_pickiness, self._pickiness, candidate_pool[0].similarity,
            candidate_pool[-1].similarity)

        return first(sample(candidate_pool, counts=sample_biases, k=1))

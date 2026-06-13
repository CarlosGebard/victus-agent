from __future__ import annotations

import math

from victus_routing.embeddings import Embedder, embed_many
from victus_routing.models import IntentScore
from victus_routing.prototype_store import IntentPrototype, PrototypeStore, ScoreWeights


class IntentScorer:
    def __init__(self, embedder: Embedder, prototype_store: PrototypeStore, weights: ScoreWeights) -> None:
        self.embedder = embedder
        self.prototype_store = prototype_store
        self.weights = weights
        self._embedded = {
            prototype.intent_type: _EmbeddedPrototype(
                prototype=prototype,
                definitions=embed_many(embedder, prototype.definition),
                positives=embed_many(embedder, prototype.positive_examples),
                negatives=embed_many(embedder, prototype.negative_examples),
                boundaries=embed_many(embedder, prototype.boundary_examples),
            )
            for prototype in prototype_store.intents
        }

    def score(self, normalized_text: str) -> list[IntentScore]:
        input_embedding = self.embedder.embed(normalized_text)
        scores = [self._score_one(input_embedding, embedded) for embedded in self._embedded.values()]
        return sorted(scores, key=lambda item: item.score, reverse=True)

    def _score_one(self, input_embedding: list[float], embedded: "_EmbeddedPrototype") -> IntentScore:
        positive_score = _max_cosine(input_embedding, embedded.positives)
        definition_score = _max_cosine(input_embedding, embedded.definitions)
        boundary_score = _max_cosine(input_embedding, embedded.boundaries)
        negative_score = _max_cosine(input_embedding, embedded.negatives)

        score = (
            self.weights.positive * positive_score
            + self.weights.definition * definition_score
            + self.weights.boundary * boundary_score
            - self.weights.negative_penalty * negative_score
        )

        return IntentScore(
            intent_type=embedded.prototype.intent_type,
            route=embedded.prototype.route,
            score=score,
            positive_score=positive_score,
            definition_score=definition_score,
            boundary_score=boundary_score,
            negative_score=negative_score,
        )


class _EmbeddedPrototype:
    def __init__(
        self,
        prototype: IntentPrototype,
        definitions: list[list[float]],
        positives: list[list[float]],
        negatives: list[list[float]],
        boundaries: list[list[float]],
    ) -> None:
        self.prototype = prototype
        self.definitions = definitions
        self.positives = positives
        self.negatives = negatives
        self.boundaries = boundaries


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have the same dimensions")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    dot = sum(left_value * right_value for left_value, right_value in zip(left, right))
    return dot / (left_norm * right_norm)


def _max_cosine(input_embedding: list[float], candidates: list[list[float]]) -> float:
    if not candidates:
        return 0.0
    return max(cosine_similarity(input_embedding, candidate) for candidate in candidates)

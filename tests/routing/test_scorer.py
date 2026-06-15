from application.routing.prototype_store import IntentPrototype, PrototypeStore, ScoreWeights
from application.routing.scorer import IntentScorer, cosine_similarity


class StaticEmbedder:
    vectors = {
        "input": [1.0, 0.0],
        "positive": [1.0, 0.0],
        "definition": [0.8, 0.6],
        "boundary": [0.6, 0.8],
        "negative": [0.0, 1.0],
    }

    def embed(self, text: str) -> list[float]:
        return self.vectors[text]


def test_cosine_similarity() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_scorer_uses_positive_definition_boundary_and_negative() -> None:
    store = PrototypeStore(
        "victus-router-v1",
        [
            IntentPrototype(
                intent_type="new_plan",
                route="PlanningSessionGraph",
                definition=["definition"],
                positive_examples=["positive"],
                negative_examples=["negative"],
                boundary_examples=["boundary"],
            )
        ],
    )
    weights = ScoreWeights(
        positive=0.45,
        definition=0.20,
        boundary=0.15,
        context=0.10,
        entity_signal=0.10,
        negative_penalty=0.25,
    )
    score = IntentScorer(StaticEmbedder(), store, weights).score("input")[0]
    assert score.positive_score == 1.0
    assert score.definition_score == 0.8
    assert score.boundary_score == 0.6
    assert score.negative_score == 0.0
    assert score.score == 0.7000000000000001

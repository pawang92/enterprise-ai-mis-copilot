from app.knowledge.rag_evaluation import evaluate_retrieval


class FakeRAG:
    def __init__(self, responses):
        self.responses = responses

    def retrieve(self, query, top_k=3):
        return self.responses.get(query, [])[:top_k]


def test_evaluation_computes_hit_rate_mrr_and_no_answer_accuracy():
    cases = [
        {"id": "inventory", "query": "inventory policy", "expected_sources": ["inventory_sop.md"]},
        {"id": "sales", "query": "sales decline", "expected_sources": ["sales_sop.md"]},
        {"id": "none", "query": "unanswerable", "expected_sources": []},
    ]
    rag = FakeRAG({
        "inventory policy": [
            {"source": "sales_sop.md", "score": 0.4},
            {"source": "inventory_sop.md", "score": 0.3},
        ],
        "sales decline": [{"source": "sales_sop.md", "score": 0.9}],
        "unanswerable": [],
    })
    result = evaluate_retrieval(cases, rag=rag, k=2)
    assert result["hit_rate_at_2"] == 1.0
    assert result["mrr_at_2"] == 0.75
    assert result["no_answer_accuracy"] == 1.0
    assert result["results"][0]["reciprocal_rank_at_2"] == 0.5


def test_evaluation_rejects_non_positive_k():
    try:
        evaluate_retrieval([], rag=FakeRAG({}), k=0)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "k" in str(exc)

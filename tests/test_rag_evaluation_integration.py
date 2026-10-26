from app.knowledge.rag_evaluation import evaluate_retrieval, load_evaluation_cases


def test_labelled_rag_benchmark_runs_with_expected_case_count():
    cases = load_evaluation_cases()
    assert len(cases) >= 5
    result = evaluate_retrieval(cases, k=3)
    assert result["case_count"] == len(cases)
    assert result["answerable_case_count"] > 0
    assert result["no_answer_case_count"] > 0
    assert 0.0 <= result["overall_case_pass_rate"] <= 1.0
    assert 0.0 <= result["no_answer_accuracy"] <= 1.0
    assert len(result["results"]) == len(cases)

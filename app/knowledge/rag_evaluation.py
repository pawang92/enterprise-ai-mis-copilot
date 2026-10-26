from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.knowledge.rag import LocalRAG

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CASES_PATH = ROOT_DIR / "evaluation" / "rag_test_cases.json"


def load_evaluation_cases(path: str | Path = DEFAULT_CASES_PATH) -> list[dict[str, Any]]:
    """Load small, version-controlled retrieval evaluation cases."""
    with Path(path).open("r", encoding="utf-8") as handle:
        cases = json.load(handle)
    if not isinstance(cases, list):
        raise ValueError("RAG evaluation file must contain a JSON list.")
    for index, case in enumerate(cases):
        if not isinstance(case, dict) or not case.get("query"):
            raise ValueError(f"Evaluation case {index} must have a non-empty query.")
        if not isinstance(case.get("expected_sources"), list):
            raise ValueError(f"Evaluation case {index} needs expected_sources as a list.")
    return cases


def evaluate_retrieval(
    cases: list[dict[str, Any]] | None = None,
    *,
    rag: LocalRAG | None = None,
    k: int = 3,
) -> dict[str, Any]:
    """Evaluate source retrieval with hit rate, MRR, precision and no-answer accuracy."""
    if k < 1:
        raise ValueError("k must be at least 1.")
    cases = load_evaluation_cases() if cases is None else cases
    rag = LocalRAG() if rag is None else rag
    rows: list[dict[str, Any]] = []
    answerable_hits: list[float] = []
    reciprocal_ranks: list[float] = []
    precisions: list[float] = []
    no_answer_results: list[float] = []

    for case in cases:
        expected = set(case["expected_sources"])
        retrieved = rag.retrieve(case["query"], top_k=k)
        retrieved_sources = [item["source"] for item in retrieved]
        relevant_rank = next(
            (rank for rank, source in enumerate(retrieved_sources, start=1)
             if source in expected),
            None,
        )

        if expected:
            hit = float(relevant_rank is not None)
            answerable_hits.append(hit)
            reciprocal_ranks.append(1.0 / relevant_rank if relevant_rank else 0.0)
            precision = len(set(retrieved_sources) & expected) / k
            precisions.append(precision)
            no_answer_correct = None
        else:
            hit = None
            precision = None
            no_answer_correct = float(len(retrieved_sources) == 0)
            no_answer_results.append(no_answer_correct)

        rows.append({
            "case_id": case.get("id", case["query"]),
            "query": case["query"],
            "expected_sources": sorted(expected),
            "retrieved_sources": retrieved_sources,
            f"hit_at_{k}": hit,
            f"reciprocal_rank_at_{k}": (
                1.0 / relevant_rank if relevant_rank else 0.0
            ) if expected else None,
            f"precision_at_{k}": precision,
            "no_answer_correct": no_answer_correct,
            "passed": (
                bool(hit) if expected else bool(no_answer_correct)
            ),
        })

    mean = lambda values: round(sum(values) / len(values), 4) if values else None
    return {
        "k": k,
        "case_count": len(rows),
        "answerable_case_count": len(answerable_hits),
        "no_answer_case_count": len(no_answer_results),
        f"hit_rate_at_{k}": mean(answerable_hits),
        f"mrr_at_{k}": mean(reciprocal_ranks),
        f"precision_at_{k}": mean(precisions),
        "no_answer_accuracy": mean(no_answer_results),
        "overall_case_pass_rate": mean([float(row["passed"]) for row in rows]),
        "results": rows,
        "notes": [
            "These metrics evaluate retrieval against a small hand-labelled demo set.",
            "They do not measure answer factuality, faithfulness, or production performance.",
            "Review and version evaluation cases whenever the knowledge base changes.",
        ],
    }

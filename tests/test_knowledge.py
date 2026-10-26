from app.knowledge.rag import LocalRAG
from app.knowledge.graph import BusinessKnowledgeGraph
from app.agents.workflow import ask_copilot, route_request


def test_rag_retrieves_inventory_policy():
    rag = LocalRAG()
    results = rag.retrieve("What should we do when inventory is low?")
    assert results
    assert all("source" in item and "score" in item for item in results)


def test_rag_returns_empty_for_unrelated_question():
    rag = LocalRAG()
    assert rag.retrieve("quantum spacecraft archaeology zebra") == []


def test_knowledge_graph_finds_product_category():
    graph = BusinessKnowledgeGraph()
    results = graph.query("Which category does MED001 belong to?")
    assert any(
        item["subject"] == "MED001"
        and item["relation"] == "belongs_to"
        and item["object"] == "Cardiology"
        for item in results
    )


def test_copilot_routes_policy_question_to_rag():
    result = ask_copilot("What is the inventory policy?")
    assert result["route"] == "rag"
    assert result["result"]["type"] == "rag"


def test_copilot_routes_report_question_to_report():
    result = route_request({"question": "Generate the latest MIS report"})
    assert result["route"] == "report"


def test_copilot_routes_inventory_question_to_analytics():
    result = ask_copilot("Show inventory risks")
    assert result["route"] == "analytics"
    assert result["result"]["type"] == "inventory_risks"


def test_copilot_rejects_empty_question():
    try:
        ask_copilot("   ")
        assert False, "Expected ValueError"
    except ValueError:
        pass

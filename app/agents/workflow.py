from typing import TypedDict, Any

from langgraph.graph import StateGraph, START, END

from app.config import RAW_DIR
from app.data.loader import load_tables
from app.analytics.kpis import monthly_kpis
from app.analytics.anomalies import detect_sales_declines
from app.knowledge.rag import LocalRAG
from app.knowledge.graph import BusinessKnowledgeGraph
import math
from app.analytics.anomalies import (
    detect_sales_declines,
    detect_inventory_risks,
)
from app.reporting.mis_report import build_mis_report
from app.config import RAW_DIR, REPORTS_DIR

def make_json_safe(value):
    """Convert NumPy/Pandas values and non-finite floats to JSON-safe values."""
    import numpy as np
    import pandas as pd

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [make_json_safe(item) for item in value]

    if value is None or value is pd.NA or value is pd.NaT:
        return None

    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(float(value)) else None

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.bool_):
        return bool(value)

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    return value


class CopilotState(TypedDict, total=False):
    question: str
    route: str
    result: dict[str, Any]


def route_request(state: CopilotState):
    question = state["question"].lower()

    if any(word in question for word in [
        "policy", "sop", "procedure", "governance", "rules"
    ]):
        route = "rag"

    elif any(word in question for word in [
        "relationship", "related to", "belongs to",
        "connected", "knowledge graph"
    ]):
        route = "graph"

    else:
        route = "analytics"

    return {"route": route}


def run_analytics(state: CopilotState):
    tables = load_tables(RAW_DIR)
    question = state["question"].lower()

    if any(word in question for word in [
        "anomaly", "anomalies", "decline",
        "drop", "investigate", "exception"
    ]):
        anomalies = detect_sales_declines(tables["sales"])

        rows = anomalies[
            ["month", "product_id", "region", "change_pct"]
        ].copy()

        rows["month"] = rows["month"].astype(str)

        return {
            "result": {
                "type": "sales_anomalies",
                "count": len(rows),
                "records": rows.head(20).to_dict(orient="records"),
            }
        }

    kpis = monthly_kpis(tables["sales"], tables["targets"])
    kpis["month"] = kpis["month"].astype(str)

    return {
        "result": {
            "type": "monthly_kpis",
            "records": kpis.tail(12).to_dict(orient="records"),
        }
    }


def run_rag(state: CopilotState):
    rag = LocalRAG()
    return {
        "result": {
            "type": "rag",
            **rag.answer(state["question"]),
        }
    }


def run_graph(state: CopilotState):
    graph = BusinessKnowledgeGraph()

    return {
        "result": {
            "type": "knowledge_graph",
            "records": graph.query(state["question"]),
        }
    }


def build_workflow():
    builder = StateGraph(CopilotState)

    builder.add_node("router", route_request)
    builder.add_node("analytics", run_analytics)
    builder.add_node("rag", run_rag)
    builder.add_node("graph", run_graph)

    builder.add_edge(START, "router")

    builder.add_conditional_edges(
        "router",
        lambda state: state["route"],
        {
            "analytics": "analytics",
            "rag": "rag",
            "graph": "graph",
        },
    )

    builder.add_edge("analytics", END)
    builder.add_edge("rag", END)
    builder.add_edge("graph", END)

    return builder.compile()


copilot_workflow = build_workflow()


def ask_copilot(question: str):
    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    result = copilot_workflow.invoke({
        "question": question,
    })

    return make_json_safe(result)

def run_report(state: CopilotState):
    tables = load_tables(RAW_DIR)

    kpis = monthly_kpis(
        tables["sales"],
        tables["targets"],
    )

    sales_risks = detect_sales_declines(
        tables["sales"]
    )

    inventory_risks = detect_inventory_risks(
        tables["inventory"]
    )

    report_path = build_mis_report(
        tables,
        REPORTS_DIR,
    )

    latest = kpis.sort_values("month").iloc[-1]

    return {
        "result": {
            "type": "mis_report",
            "report_path": str(report_path.resolve()),
            "latest_month": str(latest["month"]),
            "latest_revenue": float(latest["revenue"]),
            "target_attainment_pct": float(
                latest["target_attainment_pct"]
            ),
            "sales_anomaly_count": int(len(sales_risks)),
            "inventory_risk_count": int(len(inventory_risks)),
            "message": (
                "MIS report generated. Review the report "
                "and investigate the identified risks."
            ),
        }
    }
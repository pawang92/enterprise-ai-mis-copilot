from __future__ import annotations

import math
from typing import Any, TypedDict

import numpy as np
import pandas as pd
from langgraph.graph import END, START, StateGraph

from app.analytics.anomalies import (
    detect_inventory_risks,
    detect_sales_declines,
)
from app.analytics.kpis import monthly_kpis
from app.config import RAW_DIR, REPORTS_DIR
from app.data.loader import load_tables
from app.knowledge.graph import BusinessKnowledgeGraph
from app.knowledge.rag import LocalRAG
from app.reporting.mis_report import build_mis_report


class CopilotState(TypedDict, total=False):
    question: str
    route: str
    result: dict[str, Any]


def make_json_safe(value: Any) -> Any:
    """Convert common NumPy/Pandas values and NaN/Infinity to JSON-safe values."""
    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [make_json_safe(item) for item in value]
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, (float, np.floating)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def route_request(state: CopilotState) -> dict[str, str]:
    question = state["question"].strip().lower()

    # Report intent must be checked before generic analytics terms such as "sales".
    if any(term in question for term in (
        "report", "mis", "management summary",
    )):
        return {"route": "report"}

    if any(term in question for term in (
        "policy", "sop", "procedure", "governance", "rules",
    )):
        return {"route": "rag"}

    if any(term in question for term in (
        "relationship", "related to", "belongs to",
        "connected", "knowledge graph", "category does",
    )):
        return {"route": "graph"}

    return {"route": "analytics"}


def run_analytics(state: CopilotState) -> dict[str, Any]:
    tables = load_tables(RAW_DIR)
    question = state["question"].lower()

    if any(term in question for term in (
        "inventory", "stock", "low-stock", "low stock",
    )):
        risks = detect_inventory_risks(tables["inventory"])
        columns = [
            column for column in (
                "snapshot_date", "product_id", "region", "stock_units",
                "days_of_inventory", "reorder_level_units",
                "low_inventory_cover", "below_reorder_level",
            )
            if column in risks.columns
        ]
        records = risks[columns].copy()
        if "snapshot_date" in records.columns:
            records["snapshot_date"] = records["snapshot_date"].astype(str)
        return {
            "result": {
                "type": "inventory_risks",
                "count": len(records),
                "records": records.head(50).to_dict(orient="records"),
            }
        }

    if any(term in question for term in (
        "anomaly", "anomalies", "decline", "drop",
        "investigate", "exception",
    )):
        anomalies = detect_sales_declines(tables["sales"])
        rows = anomalies[
            ["month", "product_id", "region", "revenue", "baseline_revenue", "change_pct"]
        ].copy()
        rows["month"] = rows["month"].astype(str)
        return {
            "result": {
                "type": "sales_anomalies",
                "count": len(rows),
                "records": rows.head(50).to_dict(orient="records"),
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


def run_rag(state: CopilotState) -> dict[str, Any]:
    rag = LocalRAG()
    return {"result": {"type": "rag", **rag.answer(state["question"])}}


def run_graph(state: CopilotState) -> dict[str, Any]:
    graph = BusinessKnowledgeGraph()
    return {
        "result": {
            "type": "knowledge_graph",
            "records": graph.query(state["question"]),
        }
    }


def run_report(state: CopilotState) -> dict[str, Any]:
    tables = load_tables(RAW_DIR)
    kpis = monthly_kpis(tables["sales"], tables["targets"])
    sales_risks = detect_sales_declines(tables["sales"])
    inventory_risks = detect_inventory_risks(tables["inventory"])
    report_path = build_mis_report(tables, REPORTS_DIR)

    latest = kpis.sort_values("month").iloc[-1]
    return {
        "result": {
            "type": "mis_report",
            "report_path": str(report_path.resolve()),
            "latest_month": str(pd.Timestamp(latest["month"]).strftime("%Y-%m")),
            "latest_revenue": float(latest["revenue"]),
            "target_attainment_pct": float(latest["target_attainment_pct"]),
            "sales_anomaly_count": int(len(sales_risks)),
            "inventory_risk_count": int(len(inventory_risks)),
            "message": (
                "MIS report generated. Review the report and investigate "
                "the identified risks; statistical alerts do not establish cause."
            ),
        }
    }


def build_workflow():
    builder = StateGraph(CopilotState)
    builder.add_node("router", route_request)
    builder.add_node("analytics", run_analytics)
    builder.add_node("rag", run_rag)
    builder.add_node("graph", run_graph)
    builder.add_node("report", run_report)

    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        "router",
        lambda state: state["route"],
        {
            "analytics": "analytics",
            "rag": "rag",
            "graph": "graph",
            "report": "report",
        },
    )

    for node in ("analytics", "rag", "graph", "report"):
        builder.add_edge(node, END)

    return builder.compile()


copilot_workflow = build_workflow()


def ask_copilot(question: str) -> dict[str, Any]:
    question = question.strip()
    if not question:
        raise ValueError("Question cannot be empty.")
    result = copilot_workflow.invoke({"question": question})
    return make_json_safe(result)

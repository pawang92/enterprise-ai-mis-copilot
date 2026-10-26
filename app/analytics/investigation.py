from __future__ import annotations

from typing import Any

import pandas as pd

from app.analytics.anomalies import detect_inventory_risks, detect_sales_declines
from app.knowledge.rag import LocalRAG


def build_investigation(
    tables: dict[str, pd.DataFrame],
    *,
    product_id: str | None = None,
    region: str | None = None,
    sales_threshold_pct: float = -20.0,
    low_inventory_days: int = 7,
    top_k_evidence: int = 3,
    rag: LocalRAG | None = None,
) -> dict[str, Any]:
    """Correlate observed sales/inventory signals with traceable SOP evidence.

    This function assembles evidence for human review. It does not infer a
    causal explanation or initiate operational actions.
    """
    sales = tables["sales"].copy()
    inventory = tables["inventory"].copy()
    if product_id:
        sales = sales[sales["product_id"].astype(str) == str(product_id)]
        inventory = inventory[inventory["product_id"].astype(str) == str(product_id)]
    if region:
        sales = sales[sales["region"].astype(str).str.casefold() == region.casefold()]
        inventory = inventory[inventory["region"].astype(str).str.casefold() == region.casefold()]

    anomalies = detect_sales_declines(sales, threshold_pct=sales_threshold_pct)

    if not inventory.empty and "snapshot_date" in inventory.columns:
        inventory["snapshot_date"] = pd.to_datetime(inventory["snapshot_date"])
        latest_by_group = inventory.groupby(
            ["product_id", "region"]
        )["snapshot_date"].transform("max")
        latest_inventory = inventory[inventory["snapshot_date"] == latest_by_group].copy()
    else:
        latest_inventory = inventory.copy()

    inventory_risks = detect_inventory_risks(
        latest_inventory, low_days_threshold=low_inventory_days
    )
    inventory_columns = [
        c for c in (
            "product_id", "region", "snapshot_date", "stock_units",
            "days_of_inventory", "reorder_level_units",
        ) if c in latest_inventory.columns
    ]
    latest_records = latest_inventory[inventory_columns].copy()
    risk_keys = set(
        zip(inventory_risks.get("product_id", []), inventory_risks.get("region", []))
    )

    if rag is None:
        rag = LocalRAG()

    findings: list[dict[str, Any]] = []
    for row in anomalies.to_dict(orient="records"):
        key = (row["product_id"], row["region"])
        inv_rows = latest_records[
            (latest_records["product_id"] == row["product_id"])
            & (latest_records["region"] == row["region"])
        ]
        inv = inv_rows.iloc[0].to_dict() if not inv_rows.empty else {}
        evidence = rag.retrieve(
            "sales decline investigation historical baseline regional trends "
            "product availability sales targets data quality",
            top_k=top_k_evidence,
        )
        findings.append({
            "signal_type": "sales_decline",
            "month": pd.Timestamp(row["month"]).strftime("%Y-%m"),
            "product_id": str(row["product_id"]),
            "region": str(row["region"]),
            "actual_revenue": float(row["revenue"]),
            "baseline_revenue": float(row["baseline_revenue"]),
            "change_pct": float(row["change_pct"]),
            "inventory_snapshot": {
                "snapshot_date": (
                    pd.Timestamp(inv["snapshot_date"]).strftime("%Y-%m-%d")
                    if inv.get("snapshot_date") is not None
                    and not pd.isna(inv.get("snapshot_date"))
                    else None
                ),
                "stock_units": _safe_number(inv.get("stock_units")),
                "days_of_inventory": _safe_number(inv.get("days_of_inventory")),
                "reorder_level_units": _safe_number(inv.get("reorder_level_units")),
                "risk_detected": key in risk_keys,
            },
            "evidence": [
                {
                    "source": item["source"],
                    "score": item["score"],
                    "excerpt": item["text"][:500],
                }
                for item in evidence
            ],
            "interpretation": (
                "A revenue decline was detected against the prior-period baseline. "
                "Review regional trends, product availability, target changes, and data quality."
            ),
            "limitations": (
                "Association with inventory status is contextual evidence only; "
                "this result does not establish root cause."
            ),
        })

    return {
        "filters": {"product_id": product_id, "region": region},
        "sales_signal_count": int(len(anomalies)),
        "inventory_risk_count": int(len(inventory_risks)),
        "findings": findings,
        "review_guidance": [
            "Validate the source data and comparison baseline.",
            "Compare adjacent regions and products before assigning a cause.",
            "Use cited SOP excerpts as guidance, not proof that a policy caused the event.",
            "Require an authorized business user to approve any operational action.",
        ],
    }


def _safe_number(value: Any) -> float | int | None:
    if value is None or pd.isna(value):
        return None
    numeric = float(value)
    return int(numeric) if numeric.is_integer() else numeric

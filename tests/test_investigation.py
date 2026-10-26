import pandas as pd

from app.analytics.investigation import build_investigation


class FakeRAG:
    def retrieve(self, query, top_k=3):
        return [{
            "source": "sales_sop.md",
            "score": 0.8,
            "text": "Investigate regional trends and product availability.",
        }]


def test_investigation_links_sales_signal_inventory_and_sop_evidence():
    months = pd.date_range("2026-01-01", periods=5, freq="MS")
    sales = pd.DataFrame({
        "month": list(months),
        "product_id": ["MED001"] * 5,
        "region": ["West"] * 5,
        "revenue": [100.0, 100.0, 100.0, 100.0, 60.0],
        "units_sold": [10, 10, 10, 10, 6],
    })
    inventory = pd.DataFrame({
        "snapshot_date": [pd.Timestamp("2026-05-01")],
        "product_id": ["MED001"],
        "region": ["West"],
        "stock_units": [5],
        "days_of_inventory": [4],
        "reorder_level_units": [10],
    })
    targets = pd.DataFrame({
        "month": months,
        "target_revenue": [100.0] * 5,
    })
    result = build_investigation(
        {"sales": sales, "inventory": inventory, "targets": targets, "products": pd.DataFrame()},
        product_id="MED001",
        region="West",
        rag=FakeRAG(),
    )
    assert result["sales_signal_count"] == 1
    finding = result["findings"][0]
    assert finding["product_id"] == "MED001"
    assert finding["change_pct"] == -40.0
    assert finding["inventory_snapshot"]["risk_detected"] is True
    assert finding["evidence"][0]["source"] == "sales_sop.md"
    assert "does not establish root cause" in finding["limitations"]

import pandas as pd
import pytest

from app.analytics.anomalies import detect_inventory_risks, detect_sales_declines
from app.analytics.kpis import monthly_kpis


def test_monthly_kpis_calculates_target_attainment():
    sales = pd.DataFrame({
        "month": pd.to_datetime(["2026-01-01", "2026-02-01"]),
        "revenue": [80.0, 120.0],
        "units_sold": [8, 12],
    })
    targets = pd.DataFrame({
        "month": pd.to_datetime(["2026-01-01", "2026-02-01"]),
        "target_revenue": [100.0, 100.0],
    })
    result = monthly_kpis(sales, targets)
    assert result.loc[0, "target_attainment_pct"] == 80.0
    assert result.loc[1, "target_attainment_pct"] == 120.0


def test_detects_decline_against_prior_three_months():
    sales = pd.DataFrame({
        "month": pd.date_range("2026-01-01", periods=5, freq="MS"),
        "product_id": ["P1"] * 5,
        "region": ["West"] * 5,
        "revenue": [100.0, 100.0, 100.0, 100.0, 60.0],
    })
    result = detect_sales_declines(sales, threshold_pct=-20, window=3)
    assert len(result) == 1
    assert result.iloc[0]["change_pct"] == -40.0


def test_detect_inventory_by_low_cover_and_reorder_level():
    inventory = pd.DataFrame({
        "product_id": ["P1", "P2", "P3"],
        "region": ["West", "South", "East"],
        "stock_units": [100, 50, 100],
        "days_of_inventory": [5, 30, 30],
        "reorder_level_units": [40, 60, 50],
    })
    result = detect_inventory_risks(inventory)
    assert set(result["product_id"]) == {"P1", "P2"}


def test_sales_declines_rejects_invalid_window():
    sales = pd.DataFrame({
        "month": pd.date_range("2026-01-01", periods=4, freq="MS"),
        "product_id": ["P1"] * 4,
        "region": ["West"] * 4,
        "revenue": [100.0, 100.0, 100.0, 50.0],
    })
    with pytest.raises(ValueError, match="window"):
        detect_sales_declines(sales, window=0)

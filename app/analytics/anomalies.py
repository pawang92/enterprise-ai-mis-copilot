import pandas as pd

def detect_sales_declines(
    sales: pd.DataFrame,
    threshold_pct: float = -20.0,
    window: int = 3,
) -> pd.DataFrame:
    """Flag current sales below a trailing baseline, grouped by product and region.

    Baseline uses only prior observations to avoid looking ahead.
    A decline is a signal to investigate, not proof of cause.
    """
    required = {"month", "product_id", "region", "revenue"}
    if missing := required - set(sales.columns):
        raise ValueError(f"sales missing columns: {sorted(missing)}")
    df = sales.copy()
    df["month"] = pd.to_datetime(df["month"])
    df = df.sort_values(["product_id", "region", "month"])
    group = df.groupby(["product_id", "region"])["revenue"]
    df["baseline_revenue"] = group.transform(lambda s: s.shift(1).rolling(window=window, min_periods=window).mean())
    df["change_pct"] = ((df["revenue"] - df["baseline_revenue"]) / df["baseline_revenue"] * 100).round(2)
    df["is_anomaly"] = df["change_pct"] < threshold_pct
    return df[df["is_anomaly"]].reset_index(drop=True)

def detect_inventory_risks(
    inventory: pd.DataFrame,
    low_days_threshold: int = 7,
) -> pd.DataFrame:
    """Identify low inventory cover and stock below reorder levels."""

    required = {
        "product_id",
        "region",
        "stock_units",
        "days_of_inventory",
        "reorder_level_units",
    }

    missing = required - set(inventory.columns)
    if missing:
        raise ValueError(
            f"inventory missing columns: {sorted(missing)}"
        )

    df = inventory.copy()

    df["low_inventory_cover"] = (
        df["days_of_inventory"] <= low_days_threshold
    )

    df["below_reorder_level"] = (
        df["stock_units"] < df["reorder_level_units"]
    )

    df["risk_detected"] = (
        df["low_inventory_cover"] | df["below_reorder_level"]
    )

    return df[df["risk_detected"]].reset_index(drop=True)

def detect_inventory_risks(
    inventory: pd.DataFrame,
    low_days_threshold: int = 7,
) -> pd.DataFrame:
    """Identify low inventory cover and stock below reorder levels."""

    required = {
        "product_id",
        "region",
        "stock_units",
        "days_of_inventory",
        "reorder_level_units",
    }

    missing = required - set(inventory.columns)
    if missing:
        raise ValueError(
            f"inventory missing columns: {sorted(missing)}"
        )

    df = inventory.copy()

    df["low_inventory_cover"] = (
        df["days_of_inventory"] <= low_days_threshold
    )

    df["below_reorder_level"] = (
        df["stock_units"] < df["reorder_level_units"]
    )

    df["risk_detected"] = (
        df["low_inventory_cover"] | df["below_reorder_level"]
    )

    return df[df["risk_detected"]].reset_index(drop=True)

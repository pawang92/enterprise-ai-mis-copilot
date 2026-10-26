import pandas as pd


def detect_sales_declines(
    sales: pd.DataFrame,
    threshold_pct: float = -20.0,
    window: int = 3,
) -> pd.DataFrame:
    """Flag revenue below a trailing baseline by product and region.

    The baseline uses only previous observations. A flagged decline is a
    signal for investigation, not proof of a cause.
    """
    required = {"month", "product_id", "region", "revenue"}
    if missing := required - set(sales.columns):
        raise ValueError(f"sales missing columns: {sorted(missing)}")
    if window < 1:
        raise ValueError("window must be at least 1")

    df = sales.copy()
    df["month"] = pd.to_datetime(df["month"], errors="raise")
    if df["revenue"].isna().any() or (df["revenue"] < 0).any():
        raise ValueError("sales.revenue must be non-null and non-negative")

    df = df.sort_values(["product_id", "region", "month"])
    group = df.groupby(["product_id", "region"])["revenue"]
    df["baseline_revenue"] = group.transform(
        lambda series: series.shift(1).rolling(
            window=window, min_periods=window
        ).mean()
    )
    denominator = df["baseline_revenue"].where(df["baseline_revenue"] != 0)
    df["change_pct"] = (
        (df["revenue"] - df["baseline_revenue"]) / denominator * 100
    ).round(2)
    df["is_anomaly"] = df["change_pct"] < threshold_pct
    return df[df["is_anomaly"]].reset_index(drop=True)


def detect_inventory_risks(
    inventory: pd.DataFrame,
    low_days_threshold: int = 7,
) -> pd.DataFrame:
    """Identify inventory with low days-of-cover or stock below reorder level."""
    required = {
        "product_id",
        "region",
        "stock_units",
        "days_of_inventory",
        "reorder_level_units",
    }
    if missing := required - set(inventory.columns):
        raise ValueError(f"inventory missing columns: {sorted(missing)}")
    if low_days_threshold < 0:
        raise ValueError("low_days_threshold must be non-negative")

    df = inventory.copy()
    for column in ("stock_units", "days_of_inventory", "reorder_level_units"):
        df[column] = pd.to_numeric(df[column], errors="raise")
        if df[column].isna().any() or (df[column] < 0).any():
            raise ValueError(f"inventory.{column} must be non-null and non-negative")

    df["low_inventory_cover"] = df["days_of_inventory"] <= low_days_threshold
    df["below_reorder_level"] = df["stock_units"] < df["reorder_level_units"]
    df["risk_detected"] = df["low_inventory_cover"] | df["below_reorder_level"]
    return df[df["risk_detected"]].reset_index(drop=True)

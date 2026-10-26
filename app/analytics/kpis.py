import pandas as pd


def monthly_kpis(sales: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly revenue/units and calculate target attainment and MoM change."""
    required_sales = {"month", "revenue", "units_sold"}
    required_targets = {"month", "target_revenue"}
    if missing := required_sales - set(sales.columns):
        raise ValueError(f"sales missing required columns: {sorted(missing)}")
    if missing := required_targets - set(targets.columns):
        raise ValueError(f"targets missing required columns: {sorted(missing)}")

    actual = sales.groupby("month", as_index=False).agg(
        revenue=("revenue", "sum"),
        units_sold=("units_sold", "sum"),
    )
    goal = targets.groupby("month", as_index=False).agg(
        target_revenue=("target_revenue", "sum")
    )

    result = actual.merge(goal, on="month", how="left", validate="one_to_one")
    result["target_attainment_pct"] = (
        result["revenue"] / result["target_revenue"].where(result["target_revenue"] != 0) * 100
    ).round(2)
    result["revenue_mom_change_pct"] = result["revenue"].pct_change().mul(100).round(2)
    return result


def product_region_summary(
    sales: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate sales by month/product/region with descriptive product attributes."""
    merged = sales.merge(
        products[["product_id", "product_name", "category"]],
        on="product_id",
        how="left",
        validate="many_to_one",
    )
    return merged.groupby(
        ["month", "region", "product_id", "product_name", "category"],
        as_index=False,
        dropna=False,
    ).agg(
        revenue=("revenue", "sum"),
        units_sold=("units_sold", "sum"),
    )

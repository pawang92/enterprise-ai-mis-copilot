import pandas as pd

def monthly_kpis(sales: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """Aggregate revenue and units; target attainment is calculated from actual totals."""
    actual = sales.groupby("month", as_index=False).agg(
        revenue=("revenue", "sum"),
        units_sold=("units_sold", "sum"),
    )
    goal = targets.groupby("month", as_index=False).agg(target_revenue=("target_revenue", "sum"))
    result = actual.merge(goal, on="month", how="left")
    result["target_attainment_pct"] = (result["revenue"] / result["target_revenue"] * 100).round(2)
    result["revenue_mom_change_pct"] = result["revenue"].pct_change().mul(100).round(2)
    return result

def product_region_summary(sales: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    merged = sales.merge(products[["product_id", "product_name", "category"]], on="product_id", how="left")
    return merged.groupby(["month", "region", "product_id", "product_name", "category"], as_index=False).agg(
        revenue=("revenue", "sum"),
        units_sold=("units_sold", "sum"),
    )

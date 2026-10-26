from pathlib import Path

import numpy as np
import pandas as pd

from app.config import RAW_DIR

PRODUCTS = [
    ("MED001", "Cardiwell 10mg", "Cardiology", 120.0),
    ("MED002", "Glucofine 500mg", "Diabetes Care", 85.0),
    ("MED003", "Respira 5mg", "Respiratory", 95.0),
    ("MED004", "Painrelief 250mg", "Pain Management", 60.0),
    ("MED005", "VitaPlus", "Nutrition", 45.0),
]
REGIONS = ["West", "North", "South", "East"]


def generate_dataset(
    output_dir: str | Path = RAW_DIR,
    seed: int = 42,
) -> dict[str, str]:
    """Create reproducible synthetic pharma-style MIS tables; no real data."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    months = pd.date_range("2025-10-01", periods=12, freq="MS")

    products = pd.DataFrame([
        {
            "product_id": product_id,
            "product_name": name,
            "category": category,
            "unit_price": price,
        }
        for product_id, name, category, price in PRODUCTS
    ])

    sales_rows, inventory_rows, target_rows = [], [], []
    for month_idx, month in enumerate(months):
        for product_id, name, category, price in PRODUCTS:
            for region in REGIONS:
                baseline = int(rng.integers(700, 1500))
                units = max(
                    0,
                    int(baseline * (1 + 0.012 * month_idx) + rng.normal(0, 65)),
                )

                # Inject a reproducible sales decline for anomaly-detection demos.
                if (
                    month.strftime("%Y-%m") == "2026-08"
                    and product_id == "MED002"
                    and region == "West"
                ):
                    units = int(units * 0.55)

                revenue = round(units * price, 2)
                sales_rows.append({
                    "month": month.strftime("%Y-%m-%d"),
                    "product_id": product_id,
                    "region": region,
                    "units_sold": units,
                    "revenue": revenue,
                })
                target_rows.append({
                    "month": month.strftime("%Y-%m-%d"),
                    "product_id": product_id,
                    "region": region,
                    "target_revenue": round(baseline * price * 1.05, 2),
                })

                stock_days = int(rng.integers(8, 85))
                if (
                    month.strftime("%Y-%m") == "2026-09"
                    and product_id == "MED003"
                    and region == "South"
                ):
                    stock_days = 5

                inventory_rows.append({
                    "snapshot_date": month.strftime("%Y-%m-%d"),
                    "product_id": product_id,
                    "region": region,
                    "stock_units": int(units * stock_days / 30),
                    "days_of_inventory": stock_days,
                    "reorder_level_units": int(units * 0.45),
                })

    frames = {
        "products": products,
        "sales": pd.DataFrame(sales_rows),
        "inventory": pd.DataFrame(inventory_rows),
        "targets": pd.DataFrame(target_rows),
    }
    paths = {}
    for name, frame in frames.items():
        path = output_dir / f"{name}.csv"
        frame.to_csv(path, index=False)
        paths[name] = str(path)
    return paths


if __name__ == "__main__":
    for name, path in generate_dataset().items():
        print(f"{name}: {path}")

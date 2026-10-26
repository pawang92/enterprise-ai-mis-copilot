from pathlib import Path
import numpy as np
import pandas as pd

PRODUCTS = [
    ("MED001", "Cardiwell 10mg", "Cardiology", 120.0),
    ("MED002", "Glucofine 500mg", "Diabetes Care", 85.0),
    ("MED003", "Respira 5mg", "Respiratory", 95.0),
    ("MED004", "Painrelief 250mg", "Pain Management", 60.0),
    ("MED005", "VitaPlus", "Nutrition", 45.0),
]
REGIONS = ["West", "North", "South", "East"]

def generate_dataset(output_dir: str | Path = "data/raw", seed: int = 42) -> dict[str, str]:
    """Create reproducible synthetic pharmaceutical MIS data; no real patient data."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    months = pd.date_range("2025-10-01", periods=12, freq="MS")

    product_rows = [
        {"product_id": pid, "product_name": name, "category": category, "unit_price": price}
        for pid, name, category, price in PRODUCTS
    ]
    products = pd.DataFrame(product_rows)
    sales_rows, inventory_rows, target_rows = [], [], []
    for month_idx, month in enumerate(months):
        for pid, name, category, price in PRODUCTS:
            for region in REGIONS:
                baseline = int(rng.integers(700, 1500))
                units = max(0, int(baseline * (1 + 0.012 * month_idx) + rng.normal(0, 65)))
                # Seed intentional anomalies to make the demo meaningful.
                if month.strftime("%Y-%m") == "2026-08" and pid == "MED002" and region == "West":
                    units = int(units * 0.55)
                revenue = round(units * price, 2)
                sales_rows.append({
                    "month": month.strftime("%Y-%m-%d"),
                    "product_id": pid,
                    "region": region,
                    "units_sold": units,
                    "revenue": revenue,
                })
                target_rows.append({
                    "month": month.strftime("%Y-%m-%d"),
                    "product_id": pid,
                    "region": region,
                    "target_revenue": round(baseline * price * 1.05, 2),
                })
                stock_days = int(rng.integers(8, 85))
                if month.strftime("%Y-%m") == "2026-09" and pid == "MED003" and region == "South":
                    stock_days = 5
                inventory_rows.append({
                    "snapshot_date": month.strftime("%Y-%m-%d"),
                    "product_id": pid,
                    "region": region,
                    "stock_units": int(units * stock_days / 30),
                    "days_of_inventory": stock_days,
                    "reorder_level_units": int(units * 0.45),
                })

    paths = {
        "products": output_dir / "products.csv",
        "sales": output_dir / "sales.csv",
        "inventory": output_dir / "inventory.csv",
        "targets": output_dir / "targets.csv",
    }
    products.to_csv(paths["products"], index=False)
    pd.DataFrame(sales_rows).to_csv(paths["sales"], index=False)
    pd.DataFrame(inventory_rows).to_csv(paths["inventory"], index=False)
    pd.DataFrame(target_rows).to_csv(paths["targets"], index=False)
    return {key: str(value) for key, value in paths.items()}

if __name__ == "__main__":
    for name, path in generate_dataset().items():
        print(f"{name}: {path}")

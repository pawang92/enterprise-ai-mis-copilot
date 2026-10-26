from pathlib import Path
import pandas as pd

def load_tables(data_dir: str | Path = "data/raw") -> dict[str, pd.DataFrame]:
    data_dir = Path(data_dir)
    required = ["products", "sales", "inventory", "targets"]
    tables = {}
    for name in required:
        path = data_dir / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing {path}. Run: python -m app.data.generate")
        tables[name] = pd.read_csv(path, parse_dates=["month"] if name in {"sales", "targets"} else (["snapshot_date"] if name == "inventory" else None))
    validate_tables(tables)
    return tables

def validate_tables(tables: dict[str, pd.DataFrame]) -> None:
    expected = {
        "products": {"product_id", "product_name", "category", "unit_price"},
        "sales": {"month", "product_id", "region", "units_sold", "revenue"},
        "inventory": {"snapshot_date", "product_id", "region", "stock_units", "days_of_inventory", "reorder_level_units"},
        "targets": {"month", "product_id", "region", "target_revenue"},
    }
    for name, columns in expected.items():
        missing = columns - set(tables[name].columns)
        if missing:
            raise ValueError(f"{name} is missing required columns: {sorted(missing)}")
    if (tables["sales"]["units_sold"] < 0).any():
        raise ValueError("sales.units_sold cannot be negative")
    if (tables["sales"]["revenue"] < 0).any():
        raise ValueError("sales.revenue cannot be negative")

from pathlib import Path

import pandas as pd

from app.config import RAW_DIR


def load_tables(data_dir: str | Path = RAW_DIR) -> dict[str, pd.DataFrame]:
    data_dir = Path(data_dir)
    required = ["products", "sales", "inventory", "targets"]
    tables: dict[str, pd.DataFrame] = {}

    for name in required:
        path = data_dir / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(
                f"Missing {path}. Run: python -m app.data.generate"
            )
        if name in {"sales", "targets"}:
            parse_dates = ["month"]
        elif name == "inventory":
            parse_dates = ["snapshot_date"]
        else:
            parse_dates = None
        tables[name] = pd.read_csv(path, parse_dates=parse_dates)

    validate_tables(tables)
    return tables


def validate_tables(tables: dict[str, pd.DataFrame]) -> None:
    expected = {
        "products": {"product_id", "product_name", "category", "unit_price"},
        "sales": {"month", "product_id", "region", "units_sold", "revenue"},
        "inventory": {
            "snapshot_date", "product_id", "region", "stock_units",
            "days_of_inventory", "reorder_level_units",
        },
        "targets": {"month", "product_id", "region", "target_revenue"},
    }

    for name, columns in expected.items():
        if name not in tables:
            raise ValueError(f"Missing required table: {name}")
        missing = columns - set(tables[name].columns)
        if missing:
            raise ValueError(f"{name} is missing required columns: {sorted(missing)}")

    numeric_rules = {
        "sales": ["units_sold", "revenue"],
        "products": ["unit_price"],
        "inventory": ["stock_units", "days_of_inventory", "reorder_level_units"],
        "targets": ["target_revenue"],
    }
    for table_name, columns in numeric_rules.items():
        for column in columns:
            numeric = pd.to_numeric(tables[table_name][column], errors="raise")
            if numeric.isna().any():
                raise ValueError(f"{table_name}.{column} cannot contain null values")
            if (numeric < 0).any():
                raise ValueError(f"{table_name}.{column} must be non-negative")

    for table_name, date_column in (
        ("sales", "month"),
        ("targets", "month"),
        ("inventory", "snapshot_date"),
    ):
        if tables[table_name][date_column].isna().any():
            raise ValueError(f"{table_name}.{date_column} cannot contain null values")

    if tables["products"]["product_id"].duplicated().any():
        raise ValueError("products.product_id must be unique")

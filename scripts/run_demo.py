
from pathlib import Path
import sys

# Add project root to Python import path.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import RAW_DIR, REPORTS_DIR
from app.data.generate import generate_dataset
from app.data.loader import load_tables
from app.analytics.kpis import monthly_kpis
from app.analytics.anomalies import detect_sales_declines
from app.reporting.mis_report import build_mis_report


def main():
    # Generate synthetic datasets.
    generate_dataset(RAW_DIR)

    # Load and validate datasets.
    tables = load_tables(RAW_DIR)

    # Calculate KPIs and detect anomalies.
    kpis = monthly_kpis(tables["sales"], tables["targets"])
    anomalies = detect_sales_declines(tables["sales"])

    # Generate MIS report.
    report_path = build_mis_report(tables, REPORTS_DIR)

    print("\nLATEST MONTHLY KPIs")
    print(kpis.tail(3).to_string(index=False))

    print(f"\nSales decline signals detected: {len(anomalies)}")

    if not anomalies.empty:
        print(
            anomalies[
                ["month", "product_id", "region", "change_pct"]
            ].head(10).to_string(index=False)
        )

    print(f"\nMIS report written to: {report_path.resolve()}")


if __name__ == "__main__":
    main()

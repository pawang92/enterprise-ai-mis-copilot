from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from app.analytics.anomalies import detect_inventory_risks, detect_sales_declines
from app.analytics.kpis import monthly_kpis


def build_mis_report(
    tables: dict[str, pd.DataFrame],
    output_dir: str | Path = "reports",
    *,
    low_inventory_days: int = 7,
) -> Path:
    """Create a deterministic Markdown report from validated analytics outputs."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    kpis = monthly_kpis(tables["sales"], tables["targets"])
    if kpis.empty:
        raise ValueError("Cannot generate an MIS report from empty sales data.")

    sales_anomalies = detect_sales_declines(tables["sales"])
    inventory_risks = detect_inventory_risks(
        tables["inventory"],
        low_days_threshold=low_inventory_days,
    )
    latest = kpis.sort_values("month").iloc[-1]

    report_path = output_dir / "monthly_mis_report.md"
    lines = [
        "# Enterprise AI Insights & MIS Copilot",
        "",
        f"Generated at (UTC): {datetime.now(timezone.utc).isoformat()}",
        "",
        "> Synthetic-data demonstration only. Statistical alerts require business review.",
        "",
        "## Latest monthly summary",
        f"- Month: {pd.Timestamp(latest['month']).strftime('%Y-%m')}",
        f"- Revenue: {latest['revenue']:,.2f}",
        f"- Units sold: {int(latest['units_sold']):,}",
        f"- Target revenue: {latest['target_revenue']:,.2f}",
        f"- Target attainment: {latest['target_attainment_pct']:.2f}%",
        f"- Month-over-month revenue change: {latest['revenue_mom_change_pct']:.2f}%",
        "",
        "## Sales decline signals",
        "These signals indicate unusual changes; they do not prove root cause.",
        "",
    ]

    if sales_anomalies.empty:
        lines.append("No sales declines crossed the configured threshold.")
    else:
        for row in sales_anomalies.sort_values("change_pct").head(50).itertuples():
            lines.append(
                f"- {pd.Timestamp(row.month).strftime('%Y-%m')} | {row.product_id} | "
                f"{row.region} | revenue {row.revenue:,.2f} vs baseline "
                f"{row.baseline_revenue:,.2f} ({row.change_pct:.2f}%)"
            )

    lines += [
        "",
        "## Inventory risks",
        f"Configured low-cover threshold: {low_inventory_days} days.",
        "",
    ]
    if inventory_risks.empty:
        lines.append("No inventory risks crossed the configured thresholds.")
    else:
        for row in inventory_risks.head(50).itertuples():
            snapshot = getattr(row, "snapshot_date", None)
            snapshot_text = (
                f"{pd.Timestamp(snapshot).date()} | " if snapshot is not None else ""
            )
            lines.append(
                f"- {snapshot_text}{row.product_id} | {row.region} | "
                f"stock {row.stock_units} units | cover {row.days_of_inventory} days | "
                f"reorder level {row.reorder_level_units} units | "
                f"low cover={bool(row.low_inventory_cover)} | "
                f"below reorder={bool(row.below_reorder_level)}"
            )

    lines += [
        "",
        "## Data and governance notes",
        "- Data is synthetic and contains no real patient or commercial records.",
        "- Investigate alerts with source data and authorized business review.",
        "- Do not treat correlation or anomaly detection as proof of causation.",
        "- Do not trigger procurement or other operational actions automatically.",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path

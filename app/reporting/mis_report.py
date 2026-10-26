from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
from app.analytics.kpis import monthly_kpis
from app.analytics.anomalies import detect_sales_declines

def build_mis_report(tables: dict[str, pd.DataFrame], output_dir: str | Path = "reports") -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    kpis = monthly_kpis(tables["sales"], tables["targets"])
    anomalies = detect_sales_declines(tables["sales"])
    latest = kpis.sort_values("month").iloc[-1]
    report_path = output_dir / "monthly_mis_report.md"
    lines = [
        "# Enterprise AI Insights & MIS Copilot",
        "",
        f"Generated at (UTC): {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Latest monthly summary",
        f"- Month: {pd.Timestamp(latest['month']).strftime('%Y-%m')}",
        f"- Revenue: {latest['revenue']:,.2f}",
        f"- Units sold: {int(latest['units_sold']):,}",
        f"- Target revenue: {latest['target_revenue']:,.2f}",
        f"- Target attainment: {latest['target_attainment_pct']:.2f}%",
        "",
        "## Sales decline signals",
        "These are statistical signals for investigation, not confirmed root causes.",
        "",
    ]
    if anomalies.empty:
        lines.append("No sales declines crossed the configured threshold.")
    else:
        for row in anomalies.sort_values("change_pct").head(20).itertuples():
            lines.append(
                f"- {pd.Timestamp(row.month).strftime('%Y-%m')} | {row.product_id} | {row.region} | "
                f"revenue {row.revenue:,.2f} vs baseline {row.baseline_revenue:,.2f} "
                f"({row.change_pct:.2f}%)"
            )
    lines += ["", "## Data and governance notes",
              "- Data is synthetic and contains no real patient or commercial records.",
              "- Validate source data and obtain authorized review before business use.",
              "- Do not treat correlation or anomaly detection as proof of causation.", ""]
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path

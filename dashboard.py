from __future__ import annotations

import pandas as pd
import streamlit as st

from app.analytics.anomalies import detect_inventory_risks, detect_sales_declines
from app.analytics.investigation import build_investigation
from app.analytics.kpis import monthly_kpis
from app.config import RAW_DIR
from app.data.loader import load_tables
from app.knowledge.rag import LocalRAG
from app.knowledge.rag_evaluation import evaluate_retrieval


st.set_page_config(
    page_title="Enterprise AI MIS Copilot",
    page_icon="📊",
    layout="wide",
)

st.title("Enterprise AI Insights & MIS Copilot")
st.caption(
    "Local-first demonstration using synthetic data. Signals support investigation; "
    "they do not prove root cause or authorize operational actions."
)


@st.cache_data
def cached_tables():
    return load_tables(RAW_DIR)


@st.cache_resource
def cached_rag():
    return LocalRAG()


try:
    tables = cached_tables()
except (FileNotFoundError, ValueError) as exc:
    st.error(str(exc))
    st.code("python -m app.data.generate")
    st.stop()

sales = tables["sales"].copy()
inventory = tables["inventory"].copy()
sales["month"] = pd.to_datetime(sales["month"])
inventory["snapshot_date"] = pd.to_datetime(inventory["snapshot_date"])

with st.sidebar:
    st.header("Filters")
    products = ["All"] + sorted(sales["product_id"].astype(str).unique().tolist())
    regions = ["All"] + sorted(sales["region"].astype(str).unique().tolist())
    selected_product = st.selectbox("Product", products)
    selected_region = st.selectbox("Region", regions)
    min_month = sales["month"].min().date()
    max_month = sales["month"].max().date()
    date_range = st.date_input(
        "Sales date range",
        value=(min_month, max_month),
        min_value=min_month,
        max_value=max_month,
    )
    threshold = st.slider(
        "Sales decline alert threshold (%)",
        min_value=-60,
        max_value=-5,
        value=-20,
        step=5,
    )
    low_days = st.slider(
        "Low inventory cover threshold (days)",
        min_value=1,
        max_value=21,
        value=7,
    )

filtered_sales = sales.copy()
filtered_inventory = inventory.copy()
if selected_product != "All":
    filtered_sales = filtered_sales[filtered_sales["product_id"] == selected_product]
    filtered_inventory = filtered_inventory[filtered_inventory["product_id"] == selected_product]
if selected_region != "All":
    filtered_sales = filtered_sales[filtered_sales["region"] == selected_region]
    filtered_inventory = filtered_inventory[filtered_inventory["region"] == selected_region]
investigation_sales = filtered_sales.copy()
start_date, end_date = pd.Timestamp(min_month), pd.Timestamp(max_month)
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    filtered_sales = filtered_sales[
        filtered_sales["month"].between(
            start_date, end_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        )
    ]

filtered_tables = {**tables, "sales": investigation_sales, "inventory": filtered_inventory}
kpis = monthly_kpis(filtered_sales, tables["targets"])
sales_anomalies = detect_sales_declines(investigation_sales, threshold_pct=float(threshold))
sales_anomalies = sales_anomalies[
    pd.to_datetime(sales_anomalies["month"]).between(start_date, end_date + pd.Timedelta(days=1))
]
latest_inventory_date = (
    filtered_inventory["snapshot_date"].max() if not filtered_inventory.empty else None
)
latest_inventory_for_risks = (
    filtered_inventory[filtered_inventory["snapshot_date"] == latest_inventory_date]
    if latest_inventory_date is not None else filtered_inventory
)
inventory_risks = detect_inventory_risks(
    latest_inventory_for_risks, low_days_threshold=int(low_days)
)

latest_kpi = kpis.sort_values("month").iloc[-1] if not kpis.empty else None
m1, m2, m3, m4 = st.columns(4)
m1.metric("Revenue", f"{latest_kpi['revenue']:,.0f}" if latest_kpi is not None else "—")
m2.metric("Units sold", f"{latest_kpi['units_sold']:,.0f}" if latest_kpi is not None else "—")
m3.metric(
    "Target attainment",
    f"{latest_kpi['target_attainment_pct']:.1f}%"
    if latest_kpi is not None and pd.notna(latest_kpi["target_attainment_pct"]) else "—",
)
m4.metric("Sales decline signals", len(sales_anomalies))

sales_tab, inventory_tab, investigate_tab, rag_tab = st.tabs(
    ["Sales & KPIs", "Inventory", "Evidence-based investigation", "RAG evaluation"]
)

with sales_tab:
    st.subheader("Monthly revenue")
    if kpis.empty:
        st.info("No sales data matches the selected filters.")
    else:
        chart = kpis.sort_values("month").set_index("month")[["revenue", "target_revenue"]]
        st.line_chart(chart)
        display_kpis = kpis.copy()
        display_kpis["month"] = display_kpis["month"].dt.strftime("%Y-%m")
        st.dataframe(display_kpis, use_container_width=True, hide_index=True)
    st.subheader("Sales decline signals")
    if sales_anomalies.empty:
        st.success("No sales declines crossed the selected threshold.")
    else:
        anomaly_view = sales_anomalies.copy()
        anomaly_view["month"] = anomaly_view["month"].dt.strftime("%Y-%m")
        st.dataframe(
            anomaly_view[
                ["month", "product_id", "region", "revenue", "baseline_revenue", "change_pct"]
            ],
            use_container_width=True,
            hide_index=True,
        )

with inventory_tab:
    st.subheader("Latest inventory position")
    st.caption(
        f"Latest snapshot: {latest_inventory_date.date() if latest_inventory_date is not None else 'No data'}"
    )
    st.dataframe(
        latest_inventory_for_risks, use_container_width=True, hide_index=True
    )
    st.subheader("Inventory risks")
    if inventory_risks.empty:
        st.success("No inventory risks crossed the selected thresholds.")
    else:
        st.dataframe(inventory_risks, use_container_width=True, hide_index=True)

with investigate_tab:
    st.subheader("Evidence-linked investigation")
    st.write(
        "The workflow combines detected sales declines, the latest matching inventory "
        "snapshot, and relevant SOP excerpts. It intentionally does not claim a root cause."
    )
    run_investigation = st.button("Build investigation findings", type="primary")
    if run_investigation:
        with st.spinner("Assembling signals and retrieving SOP evidence..."):
            investigation = build_investigation(
                filtered_tables,
                product_id=None if selected_product == "All" else selected_product,
                region=None if selected_region == "All" else selected_region,
                sales_threshold_pct=float(threshold),
                low_inventory_days=int(low_days),
                rag=cached_rag(),
            )
        visible_findings = [
            finding for finding in investigation["findings"]
            if start_date <= pd.Timestamp(finding["month"] + "-01") <= end_date
        ]
        st.metric("Sales findings", len(visible_findings))
        st.metric("Latest inventory risks", investigation["inventory_risk_count"])
        if not visible_findings:
            st.info("No sales decline findings matched the current filters.")
        for index, finding in enumerate(visible_findings, start=1):
            with st.expander(
                f"{index}. {finding['product_id']} / {finding['region']} / "
                f"{finding['month']} ({finding['change_pct']:.1f}%)",
                expanded=index == 1,
            ):
                st.write(finding["interpretation"])
                st.write(f"Actual revenue: {finding['actual_revenue']:,.2f}")
                st.write(f"Historical baseline: {finding['baseline_revenue']:,.2f}")
                st.write("Inventory context", finding["inventory_snapshot"])
                st.warning(finding["limitations"])
                st.markdown("**Retrieved SOP evidence**")
                if not finding["evidence"]:
                    st.info("No supporting SOP passage was retrieved.")
                for evidence in finding["evidence"]:
                    st.markdown(
                        f"**{evidence['source']}** · retrieval score {evidence['score']:.3f}"
                    )
                    st.caption(evidence["excerpt"])
        st.markdown("**Review checklist**")
        for item in investigation["review_guidance"]:
            st.markdown(f"- {item}")

with rag_tab:
    st.subheader("Retrieval evaluation")
    st.write(
        "Runs a small labelled evaluation set against the local TF-IDF retriever. "
        "Metrics measure document retrieval only—not answer correctness or production quality."
    )
    k = st.selectbox("Top-k documents", [1, 2, 3], index=2)
    if st.button("Run RAG evaluation", type="primary"):
        with st.spinner("Evaluating labelled queries..."):
            evaluation = evaluate_retrieval(rag=cached_rag(), k=int(k))
        c1, c2, c3, c4 = st.columns(4)
        hit_rate = evaluation[f"hit_rate_at_{k}"]
        mrr = evaluation[f"mrr_at_{k}"]
        no_answer = evaluation["no_answer_accuracy"]
        pass_rate = evaluation["overall_case_pass_rate"]
        c1.metric(f"Hit rate@{k}", f"{hit_rate:.1%}" if hit_rate is not None else "—")
        c2.metric(f"MRR@{k}", f"{mrr:.3f}" if mrr is not None else "—")
        c3.metric("No-answer accuracy", f"{no_answer:.1%}" if no_answer is not None else "—")
        c4.metric("Case pass rate", f"{pass_rate:.1%}" if pass_rate is not None else "—")
        st.dataframe(pd.DataFrame(evaluation["results"]), use_container_width=True, hide_index=True)
        for note in evaluation["notes"]:
            st.caption(note)

st.divider()
st.caption("Synthetic demo data only · Local retrieval · Human review required before operational action")

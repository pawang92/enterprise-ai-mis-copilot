# Enterprise AI Insights & MIS Copilot

A local-first portfolio project demonstrating enterprise MIS analytics, anomaly detection, document retrieval, evidence-linked investigation, and workflow orchestration. It uses reproducible synthetic pharmaceutical-style data and does not require a paid model API or cloud account.

> All product names and data are synthetic. This is not an official Cipla system and is not validated for pharmaceutical compliance or operational decision-making.

## Features

- Reproducible synthetic sales, product, inventory, and target datasets.
- Pandas KPIs: revenue, units sold, target attainment, and month-over-month change.
- Sales decline detection using a trailing historical baseline.
- Inventory risk flags based on days of cover and reorder levels.
- Streamlit dashboard for KPI trends, sales alerts, inventory risks, and filters.
- Local TF-IDF retrieval over Markdown SOP examples with source provenance.
- Labelled RAG retrieval evaluation with Hit Rate@k, MRR@k, Precision@k, and no-answer accuracy.
- Evidence-linked investigation that combines a detected sales signal, the latest matching inventory snapshot, and retrieved SOP evidence.
- In-memory entity-relation triples and LangGraph routing.
- FastAPI endpoints and Markdown MIS report generation.
- Pytest suite and GitHub Actions CI.

## Requirements

- Python 3.11 or 3.12.
- No Azure subscription, paid model API, or cloud credentials required for local use.

## Windows PowerShell setup

Run from the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m app.data.generate
python -m pytest -q
```

If PowerShell blocks environment activation, run this in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Run the dashboard

```powershell
streamlit run dashboard.py
```

Streamlit opens a local browser page. The dashboard includes:

1. **Sales & KPIs** — revenue vs target, monthly KPIs, and sales decline alerts.
2. **Inventory** — latest inventory snapshot and configurable risk thresholds.
3. **Evidence-based investigation** — joins sales-decline signals to the latest matching inventory snapshot and retrieves relevant SOP excerpts with source filenames and scores.
4. **RAG evaluation** — runs the labelled query set in `evaluation/rag_test_cases.json` and displays retrieval metrics.

## Run RAG evaluation from the command line

```powershell
python scripts\evaluate_rag.py --k 3
```

The command prints a JSON summary and per-query results. Metrics are retrieval metrics, not measures of answer correctness or production quality. Update the labelled cases when SOP documents change.

## Run the FastAPI service

```powershell
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

Endpoints:

- `GET /api/v1/health`
- `GET /api/v1/kpis/monthly`
- `GET /api/v1/anomalies/sales?threshold_pct=-20`
- `GET /api/v1/anomalies/inventory?low_days_threshold=7`
- `POST /api/v1/reports/mis`
- `POST /api/v1/copilot/query`, for example `{"question": "What is the inventory policy?"}`

## Example questions

- `Generate the latest MIS report`
- `Investigate sales declines`
- `Show inventory risks`
- `What should happen when inventory is below seven days of cover?`
- `Does a statistical anomaly prove the root cause?`
- `Which category does MED001 belong to?`

## Synthetic data schema

- `products.csv`: `product_id`, `product_name`, `category`, `unit_price`
- `sales.csv`: `month`, `product_id`, `region`, `units_sold`, `revenue`
- `inventory.csv`: `snapshot_date`, `product_id`, `region`, `stock_units`, `days_of_inventory`, `reorder_level_units`
- `targets.csv`: `month`, `product_id`, `region`, `target_revenue`

Generated CSVs are intentionally ignored by Git; run the generator to recreate them.

## RAG evaluation metrics

- **Hit Rate@k:** proportion of answerable queries where a relevant source appears in the top k.
- **MRR@k:** mean reciprocal rank of the first relevant source.
- **Precision@k:** relevant retrieved sources divided by k.
- **No-answer accuracy:** proportion of unanswerable queries for which the retriever returns no documents.
- **Overall case pass rate:** proportion of labelled cases meeting their hit/no-answer expectation.

This is a small, hand-labelled demonstration set. It is not a statistically representative benchmark and does not evaluate generated-answer faithfulness.

## Evidence-based investigation: interpretation and limits

The investigation workflow reports observable signals, the historical baseline, the latest available inventory context, and retrieved SOP source excerpts. It does not infer a causal root cause, trigger procurement, or make an autonomous business decision. A business user must validate the source data and approve any operational action.

## Architecture and current limitations

1. Synthetic data generator creates repeatable CSVs.
2. Loader validates the schema and numeric fields.
3. Analytics calculate KPIs and sales/inventory risk signals.
4. TF-IDF retrieval finds lexical matches in Markdown SOP files.
5. Investigation assembles sales signals, latest inventory context, and cited SOP excerpts.
6. Streamlit provides local dashboard and evaluation UI; FastAPI exposes API endpoints.
7. LangGraph routes questions to analytics, RAG, graph lookup, or MIS report generation.

The router is keyword-based. TF-IDF is lexical retrieval, not semantic embeddings or generated synthesis. The knowledge graph is a small in-memory triple list, not a graph database or full KAG framework. A local LLM for report synthesis, expanded graph querying, authentication, persistent audit storage, and Azure Databricks/Azure DevOps deployment are future milestones.

## Tests

```powershell
python -m pytest -q
python scripts\evaluate_rag.py --k 3
```

Use only authorized data. Do not use real patient or confidential commercial records without appropriate privacy, security, access-control, and human-review safeguards.

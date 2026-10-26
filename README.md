# Enterprise AI Insights & MIS Copilot

A local, no-paid-API portfolio project for an enterprise Data Scientist role. It combines synthetic pharmaceutical-style MIS data, deterministic analytics, local document retrieval, graph-like knowledge lookup, LangGraph routing, and report generation.

> All product names and data are synthetic. This is not an official Cipla system and is not validated for pharmaceutical compliance or operational decision-making.

## Features

- Reproducible synthetic sales, product, inventory, and target datasets.
- Pandas KPIs: revenue, units sold, target attainment, and month-over-month change.
- Sales decline detection using a trailing historical baseline.
- Inventory risk flags based on low days-of-cover and reorder levels.
- Local TF-IDF retrieval over Markdown SOP examples (no hosted embeddings or LLM required).
- In-memory entity-relation triples for basic knowledge-graph queries.
- LangGraph workflow routing questions to analytics, RAG, graph lookup, or MIS report generation.
- FastAPI endpoints and a Markdown MIS report.
- Pytest test suite.

## Requirements

- Python 3.11 or 3.12
- No Azure subscription, paid model API, or cloud credentials required for local use.

## Windows PowerShell setup

From the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m app.data.generate
python scripts\run_demo.py
python -m pytest -q
uvicorn app.main:app --reload
```

If PowerShell blocks environment activation, run this in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

API docs: http://127.0.0.1:8000/docs

## API endpoints

- `GET /api/v1/health`
- `GET /api/v1/kpis/monthly`
- `GET /api/v1/anomalies/sales?threshold_pct=-20`
- `POST /api/v1/reports/mis`
- `POST /api/v1/copilot/query` with JSON body such as:
  ```json
  {"question": "What is the inventory policy?"}
  ```

Example prompts:

- `Generate the latest MIS report`
- `Investigate sales declines`
- `Show inventory risks`
- `What is the inventory policy?`
- `Which category does MED001 belong to?`

## Synthetic data schema

- `products.csv`: `product_id`, `product_name`, `category`, `unit_price`
- `sales.csv`: `month`, `product_id`, `region`, `units_sold`, `revenue`
- `inventory.csv`: `snapshot_date`, `product_id`, `region`, `stock_units`, `days_of_inventory`, `reorder_level_units`
- `targets.csv`: `month`, `product_id`, `region`, `target_revenue`

Generated CSVs are intentionally ignored by Git; run the generator locally to recreate them.

## Architecture

1. Data generator creates reproducible synthetic CSV tables.
2. Validation/load layer checks required columns and basic sales constraints.
3. Analytics functions calculate KPIs and flag sales/inventory risks.
4. Local TF-IDF RAG retrieves relevant SOP files with source names.
5. The simple knowledge graph stores product/metric/policy triples.
6. LangGraph routes a question to an analytics, RAG, graph, or report node.
7. FastAPI exposes the workflow; the report node writes a Markdown MIS report.

## Limitations and next improvements

- The router is keyword-based, not an LLM reasoning agent.
- TF-IDF is lexical retrieval, not semantic embedding search or generated synthesis.
- The current graph is a small in-memory triple list, not a graph database or full KAG framework.
- Root cause is not inferred from correlation; flagged findings need human investigation.
- Authentication, role-based authorization, persistent audit storage, model-quality evaluation, and cloud deployment are not implemented.
- Azure Databricks integration and Azure DevOps CI/CD remain planned extensions.

## Tests

Run:

```powershell
python -m pytest -q
```

This project is for learning and interview demonstration. Do not use real patient, confidential, or production data without authorization, privacy review, security controls, and human validation.

<<<<<<< HEAD
# Enterprise AI Insights & MIS Copilot

A local, synthetic-data prototype for a Data Scientist role involving analytics, RAG/KAG, agentic AI, MIS reporting, and enterprise lifecycle practices.

## Current baseline

- Reproducible synthetic pharmaceutical sales, inventory, target, and product data.
- Pandas KPI calculations and trailing-baseline sales decline detection.
- Markdown MIS report generation.
- FastAPI endpoints for health, monthly KPIs, anomalies, and report generation.
- Pytest tests for core analytics and API health.

**This initial version does not yet implement RAG, KAG, or LangGraph.** Those are Day 2 modules. The baseline is intentionally useful without any LLM, cloud service, or API key.

## Windows PowerShell setup

Use Python 3.11 or 3.12.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m app.data.generate
python scripts/run_demo.py
pytest -q
uvicorn app.main:app --reload
```

If PowerShell blocks activation, run this for the current terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

You can also skip activation and use `.venv\Scripts\python.exe` directly.

## API

- `GET /api/v1/health`
- `GET /api/v1/kpis/monthly`
- `GET /api/v1/anomalies/sales?threshold_pct=-20`
- `POST /api/v1/reports/mis`
- Interactive API docs: `http://127.0.0.1:8000/docs`

## Synthetic data schema

- `products.csv`: `product_id`, `product_name`, `category`, `unit_price`
- `sales.csv`: `month`, `product_id`, `region`, `units_sold`, `revenue`
- `inventory.csv`: `snapshot_date`, `product_id`, `region`, `stock_units`, `days_of_inventory`, `reorder_level_units`
- `targets.csv`: `month`, `product_id`, `region`, `target_revenue`

A deliberate sales drop and low inventory snapshot are included for testing. Data is fabricated; it is not Cipla data.

## Suggested Day 2 and Day 3 extensions

1. Add local document retrieval over fictional SOPs; include source metadata and citations.
2. Add a small entity-relation graph for products, categories, regions, metrics, and policies.
3. Add a LangGraph workflow that routes between deterministic analytics tools and retrieval.
4. Evaluate retrieval relevance, answer grounding, anomaly precision/recall, and report correctness.
5. Add CI, linting, dependency scanning, model/prompt versioning, access control, audit logging, and a Databricks deployment design.

## Important limitations

This is a portfolio prototype, not a validated pharmaceutical compliance system. Do not use patient data, confidential company data, or real operational decisions without authorization, security review, data governance, and human validation.
=======
# enterprise-ai-mis-copilot
Enterprise AI Insights &amp; MIS Copilot using RAG, KAG, LangGraph and Python analytics
>>>>>>> origin/main

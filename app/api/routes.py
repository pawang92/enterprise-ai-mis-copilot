from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.workflow import ask_copilot
from app.analytics.anomalies import detect_inventory_risks, detect_sales_declines
from app.analytics.kpis import monthly_kpis
from app.config import RAW_DIR, REPORTS_DIR
from app.data.loader import load_tables
from app.reporting.mis_report import build_mis_report

router = APIRouter()


def get_tables():
    try:
        return load_tables(RAW_DIR)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/health")
def health():
    return {"status": "ok", "service": "enterprise-ai-mis-copilot"}


@router.get("/kpis/monthly")
def monthly_kpi_endpoint():
    tables = get_tables()
    result = monthly_kpis(tables["sales"], tables["targets"])
    result["month"] = result["month"].astype(str)
    return result.where(result.notna(), None).to_dict(orient="records")


@router.get("/anomalies/sales")
def sales_anomalies(threshold_pct: float = -20.0):
    tables = get_tables()
    result = detect_sales_declines(
        tables["sales"], threshold_pct=threshold_pct
    )
    if result.empty:
        return []
    result["month"] = result["month"].astype(str)
    return result.where(result.notna(), None).to_dict(orient="records")


@router.get("/anomalies/inventory")
def inventory_anomalies(low_days_threshold: int = 7):
    if low_days_threshold < 0:
        raise HTTPException(
            status_code=422,
            detail="low_days_threshold must be non-negative",
        )
    tables = get_tables()
    result = detect_inventory_risks(
        tables["inventory"],
        low_days_threshold=low_days_threshold,
    )
    if result.empty:
        return []
    if "snapshot_date" in result.columns:
        result["snapshot_date"] = result["snapshot_date"].astype(str)
    return result.where(result.notna(), None).to_dict(orient="records")


@router.post("/reports/mis")
def generate_report():
    tables = get_tables()
    path = build_mis_report(tables, REPORTS_DIR)
    return {"status": "ok", "report_path": str(path)}


class CopilotRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
        description="Question about sales, inventory, or business policies",
    )


@router.post("/copilot/query")
def copilot_query(request: CopilotRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        return ask_copilot(request.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

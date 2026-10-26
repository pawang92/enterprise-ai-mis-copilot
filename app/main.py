from fastapi import FastAPI
from app.api.routes import router
from app.config import ROOT_DIR

app = FastAPI(
    title="Enterprise AI Insights & MIS Copilot",
    description="Local synthetic-data prototype for analytics, anomaly detection, and MIS reporting.",
    version="0.1.0",
)
app.include_router(router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "name": "Enterprise AI Insights & MIS Copilot",
        "version": "0.1.0",
        "docs": "/docs",
        "data_generation_command": "python -m app.data.generate",
    }

from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / os.getenv("DATA_DIR", "data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = ROOT_DIR / os.getenv("REPORTS_DIR", "reports")
ANOMALY_DECLINE_THRESHOLD_PCT = float(os.getenv("ANOMALY_DECLINE_THRESHOLD_PCT", "-20"))

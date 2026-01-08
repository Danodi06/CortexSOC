"""Minimal FastAPI app to exercise ingestion, detection, and response."""
import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, List
from .ingest import ingest_log, get_logs
from .detect import detect_all
from .respond import (
    block_ip,
    disable_account,
    send_alert,
    auto_respond_to_alert,
    get_incidents,
    get_incident,
)
from . import storage

app = FastAPI(title="CortexSOC - AI SOC Prototype")

# Serve static dashboard
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")



@app.get("/")
def root():
    """Redirect to dashboard."""
    return {"message": "CortexSOC API. Visit /static/index.html for dashboard"}


class LogRecord(BaseModel):
    type: str
    user: str = None
    origin: str = None
    ip: str = None
    raw: Dict[str, Any] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def api_ingest(record: LogRecord):
    r = ingest_log(record.dict())
    return {"ingested": r}


@app.get("/detect")
def api_detect() -> List[Dict[str, Any]]:
    logs = get_logs()
    alerts = detect_all(logs)
    return alerts


@app.post("/detect-and-respond")
def api_detect_and_respond() -> Dict[str, Any]:
    """Run detection and auto-respond to high/medium severity alerts."""
    logs = get_logs()
    alerts = detect_all(logs)
    
    incidents = []
    for alert in alerts:
        incident = auto_respond_to_alert(alert)
        incidents.append(incident.to_dict())
    
    return {
        "alerts_generated": len(alerts),
        "incidents_created": len(incidents),
        "incidents": incidents,
    }


class ResponseRequest(BaseModel):
    action: str
    target: str


@app.post("/respond")
def api_respond(req: ResponseRequest):
    if req.action == "block_ip":
        return block_ip(req.target)
    if req.action == "disable_account":
        return disable_account(req.target)
    if req.action == "alert":
        return send_alert("ops", req.target)
    raise HTTPException(status_code=400, detail="unknown action")


@app.get("/incidents")
def api_get_incidents() -> List[Dict[str, Any]]:
    """Get all security incidents."""
    return get_incidents()


@app.get("/incidents/{incident_id}")
def api_get_incident(incident_id: int) -> Dict[str, Any]:
    """Get details of a specific incident."""
    incident = get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="incident not found")
    return incident


@app.on_event("startup")
def startup_event():
    database_url = os.getenv("DATABASE_URL", "sqlite:///./cortexsoc.db")
    storage.init_db(database_url)

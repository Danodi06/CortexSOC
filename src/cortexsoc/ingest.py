"""Ingestion helpers: accept logs and store them in DB or in-memory fallback."""
from typing import Dict, Any, List
from datetime import datetime
from . import storage

# In-memory fallback
_logs: List[Dict[str, Any]] = []


def ingest_log(record: Dict[str, Any]) -> Dict[str, Any]:
    """Ingest a single log record into persistent storage if available.

    Falls back to an in-memory list when DB is not initialized.
    """
    if "timestamp" not in record:
        record["timestamp"] = datetime.utcnow().isoformat() + "Z"
    try:
        if storage.is_initialized():
            return storage.write_log(record)
    except Exception:
        # DB may be misconfigured or unavailable; fall back to memory
        pass
    _logs.append(record)
    return record


def get_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """Return recent logs from DB if available, otherwise from memory."""
    try:
        if storage.is_initialized():
            return storage.get_logs(limit=limit)
    except Exception:
        pass
    return list(_logs[-limit:])

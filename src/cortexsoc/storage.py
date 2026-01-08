"""SQL storage layer for CortexSOC using SQLAlchemy.

Provides a simple `Log` model and helper functions `init_db`,
`write_log`, and `get_logs`.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    JSON as SA_JSON,
    Text,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import threading

Base = declarative_base()


class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String(64), nullable=False)
    type = Column(String(64), nullable=True)
    user = Column(String(128), nullable=True)
    ip = Column(String(64), nullable=True)
    origin = Column(String(128), nullable=True)
    raw = Column(SA_JSON)


# Module-level DB objects
_engine = None
_SessionLocal = None
_lock = threading.RLock()


def init_db(database_url: str = "sqlite:///./cortexsoc.db") -> None:
    """Initialize the DB engine and create tables.

    Accepts a SQLAlchemy-compatible `database_url`. Defaults to a local
    SQLite file `cortexsoc.db`.
    """
    global _engine, _SessionLocal
    with _lock:
        if _engine is not None:
            return
        connect_args = {}
        if database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        _engine = create_engine(database_url, connect_args=connect_args)
        _SessionLocal = sessionmaker(bind=_engine)
        Base.metadata.create_all(bind=_engine)


def write_log(record: Dict[str, Any]) -> Dict[str, Any]:
    """Persist a log record and return the stored representation."""
    global _SessionLocal
    if _SessionLocal is None:
        raise RuntimeError("DB not initialized. Call init_db() first.")
    session = _SessionLocal()
    try:
        timestamp = record.get("timestamp") or datetime.utcnow().isoformat() + "Z"
        obj = Log(
            timestamp=timestamp,
            type=record.get("type"),
            user=record.get("user"),
            ip=record.get("ip"),
            origin=record.get("origin"),
            raw=record,
        )
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return {
            "id": obj.id,
            "timestamp": obj.timestamp,
            "type": obj.type,
            "user": obj.user,
            "ip": obj.ip,
            "origin": obj.origin,
            "raw": obj.raw,
        }
    finally:
        session.close()


def get_logs(limit: int = 100) -> List[Dict[str, Any]]:
    global _SessionLocal
    if _SessionLocal is None:
        raise RuntimeError("DB not initialized. Call init_db() first.")
    session = _SessionLocal()
    try:
        rows = session.query(Log).order_by(Log.id.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp,
                "type": r.type,
                "user": r.user,
                "ip": r.ip,
                "origin": r.origin,
                "raw": r.raw,
            }
            for r in rows
        ]
    finally:
        session.close()


def is_initialized() -> bool:
    return _SessionLocal is not None

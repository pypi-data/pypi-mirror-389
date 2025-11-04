"""
Centralized campaign logging utilities backed by SQLite.

Provides a logging handler to capture campaign activity without cluttering the
workspace with rotating .log files and helper functions to query the stored
events.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

DEFAULT_LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "campaign_logs.db"

_STANDARD_LOG_RECORD_KEYS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
    "asctime",
    "taskName",
}


def _ensure_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


class CampaignLogHandler(logging.Handler):
    """Logging handler that persists records to a SQLite database."""

    def __init__(self, campaign_name: Optional[str] = None, db_path: Optional[Path] = None) -> None:
        super().__init__()
        self.campaign_name = campaign_name
        self.db_path = Path(db_path) if db_path else DEFAULT_LOG_PATH
        _ensure_directory(self.db_path)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS campaign_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                logger TEXT NOT NULL,
                level TEXT NOT NULL,
                level_no INTEGER NOT NULL,
                campaign TEXT,
                module TEXT,
                func_name TEXT,
                message TEXT NOT NULL,
                extra TEXT
            );
            """
        )
        self._conn.commit()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            created_at = datetime.fromtimestamp(record.created, timezone.utc).isoformat()
            campaign = getattr(record, "campaign_name", None) or self.campaign_name
            message = record.getMessage()
            extra = self._serialize_extra(record)
            with self._lock:
                self._conn.execute(
                    """
                    INSERT INTO campaign_logs (
                        created_at, logger, level, level_no, campaign,
                        module, func_name, message, extra
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        created_at,
                        record.name,
                        record.levelname,
                        record.levelno,
                        campaign,
                        record.module,
                        record.funcName,
                        message,
                        extra,
                    ),
                )
                self._conn.commit()
        except Exception:
            self.handleError(record)

    def _serialize_extra(self, record: logging.LogRecord) -> Optional[str]:
        payload: Dict[str, object] = {}
        for key, value in record.__dict__.items():
            if key in _STANDARD_LOG_RECORD_KEYS:
                continue
            if key.startswith("_"):
                continue
            try:
                json.dumps(value)
                payload[key] = value
            except TypeError:
                payload[key] = repr(value)
        if not payload:
            return None
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    def close(self) -> None:
        try:
            with self._lock:
                if self._conn:
                    self._conn.close()
        finally:
            self._conn = None
            super().close()


def _default_formatter() -> logging.Formatter:
    return logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def setup_campaign_logging(
    campaign_name: str,
    *,
    level: int = logging.INFO,
    db_path: Optional[Path] = None,
    include_stream: bool = True,
) -> None:
    """
    Configure root logging to route events into the campaign log database.

    Removes any FileHandlers to avoid generating .log files while retaining
    optional console output.
    """

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for handler in list(root_logger.handlers):
        if isinstance(handler, logging.FileHandler):
            root_logger.removeHandler(handler)

    if include_stream and not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        stream_handler.setFormatter(_default_formatter())
        root_logger.addHandler(stream_handler)

    if not any(isinstance(h, CampaignLogHandler) and h.campaign_name == campaign_name for h in root_logger.handlers):
        handler = CampaignLogHandler(campaign_name=campaign_name, db_path=db_path)
        handler.setLevel(level)
        root_logger.addHandler(handler)


def _resolve_db_path(db_path: Optional[Path] = None) -> Path:
    return Path(db_path) if db_path else DEFAULT_LOG_PATH


def fetch_logs(
    *,
    campaign: Optional[str] = None,
    min_level: Optional[int] = None,
    since: Optional[str] = None,
    limit: int = 100,
    db_path: Optional[Path] = None,
) -> List[Dict[str, object]]:
    """Return recent log entries with optional filtering."""
    path = _resolve_db_path(db_path)
    if not path.exists():
        return []

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT id, created_at, logger, level, level_no, campaign, module, func_name, message, extra
        FROM campaign_logs
    """
    conditions: List[str] = []
    params: List[object] = []

    if campaign:
        conditions.append("campaign = ?")
        params.append(campaign)

    if min_level is not None:
        conditions.append("level_no >= ?")
        params.append(min_level)

    if since:
        conditions.append("created_at >= ?")
        params.append(since)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    results: List[Dict[str, object]] = []
    for row in rows:
        entry = dict(row)
        extra_data = entry.get("extra")
        if extra_data:
            try:
                entry["extra"] = json.loads(extra_data)
            except json.JSONDecodeError:
                entry["extra"] = {"raw": extra_data}
        else:
            entry["extra"] = {}
        results.append(entry)
    return results


def log_statistics(*, db_path: Optional[Path] = None) -> Dict[str, object]:
    """Return basic statistics such as counts per campaign and log level."""
    path = _resolve_db_path(db_path)
    if not path.exists():
        return {"total": 0, "by_campaign": {}, "by_level": {}}

    conn = sqlite3.connect(path)
    stats = {
        "total": conn.execute("SELECT COUNT(*) FROM campaign_logs").fetchone()[0],
        "by_campaign": {},
        "by_level": {},
    }

    for campaign, count in conn.execute(
        "SELECT COALESCE(campaign, 'uncategorized'), COUNT(*) FROM campaign_logs GROUP BY campaign"
    ):
        stats["by_campaign"][campaign] = count

    for level, count in conn.execute(
        "SELECT level, COUNT(*) FROM campaign_logs GROUP BY level"
    ):
        stats["by_level"][level] = count

    conn.close()
    return stats


def clear_logs(*, campaign: Optional[str] = None, db_path: Optional[Path] = None) -> int:
    """Delete log entries, optionally scoped to a single campaign."""
    path = _resolve_db_path(db_path)
    if not path.exists():
        return 0

    conn = sqlite3.connect(path)
    if campaign:
        deleted = conn.execute("DELETE FROM campaign_logs WHERE campaign = ?", (campaign,)).rowcount
    else:
        deleted = conn.execute("DELETE FROM campaign_logs").rowcount
    conn.commit()
    conn.close()
    return deleted


def level_name_to_number(level_name: str) -> Optional[int]:
    """Translate a textual log level into its numeric constant (case insensitive)."""
    mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return mapping.get(level_name.upper())

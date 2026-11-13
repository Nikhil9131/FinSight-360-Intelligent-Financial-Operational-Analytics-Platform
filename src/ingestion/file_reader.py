"""
FinSight 360 - Data Ingestion Layer
===================================
Ingests multi-format business datasets (CSV, JSON, Excel, REST API).
Tracks file metadata, validates basic structural schemas, and records
ingestion timestamps.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("ingestion")


class DataIngestionEngine:
    """
    Ingestion engine responsible for reading disparate data formats,
    performing structural pre-checks, and logging ingestion metadata.
    """

    def __init__(self):
        self.ingestion_metadata: list[dict[str, Any]] = []

    def ingest_csv(self, file_path: str | Path, **kwargs) -> pd.DataFrame:
        """Read CSV file with metadata tracking and error handling."""
        path = Path(file_path)
        logger.info("Ingesting CSV: {}", path.name)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        start_time = datetime.now()
        df = pd.read_csv(path, **kwargs)
        duration = (datetime.now() - start_time).total_seconds()

        self._record_metadata(path.name, "CSV", len(df), len(df.columns), duration)
        return df

    def ingest_json(self, file_path: str | Path, orient: str = "records") -> pd.DataFrame:
        """Read JSON records with metadata tracking."""
        path = Path(file_path)
        logger.info("Ingesting JSON: {}", path.name)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        start_time = datetime.now()
        df = pd.read_json(path, orient=orient)
        duration = (datetime.now() - start_time).total_seconds()

        self._record_metadata(path.name, "JSON", len(df), len(df.columns), duration)
        return df

    def ingest_excel(self, file_path: str | Path, sheet_name: str | int = 0, **kwargs) -> pd.DataFrame:
        """Read Excel workbook sheet."""
        path = Path(file_path)
        logger.info("Ingesting Excel: {} (Sheet: {})", path.name, sheet_name)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        start_time = datetime.now()
        df = pd.read_excel(path, sheet_name=sheet_name, **kwargs)
        duration = (datetime.now() - start_time).total_seconds()

        self._record_metadata(path.name, "Excel", len(df), len(df.columns), duration)
        return df

    def ingest_from_dict(self, data: list[dict[str, Any]], source_name: str = "REST_API") -> pd.DataFrame:
        """Ingest synthetic or REST API payloads."""
        logger.info("Ingesting API payload: {}", source_name)
        start_time = datetime.now()
        df = pd.DataFrame(data)
        duration = (datetime.now() - start_time).total_seconds()

        self._record_metadata(source_name, "API_Dict", len(df), len(df.columns), duration)
        return df

    def _record_metadata(self, source: str, file_type: str, rows: int, cols: int, duration_sec: float) -> None:
        """Log audit trail of ingested files."""
        meta = {
            "source": source,
            "file_type": file_type,
            "rows_ingested": rows,
            "columns": cols,
            "duration_seconds": round(duration_sec, 4),
            "timestamp": datetime.now().isoformat(),
        }
        self.ingestion_metadata.append(meta)
        logger.debug("Ingestion metadata: {}", meta)

    def get_audit_summary(self) -> pd.DataFrame:
        """Return audit table of all ingestion operations."""
        return pd.DataFrame(self.ingestion_metadata)


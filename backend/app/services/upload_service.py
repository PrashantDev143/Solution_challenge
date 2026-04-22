from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, UploadFile, status

from app.core.config import UPLOAD_DIR
from app.services.state import clear_latest_scan_report, set_latest_uploaded_path
from app.services.target_detector import detect_target
from app.services.model_trainer import train_model_background

logger = logging.getLogger(__name__)
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

def _validate_csv_filename(filename: str) -> None:
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only .csv files are supported.",
        )


def save_and_preview_csv(file: UploadFile) -> dict:
    """Upload and preview CSV file with validation and target detection."""
    if not file.filename:
        logger.error("Upload failed: Missing filename")
        raise HTTPException(status_code=400, detail="Missing filename.")

    _validate_csv_filename(file.filename)
    logger.info(f"Processing file upload: {file.filename}")

    # Read and validate file size
    raw_bytes = file.file.read()
    if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
        logger.error(f"File too large: {len(raw_bytes) / 1024 / 1024:.2f}MB exceeds {MAX_FILE_SIZE_MB}MB limit")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds {MAX_FILE_SIZE_MB}MB limit.",
        )

    temp_path = UPLOAD_DIR / f"{uuid4().hex}_{Path(file.filename).name}"
    temp_path.write_bytes(raw_bytes)
    logger.info(f"File saved to {temp_path}")

    try:
        df = pd.read_csv(temp_path)
        logger.info(f"CSV parsed successfully: {len(df)} rows, {len(df.columns)} columns")
    except Exception as exc:
        temp_path.unlink(missing_ok=True)
        logger.error(f"CSV parsing failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse CSV file. Ensure it's a valid CSV format.",
        ) from exc

    if df.empty:
        temp_path.unlink(missing_ok=True)
        logger.error("Uploaded dataset is empty")
        raise HTTPException(status_code=400, detail="Uploaded dataset is empty.")

    # Check for empty columns
    if df.isnull().all().any():
        logger.warning(f"Dataset contains empty columns: {df.columns[df.isnull().all()].tolist()}")

    set_latest_uploaded_path(str(temp_path))
    clear_latest_scan_report()

    # Detect target column
    try:
        target = detect_target(df)
        logger.info(f"Target column detected: {target}")
    except Exception as exc:
        logger.error(f"Target detection failed: {exc}")
        target = None

    # Trigger async background training (best-effort)
    try:
        if target:
            train_model_background(df.copy(), target, model_name=temp_path.stem)
            logger.info(f"Background training scheduled for model {temp_path.stem}")
    except Exception as exc:
        logger.warning(f"Background training scheduling failed: {exc}")
        # Don't fail upload if training scheduling fails

    return {
        "temp_path": str(temp_path),
        "columns": df.columns.tolist(),
        "target_column": target,
        "row_count": int(len(df)),
        "preview_rows": df.head(10).fillna("").to_dict(orient="records"),
    }

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, UploadFile, status

from app.core.config import UPLOAD_DIR
from app.services.state import clear_latest_scan_report, set_latest_uploaded_path


def _validate_csv_filename(filename: str) -> None:
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload a .csv file.",
        )


def save_and_preview_csv(file: UploadFile) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename.")

    _validate_csv_filename(file.filename)

    temp_path = UPLOAD_DIR / f"{uuid4().hex}_{Path(file.filename).name}"
    raw_bytes = file.file.read()
    temp_path.write_bytes(raw_bytes)

    try:
        df = pd.read_csv(temp_path)
    except Exception as exc:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not parse CSV file: {exc}",
        ) from exc

    if df.empty:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Uploaded dataset is empty.")

    set_latest_uploaded_path(str(temp_path))
    clear_latest_scan_report()

    return {
        "temp_path": str(temp_path),
        "columns": df.columns.tolist(),
        "row_count": int(len(df)),
        "preview_rows": df.head(10).fillna("").to_dict(orient="records"),
    }

from pydantic import BaseModel
from typing import Any, Dict


class AnalyzeResponse(BaseModel):
    report: Dict[str, Any]

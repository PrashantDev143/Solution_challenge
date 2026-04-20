from pydantic import BaseModel
from typing import Optional


class AnalyzeRequest(BaseModel):
    dataset_path: str
    target_column: Optional[str] = None

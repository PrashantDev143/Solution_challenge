from fastapi import APIRouter, HTTPException
from app.schemas.request import AnalyzeRequest
from app.schemas.response import AnalyzeResponse
from app.agents.orchestrator import Orchestrator
import pandas as pd

router = APIRouter(prefix="", tags=["analyze"]) 


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    try:
        df = pd.read_csv(request.dataset_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read dataset: {exc}")

    orch = Orchestrator(df, request.target_column)
    report = orch.run()
    return {"report": report}

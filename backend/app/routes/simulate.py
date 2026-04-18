from fastapi import APIRouter

from app.schemas.simulate import SimulateRequest, SimulateResponse, SimulateSchemaResponse
from app.services.simulate_service import get_simulation_schema, run_simulation


router = APIRouter(prefix="", tags=["simulate"])


@router.get("/simulate/schema", response_model=SimulateSchemaResponse)
def simulate_schema(dataset_path: str | None = None, target_column: str | None = None):
    return get_simulation_schema(dataset_path=dataset_path, target_column=target_column)


@router.post("/simulate", response_model=SimulateResponse)
def simulate(request: SimulateRequest):
    return run_simulation(
        dataset_path=request.dataset_path,
        target_column=request.target_column,
        baseline_features=request.baseline_features,
        scenario_features=request.scenario_features,
    )

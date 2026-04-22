import logging
from fastapi import APIRouter, HTTPException, status

from app.schemas.simulate import SimulateRequest, SimulateResponse, SimulateSchemaResponse
from app.services.simulate_service import get_simulation_schema, run_simulation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["simulate"])


@router.get("/simulate/schema", response_model=SimulateSchemaResponse, summary="Get simulation schema")
def simulate_schema(dataset_path: str | None = None, target_column: str | None = None):
    """Get available fields and options for what-if simulation.
    
    Returns the schema for simulating different feature combinations
    and their impact on model predictions.
    """
    logger.info(f"Schema request for simulation: dataset_path={dataset_path}, target_column={target_column}")
    try:
        result = get_simulation_schema(dataset_path=dataset_path, target_column=target_column)
        logger.info(f"Schema retrieved with {len(result.fields)} fields")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error retrieving simulation schema: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve simulation schema."
        ) from exc


@router.post("/simulate", response_model=SimulateResponse, summary="Run what-if simulation")
def simulate(request: SimulateRequest):
    """Run a what-if simulation comparing baseline vs scenario predictions.
    
    Shows how changing specific features would affect the model's decision.
    Useful for understanding feature importance and bias mitigation strategies.
    """
    logger.info(f"Simulation request: baseline_features={request.baseline_features}, scenario_features={request.scenario_features}")
    try:
        result = run_simulation(
            dataset_path=request.dataset_path,
            target_column=request.target_column,
            baseline_features=request.baseline_features,
            scenario_features=request.scenario_features,
        )
        logger.info(f"Simulation completed: baseline_prob={result.baseline.get('probability')}, scenario_prob={result.scenario.get('probability')}")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error running simulation: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run simulation."
        ) from exc

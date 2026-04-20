import os
from typing import Dict, Any

ENABLE_VERTEX = os.getenv("ENABLE_VERTEX", "false").lower() in ("1", "true", "yes")


def vertex_train_stub(config: Dict[str, Any]) -> Dict[str, Any]:
    if not ENABLE_VERTEX:
        return {"status": "disabled"}
    # TODO: implement Vertex AI integration
    return {"status": "scheduled", "details": {}}


def vertex_batch_predict_stub(config: Dict[str, Any]) -> Dict[str, Any]:
    if not ENABLE_VERTEX:
        return {"status": "disabled"}
    return {"status": "ok"}

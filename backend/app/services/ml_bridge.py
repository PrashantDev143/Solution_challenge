from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ML_ENGINE_DIR = PROJECT_ROOT / "ml-engine"

if str(ML_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ML_ENGINE_DIR))

from bias_detector import detect_bias  # noqa: E402
from simulator import predict_profile, train_predictive_model  # noqa: E402

__all__ = ["detect_bias", "predict_profile", "train_predictive_model"]

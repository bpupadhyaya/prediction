"""
Export the trained GradientBoostingClassifier + StandardScaler to ONNX format.

The resulting stock_predictor.onnx is designed to run on:
  - Desktop:  skl2onnx via this script (inference in Python is not needed — model.pkl is used instead)
  - iOS:      OnnxRuntimeGenAI (ORT) loaded from app bundle
  - Android:  OnnxRuntime for Android loaded from assets/

Input shape: (N, 9) float32
  Features (in order): return_1d, return_5d, return_20d, ma_5, ma_20, ma_50,
                        volatility_20, volume_ratio, rsi

Output: probabilities (N, 2) float32 — [prob_DOWN, prob_UP]

Usage:
    python3 -m backend.models.exporter           # exports model from default path
    python3 -m backend.models.exporter --verify  # export + run a sanity check
"""

import argparse
import logging
import pickle
import numpy as np
from pathlib import Path

from backend.config import MODELS_DIR

logger = logging.getLogger(__name__)

MODEL_PATH = MODELS_DIR / "direction_model.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
ONNX_PATH = MODELS_DIR / "stock_predictor.onnx"

N_FEATURES = 9
FEATURE_NAMES = [
    "return_1d", "return_5d", "return_20d",
    "ma_5", "ma_20", "ma_50",
    "volatility_20", "volume_ratio", "rsi",
]


def export(verify: bool = False) -> Path:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found at {MODEL_PATH}. Run setup.py first."
        )
    if not SCALER_PATH.exists():
        raise FileNotFoundError(
            f"Scaler not found at {SCALER_PATH}. Run setup.py first."
        )

    try:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
    except ImportError:
        raise ImportError(
            "skl2onnx is required for ONNX export. Install it: pip install skl2onnx"
        )

    from sklearn.pipeline import Pipeline

    logger.info("Loading trained model and scaler...")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)

    # Wrap scaler + model in a Pipeline so the single ONNX graph handles both
    pipeline = Pipeline([("scaler", scaler), ("classifier", model)])

    logger.info("Converting to ONNX...")
    initial_type = [("input", FloatTensorType([None, N_FEATURES]))]
    onnx_model = convert_sklearn(
        pipeline,
        initial_types=initial_type,
        target_opset=17,
        options={id(model): {"zipmap": False}},   # output raw float arrays, not dicts
    )

    ONNX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ONNX_PATH, "wb") as f:
        f.write(onnx_model.SerializeToString())

    size_kb = ONNX_PATH.stat().st_size / 1024
    logger.info(f"Exported ONNX model → {ONNX_PATH}  ({size_kb:.0f} KB)")

    if verify:
        _verify(onnx_model)

    return ONNX_PATH


def _verify(onnx_model) -> None:
    """Run a quick sanity check with onnxruntime to confirm the graph is valid."""
    try:
        import onnxruntime as rt
    except ImportError:
        logger.warning("onnxruntime not installed — skipping verification.")
        return

    sess = rt.InferenceSession(onnx_model.SerializeToString())
    dummy = np.random.randn(4, N_FEATURES).astype(np.float32)
    label, prob = sess.run(None, {"input": dummy})

    assert label.shape == (4,), f"Unexpected label shape: {label.shape}"
    assert prob.shape == (4, 2), f"Unexpected prob shape: {prob.shape}"
    assert np.allclose(prob.sum(axis=1), 1.0, atol=1e-5), "Probabilities do not sum to 1"

    logger.info(
        f"Verification passed — sample: label={label[0]}, "
        f"prob_UP={prob[0][1]:.3f}"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Export trained model to ONNX")
    parser.add_argument("--verify", action="store_true", help="Run onnxruntime sanity check after export")
    args = parser.parse_args()
    export(verify=args.verify)

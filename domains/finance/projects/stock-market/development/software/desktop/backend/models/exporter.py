"""
Export a compact MOBILE prediction model to ONNX.

IMPORTANT — two models, two contracts:
  • Desktop uses the full 659-feature GBM (model_*.pkl) — it has macro/fundamental/
    cross-asset/sentiment data available server-side.
  • Mobile (iOS/Android) can only compute 9 price-derived features on-device from
    the bundled price bars. So the ONNX we ship to mobile MUST be a dedicated
    9-feature model — exporting the 659-feature model would crash the mobile
    runners with an input-shape mismatch.

This module trains a small 9-feature GBM on exactly the features the mobile
PredictionEngine.buildFeatures() computes, and exports it as stock_predictor.onnx.

MOBILE FEATURE CONTRACT (order matters — must match the mobile runners):
    return_1d, return_5d, return_20d, ma_5, ma_20, ma_50,
    volatility_20, volume_ratio, rsi

where (desktop semantics — the mobile apps must match these):
    ma_N           = rolling(N).mean() / close - 1      (NOT close/ma)
    volatility_20  = std of daily returns               (NOT std of price levels)
    return_Nd      = close.pct_change(N)
    volume_ratio   = volume / rolling(20).mean(volume)
    rsi            = standard 14-day RSI

⚠️ The current iOS/Android buildFeatures() compute `close/ma` and std of price
levels — they must be updated to the above semantics for predictions to be valid.
See SESSION 7 handoff notes.

Output: probabilities (N, 2) float32 — [prob_DOWN, prob_UP]

Usage:
    python3 -m backend.models.exporter           # train + export mobile model
    python3 -m backend.models.exporter --verify  # + onnxruntime sanity check
"""

import argparse
import logging
import numpy as np
from pathlib import Path

from backend.config import MODELS_DIR

logger = logging.getLogger(__name__)

# The 9 features the mobile apps can compute on-device, in contract order.
MOBILE_FEATURES = [
    "return_1d", "return_5d", "return_20d",
    "ma_5", "ma_20", "ma_50",
    "volatility_20", "volume_ratio", "rsi",
]
N_FEATURES = len(MOBILE_FEATURES)
ONNX_PATH = MODELS_DIR / "stock_predictor.onnx"


def export(verify: bool = False, horizon: str = "1w") -> Path:
    """Train a 9-feature mobile GBM from the prepared training data and export ONNX."""
    try:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
    except ImportError:
        raise ImportError("skl2onnx is required for ONNX export. Install it: pip install skl2onnx")

    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import GradientBoostingClassifier

    from backend.models.trainer import prepare_all_training_data, HORIZON_DAYS

    horizon_days = HORIZON_DAYS.get(horizon, 5)
    logger.info(f"Preparing training data for the {horizon} mobile model...")
    combined = prepare_all_training_data(horizon_days)
    if combined is None or combined.empty:
        raise RuntimeError("No training data available — run backend.setup first.")

    missing = [c for c in MOBILE_FEATURES + ["target"] if c not in combined.columns]
    if missing:
        raise RuntimeError(f"Training data missing required columns: {missing}")

    df = combined.dropna(subset=MOBILE_FEATURES + ["target"])
    X = df[MOBILE_FEATURES].to_numpy(dtype=np.float32)
    y = df["target"].to_numpy(dtype=int)
    logger.info(f"Training 9-feature mobile GBM on {len(X):,} samples...")

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", GradientBoostingClassifier(
            n_estimators=200, max_depth=3, learning_rate=0.05,
            max_features="sqrt", subsample=0.8, random_state=42,
        )),
    ])
    pipeline.fit(X, y)
    train_acc = float((pipeline.predict(X) == y).mean())
    logger.info(f"Mobile model in-sample accuracy: {train_acc:.4f}")

    logger.info("Converting mobile model to ONNX...")
    initial_type = [("input", FloatTensorType([None, N_FEATURES]))]
    onnx_model = convert_sklearn(
        pipeline,
        initial_types=initial_type,
        target_opset=17,
        options={id(pipeline.named_steps["classifier"]): {"zipmap": False}},
    )

    ONNX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ONNX_PATH, "wb") as f:
        f.write(onnx_model.SerializeToString())

    size_kb = ONNX_PATH.stat().st_size / 1024
    logger.info(f"Exported 9-feature mobile ONNX → {ONNX_PATH}  ({size_kb:.0f} KB)")

    if verify:
        _verify(onnx_model)
    return ONNX_PATH


def _verify(onnx_model) -> None:
    """Confirm the graph accepts a (N, 9) input and emits valid probabilities."""
    try:
        import onnxruntime as rt
    except ImportError:
        logger.warning("onnxruntime not installed — skipping verification.")
        return

    sess = rt.InferenceSession(onnx_model.SerializeToString())
    in_shape = sess.get_inputs()[0].shape
    assert in_shape[-1] == N_FEATURES, f"ONNX input dim {in_shape} != {N_FEATURES}"

    dummy = np.random.randn(4, N_FEATURES).astype(np.float32)
    label, prob = sess.run(None, {"input": dummy})
    assert prob.shape == (4, 2), f"Unexpected prob shape: {prob.shape}"
    assert np.allclose(prob.sum(axis=1), 1.0, atol=1e-5), "Probabilities do not sum to 1"
    logger.info(
        f"Verification passed — input dim={N_FEATURES}, "
        f"sample prob_UP={prob[0][1]:.3f}"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Export 9-feature mobile model to ONNX")
    parser.add_argument("--verify", action="store_true", help="Run onnxruntime sanity check after export")
    args = parser.parse_args()
    export(verify=args.verify)

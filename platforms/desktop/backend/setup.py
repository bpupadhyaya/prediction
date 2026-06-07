"""
First-run setup: initialise DB and download initial data.
Called by install.sh / install.bat.
"""
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

from backend.database.duckdb_client import init_db
from backend.data.price_feed import fetch_sp500_tickers, initial_load
from backend.data.macro_feed import initial_macro_load
from backend.models.trainer import train_model
from backend.models.exporter import export as export_onnx

if __name__ == "__main__":
    logging.info("Initialising database...")
    init_db()

    logging.info("Fetching S&P 500 ticker list...")
    tickers = fetch_sp500_tickers()
    logging.info(f"Found {len(tickers)} tickers")

    logging.info("Downloading price history (this takes a few minutes)...")
    initial_load(tickers)

    logging.info("Downloading macro indicators...")
    initial_macro_load()

    logging.info("Training initial prediction model...")
    accuracy = train_model()
    logging.info(f"Initial model trained — directional accuracy: {accuracy:.3f}")

    logging.info("Exporting ONNX model for mobile platforms...")
    try:
        onnx_path = export_onnx(verify=True)
        logging.info(f"ONNX model exported → {onnx_path}")
    except Exception as e:
        logging.warning(f"ONNX export failed (non-fatal): {e}")

    logging.info("Setup complete.")

"""
Model management API: browse catalog, download, clear, activate LLM models.
"""
import json
import platform
import subprocess
import requests
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pathlib import Path

from backend.config import LLM_MODELS_DIR, LLM_CONFIG_PATH
from backend.models.registry import MODELS, MODEL_BY_ID, hf_download_url
from backend.system.hardware import get_hardware_info, model_compatibility

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory download progress: model_id → {status, progress, error}
_downloads: dict[str, dict] = {}


# ─── Config helpers ────────────────────────────────────────────────────────────
def _load_config() -> dict:
    if LLM_CONFIG_PATH.exists():
        try:
            return json.loads(LLM_CONFIG_PATH.read_text())
        except Exception:
            pass
    return {"active_model_id": None}


def _save_config(cfg: dict) -> None:
    LLM_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LLM_CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def _downloaded_ids() -> set[str]:
    return {m["id"] for m in MODELS if (LLM_MODELS_DIR / m["hf_file"]).exists()}


# ─── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/hardware")
def hardware_info():
    return get_hardware_info()


@router.get("/catalog")
def model_catalog():
    hw = get_hardware_info()
    downloaded = _downloaded_ids()
    cfg = _load_config()
    active = cfg.get("active_model_id")

    result = []
    for m in MODELS:
        model_path = LLM_MODELS_DIR / m["hf_file"]
        size_on_disk = round(model_path.stat().st_size / (1024 ** 3), 2) if model_path.exists() else None
        dl_status = _downloads.get(m["id"])
        result.append({
            **m,
            "compatibility": model_compatibility(m["ram_min_gb"], hw),
            "downloaded": m["id"] in downloaded,
            "size_on_disk_gb": size_on_disk,
            "file_path": str(model_path) if model_path.exists() else None,
            "models_dir": str(LLM_MODELS_DIR),
            "active": m["id"] == active,
            "download_status": dl_status,
        })
    return {"hardware": hw, "active_model_id": active, "models_dir": str(LLM_MODELS_DIR), "models": result}


@router.get("/config")
def get_config():
    cfg = _load_config()
    return {"active_model_id": cfg.get("active_model_id"), "downloaded": list(_downloaded_ids())}


class ActivateRequest(BaseModel):
    model_id: str | None = None   # None = revert to GBM


@router.post("/activate")
def activate_model(req: ActivateRequest):
    if req.model_id is not None:
        if req.model_id not in MODEL_BY_ID:
            raise HTTPException(status_code=404, detail=f"Unknown model: {req.model_id}")
        if req.model_id not in _downloaded_ids():
            raise HTTPException(status_code=400, detail="Model not downloaded yet")
    cfg = _load_config()
    cfg["active_model_id"] = req.model_id
    _save_config(cfg)
    return {"active_model_id": req.model_id}


@router.post("/download/{model_id}")
def start_download(model_id: str, background_tasks: BackgroundTasks):
    if model_id not in MODEL_BY_ID:
        raise HTTPException(status_code=404, detail=f"Unknown model: {model_id}")
    if model_id in _downloads and _downloads[model_id]["status"] == "downloading":
        return {"status": "already_downloading"}
    _downloads[model_id] = {"status": "downloading", "progress": 0.0, "error": None}
    background_tasks.add_task(_do_download, model_id)
    return {"status": "started", "model_id": model_id}


@router.get("/download/{model_id}/status")
def download_status(model_id: str):
    if model_id not in _downloads:
        downloaded = model_id in _downloaded_ids()
        return {"status": "done" if downloaded else "not_started", "progress": 1.0 if downloaded else 0.0}
    return _downloads[model_id]


@router.post("/open-folder")
def open_models_folder():
    """Open the LLM models directory in the system file manager."""
    folder = str(LLM_MODELS_DIR)
    sys = platform.system()
    try:
        if sys == "Darwin":
            subprocess.Popen(["open", folder])
        elif sys == "Windows":
            subprocess.Popen(["explorer", folder])
        else:
            subprocess.Popen(["xdg-open", folder])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"folder": folder}


@router.delete("/{model_id}")
def delete_model(model_id: str):
    if model_id not in MODEL_BY_ID:
        raise HTTPException(status_code=404, detail=f"Unknown model: {model_id}")
    meta = MODEL_BY_ID[model_id]
    model_path = LLM_MODELS_DIR / meta["hf_file"]
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="Model file not found on disk")

    # Unload from memory if active
    try:
        from backend.models.llm_predictor import unload_llm
        from backend.api.models_api import _load_config
        cfg = _load_config()
        if cfg.get("active_model_id") == model_id:
            unload_llm()
            cfg["active_model_id"] = None
            _save_config(cfg)
    except Exception:
        pass

    model_path.unlink()
    _downloads.pop(model_id, None)
    return {"deleted": model_id, "freed_gb": round(meta["size_gb"], 1)}


# ─── Background download ───────────────────────────────────────────────────────
def _do_download(model_id: str) -> None:
    meta = MODEL_BY_ID[model_id]
    url = hf_download_url(model_id)
    dest = LLM_MODELS_DIR / meta["hf_file"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".tmp")

    logger.info(f"Downloading {meta['name']} from {url}")
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1 MB chunks
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        _downloads[model_id]["progress"] = round(downloaded / total, 4)
        tmp.rename(dest)
        _downloads[model_id] = {"status": "done", "progress": 1.0, "error": None}
        logger.info(f"Download complete: {meta['name']} ({dest.stat().st_size / 1e9:.1f} GB)")
    except Exception as e:
        logger.error(f"Download failed for {model_id}: {e}")
        tmp.unlink(missing_ok=True)
        _downloads[model_id] = {"status": "error", "progress": 0.0, "error": str(e)}

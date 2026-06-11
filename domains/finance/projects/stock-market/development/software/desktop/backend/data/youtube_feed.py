"""
YouTube audio download and transcription pipeline.
Uses yt-dlp for audio extraction, faster-whisper for local transcription.
Whisper models stored in ~/.prediction/stock-market/whisper_models/
"""
from __future__ import annotations

import logging
import os
import tempfile
import json
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

WHISPER_MODEL_DIR = Path.home() / ".prediction" / "stock-market" / "whisper_models"
WHISPER_MODEL_DIR.mkdir(parents=True, exist_ok=True)

WHISPER_MODELS = [
    {"id": "tiny",     "label": "Tiny (75 MB)",    "sizeGB": 0.075, "quality": "Basic"},
    {"id": "base",     "label": "Base (145 MB)",   "sizeGB": 0.145, "quality": "Good"},
    {"id": "small",    "label": "Small (483 MB)",  "sizeGB": 0.483, "quality": "Great — Recommended"},
    {"id": "medium",   "label": "Medium (1.5 GB)", "sizeGB": 1.5,   "quality": "Excellent"},
    {"id": "large-v3", "label": "Large-v3 (3 GB)", "sizeGB": 3.0,   "quality": "Best possible"},
]

# Pre-seeded influential financial voices
INFLUENTIAL_SPEAKERS = [
    {"name": "Elon Musk",      "channel_id": "UCEb7pOMZ5h3MdqN7fYPD5mw", "tickers": ["TSLA", "SPACE", "DOGE"]},
    {"name": "Warren Buffett", "channel_id": "UCIRYBXDze5krPDzAEOxFGVA", "tickers": ["BRK-B", "AAPL", "BAC"]},
    {"name": "Jerome Powell",  "channel_id": "UCTk_-XgFDfSf6EGpJQJhRdA", "tickers": ["SPY", "TLT", "GLD"]},
    {"name": "Jensen Huang",   "channel_id": "UCeeFfhMcJa1kjtfZAGskOCA", "tickers": ["NVDA", "AMD", "INTC"]},
    {"name": "Tim Cook",       "channel_id": "UCE_M8A5yxnLfW0KghEeajjw", "tickers": ["AAPL"]},
    {"name": "Cathie Wood",    "channel_id": "UCimKczFRuRUKPPHarX6v_jQ", "tickers": ["TSLA", "COIN", "ARKK"]},
    {"name": "Jim Cramer",     "channel_id": "UCFiJ9iqkIEYQlFa_WJyRGqQ", "tickers": ["SPY"]},
    {"name": "Michael Saylor", "channel_id": "UCVHVFAm24e5i3kEi0IG3ItQ", "tickers": ["MSTR", "BTC-USD"]},
]


def get_active_whisper_model() -> Optional[str]:
    """Return the best available locally downloaded whisper model id."""
    for m in reversed(WHISPER_MODELS):  # prefer larger/better
        model_path = WHISPER_MODEL_DIR / m["id"]
        if model_path.exists():
            return m["id"]
    return None


def is_model_downloaded(model_id: str) -> bool:
    return (WHISPER_MODEL_DIR / model_id).exists()


def get_model_info() -> list:
    result = []
    active = get_active_whisper_model()
    for m in WHISPER_MODELS:
        downloaded = is_model_downloaded(m["id"])
        result.append({**m, "downloaded": downloaded, "active": active == m["id"]})
    return result


def download_whisper_model(model_id: str, progress_cb=None) -> None:
    """Download a whisper model via faster-whisper (auto-downloads from HuggingFace)."""
    try:
        from faster_whisper import WhisperModel
        if progress_cb:
            progress_cb(0, f"Downloading {model_id}...")
        # faster-whisper downloads the model on first instantiation
        _model = WhisperModel(model_id, device="cpu", download_root=str(WHISPER_MODEL_DIR))
        if progress_cb:
            progress_cb(100, "Download complete")
        logger.info("Whisper model %s downloaded to %s", model_id, WHISPER_MODEL_DIR / model_id)
    except ImportError:
        raise RuntimeError("faster-whisper not installed. Run: pip install faster-whisper")
    except Exception as e:
        raise RuntimeError(f"Failed to download whisper model {model_id}: {e}")


def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r'(?:v=|youtu\.be/|embed/|shorts/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


def get_video_metadata(url: str) -> dict:
    """Fetch video metadata (title, channel, duration, etc.) without downloading."""
    try:
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "video_id":    info.get("id", ""),
                "title":       info.get("title", ""),
                "channel_name": info.get("channel", "") or info.get("uploader", ""),
                "channel_id":  info.get("channel_id", "") or info.get("uploader_id", ""),
                "published_at": info.get("upload_date", ""),  # YYYYMMDD string
                "duration_sec": info.get("duration", 0) or 0,
                "view_count":  info.get("view_count", 0) or 0,
                "language":    info.get("language", "en") or "en",
                "thumbnail":   info.get("thumbnail", ""),
                "description": (info.get("description", "") or "")[:500],
            }
    except ImportError:
        raise RuntimeError("yt-dlp not installed. Run: pip install yt-dlp")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch video metadata: {e}")


def download_audio(url: str, output_path: str) -> str:
    """Download audio-only stream from YouTube URL. Returns path to audio file."""
    try:
        import yt_dlp
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        # yt-dlp appends .mp3
        if not output_path.endswith(".mp3"):
            output_path = output_path + ".mp3"
        return output_path
    except ImportError:
        raise RuntimeError("yt-dlp not installed. Run: pip install yt-dlp")
    except Exception as e:
        raise RuntimeError(f"Audio download failed: {e}")


def transcribe_audio(audio_path: str, model_id: Optional[str] = None) -> dict:
    """
    Transcribe audio file using faster-whisper.
    Returns {full_text, chunks: [{start, end, text}], word_count, language, model_used}
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError("faster-whisper not installed. Run: pip install faster-whisper")

    active_model = model_id or get_active_whisper_model()
    if not active_model:
        raise RuntimeError(
            "No whisper model downloaded. Download one first via "
            "/api/video-intelligence/whisper-models/{id}/download"
        )

    model = WhisperModel(
        active_model,
        device="cpu",
        compute_type="int8",
        download_root=str(WHISPER_MODEL_DIR),
    )

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )

    chunks = []
    full_parts = []
    for seg in segments:
        chunks.append({
            "start": round(seg.start, 2),
            "end":   round(seg.end, 2),
            "text":  seg.text.strip(),
        })
        full_parts.append(seg.text.strip())

    full_text = " ".join(full_parts)
    return {
        "full_text":  full_text,
        "chunks":     chunks,
        "word_count": len(full_text.split()),
        "language":   info.language,
        "model_used": active_model,
    }


def search_channel_videos(
    channel_url_or_id: str,
    max_results: int = 50,
    after_date: Optional[str] = None,
) -> list:
    """
    Search a YouTube channel for videos.
    Returns list of {url, video_id, title, published_at, duration_sec, view_count}.
    """
    try:
        import yt_dlp
        if not channel_url_or_id.startswith("http"):
            channel_url_or_id = f"https://www.youtube.com/channel/{channel_url_or_id}"

        ydl_opts = {
            "quiet": True,
            "extract_flat": True,
            "playlistend": max_results,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url_or_id, download=False)
            entries = info.get("entries", []) if info else []
            results = []
            for e in entries:
                if not e:
                    continue
                pub = e.get("upload_date", "")
                if after_date and pub and pub < after_date.replace("-", ""):
                    continue
                results.append({
                    "url":          f"https://www.youtube.com/watch?v={e.get('id', '')}",
                    "video_id":     e.get("id", ""),
                    "title":        e.get("title", ""),
                    "published_at": pub,
                    "duration_sec": e.get("duration", 0) or 0,
                    "view_count":   e.get("view_count", 0) or 0,
                })
            return results
    except ImportError:
        raise RuntimeError("yt-dlp not installed")
    except Exception as e:
        logger.warning("Channel search failed for %s: %s", channel_url_or_id, e)
        return []


def search_youtube(
    query: str,
    max_results: int = 20,
    after_date: Optional[str] = None,
) -> list:
    """Search YouTube by keyword/topic."""
    try:
        import yt_dlp
        search_url = f"ytsearch{max_results}:{query}"
        ydl_opts = {"quiet": True, "extract_flat": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
            entries = info.get("entries", []) if info else []
            results = []
            for e in entries:
                if not e:
                    continue
                pub = e.get("upload_date", "")
                if after_date and pub and pub < after_date.replace("-", ""):
                    continue
                results.append({
                    "url":          f"https://www.youtube.com/watch?v={e.get('id', '')}",
                    "video_id":     e.get("id", ""),
                    "title":        e.get("title", ""),
                    "channel_name": e.get("channel", "") or e.get("uploader", ""),
                    "channel_id":   e.get("channel_id", "") or e.get("uploader_id", ""),
                    "published_at": pub,
                    "duration_sec": e.get("duration", 0) or 0,
                    "view_count":   e.get("view_count", 0) or 0,
                })
            return results
    except Exception as e:
        logger.warning("YouTube search failed: %s", e)
        return []


def process_video_full(url: str, model_id: Optional[str] = None) -> dict:
    """
    Full pipeline: metadata → download audio → transcribe → return combined results.
    Caller is responsible for persisting results in DB.
    """
    meta = get_video_metadata(url)
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio")
        audio_file = download_audio(url, audio_path)
        transcript = transcribe_audio(audio_file, model_id=model_id)
    return {**meta, **transcript}

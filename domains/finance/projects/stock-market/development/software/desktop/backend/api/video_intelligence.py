"""
YouTube Video Intelligence System (YVIS) — REST API.

Endpoints for processing YouTube videos, tracking channels, querying signals,
and applying video-derived intelligence to the prediction engine.
"""
from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from backend.database.duckdb_client import get_conn

logger = logging.getLogger(__name__)
router = APIRouter()

# Module-level job status store  {job_id: {status, error, video_id, ...}}
_processing_jobs: dict[str, dict] = {}


# ── Request / response schemas ────────────────────────────────────────────────

class ProcessRequest(BaseModel):
    url: str
    speaker_name: Optional[str] = None
    model_id: Optional[str] = None          # whisper model override
    auto_apply_signals: bool = False


class BatchQueueRequest(BaseModel):
    urls: list[str]
    speaker_name: Optional[str] = None
    model_id: Optional[str] = None
    auto_apply_signals: bool = False


class TrackChannelRequest(BaseModel):
    channel_id: str
    channel_name: Optional[str] = None
    speaker_name: Optional[str] = None
    auto_process: bool = True
    time_range_years: int = 5


class SearchRequest(BaseModel):
    query: str
    max_results: int = 20
    after_date: Optional[str] = None        # ISO date string YYYY-MM-DD


class ApplySignalsRequest(BaseModel):
    video_id: Optional[str] = None
    signal_id: Optional[str] = None
    expires_days: int = 14


# ── Helpers ───────────────────────────────────────────────────────────────────

def _published_at_to_ts(raw: str) -> Optional[str]:
    """Convert YYYYMMDD string from yt-dlp to ISO timestamp."""
    if not raw:
        return None
    try:
        if len(raw) == 8:
            return datetime.strptime(raw, "%Y%m%d").isoformat()
        return raw  # already ISO-ish
    except Exception:
        return None


def _store_video_and_transcript(
    job_id: str,
    url: str,
    speaker_name: Optional[str],
    model_id: Optional[str],
    auto_apply: bool,
) -> None:
    """Background worker: fetch metadata → download audio → transcribe → extract signals → store."""
    conn = get_conn()
    video_db_id = _processing_jobs[job_id].get("video_db_id", str(uuid.uuid4()))

    try:
        # ── Step 1: metadata ───────────────────────────────────────────────────
        _processing_jobs[job_id]["status"] = "fetching_metadata"
        from backend.data.youtube_feed import (
            get_video_metadata, process_video_full, get_active_whisper_model
        )
        from backend.models.video_signal_extractor import extract_signals_from_transcript

        meta = get_video_metadata(url)
        pub_ts = _published_at_to_ts(meta.get("published_at", ""))

        # Upsert video_sources row
        conn.execute(
            """
            INSERT INTO video_sources
                (id, url, video_id, title, channel_name, channel_id, speaker_name,
                 published_at, duration_sec, view_count, language, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'processing', now())
            ON CONFLICT (url) DO UPDATE SET
                title = excluded.title,
                status = 'processing'
            """,
            [
                video_db_id,
                url,
                meta.get("video_id", ""),
                meta.get("title", ""),
                meta.get("channel_name", ""),
                meta.get("channel_id", ""),
                speaker_name,
                pub_ts,
                meta.get("duration_sec", 0),
                meta.get("view_count", 0),
                meta.get("language", "en"),
            ],
        )
        conn.commit()

        # ── Step 2: audio download + transcription ────────────────────────────
        _processing_jobs[job_id]["status"] = "transcribing"
        result = process_video_full(url, model_id=model_id)

        # ── Step 3: store transcript ──────────────────────────────────────────
        _processing_jobs[job_id]["status"] = "storing_transcript"
        conn.execute(
            """
            INSERT INTO transcripts
                (video_id, full_text, chunks_json, word_count, language, model_used)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (video_id) DO UPDATE SET
                full_text   = excluded.full_text,
                chunks_json = excluded.chunks_json,
                word_count  = excluded.word_count,
                model_used  = excluded.model_used
            """,
            [
                video_db_id,
                result.get("full_text", ""),
                json.dumps(result.get("chunks", [])),
                result.get("word_count", 0),
                result.get("language", "en"),
                result.get("model_used", ""),
            ],
        )

        # ── Step 4: extract signals ───────────────────────────────────────────
        _processing_jobs[job_id]["status"] = "extracting_signals"
        signals = extract_signals_from_transcript(
            transcript=result.get("full_text", ""),
            title=meta.get("title", ""),
            channel=meta.get("channel_name", "") or (speaker_name or ""),
        )

        for sig in signals:
            sig_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO video_signals
                    (id, video_id, ticker, parameter_name, domain, direction,
                     weight, confidence, key_quote, quote_ts_sec)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    sig_id,
                    video_db_id,
                    sig.get("ticker"),
                    sig.get("parameter_name", "market_sentiment"),
                    sig.get("domain", "macro"),
                    sig.get("direction", "up"),
                    sig.get("weight", 50),
                    sig.get("confidence", 0.7),
                    sig.get("key_quote", ""),
                    sig.get("quote_ts_sec", 0),
                ],
            )

        # ── Step 5: mark done ─────────────────────────────────────────────────
        conn.execute(
            """
            UPDATE video_sources
            SET status = 'done', processed_at = now(), transcript_model = ?
            WHERE id = ?
            """,
            [result.get("model_used", ""), video_db_id],
        )
        conn.commit()

        _processing_jobs[job_id].update({
            "status":     "done",
            "video_db_id": video_db_id,
            "signal_count": len(signals),
            "word_count": result.get("word_count", 0),
        })
        logger.info("YVIS processed %s — %d signals extracted", url, len(signals))

        # ── Optional: auto-apply signals to user_signals ──────────────────────
        if auto_apply and signals:
            _apply_video_signals_to_guidance(video_db_id, 14)

    except Exception as e:
        logger.error("YVIS processing failed for %s: %s", url, e, exc_info=True)
        try:
            conn.execute(
                "UPDATE video_sources SET status = 'error', error_msg = ? WHERE id = ?",
                [str(e)[:500], video_db_id],
            )
            conn.commit()
        except Exception:
            pass
        _processing_jobs[job_id].update({"status": "error", "error": str(e)})


def _apply_video_signals_to_guidance(video_db_id: str, expires_days: int) -> int:
    """
    Copy video_signals rows into user_signals for the prediction engine.

    Carries speaker/video/parameter provenance so the YVIS feedback loop
    (online_learner.resolve_video_signal_outcomes) can later attribute outcomes
    back to the speaker. The applied weight is scaled by the speaker's historical
    accuracy (signal_correlations) so proven speakers gain influence over time
    and unreliable ones are damped.
    """
    from backend.models.online_learner import get_speaker_signal_multiplier

    conn = get_conn()
    rows = conn.execute(
        """
        SELECT vs.ticker, vs.parameter_name, vs.domain, vs.direction,
               vs.weight, vs.confidence, vs.key_quote, src.title, src.url,
               src.speaker_name, src.channel_name
        FROM video_signals vs
        JOIN video_sources src ON vs.video_id = src.id
        WHERE vs.video_id = ?
        """,
        [video_db_id],
    ).fetchall()

    expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
    count = 0
    for row in rows:
        (ticker, param_name, domain, direction, weight, confidence, key_quote,
         title, url, speaker_name, channel_name) = row
        speaker = speaker_name or channel_name or ""
        extracted = 1.0 if direction == "up" else -1.0
        sig_id = str(uuid.uuid4())
        base_mult = max(0.5, min(2.0, weight / 50.0))
        # Scale by the speaker's proven track record (neutral 1.0 until enough samples).
        track_mult = get_speaker_signal_multiplier(speaker, ticker, param_name)
        weight_mult = max(0.5, min(2.0, base_mult * track_mult))
        content = f"[YVIS] {title} — {key_quote[:200]}" if key_quote else f"[YVIS] {title}"
        try:
            conn.execute(
                """
                INSERT INTO user_signals
                    (id, ticker, signal_type, domain, content, extracted_signal,
                     weight_multiplier, confidence, source_tag, created_at, expires_at, is_active,
                     speaker_name, video_id, parameter_name, horizon)
                VALUES (?, ?, 'video', ?, ?, ?, ?, ?, 'VIDEO_INTELLIGENCE', now(), ?, TRUE,
                        ?, ?, ?, '1w')
                """,
                [sig_id, ticker, domain, content, extracted, weight_mult, confidence,
                 expires_at, speaker, video_db_id, param_name],
            )
            count += 1
        except Exception as ex:
            logger.warning("Failed to apply video signal to guidance: %s", ex)

    conn.commit()
    return count


# ── Process single URL ────────────────────────────────────────────────────────

@router.post("/process", status_code=202)
def process_video(req: ProcessRequest, background_tasks: BackgroundTasks):
    """Queue a YouTube URL for processing (metadata + transcription + signal extraction)."""
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=422, detail="url cannot be empty")

    job_id     = str(uuid.uuid4())
    video_db_id = str(uuid.uuid4())
    _processing_jobs[job_id] = {
        "status":     "queued",
        "url":        req.url,
        "video_db_id": video_db_id,
        "created_at": datetime.now().isoformat(),
    }

    background_tasks.add_task(
        _store_video_and_transcript,
        job_id,
        req.url,
        req.speaker_name,
        req.model_id,
        req.auto_apply_signals,
    )

    logger.info("YVIS job queued: %s → %s", job_id, req.url)
    return {"id": job_id, "status": "queued", "url": req.url}


@router.get("/process/{job_id}/status")
def process_status(job_id: str):
    """Return current processing status for a job."""
    job = _processing_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job


# ── Video CRUD ────────────────────────────────────────────────────────────────

@router.get("/videos")
def list_videos(limit: int = 50, offset: int = 0):
    """List all processed/processing videos."""
    try:
        conn = get_conn()
        rows = conn.execute(
            """
            SELECT id, url, video_id, title, channel_name, speaker_name,
                   published_at, duration_sec, view_count, status,
                   processed_at, created_at
            FROM video_sources
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            [limit, offset],
        ).fetchall()
        cols = ["id", "url", "video_id", "title", "channel_name", "speaker_name",
                "published_at", "duration_sec", "view_count", "status",
                "processed_at", "created_at"]
        videos = [dict(zip(cols, r)) for r in rows]
        for v in videos:
            for k in ("published_at", "processed_at", "created_at"):
                if v.get(k) is not None:
                    v[k] = str(v[k])
        total = conn.execute("SELECT COUNT(*) FROM video_sources").fetchone()[0]
        return {"videos": videos, "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        logger.error("list_videos failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/videos/{video_id}")
def get_video(video_id: str):
    """Get a video record along with its transcript and signals."""
    try:
        conn = get_conn()
        v_row = conn.execute(
            "SELECT * FROM video_sources WHERE id = ?", [video_id]
        ).fetchone()
        if not v_row:
            raise HTTPException(status_code=404, detail=f"Video '{video_id}' not found")

        cols = [d[0] for d in conn.execute("DESCRIBE video_sources").fetchall()]
        video = dict(zip(cols, v_row))
        for k in ("published_at", "processed_at", "created_at"):
            if video.get(k) is not None:
                video[k] = str(video[k])

        # Transcript
        t_row = conn.execute(
            "SELECT full_text, chunks_json, word_count, language, model_used, transcribed_at "
            "FROM transcripts WHERE video_id = ?",
            [video_id],
        ).fetchone()
        transcript = None
        if t_row:
            transcript = {
                "full_text":   t_row[0],
                "chunks":      json.loads(t_row[1]) if t_row[1] else [],
                "word_count":  t_row[2],
                "language":    t_row[3],
                "model_used":  t_row[4],
                "transcribed_at": str(t_row[5]) if t_row[5] else None,
            }

        # Signals
        sig_rows = conn.execute(
            """
            SELECT id, ticker, parameter_name, domain, direction,
                   weight, confidence, key_quote, quote_ts_sec, extracted_at
            FROM video_signals WHERE video_id = ?
            ORDER BY weight DESC
            """,
            [video_id],
        ).fetchall()
        sig_cols = ["id", "ticker", "parameter_name", "domain", "direction",
                    "weight", "confidence", "key_quote", "quote_ts_sec", "extracted_at"]
        signals = [dict(zip(sig_cols, r)) for r in sig_rows]
        for s in signals:
            if s.get("extracted_at") is not None:
                s["extracted_at"] = str(s["extracted_at"])

        return {"video": video, "transcript": transcript, "signals": signals}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_video failed for %s: %s", video_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/videos/{video_id}")
def delete_video(video_id: str):
    """Delete a video and all associated transcript + signal data."""
    try:
        conn = get_conn()
        existing = conn.execute(
            "SELECT id FROM video_sources WHERE id = ?", [video_id]
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail=f"Video '{video_id}' not found")

        conn.execute("DELETE FROM video_signals WHERE video_id = ?", [video_id])
        conn.execute("DELETE FROM transcripts WHERE video_id = ?", [video_id])
        conn.execute("DELETE FROM video_sources WHERE id = ?", [video_id])
        conn.commit()
        logger.info("YVIS deleted video %s", video_id)
        return {"message": "Video and all associated data deleted", "id": video_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_video failed for %s: %s", video_id, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Signals ───────────────────────────────────────────────────────────────────

@router.get("/signals")
def get_signals(
    ticker: Optional[str] = None,
    domain: Optional[str] = None,
    direction: Optional[str] = None,
    time_range_days: int = 30,
    min_confidence: float = 0.5,
    limit: int = 100,
):
    """Query video signals with optional filters."""
    try:
        conn = get_conn()
        cutoff = (datetime.now() - timedelta(days=time_range_days)).isoformat()

        clauses = ["src.published_at >= ?", "vs.confidence >= ?"]
        params: list = [cutoff, min_confidence]

        if ticker:
            clauses.append("(vs.ticker = ? OR vs.ticker IS NULL)")
            params.append(ticker.upper())
        if domain:
            clauses.append("vs.domain = ?")
            params.append(domain.lower())
        if direction:
            clauses.append("vs.direction = ?")
            params.append(direction.lower())

        where_sql = " AND ".join(clauses)
        rows = conn.execute(
            f"""
            SELECT vs.id, vs.ticker, vs.parameter_name, vs.domain,
                   vs.direction, vs.weight, vs.confidence, vs.key_quote,
                   vs.quote_ts_sec, vs.extracted_at,
                   src.title, src.channel_name, src.speaker_name,
                   src.published_at, src.url
            FROM video_signals vs
            JOIN video_sources src ON vs.video_id = src.id
            WHERE {where_sql}
            ORDER BY src.published_at DESC, vs.weight DESC
            LIMIT ?
            """,
            params + [limit],
        ).fetchall()

        cols = ["id", "ticker", "parameter_name", "domain", "direction",
                "weight", "confidence", "key_quote", "quote_ts_sec", "extracted_at",
                "video_title", "channel_name", "speaker_name", "published_at", "url"]
        signals = [dict(zip(cols, r)) for r in rows]
        for s in signals:
            for k in ("extracted_at", "published_at"):
                if s.get(k) is not None:
                    s[k] = str(s[k])

        return {"signals": signals, "count": len(signals), "filters": {
            "ticker": ticker, "domain": domain, "direction": direction,
            "time_range_days": time_range_days, "min_confidence": min_confidence,
        }}
    except Exception as e:
        logger.error("get_signals failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signals/apply")
def apply_signals(req: ApplySignalsRequest):
    """
    Apply video signals to the prediction engine (insert into user_signals).
    Specify either video_id (apply all signals from that video) or signal_id.
    """
    if not req.video_id and not req.signal_id:
        raise HTTPException(status_code=422, detail="Provide either video_id or signal_id")
    try:
        conn = get_conn()
        expires_at = (datetime.now() + timedelta(days=req.expires_days)).isoformat()

        if req.video_id:
            count = _apply_video_signals_to_guidance(req.video_id, req.expires_days)
            return {"message": f"Applied {count} signals to prediction engine", "video_id": req.video_id}

        # Single signal
        from backend.models.online_learner import get_speaker_signal_multiplier

        sig = conn.execute(
            """
            SELECT vs.ticker, vs.parameter_name, vs.domain, vs.direction,
                   vs.weight, vs.confidence, vs.key_quote, src.title,
                   src.speaker_name, src.channel_name, vs.video_id
            FROM video_signals vs
            JOIN video_sources src ON vs.video_id = src.id
            WHERE vs.id = ?
            """,
            [req.signal_id],
        ).fetchone()
        if not sig:
            raise HTTPException(status_code=404, detail=f"Signal '{req.signal_id}' not found")

        (ticker, param_name, domain, direction, weight, confidence, key_quote,
         title, speaker_name, channel_name, video_db_id) = sig
        speaker = speaker_name or channel_name or ""
        extracted = 1.0 if direction == "up" else -1.0
        base_mult = max(0.5, min(2.0, weight / 50.0))
        track_mult = get_speaker_signal_multiplier(speaker, ticker, param_name)
        weight_mult = max(0.5, min(2.0, base_mult * track_mult))
        content = f"[YVIS] {title} — {key_quote[:200]}" if key_quote else f"[YVIS] {title}"
        new_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO user_signals
                (id, ticker, signal_type, domain, content, extracted_signal,
                 weight_multiplier, confidence, source_tag, created_at, expires_at, is_active,
                 speaker_name, video_id, parameter_name, horizon)
            VALUES (?, ?, 'video', ?, ?, ?, ?, ?, 'VIDEO_INTELLIGENCE', now(), ?, TRUE,
                    ?, ?, ?, '1w')
            """,
            [new_id, ticker, domain, content, extracted, weight_mult, confidence, expires_at,
             speaker, video_db_id, param_name],
        )
        conn.commit()
        return {"message": "Signal applied to prediction engine", "signal_id": req.signal_id, "user_signal_id": new_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("apply_signals failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Channel tracking ──────────────────────────────────────────────────────────

@router.post("/channels/track", status_code=201)
def track_channel(req: TrackChannelRequest):
    """Add a YouTube channel to the auto-track list."""
    try:
        conn = get_conn()
        conn.execute(
            """
            INSERT INTO channel_tracks
                (channel_id, channel_name, speaker_name, auto_process, time_range_years, created_at)
            VALUES (?, ?, ?, ?, ?, now())
            ON CONFLICT (channel_id) DO UPDATE SET
                channel_name     = excluded.channel_name,
                speaker_name     = excluded.speaker_name,
                auto_process     = excluded.auto_process,
                time_range_years = excluded.time_range_years
            """,
            [
                req.channel_id,
                req.channel_name or req.channel_id,
                req.speaker_name,
                req.auto_process,
                req.time_range_years,
            ],
        )
        conn.commit()
        logger.info("YVIS tracking channel %s (%s)", req.channel_id, req.speaker_name)
        return {
            "message":      "Channel added to tracking list",
            "channel_id":   req.channel_id,
            "speaker_name": req.speaker_name,
        }
    except Exception as e:
        logger.error("track_channel failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channels")
def list_channels():
    """Return all tracked channels."""
    try:
        conn = get_conn()
        rows = conn.execute(
            """
            SELECT channel_id, channel_name, speaker_name, auto_process,
                   time_range_years, last_checked_at, created_at
            FROM channel_tracks
            ORDER BY created_at DESC
            """,
        ).fetchall()
        cols = ["channel_id", "channel_name", "speaker_name", "auto_process",
                "time_range_years", "last_checked_at", "created_at"]
        channels = [dict(zip(cols, r)) for r in rows]
        for c in channels:
            for k in ("last_checked_at", "created_at"):
                if c.get(k) is not None:
                    c[k] = str(c[k])
        return {"channels": channels, "count": len(channels)}
    except Exception as e:
        logger.error("list_channels failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/channels/{channel_id}")
def untrack_channel(channel_id: str):
    """Remove a channel from the tracking list."""
    try:
        conn = get_conn()
        existing = conn.execute(
            "SELECT channel_id FROM channel_tracks WHERE channel_id = ?", [channel_id]
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail=f"Channel '{channel_id}' not tracked")
        conn.execute("DELETE FROM channel_tracks WHERE channel_id = ?", [channel_id])
        conn.commit()
        logger.info("YVIS untracked channel %s", channel_id)
        return {"message": "Channel removed from tracking list", "channel_id": channel_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("untrack_channel failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── YouTube search ────────────────────────────────────────────────────────────

@router.post("/search")
def search_youtube(req: SearchRequest):
    """Search YouTube by topic or ticker keyword."""
    try:
        from backend.data.youtube_feed import search_youtube as _search
        results = _search(
            query=req.query,
            max_results=min(req.max_results, 50),
            after_date=req.after_date,
        )
        return {"results": results, "count": len(results), "query": req.query}
    except Exception as e:
        logger.error("search_youtube API failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Batch queue ───────────────────────────────────────────────────────────────

@router.post("/batch-queue", status_code=202)
def batch_queue(req: BatchQueueRequest, background_tasks: BackgroundTasks):
    """Queue multiple YouTube URLs for processing."""
    if not req.urls:
        raise HTTPException(status_code=422, detail="urls list cannot be empty")
    if len(req.urls) > 50:
        raise HTTPException(status_code=422, detail="Maximum 50 URLs per batch")

    job_ids = []
    for url in req.urls:
        url = url.strip()
        if not url:
            continue
        job_id     = str(uuid.uuid4())
        video_db_id = str(uuid.uuid4())
        _processing_jobs[job_id] = {
            "status":      "queued",
            "url":         url,
            "video_db_id": video_db_id,
            "created_at":  datetime.now().isoformat(),
        }
        background_tasks.add_task(
            _store_video_and_transcript,
            job_id,
            url,
            req.speaker_name,
            req.model_id,
            req.auto_apply_signals,
        )
        job_ids.append({"job_id": job_id, "url": url})

    logger.info("YVIS batch queued %d URLs", len(job_ids))
    return {"queued": len(job_ids), "jobs": job_ids}


@router.get("/queue/status")
def queue_status():
    """Return status of all current and recent processing jobs."""
    jobs = []
    for job_id, info in _processing_jobs.items():
        jobs.append({"job_id": job_id, **info})
    # Sort most recent first (by created_at string; ISO format sorts lexicographically)
    jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
    counts = {
        "total":        len(jobs),
        "queued":       sum(1 for j in jobs if j["status"] == "queued"),
        "processing":   sum(1 for j in jobs if j["status"] not in ("done", "error", "queued")),
        "done":         sum(1 for j in jobs if j["status"] == "done"),
        "error":        sum(1 for j in jobs if j["status"] == "error"),
    }
    return {"jobs": jobs[:100], "counts": counts}  # cap at 100 to avoid huge payloads


# ── Whisper models ────────────────────────────────────────────────────────────

@router.get("/whisper-models")
def list_whisper_models():
    """List available whisper models with download status."""
    try:
        from backend.data.youtube_feed import get_model_info
        models = get_model_info()
        return {"models": models}
    except Exception as e:
        logger.error("list_whisper_models failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


_whisper_download_jobs: dict[str, dict] = {}


def _download_whisper_bg(model_id: str) -> None:
    from backend.data.youtube_feed import download_whisper_model
    def _progress(pct: int, msg: str) -> None:
        _whisper_download_jobs[model_id] = {"status": "downloading", "progress": pct, "message": msg}

    try:
        _whisper_download_jobs[model_id] = {"status": "downloading", "progress": 0, "message": "Starting..."}
        download_whisper_model(model_id, progress_cb=_progress)
        _whisper_download_jobs[model_id] = {"status": "done", "progress": 100, "message": "Download complete"}
    except Exception as e:
        _whisper_download_jobs[model_id] = {"status": "error", "message": str(e)}
        logger.error("Whisper model %s download failed: %s", model_id, e)


@router.post("/whisper-models/{model_id}/download", status_code=202)
def download_whisper_model(model_id: str):
    """Start downloading a whisper model in the background."""
    from backend.data.youtube_feed import WHISPER_MODELS, is_model_downloaded

    valid_ids = {m["id"] for m in WHISPER_MODELS}
    if model_id not in valid_ids:
        raise HTTPException(status_code=404, detail=f"Unknown model '{model_id}'. Valid: {sorted(valid_ids)}")

    if is_model_downloaded(model_id):
        return {"status": "already_downloaded", "model_id": model_id}

    if _whisper_download_jobs.get(model_id, {}).get("status") == "downloading":
        return {"status": "already_downloading", "model_id": model_id}

    thread = threading.Thread(target=_download_whisper_bg, args=(model_id,), daemon=True)
    thread.start()
    return {"status": "started", "model_id": model_id, "message": f"Downloading {model_id} in background"}


@router.get("/whisper-models/{model_id}/download/status")
def whisper_download_status(model_id: str):
    """Return download progress for a whisper model."""
    from backend.data.youtube_feed import is_model_downloaded
    if is_model_downloaded(model_id):
        return {"status": "done", "model_id": model_id, "progress": 100}
    job = _whisper_download_jobs.get(model_id)
    if not job:
        return {"status": "not_started", "model_id": model_id}
    return {"model_id": model_id, **job}


# ── Speakers ──────────────────────────────────────────────────────────────────

@router.get("/speakers")
def list_speakers():
    """Return pre-seeded influential speaker presets."""
    from backend.data.youtube_feed import INFLUENTIAL_SPEAKERS
    conn = get_conn()
    tracked_ids = {
        r[0] for r in conn.execute("SELECT channel_id FROM channel_tracks").fetchall()
    }
    result = []
    for s in INFLUENTIAL_SPEAKERS:
        result.append({
            **s,
            "is_tracked": s["channel_id"] in tracked_ids,
        })
    return {"speakers": result}


# ── Feedback loop (Layer 5 ← Layer 6) ────────────────────────────────────────

@router.post("/signals/resolve")
def resolve_signals():
    """
    Resolve elapsed applied video signals against realised price moves and refresh
    per-speaker accuracy (signal_correlations). Normally runs nightly via the
    scheduler; this endpoint triggers it on demand for testing.
    """
    try:
        from backend.models.online_learner import (
            resolve_video_signal_outcomes,
            update_speaker_correlations,
        )
        n = resolve_video_signal_outcomes()
        speakers = update_speaker_correlations()
        return {"resolved": n, "speakers_updated": len(speakers), "speakers": speakers}
    except Exception as e:
        logger.error("resolve_signals failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/speakers/correlations")
def speaker_correlations(speaker_name: str | None = None, limit: int = 100):
    """Return learned per-speaker accuracy and influence multipliers."""
    try:
        from backend.models.online_learner import get_speaker_signal_multiplier
        conn = get_conn()
        if speaker_name:
            rows = conn.execute(
                "SELECT speaker_name, ticker, parameter_name, hist_accuracy, sample_size, updated_at "
                "FROM signal_correlations WHERE speaker_name = ? ORDER BY sample_size DESC LIMIT ?",
                [speaker_name, limit],
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT speaker_name, ticker, parameter_name, hist_accuracy, sample_size, updated_at "
                "FROM signal_correlations ORDER BY sample_size DESC LIMIT ?",
                [limit],
            ).fetchall()
        out = []
        for r in rows:
            out.append({
                "speaker_name":   r[0],
                "ticker":         r[1],
                "parameter_name": r[2],
                "hist_accuracy":  r[3],
                "sample_size":    r[4],
                "multiplier":     get_speaker_signal_multiplier(r[0], r[1], r[2]),
                "updated_at":     str(r[5]),
            })
        return {"correlations": out, "count": len(out)}
    except Exception as e:
        logger.error("speaker_correlations failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Aggregated intelligence per ticker ───────────────────────────────────────

@router.get("/intelligence/{ticker}")
def get_intelligence(ticker: str, time_range_days: int = 30, min_confidence: float = 0.6):
    """
    Return aggregated video-derived intelligence for a specific ticker.
    Includes direction consensus, signal strength, and top supporting signals.
    """
    try:
        from backend.models.video_signal_extractor import aggregate_signals_for_ticker
        result = aggregate_signals_for_ticker(
            ticker=ticker.upper(),
            time_range_days=time_range_days,
            min_confidence=min_confidence,
        )
        return result
    except Exception as e:
        logger.error("get_intelligence failed for %s: %s", ticker, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

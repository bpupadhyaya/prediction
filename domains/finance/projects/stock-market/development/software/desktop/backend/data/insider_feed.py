"""
SEC EDGAR Form 4 insider-transaction feed — Tier-1 insider activity (real, free).

Source: SEC EDGAR submissions + filing documents (data.sec.gov / www.sec.gov).
For a ticker we read recent Form 4 filings, parse the non-derivative open-market
transactions (code P = purchase, S = sale), and derive a net-buy score in [-1, 1]
plus 30-day buy/sell cluster counts. These populate the previously zero-defaulted
features insider_net_buy_score / form4_sentiment_score / insider_buy_cluster_30d.

SEC fair-access rules: a descriptive User-Agent is required and requests are
rate-limited to <10/s. All network failures degrade to a neutral (zero) score.
"""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET

import requests

logger = logging.getLogger(__name__)

_UA = {"User-Agent": "prediction-research (bpupadhyaya5@gmail.com)"}
_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{doc}"

_cik_map: dict[str, int] | None = None
_NEUTRAL = {
    "insider_net_buy_score": 0.0,
    "form4_sentiment_score": 0.0,
    "insider_buy_cluster_30d": 0.0,
    "insider_sell_cluster_30d": 0.0,
}


def _get(url: str, **kw):
    """Polite SEC GET — required UA + small delay to respect <10 req/s."""
    time.sleep(0.12)
    return requests.get(url, headers=_UA, timeout=20, **kw)


def _load_cik_map() -> dict[str, int]:
    global _cik_map
    if _cik_map is not None:
        return _cik_map
    try:
        data = _get(_TICKERS_URL).json()
        _cik_map = {row["ticker"].upper(): int(row["cik_str"]) for row in data.values()}
    except Exception as e:
        logger.warning(f"SEC ticker→CIK map fetch failed: {e}")
        _cik_map = {}
    return _cik_map


def _parse_form4(xml_text: str) -> list[tuple[str, float, float]]:
    """Return [(code, shares, price)] for non-derivative transactions in a Form 4."""
    out: list[tuple[str, float, float]] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out
    for txn in root.iter("nonDerivativeTransaction"):
        code_el = txn.find(".//transactionCoding/transactionCode")
        shares_el = txn.find(".//transactionAmounts/transactionShares/value")
        price_el = txn.find(".//transactionAmounts/transactionPricePerShare/value")
        if code_el is None or code_el.text is None:
            continue
        code = code_el.text.strip().upper()
        try:
            shares = float(shares_el.text) if shares_el is not None and shares_el.text else 0.0
            price = float(price_el.text) if price_el is not None and price_el.text else 0.0
        except (TypeError, ValueError):
            continue
        out.append((code, shares, price))
    return out


def fetch_insider_score(ticker: str, lookback_days: int = 90, max_filings: int = 40) -> dict:
    """
    Compute insider activity scores for a ticker from recent Form 4 filings.

    net_buy_score = (buy_value - sell_value) / (buy_value + sell_value), in [-1, 1].
    Returns a neutral (all-zero) dict on any failure or when no filings are found.
    """
    cik = _load_cik_map().get(ticker.upper())
    if not cik:
        return dict(_NEUTRAL)

    try:
        subs = _get(_SUBMISSIONS.format(cik=cik)).json()
        recent = subs["filings"]["recent"]
    except Exception as e:
        logger.debug(f"SEC submissions fetch failed for {ticker}: {e}")
        return dict(_NEUTRAL)

    cutoff = datetime.today().date() - timedelta(days=lookback_days)
    cutoff_30 = datetime.today().date() - timedelta(days=30)

    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accs = recent.get("accessionNumber", [])
    docs = recent.get("primaryDocument", [])

    buy_value = sell_value = 0.0
    buy_cluster = sell_cluster = 0
    seen = 0

    for i, form in enumerate(forms):
        if form != "4":
            continue
        try:
            fdate = datetime.strptime(dates[i], "%Y-%m-%d").date()
        except (ValueError, IndexError):
            continue
        if fdate < cutoff:
            continue
        if seen >= max_filings:
            break
        seen += 1

        acc_nodash = accs[i].replace("-", "")
        # The primaryDocument is sometimes an xSLF viewer path; the raw XML is the
        # same filename without the "xslF345X0n/" prefix.
        doc = re.sub(r"^xslF345X0\d/", "", docs[i])
        url = _ARCHIVE.format(cik=cik, acc_nodash=acc_nodash, doc=doc)
        try:
            xml_text = _get(url).text
        except Exception:
            continue

        for code, shares, price in _parse_form4(xml_text):
            value = shares * price
            if code == "P":          # open-market purchase
                buy_value += value
                if fdate >= cutoff_30:
                    buy_cluster += 1
            elif code == "S":        # open-market sale
                sell_value += value
                if fdate >= cutoff_30:
                    sell_cluster += 1

    denom = buy_value + sell_value
    net = (buy_value - sell_value) / denom if denom > 0 else 0.0
    return {
        "insider_net_buy_score": round(net, 4),
        "form4_sentiment_score": round(net, 4),
        "insider_buy_cluster_30d": float(buy_cluster),
        "insider_sell_cluster_30d": float(sell_cluster),
    }


def store_insider_signal(ticker: str, score: dict) -> None:
    """Upsert a ticker's insider score into the insider_signals table."""
    from backend.database.duckdb_client import get_conn

    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO insider_signals
                (ticker, insider_net_buy_score, form4_sentiment_score,
                 insider_buy_cluster_30d, insider_sell_cluster_30d, updated_at)
            VALUES (?, ?, ?, ?, ?, now())
            ON CONFLICT (ticker) DO UPDATE SET
                insider_net_buy_score    = excluded.insider_net_buy_score,
                form4_sentiment_score    = excluded.form4_sentiment_score,
                insider_buy_cluster_30d  = excluded.insider_buy_cluster_30d,
                insider_sell_cluster_30d = excluded.insider_sell_cluster_30d,
                updated_at               = now()
        """, [ticker.upper(), score["insider_net_buy_score"], score["form4_sentiment_score"],
              score["insider_buy_cluster_30d"], score["insider_sell_cluster_30d"]])
        conn.commit()
    except Exception as e:
        logger.debug(f"store_insider_signal failed for {ticker}: {e}")


def refresh_insider_signal(ticker: str) -> dict:
    """Fetch + persist insider score for one ticker. Best-effort."""
    score = fetch_insider_score(ticker)
    store_insider_signal(ticker, score)
    return score


def load_insider_map() -> dict[str, dict]:
    """Return {ticker: insider score dict} for all stored signals (for training)."""
    from backend.database.duckdb_client import get_conn

    conn = get_conn()
    try:
        df = conn.execute("""
            SELECT ticker, insider_net_buy_score, form4_sentiment_score,
                   insider_buy_cluster_30d, insider_sell_cluster_30d
            FROM insider_signals
        """).df()
        return {
            r["ticker"]: {
                "insider_net_buy_score": float(r["insider_net_buy_score"]),
                "form4_sentiment_score": float(r["form4_sentiment_score"]),
                "insider_buy_cluster_30d": float(r["insider_buy_cluster_30d"]),
                "insider_sell_cluster_30d": float(r["insider_sell_cluster_30d"]),
            }
            for _, r in df.iterrows()
        }
    except Exception:
        return {}

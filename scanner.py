#!/usr/bin/env python3
"""
AI Agent Crypto Radar — Scanner
Fetches data for 30+ autonomous AI agent tokens, scores them,
and outputs JSON + standalone HTML dashboard.

Sources (all free, zero API keys):
  - CoinGecko: prices, market cap, volume, change %, ATH
  - DeFiLlama: total DeFi TVL (context data)
"""

import json
import sys
import time
import os
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

# ─── Config ──────────────────────────────────────────────────────────────────

COINGECKO_API = "https://api.coingecko.com/api/v3"
HEADERS = {"User-Agent": "AIAgentRadar/1.0", "Accept": "application/json"}
TIMEOUT = 30

SECTORS = {
    # Virtuals Protocol ecosystem
    "virtuals": ["virtuals-protocol", "aixbt-by-virtuals", "ai16z", "goatseus-maximus", "luna-by-virtuals", "aixcb", "zero-by-virtuals"],
    # ASI Alliance (merged FET/AGIX/ROSE)
    "asi": ["artificial-superintelligence-alliance", "fetch-ai", "singularitynet", "ocean-protocol", "alethea-artificial-liquid-intelligence-token"],
    # AI Infrastructure
    "infra": ["bittensor", "render", "matrix-ai-network", "deepbrain-chain", "morpheus-network", "numeraire"],
    # AI Companions / Consumer AI
    "agents": ["sentio", "brainlet", "ai-companions", "ai9", "aixbt-by-virtuals", "cookie3", "vaiot"],
    # Meme AI agents
    "meme-ai": ["griffain", "truthchain", "goatseus-maximus", "luna-by-virtuals", "ai16z", "aixbt-by-virtuals"],
    # DeFi AI automation
    "defi-ai": ["moxie", "anzen-finance", "synesis-one", "0xagent", "ai-rig-complex", "codex-3-codex-bet"],
}


@dataclass
class TokenData:
    id: str
    name: str
    symbol: str
    current_price: float
    market_cap: float
    market_cap_rank: int
    total_volume: float
    price_change_24h: float
    price_change_percentage_24h: float
    price_change_percentage_7d: float
    price_change_percentage_30d: float
    ath: float
    ath_change_percentage: float
    ath_date: str
    sector: str
    composite_score: float = 0.0
    score_label: str = ""


# ─── Fetchers ────────────────────────────────────────────────────────────────

def fetch_json(url: str, retries: int = 3) -> dict | list | None:
    """Fetch JSON from URL with retries and exponential backoff."""
    for attempt in range(retries):
        try:
            req = Request(url, headers=HEADERS)
            with urlopen(req, timeout=TIMEOUT) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            wait = 2 ** attempt
            print(f"  ⚠ Retry {attempt + 1}/{retries} — {e}", file=sys.stderr)
            time.sleep(wait)
    return None


def fetch_agents(ids: list[str]) -> list[dict]:
    """Fetch market data for all AI agent tokens."""
    # CoinGecko free API only allows IDs as comma-separated in /coins/markets
    # For many IDs, we split into batches
    all_data = []
    batches = [ids[i:i+15] for i in range(0, len(ids), 15)]

    for batch in batches:
        ids_str = ",".join(batch)
        url = (
            f"{COINGECKO_API}/coins/markets"
            f"?vs_currency=usd"
            f"&ids={ids_str}"
            f"&order=market_cap_desc"
            f"&per_page=250"
            f"&sparkline=false"
            f"&price_change_percentage=24h,7d,30d"
        )
        print(f"  Fetching batch: {len(batch)} tokens...", file=sys.stderr)
        data = fetch_json(url)
        if data:
            all_data.extend(data)
        else:
            print(f"  ❌ Failed to fetch batch: {batch[:3]}...", file=sys.stderr)
        time.sleep(1.2)  # CoinGecko free rate limit

    return all_data


def fetch_defi_tvl() -> float:
    """Fetch total DeFi TVL for context."""
    data = fetch_json("https://api.llama.fi/v2/historicalChainTvl")
    if data and len(data) > 0:
        return data[-1].get("tvl", 0)
    return 0


# ─── Sector detection ────────────────────────────────────────────────────────

def detect_sector(token_id: str) -> str:
    """Determine the primary sector for a token."""
    # Check specialized sectors first (more specific = higher priority)
    for sector in ["meme-ai", "defi-ai", "asi", "virtuals", "agents", "infra"]:
        if token_id in SECTORS.get(sector, []):
            return sector
    return "other"


# ─── Scoring ─────────────────────────────────────────────────────────────────

def compute_score(t: dict) -> tuple[float, str]:
    """
    Composite score 0-100 for an AI agent token.

    Factors:
    - Momentum (24h + 7d + 30d): 35%
    - Volume activity: 15%
    - Market cap rank (lower = better): 15%
    - ATH distance (closer is stronger trend): 10%
    - Overall crypto market context (BTC): 10%
    - Sector momentum: 15%
    """
    scores = []

    # 24h momentum (0-15): normalize -20%..+50% → 0-100 → 0-15
    ch24 = t.get("price_change_percentage_24h", 0) or 0
    mom_24 = max(0, min(100, (ch24 + 20) / 70 * 100))
    scores.append(mom_24 * 0.15)

    # 7d momentum (0-25): normalize -30%..+100% → 0-100 → 0-25
    ch7d = t.get("price_change_percentage_7d_in_currency", 0) or 0
    mom_7d = max(0, min(100, (ch7d + 30) / 130 * 100))
    scores.append(mom_7d * 0.25)

    # 30d momentum (0-10): same normalization
    ch30 = t.get("price_change_percentage_30d", 0) or 0
    mom_30 = max(0, min(100, (ch30 + 40) / 140 * 100))
    scores.append(mom_30 * 0.10)

    # Volume activity (0-15): volume/mcap ratio * 1000 → 0-100
    vol = t.get("total_volume", 0) or 0
    mcap = t.get("market_cap", 0) or 0
    vol_ratio = (vol / mcap * 1000) if mcap > 0 else 0
    vol_score = min(100, vol_ratio * 300)
    scores.append(vol_score * 0.15)

    # Market cap rank (0-15): rank 1 = 100, rank 500+  = 0
    rank = t.get("market_cap_rank", 500) or 500
    rank_score = max(0, 100 - (rank / 500 * 100))
    scores.append(rank_score * 0.15)

    # ATH distance (0-10): at 0% from ATH = 100, at -90% = 0
    ath_chg = t.get("ath_change_percentage", -90) or -90
    ath_score = max(0, min(100, 100 + ath_chg))
    scores.append(ath_score * 0.10)

    # Sector momentum (0-10): simplified from sector average 24h change
    sector = detect_sector(t["id"])
    sector_tokens = [sid for sid in SECTORS.get(sector, []) if sid != t["id"]]
    # We'd need to batch-fetch all to get this properly; for now use token's
    # 24h change as proxy for sector momentum
    sector_score = min(100, max(0, 50 + (ch24 * 2)))
    scores.append(sector_score * 0.10)

    total = sum(scores)
    total = max(0, min(100, total))

    if total >= 70:
        label = "🔥 STRONG"
    elif total >= 55:
        label = "📈 UPTREND"
    elif total >= 40:
        label = "🟡 NEUTRAL"
    elif total >= 25:
        label = "📉 DOWNTREND"
    else:
        label = "❄️ WEAK"

    return round(total, 1), label


# ─── Main ────────────────────────────────────────────────────────────────────

     print(f"{'='*60}\n", file=sys.stderr)

    # Top 10
    print(f"  {'Rank':<5} {'Name':<20} {'Price':>12} {'24h':>8} {'7d':>8} {'Score':>6} {'Signal':<12}", file=sys.stderr)
    print(f"  {'─'*4} {'─'*18} {'─'*12} {'─'*6} {'─'*6} {'─'*5} {'─'*10}", file=sys.stderr)
    for i, t in enumerate(result["tokens"][:10], 1):
        price = t["current_price"]
        price_str = f"${price:,.4f}" if price < 1 else f"${price:,.2f}"
        ch24 = f"{'▼' if t['price_change_percentage_24h'] < 0 else '▲'}{abs(t['price_change_percentage_24h']):.1f}%"
        ch7d = f"{'▼' if t['price_change_percentage_7d'] < 0 else '▲'}{abs(t['price_change_percentage_7d']):.1f}%"
        print(f"  {i:<5} {t['name']:<20} {price_str:>12} {ch24:>8} {ch7d:>8} {t['composite_score']:>5.0f} {t['score_label']:<12}", file=sys.stderr)

    # Sector summary
    print(f"\n  {'Sector':<12} {'Count':>6} {'Avg Score':>10} {'Avg 24h':>10}", file=sys.stderr)
    print(f"  {'─'*10} {'─'*4} {'─'*9} {'─'*8}")
    for s, d in sorted(result["sector_summary"].items(), key=lambda x: x[1]["avg_score"], reverse=True):
        print(f"  {s:<12} {d['count']:>6} {d['avg_score']:>9.1f} {d['avg_change_24h']:>+9.1f}%", file=sys.stderr)

    print(f"\n✅ Done. {len(result['tokens'])} tokens scored.\n", file=sys.stderr)


if __name__ == "__main__":
    main()
Add error handling to scanner.py

   
# 🤖 AI Agent Crypto Radar

**Real-time tracker and scorer for 30+ autonomous AI agent tokens.**

Monitors the AI agent crypto sector — tokens like Virtuals Protocol (VIRTUAL), Bittensor (TAO), AI16z, and more — with composite scoring, sector analysis, and a live dashboard.

---

## 🌐 Live Dashboard

👉 **https://lolarok.github.io/ai-agent-radar/**

---

## How It Works

1. **Scanner** (`scanner.py`) fetches live data from CoinGecko and DeFiLlama
2. Each token gets a **composite score (0-100)** based on:
   - Price momentum (24h, 7d, 30d) — 50%
   - Volume activity — 15%
   - Market cap rank — 15%
   - ATH distance — 10%
   - Sector momentum — 10%
3. Tokens are classified: 🔥 STRONG, 📈 UPTREND, 🟡 NEUTRAL, 📉 DOWNTREND, ❄️ WEAK
4. Results are grouped by **sector** (ASI, Virtuals, Infra, Meme-AI, DeFi-AI, Agents)
5. A **static HTML dashboard** is generated with sorting, filtering, and sector cards

## Features

- Zero API keys needed (CoinGecko free + DeFiLlama free)
- 30+ AI agent tokens tracked
- Sector classification and summary cards
- Sortable table with 10 sortable columns
- Dark-themed dashboard, mobile-friendly
- Runs automatically every 6 hours via GitHub Actions

## Sectors

| Sector | Description | Examples |
|--------|-------------|----------|
| **ASI** | ASI Alliance tokens (merged intelligence) | FET, AGIX, OCEAN |
| **Virtuals** | Virtuals Protocol ecosystem | VIRTUAL, AIXBT, GOAT |
| **Infra** | AI infrastructure & compute | TAO, RNDR, MWA |
| **Agents** | Consumer AI agents & assistants | Sentio, Brainlet |
| **Meme-AI** | AI agent meme coins | GRIFFAIN, TRUTH |
| **DeFi-AI** | AI-powered DeFi automation | MOXIE, Anzen |

## Running Locally

```bash
git clone https://github.com/Lolarok/ai-agent-radar.git
cd ai-agent-radar
python3 scanner.py
# Open public/index.html in browser
```

No pip install needed — uses only Python stdlib.

## Project Structure

```
ai-agent-radar/
├── config.json         # Token watchlist and settings
├── scanner.py          # Main scanner (CLI)
├── public/
│   ├── index.html      # Dashboard (standalone, no build)
│   └── ai-agents.json  # Latest scan results
└── .github/workflows/
    └── scan.yml        # Auto-scan every 6 hours → deploy to Pages
```

## Score Breakdown

```
>65   🔥 STRONG
55-65 📈 UPTREND
40-55 🟡 NEUTRAL
25-40 📉 DOWNTREND
<25   ❄️ WEAK
```

## Disclaimer

Scores are composite technical signals — NOT financial advice. DYOR.

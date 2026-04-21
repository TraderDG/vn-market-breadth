# VN Market Breadth — Project Tracker

## Mục tiêu
Dashboard theo dõi Market Breadth thị trường chứng khoán Việt Nam (VN100 / VNINDEX).
26 indicators chia thành 5 nhóm: A/D, NH-NL, Volume, % above MA, Return-Based.

## Tech Stack
- **Backend:** Python 3.11, FastAPI, SQLAlchemy, PostgreSQL (TimescaleDB), APScheduler, Pandas
- **Frontend:** React 18, TypeScript, TradingView Lightweight Charts, React Query, Tailwind CSS
- **Infra:** Docker Compose, Nginx

## Data Sources (VMT Drive)
- `Advances_VN100.csv` / `Declines_VN100.csv` — raw daily A/D
- `VNINDEX_A-D_line_Data.csv` — A/D line precomputed
- `NH_NL_Subtraction_VNINDEX_Data.csv` — New High/New Low
- `Market_Breadth__aboveMA_VNINDEX_Data.csv` — % above MA10/20/50/100/200
- `market_breadth_vn100_returndaily_ADratio.csv` — AD ratio ±2%
- `market_breadth_vn100_quarterlyreturn.csv` — quarterly breadth
- `VNINDEX_processed_with_volume_thrust.csv` — Up/Down Volume
- `UpVolume_pct_merged.csv` — Up Volume %

---

## Indicators (26 total)

### Group A: A/D Based
| # | Indicator | Formula | Data Needed |
|---|-----------|---------|-------------|
| 1 | A/D Line | cumsum(A - D) | Advances, Declines |
| 2 | McClellan Oscillator | EMA(19, A-D) - EMA(39, A-D) | A, D |
| 3 | McClellan Summation Index | cumsum(McClellan Osc) | above |
| 4 | A/D Ratio 5d | rolling(5, A/(A+D)) | A, D |
| 5 | A/D Ratio 10d | rolling(10, A/(A+D)) | A, D |
| 6 | Breadth Thrust (Zweig) | EMA(10, A/(A+D)) | A, D |
| 7 | A/D Line Oscillator | MA(10, ADL) - MA(30, ADL) | ADL |
| 8 | Absolute Breadth Index | EMA(21, |A - D|) | A, D |
| 9 | ROC5 of A/D | (ADt - ADt-5) / ADt-5 * 100 | ADL |

### Group B: New High / New Low
| # | Indicator | Formula | Data Needed |
|---|-----------|---------|-------------|
| 10 | NH-NL Line | cumsum(NH - NL) | NH, NL daily |
| 11 | NH-NL Oscillator | EMA(10, NH-NL) | NH, NL |
| 12 | NH-NL Ratio | NH / (NH + NL), 10d smooth | NH, NL |
| 13 | Hindenburg Omen | signal: NH%>2.2% & NL%>2.2% & MCO<0 | NH, NL, MCO |

### Group C: Volume Breadth
| # | Indicator | Formula | Data Needed |
|---|-----------|---------|-------------|
| 14 | Up/Down Volume Ratio | UV / DV | Up Vol, Down Vol |
| 15 | Up Volume % | UV / (UV + DV) * 100 | UV, DV |
| 16 | Net Up Volume (10d EMA) | EMA(10, UV - DV) | UV, DV |
| 17 | Volume Thrust Signal | UV% > 90% in 10-day window | UV% |

### Group D: % Above MA (Non-internal breadth)
| # | Indicator | Formula | Data Needed |
|---|-----------|---------|-------------|
| 18 | % Stocks above MA10 | count(close > MA10) / N | Individual prices |
| 19 | % Stocks above MA20 | count(close > MA20) / N | |
| 20 | % Stocks above MA50 | count(close > MA50) / N | |
| 21 | % Stocks above MA100 | count(close > MA100) / N | |
| 22 | % Stocks above MA200 | count(close > MA200) / N | |
| 23 | Participation Index | VMT custom composite | VMT formula |
| 24 | Disparity Index | (VNINDEX / MA150 - 1) * 100 | VNINDEX price |

### Group E: Return-Based Breadth
| # | Indicator | Formula | Data Needed |
|---|-----------|---------|-------------|
| 25 | Daily Return AD Ratio | count(ret>=+2%) / count(ret<=-2%) | Daily returns |
| 26 | Quarterly Return Breadth | count(qret>=+10%) vs count(qret<=-10%) | Quarterly returns |

---

## Project Structure
```
vn-market-breadth/
├── PROJECT.md                   ← this file
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   ├── routers/
│   │   │   ├── breadth.py
│   │   │   ├── indicators.py
│   │   │   └── signals.py
│   │   └── services/
│   │       ├── calculator.py
│   │       ├── data_loader.py
│   │       └── scheduler.py
│   ├── data/                    ← CSV files từ VMT Drive
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── api/
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

---

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Backend: FastAPI + DB + Calculator + APIs | ✅ Done |
| 2 | Frontend: React + Charts + All Panels | ✅ Done |
| 3 | Data Pipeline + Signals History | ✅ Done (embedded in Phase 1+2) |
| 4 | Docker + Deploy | ✅ Done |

---

## Phase 1 Checklist ✅ DONE
- [x] Project structure created
- [x] `database.py` — PostgreSQL connection + TimescaleDB
- [x] `models.py` — SQLAlchemy market_breadth_daily table
- [x] `schemas.py` — Pydantic response models
- [x] `calculator.py` — tính 26 indicators từ raw data
- [x] `data_loader.py` — import CSV vào DB + signal event detection
- [x] `routers/breadth.py` — /api/v1/breadth/overview, /historical, /latest-n
- [x] `routers/indicators.py` — /api/v1/indicators/list, /{name}
- [x] `routers/signals.py` — /api/v1/signals/active, /history, /stats
- [x] `main.py` — FastAPI app + CORS + lifespan
- [x] `scheduler.py` — APScheduler daily 18:30 HCM
- [x] `requirements.txt` + `Dockerfile` + `docker-compose.yml`
- [x] `import_data.py` — standalone script import CSV
- [ ] Test all endpoints (cần có DB + CSV files)

## Phase 2 Checklist
- [ ] React project setup (Vite + TypeScript + Tailwind)
- [ ] API client (React Query + axios)
- [ ] BreadthMeter component (gauge)
- [ ] DualChart component (VNINDEX + indicator overlay)
- [ ] Overview page
- [ ] AD Line page
- [ ] NH-NL page
- [ ] Volume Breadth page
- [ ] % Above MA page
- [ ] Signals History page

## Phase 3 Checklist
- [ ] APScheduler daily update job
- [ ] Data fetcher (from TCBS / SSI API or manual CSV update)
- [ ] Forward returns calculator for signal events
- [ ] Signals history table with statistics

## Phase 4 Checklist
- [ ] docker-compose.yml (backend + frontend + postgres)
- [ ] Nginx config
- [ ] Deploy to VPS

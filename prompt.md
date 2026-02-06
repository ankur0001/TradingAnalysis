I wanted to make ITOS :

# 📘 ITOS — Intraday Trading Operating System

## 1. WHAT THIS PROJECT IS

ITOS is **not**:

* a single strategy
* a bot
* an ML black box

ITOS **is**:

> A modular, data-driven intraday trading operating system that
> designs, evaluates, filters, and deploys **500+ intraday strategies**
> across **hundreds of stocks** using **rule-based intelligence**.

The system answers one core question **every trading minute**:

> “Under *current market conditions*,
> **which stock** + **which strategy** is allowed to trade — if any?”

---

## 2. WHAT DATA WE HAVE (FOUNDATION)

### Dataset

* 8–10 years of **1-minute OHLCV**
* ~300–500 Indian stocks
* Multiple market regimes:

  * Bull
  * Bear
  * Sideways
  * High / Low volatility
* Stored as **per-symbol Parquet files** in Google Drive

### Storage (FIXED)

```
itos/
├── minute_parquet/      # Clean market data (per symbol)
├── STR_results/         # Per-strategy outputs
├── analytics/           # Per-strategy analytics
├── final/               # Merged results
├── logs/                # Errors, skips
```

All processing:

* Google Colab only
* Resume-safe
* No full data loading into memory

---

## 3. FINAL GOAL (VERY IMPORTANT)

### End State

A live system that:

* Monitors market regime
* Selects quality stocks daily
* Activates **only valid strategies**
* Generates **intraday alerts** (not auto-trades)

Example alert:

```
BUY TRENT
Strategy: STR_127_VWAP_PULLBACK
Entry: 3125
Stop: 3108
Reason: Trend Day + RS + Clean Pullback
```

Capital preservation > frequency
Survivability > optimization

---

## 4. OVERALL SYSTEM PHASES (BIG PICTURE)

> ⚠️ These are **system phases**, NOT strategy numbers

### PHASE 0 — Data Engine (DONE)

Clean, align, standardize minute data.

**Input**

* Raw CSV / Parquet files

**Output**

* Clean per-symbol Parquet files

---

### PHASE 1 — Strategy Engine (CURRENT PHASE)

Run **one strategy at a time** across all symbols and years.

Each strategy:

* Is independent
* Has fixed rules (no optimization)
* Produces raw trades

**Output**

* Per-strategy trade file

---

### PHASE 2 — Strategy Analytics

Evaluate if a strategy is worth keeping.

Metrics:

* Net PnL
* Drawdown
* Profit factor
* Yearly stability
* Regime behavior
* Time-of-day edge

**Decision**

* ❌ Kill
* 🔧 Modify
* ✅ Approve

---

### PHASE 3 — Strategy Library

Only approved strategies enter the library.

This is where:

* 500+ strategies accumulate
* Metadata is attached (regime, behavior, risk)

---

### PHASE 4 — Stock Selection Engine

Daily selection of **tradable stocks**.

Filters:

* Long-term cleanliness
* Volatility sufficiency
* Relative strength
* Opening behavior

Output:

```
Tradable Stocks Today = 8–15
```

---

### PHASE 5 — Market Regime Engine

Classifies the day:

* Trend / Range
* High / Low volatility
* Risk ON / OFF

Strategies need permission from here to trade.

---

### PHASE 6 — Live Signal Engine

Real-time engine:

* Consumes minute data
* Applies filters + strategies
* Emits alerts only

---

## 5. STRATEGY DEVELOPMENT FLOW (REPEATABLE)

This is the **core loop**, repeated 500+ times.

---

### STEP A — Strategy Design

Each strategy has:

* Clear **idea**
* Strict **rules**
* Fixed **parameters**

Example:

```
STR_001_ORB
- Entry: 09:30 open breakout
- Exit: 15:25 close
- Side: Long only
```

---

### STEP B — Strategy Runner Notebook

**Notebook pattern**

```
STR_XXX_strategy_engine.ipynb
```

**Input**

* minute_parquet/
* strategy rules

**Processing**

* Symbol by symbol
* Day by day
* Resume-safe

**Output**

```
STR_results/STR_XXX_all_trades.parquet
```

---

### STEP C — Strategy Analytics Notebook

**Notebook pattern**

```
P-03_analytics_STR_XXX.ipynb
```

**Input**

* STR_results/STR_XXX_all_trades.parquet

**Outputs**

* Metrics
* Yearly PnL
* Drawdown
* Stability assessment

**Decision**

* Kill / Modify / Keep

---

## 6. IMPORTANT DESIGN RULES (NON-NEGOTIABLE)

* No per-stock optimization
* No curve fitting
* No combining strategies blindly
* No ML until rule-based edge exists
* Every strategy must survive analytics alone

Bad strategies are **permanently killed**.

---

## 7. FILE NAMING CONVENTION (FINAL)

### Strategies

```
STR_001_ORB
STR_002_ORB_FILTERED
STR_003_VWAP_PULLBACK
...
STR_500_xxx
```

### Notebooks

```
STR_001_strategy_engine.ipynb
P-03_analytics_STR_001.ipynb
```

System phases are **never** named as STR_xxx.

---
## 8. FINAL TRUTH (READ THIS TWICE)

You are not trying to:

* Predict markets
* Win every day
* Build a magic strategy

You are building:

> A **decision system** that knows
> *when NOT to trade* better than most traders know *when to trade*.

That’s how professional desks survive.

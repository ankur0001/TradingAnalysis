"""
Configuration settings for ITOS system.
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "itos" / "minute_parquet"
RESULTS_DIR = BASE_DIR / "itos" / "STR_results"
ANALYTICS_DIR = BASE_DIR / "itos" / "analytics"
FINAL_DIR = BASE_DIR / "itos" / "final"
LOGS_DIR = BASE_DIR / "itos" / "logs"

# Trading hours (Indian market)
MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"
TRADING_MINUTES = 375  # 6.25 hours * 60 minutes

# Data processing
BATCH_SIZE = 10  # symbols per batch
MAX_MEMORY_GB = 4  # maximum memory usage

# Strategy parameters
MIN_TRADES = 50  # minimum trades for analytics
MAX_DRAWDOWN = 0.20  # 20% maximum acceptable drawdown
MIN_PROFIT_FACTOR = 1.2  # minimum profit factor

# File naming
STRATEGY_PREFIX = "STR_"
ANALYTICS_PREFIX = "P-03_analytics_"

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
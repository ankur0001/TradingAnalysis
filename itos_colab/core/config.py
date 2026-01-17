"""
Configuration settings for ITOS system - Google Colab Edition.
"""

import os
from pathlib import Path

# Google Colab specific paths
try:
    from google.colab import drive
    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False

if DRIVE_AVAILABLE:
    # Google Drive paths
    DRIVE_BASE = "/content/drive/MyDrive/itos"
    DATA_DIR = f"{DRIVE_BASE}/minute_parquet"
    RESULTS_DIR = f"{DRIVE_BASE}/STR_results"
    ANALYTICS_DIR = f"{DRIVE_BASE}/analytics"
    FINAL_DIR = f"{DRIVE_BASE}/final"
    LOGS_DIR = f"{DRIVE_BASE}/logs"
else:
    # Local paths for testing
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "itos_colab" / "minute_parquet"
    RESULTS_DIR = BASE_DIR / "itos_colab" / "STR_results"
    ANALYTICS_DIR = BASE_DIR / "itos_colab" / "analytics"
    FINAL_DIR = BASE_DIR / "itos_colab" / "final"
    LOGS_DIR = BASE_DIR / "itos_colab" / "logs"

# Trading hours (Indian market)
MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"
TRADING_MINUTES = 375  # 6.25 hours * 60 minutes

# Data processing (Colab optimized)
BATCH_SIZE = 5  # Reduced for Colab memory constraints
MAX_MEMORY_GB = 2  # Conservative for Colab
CHUNK_SIZE = 10000  # Process data in chunks

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

# Google Colab specific settings
COLAB_SETTINGS = {
    'auto_save_interval': 10,  # Save every 10 symbols
    'memory_cleanup': True,    # Enable garbage collection
    'progress_display': True,   # Show progress bars
    'resume_capability': True,  # Enable resume functionality
    'chunk_processing': True,   # Process data in chunks
}

# Data source settings (for your Kaggle dataset)
DATA_SOURCE = {
    'type': 'kaggle',
    'dataset': 'debashis74017/algo-trading-data-nifty-100-data-with-indicators',
    'source_dir': '/root/.cache/kagglehub/datasets/debashis74017/algo-trading-data-nifty-100-data-with-indicators/versions/15',
    'file_pattern': '_minute.csv',
    'timestamp_columns': ['timestamp', 'datetime', 'date', 'Date', 'time', 'Time']
}
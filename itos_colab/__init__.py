"""
ITOS - Intraday Trading Operating System
Google Colab Edition
========================================

A modular, data-driven intraday trading operating system optimized for Google Colab
with Google Drive persistence and resume-safe execution.
"""

__version__ = "1.0.0"
__author__ = "ITOS Team"

# Google Colab specific imports
try:
    from google.colab import drive
    import os
    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False

# Mount Google Drive if available
if DRIVE_AVAILABLE:
    drive.mount('/content/drive')
    
    # Set up paths for Google Drive
    DRIVE_BASE = "/content/drive/MyDrive/itos"
    DATA_DIR = f"{DRIVE_BASE}/minute_parquet"
    RESULTS_DIR = f"{DRIVE_BASE}/STR_results"
    ANALYTICS_DIR = f"{DRIVE_BASE}/analytics"
    FINAL_DIR = f"{DRIVE_BASE}/final"
    LOGS_DIR = f"{DRIVE_BASE}/logs"
    
    # Create directories if they don't exist
    for directory in [DATA_DIR, RESULTS_DIR, ANALYTICS_DIR, FINAL_DIR, LOGS_DIR]:
        os.makedirs(directory, exist_ok=True)
    
    print("✅ Google Drive mounted and directories created")
else:
    print("⚠️ Google Drive not available - using local paths")
    # Fallback to local paths for testing
    from pathlib import Path
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "itos" / "minute_parquet"
    RESULTS_DIR = BASE_DIR / "itos" / "STR_results"
    ANALYTICS_DIR = BASE_DIR / "itos" / "analytics"
    FINAL_DIR = BASE_DIR / "itos" / "final"
    LOGS_DIR = BASE_DIR / "itos" / "logs"

# Import core components
from .core.data_engine import DataEngine
from .core.strategy_engine import StrategyEngine
from .core.analytics_engine import AnalyticsEngine

__all__ = ["DataEngine", "StrategyEngine", "AnalyticsEngine"]
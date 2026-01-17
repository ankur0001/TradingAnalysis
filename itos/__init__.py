"""
ITOS - Intraday Trading Operating System
========================================

A modular, data-driven intraday trading operating system that
designs, evaluates, filters, and deploys 500+ intraday strategies
across hundreds of stocks using rule-based intelligence.

Core Principles:
- Capital preservation > frequency
- Survivability > optimization
- Rule-based intelligence > ML black box
- Quality over quantity
"""

__version__ = "1.0.0"
__author__ = "ITOS Team"

from .core.data_engine import DataEngine
from .core.strategy_engine import StrategyEngine
from .core.analytics_engine import AnalyticsEngine

__all__ = ["DataEngine", "StrategyEngine", "AnalyticsEngine"]
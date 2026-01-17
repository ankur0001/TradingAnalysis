"""
Core data types and structures for ITOS system.
"""

from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional, Dict, Any
import pandas as pd


@dataclass
class Trade:
    """Represents a single trade execution."""
    symbol: str
    strategy: str
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    quantity: int
    side: str  # 'LONG' or 'SHORT'
    pnl: Optional[float] = None
    exit_reason: Optional[str] = None
    
    def __post_init__(self):
        if self.pnl is None and self.exit_price is not None:
            if self.side == 'LONG':
                self.pnl = (self.exit_price - self.entry_price) * self.quantity
            else:
                self.pnl = (self.entry_price - self.exit_price) * self.quantity


@dataclass
class StrategyResult:
    """Results from running a strategy across all symbols."""
    strategy_name: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    max_drawdown: float
    profit_factor: float
    sharpe_ratio: float
    avg_trade_duration: float  # in minutes
    metadata: Dict[str, Any]


@dataclass
class MarketData:
    """Market data container for a single symbol."""
    symbol: str
    data: pd.DataFrame  # OHLCV with datetime index
    
    def validate(self) -> bool:
        """Validate data format and completeness."""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in self.data.columns for col in required_columns):
            return False
        
        # Check for missing data
        if self.data.isnull().any().any():
            return False
            
        # Check chronological order
        if not self.data.index.is_monotonic_increasing:
            return False
            
        return True


@dataclass
class StrategyConfig:
    """Configuration for a trading strategy."""
    name: str
    side: str  # 'LONG', 'SHORT', 'BOTH'
    entry_time_start: time
    entry_time_end: time
    exit_time: time
    parameters: Dict[str, Any]
    description: str
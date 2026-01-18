from dataclasses import dataclass
from typing import Optional, Dict, Any
import pandas as pd

# Basic data types used by ITOS Colab Stock Run

@dataclass
class MarketData:
    symbol: str
    data: pd.DataFrame  # OHLCV with datetime index
    def validate(self) -> bool:
        required = ["open", "high", "low", "close", "volume"]
        if self.data is None:
            return False
        if not all(col in self.data.columns for col in required):
            return False
        if self.data.isnull().any().any():
            return False
        if not self.data.index.is_monotonic_increasing:
            return False
        return True

@dataclass
class Trade:
    symbol: str
    strategy: str
    entry_time: Any
    exit_time: Optional[Any]
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
class StrategyConfig:
    name: str
    side: str  # 'LONG', 'SHORT', 'BOTH'
    entry_time_start: Any
    entry_time_end: Any
    exit_time: Any
    parameters: Dict[str, Any]
    description: str

@dataclass
class StrategyResult:
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

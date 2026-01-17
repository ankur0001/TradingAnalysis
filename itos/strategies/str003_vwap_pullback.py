"""
STR_003_VWAP_PULLBACK - VWAP Pullback Strategy
===============================================

Strategy Rules:
- Entry: Pullback to VWAP during trend day
- Exit: 15:25 close or when target reached
- Side: Long only
- Additional filters: Trend strength, Volume confirmation
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import List

from ..core.strategy_engine import BaseStrategy
from ..core.types import Trade, StrategyConfig, MarketData


class STR003_VWAP_PULLBACK(BaseStrategy):
    """
    VWAP Pullback Strategy
    
    Entry Rules:
    - Identify trend day (price above VWAP + 0.5%)
    - Wait for pullback to VWAP
    - Enter on VWAP bounce with volume confirmation
    - Entry window: 10:00-14:30
    
    Exit Rules:
    - Stop loss: 2% below entry price
    - Target: 3% above entry price
    - Time exit: 15:25
    """
    
    def __init__(self):
        config = StrategyConfig(
            name="STR_003_VWAP_PULLBACK",
            side="LONG",
            entry_time_start=time(10, 0),
            entry_time_end=time(14, 30),
            exit_time=time(15, 25),
            parameters={
                'stop_loss_pct': 0.02,
                'target_pct': 0.03,
                'trend_threshold': 0.005,  # 0.5% above VWAP
                'pullback_threshold': 0.002,  # 0.2% below VWAP
                'volume_multiplier': 1.3,
                'min_trend_minutes': 30  # Minimum trend duration
            },
            description="VWAP Pullback Strategy - Long only"
        )
        super().__init__(config)
    
    def generate_signals(self, market_data: MarketData) -> List[Trade]:
        """Generate trades based on VWAP pullback."""
        trades = []
        data = market_data.data.copy()
        
        # Group by trading days
        data['date'] = data.index.date
        data['time'] = data.index.time
        
        for date, day_data in data.groupby('date'):
            try:
                trade = self._process_day(market_data.symbol, day_data)
                if trade:
                    trades.append(trade)
            except Exception as e:
                logger.error(f"Error processing {market_data.symbol} for {date}: {e}")
                continue
        
        return trades
    
    def _process_day(self, symbol: str, day_data: pd.DataFrame) -> Trade:
        """Process a single trading day."""
        # Sort by time
        day_data = day_data.sort_index()
        
        # Calculate VWAP
        day_data = self._calculate_vwap(day_data)
        
        # Identify trend day
        if not self._is_trend_day(day_data):
            return None
        
        # Find pullback and entry
        entry_signal = self._find_entry_signal(day_data)
        if entry_signal is None:
            return None
        
        entry_time, entry_price = entry_signal
        
        # Calculate position size
        quantity = self._calculate_position_size(entry_price)
        
        # Exit parameters
        stop_loss = entry_price * (1 - self.config.parameters['stop_loss_pct'])
        target = entry_price * (1 + self.config.parameters['target_pct'])
        
        # Find exit
        exit_data = day_data[day_data['time'] > entry_time.time()]
        exit_time = None
        exit_price = None
        exit_reason = None
        
        for timestamp, row in exit_data.iterrows():
            # Check stop loss
            if row['low'] <= stop_loss:
                exit_time = timestamp
                exit_price = stop_loss
                exit_reason = "STOP_LOSS"
                break
            
            # Check target
            if row['high'] >= target:
                exit_time = timestamp
                exit_price = target
                exit_reason = "TARGET"
                break
            
            # Check time exit
            if timestamp.time() >= time(15, 25):
                exit_time = timestamp
                exit_price = row['close']
                exit_reason = "TIME_EXIT"
                break
        
        if exit_time is None:
            # Force exit at market close
            last_row = day_data.iloc[-1]
            exit_time = last_row.name
            exit_price = last_row['close']
            exit_reason = "FORCE_CLOSE"
        
        # Create trade
        trade = Trade(
            symbol=symbol,
            strategy=self.config.name,
            entry_time=entry_time,
            exit_time=exit_time,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            side="LONG",
            exit_reason=exit_reason
        )
        
        return trade
    
    def _calculate_vwap(self, day_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate VWAP for the day."""
        # Calculate cumulative values
        day_data['cumulative_volume'] = day_data['volume'].cumsum()
        day_data['cumulative_tpv'] = (day_data['typical_price'] * day_data['volume']).cumsum()
        day_data['vwap'] = day_data['cumulative_tpv'] / day_data['cumulative_volume']
        
        return day_data
    
    def _is_trend_day(self, day_data: pd.DataFrame) -> bool:
        """Check if it's a trend day."""
        trend_threshold = self.config.parameters['trend_threshold']
        min_trend_minutes = self.config.parameters['min_trend_minutes']
        
        # Check trend after 10:00
        trend_data = day_data[day_data['time'] >= time(10, 0)]
        
        if len(trend_data) < min_trend_minutes:
            return False
        
        # Calculate percentage above VWAP
        trend_data['vwap_diff'] = (trend_data['close'] - trend_data['vwap']) / trend_data['vwap']
        
        # Check if price stays above VWAP + threshold
        above_vwap = trend_data['vwap_diff'] > trend_threshold
        trend_duration = above_vwap.sum()
        
        return trend_duration >= min_trend_minutes
    
    def _find_entry_signal(self, day_data: pd.DataFrame) -> tuple:
        """Find entry signal based on VWAP pullback."""
        pullback_threshold = self.config.parameters['pullback_threshold']
        volume_multiplier = self.config.parameters['volume_multiplier']
        
        # Entry window
        entry_data = day_data[
            (day_data['time'] >= time(10, 0)) & 
            (day_data['time'] <= time(14, 30))
        ]
        
        if len(entry_data) < 10:
            return None
        
        # Calculate average volume
        avg_volume = entry_data['volume'].mean()
        
        # Find pullback to VWAP
        for i in range(1, len(entry_data)):
            current = entry_data.iloc[i]
            previous = entry_data.iloc[i-1]
            
            # Check for pullback
            vwap_diff = (current['close'] - current['vwap']) / current['vwap']
            
            if vwap_diff < -pullback_threshold:
                # Check for bounce (next candle)
                if i + 1 < len(entry_data):
                    next_candle = entry_data.iloc[i + 1]
                    
                    # Bounce condition
                    if next_candle['low'] > current['vwap']:
                        # Volume confirmation
                        if current['volume'] > avg_volume * volume_multiplier:
                            entry_time = current.name
                            entry_price = current['close']
                            return entry_time, entry_price
        
        return None


# Import logger
import logging
logger = logging.getLogger(__name__)
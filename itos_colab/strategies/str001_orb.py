"""
STR_001_ORB - Opening Range Breakout Strategy (Google Colab Edition)
======================================================================

Strategy Rules:
- Entry: 09:30 open breakout (first 15 minutes range)
- Exit: 15:25 close (5 minutes before market close)
- Side: Long only
- Stop Loss: 2% below entry price
- Target: 3% above entry price
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import List
import logging

from ..core.strategy_engine import BaseStrategy
from ..core.types import Trade, StrategyConfig, MarketData

logger = logging.getLogger(__name__)


class STR001_ORB(BaseStrategy):
    """
    Opening Range Breakout Strategy
    
    Entry Rules:
    - Calculate opening range (09:15-09:30)
    - Enter long on breakout above opening range high
    - Entry must occur before 10:30
    
    Exit Rules:
    - Stop loss: 2% below entry price
    - Target: 3% above entry price
    - Time exit: 15:25
    """
    
    def __init__(self):
        config = StrategyConfig(
            name="STR_001_ORB",
            side="LONG",
            entry_time_start=time(9, 30),
            entry_time_end=time(10, 30),
            exit_time=time(15, 25),
            parameters={
                'opening_range_minutes': 15,
                'stop_loss_pct': 0.02,
                'target_pct': 0.03,
                'min_breakout_pct': 0.005  # 0.5% minimum breakout
            },
            description="Opening Range Breakout - Long only"
        )
        super().__init__(config)
    
    def generate_signals(self, market_data: MarketData) -> List[Trade]:
        """Generate trades based on opening range breakout."""
        try:
            trades = []
            data = market_data.data.copy()
            
            # Group by trading days
            data['date'] = data['timestamp'].dt.date
            data['time'] = data['timestamp'].dt.time
            
            for date, day_data in data.groupby('date'):
                try:
                    trade = self._process_day(market_data.symbol, day_data)
                    if trade:
                        trades.append(trade)
                except Exception as e:
                    logger.error(f"❌ Error processing {market_data.symbol} for {date}: {e}")
                    continue
            
            return trades
            
        except Exception as e:
            logger.error(f"❌ Error generating signals for {market_data.symbol}: {e}")
            return []
    
    def _process_day(self, symbol: str, day_data: pd.DataFrame) -> Trade:
        """Process a single trading day."""
        try:
            # Sort by time
            day_data = day_data.sort_values('timestamp')
            
            # Calculate opening range (first 15 minutes)
            opening_range_end = time(9, 30)
            opening_range_data = day_data[day_data['time'] <= opening_range_end]
            
            if len(opening_range_data) < 10:  # Need sufficient data
                return None
            
            or_high = opening_range_data['high'].max()
            or_low = opening_range_data['low'].min()
            or_close = opening_range_data.iloc[-1]['close']
            
            # Entry parameters
            breakout_level = or_high
            min_breakout = breakout_level * (1 + self.config.parameters['min_breakout_pct'])
            
            # Find entry
            entry_data = day_data[
                (day_data['time'] > time(9, 30)) & 
                (day_data['time'] <= time(10, 30))
            ]
            
            entry_trade = None
            entry_time = None
            entry_price = None
            
            for timestamp, row in entry_data.iterrows():
                if row['high'] > min_breakout:
                    entry_time = timestamp
                    entry_price = max(min_breakout, row['open'])
                    break
            
            if entry_time is None:
                return None  # No entry
            
            # Calculate position size
            quantity = self._calculate_position_size(entry_price)
            
            # Exit parameters
            stop_loss = entry_price * (1 - self.config.parameters['stop_loss_pct'])
            target = entry_price * (1 + self.config.parameters['target_pct'])
            
            # Find exit
            exit_data = day_data[day_data['time'] > entry_time.time()]
            exit_trade = None
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
                exit_time = last_row['timestamp']
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
            
        except Exception as e:
            logger.error(f"❌ Error processing day for {symbol}: {e}")
            return None
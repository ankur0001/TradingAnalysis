"""
Phase 1 - Strategy Engine
=========================

Run one strategy at a time across all symbols and years.
Each strategy is independent with fixed rules.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, time
from abc import ABC, abstractmethod
import logging
from dataclasses import dataclass

from .config import RESULTS_DIR, LOGS_DIR, TRADING_MINUTES
from .types import Trade, MarketData, StrategyConfig
from .data_engine import DataEngine

logger = logging.getLogger(__name__)


class Strategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    Each strategy must implement:
    - generate_signals: Create buy/sell signals
    - get_config: Return strategy configuration
    """
    
    @abstractmethod
    def generate_signals(self, data: MarketData) -> List[Trade]:
        """Generate trading signals for given market data."""
        pass
    
    @abstractmethod
    def get_config(self) -> StrategyConfig:
        """Return strategy configuration."""
        pass


class StrategyEngine:
    """
    Strategy execution engine.
    
    Features:
    - Run strategies symbol-by-symbol
    - Resume-safe execution
    - Save per-strategy results
    - Handle large datasets efficiently
    """
    
    def __init__(self, results_dir: Path = RESULTS_DIR):
        self.results_dir = results_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOGS_DIR / 'strategy_engine.log'),
                logging.StreamHandler()
            ]
        )
        
        self.data_engine = DataEngine()
    
    def run_strategy(self, strategy: Strategy, symbols: Optional[List[str]] = None) -> bool:
        """
        Run a strategy across all symbols.
        
        Args:
            strategy: Strategy instance to run
            symbols: List of symbols to process (None for all)
            
        Returns:
            True if successful, False otherwise
        """
        strategy_name = strategy.get_config().name
        logger.info(f"Starting strategy execution: {strategy_name}")
        
        try:
            # Get symbols to process
            if symbols is None:
                symbols = self.data_engine.get_processed_symbols()
            
            if not symbols:
                logger.error("No symbols found to process")
                return False
            
            # Check for existing results (resume capability)
            existing_trades = self._load_existing_trades(strategy_name)
            processed_symbols = set(trade.symbol for trade in existing_trades)
            
            # Filter symbols that need processing
            symbols_to_process = [s for s in symbols if s not in processed_symbols]
            
            if not symbols_to_process:
                logger.info(f"All symbols already processed for {strategy_name}")
                return True
            
            logger.info(f"Processing {len(symbols_to_process)} symbols for {strategy_name}")
            
            # Process symbols
            all_trades = existing_trades.copy()
            
            for i, symbol in enumerate(symbols_to_process):
                try:
                    logger.info(f"Processing {symbol} ({i+1}/{len(symbols_to_process)})")
                    
                    # Load market data
                    market_data = self.data_engine.load_symbol_data(symbol)
                    if market_data is None:
                        logger.warning(f"Skipping {symbol} - no data available")
                        continue
                    
                    # Generate trades
                    trades = strategy.generate_signals(market_data)
                    all_trades.extend(trades)
                    
                    # Save intermediate results (every 10 symbols)
                    if (i + 1) % 10 == 0:
                        self._save_trades(all_trades, strategy_name)
                        logger.info(f"Saved intermediate results after {i+1} symbols")
                
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    continue
            
            # Save final results
            self._save_trades(all_trades, strategy_name)
            
            logger.info(f"Completed {strategy_name}: {len(all_trades)} total trades")
            return True
            
        except Exception as e:
            logger.error(f"Error running strategy {strategy_name}: {e}")
            return False
    
    def _load_existing_trades(self, strategy_name: str) -> List[Trade]:
        """Load existing trades for resume capability."""
        file_path = self.results_dir / f"{strategy_name}_all_trades.parquet"
        
        if not file_path.exists():
            return []
        
        try:
            df = pd.read_parquet(file_path)
            trades = []
            
            for _, row in df.iterrows():
                trade = Trade(
                    symbol=row['symbol'],
                    strategy=row['strategy'],
                    entry_time=pd.to_datetime(row['entry_time']),
                    exit_time=pd.to_datetime(row['exit_time']) if pd.notna(row['exit_time']) else None,
                    entry_price=row['entry_price'],
                    exit_price=row['exit_price'] if pd.notna(row['exit_price']) else None,
                    quantity=row['quantity'],
                    side=row['side'],
                    pnl=row['pnl'] if pd.notna(row['pnl']) else None,
                    exit_reason=row['exit_reason'] if pd.notna(row['exit_reason']) else None
                )
                trades.append(trade)
            
            logger.info(f"Loaded {len(trades)} existing trades for {strategy_name}")
            return trades
            
        except Exception as e:
            logger.error(f"Error loading existing trades: {e}")
            return []
    
    def _save_trades(self, trades: List[Trade], strategy_name: str):
        """Save trades to Parquet file."""
        if not trades:
            return
        
        # Convert to DataFrame
        trade_data = []
        for trade in trades:
            trade_data.append({
                'symbol': trade.symbol,
                'strategy': trade.strategy,
                'entry_time': trade.entry_time,
                'exit_time': trade.exit_time,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'quantity': trade.quantity,
                'side': trade.side,
                'pnl': trade.pnl,
                'exit_reason': trade.exit_reason
            })
        
        df = pd.DataFrame(trade_data)
        file_path = self.results_dir / f"{strategy_name}_all_trades.parquet"
        df.to_parquet(file_path, index=False)
        
        logger.info(f"Saved {len(trades)} trades to {file_path}")
    
    def get_strategy_results(self, strategy_name: str) -> Optional[pd.DataFrame]:
        """Load results for a specific strategy."""
        file_path = self.results_dir / f"{strategy_name}_all_trades.parquet"
        
        if not file_path.exists():
            return None
        
        try:
            return pd.read_parquet(file_path)
        except Exception as e:
            logger.error(f"Error loading results for {strategy_name}: {e}")
            return None
    
    def list_strategies(self) -> List[str]:
        """List all available strategies with results."""
        if not self.results_dir.exists():
            return []
        
        strategies = []
        for file_path in self.results_dir.glob("*_all_trades.parquet"):
            strategy_name = file_path.stem.replace("_all_trades", "")
            strategies.append(strategy_name)
        
        return sorted(strategies)


class BaseStrategy(Strategy):
    """
    Base strategy class with common functionality.
    """
    
    def __init__(self, config: StrategyConfig):
        self.config = config
    
    def get_config(self) -> StrategyConfig:
        return self.config
    
    def _is_trading_time(self, timestamp: datetime) -> bool:
        """Check if timestamp is within allowed trading hours."""
        current_time = timestamp.time()
        return self.config.entry_time_start <= current_time <= self.config.entry_time_end
    
    def _should_exit(self, timestamp: datetime) -> bool:
        """Check if position should be exited based on time."""
        return timestamp.time() >= self.config.exit_time
    
    def _calculate_position_size(self, price: float, capital: float = 100000) -> int:
        """Calculate position size based on risk management."""
        # Simple position sizing - 1% of capital per trade
        risk_amount = capital * 0.01
        stop_loss_pct = 0.02  # 2% stop loss
        
        position_size = int(risk_amount / (price * stop_loss_pct))
        return max(1, position_size)
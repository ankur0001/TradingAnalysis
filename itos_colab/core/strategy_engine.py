"""
Phase 1 - Strategy Engine (Google Colab Edition)
================================================

Run one strategy at a time across all symbols and years.
Optimized for Google Colab with Google Drive persistence.
"""

import pandas as pd
import numpy as np
import os
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, time
from abc import ABC, abstractmethod
import logging
from dataclasses import dataclass
import warnings

from .config import RESULTS_DIR, LOGS_DIR, TRADING_MINUTES, COLAB_SETTINGS
from .types import Trade, MarketData, StrategyConfig
from .data_engine import ColabDataEngine

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


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


class ColabStrategyEngine:
    """
    Google Colab optimized strategy execution engine.
    
    Features:
    - Google Drive persistence
    - Memory-efficient batch processing
    - Resume-safe execution
    - Automatic garbage collection
    - Progress tracking
    """
    
    def __init__(self, results_dir: str = RESULTS_DIR):
        self.results_dir = results_dir
        
        # Ensure directories exist
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(LOGS_DIR, 'strategy_engine.log')),
                logging.StreamHandler()
            ]
        )
        
        self.data_engine = ColabDataEngine()
        
        # Progress tracking
        self.processed_symbols = set()
        self.failed_symbols = set()
        
        logger.info("🚀 ColabStrategyEngine initialized")
    
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
        logger.info(f"🚀 Starting strategy execution: {strategy_name}")
        
        try:
            # Get symbols to process
            if symbols is None:
                symbols = self.data_engine.get_processed_symbols()
            
            if not symbols:
                logger.error("❌ No symbols found to process")
                return False
            
            # Check for existing results (resume capability)
            existing_trades = self._load_existing_trades(strategy_name)
            processed_symbols = set(trade.symbol for trade in existing_trades)
            
            # Filter symbols that need processing
            symbols_to_process = [s for s in symbols if s not in processed_symbols]
            
            if not symbols_to_process:
                logger.info(f"✅ All symbols already processed for {strategy_name}")
                return True
            
            logger.info(f"📊 Processing {len(symbols_to_process)} symbols for {strategy_name}")
            
            # Process symbols in batches
            all_trades = existing_trades.copy()
            batch_size = COLAB_SETTINGS.get('batch_size', 5)
            auto_save_interval = COLAB_SETTINGS.get('auto_save_interval', 10)
            
            for i in range(0, len(symbols_to_process), batch_size):
                batch_symbols = symbols_to_process[i:i + batch_size]
                
                logger.info(f"🔄 Processing batch {i//batch_size + 1}/{(len(symbols_to_process)-1)//batch_size + 1}")
                
                for j, symbol in enumerate(batch_symbols):
                    try:
                        logger.info(f"📈 Processing {symbol} ({i+j+1}/{len(symbols_to_process)})")
                        
                        # Load market data
                        market_data = self.data_engine.load_symbol_data(symbol)
                        if market_data is None:
                            logger.warning(f"⚠️ Skipping {symbol} - no data available")
                            self.failed_symbols.add(symbol)
                            continue
                        
                        # Generate trades
                        trades = strategy.generate_signals(market_data)
                        all_trades.extend(trades)
                        self.processed_symbols.add(symbol)
                        
                        # Memory cleanup
                        if COLAB_SETTINGS['memory_cleanup']:
                            del market_data
                            gc.collect()
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing {symbol}: {e}")
                        self.failed_symbols.add(symbol)
                        continue
                
                # Auto-save after each batch
                if (i // batch_size + 1) % auto_save_interval == 0:
                    self._save_trades(all_trades, strategy_name)
                    logger.info(f"💾 Auto-saved after {i + len(batch_symbols)} symbols")
            
            # Save final results
            self._save_trades(all_trades, strategy_name)
            
            logger.info(f"🎉 Completed {strategy_name}: {len(all_trades)} total trades")
            logger.info(f"✅ Successful: {len(self.processed_symbols)}, Failed: {len(self.failed_symbols)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error running strategy {strategy_name}: {e}")
            return False
    
    def _load_existing_trades(self, strategy_name: str) -> List[Trade]:
        """Load existing trades for resume capability."""
        file_path = os.path.join(self.results_dir, f"{strategy_name}_all_trades.parquet")
        
        if not os.path.exists(file_path):
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
            
            logger.info(f"📊 Loaded {len(trades)} existing trades for {strategy_name}")
            return trades
            
        except Exception as e:
            logger.error(f"❌ Error loading existing trades: {e}")
            return []
    
    def _save_trades(self, trades: List[Trade], strategy_name: str):
        """Save trades to Parquet file on Google Drive."""
        if not trades:
            return
        
        try:
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
            file_path = os.path.join(self.results_dir, f"{strategy_name}_all_trades.parquet")
            
            # Save to Google Drive
            df.to_parquet(file_path, index=False)
            
            logger.info(f"💾 Saved {len(trades)} trades to {file_path}")
            
            # Cleanup
            del df
            del trade_data
            if COLAB_SETTINGS['memory_cleanup']:
                gc.collect()
            
        except Exception as e:
            logger.error(f"❌ Error saving trades: {e}")
    
    def get_strategy_results(self, strategy_name: str) -> Optional[pd.DataFrame]:
        """Load results for a specific strategy."""
        file_path = os.path.join(self.results_dir, f"{strategy_name}_all_trades.parquet")
        
        if not os.path.exists(file_path):
            return None
        
        try:
            return pd.read_parquet(file_path)
        except Exception as e:
            logger.error(f"❌ Error loading results for {strategy_name}: {e}")
            return None
    
    def list_strategies(self) -> List[str]:
        """List all available strategies with results."""
        try:
            if not os.path.exists(self.results_dir):
                return []
            
            strategies = []
            for file_path in os.listdir(self.results_dir):
                if file_path.endswith("_all_trades.parquet"):
                    strategy_name = file_path.replace("_all_trades.parquet", "")
                    strategies.append(strategy_name)
            
            return sorted(strategies)
            
        except Exception as e:
            logger.error(f"❌ Error listing strategies: {e}")
            return []
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of strategy execution."""
        return {
            'processed_symbols': len(self.processed_symbols),
            'failed_symbols': len(self.failed_symbols),
            'available_strategies': len(self.list_strategies()),
            'results_dir': self.results_dir
        }


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
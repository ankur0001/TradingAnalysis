"""
Phase 0 - Data Engine
====================

Clean, align, and standardize minute data for all symbols.
This is the foundation layer that ensures data quality.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any
import pyarrow.parquet as pq
from datetime import datetime, time
import logging

from .config import DATA_DIR, LOGS_DIR, MARKET_OPEN, MARKET_CLOSE
from .types import MarketData

logger = logging.getLogger(__name__)


class DataEngine:
    """
    Data processing engine for cleaning and standardizing minute data.
    
    Features:
    - Load raw CSV/Parquet files
    - Clean and align data
    - Standardize format
    - Save as per-symbol Parquet files
    - Resume-safe processing
    """
    
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOGS_DIR / 'data_engine.log'),
                logging.StreamHandler()
            ]
        )
    
    def load_raw_data(self, file_path: Path) -> pd.DataFrame:
        """
        Load raw data from CSV or Parquet file.
        
        Args:
            file_path: Path to raw data file
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            elif file_path.suffix.lower() == '.parquet':
                df = pd.read_parquet(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
            
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            raise
    
    def clean_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Clean and standardize data for a symbol.
        
        Args:
            df: Raw DataFrame
            symbol: Symbol name
            
        Returns:
            Cleaned DataFrame
        """
        # Standardize column names
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Create datetime index
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
        elif 'date' in df.columns and 'time' in df.columns:
            df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
            df.set_index('datetime', inplace=True)
        else:
            # Assume index is already datetime
            df.index = pd.to_datetime(df.index)
        
        # Sort by datetime
        df = df.sort_index()
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        # Filter trading hours
        trading_hours = (df.index.time >= time(9, 15)) & (df.index.time <= time(15, 30))
        df = df[trading_hours]
        
        # Remove non-trading days
        df = self._remove_non_trading_days(df)
        
        # Forward fill missing minutes
        df = self._forward_fill_missing_data(df)
        
        # Data validation
        self._validate_ohlc_relationship(df)
        
        # Add basic features
        df = self._add_basic_features(df)
        
        logger.info(f"Cleaned data for {symbol}: {len(df)} rows")
        return df
    
    def _remove_non_trading_days(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove weekends and holidays."""
        # Remove weekends
        df = df[df.index.dayofweek < 5]
        
        # TODO: Add holiday calendar for Indian market
        # For now, just keep weekdays
        return df
    
    def _forward_fill_missing_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Forward fill missing data points."""
        # Create complete datetime range for trading hours
        start_date = df.index.date.min()
        end_date = df.index.date.max()
        
        # Generate complete trading minutes
        trading_minutes = pd.date_range(
            start=f"{start_date} {MARKET_OPEN}",
            end=f"{end_date} {MARKET_CLOSE}",
            freq='1min'
        )
        
        # Filter to trading hours only
        trading_minutes = trading_minutes[
            (trading_minutes.time >= time(9, 15)) & 
            (trading_minutes.time <= time(15, 30))
        ]
        
        # Reindex and forward fill
        df = df.reindex(trading_minutes)
        df = df.fillna(method='ffill')
        
        # Remove leading NaN values
        df = df.dropna()
        
        return df
    
    def _validate_ohlc_relationship(self, df: pd.DataFrame):
        """Validate OHLC relationships."""
        # High should be >= Open, Low, Close
        invalid_high = df['high'] < df[['open', 'low', 'close']].max(axis=1)
        if invalid_high.any():
            logger.warning(f"Found {invalid_high.sum()} invalid High values")
            df.loc[invalid_high, 'high'] = df.loc[invalid_high, ['open', 'low', 'close']].max(axis=1)
        
        # Low should be <= Open, High, Close
        invalid_low = df['low'] > df[['open', 'high', 'close']].min(axis=1)
        if invalid_low.any():
            logger.warning(f"Found {invalid_low.sum()} invalid Low values")
            df.loc[invalid_low, 'low'] = df.loc[invalid_low, ['open', 'high', 'close']].min(axis=1)
    
    def _add_basic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic technical features."""
        # Returns
        df['returns'] = df['close'].pct_change()
        
        # Typical price
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        
        # Volume weighted average price (VWAP)
        df['vwap'] = (df['typical_price'] * df['volume']).cumsum() / df['volume'].cumsum()
        
        # Price ranges
        df['range'] = df['high'] - df['low']
        df['body'] = abs(df['close'] - df['open'])
        
        return df
    
    def save_clean_data(self, df: pd.DataFrame, symbol: str):
        """
        Save cleaned data as Parquet file.
        
        Args:
            df: Cleaned DataFrame
            symbol: Symbol name
        """
        file_path = self.data_dir / f"{symbol}.parquet"
        df.to_parquet(file_path, index=True)
        logger.info(f"Saved cleaned data for {symbol} to {file_path}")
    
    def process_symbol(self, raw_file_path: Path, symbol: str) -> bool:
        """
        Process a single symbol from raw to clean data.
        
        Args:
            raw_file_path: Path to raw data file
            symbol: Symbol name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load raw data
            df = self.load_raw_data(raw_file_path)
            
            # Clean data
            df_clean = self.clean_data(df, symbol)
            
            # Save clean data
            self.save_clean_data(df_clean, symbol)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
            return False
    
    def get_processed_symbols(self) -> List[str]:
        """Get list of already processed symbols."""
        if not self.data_dir.exists():
            return []
        
        symbols = []
        for file_path in self.data_dir.glob("*.parquet"):
            symbols.append(file_path.stem)
        
        return sorted(symbols)
    
    def load_symbol_data(self, symbol: str) -> Optional[MarketData]:
        """
        Load processed data for a symbol.
        
        Args:
            symbol: Symbol name
            
        Returns:
            MarketData object or None if not found
        """
        file_path = self.data_dir / f"{symbol}.parquet"
        
        if not file_path.exists():
            logger.warning(f"Data for {symbol} not found")
            return None
        
        try:
            df = pd.read_parquet(file_path)
            market_data = MarketData(symbol=symbol, data=df)
            
            if not market_data.validate():
                logger.error(f"Invalid data for {symbol}")
                return None
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error loading {symbol}: {e}")
            return None
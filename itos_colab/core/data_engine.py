"""
Phase 0 - Data Engine (Google Colab Edition)
============================================

Clean, align, and standardize minute data for all symbols.
Optimized for Google Colab with Google Drive persistence.
"""

import pandas as pd
import numpy as np
import os
import gc
from pathlib import Path
from typing import List, Optional, Dict, Any
import pyarrow.parquet as pq
from datetime import datetime, time
import logging
import warnings

from .config import DATA_DIR, LOGS_DIR, MARKET_OPEN, MARKET_CLOSE, COLAB_SETTINGS, DATA_SOURCE
from .types import MarketData

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


class ColabDataEngine:
    """
    Google Colab optimized data processing engine.
    
    Features:
    - Google Drive persistence
    - Memory-efficient chunk processing
    - Resume-safe execution
    - Automatic garbage collection
    - Progress tracking
    """
    
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(LOGS_DIR, 'data_engine.log')),
                logging.StreamHandler()
            ]
        )
        
        # Progress tracking
        self.processed_symbols = set()
        self.failed_symbols = set()
        
        logger.info("🚀 ColabDataEngine initialized")
    
    def load_existing_symbols(self) -> set:
        """Load list of already processed symbols for resume capability."""
        try:
            processed_files = [f for f in os.listdir(self.data_dir) if f.endswith('.parquet')]
            processed_symbols = {f.replace('.parquet', '') for f in processed_files}
            logger.info(f"📊 Found {len(processed_symbols)} already processed symbols")
            return processed_symbols
        except Exception as e:
            logger.error(f"Error loading existing symbols: {e}")
            return set()
    
    def convert_kaggle_data(self, source_dir: str = None) -> bool:
        """
        Convert Kaggle CSV data to Parquet format on Google Drive.
        
        Args:
            source_dir: Source directory containing CSV files
            
        Returns:
            True if successful, False otherwise
        """
        if source_dir is None:
            source_dir = DATA_SOURCE['source_dir']
        
        if not os.path.exists(source_dir):
            logger.error(f"❌ Source directory not found: {source_dir}")
            return False
        
        # Get list of CSV files
        csv_files = sorted([f for f in os.listdir(source_dir) 
                           if f.endswith(DATA_SOURCE['file_pattern'])])
        
        logger.info(f"📁 Found {len(csv_files)} CSV files to convert")
        
        # Load existing symbols for resume capability
        existing_symbols = self.load_existing_symbols()
        
        for i, csv_file in enumerate(csv_files, 1):
            symbol = csv_file.replace(DATA_SOURCE['file_pattern'], '')
            parquet_path = os.path.join(self.data_dir, f"{symbol}.parquet")
            
            # Skip if already processed
            if symbol in existing_symbols:
                logger.info(f"[{i}/{len(csv_files)}] ⏭ {symbol} already converted")
                continue
            
            try:
                logger.info(f"[{i}/{len(csv_files)}] ▶ Converting {symbol}")
                
                # Convert CSV to Parquet
                success = self._convert_csv_to_parquet(
                    os.path.join(source_dir, csv_file),
                    parquet_path,
                    symbol
                )
                
                if success:
                    self.processed_symbols.add(symbol)
                    logger.info(f"[{i}/{len(csv_files)}] ✅ {symbol} converted successfully")
                else:
                    self.failed_symbols.add(symbol)
                    logger.error(f"[{i}/{len(csv_files)}] ❌ {symbol} conversion failed")
                
                # Memory cleanup
                if COLAB_SETTINGS['memory_cleanup']:
                    gc.collect()
                
                # Progress display
                if COLAB_SETTINGS['progress_display'] and i % 10 == 0:
                    logger.info(f"📊 Progress: {i}/{len(csv_files)} files processed")
                
            except Exception as e:
                logger.error(f"❌ Error converting {symbol}: {e}")
                self.failed_symbols.add(symbol)
                continue
        
        logger.info(f"🎉 Conversion completed: {len(self.processed_symbols)} successful, {len(self.failed_symbols)} failed")
        return True
    
    def _convert_csv_to_parquet(self, csv_path: str, parquet_path: str, symbol: str) -> bool:
        """Convert a single CSV file to Parquet format."""
        try:
            # Read CSV in chunks if large
            chunks = []
            chunk_size = COLAB_SETTINGS.get('chunk_size', 10000)
            
            for chunk in pd.read_csv(csv_path, chunksize=chunk_size, low_memory=False):
                # Process chunk
                chunk = self._process_chunk(chunk, symbol)
                if chunk is not None and not chunk.empty:
                    chunks.append(chunk)
            
            if not chunks:
                logger.warning(f"⚠️ No valid data found in {symbol}")
                return False
            
            # Combine chunks
            df = pd.concat(chunks, ignore_index=True)
            
            # Save to Parquet
            df.to_parquet(
                parquet_path,
                compression='snappy',
                index=False
            )
            
            # Cleanup
            del df
            del chunks
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error converting {symbol}: {e}")
            return False
    
    def _process_chunk(self, chunk: pd.DataFrame, symbol: str) -> Optional[pd.DataFrame]:
        """Process a chunk of data."""
        try:
            # Detect timestamp column
            timestamp_col = self._detect_timestamp_column(chunk)
            if timestamp_col is None:
                logger.warning(f"⚠️ No timestamp column found for {symbol}")
                return None
            
            # Rename timestamp column
            chunk = chunk.rename(columns={timestamp_col: 'timestamp'})
            
            # Convert timestamp
            chunk['timestamp'] = pd.to_datetime(chunk['timestamp'], errors='coerce')
            
            # Remove invalid timestamps
            chunk = chunk.dropna(subset=['timestamp'])
            
            if chunk.empty:
                return None
            
            # Sort by timestamp
            chunk = chunk.sort_values('timestamp')
            
            # Filter trading hours
            chunk = self._filter_trading_hours(chunk)
            
            # Standardize column names
            chunk = self._standardize_columns(chunk)
            
            # Add basic features
            chunk = self._add_basic_features(chunk)
            
            return chunk
            
        except Exception as e:
            logger.error(f"❌ Error processing chunk for {symbol}: {e}")
            return None
    
    def _detect_timestamp_column(self, df: pd.DataFrame) -> Optional[str]:
        """Detect timestamp column in DataFrame."""
        for col in DATA_SOURCE['timestamp_columns']:
            if col in df.columns:
                return col
        return None
    
    def _filter_trading_hours(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter data to trading hours only."""
        # Add time component
        df['time'] = df['timestamp'].dt.time
        
        # Filter to trading hours
        trading_hours = (
            (df['time'] >= time(9, 15)) & 
            (df['time'] <= time(15, 30))
        )
        
        return df[trading_hours].drop('time', axis=1)
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names."""
        # Convert to lowercase
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Map common column names
        column_mapping = {
            'open': 'open',
            'high': 'high', 
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
            'v': 'volume'
        }
        
        # Rename columns
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
        
        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            logger.warning(f"⚠️ Missing columns: {missing_cols}")
            return None
        
        return df
    
    def _add_basic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic technical features."""
        # Returns
        df['returns'] = df['close'].pct_change()
        
        # Typical price
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        
        # Price ranges
        df['range'] = df['high'] - df['low']
        df['body'] = abs(df['close'] - df['open'])
        
        return df
    
    def get_processed_symbols(self) -> List[str]:
        """Get list of processed symbols."""
        try:
            files = [f for f in os.listdir(self.data_dir) if f.endswith('.parquet')]
            symbols = [f.replace('.parquet', '') for f in files]
            return sorted(symbols)
        except Exception as e:
            logger.error(f"Error getting processed symbols: {e}")
            return []
    
    def load_symbol_data(self, symbol: str) -> Optional[MarketData]:
        """
        Load processed data for a symbol.
        
        Args:
            symbol: Symbol name
            
        Returns:
            MarketData object or None if not found
        """
        file_path = os.path.join(self.data_dir, f"{symbol}.parquet")
        
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ Data for {symbol} not found")
            return None
        
        try:
            # Load data in chunks if large
            df = pd.read_parquet(file_path)
            
            # Validate data
            if df.empty:
                logger.error(f"❌ Empty data for {symbol}")
                return None
            
            # Create MarketData object
            market_data = MarketData(symbol=symbol, data=df)
            
            if not market_data.validate():
                logger.error(f"❌ Invalid data for {symbol}")
                return None
            
            return market_data
            
        except Exception as e:
            logger.error(f"❌ Error loading {symbol}: {e}")
            return None
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of processed data."""
        try:
            symbols = self.get_processed_symbols()
            
            if not symbols:
                return {'symbols': 0, 'total_records': 0, 'date_range': None}
            
            total_records = 0
            min_date = None
            max_date = None
            
            # Sample first few symbols to get date range
            sample_symbols = symbols[:min(10, len(symbols))]
            
            for symbol in sample_symbols:
                file_path = os.path.join(self.data_dir, f"{symbol}.parquet")
                if os.path.exists(file_path):
                    df = pd.read_parquet(file_path)
                    total_records += len(df)
                    
                    if 'timestamp' in df.columns:
                        symbol_min = df['timestamp'].min()
                        symbol_max = df['timestamp'].max()
                        
                        if min_date is None or symbol_min < min_date:
                            min_date = symbol_min
                        if max_date is None or symbol_max > max_date:
                            max_date = symbol_max
            
            return {
                'symbols': len(symbols),
                'total_records': total_records,
                'date_range': (min_date, max_date) if min_date else None,
                'processed': len(self.processed_symbols),
                'failed': len(self.failed_symbols)
            }
            
        except Exception as e:
            logger.error(f"Error getting data summary: {e}")
            return {'error': str(e)}
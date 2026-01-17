"""
Sample Data Generator for ITOS Testing
========================================

Generate realistic sample data for testing the ITOS system.
Creates 1-minute OHLCV data with proper market characteristics.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from pathlib import Path
from typing import List, Dict, Any
import random

from .config import DATA_DIR, MARKET_OPEN, MARKET_CLOSE
from .types import MarketData


class SampleDataGenerator:
    """
    Generate realistic sample market data for testing.
    
    Features:
    - Realistic price movements
    - Proper OHLC relationships
    - Volume patterns
    - Market hours adherence
    - Multiple symbols with different characteristics
    """
    
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Indian market symbols
        self.symbols = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR',
            'ICICIBANK', 'KOTAKBANK', 'SBIN', 'AXISBANK', 'BAJFINANCE'
        ]
        
        # Symbol characteristics (base price, volatility)
        self.symbol_characteristics = {
            'RELIANCE': {'base_price': 2500, 'volatility': 0.015},
            'TCS': {'base_price': 3500, 'volatility': 0.012},
            'HDFCBANK': {'base_price': 1600, 'volatility': 0.010},
            'INFY': {'base_price': 1400, 'volatility': 0.014},
            'HINDUNILVR': {'base_price': 2500, 'volatility': 0.011},
            'ICICIBANK': {'base_price': 900, 'volatility': 0.013},
            'KOTAKBANK': {'base_price': 1800, 'volatility': 0.010},
            'SBIN': {'base_price': 600, 'volatility': 0.015},
            'AXISBANK': {'base_price': 800, 'volatility': 0.014},
            'BAJFINANCE': {'base_price': 7000, 'volatility': 0.016}
        }
    
    def generate_sample_data(self, start_date: str = '2023-01-01', 
                           end_date: str = '2023-12-31',
                           symbols: List[str] = None) -> None:
        """
        Generate sample data for all symbols.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            symbols: List of symbols to generate (None for all)
        """
        if symbols is None:
            symbols = self.symbols
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        print(f"Generating sample data from {start_date} to {end_date}")
        
        for symbol in symbols:
            print(f"Generating data for {symbol}...")
            self._generate_symbol_data(symbol, start, end)
        
        print("Sample data generation completed!")
    
    def _generate_symbol_data(self, symbol: str, start_date: datetime, end_date: datetime):
        """Generate data for a single symbol."""
        # Get symbol characteristics
        char = self.symbol_characteristics.get(symbol, {
            'base_price': 1000, 'volatility': 0.012
        })
        
        base_price = char['base_price']
        volatility = char['volatility']
        
        # Generate trading days
        trading_days = self._generate_trading_days(start_date, end_date)
        
        all_data = []
        
        for day in trading_days:
            day_data = self._generate_day_data(symbol, day, base_price, volatility)
            all_data.extend(day_data)
            
            # Update base price for next day (with some drift)
            if day_data:
                last_close = day_data[-1]['close']
                base_price = last_close * (1 + np.random.normal(0, 0.005))
        
        # Create DataFrame
        df = pd.DataFrame(all_data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
        # Save to Parquet
        file_path = self.data_dir / f"{symbol}.parquet"
        df.to_parquet(file_path, index=True)
        
        print(f"Saved {len(df)} data points for {symbol}")
    
    def _generate_trading_days(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """Generate list of trading days (weekdays only)."""
        trading_days = []
        current_date = start_date
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:
                trading_days.append(current_date)
            current_date += timedelta(days=1)
        
        return trading_days
    
    def _generate_day_data(self, symbol: str, date: datetime, 
                          base_price: float, volatility: float) -> List[Dict]:
        """Generate data for a single trading day."""
        # Market hours: 09:15 to 15:30
        market_open = date.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = date.replace(hour=15, minute=30, second=0, microsecond=0)
        
        # Generate minute timestamps
        timestamps = []
        current_time = market_open
        
        while current_time <= market_close:
            # Skip lunch break (no lunch break in Indian market, but reduce activity)
            if time(12, 30) <= current_time.time() <= time(13, 30):
                # Keep trading but with lower volume
                pass
            timestamps.append(current_time)
            current_time += timedelta(minutes=1)
        
        # Generate price data
        day_data = []
        current_price = base_price
        
        # Add gap at open
        gap = np.random.normal(0, volatility * 0.5)
        current_price *= (1 + gap)
        
        for i, timestamp in enumerate(timestamps):
            # Time-based volatility adjustment
            time_factor = self._get_time_factor(timestamp.time())
            
            # Price movement
            price_change = np.random.normal(0, volatility * time_factor)
            current_price *= (1 + price_change)
            
            # Generate OHLC
            high = current_price * (1 + abs(np.random.normal(0, volatility * 0.3)))
            low = current_price * (1 - abs(np.random.normal(0, volatility * 0.3)))
            
            # Ensure OHLC relationships
            high = max(high, current_price)
            low = min(low, current_price)
            
            # Open and close
            if i == 0:
                open_price = current_price
            else:
                open_price = day_data[-1]['close']
            
            close_price = current_price
            
            # Volume
            base_volume = np.random.randint(1000, 5000)
            volume_multiplier = self._get_volume_multiplier(timestamp.time(), i, len(timestamps))
            volume = int(base_volume * volume_multiplier)
            
            day_data.append({
                'datetime': timestamp,
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
        
        return day_data
    
    def _get_time_factor(self, current_time: time) -> float:
        """Get time-based volatility factor."""
        # Higher volatility during first and last hours
        if time(9, 15) <= current_time <= time(10, 30):
            return 1.5  # First hour
        elif time(14, 0) <= current_time <= time(15, 30):
            return 1.3  # Last hour
        elif time(12, 30) <= current_time <= time(13, 30):
            return 0.7  # Lunch period
        else:
            return 1.0  # Normal hours
    
    def _get_volume_multiplier(self, current_time: time, minute_index: int, total_minutes: int) -> float:
        """Get volume multiplier based on time of day."""
        # Higher volume at open and close
        if time(9, 15) <= current_time <= time(9, 30):
            return 2.0  # Opening auction
        elif time(15, 15) <= current_time <= time(15, 30):
            return 1.8  # Closing
        elif time(10, 0) <= current_time <= time(11, 0):
            return 1.3  # Mid-morning
        elif time(14, 0) <= current_time <= time(15, 0):
            return 1.4  # Afternoon
        else:
            return 1.0
    
    def generate_specific_scenario(self, symbol: str, date: str, 
                                 scenario: str = 'trend_day') -> None:
        """
        Generate specific market scenario for testing.
        
        Args:
            symbol: Symbol name
            date: Date in YYYY-MM-DD format
            scenario: 'trend_day', 'range_day', 'reversal_day'
        """
        target_date = datetime.strptime(date, '%Y-%m-%d')
        char = self.symbol_characteristics.get(symbol, {
            'base_price': 1000, 'volatility': 0.012
        })
        
        if scenario == 'trend_day':
            day_data = self._generate_trend_day(symbol, target_date, char)
        elif scenario == 'range_day':
            day_data = self._generate_range_day(symbol, target_date, char)
        elif scenario == 'reversal_day':
            day_data = self._generate_reversal_day(symbol, target_date, char)
        else:
            day_data = self._generate_day_data(symbol, target_date, char['base_price'], char['volatility'])
        
        # Create DataFrame and save
        df = pd.DataFrame(day_data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
        file_path = self.data_dir / f"{symbol}_{date}_{scenario}.parquet"
        df.to_parquet(file_path, index=True)
        
        print(f"Generated {scenario} data for {symbol} on {date}")
    
    def _generate_trend_day(self, symbol: str, date: datetime, char: Dict) -> List[Dict]:
        """Generate a trend day scenario."""
        base_price = char['base_price']
        volatility = char['volatility']
        
        # Strong uptrend throughout the day
        day_data = self._generate_day_data(symbol, date, base_price, volatility)
        
        # Modify to create trend
        trend_strength = 0.02  # 2% upward trend
        minutes_in_day = len(day_data)
        
        for i, candle in enumerate(day_data):
            # Add trend component
            trend_component = trend_strength * (i / minutes_in_day)
            
            # Update prices
            candle['high'] *= (1 + trend_component)
            candle['low'] *= (1 + trend_component)
            candle['close'] *= (1 + trend_component)
            
            # Round to 2 decimal places
            candle['high'] = round(candle['high'], 2)
            candle['low'] = round(candle['low'], 2)
            candle['close'] = round(candle['close'], 2)
        
        return day_data
    
    def _generate_range_day(self, symbol: str, date: datetime, char: Dict) -> List[Dict]:
        """Generate a range-bound day scenario."""
        base_price = char['base_price']
        volatility = char['volatility'] * 0.5  # Lower volatility
        
        return self._generate_day_data(symbol, date, base_price, volatility)
    
    def _generate_reversal_day(self, symbol: str, date: datetime, char: Dict) -> List[Dict]:
        """Generate a reversal day scenario."""
        base_price = char['base_price']
        volatility = char['volatility']
        
        day_data = self._generate_day_data(symbol, date, base_price, volatility)
        
        # Create reversal pattern (down first, then up)
        minutes_in_day = len(day_data)
        reversal_point = minutes_in_day // 2
        
        for i, candle in enumerate(day_data):
            if i < reversal_point:
                # First half: downtrend
                trend_component = -0.01 * (1 - i / reversal_point)
            else:
                # Second half: uptrend
                trend_component = 0.01 * ((i - reversal_point) / reversal_point)
            
            # Update prices
            candle['high'] *= (1 + trend_component)
            candle['low'] *= (1 + trend_component)
            candle['close'] *= (1 + trend_component)
            
            # Round to 2 decimal places
            candle['high'] = round(candle['high'], 2)
            candle['low'] = round(candle['low'], 2)
            candle['close'] = round(candle['close'], 2)
        
        return day_data


# Example usage
if __name__ == "__main__":
    generator = SampleDataGenerator()
    
    # Generate sample data for all symbols
    generator.generate_sample_data(
        start_date='2023-01-01',
        end_date='2023-03-31'  # 3 months for testing
    )
    
    # Generate specific scenarios
    generator.generate_specific_scenario('RELIANCE', '2023-01-15', 'trend_day')
    generator.generate_specific_scenario('TCS', '2023-01-16', 'range_day')
    generator.generate_specific_scenario('HDFCBANK', '2023-01-17', 'reversal_day')
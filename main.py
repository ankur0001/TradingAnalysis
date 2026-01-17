"""
ITOS Main Execution Script
==========================

Main script to run the ITOS system end-to-end.
This script demonstrates the complete workflow:
1. Data generation (for testing)
2. Strategy execution
3. Analytics and evaluation
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from itos.core.data_engine import DataEngine
from itos.core.strategy_engine import StrategyEngine
from itos.core.analytics_engine import AnalyticsEngine
from itos.core.sample_data_generator import SampleDataGenerator
from itos.strategies.str001_orb import STR001_ORB
from itos.strategies.str002_orb_filtered import STR002_ORB_FILTERED
from itos.strategies.str003_vwap_pullback import STR003_VWAP_PULLBACK

import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function."""
    print("=" * 60)
    print("ITOS - Intraday Trading Operating System")
    print("=" * 60)
    
    # Step 1: Generate sample data (for testing)
    print("\n🔧 Step 1: Generating Sample Data")
    print("-" * 40)
    
    generator = SampleDataGenerator()
    generator.generate_sample_data(
        start_date='2023-01-01',
        end_date='2023-03-31',  # 3 months for testing
        symbols=['RELIANCE', 'TCS', 'HDFCBANK']  # 3 symbols for quick testing
    )
    
    # Step 2: Run strategies
    print("\n🚀 Step 2: Running Strategies")
    print("-" * 40)
    
    strategy_engine = StrategyEngine()
    
    # Define strategies to run
    strategies = [
        STR001_ORB(),
        STR002_ORB_FILTERED(),
        STR003_VWAP_PULLBACK()
    ]
    
    for strategy in strategies:
        print(f"\n📊 Running {strategy.get_config().name}...")
        success = strategy_engine.run_strategy(strategy)
        
        if success:
            print(f"✅ {strategy.get_config().name} completed successfully")
        else:
            print(f"❌ {strategy.get_config().name} failed")
    
    # Step 3: Analytics
    print("\n📈 Step 3: Running Analytics")
    print("-" * 40)
    
    analytics_engine = AnalyticsEngine()
    
    for strategy in strategies:
        strategy_name = strategy.get_config().name
        print(f"\n🔍 Analyzing {strategy_name}...")
        
        # Load strategy results
        trades_df = strategy_engine.get_strategy_results(strategy_name)
        
        if trades_df is not None and not trades_df.empty:
            # Run analytics
            result = analytics_engine.analyze_strategy(strategy_name, trades_df)
            
            # Print summary
            print(f"\n📋 {strategy_name} Summary:")
            print(f"   Total Trades: {result.total_trades}")
            print(f"   Total PnL: ₹{result.total_pnl:,.2f}")
            print(f"   Win Rate: {result.winning_trades/result.total_trades*100:.1f}%")
            print(f"   Profit Factor: {result.profit_factor:.2f}")
            print(f"   Max Drawdown: {result.max_drawdown*100:.2f}%")
            print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
            
            # Get recommendation
            recommendation = analytics_engine.evaluate_strategy(result)
            print(f"   Recommendation: {recommendation}")
            
            if recommendation == "APPROVE":
                print("   ✅ Strategy approved for live trading")
            elif recommendation == "MODIFY":
                print("   ⚠️ Strategy needs modification")
            else:
                print("   ❌ Strategy killed - not viable")
        else:
            print(f"   ⚠️ No trades found for {strategy_name}")
    
    # Step 4: Strategy comparison
    print("\n🔄 Step 4: Strategy Comparison")
    print("-" * 40)
    
    strategy_names = [s.get_config().name for s in strategies]
    comparison_df = analytics_engine.compare_strategies(strategy_names)
    
    if not comparison_df.empty:
        print("\n📊 Strategy Performance Comparison:")
        print(comparison_df.to_string(index=False))
        
        # Save comparison
        comparison_file = Path("itos") / "final" / "strategy_comparison.csv"
        comparison_file.parent.mkdir(exist_ok=True)
        comparison_df.to_csv(comparison_file, index=False)
        print(f"\n💾 Comparison saved to {comparison_file}")
    
    print("\n🎉 ITOS execution completed!")
    print("=" * 60)
    print("Next steps:")
    print("1. Review analytics in itos/analytics/")
    print("2. Check strategy comparison in itos/final/")
    print("3. Modify/kill strategies based on performance")
    print("4. Develop new strategies using the framework")
    print("=" * 60)


if __name__ == "__main__":
    main()
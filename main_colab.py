"""
ITOS Main Execution Script - Google Colab Edition
===============================================

Main script to run the ITOS system end-to-end on Google Colab.
This script demonstrates the complete workflow:
1. Mount Google Drive and convert Kaggle data
2. Strategy execution
3. Analytics and evaluation
4. Results visualization
"""

import sys
import os
import gc
import logging
from datetime import datetime

# Google Colab specific imports
try:
    from google.colab import drive
    import kagglehub
    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False

# Add the project to Python path
if DRIVE_AVAILABLE:
    # Mount Google Drive
    drive.mount("/content/drive")
    
    # Download Kaggle dataset
    DATASET = "debashis74017/algo-trading-data-nifty-100-data-with-indicators"
    print("📥 Downloading Kaggle dataset...")
    path = kagglehub.dataset_download(DATASET)
    print(f"📁 Dataset downloaded at: {path}")
    
    # Set up paths
    DRIVE_BASE = "/content/drive/MyDrive/itos"
    
    # Add project to Python path
    sys.path.insert(0, DRIVE_BASE)
    
    # Import ITOS modules
    from itos_colab.core.data_engine import ColabDataEngine
    from itos_colab.core.strategy_engine import ColabStrategyEngine
    from itos_colab.core.analytics_engine import ColabAnalyticsEngine
    from itos_colab.strategies.str001_orb import STR001_ORB
    from itos_colab.strategies.str002_orb_filtered import STR002_ORB_FILTERED
    from itos_colab.strategies.str003_vwap_pullback import STR003_VWAP_PULLBACK
    
else:
    print("⚠️ Google Colab not available - running in local mode")
    # Local imports for testing
    from itos_colab.core.data_engine import ColabDataEngine
    from itos_colab.core.strategy_engine import ColabStrategyEngine
    from itos_colab.core.analytics_engine import ColabAnalyticsEngine
    from itos_colab.strategies.str001_orb import STR001_ORB
    from itos_colab.strategies.str002_orb_filtered import STR002_ORB_FILTERED
    from itos_colab.strategies.str003_vwap_pullback import STR003_VWAP_PULLBACK

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{DRIVE_BASE}/logs/main_execution.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main execution function."""
    print("=" * 80)
    print("🚀 ITOS - Intraday Trading Operating System (Google Colab Edition)")
    print("=" * 80)
    
    try:
        # Step 1: Convert Kaggle data to Parquet
        print("\n📊 Step 1: Converting Kaggle Data to Parquet")
        print("-" * 60)
        
        data_engine = ColabDataEngine()
        
        # Convert data (resume-safe)
        success = data_engine.convert_kaggle_data()
        
        if not success:
            print("❌ Failed to convert Kaggle data")
            return
        
        # Get data summary
        summary = data_engine.get_data_summary()
        print(f"\n📋 Data Summary:")
        print(f"   Processed Symbols: {summary.get('symbols', 0)}")
        print(f"   Total Records: {summary.get('total_records', 0):,}")
        print(f"   Date Range: {summary.get('date_range', ('N/A', 'N/A'))}")
        print(f"   Successful: {summary.get('processed', 0)}")
        print(f"   Failed: {summary.get('failed', 0)}")
        
        # Memory cleanup
        del data_engine
        gc.collect()
        
        # Step 2: Run strategies
        print("\n🎯 Step 2: Running Trading Strategies")
        print("-" * 60)
        
        strategy_engine = ColabStrategyEngine()
        
        # Define strategies to run
        strategies = [
            STR001_ORB(),
            STR002_ORB_FILTERED(),
            STR003_VWAP_PULLBACK()
        ]
        
        for strategy in strategies:
            print(f"\n📈 Running {strategy.get_config().name}...")
            success = strategy_engine.run_strategy(strategy)
            
            if success:
                print(f"✅ {strategy.get_config().name} completed successfully")
                
                # Get execution summary
                summary = strategy_engine.get_execution_summary()
                print(f"   Processed: {summary['processed_symbols']}")
                print(f"   Failed: {summary['failed_symbols']}")
                
            else:
                print(f"❌ {strategy.get_config().name} failed")
            
            # Memory cleanup
            gc.collect()
        
        # Step 3: Analytics
        print("\n📊 Step 3: Running Strategy Analytics")
        print("-" * 60)
        
        analytics_engine = ColabAnalyticsEngine()
        
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
                print(f"   Winning Trades: {result.winning_trades}")
                print(f"   Losing Trades: {result.losing_trades}")
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
            
            # Memory cleanup
            gc.collect()
        
        # Step 4: Strategy comparison
        print("\n🔄 Step 4: Strategy Comparison")
        print("-" * 60)
        
        strategy_names = [s.get_config().name for s in strategies]
        comparison_df = analytics_engine.compare_strategies(strategy_names)
        
        if not comparison_df.empty:
            print("\n📊 Strategy Performance Comparison:")
            print(comparison_df.to_string(index=False))
            
            # Display best strategy
            best_strategy = comparison_df.iloc[0]
            print(f"\n🏆 Best Strategy: {best_strategy['Strategy']}")
            print(f"   Total PnL: ₹{best_strategy['Total PnL']:,.2f}")
            print(f"   Win Rate: {best_strategy['Win Rate']*100:.1f}%")
            print(f"   Sharpe Ratio: {best_strategy['Sharpe Ratio']:.2f}")
        
        # Step 5: Final summary
        print("\n🎉 Step 5: Final Summary")
        print("-" * 60)
        
        # Analytics summary
        analytics_summary = analytics_engine.get_analytics_summary()
        print(f"\n📊 Analytics Summary:")
        print(f"   Analyzed Strategies: {analytics_summary.get('analyzed_strategies', 0)}")
        print(f"   Strategies List: {analytics_summary.get('strategies', [])}")
        
        # File locations
        print(f"\n📁 Generated Files on Google Drive:")
        print(f"   📊 Data: {DRIVE_BASE}/minute_parquet/")
        print(f"   📈 Results: {DRIVE_BASE}/STR_results/")
        print(f"   📋 Analytics: {DRIVE_BASE}/analytics/")
        print(f"   📄 Comparison: {DRIVE_BASE}/analytics/strategy_comparison.csv")
        
        print("\n🎯 Next Steps:")
        print("   1. Review detailed analytics in Google Drive")
        print("   2. Examine strategy dashboards (PNG files)")
        print("   3. Modify/kill strategies based on performance")
        print("   4. Develop new strategies using the framework")
        print("   5. Test with additional market data")
        
        print("\n" + "=" * 80)
        print("✅ ITOS execution completed successfully!")
        print("=" * 80)
        
        # Final cleanup
        del strategy_engine
        del analytics_engine
        gc.collect()
        
    except Exception as e:
        logger.error(f"❌ Error in main execution: {e}")
        print(f"\n❌ Execution failed: {e}")
        print("Please check the logs for details.")
        return


def display_google_drive_info():
    """Display Google Drive information."""
    if DRIVE_AVAILABLE:
        print(f"📁 Google Drive Base: {DRIVE_BASE}")
        print(f"📊 Data Directory: {DRIVE_BASE}/minute_parquet")
        print(f"📈 Results Directory: {DRIVE_BASE}/STR_results")
        print(f"📋 Analytics Directory: {DRIVE_BASE}/analytics")
        print(f"📄 Logs Directory: {DRIVE_BASE}/logs")


if __name__ == "__main__":
    display_google_drive_info()
    main()
# 📘 ITOS — Intraday Trading Operating System (Google Colab Edition)

## 🚀 Google Colab Optimized Version

This version of ITOS is specifically optimized for **Google Colab** with **Google Drive** persistence, making it perfect for large-scale strategy development and testing.

### 🎯 Key Features

#### **Google Colab Integration**
- ✅ **Google Drive Mounting** - Automatic mounting and path setup
- ✅ **Kaggle Dataset Integration** - Direct download and processing
- ✅ **Resume-Safe Processing** - Interrupt and continue anytime
- ✅ **Memory Optimization** - Batch processing for Colab constraints
- ✅ **Progress Tracking** - Real-time progress bars and logging

#### **Data Pipeline**
- ✅ **CSV to Parquet Conversion** - Efficient data format conversion
- ✅ **Trading Hours Filtering** - Market hours adherence
- ✅ **Data Validation** - Quality checks and cleaning
- ✅ **Chunk Processing** - Memory-efficient large dataset handling

#### **Strategy Framework**
- ✅ **3 Example Strategies** - ORB, Filtered ORB, VWAP Pullback
- ✅ **Modular Architecture** - Easy strategy development
- ✅ **Configuration Management** - Centralized parameter control
- ✅ **Signal Generation** - Robust trade generation logic

#### **Analytics Engine**
- ✅ **Comprehensive Metrics** - PnL, drawdown, Sharpe, etc.
- ✅ **Risk Analysis** - VaR, consecutive losses, win/loss ratios
- ✅ **Performance Breakdown** - Monthly, daily, symbol analysis
- ✅ **Visualization Dashboard** - Interactive charts and plots

## 🛠️ Quick Start (Google Colab)

### Option 1: Complete Notebook (Recommended)
```bash
# Open in Google Colab
https://colab.research.google.com/github/yourrepo/ITOS_Colab_Demo.ipynb
```

### Option 2: Script Execution
```python
# Mount Google Drive and run main script
!python main_colab.py
```

## 📊 System Architecture

```
📁 Google Drive Structure
├── itos/
│   ├── minute_parquet/      # Clean market data (Parquet)
│   ├── STR_results/         # Per-strategy trade results
│   ├── analytics/           # Performance analytics
│   ├── logs/                # Execution logs
│   └── final/               # Merged results
```

## 🚀 One-Click Execution

### Step 1: Mount and Setup
```python
from google.colab import drive
drive.mount('/content/drive')

# Auto-setup paths and directories
# Done automatically by ITOS
```

### Step 2: Data Processing
```python
# Download and convert Kaggle data
# Automatic CSV to Parquet conversion
# Resume-safe processing
# Memory-optimized
```

### Step 3: Strategy Execution
```python
# Run strategies across all symbols
# Batch processing (5 symbols at a time)
# Auto-save every 10 symbols
# Progress tracking
```

### Step 4: Analytics
```python
# Comprehensive performance analysis
# Risk metrics calculation
# Visualization generation
# Strategy comparison
```

## 📈 Available Strategies

### STR_001_ORB - Opening Range Breakout
- **Entry**: 09:30 open breakout
- **Exit**: 15:25 close
- **Risk**: 2% stop loss, 3% target
- **Filters**: None (basic)

### STR_002_ORB_FILTERED - Filtered ORB
- **Entry**: 09:30 breakout with volume confirmation
- **Filters**: Gap-up opening, volume multiplier
- **Exit**: 15:25 close
- **Risk**: 2% stop loss, 3% target

### STR_003_VWAP_PULLBACK - VWAP Pullback
- **Entry**: Pullback to VWAP during trend day
- **Filters**: Trend strength, volume confirmation
- **Exit**: 15:25 close
- **Risk**: 2% stop loss, 3% target

## 📊 Analytics Features

### Performance Metrics
- **Total PnL**: Overall profitability
- **Win Rate**: Percentage of winning trades
- **Profit Factor**: Gross profit / gross loss
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Peak-to-trough decline
- **Average Duration**: Trade holding time

### Risk Analysis
- **Value at Risk (VaR)**: 95% and 99% confidence
- **Consecutive Losses**: Maximum losing streak
- **Win/Loss Ratio**: Average winner vs loser
- **Monthly Stability**: Consistency analysis

### Visualization
- **Equity Curves**: Cumulative performance
- **Drawdown Charts**: Risk visualization
- **Monthly/Yearly Breakdown**: Time analysis
- **Symbol Performance**: Individual stock analysis
- **Exit Reason Analysis**: Strategy effectiveness

## 🎯 Strategy Evaluation Criteria

### Minimum Requirements
- **Trades**: ≥ 50 trades
- **Drawdown**: ≤ 20%
- **Profit Factor**: ≥ 1.2
- **Total PnL**: Positive
- **Sharpe Ratio**: ≥ 0.5

### Recommendations
- **✅ APPROVE**: Strategy meets all criteria
- **⚠️ MODIFY**: Strategy needs parameter adjustment
- **❌ KILL**: Strategy not viable

## 🛠️ Development Workflow

### 1. Strategy Development
```python
class STR_XXX_NEW(BaseStrategy):
    def __init__(self):
        config = StrategyConfig(
            name="STR_XXX_NEW",
            side="LONG",
            entry_time_start=time(9, 30),
            entry_time_end=time(10, 30),
            exit_time=time(15, 25),
            parameters={...},
            description="Strategy description"
        )
        super().__init__(config)
    
    def generate_signals(self, market_data):
        # Implement strategy logic
        pass
```

### 2. Testing
```python
# Test single strategy
strategy = STR_XXX_NEW()
engine = ColabStrategyEngine()
success = engine.run_strategy(strategy)
```

### 3. Analytics
```python
# Analyze performance
analytics = ColabAnalyticsEngine()
trades_df = engine.get_strategy_results("STR_XXX_NEW")
result = analytics.analyze_strategy("STR_XXX_NEW", trades_df)
recommendation = analytics.evaluate_strategy(result)
```

## 📁 File Management

### Google Drive Organization
```
/content/drive/MyDrive/itos/
├── minute_parquet/          # Clean market data
│   ├── RELIANCE.parquet
│   ├── TCS.parquet
│   └── ...
├── STR_results/             # Strategy outputs
│   ├── STR_001_ORB_all_trades.parquet
│   ├── STR_002_ORB_FILTERED_all_trades.parquet
│   └── ...
├── analytics/              # Performance analysis
│   ├── STR_001_ORB_summary.csv
│   ├── STR_001_ORB_dashboard.png
│   ├── STR_001_ORB_analytics.json
│   └── strategy_comparison.csv
├── logs/                   # System logs
│   ├── data_engine.log
│   ├── strategy_engine.log
│   └── analytics_engine.log
└── final/                  # Merged results
    └── strategy_comparison.csv
```

## 🔧 Configuration

### Colab Optimization
```python
COLAB_SETTINGS = {
    'auto_save_interval': 10,    # Save every 10 symbols
    'memory_cleanup': True,       # Enable garbage collection
    'progress_display': True,      # Show progress bars
    'resume_capability': True,     # Enable resume functionality
    'chunk_processing': True,      # Process data in chunks
    'batch_size': 5,             # Symbols per batch
    'max_memory_gb': 2,          # Memory limit
}
```

### Data Source Configuration
```python
DATA_SOURCE = {
    'type': 'kaggle',
    'dataset': 'debashis74017/algo-trading-data-nifty-100-data-with-indicators',
    'file_pattern': '_minute.csv',
    'timestamp_columns': ['timestamp', 'datetime', 'date', 'Date', 'time', 'Time']
}
```

## 📊 Sample Results

### Strategy Performance Summary
| Strategy | Trades | PnL | Win Rate | Profit Factor | Sharpe | Recommendation |
|----------|---------|-------|-----------|---------------|----------|----------------|
| STR_001_ORB | 156 | ₹45,230 | 52.3% | 1.34 | 0.87 | MODIFY |
| STR_002_ORB_FILTERED | 89 | ₹32,150 | 58.1% | 1.56 | 1.12 | APPROVE |
| STR_003_VWAP_PULLBACK | 124 | ₹28,940 | 49.6% | 1.18 | 0.69 | MODIFY |

### Risk Analysis
- **VaR (95%)**: ₹1,250
- **Max Consecutive Losses**: 8
- **Avg Win/Loss Ratio**: 1.45
- **Monthly Stability**: 73% profitable months

## 🎯 Benefits of Google Colab Version

### ✅ Advantages
1. **No Local Setup** - Works directly in browser
2. **Free GPU Access** - For ML enhancements
3. **Google Drive Integration** - Persistent storage
4. **High RAM Available** - For large datasets
5. **Collaborative** - Easy sharing
6. **Scalable** - Handle 500+ strategies

### ✅ Cost Effective
- **Free Tier** - No additional cost
- **No Infrastructure** - No server maintenance
- **Scalable Computing** - Pay-as-you-go
- **Automatic Updates** - Always latest version

## 🔄 Next Steps

### Immediate
1. **Run Complete Workflow** - Test all 3 strategies
2. **Review Analytics** - Examine performance
3. **Modify Strategies** - Improve weak performers
4. **Develop New Strategies** - Add more approaches

### Medium Term
1. **Phase 3 - Strategy Library** - Approved strategies collection
2. **Phase 4 - Stock Selection** - Daily symbol filtering
3. **Phase 5 - Market Regime** - Real-time classification
4. **Phase 6 - Live Signals** - Real-time alerts

### Long Term
1. **ML Integration** - Machine learning enhancements
2. **Multi-Asset** - Different asset classes
3. **Portfolio Optimization** - Position sizing
4. **Risk Management** - Advanced risk controls

## 🚨 Important Notes

### Google Colab Specific
- **Runtime Limits**: 12-hour sessions
- **Memory Limits**: Based on Colab tier
- **Storage**: Google Drive quota
- **Network**: Dataset download limits

### Best Practices
- **Save Frequently**: Auto-save every 10 symbols
- **Monitor Memory**: Use batch processing
- **Resume Capability**: Interrupt and continue
- **Log Analysis**: Check logs for errors

---

## 🎯 Getting Started

### 1. Open Google Colab
```bash
# Navigate to Google Colab
# Upload ITOS_Colab_Demo.ipynb
# Or clone from repository
```

### 2. Run Cells Sequentially
1. **Install Dependencies** - Required packages
2. **Mount Google Drive** - Setup persistence
3. **Download Data** - Kaggle dataset
4. **Convert Data** - CSV to Parquet
5. **Run Strategies** - Execute trading logic
6. **Analyze Results** - Performance evaluation
7. **Review Outputs** - Check Google Drive

### 3. Review Results
- **Analytics**: `/drive/MyDrive/itos/analytics/`
- **Results**: `/drive/MyDrive/itos/STR_results/`
- **Logs**: `/drive/MyDrive/itos/logs/`

---

## 🎯 Final Note

This Google Colab version provides **enterprise-grade strategy development** capabilities with **zero infrastructure setup**. You can now:

- **Develop 500+ strategies** systematically
- **Test on real market data** 
- **Analyze performance** comprehensively
- **Make data-driven decisions** about strategy viability

**ITOS transforms strategy development from art to science.**

---

**ITOS - Intraday Trading Operating System (Google Colab Edition)**
*Professional strategy development, simplified.*
"""
Phase 2 - Strategy Analytics Engine
===================================

Evaluate if a strategy is worth keeping.
Metrics: Net PnL, Drawdown, Profit Factor, Yearly Stability, Regime Behavior
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import logging

from .config import ANALYTICS_DIR, LOGS_DIR, MIN_TRADES, MAX_DRAWDOWN, MIN_PROFIT_FACTOR
from .types import StrategyResult, Trade

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """
    Strategy analytics and evaluation engine.
    
    Features:
    - Calculate comprehensive performance metrics
    - Generate visual analytics
    - Evaluate strategy viability
    - Compare strategies
    """
    
    def __init__(self, analytics_dir: Path = ANALYTICS_DIR):
        self.analytics_dir = analytics_dir
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOGS_DIR / 'analytics_engine.log'),
                logging.StreamHandler()
            ]
        )
        
        # Set plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def analyze_strategy(self, strategy_name: str, trades_df: pd.DataFrame) -> StrategyResult:
        """
        Perform comprehensive analysis of a strategy.
        
        Args:
            strategy_name: Name of the strategy
            trades_df: DataFrame of all trades
            
        Returns:
            StrategyResult with comprehensive metrics
        """
        logger.info(f"Analyzing strategy: {strategy_name}")
        
        if trades_df.empty:
            logger.warning(f"No trades found for {strategy_name}")
            return self._create_empty_result(strategy_name)
        
        # Basic metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        total_pnl = trades_df['pnl'].sum()
        
        # Advanced metrics
        profit_factor = self._calculate_profit_factor(trades_df)
        max_drawdown = self._calculate_max_drawdown(trades_df)
        sharpe_ratio = self._calculate_sharpe_ratio(trades_df)
        avg_trade_duration = self._calculate_avg_duration(trades_df)
        
        # Additional analytics
        yearly_performance = self._analyze_yearly_performance(trades_df)
        monthly_performance = self._analyze_monthly_performance(trades_df)
        win_rate_analysis = self._analyze_win_rate(trades_df)
        risk_metrics = self._analyze_risk_metrics(trades_df)
        
        # Create result
        result = StrategyResult(
            strategy_name=strategy_name,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_pnl=total_pnl,
            max_drawdown=max_drawdown,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            avg_trade_duration=avg_trade_duration,
            metadata={
                'yearly_performance': yearly_performance,
                'monthly_performance': monthly_performance,
                'win_rate_analysis': win_rate_analysis,
                'risk_metrics': risk_metrics
            }
        )
        
        # Save analytics
        self._save_analytics(result)
        
        # Generate plots
        self._generate_plots(result, trades_df)
        
        logger.info(f"Analysis completed for {strategy_name}")
        return result
    
    def _create_empty_result(self, strategy_name: str) -> StrategyResult:
        """Create empty result for strategies with no trades."""
        return StrategyResult(
            strategy_name=strategy_name,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            total_pnl=0.0,
            max_drawdown=0.0,
            profit_factor=0.0,
            sharpe_ratio=0.0,
            avg_trade_duration=0.0,
            metadata={}
        )
    
    def _calculate_profit_factor(self, trades_df: pd.DataFrame) -> float:
        """Calculate profit factor (gross profit / gross loss)."""
        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] < 0]
        
        if losing_trades.empty:
            return float('inf') if not winning_trades.empty else 0.0
        
        gross_profit = winning_trades['pnl'].sum()
        gross_loss = abs(losing_trades['pnl'].sum())
        
        return gross_profit / gross_loss if gross_loss > 0 else 0.0
    
    def _calculate_max_drawdown(self, trades_df: pd.DataFrame) -> float:
        """Calculate maximum drawdown."""
        if trades_df.empty:
            return 0.0
        
        # Calculate cumulative PnL
        trades_df = trades_df.sort_values('entry_time')
        trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
        
        # Calculate running maximum
        trades_df['running_max'] = trades_df['cumulative_pnl'].expanding().max()
        
        # Calculate drawdown
        trades_df['drawdown'] = trades_df['cumulative_pnl'] - trades_df['running_max']
        
        return trades_df['drawdown'].min()
    
    def _calculate_sharpe_ratio(self, trades_df: pd.DataFrame) -> float:
        """Calculate Sharpe ratio (annualized)."""
        if trades_df.empty or len(trades_df) < 2:
            return 0.0
        
        # Calculate daily returns
        trades_df['entry_date'] = pd.to_datetime(trades_df['entry_time']).dt.date
        daily_pnl = trades_df.groupby('entry_date')['pnl'].sum()
        
        if len(daily_pnl) < 2:
            return 0.0
        
        # Calculate Sharpe ratio
        mean_return = daily_pnl.mean()
        std_return = daily_pnl.std()
        
        if std_return == 0:
            return 0.0
        
        # Annualize (252 trading days)
        sharpe = (mean_return / std_return) * np.sqrt(252)
        
        return sharpe
    
    def _calculate_avg_duration(self, trades_df: pd.DataFrame) -> float:
        """Calculate average trade duration in minutes."""
        if trades_df.empty:
            return 0.0
        
        trades_df['duration'] = (
            pd.to_datetime(trades_df['exit_time']) - 
            pd.to_datetime(trades_df['entry_time'])
        ).dt.total_seconds() / 60  # Convert to minutes
        
        return trades_df['duration'].mean()
    
    def _analyze_yearly_performance(self, trades_df: pd.DataFrame) -> Dict[str, float]:
        """Analyze performance by year."""
        trades_df['entry_year'] = pd.to_datetime(trades_df['entry_time']).dt.year
        yearly_stats = trades_df.groupby('entry_year').agg({
            'pnl': ['sum', 'count', 'mean'],
            'symbol': 'nunique'
        }).round(2)
        
        return yearly_stats.to_dict()
    
    def _analyze_monthly_performance(self, trades_df: pd.DataFrame) -> Dict[str, float]:
        """Analyze performance by month."""
        trades_df['entry_month'] = pd.to_datetime(trades_df['entry_time']).dt.month
        monthly_stats = trades_df.groupby('entry_month').agg({
            'pnl': ['sum', 'count', 'mean']
        }).round(2)
        
        return monthly_stats.to_dict()
    
    def _analyze_win_rate(self, trades_df: pd.DataFrame) -> Dict[str, float]:
        """Analyze win rate statistics."""
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # Win rate by symbol
        symbol_win_rate = trades_df.groupby('symbol').apply(
            lambda x: len(x[x['pnl'] > 0]) / len(x)
        ).mean()
        
        # Win rate by exit reason
        exit_reason_win_rate = trades_df.groupby('exit_reason').apply(
            lambda x: len(x[x['pnl'] > 0]) / len(x)
        ).to_dict()
        
        return {
            'overall_win_rate': win_rate,
            'symbol_avg_win_rate': symbol_win_rate,
            'exit_reason_win_rate': exit_reason_win_rate
        }
    
    def _analyze_risk_metrics(self, trades_df: pd.DataFrame) -> Dict[str, float]:
        """Analyze risk metrics."""
        if trades_df.empty:
            return {}
        
        # Calculate trade statistics
        pnl_series = trades_df['pnl']
        
        # Risk metrics
        var_95 = pnl_series.quantile(0.05)  # Value at Risk at 95%
        var_99 = pnl_series.quantile(0.01)  # Value at Risk at 99%
        
        # Maximum consecutive losses
        trades_df['is_loss'] = pnl_series < 0
        trades_df['loss_group'] = (trades_df['is_loss'] != trades_df['is_loss'].shift()).cumsum()
        max_consecutive_losses = trades_df.groupby('loss_group')['is_loss'].sum().max()
        
        # Average win and loss
        avg_win = pnl_series[pnl_series > 0].mean() if len(pnl_series[pnl_series > 0]) > 0 else 0
        avg_loss = pnl_series[pnl_series < 0].mean() if len(pnl_series[pnl_series < 0]) > 0 else 0
        
        return {
            'var_95': var_95,
            'var_99': var_99,
            'max_consecutive_losses': max_consecutive_losses,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_win_to_loss_ratio': abs(avg_win / avg_loss) if avg_loss != 0 else 0
        }
    
    def evaluate_strategy(self, result: StrategyResult) -> str:
        """
        Evaluate strategy and provide recommendation.
        
        Returns:
            'APPROVE', 'MODIFY', or 'KILL'
        """
        # Check minimum trades
        if result.total_trades < MIN_TRADES:
            return "KILL"
        
        # Check maximum drawdown
        if abs(result.max_drawdown) > MAX_DRAWDOWN:
            return "KILL"
        
        # Check profit factor
        if result.profit_factor < MIN_PROFIT_FACTOR:
            return "KILL"
        
        # Check total PnL
        if result.total_pnl <= 0:
            return "KILL"
        
        # Check Sharpe ratio
        if result.sharpe_ratio < 0.5:
            return "MODIFY"
        
        # Check consistency
        yearly_data = result.metadata.get('yearly_performance', {})
        if len(yearly_data) > 1:
            # Check if profitable in at least 60% of years
            profitable_years = sum(1 for year_data in yearly_data.values() 
                                 if year_data[('pnl', 'sum')] > 0)
            if profitable_years / len(yearly_data) < 0.6:
                return "MODIFY"
        
        return "APPROVE"
    
    def _save_analytics(self, result: StrategyResult):
        """Save analytics results to file."""
        # Create summary DataFrame
        summary_data = {
            'Strategy': [result.strategy_name],
            'Total Trades': [result.total_trades],
            'Winning Trades': [result.winning_trades],
            'Losing Trades': [result.losing_trades],
            'Total PnL': [result.total_pnl],
            'Max Drawdown': [result.max_drawdown],
            'Profit Factor': [result.profit_factor],
            'Sharpe Ratio': [result.sharpe_ratio],
            'Avg Duration (min)': [result.avg_trade_duration],
            'Recommendation': [self.evaluate_strategy(result)]
        }
        
        summary_df = pd.DataFrame(summary_data)
        
        # Save summary
        summary_file = self.analytics_dir / f"{result.strategy_name}_summary.csv"
        summary_df.to_csv(summary_file, index=False)
        
        # Save detailed analytics
        analytics_file = self.analytics_dir / f"{result.strategy_name}_analytics.json"
        import json
        with open(analytics_file, 'w') as f:
            json.dump(result.__dict__, f, indent=2, default=str)
        
        logger.info(f"Saved analytics for {result.strategy_name}")
    
    def _generate_plots(self, result: StrategyResult, trades_df: pd.DataFrame):
        """Generate visualization plots."""
        if trades_df.empty:
            return
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'{result.strategy_name} - Analytics Dashboard', fontsize=16)
        
        # Plot 1: Cumulative PnL
        trades_df_sorted = trades_df.sort_values('entry_time')
        trades_df_sorted['cumulative_pnl'] = trades_df_sorted['pnl'].cumsum()
        
        axes[0, 0].plot(trades_df_sorted['entry_time'], trades_df_sorted['cumulative_pnl'])
        axes[0, 0].set_title('Cumulative PnL')
        axes[0, 0].set_xlabel('Date')
        axes[0, 0].set_ylabel('PnL')
        axes[0, 0].grid(True)
        
        # Plot 2: PnL Distribution
        axes[0, 1].hist(trades_df['pnl'], bins=50, alpha=0.7)
        axes[0, 1].set_title('PnL Distribution')
        axes[0, 1].set_xlabel('PnL')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].grid(True)
        
        # Plot 3: Monthly Performance
        trades_df['entry_month'] = pd.to_datetime(trades_df['entry_time']).dt.month
        monthly_pnl = trades_df.groupby('entry_month')['pnl'].sum()
        
        axes[1, 0].bar(monthly_pnl.index, monthly_pnl.values)
        axes[1, 0].set_title('Monthly PnL')
        axes[1, 0].set_xlabel('Month')
        axes[1, 0].set_ylabel('PnL')
        axes[1, 0].grid(True)
        
        # Plot 4: Win Rate by Exit Reason
        exit_reason_stats = trades_df.groupby('exit_reason').apply(
            lambda x: len(x[x['pnl'] > 0]) / len(x)
        )
        
        axes[1, 1].bar(exit_reason_stats.index, exit_reason_stats.values)
        axes[1, 1].set_title('Win Rate by Exit Reason')
        axes[1, 1].set_xlabel('Exit Reason')
        axes[1, 1].set_ylabel('Win Rate')
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].grid(True)
        
        plt.tight_layout()
        
        # Save plot
        plot_file = self.analytics_dir / f"{result.strategy_name}_dashboard.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved plots for {result.strategy_name}")
    
    def compare_strategies(self, strategy_names: List[str]) -> pd.DataFrame:
        """Compare multiple strategies side by side."""
        comparison_data = []
        
        for strategy_name in strategy_names:
            analytics_file = self.analytics_dir / f"{strategy_name}_analytics.json"
            
            if analytics_file.exists():
                with open(analytics_file, 'r') as f:
                    data = json.load(f)
                
                comparison_data.append({
                    'Strategy': data['strategy_name'],
                    'Total Trades': data['total_trades'],
                    'Total PnL': data['total_pnl'],
                    'Max Drawdown': data['max_drawdown'],
                    'Profit Factor': data['profit_factor'],
                    'Sharpe Ratio': data['sharpe_ratio'],
                    'Win Rate': data['winning_trades'] / data['total_trades'] if data['total_trades'] > 0 else 0
                })
        
        return pd.DataFrame(comparison_data).sort_values('Total PnL', ascending=False)
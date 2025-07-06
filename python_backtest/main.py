import os
import time
import pandas as pd
import matplotlib.pyplot as plt
import sys
import argparse
from datetime import datetime
from utils.data_loader import load_data, print_data_summary, plot_price_volume
from strategies.moving_average import MovingAverageStrategy
from strategies.moving_average_volume_compensated import MovingAverageVolumeCompensatedStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.mean_reversion_volume_compensated import MeanReversionVolumeCompensatedStrategy
from strategies.rsi_bollinger import RSIBollingerStrategy
from backtester import Backtester
import logging
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Predefined market periods for testing
MARKET_PERIODS = {
    'bull_2017': ('2017-01-01', '2017-12-31', 'Bull Market 2017'),
    'bear_2018': ('2018-01-01', '2018-12-31', 'Bear Market 2018'),
    'bull_2019': ('2019-01-01', '2019-12-31', 'Bull Market 2019'),
    'covid_crash_2020': ('2020-02-01', '2020-04-30', 'COVID Crash 2020'),
    'bull_2021': ('2021-01-01', '2021-12-31', 'Bull Market 2021'),
    'bear_2022': ('2022-01-01', '2022-12-31', 'Bear Market 2022'),
    'recovery_2023': ('2023-01-01', '2023-12-31', 'Recovery 2023'),
    'jan_2023': ('2023-01-01', '2023-01-31', 'January 2023'),
    'march_2020': ('2020-03-01', '2020-03-31', 'March 2020 (COVID Crash)'),
    'december_2017': ('2017-12-01', '2017-12-31', 'December 2017 (Bull Market)'),
}

def parse_arguments():
    parser = argparse.ArgumentParser(description='Run trading strategy backtests')
    parser.add_argument('--start_date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end_date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--period', type=str, choices=list(MARKET_PERIODS.keys()), 
                       help='Predefined market period to test')
    parser.add_argument('--stop_loss', type=float, default=0.02, 
                       help='Stop-loss percentage (default: 0.02 = 2%%)')
    parser.add_argument('--position_size', type=float, default=0.5, 
                       help='Position size as percentage of capital (default: 0.5 = 50%%)')
    
    args = parser.parse_args()
    
    if args.period:
        start_date, end_date, description = MARKET_PERIODS[args.period]
        print(f"Using predefined period: {description}")
        return start_date, end_date, args.stop_loss, args.position_size
    elif args.start_date and args.end_date:
        return args.start_date, args.end_date, args.stop_loss, args.position_size
    else:
        print("Available predefined periods:")
        for key, (start, end, desc) in MARKET_PERIODS.items():
            print(f"  {key}: {desc} ({start} to {end})")
        print("\nUsage examples:")
        print("  python main.py --period bull_2017")
        print("  python main.py --start_date 2023-01-01 --end_date 2023-01-31")
        print("  python main.py --period bear_2022 --stop_loss 0.03 --position_size 0.3")
        sys.exit(1)

def setup_logging(output_dir: str):
    """
    Setup logging configuration for both file and console output.
    
    Args:
        output_dir (str): Directory path where log file will be saved
        
    Creates:
        - Console output for real-time monitoring
        - Log file (backtest.log) for detailed execution history
        
    Log Level: INFO - captures all important events and results
    """
    log_file = os.path.join(output_dir, 'backtest.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def main():
    """
    Main execution function for the backtesting framework.
    
    Command Line Arguments:
        --period: Market period to test (bull/bear/crisis/recovery/recent/custom)
        --start-date: Custom start date (YYYY-MM-DD format)
        --end-date: Custom end date (YYYY-MM-DD format)
        --short-window: Short MA period (default: 20)
        --long-window: Long MA period (default: 50)
        --min-crossover-strength: Signal strength threshold (default: 0.003)
        --position-size: Capital fraction per trade (default: 0.8)
        --stop-loss: Maximum loss percentage (default: 0.02)
        --data-path: Path to CSV data file
        --min-holding-period: Minimum holding period in minutes (0 = no restriction)
        --enable-regime-detection: Enable market regime detection (ATR/ADX)
        --disable-regime-detection: Disable market regime detection
        --atr-period: Period for ATR calculation
        --adx-period: Period for ADX calculation
        --multi-strategy: Run multiple strategies and compare performance
        --strategy: Strategy to use in single strategy mode (default: moving_average)
        
    Execution Flow:
        1. Parse command line arguments
        2. Setup logging and output directory
        3. Load and filter price data
        4. Create strategy and backtester
        5. Run backtest simulation
        6. Log results and generate plots
        7. Save all outputs to timestamped directory
    """
    parser = argparse.ArgumentParser(description='Run backtesting with different market periods')
    parser.add_argument('--period', choices=list(MARKET_PERIODS.keys()) + ['custom'], 
                       default=os.getenv('DEFAULT_PERIOD', 'bull_2021'), help='Market period to test')
    parser.add_argument('--start-date', type=str, help='Custom start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='Custom end date (YYYY-MM-DD)')
    parser.add_argument('--short-window', type=int, default=20, help='Short moving average window')
    parser.add_argument('--long-window', type=int, default=50, help='Long moving average window')
    parser.add_argument('--min-crossover-strength', type=float, default=0.001, 
                       help='Minimum crossover strength for signal generation')
    parser.add_argument('--position-size', type=float, default=float(os.getenv('DEFAULT_POSITION_SIZE', 0.8)), 
                       help='Position size as fraction of available capital')
    parser.add_argument('--stop-loss', type=float, default=float(os.getenv('DEFAULT_STOP_LOSS', 0.02)), 
                       help='Stop loss percentage')
    parser.add_argument('--data-path', type=str, default=os.getenv('DATA_PATH', './data/btcusd_1-min_data.csv'),
                       help='Path to the CSV data file')
    parser.add_argument('--min-holding-period', type=int, default=0,
                       help='Minimum holding period in minutes (0 = no restriction)')
    parser.add_argument('--enable-regime-detection', action='store_true', default=True,
                       help='Enable market regime detection (ATR/ADX)')
    parser.add_argument('--disable-regime-detection', action='store_true',
                       help='Disable market regime detection')
    parser.add_argument('--atr-period', type=int, default=14,
                       help='Period for ATR calculation')
    parser.add_argument('--adx-period', type=int, default=14,
                       help='Period for ADX calculation')
    parser.add_argument('--multi-strategy', action='store_true',
                       help='Run multiple strategies and compare performance')
    parser.add_argument('--strategy', choices=['moving_average', 'moving_average_volume_compensated', 'mean_reversion', 'mean_reversion_volume_compensated', 'rsi_bollinger'],
                       default='moving_average', help='Strategy to use in single strategy mode (default: moving_average)')
    
    args = parser.parse_args()

    # Use RESULTS_DIR from .env, fallback to python_backtest/results
    results_base_dir = os.getenv('RESULTS_DIR', 'python_backtest/results')
    os.makedirs(results_base_dir, exist_ok=True)
    output_dir = f"{results_base_dir}/results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)
    
    setup_logging(output_dir)
    
    # Load data
    logging.info("Loading data...")
    data = load_data(args.data_path)
    
    # Set date range - prioritize custom dates over predefined periods
    if args.start_date and args.end_date:
        start_date = args.start_date
        end_date = args.end_date
        logging.info(f"Using custom date range: {start_date} to {end_date}")
    elif args.period:
        if args.period == 'custom':
            if not args.start_date or not args.end_date:
                logging.error("Custom period requires both --start-date and --end-date")
                return
            start_date = args.start_date
            end_date = args.end_date
            logging.info(f"Using custom date range: {start_date} to {end_date}")
        else:
            start_date, end_date, description = MARKET_PERIODS[args.period]
            logging.info(f"Testing {args.period} market: {description}")
    else:
        # Default to bull_2021 if no dates specified
        start_date, end_date, description = MARKET_PERIODS['bull_2021']
        logging.info(f"Using default period: bull_2021 market - {description}")
    
    # Filter data by date range
    data = data[(data.index >= start_date) & (data.index <= end_date)]
    logging.info(f"Data loaded: {len(data)} records from {data.index[0]} to {data.index[-1]}")
    
    # Create strategy
    enable_regime = args.enable_regime_detection and not args.disable_regime_detection
    
    if args.multi_strategy:
        # Multi-strategy mode
        strategies = {
            'Moving Average': MovingAverageStrategy(
                short_window=args.short_window,
                long_window=args.long_window,
                min_crossover_strength=args.min_crossover_strength,
                min_holding_period=args.min_holding_period,
                enable_regime_detection=enable_regime,
                atr_period=args.atr_period,
                adx_period=args.adx_period
            ),
            'Moving Average Volume Compensated': MovingAverageVolumeCompensatedStrategy(
                short_window=args.short_window,
                long_window=args.long_window,
                enable_regime_detection=enable_regime,
                atr_period=args.atr_period,
                adx_period=args.adx_period
            ),
            'Mean Reversion': MeanReversionStrategy(
                window=args.short_window,
                enable_regime_detection=enable_regime,
                atr_period=args.atr_period,
                adx_period=args.adx_period
            ),
            'Mean Reversion Volume Compensated': MeanReversionVolumeCompensatedStrategy(
                window=args.short_window,
                enable_regime_detection=enable_regime,
                atr_period=args.atr_period,
                adx_period=args.adx_period
            ),
            'RSI + Bollinger Bands': RSIBollingerStrategy(
                enable_regime_detection=enable_regime,
                atr_period=args.atr_period,
                adx_period=args.adx_period
            )
        }
        
        # Create backtester
        backtester = Backtester(
            initial_capital=100.0,
            position_size=args.position_size,
            stop_loss=args.stop_loss
        )
        
        # Run multi-strategy backtest
        logging.info("Running multi-strategy backtest...")
        comparison_results = backtester.run_multiple_strategies(data, strategies)
        
        # Log comparison results
        logging.info("Multi-strategy backtest completed!")
        logging.info(f"Best strategy: {comparison_results['best_strategy']}")
        logging.info("\nStrategy Comparison:")
        print(comparison_results['comparison_table'].to_string(index=False))
        
        # Save comparison results
        comparison_file = os.path.join(output_dir, 'strategy_comparison.txt')
        with open(comparison_file, 'w') as f:
            f.write(f"Strategy Comparison - {args.period.upper()} Market\n")
            f.write("=" * 60 + "\n")
            f.write(f"Period: {start_date} to {end_date}\n")
            f.write(f"Best Strategy: {comparison_results['best_strategy']}\n\n")
            f.write(comparison_results['comparison_table'].to_string(index=False))
        
        # Create and save per-strategy plots
        for strategy_name, strategy_results in comparison_results['results'].items():
            portfolio = strategy_results['portfolio']
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
            # Price chart with buy/sell signals
            ax1.plot(portfolio.index, portfolio['price'], label='BTC Price', alpha=0.7)
            buy_signals = portfolio[portfolio['signal'] == 1]
            sell_signals = portfolio[portfolio['signal'] == -1]
            hold_signals = portfolio[portfolio['signal'] == 0]
            if len(buy_signals) > 0:
                ax1.scatter(buy_signals.index, buy_signals['price'], color='green', marker='^', s=60, label='Buy', alpha=0.8)
            if len(sell_signals) > 0:
                ax1.scatter(sell_signals.index, sell_signals['price'], color='red', marker='v', s=60, label='Sell', alpha=0.8)
            ax1.set_title(f'{strategy_name} - Price & Signals')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            # Equity curve (simple line like BTC price)
            ax2.plot(portfolio.index, portfolio['total_value'], label='Equity Curve', color='blue', linewidth=2)
            
            ax2.set_title('Equity Curve')
            ax2.set_ylabel('Portfolio Value (USD)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            plt.tight_layout()
            plot_filename = os.path.join(output_dir, f"{strategy_name.replace(' ', '_').replace('/', '_')}_plot.png")
            plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
            plt.close(fig)
            logging.info(f"Saved plot for {strategy_name} to: {plot_filename}")
        
        # Create comparison plot (do not show, only save)
        plt.figure(figsize=(14, 8))
        for strategy_name, strategy_results in comparison_results['results'].items():
            portfolio = strategy_results['portfolio']
            plt.plot(portfolio.index, portfolio['total_value'], 
                    label=f'{strategy_name} (Return: {strategy_results["total_return"]:.1%})', linewidth=2)
        plt.axhline(y=100, color='red', linestyle='--', alpha=0.7, label='Initial Capital')
        plt.title(f'Strategy Comparison - {args.period.upper()} Market')
        plt.ylabel('Portfolio Value (USD)')
        plt.xlabel('Date')
        plt.legend()
        plt.grid(True, alpha=0.3)
        comparison_plot_file = os.path.join(output_dir, 'strategy_comparison.png')
        plt.savefig(comparison_plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        logging.info(f"Comparison results saved to: {comparison_file}")
        logging.info(f"Comparison plot saved to: {comparison_plot_file}")
        
    else:
        # Single strategy mode
        if args.strategy == 'moving_average':
            strategy = MovingAverageStrategy(
                short_window=args.short_window,
                long_window=args.long_window,
                min_crossover_strength=args.min_crossover_strength,
                min_holding_period=args.min_holding_period,
                enable_regime_detection=enable_regime,
                atr_period=args.atr_period,
                adx_period=args.adx_period
            )
            strategy_name = f"Moving Average ({args.short_window}/{args.long_window})"
        elif args.strategy == 'moving_average_volume_compensated':
            strategy = MovingAverageVolumeCompensatedStrategy(
                short_window=args.short_window,
                long_window=args.long_window,
                enable_regime_detection=enable_regime,
                atr_period=args.atr_period,
                adx_period=args.adx_period
            )
            strategy_name = f"Moving Average Volume Compensated ({args.short_window}/{args.long_window})"
        elif args.strategy == 'mean_reversion':
            strategy = MeanReversionStrategy(
                window=args.short_window,
                enable_regime_detection=enable_regime,
                atr_period=args.atr_period,
                adx_period=args.adx_period
            )
            strategy_name = f"Mean Reversion (window={args.short_window})"
        elif args.strategy == 'mean_reversion_volume_compensated':
            strategy = MeanReversionVolumeCompensatedStrategy(
                window=args.short_window,
                enable_regime_detection=enable_regime,
                atr_period=args.atr_period,
                adx_period=args.adx_period
            )
            strategy_name = f"Mean Reversion Volume Compensated (window={args.short_window})"
        elif args.strategy == 'rsi_bollinger':
            strategy = RSIBollingerStrategy(
                enable_regime_detection=enable_regime,
                atr_period=args.atr_period,
                adx_period=args.adx_period
            )
            strategy_name = "RSI + Bollinger Bands"
        else:
            logging.error(f"Unknown strategy: {args.strategy}")
            return
        
        # Create backtester with day trading parameters
        backtester = Backtester(
            initial_capital=100.0,
            position_size=args.position_size,
            stop_loss=args.stop_loss
        )
        
        # Run backtest
        logging.info("Running backtest...")
        results = backtester.run(data, strategy)
        
        # Log results
        logging.info("Backtest completed!")
        logging.info(f"Total Return: {results['total_return']:.2%}")
        logging.info(f"Annualized Return: {results['annualized_return']:.2%}")
        logging.info(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        logging.info(f"Max Drawdown: {results['max_drawdown']:.2%}")
        logging.info(f"Volatility: {results['volatility']:.2%}")
        logging.info(f"Number of Trades: {results['num_trades']}")
        logging.info(f"Win Rate: {results['win_rate']:.2%}")
        logging.info(f"Profit Factor: {results['profit_factor']:.2f}")
        
        # Save results to file
        results_file = os.path.join(output_dir, 'results.txt')
        with open(results_file, 'w') as f:
            f.write(f"Backtest Results - {args.period.upper()} Market\n")
            f.write("=" * 50 + "\n")
            f.write(f"Period: {start_date} to {end_date}\n")
            f.write(f"Strategy: {strategy_name}\n")
            f.write(f"Min Crossover Strength: {args.min_crossover_strength}\n")
            f.write(f"Position Size: {args.position_size:.1%}\n")
            f.write(f"Stop Loss: {args.stop_loss:.1%}\n")
            f.write(f"Initial Capital: $100.00\n")
            f.write(f"Final Capital: ${results['portfolio']['total_value'].iloc[-1]:.2f}\n")
            f.write(f"Total Return: {results['total_return']:.2%}\n")
            f.write(f"Annualized Return: {results['annualized_return']:.2%}\n")
            f.write(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}\n")
            f.write(f"Max Drawdown: {results['max_drawdown']:.2%}\n")
            f.write(f"Volatility: {results['volatility']:.2%}\n")
            f.write(f"Number of Trades: {results['num_trades']}\n")
            f.write(f"Win Rate: {results['win_rate']:.2%}\n")
            f.write(f"Profit Factor: {results['profit_factor']:.2f}\n")
        
        # Create plots
        portfolio = results['portfolio']
        
        # Plot 1: Price and signals
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
        
        # Price chart with buy/sell signals
        ax1.plot(portfolio.index, portfolio['price'], label='BTC Price', alpha=0.7)
        
        # Plot buy signals
        buy_signals = portfolio[portfolio['signal'] == 1]
        if len(buy_signals) > 0:
            ax1.scatter(buy_signals.index, buy_signals['price'], 
                       color='green', marker='^', s=100, label='Buy Signal', alpha=0.8)
        
        # Plot sell signals
        sell_signals = portfolio[portfolio['signal'] == -1]
        if len(sell_signals) > 0:
            ax1.scatter(sell_signals.index, sell_signals['price'], 
                       color='red', marker='v', s=100, label='Sell Signal', alpha=0.8)
        
        ax1.set_title(f'BTC Price and Trading Signals - {args.period.upper()} Market')
        ax1.set_ylabel('Price (USD)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Portfolio value line (simple progression like BTC price)
        ax2.plot(portfolio.index, portfolio['total_value'], label='Portfolio Value', color='blue', linewidth=2)
        ax2.axhline(y=100, color='red', linestyle='--', alpha=0.7, label='Initial Capital')
        
        ax2.set_title('Portfolio Value Over Time')
        ax2.set_ylabel('Portfolio Value (USD)')
        ax2.set_xlabel('Date')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_file = os.path.join(output_dir, 'backtest_results.png')
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        logging.info(f"Saved plot for backtest results to: {plot_file}")
        
        # Plot 2: Market Regime Analysis (if enabled)
        if enable_regime and 'ATR' in data.columns and 'ADX' in data.columns:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            
            # ATR (Volatility)
            ax1.plot(data.index, data['ATR'], label='ATR', color='purple', alpha=0.7)
            ax1.set_title('Average True Range (Volatility)')
            ax1.set_ylabel('ATR')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # ADX (Trend Strength)
            ax2.plot(data.index, data['ADX'], label='ADX', color='orange', alpha=0.7)
            ax2.axhline(y=25, color='red', linestyle='--', alpha=0.7, label='Strong Trend (25)')
            ax2.axhline(y=20, color='yellow', linestyle='--', alpha=0.7, label='Weak Trend (20)')
            ax2.set_title('Average Directional Index (Trend Strength)')
            ax2.set_ylabel('ADX')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Volatility Regime
            regime_colors = {'high': 'red', 'medium': 'yellow', 'low': 'green'}
            for regime in ['high', 'medium', 'low']:
                regime_data = data[data['volatility_regime'] == regime]
                if len(regime_data) > 0:
                    ax3.scatter(regime_data.index, regime_data['Close'], 
                               c=regime_colors[regime], label=f'{regime.capitalize()} Volatility', 
                               alpha=0.6, s=10)
            ax3.set_title('Price by Volatility Regime')
            ax3.set_ylabel('Price (USD)')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # Trend Regime
            trend_colors = {'trending': 'blue', 'moderate': 'orange', 'ranging': 'gray'}
            for regime in ['trending', 'moderate', 'ranging']:
                regime_data = data[data['trend_regime'] == regime]
                if len(regime_data) > 0:
                    ax4.scatter(regime_data.index, regime_data['Close'], 
                               c=trend_colors[regime], label=f'{regime.capitalize()} Trend', 
                               alpha=0.6, s=10)
            ax4.set_title('Price by Trend Regime')
            ax4.set_ylabel('Price (USD)')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            regime_file = os.path.join(output_dir, 'market_regime_analysis.png')
            plt.savefig(regime_file, dpi=300, bbox_inches='tight')
            plt.close()
            logging.info(f"Saved plot for market regime analysis to: {regime_file}")
            
            # Log regime statistics
            if 'volatility_regime' in data.columns and 'trend_regime' in data.columns:
                vol_stats = data['volatility_regime'].value_counts()
                trend_stats = data['trend_regime'].value_counts()
                
                logging.info("Market Regime Analysis:")
                logging.info(f"Volatility Regimes: {dict(vol_stats)}")
                logging.info(f"Trend Regimes: {dict(trend_stats)}")
                
                # Save regime statistics to results file
                with open(results_file, 'a') as f:
                    f.write(f"\nMarket Regime Analysis:\n")
                    f.write(f"Volatility Regimes: {dict(vol_stats)}\n")
                    f.write(f"Trend Regimes: {dict(trend_stats)}\n")
        
        # Plot 3: Daily P&L distribution
        plt.figure(figsize=(12, 6))
        daily_pnl = portfolio['daily_pnl'].dropna()
        plt.hist(daily_pnl, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        plt.axvline(x=0, color='red', linestyle='--', alpha=0.7)
        plt.title('Daily P&L Distribution')
        plt.xlabel('Daily P&L (USD)')
        plt.ylabel('Frequency')
        plt.grid(True, alpha=0.3)
        
        pnl_file = os.path.join(output_dir, 'daily_pnl_distribution.png')
        plt.savefig(pnl_file, dpi=300, bbox_inches='tight')
        plt.close()
        logging.info(f"Saved plot for daily P&L distribution to: {pnl_file}")
        
        logging.info(f"Results saved to: {output_dir}")
        if enable_regime and 'ATR' in data.columns:
            logging.info(f"Plots saved as: {plot_file}, {regime_file}, {pnl_file}")
        else:
            logging.info(f"Plots saved as: {plot_file}, {pnl_file}")

if __name__ == "__main__":
    main()

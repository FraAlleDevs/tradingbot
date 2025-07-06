# Python Backtesting Framework

A Python-based backtesting framework for cryptocurrency trading strategies, optimized for minute-level day trading with multiple trades per day and daily profit reinvestment.

## Features

- **Minute-level data processing** for high-frequency trading analysis
- **Multiple trading strategies** (Moving Average, Mean Reversion, Volume-compensated variants)
- **Day trading optimization** with frequent signals and profit reinvestment
- **Risk management** with configurable stop-loss and position sizing
- **Performance metrics** including Sharpe ratio, max drawdown, win rate, and profit factor
- **Market period testing** with predefined bull, bear, crisis, recovery, and recent periods
- **Comprehensive logging** and visualization with detailed plots
- **Daily profit reinvestment** to compound gains over time

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run a backtest with default parameters on the recent market period:

```bash
python main.py
```

### Advanced Usage

Test different market periods and customize parameters:

```bash
# Test bull market with custom parameters
python main.py --period bull --short-window 15 --long-window 40 --position-size 0.9

# Test bear market with tighter stop-loss
python main.py --period bear --stop-loss 0.015 --min-crossover-strength 0.002

# Custom date range
python main.py --period custom --start-date 2023-06-01 --end-date 2023-08-31

# Test crisis period with conservative settings
python main.py --period crisis --position-size 0.6 --stop-loss 0.025
```

### Available Market Periods

- `bull` (2021): Bull market period for testing uptrend strategies
- `bear` (2022): Bear market period for testing downtrend strategies  
- `crisis` (2020-03 to 2020-06): COVID-19 crisis period for stress testing
- `recovery` (2020-07 to 2020-12): Post-crisis recovery period
- `recent` (2023): Recent market period (default)
- `custom`: Use with --start-date and --end-date for custom periods

### Parameters

- `--period`: Market period to test (default: recent)
- `--start-date`: Custom start date (YYYY-MM-DD format)
- `--end-date`: Custom end date (YYYY-MM-DD format)
- `--short-window`: Short moving average window (default: 20)
- `--long-window`: Long moving average window (default: 50)
- `--min-crossover-strength`: Minimum crossover strength for signals (default: 0.003)
- `--position-size`: Position size as fraction of capital (default: 0.8)
- `--stop-loss`: Stop loss percentage (default: 0.02)
- `--data-path`: Path to CSV data file (default: ../data/btc_usd_1min.csv)

## Day Trading Features

The framework is optimized for active day trading with the following features:

### High-Frequency Signals
- Reduced minimum crossover strength (0.003) for more frequent signals
- Short minimum holding period (1 minute) to allow rapid position changes
- Multiple trades per day to capture short-term price movements

### Aggressive Position Sizing
- Default 80% position size to maximize capital utilization
- Configurable position sizing for different risk tolerances
- Stop-loss protection to limit downside risk

### Profit Reinvestment
- Daily profit reinvestment to compound gains
- Capital grows over time as profits are added to available trading capital
- Optimized for long-term growth through compounding

### Risk Management
- Configurable stop-loss levels (default 2%)
- Position sizing controls to manage risk per trade
- Performance metrics to evaluate strategy effectiveness

## Output

The framework generates comprehensive output including:

1. **Console logging** with real-time progress and results
2. **Results file** (`results.txt`) with detailed performance metrics
3. **Log file** (`backtest.log`) with complete execution log
4. **Price and signals plot** showing BTC price with buy/sell markers
5. **Portfolio value chart** showing equity curve over time
6. **Daily P&L distribution** histogram for risk analysis

All output is saved to timestamped directories for easy organization and comparison.

## Performance Metrics

- **Total Return**: Overall percentage gain/loss
- **Annualized Return**: Return adjusted for time period
- **Sharpe Ratio**: Risk-adjusted return measure
- **Max Drawdown**: Largest peak-to-trough decline
- **Volatility**: Price variability measure
- **Number of Trades**: Total trading activity
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of gross profit to gross loss

## Data Format

The framework expects CSV data with the following columns:
- `timestamp`: Datetime index
- `Open`: Opening price
- `High`: High price
- `Low`: Low price
- `Close`: Closing price
- `Volume`: Trading volume

## Example Results

```
Backtest Results - RECENT Market
==================================================
Period: 2023-01-01 to 2023-12-31
Strategy: Moving Average (20/50)
Min Crossover Strength: 0.003
Position Size: 80.0%
Stop Loss: 2.0%
Initial Capital: $100.00
Final Capital: $156.78
Total Return: 56.78%
Annualized Return: 56.78%
Sharpe Ratio: 1.23
Max Drawdown: -8.45%
Volatility: 45.67%
Number of Trades: 1,247
Win Rate: 52.3%
Profit Factor: 1.15
```

## Contributing

To add new strategies, inherit from the `Strategy` base class and implement the `generate_signals` method. See existing strategies in the `strategies/` directory for examples.

## Environment Configuration (.env)

This project supports configuration via a `.env` file placed in the `python_backtest/` directory. The `.env` file allows you to customize paths and default parameters without changing the code.

### Example `.env` file:

```
# Output and Data Paths
RESULTS_DIR=python_backtest/results
DATA_PATH=./data/btcusd_1-min_data.csv

# Logging
LOG_LEVEL=INFO

# Default Backtest Parameters
DEFAULT_PERIOD=bull_2021
DEFAULT_POSITION_SIZE=0.8
DEFAULT_STOP_LOSS=0.02

# Plotting
PLOTS_DPI=300
PLOTS_FORMAT=png

# Timezone
TIMEZONE=UTC

# Data Loading
MAX_ROWS=0  # 0 means no limit

# Notifications (future use)
EMAIL_NOTIFICATIONS=

# Reproducibility
RANDOM_SEED=42
```

### Variable Descriptions
- `RESULTS_DIR`: Directory where backtest results and plots are saved.
- `DATA_PATH`: Path to the CSV data file to use for backtesting.
- `LOG_LEVEL`: Logging verbosity (e.g., INFO, DEBUG).
- `DEFAULT_PERIOD`: Default market period if not specified via CLI.
- `DEFAULT_POSITION_SIZE`: Default position size as a fraction of capital.
- `DEFAULT_STOP_LOSS`: Default stop loss percentage.
- `PLOTS_DPI`: DPI for saved plots.
- `PLOTS_FORMAT`: File format for plots (e.g., png, svg).
- `TIMEZONE`: Timezone for datetime handling.
- `MAX_ROWS`: Maximum number of rows to load from the data file (0 = no limit).
- `EMAIL_NOTIFICATIONS`: Email address for notifications (future feature).
- `RANDOM_SEED`: Random seed for reproducibility.

**To use the `.env` file, simply edit the values as needed. The code will automatically load these settings on startup.**

# Python Trading Strategy Backtester

This project provides a modular Python framework for backtesting and comparing multiple trading strategies on historical price data. It is designed for extensibility and clear analysis, allowing you to add new strategies and visualize their performance.

## Project Structure

```
python_backtest/
├── backtest/
│   └── backtester.py                # Core backtesting engine
├── strategies/
│   ├── base.py                      # Abstract base class for all strategies
│   ├── moving_average.py            # Moving Average strategy
│   ├── moving_average_volume_compensated.py # MA Volume Compensated strategy
│   ├── mean_reversion.py            # Mean Reversion strategy
│   └── mean_reversion_volume_compensated.py # Mean Reversion Volume Compensated
├── utils/
│   └── data_loader.py               # Data loading and summary utilities
├── main.py                          # Main script to run and compare strategies
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Setup

1. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Place your data file** (e.g., `btcusd_1-min_data.csv`) in the appropriate directory. Update the path in `main.py` if needed.

## Usage

Run the main script:
```bash
python main.py
```

- The script will load your data, select a period (e.g., January 2023), and run all implemented strategies.
- For each strategy, it will print the number of trades, total profit, and show a detailed plot with price, equity curve, and buy/sell markers.
- At the end, it will display a comparison plot of the equity curves for all strategies.

## Implemented Strategies

- **Moving Average:**
  - Buys when the short-term moving average crosses above the long-term, sells on the opposite crossover.
- **Moving Average Volume Compensated:**
  - Like Moving Average, but only acts when short-term volume is also above long-term volume (for buys) or below (for sells).
- **Mean Reversion:**
  - Buys when price crosses below its rolling mean, sells when it crosses above.
- **Mean Reversion Volume Compensated:**
  - Like Mean Reversion, but only acts when volume is above its rolling mean.

## How the Backtest Works

- **Initial Portfolio:** Starts with 100 units of cash.
- **Trade Logic:**
  - On a buy signal, invests all available cash into the asset.
  - On a sell signal, liquidates all holdings back to cash.
  - Holds position otherwise.
- **Equity Curve:**
  - Shows the value of your portfolio over time, relative to the starting capital (1.0 = break-even, 1.2 = +20%, 0.8 = -20%).
- **Trade Log:**
  - For each strategy, prints a summary of all trades (entry/exit times, prices, profit) and the total number of trades and profit.

## Customization

- **Change the backtest period:** Edit the `start_date` and `end_date` in `main.py`.
- **Tune strategy parameters:** Adjust window sizes in the strategy constructors in `main.py`.
- **Add new strategies:** Create a new class in `strategies/` inheriting from `Strategy` and add it to the `strategies` dict in `main.py`.

## Interpreting Results

- **Individual Plots:** For each strategy, see when trades occurred and how the portfolio value evolved.
- **Comparison Plot:** See which strategy performed best over the selected period.
- **Trade Log:** Review the number and quality of trades for each approach.

---

Feel free to experiment with different strategies, parameters, and time periods to find what works best for your data!

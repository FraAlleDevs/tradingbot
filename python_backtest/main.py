import os
import time
import pandas as pd
import matplotlib.pyplot as plt
import sys
from datetime import datetime
from utils.data_loader import load_data, print_data_summary, plot_price_volume
from strategies.moving_average import MovingAverageStrategy
from strategies.moving_average_volume_compensated import MovingAverageVolumeCompensatedStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.mean_reversion_volume_compensated import MeanReversionVolumeCompensatedStrategy
from backtest.backtester import Backtester

if __name__ == "__main__":
    # Create output directory inside python_backtest/results/
    results_base_dir = "python_backtest/results"
    os.makedirs(results_base_dir, exist_ok=True)
    output_dir = f"{results_base_dir}/results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)

    # Redirect all output to a log file
    log_file = open(f"{output_dir}/backtest_log.txt", "w")
    sys.stdout = log_file

    t0 = time.time()
    data = load_data("python_backtest/data/btcusd_1-min_data.csv")
    print(f"Data loaded in {time.time() - t0:.2f} seconds.")

    t1 = time.time()
    # print_data_summary(data)
    print(f"Data summary printed in {time.time() - t1:.2f} seconds.")

    t2 = time.time()
    # plot_price_volume(data, n=1000, last=True)  # Plot last 1000 rows for inspection
    print(f"Price/volume plot in {time.time() - t2:.2f} seconds.")

    # Set the backtest period to January 2023
    start_date = pd.Timestamp("2023-01-01")
    end_date = pd.Timestamp("2023-01-31 23:59:59")
    period_data = data.loc[start_date:end_date]
    print(f"Using period: {start_date.date()} to {end_date.date()} ({len(period_data)} rows)")

    t3 = time.time()
    strategies = {
        'Moving Average': MovingAverageStrategy(short_window=20, long_window=50),
        'MA Volume Compensated': MovingAverageVolumeCompensatedStrategy(short_window=20, long_window=50),
        'Mean Reversion': MeanReversionStrategy(window=20),
        'Mean Reversion Volume Compensated': MeanReversionVolumeCompensatedStrategy(window=20)
    }
    results = {}
    for name, strategy in strategies.items():
        print(f"\nRunning {name} strategy...")
        backtester = Backtester(period_data, strategy)
        equity_curve = backtester.run()
        trades = backtester.get_trade_log()
        print(f"{name} - Total trades: {len(trades)}")
        total_profit = sum(trade['profit'] for trade in trades)
        print(f"{name} - Total profit: {total_profit:.2f}")
        results[name] = (equity_curve, trades)
        # Save detailed plot for this strategy
        plot_filename = f"{output_dir}/{name.replace(' ', '_').replace('/', '_')}_plot.png"
        backtester.plot(save_path=plot_filename)
        print(f"Plot saved to: {plot_filename}")
    print(f"Backtests run in {time.time() - t3:.2f} seconds.")

    # Save comparison plot
    plt.figure(figsize=(14, 7))
    for name, (equity_curve, _) in results.items():
        plt.plot(equity_curve.index, equity_curve, label=f'Equity: {name}', linewidth=2)
    plt.ylabel('Equity (relative to start)')
    plt.title('Equity Curve Comparison')
    plt.legend()
    plt.grid(True)
    comparison_filename = f"{output_dir}/comparison_plot.png"
    plt.savefig(comparison_filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Comparison plot saved to: {comparison_filename}")

    print(f"\nTotal script time: {time.time() - t0:.2f} seconds.")

    # Close log file and restore stdout
    log_file.close()
    sys.stdout = sys.__stdout__
    print(f"Results saved to: {output_dir}")
    print(f"Log file: {output_dir}/backtest_log.txt")
    print(f"Individual strategy plots: {output_dir}/*_plot.png")
    print(f"Comparison plot: {output_dir}/comparison_plot.png")

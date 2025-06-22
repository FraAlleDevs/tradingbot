import pandas as pd
import matplotlib.pyplot as plt

class Backtester:
    def __init__(self, data: pd.DataFrame, strategy, initial_cash: float = 100.0):
        self.data = data
        self.strategy = strategy
        self.signals = None
        self.equity_curve = None
        self.initial_cash = initial_cash
        self.portfolio_value = None

    def run(self):
        self.signals = self.strategy.generate_signals(self.data)
        # Portfolio simulation
        cash = self.initial_cash
        holdings = 0.0
        portfolio_values = []
        position = 0
        entry_price = None
        for i, (signal, price) in enumerate(zip(self.signals, self.data['Close'])):
            if position == 0 and signal == 1:
                # Buy: invest all cash
                holdings = cash / price
                cash = 0.0
                entry_price = price
                position = 1
            elif position == 1 and signal == -1:
                # Sell: liquidate all holdings
                cash = holdings * price
                holdings = 0.0
                position = 0
            # Portfolio value at each step
            portfolio_values.append(cash + holdings * price)
        self.portfolio_value = pd.Series(portfolio_values, index=self.data.index)
        self.equity_curve = self.portfolio_value / self.initial_cash
        return self.equity_curve

    def plot(self):
        fig, ax1 = plt.subplots(figsize=(14, 7))
        ax1.plot(self.data.index, self.data['Close'], label='Price', color='blue', alpha=0.5)
        ax1.set_ylabel('Price')
        ax2 = ax1.twinx()
        ax2.plot(self.equity_curve.index, self.equity_curve, label='Equity Curve', color='green')
        ax2.set_ylabel('Equity')
        # Plot buy/sell signals
        buy_signals = self.signals[self.signals == 1]
        sell_signals = self.signals[self.signals == -1]
        ax1.plot(buy_signals.index, self.data.loc[buy_signals.index, 'Close'], '^', markersize=8, color='g', label='Buy')
        ax1.plot(sell_signals.index, self.data.loc[sell_signals.index, 'Close'], 'v', markersize=8, color='r', label='Sell')
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')
        plt.title('Price, Equity Curve, and Trade Signals')
        plt.show()

    def get_trade_log(self):
        trades = []
        position = 0
        entry_price = None
        entry_time = None
        for i, (signal, price) in enumerate(zip(self.signals, self.data['Close'])):
            if position == 0 and signal == 1:
                # Buy
                entry_price = price
                entry_time = self.data.index[i]
                position = 1
            elif position == 1 and signal == -1:
                # Sell
                exit_price = price
                exit_time = self.data.index[i]
                profit = exit_price - entry_price
                trades.append({'entry_time': entry_time, 'entry_price': entry_price,
                               'exit_time': exit_time, 'exit_price': exit_price,
                               'profit': profit})
                position = 0
        return trades

import pandas as pd
from .base import Strategy

class MovingAverageStrategy(Strategy):
    def __init__(self, short_window: int = 20, long_window: int = 50):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        short_ma = data['Close'].rolling(window=self.short_window, min_periods=1).mean()
        long_ma = data['Close'].rolling(window=self.long_window, min_periods=1).mean()
        signal = pd.Series(0, index=data.index)
        # Buy signal: short MA crosses above long MA
        signal[(short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))] = 1
        # Sell signal: short MA crosses below long MA
        signal[(short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))] = -1
        # Hold otherwise (remains 0)
        return signal

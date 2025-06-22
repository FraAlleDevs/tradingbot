import pandas as pd
from .base import Strategy

class MovingAverageVolumeCompensatedStrategy(Strategy):
    def __init__(self, short_window: int = 20, long_window: int = 50):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        short_ma = data['Close'].rolling(window=self.short_window, min_periods=1).mean()
        long_ma = data['Close'].rolling(window=self.long_window, min_periods=1).mean()
        short_vol = data['Volume'].rolling(window=self.short_window, min_periods=1).mean()
        long_vol = data['Volume'].rolling(window=self.long_window, min_periods=1).mean()
        signal = pd.Series(0, index=data.index)
        # Buy: short MA > long MA and short Vol > long Vol (cross above)
        buy = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1)) & (short_vol > long_vol)
        # Sell: short MA < long MA and short Vol < long Vol (cross below)
        sell = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1)) & (short_vol < long_vol)
        signal[buy] = 1
        signal[sell] = -1
        return signal 
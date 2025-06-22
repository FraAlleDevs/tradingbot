import pandas as pd
from .base import Strategy

class MeanReversionVolumeCompensatedStrategy(Strategy):
    def __init__(self, window: int = 20):
        self.window = window

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        mean_price = data['Close'].rolling(window=self.window, min_periods=1).mean()
        mean_vol = data['Volume'].rolling(window=self.window, min_periods=1).mean()
        signal = pd.Series(0, index=data.index)
        # Buy when price crosses below mean and volume above mean
        buy = (data['Close'] < mean_price) & (data['Close'].shift(1) >= mean_price.shift(1)) & (data['Volume'] > mean_vol)
        # Sell when price crosses above mean and volume above mean
        sell = (data['Close'] > mean_price) & (data['Close'].shift(1) <= mean_price.shift(1)) & (data['Volume'] > mean_vol)
        signal[buy] = 1
        signal[sell] = -1
        return signal 
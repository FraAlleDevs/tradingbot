import pandas as pd
from .base import Strategy

class MeanReversionStrategy(Strategy):
    def __init__(self, window: int = 20):
        self.window = window

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        mean_price = data['Close'].rolling(window=self.window, min_periods=1).mean()
        signal = pd.Series(0, index=data.index)
        # Buy when price crosses below mean, sell when crosses above
        signal[(data['Close'] < mean_price) & (data['Close'].shift(1) >= mean_price.shift(1))] = 1
        signal[(data['Close'] > mean_price) & (data['Close'].shift(1) <= mean_price.shift(1))] = -1
        return signal 
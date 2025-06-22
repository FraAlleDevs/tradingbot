from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Given a DataFrame of price data, return a Series of trading signals:
        +1 for buy, -1 for sell, 0 for hold.
        """
        pass

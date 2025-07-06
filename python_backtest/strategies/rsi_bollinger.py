import pandas as pd
import numpy as np
from strategies.base import Strategy

class RSIBollingerStrategy(Strategy):
    """
    RSI + Bollinger Bands Strategy for Day Trading
    
    This is a proven day trading strategy that combines:
    1. RSI (Relative Strength Index) for momentum confirmation
    2. Bollinger Bands for volatility-based entry/exit signals
    3. Volume confirmation for signal strength
    
    Strategy Logic:
    - Buy: Price touches lower Bollinger Band + RSI oversold (< 30) + Volume spike
    - Sell: Price touches upper Bollinger Band + RSI overbought (> 70) + Volume spike
    - Exit: RSI returns to neutral (40-60) or price crosses middle band
    
    Parameters:
        rsi_period (int): Period for RSI calculation (default: 14)
        bb_period (int): Period for Bollinger Bands (default: 20)
        bb_std (float): Standard deviation multiplier for BB (default: 2.0)
        rsi_oversold (float): RSI level considered oversold (default: 30)
        rsi_overbought (float): RSI level considered overbought (default: 70)
        volume_threshold (float): Volume spike threshold (default: 1.5)
        enable_regime_detection (bool): Enable market regime detection (default: True)
        atr_period (int): Period for ATR calculation (default: 14)
        adx_period (int): Period for ADX calculation (default: 14)
    """
    
    def __init__(self, rsi_period: int = 14, bb_period: int = 20, bb_std: float = 2.0,
                 rsi_oversold: float = 25, rsi_overbought: float = 75, 
                 volume_threshold: float = 2.0, enable_regime_detection: bool = True,
                 atr_period: int = 14, adx_period: int = 14):
        super().__init__(enable_regime_detection, atr_period, adx_period)
        self.rsi_period = rsi_period
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.volume_threshold = volume_threshold

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate buy/sell signals based on RSI + Bollinger Bands strategy.
        
        Args:
            data (pd.DataFrame): Price data with 'Close', 'Volume', 'High', 'Low' columns
            
        Returns:
            pd.Series: Signal series with values:
                - 1: Buy signal (RSI oversold + BB lower touch + Volume spike)
                - -1: Sell signal (RSI overbought + BB upper touch + Volume spike)
                - 0: No signal
        """
        # Calculate market regime indicators
        if self.enable_regime_detection:
            atr = self._calculate_atr(data, self.atr_period)
            adx = self._calculate_adx(data, self.adx_period)
            
            # Store regime information for potential use in backtester
            data = data.copy()
            data['ATR'] = atr
            data['ADX'] = adx
            data['volatility_regime'] = self._classify_volatility_regime(atr)
            data['trend_regime'] = self._classify_trend_regime(adx)
        
        # Get adaptive parameters based on current market regime
        base_params = {
            'rsi_period': self.rsi_period,
            'bb_period': self.bb_period,
            'bb_std': self.bb_std,
            'rsi_oversold': self.rsi_oversold,
            'rsi_overbought': self.rsi_overbought,
            'volume_threshold': self.volume_threshold
        }
        
        adapted_params = self._get_adaptive_parameters(data, base_params)
        
        # Calculate RSI
        rsi = self._calculate_rsi(data['Close'], adapted_params['rsi_period'])
        
        # Calculate Bollinger Bands
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
            data['Close'], adapted_params['bb_period'], adapted_params['bb_std']
        )
        
        # Calculate volume moving average for spike detection
        volume_ma = data['Volume'].rolling(window=adapted_params['bb_period'], min_periods=1).mean()
        volume_spike = data['Volume'] > (volume_ma * adapted_params['volume_threshold'])
        
        # Generate signals
        signal = pd.Series(0, index=data.index)
        
        # Buy signal: RSI oversold + Price touches lower BB + Volume spike
        buy_condition = (
            (rsi < adapted_params['rsi_oversold']) & 
            (data['Close'] <= bb_lower * 1.001) &  # Allow small tolerance
            volume_spike
        )
        
        # Sell signal: RSI overbought + Price touches upper BB + Volume spike
        sell_condition = (
            (rsi > adapted_params['rsi_overbought']) & 
            (data['Close'] >= bb_upper * 0.999) &  # Allow small tolerance
            volume_spike
        )
        
        # Exit conditions: RSI returns to neutral or price crosses middle band
        exit_long = (rsi > 65) | (data['Close'] < bb_middle)
        exit_short = (rsi < 35) | (data['Close'] > bb_middle)
        
        # Apply signals
        signal[buy_condition] = 1
        signal[sell_condition] = -1
        
        # Apply exit signals (only if we have a position)
        position = 0
        for i in range(len(signal)):
            if signal.iloc[i] == 1:
                position = 1
            elif signal.iloc[i] == -1:
                position = -1
            elif position == 1 and exit_long.iloc[i]:
                signal.iloc[i] = -1  # Exit long position
                position = 0
            elif position == -1 and exit_short.iloc[i]:
                signal.iloc[i] = 1   # Exit short position
                position = 0
        
        return signal
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).
        
        Args:
            prices (pd.Series): Price series
            period (int): Period for RSI calculation
            
        Returns:
            pd.Series: RSI values (0-100)
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int, std_mult: float) -> tuple:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices (pd.Series): Price series
            period (int): Period for moving average
            std_mult (float): Standard deviation multiplier
            
        Returns:
            tuple: (upper_band, middle_band, lower_band)
        """
        middle = prices.rolling(window=period, min_periods=1).mean()
        std = prices.rolling(window=period, min_periods=1).std()
        
        upper = middle + (std * std_mult)
        lower = middle - (std * std_mult)
        
        return upper, middle, lower
    
    def _get_adaptive_parameters(self, data: pd.DataFrame, base_params: dict) -> dict:
        """
        Get adaptive parameters based on current market regime for RSI + Bollinger Bands.
        
        Args:
            data (pd.DataFrame): Price data with regime information
            base_params (dict): Base parameters for the strategy
            
        Returns:
            dict: Adapted parameters based on market conditions
        """
        if not self.enable_regime_detection:
            return base_params
        
        # Get current regime (use most recent values)
        if 'volatility_regime' in data.columns and 'trend_regime' in data.columns:
            current_volatility = data['volatility_regime'].iloc[-1]
            current_trend = data['trend_regime'].iloc[-1]
            
            adapted_params = base_params.copy()
            
            # Volatility-based adaptations
            if current_volatility == 'high':
                # High volatility: more conservative RSI levels, wider BB bands
                adapted_params['rsi_oversold'] = base_params['rsi_oversold'] - 5  # 25
                adapted_params['rsi_overbought'] = base_params['rsi_overbought'] + 5  # 75
                adapted_params['bb_std'] = base_params['bb_std'] * 1.2
                adapted_params['volume_threshold'] = base_params['volume_threshold'] * 1.3
            elif current_volatility == 'low':
                # Low volatility: more sensitive RSI levels, tighter BB bands
                adapted_params['rsi_oversold'] = base_params['rsi_oversold'] + 5  # 35
                adapted_params['rsi_overbought'] = base_params['rsi_overbought'] - 5  # 65
                adapted_params['bb_std'] = base_params['bb_std'] * 0.8
                adapted_params['volume_threshold'] = base_params['volume_threshold'] * 0.8
            
            # Trend-based adaptations
            if current_trend == 'trending':
                # Strong trend: use trend-following logic, less mean reversion
                adapted_params['rsi_oversold'] = base_params['rsi_oversold'] - 10  # 20
                adapted_params['rsi_overbought'] = base_params['rsi_overbought'] + 10  # 80
                adapted_params['bb_std'] = base_params['bb_std'] * 1.5
            elif current_trend == 'ranging':
                # Ranging market: optimal for mean reversion, use standard settings
                # Keep adapted parameters as is
                pass
            
            return adapted_params
        
        return base_params
    
    def _calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range (ATR) for volatility measurement."""
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period, min_periods=1).mean()
        
        return atr
    
    def _calculate_adx(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average Directional Index (ADX) for trend strength measurement."""
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        high_diff = high - high.shift(1)
        low_diff = low.shift(1) - low
        
        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        tr_smooth = true_range.rolling(window=period, min_periods=1).mean()
        plus_dm_smooth = pd.Series(plus_dm, index=data.index).rolling(window=period, min_periods=1).mean()
        minus_dm_smooth = pd.Series(minus_dm, index=data.index).rolling(window=period, min_periods=1).mean()
        
        plus_di = 100 * (plus_dm_smooth / tr_smooth)
        minus_di = 100 * (minus_dm_smooth / tr_smooth)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period, min_periods=1).mean()
        
        return adx
    
    def _classify_volatility_regime(self, atr: pd.Series) -> pd.Series:
        """Classify volatility regime based on ATR values."""
        high_threshold = atr.rolling(window=100, min_periods=1).quantile(0.75)
        low_threshold = atr.rolling(window=100, min_periods=1).quantile(0.25)
        
        regime = pd.Series('medium', index=atr.index)
        regime[atr > high_threshold] = 'high'
        regime[atr < low_threshold] = 'low'
        
        return regime
    
    def _classify_trend_regime(self, adx: pd.Series) -> pd.Series:
        """Classify trend regime based on ADX values."""
        regime = pd.Series('ranging', index=adx.index)
        regime[adx > 25] = 'trending'
        
        return regime 
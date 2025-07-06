import pandas as pd
import numpy as np
from strategies.base import Strategy

class MovingAverageStrategy(Strategy):
    """
    Moving Average Crossover Strategy with Adaptive Parameters
    
    This strategy generates buy/sell signals based on the crossover of two moving averages.
    It includes market regime detection and automatically adapts parameters based on
    volatility and trend conditions.
    
    Parameters:
        short_window (int): Period for short-term moving average (default: 20)
            - Lower values = more responsive to price changes, more signals
            - Higher values = smoother signals, fewer false positives
            - Typical range: 5-50 minutes for day trading
            
        long_window (int): Period for long-term moving average (default: 50)
            - Lower values = faster trend detection, more signals
            - Higher values = stronger trend confirmation, fewer signals
            - Should be > short_window, typical range: 20-200 minutes
            
        min_crossover_strength (float): Minimum strength required for signal (default: 0.003)
            - Lower values = more signals, potential for noise
            - Higher values = stronger signals, fewer false positives
            - Range: 0.001-0.01 (0.1%-1% price difference)
            
        min_holding_period (int): Minimum periods to hold position before allowing reversal (default: 0)
            - 0 = No restriction, exit immediately on new signals (recommended for day trading)
            - Higher values = prevent whipsaw trading, but may hold bad trades longer
            - Range: 0-60 minutes (0-60 for minute data)
            - Set to 0 for maximum responsiveness to market changes
            
        enable_regime_detection (bool): Enable market regime detection (default: True)
            - True = Adapt strategy based on volatility and trend conditions
            - False = Use fixed parameters regardless of market conditions
            
        atr_period (int): Period for ATR calculation (default: 14)
            - Used to measure volatility and adjust stop-losses
            - Lower values = more responsive to recent volatility
            - Higher values = smoother volatility measure
            
        adx_period (int): Period for ADX calculation (default: 14)
            - Used to measure trend strength
            - ADX > 25 = strong trend, ADX < 20 = weak trend/ranging
    """
    
    def __init__(self, short_window: int = 20, long_window: int = 50, 
                 min_crossover_strength: float = 0.001, min_holding_period: int = 0,
                 enable_regime_detection: bool = True, atr_period: int = 14, adx_period: int = 14):
        super().__init__(enable_regime_detection, atr_period, adx_period)
        self.short_window = short_window
        self.long_window = long_window
        self.min_crossover_strength = min_crossover_strength
        self.min_holding_period = min_holding_period

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate buy/sell signals based on moving average crossovers with adaptive parameters.
        
        Args:
            data (pd.DataFrame): Price data with 'Close', 'High', 'Low' columns
            
        Returns:
            pd.Series: Signal series with values:
                - 1: Buy signal (short MA crosses above long MA)
                - -1: Sell signal (short MA crosses below long MA)
                - 0: No signal
                
        Strategy Logic:
            1. Calculate market regime indicators (ATR, ADX)
            2. Adapt parameters based on current market conditions
            3. Calculate short and long moving averages
            4. Detect crossovers with minimum strength requirement
            5. Apply optional holding period filter (if min_holding_period > 0)
            6. Return filtered signals
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
            'short_window': self.short_window,
            'long_window': self.long_window,
            'min_crossover_strength': self.min_crossover_strength,
            'min_holding_period': self.min_holding_period
        }
        
        adapted_params = self._get_adaptive_parameters(data, base_params)
        
        # Use adapted parameters for signal generation
        short_ma = data['Close'].rolling(window=adapted_params['short_window'], min_periods=1).mean()
        long_ma = data['Close'].rolling(window=adapted_params['long_window'], min_periods=1).mean()
        signal = pd.Series(0, index=data.index)
        
        # Calculate crossover strength (percentage difference between MAs)
        crossover_strength = abs(short_ma - long_ma) / long_ma
        
        # Buy signal: short MA above long MA with minimum strength (trend-following)
        buy_condition = (short_ma > long_ma) & (crossover_strength > adapted_params['min_crossover_strength'])
        # Sell signal: short MA below long MA with minimum strength (trend-following)
        sell_condition = (short_ma < long_ma) & (crossover_strength > adapted_params['min_crossover_strength'])
        
        signal[buy_condition] = 1
        signal[sell_condition] = -1
        
        # Apply minimum holding period only if specified (default: 0 = no restriction)
        if adapted_params['min_holding_period'] > 0:
            signal = self._apply_min_holding_period(signal, adapted_params['min_holding_period'])
        
        return signal
    
    def _get_adaptive_parameters(self, data: pd.DataFrame, base_params: dict) -> dict:
        """
        Get adaptive parameters based on current market regime for Moving Average strategy.
        
        Args:
            data (pd.DataFrame): Price data with regime information
            base_params (dict): Base parameters for the strategy
            
        Returns:
            dict: Adapted parameters based on market conditions
            
        Adaptation Logic:
            - High Volatility: Shorter MA windows, higher crossover strength, longer holding period
            - Low Volatility: Longer MA windows, lower crossover strength, shorter holding period
            - Strong Trend: Longer MA windows, let profits run
            - Ranging Market: Shorter MA windows, take profits quickly
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
                # High volatility: shorter windows for faster response, higher strength threshold
                adapted_params['short_window'] = max(int(base_params['short_window'] * 0.7), 10)
                adapted_params['long_window'] = max(int(base_params['long_window'] * 0.8), 20)
                adapted_params['min_crossover_strength'] = base_params['min_crossover_strength'] * 1.5
                adapted_params['min_holding_period'] = max(base_params['min_holding_period'], 3)
            elif current_volatility == 'low':
                # Low volatility: longer windows for smoother signals, lower strength threshold
                adapted_params['short_window'] = min(int(base_params['short_window'] * 1.3), 40)
                adapted_params['long_window'] = min(int(base_params['long_window'] * 1.2), 80)
                adapted_params['min_crossover_strength'] = base_params['min_crossover_strength'] * 0.7
                adapted_params['min_holding_period'] = base_params['min_holding_period']
            
            # Trend-based adaptations
            if current_trend == 'trending':
                # Strong trend: longer windows to follow trend, longer holding period
                adapted_params['short_window'] = min(int(adapted_params['short_window'] * 1.2), 30)
                adapted_params['long_window'] = min(int(adapted_params['long_window'] * 1.3), 100)
                adapted_params['min_holding_period'] = max(adapted_params['min_holding_period'], 5)
            elif current_trend == 'ranging':
                # Ranging market: shorter windows for quick reversals, shorter holding period
                adapted_params['short_window'] = max(int(adapted_params['short_window'] * 0.8), 10)
                adapted_params['long_window'] = max(int(adapted_params['long_window'] * 0.7), 30)
                adapted_params['min_holding_period'] = base_params['min_holding_period']
            
            return adapted_params
        
        return base_params
    
    def _calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """
        Calculate Average True Range (ATR) for volatility measurement.
        
        Args:
            data (pd.DataFrame): Price data with 'High', 'Low', 'Close' columns
            period (int): Period for ATR calculation
            
        Returns:
            pd.Series: ATR values
            
        ATR measures volatility by considering:
        - High-Low range
        - High-Previous Close range
        - Low-Previous Close range
        """
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR as rolling average of True Range
        atr = true_range.rolling(window=period, min_periods=1).mean()
        
        return atr
    
    def _calculate_adx(self, data: pd.DataFrame, period: int) -> pd.Series:
        """
        Calculate Average Directional Index (ADX) for trend strength measurement.
        
        Args:
            data (pd.DataFrame): Price data with 'High', 'Low', 'Close' columns
            period (int): Period for ADX calculation
            
        Returns:
            pd.Series: ADX values
            
        ADX measures trend strength:
        - ADX > 25: Strong trend
        - ADX < 20: Weak trend or ranging market
        - ADX 20-25: Moderate trend
        """
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        # Calculate +DM and -DM
        high_diff = high - high.shift(1)
        low_diff = low.shift(1) - low
        
        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
        
        # Calculate True Range (same as ATR)
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate smoothed values
        tr_smooth = true_range.rolling(window=period, min_periods=1).mean()
        plus_dm_smooth = pd.Series(plus_dm, index=data.index).rolling(window=period, min_periods=1).mean()
        minus_dm_smooth = pd.Series(minus_dm, index=data.index).rolling(window=period, min_periods=1).mean()
        
        # Calculate +DI and -DI
        plus_di = 100 * (plus_dm_smooth / tr_smooth)
        minus_di = 100 * (minus_dm_smooth / tr_smooth)
        
        # Calculate DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period, min_periods=1).mean()
        
        return adx
    
    def _classify_volatility_regime(self, atr: pd.Series) -> pd.Series:
        """
        Classify volatility regime based on ATR values.
        
        Args:
            atr (pd.Series): ATR values
            
        Returns:
            pd.Series: Volatility regime classification
                - 'high': High volatility (ATR > 75th percentile)
                - 'medium': Medium volatility (ATR between 25th and 75th percentile)
                - 'low': Low volatility (ATR < 25th percentile)
        """
        # Use rolling percentiles to adapt to changing market conditions
        high_threshold = atr.rolling(window=100, min_periods=1).quantile(0.75)
        low_threshold = atr.rolling(window=100, min_periods=1).quantile(0.25)
        
        regime = pd.Series('medium', index=atr.index)
        regime[atr > high_threshold] = 'high'
        regime[atr < low_threshold] = 'low'
        
        return regime
    
    def _classify_trend_regime(self, adx: pd.Series) -> pd.Series:
        """
        Classify trend regime based on ADX values.
        
        Args:
            adx (pd.Series): ADX values
            
        Returns:
            pd.Series: Trend regime classification
                - 'trending': Strong trend (ADX > 25)
                - 'ranging': Weak trend or ranging (ADX < 20)
                - 'moderate': Moderate trend (ADX 20-25)
        """
        regime = pd.Series('moderate', index=adx.index)
        regime[adx > 25] = 'trending'
        regime[adx < 20] = 'ranging'
        
        return regime
    
    def _apply_min_holding_period(self, signal: pd.Series, min_periods: int) -> pd.Series:
        """
        Apply minimum holding period to prevent rapid position changes.
        
        Args:
            signal (pd.Series): Original signal series
            min_periods (int): Minimum periods to hold a position before allowing reversal
                - Lower values = more frequent trading, higher transaction costs
                - Higher values = fewer trades, potential missed opportunities
                - For minute data: 5-30 minutes typical for day trading
                
        Returns:
            pd.Series: Filtered signal series with holding period restrictions
            
        Logic:
            - Once a position is entered, ignore opposite signals for min_periods
            - After min_periods, allow position reversal
            - This prevents whipsaw trading and reduces transaction costs
            - Note: This method is only called if min_holding_period > 0
        """
        filtered_signal = signal.copy()
        position = 0  # 0: no position, 1: long, -1: short
        position_start = 0
        
        for i in range(len(signal)):
            if signal.iloc[i] != 0:  # New signal detected
                if position == 0:  # No current position, can enter
                    position = signal.iloc[i]
                    position_start = i
                elif position != signal.iloc[i]:  # Opposite signal (potential reversal)
                    if i - position_start >= min_periods:  # Minimum holding period met
                        position = signal.iloc[i]
                        position_start = i
                    else:  # Ignore signal, maintain current position
                        filtered_signal.iloc[i] = 0
                else:  # Same signal, ignore (already in position)
                    filtered_signal.iloc[i] = 0
        
        return filtered_signal

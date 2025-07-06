import pandas as pd
from strategies.base import Strategy

class MovingAverageVolumeCompensatedStrategy(Strategy):
    """
    Moving Average Volume Compensated Strategy with Adaptive Parameters
    
    This strategy generates buy/sell signals based on moving average crossovers
    with volume confirmation. It includes market regime detection and automatically
    adapts parameters based on volatility and trend conditions.
    
    Parameters:
        short_window (int): Period for short-term moving average (default: 20)
        long_window (int): Period for long-term moving average (default: 50)
        min_crossover_strength (float): Minimum strength required for signal (default: 0.01)
        enable_regime_detection (bool): Enable market regime detection (default: True)
        atr_period (int): Period for ATR calculation (default: 14)
        adx_period (int): Period for ADX calculation (default: 14)
    """
    
    def __init__(self, short_window: int = 20, long_window: int = 50, 
                 min_crossover_strength: float = 0.001, enable_regime_detection: bool = True,
                 atr_period: int = 14, adx_period: int = 14):
        super().__init__(enable_regime_detection, atr_period, adx_period)
        self.short_window = short_window
        self.long_window = long_window
        self.min_crossover_strength = min_crossover_strength

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate buy/sell signals based on moving average crossovers with volume confirmation.
        
        Args:
            data (pd.DataFrame): Price data with 'Close', 'Volume', 'High', 'Low' columns
            
        Returns:
            pd.Series: Signal series with values:
                - 1: Buy signal (MA crossover + volume confirmation)
                - -1: Sell signal (MA crossover + volume confirmation)
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
            'short_window': self.short_window,
            'long_window': self.long_window,
            'min_crossover_strength': self.min_crossover_strength
        }
        
        adapted_params = self._get_adaptive_parameters(data, base_params)
        
        # Calculate moving averages using adapted parameters
        short_ma = data['Close'].rolling(window=adapted_params['short_window'], min_periods=1).mean()
        long_ma = data['Close'].rolling(window=adapted_params['long_window'], min_periods=1).mean()
        short_vol = data['Volume'].rolling(window=adapted_params['short_window'], min_periods=1).mean()
        long_vol = data['Volume'].rolling(window=adapted_params['long_window'], min_periods=1).mean()
        
        # Calculate crossover strength
        crossover_strength = abs(short_ma - long_ma) / long_ma
        
        signal = pd.Series(0, index=data.index)
        
        # Buy: short MA > long MA and short Vol > long Vol with minimum strength (trend-following)
        buy = (short_ma > long_ma) & (short_vol > long_vol) & (crossover_strength > adapted_params['min_crossover_strength'])
        # Sell: short MA < long MA and short Vol < long Vol with minimum strength (trend-following)
        sell = (short_ma < long_ma) & (short_vol < long_vol) & (crossover_strength > adapted_params['min_crossover_strength'])
        
        signal[buy] = 1
        signal[sell] = -1
        
        return signal
    
    def _get_adaptive_parameters(self, data: pd.DataFrame, base_params: dict) -> dict:
        """
        Get adaptive parameters based on current market regime for Volume Compensated strategy.
        
        Args:
            data (pd.DataFrame): Price data with regime information
            base_params (dict): Base parameters for the strategy
            
        Returns:
            dict: Adapted parameters based on market conditions
            
        Adaptation Logic:
            - High Volatility: Shorter windows, higher crossover strength
            - Low Volatility: Longer windows, lower crossover strength
            - Strong Trend: Longer windows to follow trend
            - Ranging Market: Shorter windows for quick reversals
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
            elif current_volatility == 'low':
                # Low volatility: longer windows for smoother signals, lower strength threshold
                adapted_params['short_window'] = min(int(base_params['short_window'] * 1.3), 40)
                adapted_params['long_window'] = min(int(base_params['long_window'] * 1.2), 80)
                adapted_params['min_crossover_strength'] = base_params['min_crossover_strength'] * 0.7
            
            # Trend-based adaptations
            if current_trend == 'trending':
                # Strong trend: longer windows to follow trend
                adapted_params['short_window'] = min(int(adapted_params['short_window'] * 1.2), 30)
                adapted_params['long_window'] = min(int(adapted_params['long_window'] * 1.3), 100)
            elif current_trend == 'ranging':
                # Ranging market: shorter windows for quick reversals
                adapted_params['short_window'] = max(int(adapted_params['short_window'] * 0.8), 10)
                adapted_params['long_window'] = max(int(adapted_params['long_window'] * 0.7), 30)
            
            return adapted_params
        
        return base_params
    
    def _apply_min_holding_period(self, signal: pd.Series, min_periods: int) -> pd.Series:
        """Apply minimum holding period to prevent rapid trading"""
        filtered_signal = signal.copy()
        position = 0
        position_start = 0
        
        for i in range(len(signal)):
            if signal.iloc[i] != 0:  # New signal
                if position == 0:  # No position, can enter
                    position = signal.iloc[i]
                    position_start = i
                elif position != signal.iloc[i]:  # Opposite signal
                    if i - position_start >= min_periods:  # Minimum holding period met
                        position = signal.iloc[i]
                        position_start = i
                    else:  # Ignore signal, maintain current position
                        filtered_signal.iloc[i] = 0
                # If same signal, ignore (already in position)
                else:
                    filtered_signal.iloc[i] = 0
        
        return filtered_signal 
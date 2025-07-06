import pandas as pd
from strategies.base import Strategy

class MeanReversionStrategy(Strategy):
    """
    Mean Reversion Strategy with Adaptive Parameters
    
    This strategy generates buy/sell signals based on price deviations from its moving average.
    It includes market regime detection and automatically adapts parameters based on
    volatility and trend conditions.
    
    Parameters:
        window (int): Period for moving average calculation (default: 20)
            - Lower values = more responsive to price changes, more signals
            - Higher values = smoother mean, fewer false signals
            - Typical range: 10-50 minutes for day trading
            
        deviation_threshold (float): Minimum deviation from mean for signal (default: 0.01)
            - Lower values = more signals, potential for noise
            - Higher values = stronger signals, fewer false positives
            - Range: 0.005-0.02 (0.5%-2% deviation from mean)
            
        enable_regime_detection (bool): Enable market regime detection (default: True)
            - True = Adapt strategy based on volatility and trend conditions
            - False = Use fixed parameters regardless of market conditions
            
        atr_period (int): Period for ATR calculation (default: 14)
        adx_period (int): Period for ADX calculation (default: 14)
    """
    
    def __init__(self, window: int = 20, deviation_threshold: float = 0.015,
                 enable_regime_detection: bool = True, atr_period: int = 14, adx_period: int = 14):
        super().__init__(enable_regime_detection, atr_period, adx_period)
        self.window = window
        self.deviation_threshold = deviation_threshold

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate buy/sell signals based on mean reversion with adaptive parameters.
        
        Args:
            data (pd.DataFrame): Price data with 'Close', 'High', 'Low' columns
            
        Returns:
            pd.Series: Signal series with values:
                - 1: Buy signal (price below mean by threshold)
                - -1: Sell signal (price above mean by threshold)
                - 0: No signal
                
        Strategy Logic:
            1. Calculate market regime indicators (ATR, ADX)
            2. Adapt parameters based on current market conditions
            3. Calculate moving average (mean)
            4. Detect deviations from mean
            5. Generate signals based on deviation threshold
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
            'window': self.window,
            'deviation_threshold': self.deviation_threshold
        }
        
        adapted_params = self._get_adaptive_parameters(data, base_params)
        
        # Calculate moving average using adapted window
        ma = data['Close'].rolling(window=adapted_params['window'], min_periods=1).mean()
        
        # Calculate deviation from mean
        deviation = (data['Close'] - ma) / ma
        
        # Generate signals
        signal = pd.Series(0, index=data.index)
        
        # Buy signal: price significantly below mean
        buy_condition = deviation < -adapted_params['deviation_threshold']
        # Sell signal: price significantly above mean
        sell_condition = deviation > adapted_params['deviation_threshold']
        
        signal[buy_condition] = 1
        signal[sell_condition] = -1
        
        return signal
    
    def _get_adaptive_parameters(self, data: pd.DataFrame, base_params: dict) -> dict:
        """
        Get adaptive parameters based on current market regime for Mean Reversion strategy.
        
        Args:
            data (pd.DataFrame): Price data with regime information
            base_params (dict): Base parameters for the strategy
            
        Returns:
            dict: Adapted parameters based on market conditions
            
        Adaptation Logic:
            - High Volatility: Shorter window, higher deviation threshold
            - Low Volatility: Longer window, lower deviation threshold
            - Strong Trend: Avoid mean reversion (not suitable for trending markets)
            - Ranging Market: Optimal conditions for mean reversion
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
                # High volatility: shorter window for faster response, higher threshold
                adapted_params['window'] = max(int(base_params['window'] * 0.7), 10)
                adapted_params['deviation_threshold'] = base_params['deviation_threshold'] * 1.5
            elif current_volatility == 'low':
                # Low volatility: longer window for smoother mean, lower threshold
                adapted_params['window'] = min(int(base_params['window'] * 1.3), 40)
                adapted_params['deviation_threshold'] = base_params['deviation_threshold'] * 0.7
            
            # Trend-based adaptations
            if current_trend == 'trending':
                # Strong trend: mean reversion is less effective, use more conservative settings
                adapted_params['window'] = min(int(adapted_params['window'] * 1.2), 30)
                adapted_params['deviation_threshold'] = adapted_params['deviation_threshold'] * 1.3
            elif current_trend == 'ranging':
                # Ranging market: optimal for mean reversion, use standard settings
                # Keep adapted parameters as is
                pass
            
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
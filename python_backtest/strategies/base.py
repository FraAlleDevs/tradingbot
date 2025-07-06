from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class Strategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    This class provides the foundation for implementing trading strategies
    and includes market regime detection capabilities that can be inherited
    by all strategy implementations.
    """
    
    def __init__(self, enable_regime_detection: bool = True, atr_period: int = 14, adx_period: int = 14):
        """
        Initialize strategy with regime detection capabilities.
        
        Args:
            enable_regime_detection (bool): Enable market regime detection (default: True)
            atr_period (int): Period for ATR calculation (default: 14)
            adx_period (int): Period for ADX calculation (default: 14)
        """
        self.enable_regime_detection = enable_regime_detection
        self.atr_period = atr_period
        self.adx_period = adx_period
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on the strategy logic.
        
        Args:
            data (pd.DataFrame): Price data with required columns
            
        Returns:
            pd.Series: Signal series with values:
                - 1: Buy signal
                - -1: Sell signal
                - 0: No signal
        """
        pass
    
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
    
    def _get_adaptive_parameters(self, data: pd.DataFrame, base_params: dict) -> dict:
        """
        Get adaptive parameters based on current market regime.
        
        Args:
            data (pd.DataFrame): Price data with regime information
            base_params (dict): Base parameters for the strategy
            
        Returns:
            dict: Adapted parameters based on market conditions
            
        This method should be overridden by each strategy to implement
        regime-specific parameter adaptations.
        """
        if not self.enable_regime_detection:
            return base_params
        
        # Get current regime (use most recent values)
        if 'volatility_regime' in data.columns and 'trend_regime' in data.columns:
            current_volatility = data['volatility_regime'].iloc[-1]
            current_trend = data['trend_regime'].iloc[-1]
            
            # Default adaptation logic (can be overridden by specific strategies)
            adapted_params = base_params.copy()
            
            # Volatility-based adaptations
            if current_volatility == 'high':
                # High volatility: more conservative
                adapted_params['position_size'] = base_params.get('position_size', 0.8) * 0.7
                adapted_params['stop_loss'] = base_params.get('stop_loss', 0.02) * 1.5
            elif current_volatility == 'low':
                # Low volatility: more aggressive
                adapted_params['position_size'] = base_params.get('position_size', 0.8) * 1.2
                adapted_params['stop_loss'] = base_params.get('stop_loss', 0.02) * 0.8
            
            # Trend-based adaptations
            if current_trend == 'trending':
                # Strong trend: let profits run
                adapted_params['min_holding_period'] = max(base_params.get('min_holding_period', 0), 5)
            elif current_trend == 'ranging':
                # Ranging market: take profits quickly
                adapted_params['min_holding_period'] = base_params.get('min_holding_period', 0)
            
            return adapted_params
        
        return base_params

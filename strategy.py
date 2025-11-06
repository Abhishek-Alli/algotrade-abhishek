"""
Trading strategies base class and implementations
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Strategy(ABC):
    """Base class for trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
        self.positions = []
        self.signals = []
    
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        """
        Generate trading signal based on market data
        Returns: {'action': 'BUY', 'SELL', or 'HOLD', 'confidence': float, 'price': float}
        """
        pass
    
    @abstractmethod
    def should_exit(self, position: Dict, current_price: float) -> bool:
        """Check if position should be exited"""
        pass


class MovingAverageStrategy(Strategy):
    """Simple Moving Average Crossover Strategy"""
    
    def __init__(self, fast_period: int = 10, slow_period: int = 30):
        super().__init__("Moving Average Crossover")
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        """Generate signal based on MA crossover"""
        if len(data) < self.slow_period:
            return {'action': 'HOLD', 'confidence': 0.0, 'price': 0.0}
        
        # Calculate moving averages
        data['MA_fast'] = data['close'].rolling(window=self.fast_period).mean()
        data['MA_slow'] = data['close'].rolling(window=self.slow_period).mean()
        
        current_price = float(data['close'].iloc[-1])
        ma_fast = data['MA_fast'].iloc[-1]
        ma_slow = data['MA_slow'].iloc[-1]
        prev_ma_fast = data['MA_fast'].iloc[-2]
        prev_ma_slow = data['MA_slow'].iloc[-2]
        
        # Golden cross: fast MA crosses above slow MA
        if prev_ma_fast <= prev_ma_slow and ma_fast > ma_slow:
            confidence = min(abs(ma_fast - ma_slow) / current_price * 100, 1.0)
            return {'action': 'BUY', 'confidence': confidence, 'price': current_price}
        
        # Death cross: fast MA crosses below slow MA
        elif prev_ma_fast >= prev_ma_slow and ma_fast < ma_slow:
            confidence = min(abs(ma_fast - ma_slow) / current_price * 100, 1.0)
            return {'action': 'SELL', 'confidence': confidence, 'price': current_price}
        
        return {'action': 'HOLD', 'confidence': 0.0, 'price': current_price}
    
    def should_exit(self, position: Dict, current_price: float) -> bool:
        """Exit if opposite signal"""
        entry_price = position.get('entry_price', 0)
        if entry_price == 0:
            return False
        
        if position['side'] == 'BUY':
            # Exit long if price drops below entry
            return current_price < entry_price * 0.98
        else:
            # Exit short if price rises above entry
            return current_price > entry_price * 1.02


class RSIMomentumStrategy(Strategy):
    """RSI-based momentum strategy"""
    
    def __init__(self, rsi_period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__("RSI Momentum")
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
    
    def calculate_rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        """Generate signal based on RSI"""
        if len(data) < self.rsi_period + 1:
            return {'action': 'HOLD', 'confidence': 0.0, 'price': 0.0}
        
        data['RSI'] = self.calculate_rsi(data['close'], self.rsi_period)
        current_price = float(data['close'].iloc[-1])
        current_rsi = data['RSI'].iloc[-1]
        prev_rsi = data['RSI'].iloc[-2]
        
        # Buy when RSI crosses above oversold level
        if prev_rsi <= self.oversold and current_rsi > self.oversold:
            confidence = min((current_rsi - self.oversold) / 40, 1.0)
            return {'action': 'BUY', 'confidence': confidence, 'price': current_price}
        
        # Sell when RSI crosses below overbought level
        elif prev_rsi >= self.overbought and current_rsi < self.overbought:
            confidence = min((self.overbought - current_rsi) / 40, 1.0)
            return {'action': 'SELL', 'confidence': confidence, 'price': current_price}
        
        return {'action': 'HOLD', 'confidence': 0.0, 'price': current_price}
    
    def should_exit(self, position: Dict, current_price: float) -> bool:
        """Exit based on RSI reversal"""
        entry_price = position.get('entry_price', 0)
        if entry_price == 0:
            return False
        
        # Simple exit logic
        if position['side'] == 'BUY':
            return current_price < entry_price * 0.97
        else:
            return current_price > entry_price * 1.03


class BollingerBandsStrategy(Strategy):
    """Bollinger Bands mean reversion strategy"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__("Bollinger Bands")
        self.period = period
        self.std_dev = std_dev
    
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        """Generate signal based on Bollinger Bands"""
        if len(data) < self.period:
            return {'action': 'HOLD', 'confidence': 0.0, 'price': 0.0}
        
        data['MA'] = data['close'].rolling(window=self.period).mean()
        data['STD'] = data['close'].rolling(window=self.period).std()
        data['Upper'] = data['MA'] + (data['STD'] * self.std_dev)
        data['Lower'] = data['MA'] - (data['STD'] * self.std_dev)
        
        current_price = float(data['close'].iloc[-1])
        upper = data['Upper'].iloc[-1]
        lower = data['Lower'].iloc[-1]
        ma = data['MA'].iloc[-1]
        
        # Buy when price touches lower band
        if current_price <= lower:
            confidence = min((lower - current_price) / current_price * 100, 1.0)
            return {'action': 'BUY', 'confidence': confidence, 'price': current_price}
        
        # Sell when price touches upper band
        elif current_price >= upper:
            confidence = min((current_price - upper) / current_price * 100, 1.0)
            return {'action': 'SELL', 'confidence': confidence, 'price': current_price}
        
        return {'action': 'HOLD', 'confidence': 0.0, 'price': current_price}
    
    def should_exit(self, position: Dict, current_price: float) -> bool:
        """Exit when price returns to mean"""
        entry_price = position.get('entry_price', 0)
        if entry_price == 0:
            return False
        
        # Exit when price moves back to mean
        if position['side'] == 'BUY':
            return current_price > entry_price * 1.02
        else:
            return current_price < entry_price * 0.98


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()


class EMAStrategy(Strategy):
    """EMA Crossover Strategy - Most popular EMA strategy"""
    
    def __init__(self, fast_period: int = 9, slow_period: int = 21):
        """
        Initialize EMA Crossover Strategy
        
        Common settings:
        - 9 & 21 periods (popular for day trading)
        - 12 & 26 periods (similar to MACD)
        """
        super().__init__("EMA Crossover")
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        """Generate signal based on EMA crossover"""
        if len(data) < self.slow_period + 1:
            return {'action': 'HOLD', 'confidence': 0.0, 'price': 0.0}
        
        # Calculate EMAs
        data['EMA_fast'] = calculate_ema(data['close'], self.fast_period)
        data['EMA_slow'] = calculate_ema(data['close'], self.slow_period)
        
        current_price = float(data['close'].iloc[-1])
        ema_fast = data['EMA_fast'].iloc[-1]
        ema_slow = data['EMA_slow'].iloc[-1]
        prev_ema_fast = data['EMA_fast'].iloc[-2]
        prev_ema_slow = data['EMA_slow'].iloc[-2]
        
        # Golden Cross: Fast EMA crosses above Slow EMA (Bullish)
        if prev_ema_fast <= prev_ema_slow and ema_fast > ema_slow:
            confidence = min(abs(ema_fast - ema_slow) / current_price * 100 * 2, 1.0)
            return {
                'action': 'BUY',
                'confidence': confidence,
                'price': current_price,
                'signal_type': 'Golden Cross',
                'entry_reason': f'Fast EMA ({self.fast_period}) crossed above Slow EMA ({self.slow_period})'
            }
        
        # Death Cross: Fast EMA crosses below Slow EMA (Bearish)
        elif prev_ema_fast >= prev_ema_slow and ema_fast < ema_slow:
            confidence = min(abs(ema_fast - ema_slow) / current_price * 100 * 2, 1.0)
            return {
                'action': 'SELL',
                'confidence': confidence,
                'price': current_price,
                'signal_type': 'Death Cross',
                'entry_reason': f'Fast EMA ({self.fast_period}) crossed below Slow EMA ({self.slow_period})'
            }
        
        return {'action': 'HOLD', 'confidence': 0.0, 'price': current_price}
    
    def should_exit(self, position: Dict, current_price: float) -> bool:
        """Exit if opposite crossover occurs"""
        entry_price = position.get('entry_price', 0)
        if entry_price == 0:
            return False
        
        # Exit long if price drops significantly
        if position['side'] == 'BUY':
            return current_price < entry_price * 0.97
        # Exit short if price rises significantly
        else:
            return current_price > entry_price * 1.03


class EMARibbonStrategy(Strategy):
    """EMA Ribbon Strategy - Multiple EMAs for trend strength"""
    
    def __init__(self, periods: List[int] = None):
        """
        Initialize EMA Ribbon Strategy
        
        Default periods: [8, 13, 21, 34, 55, 89] - Creates a ribbon effect
        """
        super().__init__("EMA Ribbon")
        self.periods = periods or [8, 13, 21, 34, 55, 89]
    
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        """Generate signal based on EMA ribbon alignment"""
        max_period = max(self.periods)
        if len(data) < max_period + 1:
            return {'action': 'HOLD', 'confidence': 0.0, 'price': 0.0}
        
        current_price = float(data['close'].iloc[-1])
        
        # Calculate all EMAs
        ema_values = []
        for period in self.periods:
            ema = calculate_ema(data['close'], period)
            ema_values.append(ema.iloc[-1])
        
        # Check ribbon alignment
        # Strong Uptrend: All EMAs stacked in order (fastest on top, slowest on bottom)
        # Price above all EMAs
        is_uptrend = all(ema_values[i] >= ema_values[i+1] for i in range(len(ema_values)-1))
        price_above_all = current_price > max(ema_values)
        
        # Strong Downtrend: All EMAs stacked in reverse order (fastest on bottom)
        # Price below all EMAs
        is_downtrend = all(ema_values[i] <= ema_values[i+1] for i in range(len(ema_values)-1))
        price_below_all = current_price < min(ema_values)
        
        # Check if ribbon is twisting (converging) - trend weakening
        ema_range = max(ema_values) - min(ema_values)
        price_range = data['high'].iloc[-20:].max() - data['low'].iloc[-20:].min()
        ribbon_twisting = ema_range < price_range * 0.1  # EMAs are converging
        
        # Strong uptrend signal
        if is_uptrend and price_above_all and not ribbon_twisting:
            # Look for pullback to ribbon
            if current_price <= ema_values[2]:  # Price near middle EMA
                confidence = 0.7
                return {
                    'action': 'BUY',
                    'confidence': confidence,
                    'price': current_price,
                    'signal_type': 'Ribbon Pullback',
                    'entry_reason': 'Pullback to EMA ribbon in strong uptrend'
                }
        
        # Strong downtrend signal
        if is_downtrend and price_below_all and not ribbon_twisting:
            # Look for bounce to ribbon
            if current_price >= ema_values[2]:  # Price near middle EMA
                confidence = 0.7
                return {
                    'action': 'SELL',
                    'confidence': confidence,
                    'price': current_price,
                    'signal_type': 'Ribbon Bounce',
                    'entry_reason': 'Bounce to EMA ribbon in strong downtrend'
                }
        
        return {'action': 'HOLD', 'confidence': 0.0, 'price': current_price}
    
    def should_exit(self, position: Dict, current_price: float) -> bool:
        """Exit when ribbon twists or reverses"""
        entry_price = position.get('entry_price', 0)
        if entry_price == 0:
            return False
        
        # Simple exit logic
        if position['side'] == 'BUY':
            return current_price < entry_price * 0.96
        else:
            return current_price > entry_price * 1.04


class EMA200Strategy(Strategy):
    """EMA 200 Strategy - Uses 200 EMA as bull/bear separator"""
    
    def __init__(self, ema_period: int = 200, pullback_ema: int = 21):
        """
        Initialize EMA 200 Strategy
        
        Uses 200 EMA to determine trend direction
        Uses shorter EMA (21) for pullback entries
        """
        super().__init__("EMA 200 Dynamic S/R")
        self.ema_period = ema_period
        self.pullback_ema = pullback_ema
    
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        """Generate signal based on 200 EMA and pullback"""
        if len(data) < self.ema_period + 1:
            return {'action': 'HOLD', 'confidence': 0.0, 'price': 0.0}
        
        # Calculate EMAs
        data['EMA_200'] = calculate_ema(data['close'], self.ema_period)
        data['EMA_pullback'] = calculate_ema(data['close'], self.pullback_ema)
        
        current_price = float(data['close'].iloc[-1])
        ema_200 = data['EMA_200'].iloc[-1]
        ema_pullback = data['EMA_pullback'].iloc[-1]
        
        # Uptrend: Price above 200 EMA
        if current_price > ema_200:
            # Look for pullback to pullback EMA
            recent_low = data['low'].iloc[-5:].min()
            if recent_low <= ema_pullback * 1.01 and current_price >= ema_pullback:
                # Bullish candlestick pattern check (simplified)
                if data['close'].iloc[-1] > data['open'].iloc[-1]:
                    confidence = 0.65
                    return {
                        'action': 'BUY',
                        'confidence': confidence,
                        'price': current_price,
                        'signal_type': 'Pullback Entry',
                        'entry_reason': f'Pullback to {self.pullback_ema} EMA in uptrend (above 200 EMA)'
                    }
        
        # Downtrend: Price below 200 EMA
        elif current_price < ema_200:
            # Look for rally to pullback EMA
            recent_high = data['high'].iloc[-5:].max()
            if recent_high >= ema_pullback * 0.99 and current_price <= ema_pullback:
                # Bearish candlestick pattern check (simplified)
                if data['close'].iloc[-1] < data['open'].iloc[-1]:
                    confidence = 0.65
                    return {
                        'action': 'SELL',
                        'confidence': confidence,
                        'price': current_price,
                        'signal_type': 'Rally Entry',
                        'entry_reason': f'Rally to {self.pullback_ema} EMA in downtrend (below 200 EMA)'
                    }
        
        return {'action': 'HOLD', 'confidence': 0.0, 'price': current_price}
    
    def should_exit(self, position: Dict, current_price: float) -> bool:
        """Exit based on 200 EMA reversal"""
        entry_price = position.get('entry_price', 0)
        if entry_price == 0:
            return False
        
        # Exit if trend reverses
        if position['side'] == 'BUY':
            return current_price < entry_price * 0.97
        else:
            return current_price > entry_price * 1.03



"""
Chart Pattern Detection and Trading Strategies
Detects and trades chart patterns: Head & Shoulders, Double Top/Bottom, Wedges, Flags, Pennants, Triangles
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from strategy import Strategy

logger = logging.getLogger(__name__)


class ChartPatternDetector:
    """Detect chart patterns in price data with validation"""
    
    def __init__(self):
        self.patterns_detected = []
        self.min_pattern_strength = 0.5  # Minimum confidence for pattern
        self.volume_confirmation_required = True
    
    def find_peaks(self, data: pd.Series, window: int = 5) -> List[int]:
        """Find peaks (local maxima)"""
        peaks = []
        for i in range(window, len(data) - window):
            if all(data.iloc[i] >= data.iloc[i-j] for j in range(1, window+1)) and \
               all(data.iloc[i] >= data.iloc[i+j] for j in range(1, window+1)):
                peaks.append(i)
        return peaks
    
    def find_troughs(self, data: pd.Series, window: int = 5) -> List[int]:
        """Find troughs (local minima)"""
        troughs = []
        for i in range(window, len(data) - window):
            if all(data.iloc[i] <= data.iloc[i-j] for j in range(1, window+1)) and \
               all(data.iloc[i] <= data.iloc[i+j] for j in range(1, window+1)):
                troughs.append(i)
        return troughs
    
    def validate_breakout(self, data: pd.DataFrame, breakout_price: float, 
                        breakout_direction: str, volume_threshold: float = 1.5) -> bool:
        """
        Validate breakout with volume confirmation
        
        Args:
            data: Recent price data
            breakout_price: Breakout level
            breakout_direction: 'up' or 'down'
            volume_threshold: Volume should be X times average
        
        Returns:
            True if valid breakout
        """
        if 'volume' not in data.columns:
            return True  # Skip volume validation if not available
        
        # Get recent volume
        recent_volume = data['volume'].tail(20).mean()
        current_volume = data['volume'].iloc[-1]
        
        # Check volume spike
        volume_confirmation = current_volume >= recent_volume * volume_threshold
        
        # Check price action
        current_price = data['close'].iloc[-1]
        current_high = data['high'].iloc[-1]
        current_low = data['low'].iloc[-1]
        
        if breakout_direction == 'down':
            # Downward breakout: close should be below breakout level
            price_confirmation = current_price < breakout_price * 0.995  # 0.5% below
        else:
            # Upward breakout: close should be above breakout level
            price_confirmation = current_price > breakout_price * 1.005  # 0.5% above
        
        return volume_confirmation and price_confirmation
    
    def calculate_pattern_strength(self, pattern_data: Dict, data: pd.DataFrame) -> float:
        """
        Calculate pattern strength (0-1)
        
        Factors:
        - Pattern symmetry
        - Volume confirmation
        - Breakout strength
        - Timeframe
        """
        strength = 0.5  # Base strength
        
        # Volume confirmation (+0.2)
        if 'volume' in data.columns:
            recent_volume = data['volume'].tail(20).mean()
            current_volume = data['volume'].iloc[-1]
            if current_volume >= recent_volume * 1.5:
                strength += 0.2
        
        # Breakout strength (+0.2)
        if pattern_data.get('breakout', False):
            current_price = data['close'].iloc[-1]
            breakout_price = pattern_data.get('neckline') or pattern_data.get('support') or pattern_data.get('resistance')
            if breakout_price:
                if pattern_data['type'] == 'Bullish':
                    breakout_strength = (current_price - breakout_price) / breakout_price
                else:
                    breakout_strength = (breakout_price - current_price) / breakout_price
                
                if breakout_strength > 0.01:  # 1% breakout
                    strength += 0.2
        
        # Pattern confidence from detection (+0.1)
        if pattern_data.get('confidence', 0) > 0.7:
            strength += 0.1
        
        return min(strength, 1.0)
    
    def detect_head_and_shoulders(self, data: pd.DataFrame, lookback: int = 50) -> Optional[Dict]:
        """Detect Head and Shoulders pattern with validation"""
        if len(data) < lookback:
            return None
        
        recent_data = data.tail(lookback)
        high = recent_data['high']
        
        # Find peaks
        peaks = self.find_peaks(high, window=3)
        
        if len(peaks) < 3:
            return None
        
        # Get last 3 peaks
        last_peaks = peaks[-3:]
        
        # Check H&S pattern: left shoulder < head > right shoulder, right shoulder ≈ left shoulder
        left_shoulder_idx = last_peaks[0]
        head_idx = last_peaks[1]
        right_shoulder_idx = last_peaks[2]
        
        left_shoulder_price = high.iloc[left_shoulder_idx]
        head_price = high.iloc[head_idx]
        right_shoulder_price = high.iloc[right_shoulder_idx]
        
        # Pattern conditions
        if (left_shoulder_price < head_price and 
            right_shoulder_price < head_price and
            abs(left_shoulder_price - right_shoulder_price) / left_shoulder_price < 0.05):  # Within 5%
            
            # Find neckline (support between shoulders)
            neckline_start = left_shoulder_idx
            neckline_end = right_shoulder_idx
            neckline_price = recent_data['low'].iloc[neckline_start:neckline_end].min()
            
            # Check if price broke below neckline
            current_price = recent_data['close'].iloc[-1]
            
            if current_price < neckline_price:
                # Validate breakout
                is_valid_breakout = self.validate_breakout(recent_data.tail(5), neckline_price, 'down')
                
                if not is_valid_breakout:
                    return {
                        'pattern': 'Head and Shoulders',
                        'type': 'Bearish',
                        'neckline': neckline_price,
                        'head': head_price,
                        'target': neckline_price - (head_price - neckline_price),
                        'breakout': False,  # False breakout - not confirmed
                        'confidence': 0.3,
                        'is_fake': True,
                        'reason': 'Volume confirmation missing or weak breakout'
                    }
                
                # Calculate target
                pattern_height = head_price - neckline_price
                target_price = neckline_price - pattern_height
                
                pattern_data = {
                    'pattern': 'Head and Shoulders',
                    'type': 'Bearish',
                    'neckline': neckline_price,
                    'head': head_price,
                    'target': target_price,
                    'breakout': True,
                    'confidence': 0.7,
                    'is_fake': False
                }
                
                # Calculate pattern strength
                pattern_data['strength'] = self.calculate_pattern_strength(pattern_data, recent_data)
                
                return pattern_data
        
        return None
    
    def detect_inverse_head_and_shoulders(self, data: pd.DataFrame, lookback: int = 50) -> Optional[Dict]:
        """Detect Inverse Head and Shoulders pattern with validation"""
        if len(data) < lookback:
            return None
        
        recent_data = data.tail(lookback)
        low = recent_data['low']
        
        # Find troughs
        troughs = self.find_troughs(low, window=3)
        
        if len(troughs) < 3:
            return None
        
        # Get last 3 troughs
        last_troughs = troughs[-3:]
        
        # Check Inverse H&S: left shoulder > head < right shoulder, right shoulder ≈ left shoulder
        left_shoulder_idx = last_troughs[0]
        head_idx = last_troughs[1]
        right_shoulder_idx = last_troughs[2]
        
        left_shoulder_price = low.iloc[left_shoulder_idx]
        head_price = low.iloc[head_idx]
        right_shoulder_price = low.iloc[right_shoulder_idx]
        
        # Pattern conditions
        if (left_shoulder_price > head_price and 
            right_shoulder_price > head_price and
            abs(left_shoulder_price - right_shoulder_price) / left_shoulder_price < 0.05):
            
            # Find neckline (resistance between shoulders)
            neckline_start = left_shoulder_idx
            neckline_end = right_shoulder_idx
            neckline_price = recent_data['high'].iloc[neckline_start:neckline_end].max()
            
            # Check if price broke above neckline
            current_price = recent_data['close'].iloc[-1]
            
            if current_price > neckline_price:
                # Validate breakout
                is_valid_breakout = self.validate_breakout(recent_data.tail(5), neckline_price, 'up')
                
                if not is_valid_breakout:
                    return {
                        'pattern': 'Inverse Head and Shoulders',
                        'type': 'Bullish',
                        'neckline': neckline_price,
                        'head': head_price,
                        'target': neckline_price + (neckline_price - head_price),
                        'breakout': False,
                        'confidence': 0.3,
                        'is_fake': True,
                        'reason': 'Volume confirmation missing or weak breakout'
                    }
                
                # Calculate target
                pattern_height = neckline_price - head_price
                target_price = neckline_price + pattern_height
                
                pattern_data = {
                    'pattern': 'Inverse Head and Shoulders',
                    'type': 'Bullish',
                    'neckline': neckline_price,
                    'head': head_price,
                    'target': target_price,
                    'breakout': True,
                    'confidence': 0.7,
                    'is_fake': False
                }
                
                pattern_data['strength'] = self.calculate_pattern_strength(pattern_data, recent_data)
                return pattern_data
        
        return None
    
    def detect_double_top(self, data: pd.DataFrame, lookback: int = 50) -> Optional[Dict]:
        """Detect Double Top pattern"""
        if len(data) < lookback:
            return None
        
        recent_data = data.tail(lookback)
        high = recent_data['high']
        
        # Find peaks
        peaks = self.find_peaks(high, window=3)
        
        if len(peaks) < 2:
            return None
        
        # Get last 2 peaks
        last_peaks = peaks[-2:]
        
        peak1_price = high.iloc[last_peaks[0]]
        peak2_price = high.iloc[last_peaks[1]]
        
        # Check if peaks are similar (within 2%)
        if abs(peak1_price - peak2_price) / peak1_price < 0.02:
            # Find valley (support between peaks)
            valley_start = last_peaks[0]
            valley_end = last_peaks[1]
            valley_price = recent_data['low'].iloc[valley_start:valley_end].min()
            
            # Check if price broke below valley
            current_price = recent_data['close'].iloc[-1]
            
            if current_price < valley_price:
                # Calculate target
                pattern_height = peak1_price - valley_price
                target_price = valley_price - pattern_height
                
                return {
                    'pattern': 'Double Top',
                    'type': 'Bearish',
                    'resistance': peak1_price,
                    'support': valley_price,
                    'target': target_price,
                    'breakout': True,
                    'confidence': 0.65
                }
        
        return None
    
    def detect_double_bottom(self, data: pd.DataFrame, lookback: int = 50) -> Optional[Dict]:
        """Detect Double Bottom pattern"""
        if len(data) < lookback:
            return None
        
        recent_data = data.tail(lookback)
        low = recent_data['low']
        
        # Find troughs
        troughs = self.find_troughs(low, window=3)
        
        if len(troughs) < 2:
            return None
        
        # Get last 2 troughs
        last_troughs = troughs[-2:]
        
        trough1_price = low.iloc[last_troughs[0]]
        trough2_price = low.iloc[last_troughs[1]]
        
        # Check if troughs are similar (within 2%)
        if abs(trough1_price - trough2_price) / trough1_price < 0.02:
            # Find peak (resistance between troughs)
            peak_start = last_troughs[0]
            peak_end = last_troughs[1]
            peak_price = recent_data['high'].iloc[peak_start:peak_end].max()
            
            # Check if price broke above peak
            current_price = recent_data['close'].iloc[-1]
            
            if current_price > peak_price:
                # Calculate target
                pattern_height = peak_price - trough1_price
                target_price = peak_price + pattern_height
                
                return {
                    'pattern': 'Double Bottom',
                    'type': 'Bullish',
                    'support': trough1_price,
                    'resistance': peak_price,
                    'target': target_price,
                    'breakout': True,
                    'confidence': 0.65
                }
        
        return None
    
    def detect_triangle(self, data: pd.DataFrame, lookback: int = 30) -> Optional[Dict]:
        """Detect Triangle patterns (Ascending, Descending, Symmetrical)"""
        if len(data) < lookback:
            return None
        
        recent_data = data.tail(lookback)
        
        # Find peaks and troughs
        peaks = self.find_peaks(recent_data['high'], window=2)
        troughs = self.find_troughs(recent_data['low'], window=2)
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        # Get trendlines
        recent_peaks = peaks[-2:]
        recent_troughs = troughs[-2:]
        
        peak1_price = recent_data['high'].iloc[recent_peaks[0]]
        peak2_price = recent_data['high'].iloc[recent_peaks[1]]
        trough1_price = recent_data['low'].iloc[recent_troughs[0]]
        trough2_price = recent_data['low'].iloc[recent_troughs[1]]
        
        # Calculate slopes
        resistance_slope = (peak2_price - peak1_price) / (recent_peaks[1] - recent_peaks[0])
        support_slope = (trough2_price - trough1_price) / (recent_troughs[1] - recent_troughs[0])
        
        current_price = recent_data['close'].iloc[-1]
        
        # Ascending Triangle: Flat resistance, rising support
        if abs(resistance_slope) < 0.001 and support_slope > 0.001:
            # Breakout above resistance
            if current_price > peak2_price:
                target = peak2_price + (peak2_price - trough2_price)
                return {
                    'pattern': 'Ascending Triangle',
                    'type': 'Bullish',
                    'resistance': peak2_price,
                    'support': trough2_price,
                    'target': target,
                    'breakout': True,
                    'confidence': 0.7
                }
        
        # Descending Triangle: Flat support, falling resistance
        elif abs(support_slope) < 0.001 and resistance_slope < -0.001:
            # Breakout below support
            if current_price < trough2_price:
                target = trough2_price - (peak2_price - trough2_price)
                return {
                    'pattern': 'Descending Triangle',
                    'type': 'Bearish',
                    'resistance': peak2_price,
                    'support': trough2_price,
                    'target': target,
                    'breakout': True,
                    'confidence': 0.7
                }
        
        # Symmetrical Triangle: Converging trendlines
        elif (resistance_slope < 0 and support_slope > 0) or (abs(resistance_slope) < 0.001 and abs(support_slope) < 0.001):
            # Determine trend direction
            price_trend = (recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]) / recent_data['close'].iloc[0]
            
            if price_trend > 0:
                # Breakout above
                if current_price > peak2_price:
                    target = peak2_price + (peak2_price - trough2_price)
                    return {
                        'pattern': 'Symmetrical Triangle',
                        'type': 'Bullish',
                        'resistance': peak2_price,
                        'support': trough2_price,
                        'target': target,
                        'breakout': True,
                        'confidence': 0.6
                    }
            else:
                # Breakout below
                if current_price < trough2_price:
                    target = trough2_price - (peak2_price - trough2_price)
                    return {
                        'pattern': 'Symmetrical Triangle',
                        'type': 'Bearish',
                        'resistance': peak2_price,
                        'support': trough2_price,
                        'target': target,
                        'breakout': True,
                        'confidence': 0.6
                    }
        
        return None
    
    def detect_flag(self, data: pd.DataFrame, lookback: int = 30) -> Optional[Dict]:
        """Detect Flag pattern (Bull Flag or Bear Flag)"""
        if len(data) < lookback:
            return None
        
        recent_data = data.tail(lookback)
        
        # Split into flagpole and flag
        flagpole_length = lookback // 3
        flag_length = lookback - flagpole_length
        
        flagpole = recent_data.head(flagpole_length)
        flag = recent_data.tail(flag_length)
        
        # Calculate flagpole direction and magnitude
        flagpole_start = flagpole['close'].iloc[0]
        flagpole_end = flagpole['close'].iloc[-1]
        flagpole_change = (flagpole_end - flagpole_start) / flagpole_start
        
        # Bull Flag: Strong upward flagpole
        if flagpole_change > 0.05:  # 5% move
            # Flag should be consolidating downward
            flag_high = flag['high'].max()
            flag_low = flag['low'].min()
            flag_range = (flag_high - flag_low) / flag_low
            
            if flag_range < 0.03:  # Tight consolidation
                current_price = recent_data['close'].iloc[-1]
                if current_price > flag_high:
                    target = current_price + abs(flagpole_change * flagpole_start)
                    return {
                        'pattern': 'Bull Flag',
                        'type': 'Bullish',
                        'resistance': flag_high,
                        'target': target,
                        'breakout': True,
                        'confidence': 0.7
                    }
        
        # Bear Flag: Strong downward flagpole
        elif flagpole_change < -0.05:  # -5% move
            # Flag should be consolidating upward
            flag_high = flag['high'].max()
            flag_low = flag['low'].min()
            flag_range = (flag_high - flag_low) / flag_low
            
            if flag_range < 0.03:  # Tight consolidation
                current_price = recent_data['close'].iloc[-1]
                if current_price < flag_low:
                    target = current_price - abs(flagpole_change * flagpole_start)
                    return {
                        'pattern': 'Bear Flag',
                        'type': 'Bearish',
                        'support': flag_low,
                        'target': target,
                        'breakout': True,
                        'confidence': 0.7
                    }
        
        return None
    
    def detect_wedge(self, data: pd.DataFrame, lookback: int = 30) -> Optional[Dict]:
        """Detect Wedge pattern (Rising or Falling)"""
        if len(data) < lookback:
            return None
        
        recent_data = data.tail(lookback)
        
        # Find peaks and troughs
        peaks = self.find_peaks(recent_data['high'], window=2)
        troughs = self.find_troughs(recent_data['low'], window=2)
        
        if len(peaks) < 2 or len(troughs) < 2:
            return None
        
        recent_peaks = peaks[-2:]
        recent_troughs = troughs[-2:]
        
        peak1_price = recent_data['high'].iloc[recent_peaks[0]]
        peak2_price = recent_data['high'].iloc[recent_peaks[1]]
        trough1_price = recent_data['low'].iloc[recent_troughs[0]]
        trough2_price = recent_data['low'].iloc[recent_troughs[1]]
        
        # Calculate slopes
        resistance_slope = (peak2_price - peak1_price) / (recent_peaks[1] - recent_peaks[0])
        support_slope = (trough2_price - trough1_price) / (recent_troughs[1] - recent_troughs[0])
        
        current_price = recent_data['close'].iloc[-1]
        
        # Rising Wedge: Both trendlines rising but converging
        if resistance_slope > 0 and support_slope > 0 and resistance_slope < support_slope:
            # Breakout typically downward
            if current_price < trough2_price:
                target = trough2_price - (peak2_price - trough2_price)
                return {
                    'pattern': 'Rising Wedge',
                    'type': 'Bearish',
                    'resistance': peak2_price,
                    'support': trough2_price,
                    'target': target,
                    'breakout': True,
                    'confidence': 0.65
                }
        
        # Falling Wedge: Both trendlines falling but converging
        elif resistance_slope < 0 and support_slope < 0 and abs(resistance_slope) < abs(support_slope):
            # Breakout typically upward
            if current_price > peak2_price:
                target = peak2_price + (peak2_price - trough2_price)
                return {
                    'pattern': 'Falling Wedge',
                    'type': 'Bullish',
                    'resistance': peak2_price,
                    'support': trough2_price,
                    'target': target,
                    'breakout': True,
                    'confidence': 0.65
                }
        
        return None
    
    def detect_all_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """Detect all chart patterns"""
        patterns = []
        
        # Try different lookback periods
        for lookback in [30, 50, 100]:
            if len(data) < lookback:
                continue
            
            # Reversal patterns
            hns = self.detect_head_and_shoulders(data, lookback)
            if hns:
                patterns.append(hns)
            
            inv_hns = self.detect_inverse_head_and_shoulders(data, lookback)
            if inv_hns:
                patterns.append(inv_hns)
            
            dt = self.detect_double_top(data, lookback)
            if dt:
                patterns.append(dt)
            
            db = self.detect_double_bottom(data, lookback)
            if db:
                patterns.append(db)
            
            # Continuation patterns
            triangle = self.detect_triangle(data, lookback)
            if triangle:
                patterns.append(triangle)
            
            flag = self.detect_flag(data, lookback)
            if flag:
                patterns.append(flag)
            
            wedge = self.detect_wedge(data, lookback)
            if wedge:
                patterns.append(wedge)
        
        return patterns


class ChartPatternStrategy(Strategy):
    """Chart Pattern Trading Strategy"""
    
    def __init__(self, pattern_types: List[str] = None):
        """
        Initialize Chart Pattern Strategy
        
        Args:
            pattern_types: List of patterns to trade (None = all patterns)
        """
        super().__init__("Chart Patterns")
        self.detector = ChartPatternDetector()
        self.pattern_types = pattern_types or ['all']
    
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        """Generate signal based on chart patterns with fake signal detection"""
        if len(data) < 50:
            return {'action': 'HOLD', 'confidence': 0.0, 'price': 0.0, 'is_fake': False}
        
        # Detect patterns
        patterns = self.detector.detect_all_patterns(data)
        
        if not patterns:
            return {'action': 'HOLD', 'confidence': 0.0, 'price': float(data['close'].iloc[-1]), 'is_fake': False}
        
        # Filter patterns: only real breakouts with sufficient strength
        valid_patterns = []
        for pattern in patterns:
            # Check if pattern has breakout
            if not pattern.get('breakout', False):
                continue
            
            # Check if it's a fake signal
            if pattern.get('is_fake', False):
                continue
            
            # Check pattern strength
            pattern_strength = pattern.get('strength', 0.5)
            if pattern_strength < self.min_pattern_strength:
                continue  # Skip weak patterns
            
            valid_patterns.append(pattern)
        
        if not valid_patterns:
            # Check if there are fake patterns detected
            fake_patterns = [p for p in patterns if p.get('is_fake', False)]
            if fake_patterns:
                return {
                    'action': 'HOLD',
                    'confidence': 0.0,
                    'price': float(data['close'].iloc[-1]),
                    'is_fake': True,
                    'fake_reason': fake_patterns[0].get('reason', 'Pattern detected but not confirmed')
                }
            return {'action': 'HOLD', 'confidence': 0.0, 'price': float(data['close'].iloc[-1]), 'is_fake': False}
        
        # Sort by strength and confidence
        valid_patterns.sort(key=lambda x: (x.get('strength', 0) + x.get('confidence', 0)) / 2, reverse=True)
        best_pattern = valid_patterns[0]
        
        current_price = float(data['close'].iloc[-1])
        
        # Generate signal based on pattern type
        if best_pattern['type'] == 'Bullish':
            return {
                'action': 'BUY',
                'confidence': best_pattern.get('strength', best_pattern.get('confidence', 0.6)),
                'price': current_price,
                'stop_loss': best_pattern.get('support', current_price * 0.98),
                'take_profit': best_pattern.get('target', current_price * 1.03),
                'pattern': best_pattern['pattern'],
                'signal_type': 'Bullish Pattern',
                'entry_reason': f"{best_pattern['pattern']} breakout confirmed (Real Signal)",
                'is_fake': False,
                'pattern_strength': best_pattern.get('strength', 0.7)
            }
        else:  # Bearish
            return {
                'action': 'SELL',
                'confidence': best_pattern.get('strength', best_pattern.get('confidence', 0.6)),
                'price': current_price,
                'stop_loss': best_pattern.get('resistance', current_price * 1.02),
                'take_profit': best_pattern.get('target', current_price * 0.97),
                'pattern': best_pattern['pattern'],
                'signal_type': 'Bearish Pattern',
                'entry_reason': f"{best_pattern['pattern']} breakout confirmed (Real Signal)",
                'is_fake': False,
                'pattern_strength': best_pattern.get('strength', 0.7)
            }
    
    def should_exit(self, position: Dict, current_price: float) -> bool:
        """Exit based on pattern failure or target hit"""
        entry_price = position.get('entry_price', 0)
        if entry_price == 0:
            return False
        
        # Simple exit logic - can be enhanced
        if position['side'] == 'BUY':
            return current_price < entry_price * 0.97
        else:
            return current_price > entry_price * 1.03


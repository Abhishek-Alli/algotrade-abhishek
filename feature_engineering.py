"""
Feature Engineering Module
Creates technical indicators, sentiment features, and F&O-specific features
"""
import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Feature engineering for trading models"""
    
    def __init__(self):
        pass
    
    def create_features(self, price_data: pd.DataFrame, news_data: pd.DataFrame = None,
                       sentiment_data: pd.DataFrame = None) -> pd.DataFrame:
        """Create all features from raw data"""
        df = price_data.copy()
        
        # Technical indicators
        df = self._add_trend_indicators(df)
        df = self._add_momentum_indicators(df)
        df = self._add_volatility_indicators(df)
        df = self._add_volume_indicators(df)
        
        # Sentiment features
        if news_data is not None and not news_data.empty:
            df = self._add_sentiment_features(df, news_data)
        
        # F&O features (if available)
        df = self._add_fo_features(df)
        
        # Price-based features
        df = self._add_price_features(df)
        
        return df
    
    def _add_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add trend indicators: SMA, EMA, MACD"""
        if 'close' not in df.columns:
            return df
        
        # Simple Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # Exponential Moving Averages
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Trend strength
        df['price_above_sma20'] = (df['close'] > df['sma_20']).astype(int)
        df['price_above_sma50'] = (df['close'] > df['sma_50']).astype(int)
        df['price_above_sma200'] = (df['close'] > df['sma_200']).astype(int)
        
        return df
    
    def _add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum indicators: RSI, Stochastic"""
        if 'close' not in df.columns:
            return df
        
        # RSI
        df['rsi'] = self._calculate_rsi(df['close'], period=14)
        df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
        df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
        
        # Stochastic Oscillator
        low_14 = df['low'].rolling(window=14).min()
        high_14 = df['high'].rolling(window=14).max()
        df['stoch_k'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
        df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
        
        # Rate of Change
        df['roc'] = df['close'].pct_change(periods=10) * 100
        
        return df
    
    def _add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility indicators: Bollinger Bands, ATR"""
        if 'close' not in df.columns:
            return df
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Average True Range (ATR)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(window=14).mean()
        df['atr_pct'] = (df['atr'] / df['close']) * 100
        
        return df
    
    def _add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume indicators: OBV, VWAP"""
        if 'volume' not in df.columns or 'close' not in df.columns:
            return df
        
        # On-Balance Volume (OBV)
        price_change = df['close'].diff()
        df['obv'] = (np.sign(price_change) * df['volume']).fillna(0).cumsum()
        df['obv_sma'] = df['obv'].rolling(window=20).mean()
        
        # Volume Weighted Average Price (VWAP)
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        df['vwap'] = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        df['price_vs_vwap'] = (df['close'] - df['vwap']) / df['vwap'] * 100
        
        # Volume ratio
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        df['volume_spike'] = (df['volume_ratio'] > 1.5).astype(int)
        
        return df
    
    def _add_sentiment_features(self, df: pd.DataFrame, news_data: pd.DataFrame) -> pd.DataFrame:
        """Add sentiment-based features"""
        if news_data.empty:
            return df
        
        # Merge sentiment data by timestamp
        news_data['published_at'] = pd.to_datetime(news_data['published_at'])
        news_data = news_data.sort_values('published_at')
        
        # Calculate rolling sentiment averages
        for window in [1, 24, 168]:  # 1h, 24h, 7 days
            df[f'news_sentiment_{window}h_avg'] = 0.0
            df[f'news_volume_{window}h'] = 0
        
        # Calculate sentiment metrics
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            for idx, row in df.iterrows():
                time_window = row['timestamp'] - pd.Timedelta(hours=24)
                recent_news = news_data[news_data['published_at'] >= time_window]
                
                if not recent_news.empty:
                    df.at[idx, 'news_sentiment_24h_avg'] = recent_news['sentiment_score'].mean()
                    df.at[idx, 'news_volume_24h'] = len(recent_news)
        
        # News volume spike
        if 'news_volume_24h' in df.columns:
            avg_news_volume = df['news_volume_24h'].rolling(window=30).mean()
            df['news_volume_spike'] = (df['news_volume_24h'] > avg_news_volume * 2).astype(int)
        
        return df
    
    def _add_fo_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add F&O-specific features"""
        # Placeholder for F&O features
        # These would come from broker API
        df['open_interest'] = 0
        df['open_interest_change'] = 0
        df['put_call_ratio'] = 1.0
        df['implied_volatility'] = 0.0
        
        return df
    
    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add price-based features"""
        if 'close' not in df.columns:
            return df
        
        # Price change features
        for period in [1, 5, 10, 20]:
            df[f'price_change_{period}'] = df['close'].pct_change(periods=period) * 100
        
        # Support and resistance levels (simplified)
        df['recent_high'] = df['high'].rolling(window=20).max()
        df['recent_low'] = df['low'].rolling(window=20).min()
        
        # Distance from high/low
        df['dist_from_high'] = (df['close'] - df['recent_high']) / df['recent_high'] * 100
        df['dist_from_low'] = (df['close'] - df['recent_low']) / df['recent_low'] * 100
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def create_target_labels(self, df: pd.DataFrame, forward_periods: int = 5,
                           threshold: float = 0.5) -> pd.Series:
        """Create target labels for supervised learning"""
        if 'close' not in df.columns:
            return pd.Series()
        
        future_price = df['close'].shift(-forward_periods)
        price_change_pct = ((future_price - df['close']) / df['close']) * 100
        
        # Create labels: 1 for up, -1 for down, 0 for no significant move
        labels = pd.Series(0, index=df.index)
        labels[price_change_pct > threshold] = 1
        labels[price_change_pct < -threshold] = -1
        
        return labels



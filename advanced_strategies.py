"""
Advanced Trading Strategies
News-Based Momentum, Mean Reversion, IV Crush, Crypto On-Chain
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging
from strategy import Strategy
from data_ingestion import DataFusion
from feature_engineering import FeatureEngineer
from ml_models import PriceDirectionModel

logger = logging.getLogger(__name__)


class NewsMomentumStrategy(Strategy):
    """Strategy 1: News-Based Momentum (Intraday/Swing)"""
    
    def __init__(self, sentiment_threshold: float = 0.7, volume_multiplier: float = 1.5):
        super().__init__("News-Based Momentum")
        self.sentiment_threshold = sentiment_threshold
        self.volume_multiplier = volume_multiplier
        self.data_fusion = DataFusion()
        self.feature_engineer = FeatureEngineer()
    
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        """Generate signal based on news momentum"""
        if len(data) < 20:
            return {'action': 'HOLD', 'confidence': 0.0, 'price': 0.0, 'stop_loss': 0.0, 'take_profit': 0.0}
        
        current_price = float(data['close'].iloc[-1])
        
        # Get news sentiment
        symbol = data.get('symbol', 'UNKNOWN').iloc[0] if 'symbol' in data.columns else 'UNKNOWN'
        sentiment_24h = self.data_fusion.news_ingestion.get_sentiment_24h(symbol)
        
        # Check if strong positive news
        if sentiment_24h < self.sentiment_threshold:
            return {'action': 'HOLD', 'confidence': 0.0, 'price': current_price}
        
        # Calculate VWAP
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        vwap = (typical_price * data['volume']).cumsum() / data['volume'].cumsum()
        current_vwap = vwap.iloc[-1]
        
        # Calculate volume average
        volume_avg = data['volume'].rolling(window=20).mean().iloc[-1]
        current_volume = data['volume'].iloc[-1]
        
        # Check confirmation: price above VWAP and volume spike
        price_above_vwap = current_price > current_vwap
        volume_spike = current_volume > volume_avg * self.volume_multiplier
        
        if price_above_vwap and volume_spike:
            # Calculate SL and TP
            recent_low = data['low'].rolling(window=10).min().iloc[-1]
            sl_percent = 1.5
            sl_price = min(recent_low, current_price * (1 - sl_percent / 100))
            tp_price_1 = current_price * (1 + sl_percent / 100)  # Risk 1x
            tp_price_2 = current_price * (1 + sl_percent * 1.5 / 100)  # Extended target
            
            confidence = min(sentiment_24h * 0.7 + 0.3, 1.0)
            
            return {
                'action': 'BUY',
                'confidence': confidence,
                'price': current_price,
                'stop_loss': sl_price,
                'take_profit': tp_price_1,
                'take_profit_2': tp_price_2,
                'entry_reason': 'News momentum with volume confirmation'
            }
        
        return {'action': 'HOLD', 'confidence': 0.0, 'price': current_price}
    
    def should_exit(self, position: Dict, current_price: float) -> bool:
        """Exit when RSI crosses above 80 (overbought)"""
        # This would be checked in trading engine with real-time data
        return False


class MeanReversionStrategy(Strategy):
    """Strategy 2: Mean Reversion with Sentiment Filter"""
    
    def __init__(self, ema_period: int = 200, rsi_oversold: int = 30):
        super().__init__("Mean Reversion with Sentiment")
        self.ema_period = ema_period
        self.rsi_oversold = rsi_oversold
        self.data_fusion = DataFusion()
        self.feature_engineer = FeatureEngineer()
    
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        """Generate signal based on mean reversion"""
        if len(data) < self.ema_period:
            return {'action': 'HOLD', 'confidence': 0.0, 'price': 0.0}
        
        # Calculate indicators
        data['ema_200'] = data['close'].ewm(span=self.ema_period, adjust=False).mean()
        data['rsi'] = self.feature_engineer._calculate_rsi(data['close'], period=14)
        
        current_price = float(data['close'].iloc[-1])
        ema_200 = data['ema_200'].iloc[-1]
        rsi = data['rsi'].iloc[-1]
        prev_rsi = data['rsi'].iloc[-2] if len(data) > 1 else rsi
        
        # Check long-term uptrend
        price_above_ema = current_price > ema_200
        
        # Get sentiment
        symbol = data.get('symbol', 'UNKNOWN').iloc[0] if 'symbol' in data.columns else 'UNKNOWN'
        sentiment_24h = self.data_fusion.news_ingestion.get_sentiment_24h(symbol)
        sentiment_positive = sentiment_24h > 0.2
        
        # Check for oversold condition
        rsi_oversold_now = rsi < self.rsi_oversold
        rsi_crossing_up = prev_rsi <= self.rsi_oversold and rsi > self.rsi_oversold
        
        # Buy signal: Uptrend + Positive sentiment + RSI oversold recovery
        if price_above_ema and sentiment_positive and rsi_crossing_up:
            # Calculate SL and TP
            recent_low = data['low'].rolling(window=20).min().iloc[-1]
            sl_price = recent_low * 0.98
            
            # TP at upper Bollinger Band
            bb_upper = data['close'].rolling(window=20).mean().iloc[-1] + \
                       (data['close'].rolling(window=20).std().iloc[-1] * 2)
            tp_price = min(bb_upper, current_price * 1.04)
            
            confidence = 0.6 + (sentiment_24h * 0.2)
            
            return {
                'action': 'BUY',
                'confidence': min(confidence, 1.0),
                'price': current_price,
                'stop_loss': sl_price,
                'take_profit': tp_price,
                'entry_reason': 'Mean reversion in uptrend with positive sentiment'
            }
        
        return {'action': 'HOLD', 'confidence': 0.0, 'price': current_price}
    
    def should_exit(self, position: Dict, current_price: float) -> bool:
        """Exit logic"""
        entry_price = position.get('entry_price', 0)
        if entry_price == 0:
            return False
        return current_price > entry_price * 1.03


class IVCrushStrategy(Strategy):
    """Strategy 3: IV Crush Play (Options)"""
    
    def __init__(self, iv_percentile_threshold: int = 90):
        super().__init__("IV Crush Play")
        self.iv_percentile_threshold = iv_percentile_threshold
    
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        """Generate signal for IV crush strategy"""
        # This strategy is specific to options
        # Requires IV data from broker API
        current_price = float(data['close'].iloc[-1])
        
        # Placeholder: Would check IV percentile
        # If IV is high (90th percentile), sell strangle
        # This is a complex strategy that requires options chain data
        
        return {
            'action': 'HOLD',
            'confidence': 0.0,
            'price': current_price,
            'note': 'IV Crush strategy requires options chain and IV data'
        }
    
    def should_exit(self, position: Dict, current_price: float) -> bool:
        """Exit when premium doubles or captures 60-70%"""
        # Would check premium received vs current premium
        return False


class CryptoOnChainStrategy(Strategy):
    """Strategy 4: Crypto On-Chain & Social Sentiment"""
    
    def __init__(self, fear_threshold: int = 20, greed_threshold: int = 75):
        super().__init__("Crypto On-Chain Strategy")
        self.fear_threshold = fear_threshold
        self.greed_threshold = greed_threshold
        self.data_fusion = DataFusion()
        self.feature_engineer = FeatureEngineer()
    
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        """Generate signal based on crypto fear/greed and on-chain data"""
        if len(data) < 200:
            return {'action': 'HOLD', 'confidence': 0.0, 'price': 0.0}
        
        current_price = float(data['close'].iloc[-1])
        
        # Get Fear & Greed Index
        fear_greed_index = self.data_fusion.sentiment_ingestion.get_crypto_fear_greed_index()
        
        # Get exchange reserves (simplified)
        symbol = data.get('symbol', 'BTC').iloc[0] if 'symbol' in data.columns else 'BTC'
        if symbol in ['BTC', 'ETH']:
            reserves = self.data_fusion.onchain_ingestion.get_exchange_reserves(symbol)
            reserves_decreasing = reserves.get('change_24h', 0) < 0
        else:
            reserves_decreasing = False
        
        # Calculate 200-week MA (simplified to 200-day)
        ma_200 = data['close'].rolling(window=200).mean().iloc[-1]
        price_near_support = abs(current_price - ma_200) / ma_200 < 0.05
        
        # Buy signal: Extreme fear + Reserves decreasing + Price near support
        if fear_greed_index < self.fear_threshold and reserves_decreasing and price_near_support:
            # Wide stop loss for swing/long-term
            sl_price = ma_200 * 0.95
            
            # TP: Scale out as Fear & Greed moves to Greed
            tp_price = current_price * 1.15  # Initial target
            
            confidence = 0.7
            
            return {
                'action': 'BUY',
                'confidence': confidence,
                'price': current_price,
                'stop_loss': sl_price,
                'take_profit': tp_price,
                'entry_reason': f'Extreme fear ({fear_greed_index}) + Reserves decreasing + Support level'
            }
        
        # Sell signal: Extreme greed
        elif fear_greed_index > self.greed_threshold:
            confidence = 0.6
            return {
                'action': 'SELL',
                'confidence': confidence,
                'price': current_price,
                'entry_reason': f'Extreme greed ({fear_greed_index}) - Take profit'
            }
        
        return {'action': 'HOLD', 'confidence': 0.0, 'price': current_price}
    
    def should_exit(self, position: Dict, current_price: float) -> bool:
        """Exit when Fear & Greed moves to Greed territory"""
        fear_greed = self.data_fusion.sentiment_ingestion.get_crypto_fear_greed_index()
        if position['side'] == 'BUY':
            return fear_greed > self.greed_threshold
        return False


class MLBasedStrategy(Strategy):
    """ML-based strategy using trained models"""
    
    def __init__(self, model: PriceDirectionModel = None):
        super().__init__("ML-Based Strategy")
        self.model = model or PriceDirectionModel(model_type='xgboost')
        self.feature_engineer = FeatureEngineer()
        self.is_trained = False
    
    def train(self, data: pd.DataFrame, forward_periods: int = 5):
        """Train the model"""
        # Create features
        features_df = self.feature_engineer.create_features(data)
        
        # Create target labels
        labels = self.feature_engineer.create_target_labels(features_df, forward_periods)
        
        # Prepare data
        feature_cols = [col for col in features_df.columns 
                       if col not in ['timestamp', 'symbol', 'close', 'open', 'high', 'low', 'volume']]
        X = features_df[feature_cols].dropna()
        y = labels[X.index]
        
        # Remove rows with invalid labels
        valid_mask = y.isin([-1, 0, 1])
        X = X[valid_mask]
        y = y[valid_mask]
        
        if len(X) < 100:
            logger.warning("Insufficient data for training")
            return
        
        # Train model
        results = self.model.train(X, y)
        self.is_trained = True
        logger.info(f"ML model trained: {results}")
    
    def generate_signal(self, data: pd.DataFrame) -> Dict:
        """Generate signal using ML model"""
        if not self.is_trained:
            return {'action': 'HOLD', 'confidence': 0.0, 'price': 0.0}
        
        current_price = float(data['close'].iloc[-1])
        
        # Create features
        features_df = self.feature_engineer.create_features(data)
        
        # Get latest features
        feature_cols = [col for col in features_df.columns 
                       if col not in ['timestamp', 'symbol', 'close', 'open', 'high', 'low', 'volume']]
        X = features_df[feature_cols].iloc[-1:].dropna(axis=1)
        
        if X.empty:
            return {'action': 'HOLD', 'confidence': 0.0, 'price': current_price}
        
        # Predict
        try:
            prediction = self.model.predict(X)
            probabilities = self.model.predict_proba(X)
            
            if len(prediction) > 0:
                pred = prediction[0]
                prob = probabilities[0]
                
                if pred == 1:
                    action = 'BUY'
                    confidence = float(prob[2]) if len(prob) > 2 else 0.5
                elif pred == -1:
                    action = 'SELL'
                    confidence = float(prob[0]) if len(prob) > 0 else 0.5
                else:
                    action = 'HOLD'
                    confidence = float(prob[1]) if len(prob) > 1 else 0.0
                
                return {
                    'action': action,
                    'confidence': confidence,
                    'price': current_price,
                    'prediction': pred,
                    'entry_reason': 'ML model prediction'
                }
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
        
        return {'action': 'HOLD', 'confidence': 0.0, 'price': current_price}
    
    def should_exit(self, position: Dict, current_price: float) -> bool:
        """Exit based on ML model"""
        # Would check model prediction for exit signal
        return False



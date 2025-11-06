"""
AI Analysis Interface
Provides synthesized analysis for user queries
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from data_ingestion import DataFusion
from feature_engineering import FeatureEngineer
from api_client import APIClient

logger = logging.getLogger(__name__)


class AIAnalyst:
    """AI-powered analyst for comprehensive market analysis"""
    
    def __init__(self, api_client: APIClient = None):
        self.data_fusion = DataFusion()
        self.feature_engineer = FeatureEngineer()
        self.api_client = api_client
    
    def analyze_symbol(self, symbol: str, timeframe: str = '1h') -> Dict:
        """Comprehensive analysis for a symbol"""
        analysis = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'technical': {},
            'sentiment': {},
            'fo_data': {},
            'trade_ideas': []
        }
        
        # Get comprehensive data
        data = self.data_fusion.get_comprehensive_data(symbol, timeframe)
        price_data = data.get('price', pd.DataFrame())
        
        if price_data.empty:
            return {'error': 'No price data available'}
        
        # Technical Analysis
        analysis['technical'] = self._analyze_technical(price_data)
        
        # Sentiment Analysis
        analysis['sentiment'] = self._analyze_sentiment(symbol, data.get('news', pd.DataFrame()))
        
        # F&O Data (if applicable)
        if 'NFO:' in symbol or 'NSE:' in symbol:
            analysis['fo_data'] = self._analyze_fo_data(symbol)
        
        # Generate Trade Ideas
        analysis['trade_ideas'] = self._generate_trade_ideas(symbol, price_data, analysis)
        
        return analysis
    
    def _analyze_technical(self, data: pd.DataFrame) -> Dict:
        """Technical analysis"""
        if len(data) < 50:
            return {}
        
        current_price = float(data['close'].iloc[-1])
        
        # Calculate indicators
        df = self.feature_engineer.create_features(data)
        
        # Trend Analysis
        sma_20 = df['sma_20'].iloc[-1] if 'sma_20' in df.columns else None
        sma_50 = df['sma_50'].iloc[-1] if 'sma_50' in df.columns else None
        sma_200 = df['sma_200'].iloc[-1] if 'sma_200' in df.columns else None
        
        trend = 'Neutral'
        if sma_200 and current_price > sma_200:
            if sma_50 and current_price > sma_50:
                if sma_20 and current_price > sma_20:
                    trend = 'Strongly Bullish'
                else:
                    trend = 'Bullish'
            else:
                trend = 'Weakly Bullish'
        elif sma_200 and current_price < sma_200:
            trend = 'Bearish'
        
        # Momentum
        rsi = df['rsi'].iloc[-1] if 'rsi' in df.columns else 50
        momentum = 'Neutral'
        if rsi > 70:
            momentum = 'Overbought'
        elif rsi < 30:
            momentum = 'Oversold'
        
        # Support and Resistance
        recent_high = df['recent_high'].iloc[-1] if 'recent_high' in df.columns else current_price
        recent_low = df['recent_low'].iloc[-1] if 'recent_low' in df.columns else current_price
        
        # Key Levels
        support = recent_low
        resistance = recent_high
        
        # Bollinger Bands
        bb_upper = df['bb_upper'].iloc[-1] if 'bb_upper' in df.columns else None
        bb_lower = df['bb_lower'].iloc[-1] if 'bb_lower' in df.columns else None
        
        return {
            'current_price': current_price,
            'trend': trend,
            'momentum': momentum,
            'rsi': round(rsi, 2),
            'support': round(support, 2),
            'resistance': round(resistance, 2),
            'sma_20': round(sma_20, 2) if sma_20 else None,
            'sma_50': round(sma_50, 2) if sma_50 else None,
            'sma_200': round(sma_200, 2) if sma_200 else None,
            'bb_upper': round(bb_upper, 2) if bb_upper else None,
            'bb_lower': round(bb_lower, 2) if bb_lower else None,
            'price_above_ema_20': df['price_above_sma20'].iloc[-1] if 'price_above_sma20' in df.columns else None,
            'price_above_ema_50': df['price_above_sma50'].iloc[-1] if 'price_above_sma50' in df.columns else None,
            'price_above_ema_200': df['price_above_sma200'].iloc[-1] if 'price_above_sma200' in df.columns else None
        }
    
    def _analyze_sentiment(self, symbol: str, news_data: pd.DataFrame) -> Dict:
        """Sentiment analysis"""
        sentiment_24h = self.data_fusion.news_ingestion.get_sentiment_24h(symbol)
        
        # Get recent news
        if not news_data.empty:
            recent_news = news_data.head(5)
            headlines = []
            for _, row in recent_news.iterrows():
                headlines.append({
                    'headline': row.get('headline', ''),
                    'sentiment': round(row.get('sentiment_score', 0), 2),
                    'source': row.get('source', ''),
                    'published_at': row.get('published_at', '')
                })
        else:
            headlines = []
        
        # Sentiment score interpretation
        if sentiment_24h > 0.5:
            sentiment_label = 'Very Positive'
        elif sentiment_24h > 0.2:
            sentiment_label = 'Positive'
        elif sentiment_24h < -0.5:
            sentiment_label = 'Very Negative'
        elif sentiment_24h < -0.2:
            sentiment_label = 'Negative'
        else:
            sentiment_label = 'Neutral'
        
        return {
            'sentiment_score_24h': round(sentiment_24h, 3),
            'sentiment_label': sentiment_label,
            'recent_headlines': headlines,
            'news_count_24h': len(news_data) if not news_data.empty else 0
        }
    
    def _analyze_fo_data(self, symbol: str) -> Dict:
        """F&O data analysis"""
        # Placeholder - would fetch from broker API
        return {
            'open_interest': 0,
            'open_interest_change': 0,
            'put_call_ratio': 1.0,
            'implied_volatility': 0.0,
            'note': 'F&O data requires broker API integration'
        }
    
    def _generate_trade_ideas(self, symbol: str, price_data: pd.DataFrame, 
                             analysis: Dict) -> List[Dict]:
        """Generate trade ideas based on analysis"""
        ideas = []
        
        technical = analysis.get('technical', {})
        sentiment = analysis.get('sentiment', {})
        
        current_price = technical.get('current_price', 0)
        support = technical.get('support', 0)
        resistance = technical.get('resistance', 0)
        rsi = technical.get('rsi', 50)
        trend = technical.get('trend', 'Neutral')
        sentiment_score = sentiment.get('sentiment_score_24h', 0)
        
        # Scenario A: Breakout
        if trend in ['Bullish', 'Strongly Bullish'] and sentiment_score > 0.3:
            if current_price > resistance * 0.98:  # Near resistance
                ideas.append({
                    'scenario': 'Breakout',
                    'type': 'LONG',
                    'entry': round(resistance * 1.01, 2) if resistance > 0 else current_price * 1.01,
                    'target_1': round(resistance * 1.03, 2) if resistance > 0 else current_price * 1.03,
                    'target_2': round(resistance * 1.05, 2) if resistance > 0 else current_price * 1.05,
                    'stop_loss': round(resistance * 0.98, 2) if resistance > 0 else current_price * 0.98,
                    'confidence': 'Medium',
                    'reasoning': f'Breakout above resistance with positive sentiment ({sentiment_score:.2f})'
                })
        
        # Scenario B: Dip Buy (Mean Reversion)
        if trend in ['Bullish', 'Strongly Bullish'] and sentiment_score > 0.2:
            if rsi < 40 and current_price <= support * 1.02:  # Near support, oversold
                ideas.append({
                    'scenario': 'Dip Buy',
                    'type': 'LONG',
                    'entry': round(support * 1.01, 2) if support > 0 else current_price * 0.99,
                    'target_1': round(current_price * 1.03, 2),
                    'target_2': round(resistance * 0.98, 2) if resistance > 0 else current_price * 1.05,
                    'stop_loss': round(support * 0.98, 2) if support > 0 else current_price * 0.97,
                    'confidence': 'Medium-High',
                    'reasoning': f'Mean reversion in uptrend. RSI at {rsi:.1f}, sentiment positive'
                })
        
        # Scenario C: News Momentum
        if sentiment_score > 0.7:  # Very positive news
            ideas.append({
                'scenario': 'News Momentum',
                'type': 'LONG',
                'entry': current_price,
                'target_1': round(current_price * 1.015, 2),  # 1.5% target
                'target_2': round(current_price * 1.03, 2),  # 3% target
                'stop_loss': round(current_price * 0.985, 2),  # 1.5% SL
                'confidence': 'High',
                'reasoning': f'Strong positive news sentiment ({sentiment_score:.2f}). Trade momentum'
            })
        
        return ideas
    
    def format_analysis_report(self, analysis: Dict) -> str:
        """Format analysis as readable report"""
        symbol = analysis.get('symbol', 'UNKNOWN')
        technical = analysis.get('technical', {})
        sentiment = analysis.get('sentiment', {})
        trade_ideas = analysis.get('trade_ideas', [])
        
        report = f"""
{'='*60}
COMPREHENSIVE ANALYSIS: {symbol}
{'='*60}

1. TECHNICAL VIEW
   Current Price: ₹{technical.get('current_price', 0):.2f}
   Trend: {technical.get('trend', 'Neutral')}
   Momentum: {technical.get('momentum', 'Neutral')} (RSI: {technical.get('rsi', 50):.1f})
   
   Key Levels:
   - Support: ₹{technical.get('support', 0):.2f}
   - Resistance: ₹{technical.get('resistance', 0):.2f}
   
   Moving Averages:
   - SMA 20: ₹{technical.get('sma_20', 0):.2f}
   - SMA 50: ₹{technical.get('sma_50', 0):.2f}
   - SMA 200: ₹{technical.get('sma_200', 0):.2f}

2. NEWS & SENTIMENT ANALYSIS
   Sentiment Score (24h): {sentiment.get('sentiment_score_24h', 0):.3f} ({sentiment.get('sentiment_label', 'Neutral')})
   News Count (24h): {sentiment.get('news_count_24h', 0)}
   
   Recent Headlines:
"""
        
        for headline in sentiment.get('recent_headlines', [])[:3]:
            report += f"   - {headline['headline'][:60]}... (Sentiment: {headline['sentiment']:.2f})\n"
        
        # F&O Data
        fo_data = analysis.get('fo_data', {})
        if fo_data:
            report += f"""
3. F&O DATA
   Open Interest: {fo_data.get('open_interest', 0)}
   Put-Call Ratio: {fo_data.get('put_call_ratio', 1.0):.2f}
   Implied Volatility: {fo_data.get('implied_volatility', 0):.2f}%
"""
        
        # Trade Ideas
        if trade_ideas:
            report += f"""
4. AI-GENERATED TRADE IDEAS
"""
            for i, idea in enumerate(trade_ideas, 1):
                report += f"""
   Scenario {i}: {idea['scenario']} ({idea['type']})
   Entry: ₹{idea['entry']:.2f}
   Target 1: ₹{idea['target_1']:.2f}
   Target 2: ₹{idea['target_2']:.2f}
   Stop Loss: ₹{idea['stop_loss']:.2f}
   Confidence: {idea['confidence']}
   Reasoning: {idea['reasoning']}
"""
        
        report += f"""
{'='*60}
⚠️  RISK WARNING: Market is volatile. The above is not a recommendation.
Manage your risk. Never risk more than 1-2% of capital per trade.
{'='*60}
"""
        
        return report
    
    def query(self, query: str) -> str:
        """Handle user queries"""
        query_lower = query.lower()
        
        # Extract symbol from query
        symbol = None
        if 'reliance' in query_lower or 'ril' in query_lower:
            symbol = 'NSE:RELIANCE'
        elif 'tcs' in query_lower:
            symbol = 'NSE:TCS'
        elif 'infy' in query_lower or 'infosys' in query_lower:
            symbol = 'NSE:INFY'
        elif 'nifty' in query_lower:
            symbol = 'NFO:NIFTY24JANFUT'
        elif 'btc' in query_lower or 'bitcoin' in query_lower:
            symbol = 'BTCUSDT'
        
        if not symbol:
            # Try to extract any symbol mentioned
            words = query.split()
            for word in words:
                if word.upper() in ['NSE', 'NFO', 'BSE']:
                    symbol = word  # Would need more parsing
        
        if not symbol:
            return "Please specify a symbol (e.g., 'Analysis for RELIANCE' or 'Give me details on NIFTY')"
        
        # Perform analysis
        analysis = self.analyze_symbol(symbol)
        
        if 'error' in analysis:
            return f"Error: {analysis['error']}"
        
        # Format and return report
        return self.format_analysis_report(analysis)



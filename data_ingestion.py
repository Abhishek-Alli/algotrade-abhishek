"""
Data Ingestion & Fusion Module
Collects data from multiple sources: Price, News, Sentiment, Macro, On-chain
"""
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from abc import ABC, abstractmethod
import sqlite3
import json
from database import get_db

logger = logging.getLogger(__name__)


class DataIngestion(ABC):
    """Base class for data ingestion"""
    
    @abstractmethod
    def fetch_data(self, symbol: str, **kwargs) -> pd.DataFrame:
        """Fetch data from source"""
        pass


class PriceDataIngestion(DataIngestion):
    """Fetch OHLCV data from multiple sources"""
    
    def __init__(self, api_client=None):
        self.api_client = api_client
        self.db = get_db()
        self.db_type = self.db.db_type
    
    def fetch_data(self, symbol: str, interval: str = '1h', limit: int = 100, 
                   source: str = 'broker') -> pd.DataFrame:
        """Fetch OHLCV data"""
        if source == 'broker' and self.api_client:
            try:
                klines = self.api_client.get_klines(symbol, interval, limit)
                df = self._format_klines(klines, symbol, interval)
                self._store_data(df, symbol, interval)
                return df
            except Exception as e:
                logger.error(f"Error fetching from broker: {e}")
        
        # Fallback to database
        return self._fetch_from_db(symbol, interval, limit)
    
    def _format_klines(self, klines: List, symbol: str, interval: str) -> pd.DataFrame:
        """Format klines data to DataFrame"""
        if isinstance(klines[0], dict):
            # Binance format
            df = pd.DataFrame(klines)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol
            df['timeframe'] = interval
        else:
            # Kite format (list of lists)
            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['date'])
            df['symbol'] = symbol
            df['timeframe'] = interval
        
        return df[['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'timeframe']]
    
    def _store_data(self, df: pd.DataFrame, symbol: str, interval: str):
        """Store data in database"""
        if df.empty:
            return
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            for _, row in df.iterrows():
                if self.db_type == 'postgresql':
                    query = '''
                        INSERT INTO ohlcv_data (symbol, timestamp, open, high, low, close, volume, timeframe)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, timestamp, timeframe) 
                        DO UPDATE SET 
                            open = EXCLUDED.open,
                            high = EXCLUDED.high,
                            low = EXCLUDED.low,
                            close = EXCLUDED.close,
                            volume = EXCLUDED.volume
                    '''
                    cursor.execute(query, (
                        str(row.get('symbol', symbol)),
                        pd.to_datetime(row['timestamp']),
                        float(row.get('open', 0)),
                        float(row.get('high', 0)),
                        float(row.get('low', 0)),
                        float(row.get('close', 0)),
                        float(row.get('volume', 0)),
                        str(interval)
                    ))
                else:
                    # SQLite
                    query = '''
                        INSERT OR REPLACE INTO ohlcv_data 
                        (symbol, timestamp, open, high, low, close, volume, timeframe)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    '''
                    cursor.execute(query, (
                        str(row.get('symbol', symbol)),
                        str(row['timestamp']),
                        float(row.get('open', 0)),
                        float(row.get('high', 0)),
                        float(row.get('low', 0)),
                        float(row.get('close', 0)),
                        float(row.get('volume', 0)),
                        str(interval)
                    ))
            
            conn.commit()
            logger.debug(f"Stored {len(df)} records for {symbol} at {interval}")
            
        except Exception as e:
            logger.error(f"Error storing data: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn and self.db_type == 'postgresql':
                self.db.return_connection(conn)
            elif conn and self.db_type == 'sqlite':
                pass  # SQLite connection stays open
    
    def _fetch_from_db(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        """Fetch data from database"""
        try:
            conn = self.db.get_connection()
            
            if self.db_type == 'postgresql':
                query = '''
                    SELECT symbol, timestamp, open, high, low, close, volume, timeframe
                    FROM ohlcv_data 
                    WHERE symbol = %s AND timeframe = %s
                    ORDER BY timestamp DESC LIMIT %s
                '''
                df = pd.read_sql_query(query, conn, params=(symbol, interval, limit))
            else:
                # SQLite
                query = '''
                    SELECT * FROM ohlcv_data 
                    WHERE symbol = ? AND timeframe = ?
                    ORDER BY timestamp DESC LIMIT ?
                '''
                df = pd.read_sql_query(query, conn, params=(symbol, interval, limit))
            
            if not df.empty and 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching from DB: {e}")
            return pd.DataFrame()
        finally:
            if conn and self.db_type == 'postgresql':
                self.db.return_connection(conn)


class NewsDataIngestion(DataIngestion):
    """Fetch news and perform sentiment analysis"""
    
    def __init__(self, news_api_key: str = None):
        self.news_api_key = news_api_key
        self.db = get_db()
        self.db_type = self.db.db_type
    
    def fetch_data(self, symbol: str, query: str = None, days: int = 7) -> pd.DataFrame:
        """Fetch news data"""
        # Try NewsAPI first
        if self.news_api_key:
            try:
                news = self._fetch_from_newsapi(symbol, query, days)
                if not news.empty:
                    news['sentiment_score'] = news['headline'].apply(self._analyze_sentiment)
                    self._store_news(news)
                    return news
            except Exception as e:
                logger.error(f"Error fetching from NewsAPI: {e}")
        
        # Fallback to database
        return self._fetch_from_db(symbol, days)
    
    def _fetch_from_newsapi(self, symbol: str, query: str, days: int) -> pd.DataFrame:
        """Fetch from NewsAPI"""
        if not self.news_api_key:
            return pd.DataFrame()
        
        url = 'https://newsapi.org/v2/everything'
        params = {
            'q': query or symbol,
            'apiKey': self.news_api_key,
            'from': (datetime.now() - timedelta(days=days)).isoformat(),
            'sortBy': 'publishedAt',
            'language': 'en'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for article in data.get('articles', []):
                articles.append({
                    'symbol': symbol,
                    'headline': article.get('title', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'published_at': article.get('publishedAt', ''),
                    'content': article.get('description', ''),
                    'url': article.get('url', '')
                })
            
            return pd.DataFrame(articles)
        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
            return pd.DataFrame()
    
    def _analyze_sentiment(self, text: str) -> float:
        """Simple sentiment analysis (returns -1 to +1)"""
        if not text:
            return 0.0
        
        # Simple keyword-based sentiment (can be replaced with NLP model)
        positive_words = ['profit', 'gain', 'rise', 'surge', 'growth', 'positive', 'bullish', 'up', 'increase']
        negative_words = ['loss', 'fall', 'decline', 'drop', 'negative', 'bearish', 'down', 'decrease', 'crash']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count == 0 and negative_count == 0:
            return 0.0
        
        score = (positive_count - negative_count) / (positive_count + negative_count + 1)
        return np.clip(score, -1.0, 1.0)
    
    def _store_news(self, df: pd.DataFrame):
        """Store news in database"""
        if df.empty:
            return
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            for _, row in df.iterrows():
                if self.db_type == 'postgresql':
                    query = '''
                        INSERT INTO news_data (symbol, headline, source, published_at, sentiment_score, content, url)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    '''
                    cursor.execute(query, (
                        str(row.get('symbol', '')),
                        str(row.get('headline', '')),
                        str(row.get('source', '')),
                        pd.to_datetime(row.get('published_at', datetime.now())),
                        float(row.get('sentiment_score', 0.0)),
                        str(row.get('content', '')),
                        str(row.get('url', ''))
                    ))
                else:
                    # SQLite
                    query = '''
                        INSERT INTO news_data (symbol, headline, source, published_at, sentiment_score, content, url)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    '''
                    cursor.execute(query, (
                        str(row.get('symbol', '')),
                        str(row.get('headline', '')),
                        str(row.get('source', '')),
                        str(row.get('published_at', datetime.now())),
                        float(row.get('sentiment_score', 0.0)),
                        str(row.get('content', '')),
                        str(row.get('url', ''))
                    ))
            
            conn.commit()
            logger.debug(f"Stored {len(df)} news articles")
            
        except Exception as e:
            logger.error(f"Error storing news: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn and self.db_type == 'postgresql':
                self.db.return_connection(conn)
    
    def _fetch_from_db(self, symbol: str, days: int) -> pd.DataFrame:
        """Fetch news from database"""
        try:
            conn = self.db.get_connection()
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if self.db_type == 'postgresql':
                query = '''
                    SELECT * FROM news_data 
                    WHERE symbol = %s AND published_at >= %s
                    ORDER BY published_at DESC
                '''
                df = pd.read_sql_query(query, conn, params=(symbol, cutoff_date))
            else:
                # SQLite
                query = '''
                    SELECT * FROM news_data 
                    WHERE symbol = ? AND published_at >= ?
                    ORDER BY published_at DESC
                '''
                df = pd.read_sql_query(query, conn, params=(symbol, cutoff_date.isoformat()))
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching news from DB: {e}")
            return pd.DataFrame()
        finally:
            if conn and self.db_type == 'postgresql':
                self.db.return_connection(conn)
    
    def get_sentiment_24h(self, symbol: str) -> float:
        """Get average sentiment score for last 24 hours"""
        news = self.fetch_data(symbol, days=1)
        if news.empty:
            return 0.0
        return news['sentiment_score'].mean()


class SentimentDataIngestion(DataIngestion):
    """Fetch social media sentiment (Twitter, Reddit)"""
    
    def __init__(self, twitter_api_key: str = None):
        self.twitter_api_key = twitter_api_key
        self.db = get_db()
        self.db_type = self.db.db_type
    
    def fetch_data(self, symbol: str, platform: str = 'twitter', 
                   hours: int = 24) -> pd.DataFrame:
        """Fetch sentiment data from social platforms"""
        # Placeholder - would integrate with Twitter/Reddit APIs
        # For now, return empty DataFrame
        logger.warning(f"Sentiment data ingestion for {platform} not fully implemented")
        return pd.DataFrame()
    
    def get_crypto_fear_greed_index(self) -> int:
        """Get Crypto Fear & Greed Index (0-100)"""
        try:
            # Using alternative.me API (free)
            url = 'https://api.alternative.me/fng/'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('data'):
                return int(data['data'][0]['value'])
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed Index: {e}")
        return 50  # Neutral


class MacroDataIngestion(DataIngestion):
    """Fetch macroeconomic data"""
    
    def __init__(self, alpha_vantage_key: str = None):
        self.alpha_vantage_key = alpha_vantage_key
    
    def fetch_data(self, indicator: str = 'GDP', **kwargs) -> pd.DataFrame:
        """Fetch macroeconomic indicators"""
        # Placeholder for macro data fetching
        logger.warning("Macro data ingestion not fully implemented")
        return pd.DataFrame()
    
    def get_interest_rate(self, country: str = 'IN') -> float:
        """Get current interest rate"""
        # Placeholder - would fetch from RBI/central bank APIs
        return 6.5  # Default


class OnChainDataIngestion(DataIngestion):
    """Fetch cryptocurrency on-chain data"""
    
    def __init__(self):
        self.db_path = 'onchain_data.db'
    
    def fetch_data(self, symbol: str = 'BTC', **kwargs) -> pd.DataFrame:
        """Fetch on-chain metrics"""
        # Placeholder for on-chain data
        logger.warning("On-chain data ingestion not fully implemented")
        return pd.DataFrame()
    
    def get_exchange_reserves(self, symbol: str = 'BTC') -> Dict:
        """Get exchange reserve data"""
        # Placeholder - would use Glassnode or similar API
        return {'balance': 0, 'change_24h': 0}


class DataFusion:
    """Fuse data from multiple sources"""
    
    def __init__(self):
        self.price_ingestion = PriceDataIngestion()
        self.news_ingestion = NewsDataIngestion()
        self.sentiment_ingestion = SentimentDataIngestion()
        self.macro_ingestion = MacroDataIngestion()
        self.onchain_ingestion = OnChainDataIngestion()
    
    def get_comprehensive_data(self, symbol: str, timeframe: str = '1h') -> Dict:
        """Get all available data for a symbol"""
        data = {
            'price': self.price_ingestion.fetch_data(symbol, interval=timeframe),
            'news': self.news_ingestion.fetch_data(symbol, days=7),
            'sentiment_24h': self.news_ingestion.get_sentiment_24h(symbol),
            'fear_greed_index': self.sentiment_ingestion.get_crypto_fear_greed_index() if symbol in ['BTC', 'ETH'] else None,
            'timestamp': datetime.now()
        }
        return data


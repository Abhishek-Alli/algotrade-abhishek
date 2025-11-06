"""
Data Collection Service
Automatically collects and stores data every minute for all symbols
Runs in background as a daemon service
"""
import time
import threading
import logging
from datetime import datetime
from typing import List, Dict
import pandas as pd
from data_ingestion import (
    PriceDataIngestion, NewsDataIngestion, 
    SentimentDataIngestion, DataFusion
)
from config import Config

logger = logging.getLogger(__name__)


class DataCollector:
    """Background service for continuous data collection"""
    
    def __init__(self, symbols: List[str] = None, interval_seconds: int = 60, api_client=None):
        """
        Initialize data collector
        
        Args:
            symbols: List of symbols to monitor (default from config)
            interval_seconds: Collection interval in seconds (default 60 = 1 minute)
            api_client: API client for fetching data (optional)
        """
        self.symbols = symbols or [Config.SYMBOL]
        self.interval_seconds = interval_seconds
        self.is_running = False
        self.thread = None
        self.api_client = api_client
        
        # Initialize data ingestion modules
        self.price_ingestion = PriceDataIngestion(api_client=api_client)
        self.news_ingestion = NewsDataIngestion(news_api_key=Config.NEWS_API_KEY)
        self.sentiment_ingestion = SentimentDataIngestion()
        self.data_fusion = DataFusion()
        
        logger.info(f"Data Collector initialized for {len(self.symbols)} symbols")
        logger.info(f"Collection interval: {interval_seconds} seconds")
    
    def collect_price_data(self, symbol: str, timeframes: List[str] = None):
        """Collect price data for a symbol"""
        if timeframes is None:
            timeframes = ['1m', '5m', '15m', '1h', '1d']
        
        try:
            for timeframe in timeframes:
                try:
                    # Fetch latest data
                    df = self.price_ingestion.fetch_data(
                        symbol=symbol,
                        interval=timeframe,
                        limit=100,
                        source='broker'
                    )
                    
                    if not df.empty:
                        # Store in database
                        self.price_ingestion._store_data(df, symbol, timeframe)
                        logger.debug(f"Collected {timeframe} data for {symbol}: {len(df)} candles")
                    else:
                        logger.warning(f"No data fetched for {symbol} at {timeframe}")
                        
                except Exception as e:
                    logger.error(f"Error collecting {timeframe} data for {symbol}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in price data collection for {symbol}: {e}")
    
    def collect_news_data(self, symbol: str):
        """Collect news data for a symbol"""
        try:
            # Fetch news from last 1 hour
            news_df = self.news_ingestion.fetch_data(
                symbol=symbol,
                days=1
            )
            
            if not news_df.empty:
                # News already stored in fetch_data method
                logger.debug(f"Collected {len(news_df)} news articles for {symbol}")
            else:
                logger.debug(f"No new news articles for {symbol}")
                
        except Exception as e:
            logger.error(f"Error collecting news for {symbol}: {e}")
    
    def collect_sentiment_data(self, symbol: str):
        """Collect sentiment data for a symbol"""
        try:
            # Get Fear & Greed Index for crypto
            if symbol in ['BTC', 'ETH', 'BTCUSDT', 'ETHUSDT']:
                fng_index = self.sentiment_ingestion.get_crypto_fear_greed_index()
                logger.debug(f"Fear & Greed Index for {symbol}: {fng_index}")
            
            # Collect social media sentiment (if implemented)
            sentiment_df = self.sentiment_ingestion.fetch_data(symbol, hours=1)
            
        except Exception as e:
            logger.error(f"Error collecting sentiment for {symbol}: {e}")
    
    def collect_all_data(self, symbol: str):
        """Collect all types of data for a symbol"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"[{timestamp}] Collecting data for {symbol}...")
        
        # Collect price data (multiple timeframes)
        self.collect_price_data(symbol)
        
        # Collect news data
        self.collect_news_data(symbol)
        
        # Collect sentiment data
        self.collect_sentiment_data(symbol)
        
        logger.info(f"[{timestamp}] Data collection completed for {symbol}")
    
    def run_collection_cycle(self):
        """Run one complete collection cycle for all symbols"""
        for symbol in self.symbols:
            try:
                self.collect_all_data(symbol)
            except Exception as e:
                logger.error(f"Error in collection cycle for {symbol}: {e}")
    
    def start(self):
        """Start the data collection service"""
        if self.is_running:
            logger.warning("Data collector is already running")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"Data Collector started (interval: {self.interval_seconds}s)")
    
    def _run(self):
        """Main collection loop (runs in background thread)"""
        logger.info("Data Collector background thread started")
        
        while self.is_running:
            try:
                # Run collection cycle
                self.run_collection_cycle()
                
                # Wait for next interval
                time.sleep(self.interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Data Collector interrupted")
                self.is_running = False
                break
            except Exception as e:
                logger.error(f"Error in data collection loop: {e}")
                time.sleep(self.interval_seconds)
    
    def stop(self):
        """Stop the data collection service"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Data Collector stopped")
    
    def get_stored_data_stats(self) -> Dict:
        """Get statistics about stored data"""
        from database import get_db
        
        stats = {}
        db = get_db()
        
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Count records per symbol and timeframe
            if db.db_type == 'postgresql':
                query = '''
                    SELECT symbol, timeframe, COUNT(*) as count, 
                           MIN(timestamp)::text as first, MAX(timestamp)::text as last
                    FROM ohlcv_data
                    GROUP BY symbol, timeframe
                '''
            else:
                query = '''
                    SELECT symbol, timeframe, COUNT(*) as count, 
                           MIN(timestamp) as first, MAX(timestamp) as last
                    FROM ohlcv_data
                    GROUP BY symbol, timeframe
                '''
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            stats['price_data'] = []
            for row in results:
                stats['price_data'].append({
                    'symbol': row[0],
                    'timeframe': row[1],
                    'count': row[2],
                    'first_record': row[3],
                    'last_record': row[4]
                })
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
        finally:
            if conn and db.db_type == 'postgresql':
                db.return_connection(conn)
        
        # News data stats
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if db.db_type == 'postgresql':
                query = '''
                    SELECT symbol, COUNT(*) as count,
                           MIN(published_at)::text as first, MAX(published_at)::text as last
                    FROM news_data
                    GROUP BY symbol
                '''
            else:
                query = '''
                    SELECT symbol, COUNT(*) as count,
                           MIN(published_at) as first, MAX(published_at) as last
                    FROM news_data
                    GROUP BY symbol
                '''
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            stats['news_data'] = []
            for row in results:
                stats['news_data'].append({
                    'symbol': row[0],
                    'count': row[1],
                    'first_record': row[2],
                    'last_record': row[3]
                })
            
        except Exception as e:
            logger.error(f"Error getting news stats: {e}")
        finally:
            if conn and db.db_type == 'postgresql':
                db.return_connection(conn)
        
        return stats


class DataCollectorService:
    """Service wrapper for easy management"""
    
    def __init__(self, symbols: List[str] = None, interval_seconds: int = 60, api_client=None):
        self.collector = DataCollector(symbols=symbols, interval_seconds=interval_seconds, api_client=api_client)
    
    def start(self):
        """Start the service"""
        self.collector.start()
    
    def stop(self):
        """Stop the service"""
        self.collector.stop()
    
    def get_stats(self):
        """Get data statistics"""
        return self.collector.get_stored_data_stats()
    
    def add_symbol(self, symbol: str):
        """Add a new symbol to monitor"""
        if symbol not in self.collector.symbols:
            self.collector.symbols.append(symbol)
            logger.info(f"Added {symbol} to monitoring list")
    
    def remove_symbol(self, symbol: str):
        """Remove a symbol from monitoring"""
        if symbol in self.collector.symbols:
            self.collector.symbols.remove(symbol)
            logger.info(f"Removed {symbol} from monitoring list")


def main():
    """Standalone data collector service"""
    import argparse
    from api_client import ZerodhaKiteClient, BinanceClient, DeltaExchangeClient
    
    parser = argparse.ArgumentParser(description='Data Collection Service')
    parser.add_argument('--symbols', type=str, nargs='+', 
                       default=[Config.SYMBOL],
                       help='Symbols to monitor')
    parser.add_argument('--interval', type=int, default=60,
                       help='Collection interval in seconds (default: 60)')
    parser.add_argument('--stats', action='store_true',
                       help='Show stored data statistics')
    parser.add_argument('--broker', type=str, default='binance',
                       choices=['zerodha', 'binance', 'delta'],
                       help='Broker to use for data collection')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize API client
    api_client = None
    if args.broker == 'zerodha':
        api_client = ZerodhaKiteClient(
            api_key=Config.API_KEY,
            api_secret=Config.API_SECRET,
            access_token=Config.API_PASSPHRASE
        )
    elif args.broker == 'binance':
        api_client = BinanceClient(testnet=Config.TESTNET)
    elif args.broker == 'delta':
        api_client = DeltaExchangeClient(
            api_key=Config.API_KEY,
            api_secret=Config.API_SECRET,
            testnet=Config.DELTA_TESTNET
        )
    
    collector = DataCollector(
        symbols=args.symbols,
        interval_seconds=args.interval,
        api_client=api_client
    )
    
    if args.stats:
        # Show statistics and exit
        stats = collector.get_stored_data_stats()
        print("\n" + "="*60)
        print("STORED DATA STATISTICS")
        print("="*60)
        
        print("\nPrice Data:")
        for item in stats.get('price_data', []):
            print(f"  {item['symbol']} ({item['timeframe']}): "
                  f"{item['count']} records, "
                  f"First: {item['first_record']}, "
                  f"Last: {item['last_record']}")
        
        print("\nNews Data:")
        for item in stats.get('news_data', []):
            print(f"  {item['symbol']}: {item['count']} articles, "
                  f"First: {item['first_record']}, "
                  f"Last: {item['last_record']}")
        
        print("="*60 + "\n")
        return
    
    # Start collection service
    print("="*60)
    print(f"Data Collection Service")
    print(f"Monitoring: {', '.join(args.symbols)}")
    print(f"Interval: {args.interval} seconds")
    print("="*60)
    print("Press Ctrl+C to stop\n")
    
    try:
        collector.start()
        
        # Keep main thread alive
        while collector.is_running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping data collector...")
        collector.stop()
        print("Data collector stopped.")


if __name__ == "__main__":
    main()


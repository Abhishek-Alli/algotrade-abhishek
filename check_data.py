"""
Check stored data in databases (PostgreSQL or SQLite)
"""
import pandas as pd
from datetime import datetime
import argparse
from database import get_db


def check_price_data(symbol=None):
    """Check stored price data"""
    try:
        db = get_db()
        conn = db.get_connection()
        
        if db.db_type == 'postgresql':
            query = '''
                SELECT symbol, timeframe, COUNT(*) as count,
                       MIN(timestamp)::text as first_record,
                       MAX(timestamp)::text as last_record,
                       COUNT(DISTINCT DATE(timestamp)) as days
                FROM ohlcv_data
            '''
            if symbol:
                query += f" WHERE symbol = '{symbol}'"
            query += ' GROUP BY symbol, timeframe ORDER BY symbol, timeframe'
        else:
            # SQLite
            query = '''
                SELECT symbol, timeframe, COUNT(*) as count,
                       MIN(timestamp) as first_record,
                       MAX(timestamp) as last_record,
                       COUNT(DISTINCT DATE(timestamp)) as days
                FROM ohlcv_data
            '''
            if symbol:
                query += f" WHERE symbol = '{symbol}'"
            query += ' GROUP BY symbol, timeframe ORDER BY symbol, timeframe'
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("No price data found in database.")
            return
        
        print("\n" + "="*80)
        print("PRICE DATA (OHLCV)")
        print("="*80)
        print(df.to_string(index=False))
        print("="*80)
        
        # Show recent records
        if symbol:
            if db.db_type == 'postgresql':
                query = f'''
                    SELECT symbol, timestamp, open, high, low, close, volume, timeframe
                    FROM ohlcv_data 
                    WHERE symbol = '{symbol}'
                    ORDER BY timestamp DESC LIMIT 10
                '''
            else:
                query = f'''
                    SELECT * FROM ohlcv_data 
                    WHERE symbol = '{symbol}'
                    ORDER BY timestamp DESC LIMIT 10
                '''
            recent = pd.read_sql_query(query, conn)
            
            if not recent.empty:
                print(f"\nRecent 10 records for {symbol}:")
                print(recent[['timestamp', 'open', 'high', 'low', 'close', 'volume']].to_string(index=False))
        
        finally:
            if conn and db.db_type == 'postgresql':
                db.return_connection(conn)
        
    except Exception as e:
        print(f"Error checking price data: {e}")


def check_news_data(symbol=None):
    """Check stored news data"""
    try:
        db = get_db()
        conn = db.get_connection()
        
        if db.db_type == 'postgresql':
            query = '''
                SELECT symbol, COUNT(*) as count,
                       MIN(published_at)::text as first_record,
                       MAX(published_at)::text as last_record,
                       AVG(sentiment_score) as avg_sentiment
                FROM news_data
            '''
            if symbol:
                query += f" WHERE symbol = '{symbol}'"
            query += ' GROUP BY symbol ORDER BY symbol'
        else:
            query = '''
                SELECT symbol, COUNT(*) as count,
                       MIN(published_at) as first_record,
                       MAX(published_at) as last_record,
                       AVG(sentiment_score) as avg_sentiment
                FROM news_data
            '''
            if symbol:
                query += f" WHERE symbol = '{symbol}'"
            query += ' GROUP BY symbol ORDER BY symbol'
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("No news data found in database.")
            return
        
        print("\n" + "="*80)
        print("NEWS DATA")
        print("="*80)
        print(df.to_string(index=False))
        print("="*80)
        
        # Show recent headlines
        if symbol:
            query = f'''
                SELECT headline, source, published_at, sentiment_score
                FROM news_data 
                WHERE symbol = '{symbol}'
                ORDER BY published_at DESC LIMIT 5
            '''
            recent = pd.read_sql_query(query, conn)
            
            if not recent.empty:
                print(f"\nRecent 5 headlines for {symbol}:")
                for _, row in recent.iterrows():
                    print(f"  [{row['sentiment_score']:.2f}] {row['headline'][:60]}...")
                    print(f"    Source: {row['source']}, Date: {row['published_at']}")
        
        finally:
            if conn and db.db_type == 'postgresql':
                db.return_connection(conn)
        
    except Exception as e:
        print(f"Error checking news data: {e}")


def main():
    parser = argparse.ArgumentParser(description='Check stored data')
    parser.add_argument('--symbol', type=str, help='Symbol to check')
    parser.add_argument('--type', type=str, choices=['price', 'news', 'all'],
                       default='all', help='Type of data to check')
    
    args = parser.parse_args()
    
    print(f"\nData Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.type in ['price', 'all']:
        check_price_data(symbol=args.symbol)
    
    if args.type in ['news', 'all']:
        check_news_data(symbol=args.symbol)
    
    print("\n")


if __name__ == "__main__":
    main()


"""
Configuration file for trading software
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Credentials
    API_KEY = os.getenv('API_KEY', '')
    API_SECRET = os.getenv('API_SECRET', '')
    API_PASSPHRASE = os.getenv('API_PASSPHRASE', '')
    
    # Broker/Exchange settings
    BROKER = os.getenv('BROKER', 'binance')  # binance, coinbase, delta, zerodha, angelone
    BASE_URL = os.getenv('BASE_URL', 'https://api.binance.com')
    TESTNET = os.getenv('TESTNET', 'true').lower() == 'true'
    
    # Delta Exchange Settings
    DELTA_TESTNET = os.getenv('DELTA_TESTNET', 'false').lower() == 'true'
    
    # Trading settings
    SYMBOL = os.getenv('SYMBOL', 'BTCUSDT')
    QUANTITY = float(os.getenv('QUANTITY', '0.001'))
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '0.01'))
    
    # Indian Stock Market Settings
    MARKET = os.getenv('MARKET', 'NSE')  # NSE or BSE
    PRODUCT_TYPE = os.getenv('PRODUCT_TYPE', 'MIS')  # MIS, CNC, NRML for F&O
    EXCHANGE = os.getenv('EXCHANGE', 'NSE')  # NSE, BSE, NFO (for F&O)
    VARIETY = os.getenv('VARIETY', 'regular')  # regular, amo, ioc, fok
    
    # Risk management
    MAX_DAILY_LOSS = float(os.getenv('MAX_DAILY_LOSS', '100.0'))
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '2.0'))
    TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '3.0'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'trading.log')
    
    # Data Sources API Keys
    NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
    ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY', '')
    TWITTER_API_KEY = os.getenv('TWITTER_API_KEY', '')
    
    # PostgreSQL Database Settings
    DB_TYPE = os.getenv('DB_TYPE', 'postgresql')  # postgresql or sqlite
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'trading_db')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    # Full connection string (optional - agar DB_URL set hai to use hoga)
    DB_URL = os.getenv('DB_URL', '')  # Empty = use individual settings above


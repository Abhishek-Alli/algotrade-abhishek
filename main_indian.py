"""
Main entry point for Indian Stock Market trading
Supports NSE/BSE stocks and F&O (Futures & Options)
"""
import sys
import signal
from trading_engine import TradingEngine
from strategy import MovingAverageStrategy, RSIMomentumStrategy, BollingerBandsStrategy
from api_client import ZerodhaKiteClient, AngelOneClient
from config import Config
from indian_market_utils import is_market_open, format_indian_symbol
import logging

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main function for Indian market trading"""
    print("=" * 50)
    print("Indian Stock Market Trading Software - Starting...")
    print("=" * 50)
    
    # Check if market is open
    if not is_market_open():
        logger.warning("Market is currently closed. Software will wait for market hours.")
        print("Note: Market timings are 9:15 AM to 3:30 PM IST (Monday-Friday)")
    
    # Initialize API client based on broker
    broker = Config.BROKER.lower()
    
    if broker == 'zerodha' or broker == 'kite':
        try:
            # Zerodha Kite Connect
            # Note: You need to get access_token first using request_token
            # For first time setup, use get_access_token(request_token) method
            api_client = ZerodhaKiteClient(
                api_key=Config.API_KEY,
                api_secret=Config.API_SECRET,
                access_token=Config.API_PASSPHRASE  # Access token stored here
            )
            logger.info("Zerodha Kite Connect client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Zerodha client: {e}")
            logger.info("Note: For first time setup, generate access_token using request_token")
            sys.exit(1)
    
    elif broker == 'angelone' or broker == 'angel':
        try:
            # Angel One SmartAPI
            # Note: You need client_id, password, and TOTP for authentication
            api_client = AngelOneClient(
                api_key=Config.API_KEY,
                client_id=Config.API_SECRET,
                password=Config.API_PASSPHRASE  # Password stored here
            )
            logger.info("Angel One SmartAPI client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Angel One client: {e}")
            sys.exit(1)
    
    else:
        logger.error(f"Unsupported broker: {broker}")
        logger.info("Supported brokers: 'zerodha', 'angelone'")
        sys.exit(1)
    
    # Initialize strategy
    strategy = MovingAverageStrategy(fast_period=10, slow_period=30)
    # strategy = RSIMomentumStrategy()
    # strategy = BollingerBandsStrategy()
    
    logger.info(f"Strategy: {strategy.name}")
    
    # Format symbol for Indian market
    symbol = format_indian_symbol(Config.SYMBOL, exchange=Config.EXCHANGE)
    logger.info(f"Trading symbol: {symbol}")
    logger.info(f"Exchange: {Config.EXCHANGE}")
    logger.info(f"Product Type: {Config.PRODUCT_TYPE}")
    
    # Initialize trading engine
    engine = TradingEngine(strategy=strategy, api_client=api_client)
    engine.symbol = symbol  # Update symbol for Indian market format
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        engine.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start trading
    try:
        # Check market hours before starting
        if is_market_open():
            logger.info("Market is open. Starting trading engine...")
            engine.run(interval=60)  # Run every 60 seconds
        else:
            logger.info("Market is closed. Waiting for market hours...")
            # Wait until market opens
            import time
            while not is_market_open():
                time.sleep(60)  # Check every minute
            logger.info("Market is now open. Starting trading engine...")
            engine.run(interval=60)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        engine.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()



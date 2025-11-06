"""
Main entry point for trading software
"""
import sys
import signal
from trading_engine import TradingEngine
from strategy import MovingAverageStrategy, RSIMomentumStrategy, BollingerBandsStrategy
from api_client import BinanceClient, DeltaExchangeClient
from config import Config
import logging

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main function"""
    print("=" * 50)
    print("Trading Software - Starting...")
    print("=" * 50)
    
    # Initialize API client based on broker
    broker = Config.BROKER.lower()
    try:
        if broker == 'delta' or broker == 'deltaexchange':
            api_client = DeltaExchangeClient(
                api_key=Config.API_KEY,
                api_secret=Config.API_SECRET,
                testnet=Config.DELTA_TESTNET
            )
            logger.info(f"Delta Exchange API client initialized (Testnet: {Config.DELTA_TESTNET})")
        else:
            # Default to Binance
            api_client = BinanceClient(testnet=Config.TESTNET)
            logger.info(f"Binance API client initialized (Testnet: {Config.TESTNET})")
    except Exception as e:
        logger.error(f"Failed to initialize API client: {e}")
        sys.exit(1)
    
    # Initialize strategy (you can change this)
    strategy = MovingAverageStrategy(fast_period=10, slow_period=30)
    # strategy = RSIMomentumStrategy()
    # strategy = BollingerBandsStrategy()
    
    logger.info(f"Strategy: {strategy.name}")
    
    # Initialize trading engine
    engine = TradingEngine(strategy=strategy, api_client=api_client)
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        engine.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start trading
    try:
        engine.run(interval=60)  # Run every 60 seconds
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        engine.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()


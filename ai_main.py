"""
AI-Powered Trading System Main Entry Point
Integrates data ingestion, feature engineering, ML models, and advanced strategies
"""
import sys
import signal
import logging
import time
from datetime import datetime
from trading_engine import TradingEngine
from advanced_strategies import (
    NewsMomentumStrategy, MeanReversionStrategy, 
    CryptoOnChainStrategy, MLBasedStrategy
)
from ml_models import PriceDirectionModel
from data_ingestion import DataFusion
from feature_engineering import FeatureEngineer
from ai_analysis import AIAnalyst
from api_client import ZerodhaKiteClient, AngelOneClient, BinanceClient, DeltaExchangeClient
from config import Config
from data_collector import DataCollector

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class AITradingSystem:
    """AI-powered trading system"""
    
    def __init__(self, broker: str = 'zerodha', strategy_type: str = 'ml'):
        self.broker = broker.lower()
        self.strategy_type = strategy_type.lower()
        self.api_client = self._initialize_api_client()
        self.data_fusion = DataFusion()
        self.feature_engineer = FeatureEngineer()
        self.ai_analyst = AIAnalyst(api_client=self.api_client)
        self.strategy = self._initialize_strategy()
        self.engine = TradingEngine(
            strategy=self.strategy, 
            api_client=self.api_client,
            enable_data_collection=True  # Enable automatic data collection
        )
        self.data_collector = DataCollector(
            symbols=[Config.SYMBOL], 
            interval_seconds=60,
            api_client=self.api_client
        )
        self.is_running = False
    
    def _initialize_api_client(self):
        """Initialize API client based on broker"""
        if self.broker == 'zerodha':
            return ZerodhaKiteClient(
                api_key=Config.API_KEY,
                api_secret=Config.API_SECRET,
                access_token=Config.API_PASSPHRASE
            )
        elif self.broker == 'angelone':
            return AngelOneClient(
                api_key=Config.API_KEY,
                client_id=Config.API_SECRET,
                password=Config.API_PASSPHRASE
            )
        elif self.broker == 'binance':
            return BinanceClient(testnet=Config.TESTNET)
        elif self.broker == 'delta' or self.broker == 'deltaexchange':
            return DeltaExchangeClient(
                api_key=Config.API_KEY,
                api_secret=Config.API_SECRET,
                testnet=Config.DELTA_TESTNET
            )
        else:
            logger.error(f"Unsupported broker: {self.broker}")
            return None
    
    def _initialize_strategy(self):
        """Initialize strategy based on type"""
        if self.strategy_type == 'news_momentum':
            return NewsMomentumStrategy()
        elif self.strategy_type == 'mean_reversion':
            return MeanReversionStrategy()
        elif self.strategy_type == 'crypto_onchain':
            return CryptoOnChainStrategy()
        elif self.strategy_type == 'ml':
            # Initialize ML model
            model = PriceDirectionModel(model_type='xgboost')
            return MLBasedStrategy(model=model)
        else:
            logger.warning(f"Unknown strategy type: {self.strategy_type}, using ML")
            model = PriceDirectionModel(model_type='xgboost')
            return MLBasedStrategy(model=model)
    
    def train_ml_model(self, symbol: str, timeframe: str = '1h', days: int = 90):
        """Train ML model on historical data"""
        logger.info(f"Training ML model for {symbol}...")
        
        if not isinstance(self.strategy, MLBasedStrategy):
            logger.warning("Strategy is not ML-based")
            return
        
        # Fetch historical data
        data_fusion = DataFusion()
        price_data = data_fusion.price_ingestion.fetch_data(
            symbol, interval=timeframe, limit=days * 24  # Approximate
        )
        
        if price_data.empty:
            logger.error("No historical data available for training")
            return
        
        # Train model
        self.strategy.train(price_data, forward_periods=5)
        logger.info("ML model training completed")
    
    def analyze_symbol(self, symbol: str):
        """Perform comprehensive analysis on a symbol"""
        logger.info(f"Analyzing {symbol}...")
        analysis = self.ai_analyst.analyze_symbol(symbol)
        report = self.ai_analyst.format_analysis_report(analysis)
        print(report)
        return analysis
    
    def query(self, query: str):
        """Handle user query"""
        logger.info(f"Processing query: {query}")
        response = self.ai_analyst.query(query)
        print(response)
        return response
    
    def run(self, interval: int = 60):
        """Start AI trading system"""
        self.is_running = True
        logger.info("AI Trading System started")
        
        try:
            while self.is_running:
                try:
                    # Get market data
                    symbol = Config.SYMBOL
                    market_data = self.engine.get_market_data()
                    
                    # Generate signal using strategy
                    signal = self.strategy.generate_signal(market_data)
                    logger.info(f"Signal generated: {signal}")
                    
                    # Check existing positions
                    self.engine.check_positions()
                    
                    # Execute trade if signal is strong enough
                    if signal['action'] != 'HOLD' and signal.get('confidence', 0) > 0.5:
                        account_balance = self.engine.get_account_balance()
                        if account_balance > 0:
                            # Calculate position size with advanced risk management
                            entry_price = signal.get('price', 0)
                            stop_loss = signal.get('stop_loss', 0)
                            
                            if entry_price > 0 and stop_loss > 0:
                                position_size = self.engine.risk_manager.calculate_position_size(
                                    account_balance, entry_price, stop_loss, risk_percent=1.0
                                )
                            else:
                                position_size = self.engine.risk_manager.calculate_position_size_legacy(
                                    account_balance, risk_percent=1.0
                                )
                            
                            if position_size > 0:
                                self.engine.execute_trade(signal, account_balance)
                    
                    # Wait before next iteration
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    logger.info("Trading system stopped by user")
                    self.is_running = False
                    break
                except Exception as e:
                    logger.error(f"Error in trading loop: {e}")
                    time.sleep(interval)
        
        except Exception as e:
            logger.error(f"Fatal error in AI trading system: {e}")
            self.is_running = False
    
    def stop(self):
        """Stop the trading system"""
        self.is_running = False
        self.engine.stop()
        if self.data_collector:
            self.data_collector.stop()
        logger.info("AI Trading System stopped")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI-Powered Trading System')
    parser.add_argument('--broker', type=str, default='zerodha', 
                       choices=['zerodha', 'angelone', 'binance'],
                       help='Broker to use')
    parser.add_argument('--strategy', type=str, default='ml',
                       choices=['ml', 'news_momentum', 'mean_reversion', 'crypto_onchain'],
                       help='Strategy to use')
    parser.add_argument('--analyze', type=str, help='Symbol to analyze')
    parser.add_argument('--query', type=str, help='Natural language query')
    parser.add_argument('--train', type=str, help='Symbol to train ML model on')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AI-Powered Trading System")
    print("=" * 60)
    
    # Initialize system
    system = AITradingSystem(broker=args.broker, strategy_type=args.strategy)
    
    # Handle different modes
    if args.analyze:
        # Analysis mode
        system.analyze_symbol(args.analyze)
        return
    
    if args.query:
        # Query mode
        system.query(args.query)
        return
    
    if args.train:
        # Training mode
        system.train_ml_model(args.train)
        return
    
    # Trading mode
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        system.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start trading
    try:
        system.run(interval=60)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        system.stop()
        sys.exit(1)


if __name__ == "__main__":
    import time
    main()


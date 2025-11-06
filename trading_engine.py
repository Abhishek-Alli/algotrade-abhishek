"""
Main trading engine that coordinates API, strategy, and risk management
"""
import time
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Optional
from api_client import APIClient, BinanceClient
from strategy import Strategy, MovingAverageStrategy
from risk_manager import RiskManager
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


class TradingEngine:
    """Main trading engine"""
    
    def __init__(self, strategy: Strategy = None, api_client: APIClient = None, 
                 enable_data_collection: bool = True):
        self.strategy = strategy or MovingAverageStrategy()
        self.api_client = api_client or BinanceClient(
            testnet=Config.TESTNET
        )
        self.risk_manager = RiskManager()
        self.symbol = Config.SYMBOL
        self.is_running = False
        self.positions = {}
        
        # Start data collector if enabled
        self.data_collector = None
        if enable_data_collection:
            self.data_collector = DataCollector(
                symbols=[self.symbol], 
                interval_seconds=60,
                api_client=self.api_client
            )
            self.data_collector.start()
            logger.info("Data collection service started")
    
    def get_market_data(self, interval: str = '1h', limit: int = 100) -> pd.DataFrame:
        """Fetch market data and convert to DataFrame"""
        try:
            klines = self.api_client.get_klines(self.symbol, interval, limit)
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            raise
    
    def get_account_balance(self) -> float:
        """Get account balance"""
        try:
            account = self.api_client.get_account_balance()
            # Find USDT or base currency balance
            for asset in account.get('balances', []):
                if asset['asset'] == 'USDT':
                    return float(asset['free'])
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching account balance: {e}")
            return 0.0
    
    def execute_trade(self, signal: Dict, account_balance: float) -> Optional[Dict]:
        """Execute a trade based on signal"""
        if signal['action'] == 'HOLD':
            return None
        
        # Check risk limits
        if not self.risk_manager.should_place_trade(account_balance):
            logger.warning("Trade blocked by risk manager")
            return None
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            account_balance, 
            risk_percent=1.0
        )
        
        if position_size <= 0:
            logger.warning("Position size too small")
            return None
        
        try:
            # Place market order
            order = self.api_client.place_market_order(
                symbol=self.symbol,
                side=signal['action'],
                quantity=position_size
            )
            
            # Get execution price
            current_price = self.api_client.get_current_price(self.symbol)
            
            # Create position record
            position = {
                'id': str(order.get('orderId', int(time.time()))),
                'order_id': order.get('orderId'),
                'symbol': self.symbol,
                'side': signal['action'],
                'quantity': position_size,
                'entry_price': current_price,
                'entry_time': datetime.now(),
                'signal_confidence': signal.get('confidence', 0.0)
            }
            
            # Add risk management
            self.risk_manager.add_position(position)
            self.positions[position['id']] = position
            
            logger.info(f"Trade executed: {position}")
            return position
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return None
    
    def check_positions(self):
        """Check and manage open positions"""
        current_price = self.api_client.get_current_price(self.symbol)
        
        for position_id, position in list(self.positions.items()):
            # Check stop loss
            if self.risk_manager.check_stop_loss(position, current_price):
                logger.info(f"Stop loss triggered for position {position_id}")
                self.close_position(position_id, 'STOP_LOSS')
                continue
            
            # Check take profit
            if self.risk_manager.check_take_profit(position, current_price):
                logger.info(f"Take profit triggered for position {position_id}")
                self.close_position(position_id, 'TAKE_PROFIT')
                continue
            
            # Check strategy exit signal
            if self.strategy.should_exit(position, current_price):
                logger.info(f"Strategy exit signal for position {position_id}")
                self.close_position(position_id, 'STRATEGY_EXIT')
                continue
    
    def close_position(self, position_id: str, reason: str = 'MANUAL'):
        """Close a position"""
        if position_id not in self.positions:
            return
        
        position = self.positions[position_id]
        side = 'SELL' if position['side'] == 'BUY' else 'BUY'
        
        try:
            order = self.api_client.place_market_order(
                symbol=self.symbol,
                side=side,
                quantity=position['quantity']
            )
            
            current_price = self.api_client.get_current_price(self.symbol)
            
            # Calculate P&L
            entry_price = position['entry_price']
            if position['side'] == 'BUY':
                pnl = (current_price - entry_price) * position['quantity']
            else:
                pnl = (entry_price - current_price) * position['quantity']
            
            self.risk_manager.update_daily_pnl(pnl)
            
            logger.info(f"Position closed: {position_id}, Reason: {reason}, P&L: {pnl:.2f}")
            
            # Remove position
            self.risk_manager.remove_position(position_id)
            del self.positions[position_id]
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
    
    def run(self, interval: int = 60):
        """Main trading loop"""
        self.is_running = True
        logger.info("Trading engine started")
        
        try:
            while self.is_running:
                try:
                    # Get market data
                    market_data = self.get_market_data()
                    
                    # Generate signal
                    signal = self.strategy.generate_signal(market_data)
                    logger.info(f"Signal generated: {signal}")
                    
                    # Check existing positions
                    self.check_positions()
                    
                    # Execute trade if signal is strong enough
                    if signal['action'] != 'HOLD' and signal.get('confidence', 0) > 0.5:
                        account_balance = self.get_account_balance()
                        if account_balance > 0:
                            self.execute_trade(signal, account_balance)
                    
                    # Wait before next iteration
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    logger.info("Trading engine stopped by user")
                    self.is_running = False
                    break
                except Exception as e:
                    logger.error(f"Error in trading loop: {e}")
                    time.sleep(interval)
        
        except Exception as e:
            logger.error(f"Fatal error in trading engine: {e}")
            self.is_running = False
    
    def stop(self):
        """Stop the trading engine"""
        self.is_running = False
        if self.data_collector:
            self.data_collector.stop()
        logger.info("Trading engine stopped")
    
    def get_status(self) -> Dict:
        """Get current engine status"""
        return {
            'is_running': self.is_running,
            'symbol': self.symbol,
            'strategy': self.strategy.name,
            'open_positions': len(self.positions),
            'positions': self.positions,
            'daily_pnl': self.risk_manager.daily_pnl
        }


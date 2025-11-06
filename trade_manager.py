"""
Trade Manager - Manage all trades with monitoring and execution
"""
import time
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from trade_setup import TradeSetup, PositionType, StrategyBasedTradeSetup
from api_client import APIClient
from feature_engineering import FeatureEngineer
from strategy import Strategy
from config import Config

logger = logging.getLogger(__name__)


class TradeManager:
    """Complete trade management system"""
    
    def __init__(self, api_client: APIClient, strategy: Strategy = None):
        self.api_client = api_client
        self.strategy = strategy
        self.trade_setup = StrategyBasedTradeSetup()
        self.feature_engineer = FeatureEngineer()
        self.is_running = False
    
    def initialize_account(self):
        """Initialize with account balance"""
        try:
            balance_data = self.api_client.get_account_balance()
            
            # Extract balance (different for different exchanges)
            if isinstance(balance_data, dict):
                if 'result' in balance_data:
                    # Delta Exchange format
                    balances = balance_data.get('result', {}).get('balances', [])
                    if balances:
                        total_balance = sum(float(b.get('balance', 0)) for b in balances)
                    else:
                        total_balance = float(balance_data.get('result', {}).get('available_balance', 0))
                elif 'balances' in balance_data:
                    # Binance format
                    for asset in balance_data.get('balances', []):
                        if asset.get('asset') == 'USDT':
                            total_balance = float(asset.get('free', 0))
                            break
                    else:
                        total_balance = 0.0
                else:
                    total_balance = float(balance_data.get('available_balance', 0))
            else:
                total_balance = 0.0
            
            self.trade_setup.set_account_balance(total_balance)
            logger.info(f"Account initialized with balance: {total_balance}")
            return total_balance
        except Exception as e:
            logger.error(f"Error initializing account: {e}")
            # Set default balance
            self.trade_setup.set_account_balance(10000.0)
            return 10000.0
    
    def create_manual_trade(self, symbol: str, position_type: str,
                           entry_price: float, sl_price: float, target_price: float,
                           quantity: float = None, risk_percent: float = 1.0) -> Dict:
        """Create a manual trade"""
        pos_type = PositionType.LONG if position_type.upper() == 'LONG' else PositionType.SHORT
        
        trade = self.trade_setup.create_trade(
            symbol=symbol,
            position_type=pos_type,
            entry_price=entry_price,
            sl_price=sl_price,
            target_price=target_price,
            quantity=quantity,
            risk_percent=risk_percent,
            strategy="Manual"
        )
        
        return trade
    
    def create_strategy_trade(self, symbol: str, data: pd.DataFrame, 
                             strategy_name: str, indicators: Dict = None,
                             strategy_params: Dict = None,
                             sl_percent: float = None,
                             target_percent: float = None,
                             sl_price: float = None,
                             target_price: float = None) -> Dict:
        """
        Create trade from strategy signals
        
        Args:
            symbol: Trading symbol
            data: Market data
            strategy_name: Strategy name
            indicators: Indicator values (optional)
            strategy_params: Strategy parameters (e.g., {'fast_period': 9, 'slow_period': 21})
        """
        from strategy import MovingAverageStrategy, RSIMomentumStrategy, BollingerBandsStrategy
        from strategy import EMAStrategy, EMARibbonStrategy, EMA200Strategy
        try:
            from chart_patterns import ChartPatternStrategy
            CHART_PATTERNS_AVAILABLE = True
        except ImportError:
            CHART_PATTERNS_AVAILABLE = False
        
        # Calculate indicators if not provided
        if indicators is None:
            data_with_features = self.feature_engineer.create_features(data)
            indicators = {
                'rsi': float(data_with_features['rsi'].iloc[-1]) if 'rsi' in data_with_features.columns else 50,
                'macd_signal': float(data_with_features['macd_histogram'].iloc[-1]) if 'macd_histogram' in data_with_features.columns else 0,
                'atr': float(data_with_features['atr'].iloc[-1]) if 'atr' in data_with_features.columns else 0,
                'support': float(data_with_features['recent_low'].iloc[-1]) if 'recent_low' in data_with_features.columns else None,
                'resistance': float(data_with_features['recent_high'].iloc[-1]) if 'recent_high' in data_with_features.columns else None,
                'bb_upper': float(data_with_features['bb_upper'].iloc[-1]) if 'bb_upper' in data_with_features.columns else None,
                'bb_lower': float(data_with_features['bb_lower'].iloc[-1]) if 'bb_lower' in data_with_features.columns else None,
            }
        
        # Initialize strategy based on name
        strategy = None
        if strategy_name == "Moving Average":
            fast = strategy_params.get('fast_period', 10) if strategy_params else 10
            slow = strategy_params.get('slow_period', 30) if strategy_params else 30
            strategy = MovingAverageStrategy(fast_period=fast, slow_period=slow)
        elif strategy_name == "RSI Momentum":
            strategy = RSIMomentumStrategy()
        elif strategy_name == "Bollinger Bands":
            strategy = BollingerBandsStrategy()
        elif strategy_name == "EMA Crossover":
            fast = strategy_params.get('fast_period', 9) if strategy_params else 9
            slow = strategy_params.get('slow_period', 21) if strategy_params else 21
            strategy = EMAStrategy(fast_period=fast, slow_period=slow)
        elif strategy_name == "EMA Ribbon":
            periods = strategy_params.get('periods', [8, 13, 21, 34, 55, 89]) if strategy_params else None
            strategy = EMARibbonStrategy(periods=periods)
        elif strategy_name == "EMA 200 Dynamic S/R":
            pullback = strategy_params.get('pullback_ema', 21) if strategy_params else 21
            strategy = EMA200Strategy(pullback_ema=pullback)
        elif strategy_name == "Chart Patterns" and CHART_PATTERNS_AVAILABLE:
            pattern_types = strategy_params.get('pattern_types', ['all']) if strategy_params else ['all']
            strategy = ChartPatternStrategy(pattern_types=pattern_types)
        else:
            # Fallback to default strategy-based trade setup
            return self.trade_setup.create_trade_from_strategy(
                symbol=symbol,
                data=data,
                strategy_name=strategy_name,
                indicators=indicators
            )
        
        # Generate signal from strategy
        signal = strategy.generate_signal(data)
        
        if signal.get('action') == 'HOLD':
            raise ValueError("Strategy generated HOLD signal. No trade available.")
        
        current_price = signal.get('price', float(data['close'].iloc[-1]))
        action = signal.get('action')
        
        # Determine position type
        from trade_setup import PositionType
        position_type = PositionType.LONG if action == 'BUY' else PositionType.SHORT
        
        # Calculate SL and Target
        atr = indicators.get('atr', 0)
        if atr > 0:
            atr_multiplier_sl = 2.0
            atr_multiplier_target = 3.0
        else:
            atr_multiplier_sl = 0.02  # 2% default
            atr_multiplier_target = 0.03  # 3% default
        
        if position_type == PositionType.LONG:
            # Priority: Manual price > Percentage > Signal default > ATR default
            if sl_price is not None:
                sl_price = sl_price  # Use provided price
            elif sl_percent is not None:
                sl_price = current_price * (1 - sl_percent / 100)
            else:
                sl_price = signal.get('stop_loss', current_price - (atr * atr_multiplier_sl) if atr > 0 else current_price * 0.98)
            
            if target_price is not None:
                target_price = target_price  # Use provided price
            elif target_percent is not None:
                target_price = current_price * (1 + target_percent / 100)
            else:
                target_price = signal.get('take_profit', current_price + (atr * atr_multiplier_target) if atr > 0 else current_price * 1.03)
        else:  # SHORT
            # Priority: Manual price > Percentage > Signal default > ATR default
            if sl_price is not None:
                sl_price = sl_price  # Use provided price
            elif sl_percent is not None:
                sl_price = current_price * (1 + sl_percent / 100)
            else:
                sl_price = signal.get('stop_loss', current_price + (atr * atr_multiplier_sl) if atr > 0 else current_price * 1.02)
            
            if target_price is not None:
                target_price = target_price  # Use provided price
            elif target_percent is not None:
                target_price = current_price * (1 - target_percent / 100)
            else:
                target_price = signal.get('take_profit', current_price - (atr * atr_multiplier_target) if atr > 0 else current_price * 0.97)
        
        # Use support/resistance if available
        support = indicators.get('support', None)
        resistance = indicators.get('resistance', None)
        
        if position_type == PositionType.LONG and support:
            sl_price = min(sl_price, support * 0.99)
        if position_type == PositionType.LONG and resistance:
            target_price = max(target_price, resistance * 0.99)
        
        if position_type == PositionType.SHORT and resistance:
            sl_price = max(sl_price, resistance * 1.01)
        if position_type == PositionType.SHORT and support:
            target_price = min(target_price, support * 1.01)
        
        # Create trade with pattern information
        trade_indicators = {**indicators}
        
        # Add pattern information if available
        if signal.get('pattern'):
            trade_indicators['pattern'] = signal.get('pattern')
        if signal.get('signal_type'):
            trade_indicators['signal_type'] = signal.get('signal_type')
        if signal.get('entry_reason'):
            trade_indicators['entry_reason'] = signal.get('entry_reason')
        if signal.get('is_fake') is not None:
            trade_indicators['is_fake'] = signal.get('is_fake')
        if signal.get('fake_reason'):
            trade_indicators['fake_reason'] = signal.get('fake_reason')
        if signal.get('pattern_strength') is not None:
            trade_indicators['pattern_strength'] = signal.get('pattern_strength')
        
        # Create trade
        trade = self.trade_setup.create_trade(
            symbol=symbol,
            position_type=position_type,
            entry_price=current_price,
            sl_price=round(sl_price, 8),
            target_price=round(target_price, 8),
            strategy=strategy_name,
            indicators=trade_indicators
        )
        
        return trade
    
    def execute_trade(self, trade_id: str) -> Dict:
        """Execute trade (place order)"""
        trade = self.trade_setup.get_trade(trade_id)
        if not trade:
            raise ValueError(f"Trade {trade_id} not found")
        
        try:
            # Place order
            if trade['position_type'] == PositionType.LONG.value:
                side = 'BUY'
            else:
                side = 'SELL'
            
            order = self.api_client.place_limit_order(
                symbol=trade['symbol'],
                side=side,
                quantity=trade['quantity'],
                price=trade['entry_price']
            )
            
            # Activate trade
            actual_entry = trade['entry_price']  # Can be updated from order fill price
            self.trade_setup.activate_trade(trade_id, actual_entry)
            
            logger.info(f"Trade executed: {trade_id}, Order: {order}")
            return {'trade': trade, 'order': order}
            
        except Exception as e:
            logger.error(f"Error executing trade {trade_id}: {e}")
            raise
    
    def monitor_trades(self, interval: int = 5):
        """Monitor all active trades"""
        self.is_running = True
        
        while self.is_running:
            try:
                active_trades = self.trade_setup.get_active_trades()
                
                for trade in active_trades:
                    try:
                        # Get current price
                        current_price = self.api_client.get_current_price(trade['symbol'])
                        
                        # Check trade
                        result = self.trade_setup.check_trade(trade['id'], current_price)
                        
                        if result['status'] == 'sl_hit':
                            logger.warning(f"SL Hit for {trade['id']}: P&L = {trade['pnl']}")
                            # Place exit order if needed
                            self._exit_trade(trade, current_price)
                        
                        elif result['status'] == 'target_hit':
                            logger.info(f"Target Hit for {trade['id']}: P&L = {trade['pnl']}")
                            # Place exit order if needed
                            self._exit_trade(trade, current_price)
                        
                        else:
                            # Update unrealized P&L
                            logger.debug(f"{trade['id']}: Price={current_price}, Unrealized P&L={trade['pnl']}")
                    
                    except Exception as e:
                        logger.error(f"Error monitoring trade {trade['id']}: {e}")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Trade monitoring stopped")
                self.is_running = False
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _exit_trade(self, trade: Dict, exit_price: float):
        """Exit a trade"""
        try:
            # Place opposite order
            if trade['position_type'] == PositionType.LONG.value:
                side = 'SELL'
            else:
                side = 'BUY'
            
            order = self.api_client.place_market_order(
                symbol=trade['symbol'],
                side=side,
                quantity=trade['quantity']
            )
            
            logger.info(f"Exit order placed for {trade['id']}: {order}")
            
        except Exception as e:
            logger.error(f"Error placing exit order: {e}")
    
    def get_dashboard(self) -> Dict:
        """Get trading dashboard data"""
        summary = self.trade_setup.get_trade_summary()
        active_trades = self.trade_setup.get_active_trades()
        
        # Get current prices for active trades
        for trade in active_trades:
            try:
                current_price = self.api_client.get_current_price(trade['symbol'])
                self.trade_setup.check_trade(trade['id'], current_price)
            except:
                pass
        
        return {
            'summary': summary,
            'active_trades': active_trades,
            'long_positions': self.trade_setup.get_long_positions(),
            'short_positions': self.trade_setup.get_short_positions(),
            'timestamp': datetime.now()
        }
    
    def stop_monitoring(self):
        """Stop trade monitoring"""
        self.is_running = False
        logger.info("Trade monitoring stopped")


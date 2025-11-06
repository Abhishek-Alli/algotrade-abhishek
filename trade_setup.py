"""
Trade Setup Module
Manage trade parameters: Entry, SL, Target, Indicators, Strategies, Positions
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class PositionType(Enum):
    """Position types"""
    LONG = "LONG"
    SHORT = "SHORT"


class TradeStatus(Enum):
    """Trade status"""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SL_HIT = "SL_HIT"
    TARGET_HIT = "TARGET_HIT"
    CLOSED = "CLOSED"


class TradeSetup:
    """Complete trade setup with all parameters"""
    
    def __init__(self):
        self.account_balance = 0.0
        self.trades = []
        self.active_positions = []
    
    def set_account_balance(self, balance: float):
        """Set account balance"""
        self.account_balance = balance
        logger.info(f"Account balance set: {balance}")
    
    def calculate_position_size(self, entry_price: float, sl_price: float, 
                               risk_percent: float = 1.0) -> float:
        """
        Calculate position size based on risk management
        Position Size = (Account Risk %) / (Entry Price - Stop Loss Price)
        """
        if entry_price <= sl_price:
            logger.warning("Stop loss must be below entry price for long positions")
            return 0.0
        
        risk_per_unit = abs(entry_price - sl_price)
        risk_amount = self.account_balance * (risk_percent / 100.0)
        position_size = risk_amount / risk_per_unit
        
        return round(position_size, 8)
    
    def create_trade(self, symbol: str, position_type: PositionType,
                    entry_price: float, sl_price: float, target_price: float,
                    quantity: float = None, risk_percent: float = 1.0,
                    strategy: str = "Manual", indicators: Dict = None) -> Dict:
        """
        Create a new trade setup
        
        Args:
            symbol: Trading symbol
            position_type: LONG or SHORT
            entry_price: Entry price
            sl_price: Stop loss price
            target_price: Target price
            quantity: Position size (auto-calculated if None)
            risk_percent: Risk percentage (default 1%)
            strategy: Strategy name
            indicators: Dictionary of indicator values
        """
        # Validate prices
        if position_type == PositionType.LONG:
            if sl_price >= entry_price:
                raise ValueError("Stop loss must be below entry price for LONG position")
            if target_price <= entry_price:
                raise ValueError("Target must be above entry price for LONG position")
        else:  # SHORT
            if sl_price <= entry_price:
                raise ValueError("Stop loss must be above entry price for SHORT position")
            if target_price >= entry_price:
                raise ValueError("Target must be below entry price for SHORT position")
        
        # Calculate position size if not provided
        if quantity is None:
            quantity = self.calculate_position_size(entry_price, sl_price, risk_percent)
        
        # Calculate risk/reward
        risk_amount = abs(entry_price - sl_price) * quantity
        reward_amount = abs(target_price - entry_price) * quantity
        risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
        
        # Calculate percentages
        sl_percent = abs((sl_price - entry_price) / entry_price) * 100
        target_percent = abs((target_price - entry_price) / entry_price) * 100
        
        # Create trade
        trade = {
            'id': f"TRADE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.trades)}",
            'symbol': symbol,
            'position_type': position_type.value,
            'entry_price': round(entry_price, 8),
            'sl_price': round(sl_price, 8),
            'target_price': round(target_price, 8),
            'quantity': round(quantity, 8),
            'risk_percent': risk_percent,
            'risk_amount': round(risk_amount, 2),
            'reward_amount': round(reward_amount, 2),
            'risk_reward_ratio': round(risk_reward_ratio, 2),
            'sl_percent': round(sl_percent, 2),
            'target_percent': round(target_percent, 2),
            'strategy': strategy,
            'indicators': indicators or {},
            'status': TradeStatus.PENDING.value,
            'created_at': datetime.now(),
            'entry_time': None,
            'exit_time': None,
            'exit_price': None,
            'pnl': 0.0,
            'pnl_percent': 0.0
        }
        
        self.trades.append(trade)
        logger.info(f"Trade created: {trade['id']}")
        logger.info(f"  Symbol: {symbol}, Type: {position_type.value}")
        logger.info(f"  Entry: {entry_price}, SL: {sl_price}, Target: {target_price}")
        logger.info(f"  Quantity: {quantity}, Risk/Reward: {risk_reward_ratio:.2f}")
        
        return trade
    
    def activate_trade(self, trade_id: str, actual_entry_price: float = None):
        """Activate a trade (mark as entered)"""
        trade = self.get_trade(trade_id)
        if not trade:
            raise ValueError(f"Trade {trade_id} not found")
        
        if trade['status'] != TradeStatus.PENDING.value:
            raise ValueError(f"Trade {trade_id} is not pending")
        
        trade['status'] = TradeStatus.ACTIVE.value
        trade['entry_time'] = datetime.now()
        if actual_entry_price:
            trade['entry_price'] = round(actual_entry_price, 8)
            # Recalculate quantities based on actual entry
            risk_amount = abs(trade['entry_price'] - trade['sl_price']) * trade['quantity']
            reward_amount = abs(trade['target_price'] - trade['entry_price']) * trade['quantity']
            trade['risk_amount'] = round(risk_amount, 2)
            trade['reward_amount'] = round(reward_amount, 2)
        
        self.active_positions.append(trade)
        logger.info(f"Trade activated: {trade_id}")
        return trade
    
    def check_trade(self, trade_id: str, current_price: float) -> Dict:
        """
        Check if trade SL or target is hit
        
        Returns:
            Dict with status update
        """
        trade = self.get_trade(trade_id)
        if not trade or trade['status'] != TradeStatus.ACTIVE.value:
            return {'status': 'not_active'}
        
        position_type = PositionType(trade['position_type'])
        sl_hit = False
        target_hit = False
        
        if position_type == PositionType.LONG:
            sl_hit = current_price <= trade['sl_price']
            target_hit = current_price >= trade['target_price']
        else:  # SHORT
            sl_hit = current_price >= trade['sl_price']
            target_hit = current_price <= trade['target_price']
        
        if sl_hit:
            trade['status'] = TradeStatus.SL_HIT.value
            trade['exit_time'] = datetime.now()
            trade['exit_price'] = round(current_price, 8)
            self._calculate_pnl(trade)
            self.active_positions = [t for t in self.active_positions if t['id'] != trade_id]
            logger.warning(f"Trade {trade_id}: Stop Loss HIT!")
            return {'status': 'sl_hit', 'trade': trade}
        
        if target_hit:
            trade['status'] = TradeStatus.TARGET_HIT.value
            trade['exit_time'] = datetime.now()
            trade['exit_price'] = round(current_price, 8)
            self._calculate_pnl(trade)
            self.active_positions = [t for t in self.active_positions if t['id'] != trade_id]
            logger.info(f"Trade {trade_id}: Target HIT!")
            return {'status': 'target_hit', 'trade': trade}
        
        # Calculate unrealized P&L
        self._calculate_pnl(trade, current_price)
        return {'status': 'active', 'trade': trade}
    
    def _calculate_pnl(self, trade: Dict, current_price: float = None):
        """Calculate P&L for a trade"""
        if current_price is None:
            current_price = trade.get('exit_price', trade['entry_price'])
        
        position_type = PositionType(trade['position_type'])
        entry_price = trade['entry_price']
        quantity = trade['quantity']
        
        if position_type == PositionType.LONG:
            pnl = (current_price - entry_price) * quantity
        else:  # SHORT
            pnl = (entry_price - current_price) * quantity
        
        trade['pnl'] = round(pnl, 2)
        trade['pnl_percent'] = round((pnl / (entry_price * quantity)) * 100, 2)
    
    def close_trade(self, trade_id: str, exit_price: float):
        """Manually close a trade"""
        trade = self.get_trade(trade_id)
        if not trade:
            raise ValueError(f"Trade {trade_id} not found")
        
        if trade['status'] not in [TradeStatus.ACTIVE.value, TradeStatus.PENDING.value]:
            raise ValueError(f"Trade {trade_id} is not active")
        
        trade['status'] = TradeStatus.CLOSED.value
        trade['exit_time'] = datetime.now()
        trade['exit_price'] = round(exit_price, 8)
        self._calculate_pnl(trade)
        
        if trade_id in [t['id'] for t in self.active_positions]:
            self.active_positions = [t for t in self.active_positions if t['id'] != trade_id]
        
        logger.info(f"Trade closed: {trade_id}, P&L: {trade['pnl']}")
        return trade
    
    def get_trade(self, trade_id: str) -> Optional[Dict]:
        """Get trade by ID"""
        for trade in self.trades:
            if trade['id'] == trade_id:
                return trade
        return None
    
    def get_active_trades(self) -> List[Dict]:
        """Get all active trades"""
        return [t for t in self.trades if t['status'] == TradeStatus.ACTIVE.value]
    
    def get_long_positions(self) -> List[Dict]:
        """Get all long positions"""
        return [t for t in self.active_positions if t['position_type'] == PositionType.LONG.value]
    
    def get_short_positions(self) -> List[Dict]:
        """Get all short positions"""
        return [t for t in self.active_positions if t['position_type'] == PositionType.SHORT.value]
    
    def get_trade_summary(self) -> Dict:
        """Get summary of all trades"""
        total_trades = len(self.trades)
        active_trades = len(self.get_active_trades())
        closed_trades = len([t for t in self.trades if t['status'] in 
                            [TradeStatus.SL_HIT.value, TradeStatus.TARGET_HIT.value, TradeStatus.CLOSED.value]])
        
        total_pnl = sum(t.get('pnl', 0) for t in self.trades)
        winning_trades = len([t for t in self.trades if t.get('pnl', 0) > 0])
        losing_trades = len([t for t in self.trades if t.get('pnl', 0) < 0])
        
        return {
            'account_balance': self.account_balance,
            'total_trades': total_trades,
            'active_trades': active_trades,
            'closed_trades': closed_trades,
            'long_positions': len(self.get_long_positions()),
            'short_positions': len(self.get_short_positions()),
            'total_pnl': round(total_pnl, 2),
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round((winning_trades / closed_trades * 100) if closed_trades > 0 else 0, 2)
        }


class StrategyBasedTradeSetup(TradeSetup):
    """Trade setup with strategy-based entry/exit"""
    
    def create_trade_from_strategy(self, symbol: str, data: pd.DataFrame,
                                  strategy_name: str, indicators: Dict,
                                  position_type: PositionType = None) -> Dict:
        """
        Create trade based on strategy signals and indicators
        
        Args:
            symbol: Trading symbol
            data: Market data with indicators
            strategy_name: Strategy name
            indicators: Indicator values (RSI, MACD, etc.)
            position_type: LONG or SHORT (auto-detect if None)
        """
        if data.empty or len(data) < 2:
            raise ValueError("Insufficient data for trade setup")
        
        current_price = float(data['close'].iloc[-1])
        
        # Auto-detect position type from strategy
        if position_type is None:
            # Determine from indicators
            rsi = indicators.get('rsi', 50)
            macd_signal = indicators.get('macd_signal', 0)
            
            if rsi < 30 or macd_signal > 0:
                position_type = PositionType.LONG
            else:
                position_type = PositionType.SHORT
        
        # Calculate SL and Target based on indicators
        atr = indicators.get('atr', 0)
        atr_multiplier_sl = 2.0
        atr_multiplier_target = 3.0
        
        if position_type == PositionType.LONG:
            sl_price = current_price - (atr * atr_multiplier_sl) if atr > 0 else current_price * 0.98
            target_price = current_price + (atr * atr_multiplier_target) if atr > 0 else current_price * 1.03
        else:  # SHORT
            sl_price = current_price + (atr * atr_multiplier_sl) if atr > 0 else current_price * 1.02
            target_price = current_price - (atr * atr_multiplier_target) if atr > 0 else current_price * 0.97
        
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
        
        # Create trade
        trade = self.create_trade(
            symbol=symbol,
            position_type=position_type,
            entry_price=current_price,
            sl_price=round(sl_price, 8),
            target_price=round(target_price, 8),
            strategy=strategy_name,
            indicators=indicators
        )
        
        return trade



"""
Risk management module for position sizing and risk controls
"""
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger(__name__)


class RiskManager:
    """Manages risk controls and position sizing"""
    
    def __init__(self):
        self.max_daily_loss = Config.MAX_DAILY_LOSS
        self.max_position_size = Config.MAX_POSITION_SIZE
        self.stop_loss_percent = Config.STOP_LOSS_PERCENT
        self.take_profit_percent = Config.TAKE_PROFIT_PERCENT
        self.daily_pnl = 0.0
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0)
        self.positions = []
    
    def reset_daily_stats(self):
        """Reset daily statistics at midnight"""
        now = datetime.now()
        if now.date() > self.daily_reset_time.date():
            self.daily_pnl = 0.0
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0)
            logger.info("Daily statistics reset")
    
    def calculate_position_size(self, account_balance: float, entry_price: float, 
                                stop_loss_price: float, risk_percent: float = 1.0) -> float:
        """
        Calculate position size based on risk management formula:
        Position Size = (Account Risk %) / (Entry Price - Stop-Loss Price)
        
        Args:
            account_balance: Total account balance
            entry_price: Entry price for the trade
            stop_loss_price: Stop loss price
            risk_percent: Percentage of account to risk (default 1%)
        
        Returns:
            Position size in units
        """
        self.reset_daily_stats()
        
        # Calculate risk per unit
        if entry_price <= stop_loss_price:
            logger.warning("Stop loss must be below entry price for long positions")
            return 0.0
        
        risk_per_unit = abs(entry_price - stop_loss_price)
        
        # Calculate total risk amount
        risk_amount = account_balance * (risk_percent / 100.0)
        
        # Calculate position size
        position_size = risk_amount / risk_per_unit
        
        # Cap at configured maximum
        position_size = min(position_size, self.max_position_size)
        
        # Ensure minimum position size
        if position_size < 0.001:
            return 0.0
        
        return round(position_size, 8)
    
    def calculate_position_size_legacy(self, account_balance: float, risk_percent: float = 1.0) -> float:
        """
        Legacy method for backward compatibility
        Calculate position size based on account balance and risk percentage
        """
        self.reset_daily_stats()
        
        # Maximum position size based on account balance
        max_size = account_balance * (risk_percent / 100.0)
        
        # Cap at configured maximum
        position_size = min(max_size, self.max_position_size)
        
        return round(position_size, 8)
    
    def should_place_trade(self, account_balance: float) -> bool:
        """Check if trading is allowed based on risk limits"""
        self.reset_daily_stats()
        
        # Check daily loss limit
        if self.daily_pnl <= -self.max_daily_loss:
            logger.warning(f"Daily loss limit reached: {self.daily_pnl}")
            return False
        
        # Check if account has sufficient balance
        if account_balance < 10.0:  # Minimum balance threshold
            logger.warning(f"Insufficient balance: {account_balance}")
            return False
        
        return True
    
    def calculate_stop_loss(self, entry_price: float, side: str) -> float:
        """Calculate stop loss price"""
        if side.upper() == 'BUY':
            stop_loss = entry_price * (1 - self.stop_loss_percent / 100.0)
        else:
            stop_loss = entry_price * (1 + self.stop_loss_percent / 100.0)
        
        return round(stop_loss, 8)
    
    def calculate_take_profit(self, entry_price: float, side: str) -> float:
        """Calculate take profit price"""
        if side.upper() == 'BUY':
            take_profit = entry_price * (1 + self.take_profit_percent / 100.0)
        else:
            take_profit = entry_price * (1 - self.take_profit_percent / 100.0)
        
        return round(take_profit, 8)
    
    def check_stop_loss(self, position: Dict, current_price: float) -> bool:
        """Check if stop loss is triggered"""
        if 'stop_loss' not in position:
            return False
        
        stop_loss = position['stop_loss']
        side = position.get('side', 'BUY').upper()
        
        if side == 'BUY':
            return current_price <= stop_loss
        else:
            return current_price >= stop_loss
    
    def check_take_profit(self, position: Dict, current_price: float) -> bool:
        """Check if take profit is triggered"""
        if 'take_profit' not in position:
            return False
        
        take_profit = position['take_profit']
        side = position.get('side', 'BUY').upper()
        
        if side == 'BUY':
            return current_price >= take_profit
        else:
            return current_price <= take_profit
    
    def update_daily_pnl(self, pnl: float):
        """Update daily P&L"""
        self.daily_pnl += pnl
        logger.info(f"Daily P&L updated: {self.daily_pnl}")
    
    def add_position(self, position: Dict):
        """Add a new position with risk management"""
        position['stop_loss'] = self.calculate_stop_loss(
            position['entry_price'], 
            position['side']
        )
        position['take_profit'] = self.calculate_take_profit(
            position['entry_price'], 
            position['side']
        )
        position['entry_time'] = datetime.now()
        self.positions.append(position)
        logger.info(f"Position added: {position}")
    
    def remove_position(self, position_id: str):
        """Remove a position"""
        self.positions = [p for p in self.positions if p.get('id') != position_id]
    
    def get_open_positions(self) -> list:
        """Get all open positions"""
        return self.positions.copy()


"""
Utility functions for Indian Stock Market (NSE/BSE) and F&O trading
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def get_fno_symbol(base_symbol: str, expiry_date: str, option_type: str = None, 
                   strike_price: int = None) -> str:
    """
    Generate F&O symbol for Indian market
    
    Args:
        base_symbol: Base symbol (e.g., 'NIFTY', 'BANKNIFTY')
        expiry_date: Expiry date in format 'YYMMDD' (e.g., '240125' for 25 Jan 2024)
        option_type: 'CE' for Call, 'PE' for Put, None for Futures
        strike_price: Strike price for options
    
    Returns:
        Formatted symbol (e.g., 'NIFTY24JANFUT', 'NIFTY24JAN18000CE')
    """
    if option_type and strike_price:
        # Option symbol: NIFTY24JAN18000CE
        month_map = {
            '01': 'JAN', '02': 'FEB', '03': 'MAR', '04': 'APR',
            '05': 'MAY', '06': 'JUN', '07': 'JUL', '08': 'AUG',
            '09': 'SEP', '10': 'OCT', '11': 'NOV', '12': 'DEC'
        }
        month = expiry_date[2:4]
        month_name = month_map.get(month, month)
        year = expiry_date[0:2]
        return f"{base_symbol}{year}{month_name}{strike_price}{option_type}"
    else:
        # Future symbol: NIFTY24JANFUT
        month_map = {
            '01': 'JAN', '02': 'FEB', '03': 'MAR', '04': 'APR',
            '05': 'MAY', '06': 'JUN', '07': 'JUL', '08': 'AUG',
            '09': 'SEP', '10': 'OCT', '11': 'NOV', '12': 'DEC'
        }
        month = expiry_date[2:4]
        month_name = month_map.get(month, month)
        year = expiry_date[0:2]
        return f"{base_symbol}{year}{month_name}FUT"


def get_next_expiry_date(day: int = 3) -> str:
    """
    Get next expiry date (Thursday for weekly, last Thursday for monthly)
    
    Args:
        day: Day of week (0=Monday, 3=Thursday)
    
    Returns:
        Expiry date in format 'YYMMDD'
    """
    today = datetime.now()
    days_until_expiry = (day - today.weekday()) % 7
    if days_until_expiry == 0:
        days_until_expiry = 7  # Next week
    
    expiry = today + timedelta(days=days_until_expiry)
    return expiry.strftime('%y%m%d')


def get_lot_size(symbol: str, exchange: str = 'NFO') -> int:
    """
    Get lot size for F&O symbol
    Common lot sizes:
    - NIFTY: 50
    - BANKNIFTY: 15
    - FINNIFTY: 40
    - SENSEX: 10
    
    Note: This is a simplified version. In production, fetch from broker API
    """
    lot_sizes = {
        'NIFTY': 50,
        'BANKNIFTY': 15,
        'FINNIFTY': 40,
        'SENSEX': 10,
        'MIDCPNIFTY': 50
    }
    
    for key, size in lot_sizes.items():
        if key in symbol.upper():
            return size
    
    return 50  # Default lot size


def format_indian_symbol(symbol: str, exchange: str = 'NSE') -> str:
    """
    Format symbol for Indian market API calls
    Format: EXCHANGE:SYMBOL (e.g., NSE:INFY, NFO:NIFTY24JANFUT)
    """
    if ':' in symbol:
        return symbol
    return f"{exchange}:{symbol}"


def calculate_option_greeks(spot_price: float, strike_price: float, 
                           time_to_expiry: float, volatility: float, 
                           risk_free_rate: float = 0.06, option_type: str = 'CE') -> Dict:
    """
    Calculate option Greeks (simplified Black-Scholes model)
    Note: This is a simplified implementation. For production, use proper libraries
    """
    # This is a placeholder. For production, use libraries like numpy-financial
    # or implement proper Black-Scholes model
    greeks = {
        'delta': 0.5,
        'gamma': 0.01,
        'theta': -0.5,
        'vega': 0.1
    }
    return greeks


def get_market_holidays(year: int = None) -> List[datetime]:
    """
    Get list of market holidays for NSE/BSE
    Note: This is a placeholder. In production, fetch from NSE/BSE website or API
    """
    if year is None:
        year = datetime.now().year
    
    # Common holidays (example)
    holidays = [
        datetime(year, 1, 26),  # Republic Day
        datetime(year, 3, 29),  # Holi (varies)
        datetime(year, 4, 11),  # Good Friday (varies)
        datetime(year, 8, 15),  # Independence Day
        datetime(year, 10, 2),  # Gandhi Jayanti
        datetime(year, 10, 31),  # Diwali (varies)
        # Add more holidays
    ]
    
    return holidays


def is_market_open() -> bool:
    """Check if Indian stock market is currently open"""
    now = datetime.now()
    
    # Market timings: 9:15 AM to 3:30 PM IST
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    # Check if it's a weekday (Monday-Friday)
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Check if current time is within market hours
    if now < market_open or now > market_close:
        return False
    
    # Check if it's a holiday (simplified)
    holidays = get_market_holidays(now.year)
    if any(holiday.date() == now.date() for holiday in holidays):
        return False
    
    return True


def get_expiry_series(base_symbol: str, num_expiries: int = 3) -> List[str]:
    """
    Get list of upcoming expiry dates for a symbol
    
    Args:
        base_symbol: Base symbol (e.g., 'NIFTY')
        num_expiries: Number of expiry dates to return
    
    Returns:
        List of expiry dates in format 'YYMMDD'
    """
    expiries = []
    today = datetime.now()
    
    # Get next 3 Thursdays
    for i in range(num_expiries):
        days_until_thursday = (3 - today.weekday()) % 7
        if days_until_thursday == 0:
            days_until_thursday = 7
        
        expiry = today + timedelta(days=days_until_thursday + (i * 7))
        expiries.append(expiry.strftime('%y%m%d'))
    
    return expiries



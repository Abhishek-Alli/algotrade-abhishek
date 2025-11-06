"""
Example: Futures & Options Trading for Indian Stock Market
This example shows how to trade NIFTY futures and options
"""
from api_client import ZerodhaKiteClient
from indian_market_utils import get_fno_symbol, get_next_expiry_date, get_lot_size, is_market_open
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_nifty_future_trading():
    """Example: Trading NIFTY Futures"""
    
    # Initialize Zerodha Kite client
    client = ZerodhaKiteClient(
        api_key=Config.API_KEY,
        api_secret=Config.API_SECRET,
        access_token=Config.API_PASSPHRASE
    )
    
    # Get next expiry date
    expiry_date = get_next_expiry_date()
    logger.info(f"Next expiry date: {expiry_date}")
    
    # Generate NIFTY Future symbol
    nifty_future_symbol = get_fno_symbol('NIFTY', expiry_date)
    symbol = f"NFO:{nifty_future_symbol}"
    logger.info(f"NIFTY Future symbol: {symbol}")
    
    # Get lot size
    lot_size = get_lot_size('NIFTY', exchange='NFO')
    logger.info(f"Lot size: {lot_size}")
    
    # Check if market is open
    if not is_market_open():
        logger.warning("Market is closed. Cannot place order.")
        return
    
    # Get current price
    try:
        current_price = client.get_current_price(symbol)
        logger.info(f"Current NIFTY Future price: {current_price}")
    except Exception as e:
        logger.error(f"Error fetching price: {e}")
        return
    
    # Place a market order (example - commented out for safety)
    # Uncomment below to place actual order
    """
    try:
        order = client.place_market_order(
            symbol=symbol,
            side='BUY',
            quantity=lot_size,
            product_type='MIS',  # Intraday
            exchange='NFO'
        )
        logger.info(f"Order placed: {order}")
    except Exception as e:
        logger.error(f"Error placing order: {e}")
    """
    
    # Get positions
    try:
        positions = client.get_positions()
        logger.info(f"Current positions: {positions}")
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")


def example_nifty_option_trading():
    """Example: Trading NIFTY Options (Call/Put)"""
    
    # Initialize Zerodha Kite client
    client = ZerodhaKiteClient(
        api_key=Config.API_KEY,
        api_secret=Config.API_SECRET,
        access_token=Config.API_PASSPHRASE
    )
    
    # Get next expiry date
    expiry_date = get_next_expiry_date()
    
    # Example: NIFTY 18000 Call Option
    strike_price = 18000
    option_type = 'CE'  # Call Option (use 'PE' for Put)
    
    nifty_option_symbol = get_fno_symbol('NIFTY', expiry_date, option_type, strike_price)
    symbol = f"NFO:{nifty_option_symbol}"
    logger.info(f"NIFTY Option symbol: {symbol}")
    
    # Get lot size
    lot_size = get_lot_size('NIFTY', exchange='NFO')
    
    # Check if market is open
    if not is_market_open():
        logger.warning("Market is closed.")
        return
    
    # Get current price
    try:
        current_price = client.get_current_price(symbol)
        logger.info(f"Current NIFTY {strike_price} {option_type} price: {current_price}")
    except Exception as e:
        logger.error(f"Error fetching price: {e}")
        return
    
    # Place a limit order (example - commented out for safety)
    """
    try:
        # Place limit order at current price
        order = client.place_limit_order(
            symbol=symbol,
            side='BUY',
            quantity=lot_size,
            price=current_price,
            product_type='MIS',
            exchange='NFO'
        )
        logger.info(f"Order placed: {order}")
    except Exception as e:
        logger.error(f"Error placing order: {e}")
    """


def example_banknifty_future():
    """Example: Trading BANKNIFTY Futures"""
    
    client = ZerodhaKiteClient(
        api_key=Config.API_KEY,
        api_secret=Config.API_SECRET,
        access_token=Config.API_PASSPHRASE
    )
    
    expiry_date = get_next_expiry_date()
    banknifty_future_symbol = get_fno_symbol('BANKNIFTY', expiry_date)
    symbol = f"NFO:{banknifty_future_symbol}"
    
    lot_size = get_lot_size('BANKNIFTY', exchange='NFO')
    
    logger.info(f"BANKNIFTY Future symbol: {symbol}")
    logger.info(f"Lot size: {lot_size}")
    
    if is_market_open():
        try:
            current_price = client.get_current_price(symbol)
            logger.info(f"Current BANKNIFTY Future price: {current_price}")
        except Exception as e:
            logger.error(f"Error: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("F&O Trading Examples")
    print("=" * 50)
    
    # Example 1: NIFTY Futures
    print("\n1. NIFTY Futures Example:")
    example_nifty_future_trading()
    
    # Example 2: NIFTY Options
    print("\n2. NIFTY Options Example:")
    example_nifty_option_trading()
    
    # Example 3: BANKNIFTY Futures
    print("\n3. BANKNIFTY Futures Example:")
    example_banknifty_future()
    
    print("\n" + "=" * 50)
    print("Note: Uncomment order placement code to execute trades")
    print("=" * 50)



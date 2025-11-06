"""
Interactive Trade Setup Script
"""
import argparse
from trade_manager import TradeManager
from trade_setup import PositionType
from api_client import DeltaExchangeClient, BinanceClient, ZerodhaKiteClient
from strategy import MovingAverageStrategy
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Setup Trade')
    
    # Trade parameters
    parser.add_argument('--symbol', type=str, required=True, help='Trading symbol')
    parser.add_argument('--type', type=str, choices=['LONG', 'SHORT'], required=True, help='Position type')
    parser.add_argument('--entry', type=float, required=True, help='Entry price')
    parser.add_argument('--sl', type=float, required=True, help='Stop loss price')
    parser.add_argument('--target', type=float, required=True, help='Target price')
    parser.add_argument('--quantity', type=float, help='Position size (auto-calculated if not provided)')
    parser.add_argument('--risk', type=float, default=1.0, help='Risk percentage (default: 1%)')
    
    # Broker
    parser.add_argument('--broker', type=str, default=Config.BROKER,
                       choices=['delta', 'binance', 'zerodha'],
                       help='Broker to use')
    
    # Execute
    parser.add_argument('--execute', action='store_true', help='Execute trade immediately')
    parser.add_argument('--monitor', action='store_true', help='Start monitoring after setup')
    
    args = parser.parse_args()
    
    # Initialize API client
    if args.broker == 'delta':
        api_client = DeltaExchangeClient(
            api_key=Config.API_KEY,
            api_secret=Config.API_SECRET,
            testnet=Config.DELTA_TESTNET
        )
    elif args.broker == 'binance':
        api_client = BinanceClient(testnet=Config.TESTNET)
    else:
        api_client = ZerodhaKiteClient(
            api_key=Config.API_KEY,
            api_secret=Config.API_SECRET,
            access_token=Config.API_PASSPHRASE
        )
    
    # Initialize trade manager
    manager = TradeManager(api_client=api_client)
    manager.initialize_account()
    
    # Create trade
    print("\n" + "="*60)
    print("SETTING UP TRADE")
    print("="*60)
    
    trade = manager.create_manual_trade(
        symbol=args.symbol,
        position_type=args.type,
        entry_price=args.entry,
        sl_price=args.sl,
        target_price=args.target,
        quantity=args.quantity,
        risk_percent=args.risk
    )
    
    print(f"\n✓ Trade Created: {trade['id']}")
    print(f"  Symbol: {trade['symbol']}")
    print(f"  Type: {trade['position_type']}")
    print(f"  Entry: ₹{trade['entry_price']:.2f}")
    print(f"  SL: ₹{trade['sl_price']:.2f} ({trade['sl_percent']:.2f}%)")
    print(f"  Target: ₹{trade['target_price']:.2f} ({trade['target_percent']:.2f}%)")
    print(f"  Quantity: {trade['quantity']:.8f}")
    print(f"  Risk: ₹{trade['risk_amount']:.2f}")
    print(f"  Reward: ₹{trade['reward_amount']:.2f}")
    print(f"  Risk/Reward Ratio: {trade['risk_reward_ratio']:.2f}")
    
    # Execute if requested
    if args.execute:
        print("\nExecuting trade...")
        try:
            result = manager.execute_trade(trade['id'])
            print(f"✓ Trade executed successfully!")
            print(f"  Order: {result.get('order', {})}")
        except Exception as e:
            print(f"✗ Error executing trade: {e}")
    
    # Monitor if requested
    if args.monitor:
        print("\nStarting trade monitoring...")
        print("Press Ctrl+C to stop\n")
        try:
            manager.monitor_trades(interval=5)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
            manager.stop_monitoring()
    
    # Show dashboard
    from trade_dashboard import print_dashboard
    print_dashboard(manager)


if __name__ == "__main__":
    main()



"""
Trade Dashboard - Display trade information
"""
import json
from datetime import datetime
from trade_manager import TradeManager
from trade_setup import PositionType
from api_client import APIClient
from strategy import MovingAverageStrategy
from config import Config


def print_dashboard(manager: TradeManager):
    """Print trading dashboard"""
    dashboard = manager.get_dashboard()
    
    print("\n" + "="*80)
    print("TRADING DASHBOARD")
    print("="*80)
    
    # Summary
    summary = dashboard['summary']
    print(f"\n📊 ACCOUNT SUMMARY")
    print(f"  Account Balance: ₹{summary['account_balance']:.2f}")
    print(f"  Total Trades: {summary['total_trades']}")
    print(f"  Active Trades: {summary['active_trades']}")
    print(f"  Closed Trades: {summary['closed_trades']}")
    print(f"  Long Positions: {summary['long_positions']}")
    print(f"  Short Positions: {summary['short_positions']}")
    print(f"  Total P&L: ₹{summary['total_pnl']:.2f}")
    print(f"  Win Rate: {summary['win_rate']:.2f}%")
    print(f"  Winning Trades: {summary['winning_trades']}")
    print(f"  Losing Trades: {summary['losing_trades']}")
    
    # Active Trades
    active_trades = dashboard['active_trades']
    if active_trades:
        print(f"\n📈 ACTIVE TRADES ({len(active_trades)})")
        for trade in active_trades:
            print(f"\n  Trade ID: {trade['id']}")
            print(f"  Symbol: {trade['symbol']}")
            print(f"  Type: {trade['position_type']}")
            print(f"  Entry: ₹{trade['entry_price']:.2f}")
            print(f"  SL: ₹{trade['sl_price']:.2f} ({trade['sl_percent']:.2f}%)")
            print(f"  Target: ₹{trade['target_price']:.2f} ({trade['target_percent']:.2f}%)")
            print(f"  Quantity: {trade['quantity']:.8f}")
            print(f"  Risk: ₹{trade['risk_amount']:.2f} | Reward: ₹{trade['reward_amount']:.2f}")
            print(f"  Risk/Reward: {trade['risk_reward_ratio']:.2f}")
            print(f"  Unrealized P&L: ₹{trade.get('pnl', 0):.2f} ({trade.get('pnl_percent', 0):.2f}%)")
            print(f"  Strategy: {trade['strategy']}")
            
            if trade.get('indicators'):
                print(f"  Indicators:")
                for key, value in trade['indicators'].items():
                    if value is not None:
                        print(f"    {key}: {value:.2f}" if isinstance(value, (int, float)) else f"    {key}: {value}")
    else:
        print(f"\n📈 ACTIVE TRADES: None")
    
    # Long Positions
    long_positions = dashboard['long_positions']
    if long_positions:
        print(f"\n📊 LONG POSITIONS ({len(long_positions)})")
        for trade in long_positions:
            print(f"  {trade['symbol']}: Entry={trade['entry_price']:.2f}, "
                  f"SL={trade['sl_price']:.2f}, Target={trade['target_price']:.2f}, "
                  f"P&L={trade.get('pnl', 0):.2f}")
    
    # Short Positions
    short_positions = dashboard['short_positions']
    if short_positions:
        print(f"\n📉 SHORT POSITIONS ({len(short_positions)})")
        for trade in short_positions:
            print(f"  {trade['symbol']}: Entry={trade['entry_price']:.2f}, "
                  f"SL={trade['sl_price']:.2f}, Target={trade['target_price']:.2f}, "
                  f"P&L={trade.get('pnl', 0):.2f}")
    
    print("\n" + "="*80 + "\n")


def main():
    """Main function for trade dashboard"""
    import argparse
    from api_client import DeltaExchangeClient, BinanceClient, ZerodhaKiteClient
    
    parser = argparse.ArgumentParser(description='Trade Dashboard')
    parser.add_argument('--broker', type=str, default=Config.BROKER,
                       choices=['delta', 'binance', 'zerodha'],
                       help='Broker to use')
    parser.add_argument('--monitor', action='store_true',
                       help='Start monitoring trades')
    
    args = parser.parse_args()
    
    # Initialize API client
    if args.broker == 'delta':
        from api_client import DeltaExchangeClient
        api_client = DeltaExchangeClient(
            api_key=Config.API_KEY,
            api_secret=Config.API_SECRET,
            testnet=Config.DELTA_TESTNET
        )
    elif args.broker == 'binance':
        from api_client import BinanceClient
        api_client = BinanceClient(testnet=Config.TESTNET)
    else:
        from api_client import ZerodhaKiteClient
        api_client = ZerodhaKiteClient(
            api_key=Config.API_KEY,
            api_secret=Config.API_SECRET,
            access_token=Config.API_PASSPHRASE
        )
    
    # Initialize trade manager
    manager = TradeManager(api_client=api_client)
    manager.initialize_account()
    
    if args.monitor:
        # Start monitoring
        print("Starting trade monitoring...")
        try:
            manager.monitor_trades(interval=5)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
            manager.stop_monitoring()
    else:
        # Show dashboard
        print_dashboard(manager)


if __name__ == "__main__":
    main()



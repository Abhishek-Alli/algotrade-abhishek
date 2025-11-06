# Trade Setup System

Complete trade management system with entry, SL, target, indicators, strategies, and position tracking.

## Features

✅ **Account Balance Management**: Automatic balance tracking  
✅ **Entry Price**: Set precise entry prices  
✅ **Stop Loss (SL)**: Automatic SL calculation and monitoring  
✅ **Target Price**: Multiple target levels  
✅ **Indicators**: RSI, MACD, ATR, Bollinger Bands, Support/Resistance  
✅ **Strategies**: Multiple trading strategies  
✅ **Long Positions**: Track long positions  
✅ **Short Positions**: Track short positions  
✅ **Risk Management**: Position sizing based on risk percentage  
✅ **Real-time Monitoring**: Automatic SL/Target hit detection  

## Quick Start

### 1. Manual Trade Setup

```bash
python setup_trade.py \
  --symbol "BTCUSDT" \
  --type LONG \
  --entry 45000 \
  --sl 44500 \
  --target 46500 \
  --risk 1.0 \
  --broker delta \
  --execute
```

### 2. Trade Dashboard

```bash
# View dashboard
python trade_dashboard.py --broker delta

# Monitor trades in real-time
python trade_dashboard.py --broker delta --monitor
```

## Usage Examples

### Example 1: Long Position

```bash
python setup_trade.py \
  --symbol "BTCUSDT" \
  --type LONG \
  --entry 45000 \
  --sl 44500 \
  --target 46500 \
  --risk 1.0 \
  --broker delta \
  --execute \
  --monitor
```

**Output:**
```
Trade ID: TRADE_20241105120000_0
Symbol: BTCUSDT
Type: LONG
Entry: ₹45000.00
SL: ₹44500.00 (1.11%)
Target: ₹46500.00 (3.33%)
Quantity: 0.00002222
Risk: ₹11.11
Reward: ₹33.33
Risk/Reward Ratio: 3.00
```

### Example 2: Short Position

```bash
python setup_trade.py \
  --symbol "ETHUSDT" \
  --type SHORT \
  --entry 2500 \
  --sl 2550 \
  --target 2400 \
  --risk 1.0 \
  --broker delta
```

### Example 3: Auto Position Size

```bash
# Position size automatically calculated based on risk
python setup_trade.py \
  --symbol "BTCUSDT" \
  --type LONG \
  --entry 45000 \
  --sl 44500 \
  --target 46500 \
  --risk 1.0 \
  --broker delta
```

Position size formula:
```
Position Size = (Account Balance × Risk %) / (Entry Price - SL Price)
```

### Example 4: Strategy-Based Trade

```python
from trade_manager import TradeManager
from api_client import DeltaExchangeClient
from strategy import MovingAverageStrategy
from config import Config
import pandas as pd

# Initialize
api_client = DeltaExchangeClient(
    api_key=Config.API_KEY,
    api_secret=Config.API_SECRET
)
manager = TradeManager(api_client=api_client)
manager.initialize_account()

# Get market data
market_data = api_client.get_klines("BTCUSDT", "1h", 100)
df = pd.DataFrame(market_data)

# Create trade from strategy
trade = manager.create_strategy_trade(
    symbol="BTCUSDT",
    data=df,
    strategy_name="Moving Average"
)

print(f"Trade created: {trade['id']}")
print(f"Entry: {trade['entry_price']}")
print(f"SL: {trade['sl_price']}")
print(f"Target: {trade['target_price']}")
```

## Trade Parameters

### Entry Price
- Current market price ya specific price
- Strategy-based automatic entry
- Manual entry price

### Stop Loss (SL)
- Percentage-based: `SL = Entry × (1 - SL%)`
- ATR-based: `SL = Entry ± (ATR × 2)`
- Support/Resistance based
- Manual SL price

### Target Price
- Percentage-based: `Target = Entry × (1 + Target%)`
- ATR-based: `Target = Entry ± (ATR × 3)`
- Resistance/Support based
- Multiple targets (Target 1, Target 2)

### Position Size
- Risk-based: `Size = (Balance × Risk%) / (Entry - SL)`
- Manual quantity
- Maximum position size limit

## Indicators

### Technical Indicators
- **RSI**: Relative Strength Index
- **MACD**: Moving Average Convergence Divergence
- **ATR**: Average True Range
- **Bollinger Bands**: Upper, Middle, Lower
- **Support/Resistance**: Key levels
- **Moving Averages**: SMA, EMA

### Indicator-Based Entry
```python
indicators = {
    'rsi': 45.5,
    'macd_signal': 0.02,
    'atr': 500.0,
    'support': 44000,
    'resistance': 46000,
    'bb_upper': 45500,
    'bb_lower': 44500
}

trade = manager.create_strategy_trade(
    symbol="BTCUSDT",
    data=df,
    strategy_name="RSI Strategy",
    indicators=indicators
)
```

## Strategies

### 1. Moving Average Crossover
```python
trade = manager.create_strategy_trade(
    symbol="BTCUSDT",
    data=df,
    strategy_name="MA Crossover"
)
```

### 2. RSI Strategy
```python
# RSI < 30: Buy signal
# RSI > 70: Sell signal
trade = manager.create_strategy_trade(
    symbol="BTCUSDT",
    data=df,
    strategy_name="RSI Strategy"
)
```

### 3. Bollinger Bands
```python
# Price at lower band: Buy
# Price at upper band: Sell
trade = manager.create_strategy_trade(
    symbol="BTCUSDT",
    data=df,
    strategy_name="Bollinger Bands"
)
```

## Position Management

### Long Positions
```python
# Get all long positions
long_positions = manager.trade_setup.get_long_positions()

for position in long_positions:
    print(f"Symbol: {position['symbol']}")
    print(f"Entry: {position['entry_price']}")
    print(f"Current P&L: {position['pnl']}")
```

### Short Positions
```python
# Get all short positions
short_positions = manager.trade_setup.get_short_positions()

for position in short_positions:
    print(f"Symbol: {position['symbol']}")
    print(f"Entry: {position['entry_price']}")
    print(f"Current P&L: {position['pnl']}")
```

## Risk Management

### Position Sizing
- **Risk Percentage**: Default 1% per trade
- **Maximum Risk**: Never risk more than 2% per trade
- **Position Size**: Based on SL distance

### Risk/Reward Ratio
- **Minimum**: 1:2 (Risk 1, Reward 2)
- **Optimal**: 1:3 (Risk 1, Reward 3)
- **Calculated**: Automatic calculation

### Stop Loss Management
- **Fixed SL**: Percentage-based
- **Trailing SL**: Update based on price movement
- **ATR-based SL**: Dynamic based on volatility

## Monitoring

### Real-time Monitoring
```bash
# Start monitoring
python trade_dashboard.py --broker delta --monitor
```

### Check Trade Status
```python
# Check specific trade
trade = manager.trade_setup.get_trade("TRADE_ID")
current_price = api_client.get_current_price("BTCUSDT")
result = manager.trade_setup.check_trade("TRADE_ID", current_price)

if result['status'] == 'sl_hit':
    print("Stop Loss Hit!")
elif result['status'] == 'target_hit':
    print("Target Hit!")
```

## Trade Dashboard

### View Dashboard
```bash
python trade_dashboard.py --broker delta
```

**Output:**
```
================================================================================
TRADING DASHBOARD
================================================================================

📊 ACCOUNT SUMMARY
  Account Balance: ₹10000.00
  Total Trades: 5
  Active Trades: 2
  Closed Trades: 3
  Long Positions: 1
  Short Positions: 1
  Total P&L: ₹150.50
  Win Rate: 66.67%
  Winning Trades: 2
  Losing Trades: 1

📈 ACTIVE TRADES (2)
  Trade ID: TRADE_20241105120000_0
  Symbol: BTCUSDT
  Type: LONG
  Entry: ₹45000.00
  SL: ₹44500.00 (1.11%)
  Target: ₹46500.00 (3.33%)
  Quantity: 0.00002222
  Risk: ₹11.11 | Reward: ₹33.33
  Risk/Reward: 3.00
  Unrealized P&L: ₹5.50 (2.50%)
  Strategy: Moving Average
```

## Complete Example

```python
from trade_manager import TradeManager
from api_client import DeltaExchangeClient
from config import Config

# Initialize
api_client = DeltaExchangeClient(
    api_key=Config.API_KEY,
    api_secret=Config.API_SECRET
)
manager = TradeManager(api_client=api_client)

# Initialize account
balance = manager.initialize_account()
print(f"Account Balance: ₹{balance:.2f}")

# Create trade
trade = manager.create_manual_trade(
    symbol="BTCUSDT",
    position_type="LONG",
    entry_price=45000,
    sl_price=44500,
    target_price=46500,
    risk_percent=1.0
)

print(f"Trade Created: {trade['id']}")

# Execute trade
result = manager.execute_trade(trade['id'])
print(f"Trade Executed: {result['order']}")

# Monitor trades
manager.monitor_trades(interval=5)
```

## Important Notes

1. **Risk Management**: Always use 1-2% risk per trade
2. **Stop Loss**: Never trade without SL
3. **Target**: Set realistic targets (2-3x risk)
4. **Position Size**: Let system calculate automatically
5. **Monitoring**: Always monitor active trades
6. **Exit Strategy**: Exit at target or SL, don't be greedy

## Commands Reference

```bash
# Setup trade
python setup_trade.py --symbol BTCUSDT --type LONG --entry 45000 --sl 44500 --target 46500

# Execute trade
python setup_trade.py --symbol BTCUSDT --type LONG --entry 45000 --sl 44500 --target 46500 --execute

# Monitor trades
python trade_dashboard.py --broker delta --monitor

# View dashboard
python trade_dashboard.py --broker delta
```

Happy Trading! 🚀



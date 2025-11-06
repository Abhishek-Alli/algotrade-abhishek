# Delta Exchange API Integration

Delta Exchange crypto derivatives exchange ke liye API client add kar diya hai.

## Delta Exchange Kya Hai?

Delta Exchange ek crypto derivatives exchange hai jahan aap:
- **Perpetual Futures**: BTC, ETH, etc. ke perpetual contracts
- **Futures**: Expiry wale futures contracts
- **Options**: Call aur Put options

## API Key Setup

### 1. Delta Exchange Account

1. Delta Exchange website pe account banayein: https://www.delta.exchange/
2. Login karein

### 2. API Key Generate Karein

1. Top-right corner mein username click karein
2. **"API Management"** select karein
3. **"Create New Key"** click karein
4. API key ko naam dein (e.g., "Trading Bot")
5. **Permissions** set karein:
   - Trading ke liye **Trading** permission enable karein
   - Data ke liye **Read** permission sufficient hai
6. **IP Whitelisting**: Trading permissions ke liye IP whitelist karein
   - Aapke current IP address ko whitelist karein
   - Multiple IPs add kar sakte ho

### 3. API Credentials

API key create hone ke baad:
- **API Key**: Copy karein
- **API Secret**: Copy karein (yeh sirf ek baar dikhayega)

⚠️ **Important**: API Secret ko save kar lein - dobara nahi dikhayega!

## Configuration

`.env` file mein Delta Exchange settings add karein:

```env
# Broker Selection
BROKER=delta

# Delta Exchange API Credentials
API_KEY=your_delta_api_key_here
API_SECRET=your_delta_api_secret_here

# Delta Exchange Settings
DELTA_TESTNET=false  # true for testnet, false for production

# Trading Symbol (Delta Exchange format)
SYMBOL=BTCUSDT  # Example: BTCUSDT, ETHUSDT, etc.
```

## Usage

### 1. Basic Trading

```bash
# Trading engine start karein
python main.py
```

### 2. AI Trading System

```bash
# Delta Exchange ke saath AI trading
python ai_main.py --broker delta --strategy ml
```

### 3. Data Collection

```bash
# Delta Exchange data collect karein
python data_collector.py --broker delta --symbols "BTCUSDT" "ETHUSDT"
```

### 4. Symbol Analysis

```bash
# Delta Exchange symbol analyze karein
python ai_main.py --broker delta --analyze "BTCUSDT"
```

## Delta Exchange Symbols

Delta Exchange pe symbols format:
- **Perpetual Futures**: `BTCUSDT`, `ETHUSDT`
- **Futures**: `BTC-30JAN24-USD`, `ETH-30JAN24-USD`
- **Options**: Complex format

Available products check karne ke liye:
```python
from api_client import DeltaExchangeClient

client = DeltaExchangeClient()
products = client.get_products()
print(products)
```

## Features

✅ **Market Orders**: Instant execution  
✅ **Limit Orders**: Price specified orders  
✅ **Stop Loss Orders**: Automatic stop loss  
✅ **Position Management**: Current positions check  
✅ **Order Management**: Cancel orders, check status  
✅ **Historical Data**: Candlestick data  
✅ **Real-time Prices**: Latest prices  

## Testnet vs Production

### Testnet (Development)

```env
DELTA_TESTNET=true
```

- Test trading ke liye
- Real money risk nahi
- Testing ke liye perfect

### Production (Live Trading)

```env
DELTA_TESTNET=false
```

- Real money trading
- Real positions
- ⚠️ Careful use karein!

## API Rate Limits

Delta Exchange API rate limits:
- Check Delta Exchange documentation
- Rate limiting handle karein
- Respect API limits

## Security

1. **API Secret**: Never share karein
2. **IP Whitelisting**: Trading ke liye required
3. **Permissions**: Minimum required permissions use karein
4. **Testnet First**: Pehle testnet pe test karein

## Example Code

```python
from api_client import DeltaExchangeClient
from config import Config

# Initialize client
client = DeltaExchangeClient(
    api_key=Config.API_KEY,
    api_secret=Config.API_SECRET,
    testnet=False
)

# Get account balance
balance = client.get_account_balance()
print(f"Balance: {balance}")

# Get current price
price = client.get_current_price("BTCUSDT")
print(f"BTC Price: {price}")

# Place market order
order = client.place_market_order(
    symbol="BTCUSDT",
    side="BUY",
    quantity=0.001
)
print(f"Order placed: {order}")

# Get positions
positions = client.get_positions()
print(f"Positions: {positions}")
```

## Troubleshooting

### Connection Error

**Problem**: Cannot connect to Delta Exchange

**Solution**:
- Check internet connection
- Verify API key and secret
- Check if IP is whitelisted (for trading)

### Authentication Error

**Problem**: Invalid signature

**Solution**:
- Verify API secret is correct
- Check timestamp synchronization
- Verify signature generation

### Order Placement Error

**Problem**: Order rejected

**Solution**:
- Check sufficient balance
- Verify symbol format
- Check product ID
- Verify IP whitelisting

## Notes

- Delta Exchange uses different authentication method
- Signature generation: `method + timestamp + path + query + body`
- Product IDs required for some operations
- Testnet available for safe testing

## Support

- Delta Exchange Docs: https://docs.delta.exchange/
- API Reference: Check Delta Exchange documentation

Happy Trading! 🚀



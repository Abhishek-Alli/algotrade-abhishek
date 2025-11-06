# Trading Software - Python with API Integration

A comprehensive trading software built in Python with API integration for cryptocurrency trading and **Indian Stock Market (NSE/BSE) including Futures & Options**.

## Features

- **Multiple Broker Support**: 
  - **Cryptocurrency**: Binance, Coinbase
  - **Indian Stock Market**: Zerodha Kite Connect, Angel One SmartAPI
- **Trading Strategies**: Moving Average, RSI Momentum, Bollinger Bands
- **Risk Management**: Position sizing, stop loss, take profit, daily loss limits
- **Real-time Trading**: Market order execution with automatic position management
- **F&O Support**: Futures and Options trading for Indian market
- **Market Hours**: Automatic market hours detection for Indian stock market
- **Logging**: Comprehensive logging for monitoring and debugging

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ppc
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file from `.env.example`:
```bash
cp .env.example .env
```

4. Configure your API credentials in `.env`:
```
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here
TESTNET=true  # Use testnet for testing
```

## Usage

### For Cryptocurrency Trading

Run the trading software:
```bash
python main.py
```

### For Indian Stock Market (NSE/BSE) - Futures & Options

Run the Indian market trading software:
```bash
python main_indian.py
```

**Setup for Zerodha Kite Connect:**
1. Get API key and secret from Kite Connect developer console
2. Generate request_token using login flow
3. Generate access_token using `get_access_token(request_token)` method
4. Set `API_PASSPHRASE=your_access_token` in `.env`

**Setup for Angel One SmartAPI:**
1. Get API key from Angel One developer console
2. Set `API_KEY`, `API_SECRET=client_id`, `API_PASSPHRASE=password` in `.env`
3. Provide TOTP during authentication

### Configuration

Edit `config.py` or set environment variables in `.env`:

**For Cryptocurrency:**
- **API Credentials**: Your broker API key and secret
- **Symbol**: Trading pair (e.g., BTCUSDT)
- **Broker**: binance, coinbase

**For Indian Stock Market:**
- **BROKER**: zerodha or angelone
- **EXCHANGE**: NSE, BSE, NFO (for F&O)
- **PRODUCT_TYPE**: MIS (Intraday), CNC (Delivery), NRML (Carry Forward)
- **SYMBOL**: Stock symbol (e.g., NSE:INFY, NFO:NIFTY24JANFUT)
- **Market Hours**: Automatic detection (9:15 AM - 3:30 PM IST)

**Common Settings:**
- **Strategy**: Choose from MovingAverageStrategy, RSIMomentumStrategy, or BollingerBandsStrategy
- **Risk Parameters**: Stop loss, take profit, max daily loss

### Changing Strategy

Edit `main.py` to use a different strategy:

```python
# Use RSI Strategy
strategy = RSIMomentumStrategy()

# Use Bollinger Bands Strategy
strategy = BollingerBandsStrategy()
```

## Project Structure

```
ppc/
├── main.py                  # Main entry point (cryptocurrency)
├── main_indian.py           # Main entry point (Indian stock market)
├── trading_engine.py        # Core trading engine
├── api_client.py            # API client for brokers
├── indian_market_utils.py   # Utilities for Indian market (F&O)
├── strategy.py              # Trading strategies
├── risk_manager.py          # Risk management
├── config.py                # Configuration
├── requirements.txt         # Dependencies
├── .env.example             # Environment variables template
└── README.md                # This file
```

## API Client

The `APIClient` class provides a unified interface for:
- Getting account balance
- Fetching market data (candlesticks)
- Placing orders (market, limit, stop loss)
- Managing positions

## Strategies

### Moving Average Crossover
- Golden cross (buy) and death cross (sell) signals
- Configurable fast and slow periods

### RSI Momentum
- Oversold/overbought conditions
- Momentum-based entry/exit

### Bollinger Bands
- Mean reversion strategy
- Buy at lower band, sell at upper band

## Risk Management

- **Position Sizing**: Based on account balance and risk percentage
- **Stop Loss**: Automatic stop loss orders
- **Take Profit**: Automatic profit taking
- **Daily Loss Limit**: Prevents excessive losses
- **Maximum Position Size**: Caps individual position sizes

## Safety Features

- Testnet support for safe testing
- Comprehensive error handling
- Logging for audit trail
- Graceful shutdown on interrupt

## Indian Stock Market Features

### Futures & Options (F&O) Trading

- **Futures**: Support for NIFTY, BANKNIFTY, FINNIFTY futures
- **Options**: Support for Call and Put options
- **Lot Sizing**: Automatic lot size calculation
- **Expiry Handling**: Automatic expiry date management
- **Product Types**: 
  - **MIS**: Intraday (Margin Intraday Square-off)
  - **CNC**: Delivery (Cash and Carry)
  - **NRML**: Carry Forward (Normal)

### Market Utilities

- `get_fno_symbol()`: Generate F&O symbols
- `get_next_expiry_date()`: Get next expiry date
- `is_market_open()`: Check if market is open
- `get_lot_size()`: Get lot size for F&O instruments

### Example F&O Symbols

```
# NIFTY Future
NFO:NIFTY24JANFUT

# NIFTY Call Option
NFO:NIFTY24JAN18000CE

# NIFTY Put Option
NFO:NIFTY24JAN18000PE
```

## Important Notes

⚠️ **WARNING**: 
- This software is for educational purposes only
- Always test on testnet/demo before using real funds
- Trading involves significant risk - use at your own discretion
- Ensure compliance with broker terms and regulations
- For Indian market: Verify market hours and holidays before trading

## License

This project is for educational purposes only.


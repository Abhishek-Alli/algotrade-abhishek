# Data Collection Service

Automatic data collection har minute local database mein store hota hai.

## Features

✅ **Automatic Data Collection**: Har minute data collect hota hai  
✅ **Multiple Timeframes**: 1m, 5m, 15m, 1h, 1d data store hota hai  
✅ **Price Data**: OHLCV data SQLite database mein  
✅ **News Data**: News articles with sentiment scores  
✅ **Background Service**: Trading engine ke saath automatically start hota hai  

## Usage

### 1. Standalone Data Collector

Data collection service ko separately run kar sakte ho:

```bash
# Basic usage (default: 1 minute interval)
python data_collector.py --symbols "NSE:RELIANCE" "NSE:TCS" "NFO:NIFTY24JANFUT"

# Custom interval (30 seconds)
python data_collector.py --symbols "BTCUSDT" --interval 30

# Zerodha ke liye
python data_collector.py --broker zerodha --symbols "NSE:RELIANCE"

# Data statistics check karo
python data_collector.py --stats
```

### 2. Trading Engine ke saath

Trading engine automatically data collect karta hai:

```bash
# Trading engine start karo - automatically data collection start hogi
python main.py

# AI trading system
python ai_main.py --broker zerodha --strategy ml
```

### 3. Stored Data Check Karo

```bash
# All data check karo
python check_data.py

# Specific symbol check karo
python check_data.py --symbol "NSE:RELIANCE"

# Only price data
python check_data.py --type price

# Only news data
python check_data.py --type news
```

## Database Structure

### Price Data (`market_data.db`)

Table: `ohlcv_data`

Columns:
- `symbol`: Trading symbol (e.g., NSE:RELIANCE)
- `timestamp`: Timestamp
- `open`, `high`, `low`, `close`: OHLC prices
- `volume`: Trading volume
- `timeframe`: Timeframe (1m, 5m, 1h, etc.)

### News Data (`news_data.db`)

Table: `news_data`

Columns:
- `symbol`: Trading symbol
- `headline`: News headline
- `source`: News source
- `published_at`: Publication timestamp
- `sentiment_score`: Sentiment score (-1 to +1)
- `content`: News content
- `url`: News URL

## Data Collection Timeframes

Default timeframes jo collect hote hain:
- **1m**: 1 minute candles
- **5m**: 5 minute candles
- **15m**: 15 minute candles
- **1h**: 1 hour candles
- **1d**: Daily candles

## Configuration

`.env` file mein:

```env
# Broker API (data collection ke liye required)
API_KEY=your_api_key
API_SECRET=your_api_secret
API_PASSPHRASE=your_access_token

# News API (optional, news data ke liye)
NEWS_API_KEY=your_newsapi_key

# Trading symbol
SYMBOL=NSE:RELIANCE
```

## Example Output

### Data Statistics

```
Data Check - 2024-01-15 10:30:00

================================================================================
PRICE DATA (OHLCV)
================================================================================
symbol        timeframe  count  first_record         last_record
NSE:RELIANCE  1m         1440   2024-01-15 09:15:00  2024-01-15 15:30:00
NSE:RELIANCE  5m         288    2024-01-15 09:15:00  2024-01-15 15:30:00
NSE:RELIANCE  1h         6      2024-01-15 09:15:00  2024-01-15 15:00:00
NSE:RELIANCE  1d         1      2024-01-15 00:00:00  2024-01-15 00:00:00

Recent 10 records for NSE:RELIANCE:
timestamp            open    high    low     close   volume
2024-01-15 15:30:00  2450.00 2455.00 2448.00 2452.00 1250000
2024-01-15 15:29:00  2449.00 2451.00 2447.00 2450.00 1180000
...
```

## Benefits

1. **Historical Data**: Long-term data analysis ke liye
2. **ML Training**: ML models train karne ke liye historical data
3. **Backtesting**: Strategies ko test karne ke liye
4. **Offline Analysis**: Internet connection ke bina bhi analysis
5. **Data Backup**: Local backup of all trading data

## Notes

- Data automatically SQLite database mein store hota hai
- Database files: `market_data.db`, `news_data.db`
- Har minute new data add hota hai
- Old data automatically preserve hota hai
- Trading engine stop karne par data collection bhi stop ho jati hai

## Troubleshooting

**Problem**: Data collect nahi ho raha

**Solution**: 
- Check API credentials in `.env`
- Check broker connection
- Check logs: `trading.log`

**Problem**: Database file size badh raha hai

**Solution**: 
- Regularly clean old data if needed
- Use SQLite commands to archive old data
- Database files are lightweight, but can grow over time



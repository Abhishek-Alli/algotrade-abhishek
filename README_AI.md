# AI-Powered Trading System

Complete AI trading system with data ingestion, feature engineering, ML models, and advanced strategies.

## Architecture

### Phase 1: Data Ingestion & Fusion
- **Price Data**: OHLCV from broker APIs (Zerodha, Angel One, Binance)
- **News Data**: NewsAPI integration with sentiment analysis
- **Sentiment Data**: Social media sentiment (Twitter, Reddit)
- **On-Chain Data**: Crypto on-chain metrics (Fear & Greed Index)
- **Macro Data**: Economic indicators (Interest rates, GDP)

### Phase 2: Feature Engineering
- **Technical Indicators**: SMA, EMA, MACD, RSI, Bollinger Bands, ATR, VWAP, OBV
- **Sentiment Features**: 24h sentiment average, news volume spikes
- **F&O Features**: Open interest, Put-Call ratio, Implied Volatility
- **Price Features**: Price changes, support/resistance levels

### Phase 3: ML Models
- **XGBoost**: Gradient boosting for price direction prediction
- **LightGBM**: Fast gradient boosting
- **LSTM**: Deep learning for sequence analysis
- **Ensemble**: Multiple models for better predictions

### Phase 4: Advanced Strategies
1. **News Momentum**: Trade on strong news sentiment
2. **Mean Reversion**: Buy dips in uptrends with sentiment filter
3. **IV Crush**: Options strategy for volatility events
4. **Crypto On-Chain**: Fear & Greed + on-chain metrics
5. **ML-Based**: AI-driven predictions

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### 1. Analysis Mode

Analyze a symbol comprehensively:
```bash
python ai_main.py --analyze "NSE:RELIANCE"
```

Or using natural language:
```bash
python ai_main.py --query "Give me details on RELIANCE"
```

### 2. Training ML Model

Train ML model on historical data:
```bash
python ai_main.py --train "NSE:RELIANCE" --strategy ml
```

### 3. Live Trading

Start AI trading system:
```bash
python ai_main.py --broker zerodha --strategy ml
```

Available strategies:
- `ml`: ML-based predictions
- `news_momentum`: News-based momentum
- `mean_reversion`: Mean reversion with sentiment
- `crypto_onchain`: Crypto on-chain strategy

## Configuration

Update `.env` file:
```
# Broker API
API_KEY=your_api_key
API_SECRET=your_api_secret
API_PASSPHRASE=your_access_token

# Data Sources
NEWS_API_KEY=your_newsapi_key
ALPHA_VANTAGE_KEY=your_alpha_vantage_key

# Trading Settings
BROKER=zerodha
SYMBOL=NSE:RELIANCE
EXCHANGE=NSE
PRODUCT_TYPE=MIS
```

## Example AI Analysis Output

```
============================================================
COMPREHENSIVE ANALYSIS: NSE:RELIANCE
============================================================

1. TECHNICAL VIEW
   Current Price: ₹2450.00
   Trend: Bullish
   Momentum: Neutral (RSI: 58.2)
   
   Key Levels:
   - Support: ₹2400.00
   - Resistance: ₹2500.00
   
   Moving Averages:
   - SMA 20: ₹2435.00
   - SMA 50: ₹2420.00
   - SMA 200: ₹2400.00

2. NEWS & SENTIMENT ANALYSIS
   Sentiment Score (24h): 0.650 (Positive)
   News Count (24h): 12
   
   Recent Headlines:
   - Reliance Jio announces new 5G partnership... (Sentiment: 0.75)
   - RIL reports Q3 profits in line with estimates... (Sentiment: 0.50)

3. F&O DATA
   Open Interest: 45000
   Put-Call Ratio: 1.15
   Implied Volatility: 28.50%

4. AI-GENERATED TRADE IDEAS

   Scenario 1: Breakout (LONG)
   Entry: ₹2505.00
   Target 1: ₹2575.00
   Target 2: ₹2625.00
   Stop Loss: ₹2455.00
   Confidence: Medium
   Reasoning: Breakout above resistance with positive sentiment (0.65)

   Scenario 2: Dip Buy (LONG)
   Entry: ₹2425.00
   Target 1: ₹2500.00
   Target 2: ₹2450.00
   Stop Loss: ₹2376.00
   Confidence: Medium-High
   Reasoning: Mean reversion in uptrend. RSI at 38.5, sentiment positive
```

## Advanced Risk Management

Position sizing formula:
```
Position Size = (Account Risk %) / (Entry Price - Stop-Loss Price)
```

Example:
- Account: ₹100,000
- Risk: 1%
- Entry: ₹2450
- Stop Loss: ₹2400
- Position Size = (100,000 × 0.01) / (2450 - 2400) = 20 units

## Strategies Explained

### News Momentum Strategy
- **Trigger**: Sentiment score > 0.7 (very positive news)
- **Confirmation**: Price above VWAP + Volume spike (150% average)
- **Entry**: Buy on next candle
- **SL**: 1.5% below entry or pre-news low
- **TP**: 1x risk (1.5%), exit at RSI > 80

### Mean Reversion Strategy
- **Trigger**: Price above 200 EMA + Positive sentiment (>0.2)
- **Signal**: RSI dips below 30, then crosses back above
- **Entry**: When RSI crosses above 30
- **SL**: Below recent swing low
- **TP**: Upper Bollinger Band or resistance

### Crypto On-Chain Strategy
- **Trigger**: Fear & Greed Index < 20 (Extreme Fear) + Reserves decreasing
- **Confirmation**: Price near 200-week MA support
- **Entry**: Accumulate in tranches
- **SL**: Weekly close below support
- **TP**: Scale out as Fear & Greed moves to Greed (>75)

## Project Structure

```
ppc/
├── ai_main.py                 # AI system entry point
├── data_ingestion.py          # Data collection & fusion
├── feature_engineering.py     # Feature creation
├── ml_models.py               # ML models (XGBoost, LSTM)
├── advanced_strategies.py    # Advanced strategies
├── ai_analysis.py             # AI analysis interface
├── trading_engine.py          # Core trading engine
├── api_client.py              # Broker APIs
├── strategy.py                # Base strategies
├── risk_manager.py            # Risk management
└── config.py                  # Configuration
```

## Important Notes

⚠️ **WARNING**:
- This is a sophisticated trading system requiring extensive testing
- Always test on paper trading/demo accounts first
- ML models need sufficient historical data for training
- News API keys required for sentiment analysis
- Risk management is critical - never risk more than 1-2% per trade

## Next Steps

1. **Get API Keys**: NewsAPI, Alpha Vantage (optional)
2. **Train Models**: Collect historical data and train ML models
3. **Paper Trading**: Test strategies in demo mode
4. **Backtesting**: Validate strategies on historical data
5. **Live Trading**: Start with small position sizes

## License

This project is for educational purposes only.



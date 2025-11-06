# Trading Dashboard

Complete multi-page web dashboard for trading management.

## Features

✅ **Multi-Page Navigation**: Dashboard, Trades, Charts, Indicators, Strategies, Profile, Settings  
✅ **Sidebar Navigation**: Easy navigation between sections  
✅ **Account Balance**: Real-time balance display  
✅ **Charts**: Interactive candlestick charts with Plotly  
✅ **Indicators**: RSI, MACD, ATR, Bollinger Bands  
✅ **Strategies**: Multiple trading strategies  
✅ **Trade Management**: Create, monitor, close trades  
✅ **Long/Short Positions**: Track all positions  
✅ **Real-time Updates**: Auto-refresh option  

## Installation

```bash
pip install -r requirements.txt
```

## Running the Dashboard

```bash
# Method 1: Direct run
streamlit run dashboard_app.py

# Method 2: Using run script
python run_dashboard.py
```

Dashboard automatically opens in browser at: `http://localhost:8501`

## Dashboard Pages

### 1. Dashboard (Home)
- Account balance
- Total P&L
- Active trades count
- Long positions
- Short positions
- Trading statistics
- Win rate

### 2. Trades
- **New Trade**: Create new trades
- **Active Trades**: View all active trades
- **Trade History**: All trades history
- **Close Trade**: Manually close trades

### 3. Charts
- Interactive candlestick charts
- Volume charts
- Multiple timeframes
- Real-time price updates

### 4. Indicators
- RSI indicator
- MACD indicator
- Bollinger Bands
- ATR
- Support/Resistance levels
- Visual indicator charts

### 5. Strategies
- Moving Average strategy
- RSI Momentum strategy
- Bollinger Bands strategy
- Auto trade signal generation
- One-click trade execution
- **Strategy Backtesting**: Test strategies on historical data
  - Compare multiple strategies
  - View performance metrics (Win Rate, P&L, Sharpe Ratio, etc.)
  - Equity curve visualization
  - Trade history analysis

### 6. Profile
- Account information
- Broker settings
- Account statistics
- Profile photo

### 7. Settings
- Trading settings
- Risk management
- Notification settings
- Auto-execute options

## Usage

### 1. Connect to Broker

1. Open sidebar
2. Select broker (Delta, Binance, Zerodha)
3. Click "Connect" button
4. Wait for connection confirmation

### 2. Create Trade

1. Go to "Trades" page
2. Click "New Trade" tab
3. Fill in:
   - Symbol
   - Position Type (LONG/SHORT)
   - Entry Price
   - Stop Loss
   - Target Price
   - Risk %
4. Click "Create Trade"

### 3. View Charts

1. Go to "Charts" page
2. Enter symbol
3. Select timeframe
4. Click "Load Chart"

### 4. Check Indicators

1. Go to "Indicators" page
2. Enter symbol
3. Select timeframe
4. Click "Calculate Indicators"

### 5. Use Strategies

1. Go to "Strategies" page
2. Select strategy
3. Enter symbol
4. Click "Generate Trade Signal"
5. Review and execute if needed

### 6. Backtest Strategies

1. Go to "Strategies" page
2. Click "Backtesting" tab
3. Select strategies to backtest
4. Set parameters:
   - Symbol and timeframe
   - Initial capital
   - Position size percentage
   - Commission rate
5. Click "Run Backtest"
6. View results:
   - Summary metrics table
   - Equity curve comparison chart
   - Detailed results for each strategy
   - Trade history

## Dashboard Features

### Sidebar
- Broker selection
- Connection status
- Account balance
- Auto-refresh toggle
- Navigation menu

### Main Content
- Dynamic content based on selected page
- Real-time updates
- Interactive charts
- Trade management

### Responsive Design
- Works on desktop and mobile
- Wide layout for charts
- Optimized for trading

## Example Workflow

1. **Connect**: Select broker and connect
2. **Analyze**: Check charts and indicators
3. **Strategy**: Generate trade signal
4. **Execute**: Create and execute trade
5. **Monitor**: Watch active trades on dashboard
6. **Close**: Close trade when target/SL hit

## Screenshots

### Dashboard View
- Account summary
- Active positions
- Trading statistics

### Charts View
- Candlestick charts
- Volume analysis
- Multiple timeframes

### Indicators View
- RSI chart
- MACD chart
- Bollinger Bands

## Customization

### Themes
Edit `dashboard_app.py` to customize:
- Colors
- Layout
- Components

### Add New Pages
Add new page function and route in main router

### Custom Indicators
Add custom indicators in `indicators_page()` function

## Troubleshooting

### Dashboard Not Loading
- Check if Streamlit is installed
- Verify port 8501 is available
- Check browser console for errors

### Connection Failed
- Verify API credentials in `.env`
- Check broker API status
- Verify IP whitelisting (for trading)

### Charts Not Displaying
- Check symbol format
- Verify API connection
- Check data availability

## Security Notes

⚠️ **Important**:
- Dashboard runs on localhost by default
- Don't expose to public internet
- Use authentication for production
- Keep API keys secure

## Next Steps

1. **Deploy**: Deploy to cloud (Heroku, AWS, etc.)
2. **Authentication**: Add login system
3. **Notifications**: Add email/SMS alerts
4. **Backtesting**: Add strategy backtesting
5. **Alerts**: Price alerts and notifications

Happy Trading! 🚀



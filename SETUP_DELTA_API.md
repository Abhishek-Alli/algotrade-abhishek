# Delta Exchange API Key Setup Guide

## Step 1: Delta Exchange pe API Key Generate Karein

### 1.1 Login Karein
1. Delta Exchange website pe jayein: https://www.delta.exchange/
2. Apna account se login karein

### 1.2 API Key Create Karein
1. Top-right corner mein **username** click karein
2. **"API Management"** select karein
3. **"Create New Key"** button click karein
4. API key ko naam dein (e.g., "Trading Bot")
5. **Permissions** set karein:
   - **Read**: Data fetch karne ke liye
   - **Trading**: Orders place karne ke liye (optional)
6. **IP Whitelisting** (Trading ke liye required):
   - Aapke current IP address ko whitelist karein
   - Multiple IPs add kar sakte ho
7. **Create** button click karein

### 1.3 API Credentials Copy Karein
- **API Key**: Copy karein
- **API Secret**: Copy karein (⚠️ Yeh sirf ek baar dikhayega!)

⚠️ **Important**: API Secret ko immediately save kar lein - dobara nahi dikhayega!

## Step 2: `.env` File Mein Add Karein

### 2.1 `.env` File Location
Project folder mein `.env` file create karein:
```
C:\Users\abhis\Desktop\ppc\.env
```

### 2.2 `.env` File Mein Ye Add Karein:

```env
# Delta Exchange API Credentials
API_KEY=your_delta_api_key_paste_here
API_SECRET=your_delta_api_secret_paste_here

# Broker Selection
BROKER=delta

# Delta Exchange Settings
DELTA_TESTNET=false
```

### 2.3 Example `.env` File:

```env
# API Credentials - Delta Exchange
API_KEY=abc123xyz456def789
API_SECRET=secret123xyz456secret789

# Broker/Exchange Settings
BROKER=delta
BASE_URL=https://api.delta.exchange
TESTNET=false

# Delta Exchange Settings
DELTA_TESTNET=false

# Trading Settings
SYMBOL=BTCUSDT
QUANTITY=0.001
MAX_POSITION_SIZE=0.01

# Risk Management
MAX_DAILY_LOSS=100.0
STOP_LOSS_PERCENT=2.0
TAKE_PROFIT_PERCENT=3.0

# Logging
LOG_LEVEL=INFO
LOG_FILE=trading.log

# PostgreSQL Database Settings
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_db
DB_USER=postgres
DB_PASSWORD=Abhi122103
DB_URL=
```

## Step 3: Verify Karein

### 3.1 Test Connection:

```bash
python test_db_connection.py
```

### 3.2 Simple Test Script:

Test file create karein: `test_delta_connection.py`

```python
from api_client import DeltaExchangeClient
from config import Config

try:
    client = DeltaExchangeClient(
        api_key=Config.API_KEY,
        api_secret=Config.API_SECRET,
        testnet=Config.DELTA_TESTNET
    )
    
    # Test connection
    balance = client.get_account_balance()
    print("✓ Delta Exchange connection successful!")
    print(f"Balance: {balance}")
    
except Exception as e:
    print(f"✗ Connection failed: {e}")
    print("\nCheck:")
    print("1. API_KEY correct hai?")
    print("2. API_SECRET correct hai?")
    print("3. IP whitelisted hai? (for trading)")
```

Run karein:
```bash
python test_delta_connection.py
```

## Step 4: Usage

### 4.1 Trading Engine Start Karein:

```bash
python main.py
```

### 4.2 Data Collection:

```bash
python data_collector.py --broker delta --symbols "BTCUSDT"
```

### 4.3 AI Trading System:

```bash
python ai_main.py --broker delta --strategy ml
```

## Important Notes:

1. **API Secret Security**:
   - `.env` file ko **NEVER** commit karein git mein
   - `.gitignore` mein `.env` add karein
   - Share mat karein kisi ke saath

2. **IP Whitelisting**:
   - Trading permissions ke liye IP whitelist karna zaroori hai
   - Dynamic IP ho to problem ho sakti hai
   - Static IP use karein

3. **Testnet First**:
   - Pehle testnet pe test karein:
   ```env
   DELTA_TESTNET=true
   ```

4. **Permissions**:
   - Read-only: Data fetch ke liye
   - Trading: Orders place karne ke liye
   - Minimum required permissions use karein

## Troubleshooting:

### Problem: Connection Failed
**Solution**:
- Check API_KEY aur API_SECRET correct hai
- Check `.env` file exists hai
- Check environment variables load ho rahe hain

### Problem: Invalid Signature
**Solution**:
- Verify API_SECRET correct hai
- Check timestamp synchronization
- Verify signature generation

### Problem: IP Not Whitelisted
**Solution**:
- Delta Exchange API Management mein IP whitelist karein
- Current IP check karein: https://whatismyipaddress.com/

## Quick Start Checklist:

- [ ] Delta Exchange account created
- [ ] API key generated
- [ ] API key and secret copied
- [ ] `.env` file created
- [ ] API_KEY added in `.env`
- [ ] API_SECRET added in `.env`
- [ ] BROKER=delta set kiya
- [ ] IP whitelisted (for trading)
- [ ] Test connection successful
- [ ] Ready to trade!

Happy Trading! 🚀



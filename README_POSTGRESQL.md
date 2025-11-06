# PostgreSQL Database Setup

Trading system ab PostgreSQL database use karta hai.

## Installation

### 1. PostgreSQL Install Karein

**Windows:**
- Download from: https://www.postgresql.org/download/windows/
- Install PostgreSQL with default settings

**Linux:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
```

### 2. Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `psycopg2-binary`: PostgreSQL adapter
- `sqlalchemy`: Database toolkit

### 3. Database Setup

#### Option 1: Using psql (Command Line)

```bash
# PostgreSQL ko start karein
sudo service postgresql start  # Linux
# Windows: Services se PostgreSQL start karein

# PostgreSQL me login karein
sudo -u postgres psql

# Database create karein
CREATE DATABASE trading_db;

# User create karein (optional)
CREATE USER trading_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_user;

# Exit
\q
```

#### Option 2: Using pgAdmin (GUI)

1. pgAdmin open karein
2. Right-click on "Databases" → Create → Database
3. Name: `trading_db`
4. Save

### 4. Configuration

`.env` file mein PostgreSQL settings add karein:

```env
# Database Type
DB_TYPE=postgresql

# PostgreSQL Connection
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_db
DB_USER=postgres
DB_PASSWORD=your_password

# OR Full Connection String
DB_URL=postgresql://postgres:your_password@localhost:5432/trading_db
```

## Usage

### Normal Usage

Trading system automatically PostgreSQL use karega:

```bash
# Trading engine start karein
python main.py

# AI system start karein
python ai_main.py --broker zerodha --strategy ml

# Data collector start karein
python data_collector.py --symbols "NSE:RELIANCE"
```

### Check Database

```bash
# Stored data check karein
python check_data.py

# Specific symbol
python check_data.py --symbol "NSE:RELIANCE"
```

## Database Structure

### Tables

1. **ohlcv_data**: Price data (OHLCV)
   - Columns: symbol, timestamp, open, high, low, close, volume, timeframe
   - Index: (symbol, timeframe, timestamp)

2. **news_data**: News articles
   - Columns: symbol, headline, source, published_at, sentiment_score, content, url
   - Index: (symbol, published_at)

3. **sentiment_data**: Social media sentiment
   - Columns: symbol, platform, text, timestamp, sentiment_score, engagement_score

## Switching Between Databases

### PostgreSQL to SQLite

`.env` file mein:
```env
DB_TYPE=sqlite
```

### SQLite to PostgreSQL

`.env` file mein:
```env
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_db
DB_USER=postgres
DB_PASSWORD=your_password
```

## Benefits of PostgreSQL

✅ **Better Performance**: Large datasets ke liye fast  
✅ **Concurrent Access**: Multiple users simultaneously  
✅ **Advanced Features**: Full-text search, JSON support  
✅ **Scalability**: Production-ready  
✅ **Data Integrity**: Better constraints and validation  
✅ **Backup & Recovery**: Built-in tools  

## Troubleshooting

### Connection Error

**Problem**: `psycopg2.OperationalError: could not connect`

**Solution**:
1. Check PostgreSQL service running: `sudo service postgresql status`
2. Check credentials in `.env`
3. Check firewall settings
4. Verify database exists: `psql -l`

### Authentication Error

**Problem**: `password authentication failed`

**Solution**:
1. Check password in `.env`
2. Verify user exists: `psql -U postgres -l`
3. Update `pg_hba.conf` if needed

### Table Not Found

**Problem**: Tables don't exist

**Solution**:
- Tables automatically create hote hain first run pe
- Or manually run `setup_postgresql.sql`

## Migration from SQLite

Agar SQLite se migrate karna hai:

1. Export SQLite data:
```bash
sqlite3 market_data.db .dump > export.sql
```

2. Import to PostgreSQL:
```bash
psql trading_db < export.sql
```

Ya phir application automatically new data PostgreSQL mein store karega.

## Performance Tips

1. **Indexes**: Automatically created for common queries
2. **Connection Pooling**: Built-in connection pool
3. **Batch Inserts**: Efficient bulk inserts
4. **Vacuum**: Regular vacuum for performance

```sql
-- Manual vacuum
VACUUM ANALYZE ohlcv_data;
```

## Backup

```bash
# Backup database
pg_dump -U postgres trading_db > backup.sql

# Restore database
psql -U postgres trading_db < backup.sql
```

## Notes

- Tables automatically create hote hain first run pe
- Connection pooling automatically handle hota hai
- Both PostgreSQL and SQLite support available
- Easy switching between databases via config



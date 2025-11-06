"""
Test PostgreSQL Database Connection
Database connection verify karne ke liye
"""
import logging
from database import get_db
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_connection():
    """Test database connection"""
    print("="*60)
    print("Testing PostgreSQL Database Connection")
    print("="*60)
    
    print(f"\nDatabase Configuration:")
    print(f"  Type: {Config.DB_TYPE}")
    print(f"  Host: {Config.DB_HOST}")
    print(f"  Port: {Config.DB_PORT}")
    print(f"  Database: {Config.DB_NAME}")
    print(f"  User: {Config.DB_USER}")
    print(f"  Password: {'*' * len(Config.DB_PASSWORD)}")
    
    try:
        # Get database connection
        print("\n1. Connecting to database...")
        db = get_db()
        print(f"   ✓ Database connection created (Type: {db.db_type})")
        
        # Test connection
        print("\n2. Testing connection...")
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"   ✓ PostgreSQL version: {version[0]}")
        
        # Check if database exists and is accessible
        cursor.execute("SELECT current_database();")
        current_db = cursor.fetchone()
        print(f"   ✓ Connected to database: {current_db[0]}")
        
        # Check tables
        print("\n3. Checking tables...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"   ✓ Found {len(tables)} table(s):")
            for table in tables:
                print(f"      - {table[0]}")
        else:
            print("   ℹ No tables found (will be created on first run)")
        
        # Return connection
        if db.db_type == 'postgresql':
            db.return_connection(conn)
        
        print("\n" + "="*60)
        print("✓ Database connection test PASSED!")
        print("="*60)
        print("\nAb aap trading system use kar sakte ho:")
        print("  python main.py")
        print("  python ai_main.py --broker zerodha")
        print("  python data_collector.py --symbols 'NSE:RELIANCE'")
        print("\n")
        
        return True
        
    except Exception as e:
        print("\n" + "="*60)
        print("✗ Database connection test FAILED!")
        print("="*60)
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("1. Check PostgreSQL service running:")
        print("   - Windows: Services app mein PostgreSQL check karein")
        print("   - Linux: sudo service postgresql status")
        print("\n2. Verify credentials in .env file:")
        print("   - DB_HOST=localhost")
        print("   - DB_PORT=5432")
        print("   - DB_NAME=trading_db")
        print("   - DB_USER=postgres")
        print("   - DB_PASSWORD=your_password")
        print("\n3. Check pgAdmin mein database exists:")
        print("   - Right click on Databases → Refresh")
        print("   - trading_db dikhna chahiye")
        print("\n4. Test connection manually:")
        print("   psql -U postgres -d trading_db")
        print("\n")
        return False


if __name__ == "__main__":
    test_connection()



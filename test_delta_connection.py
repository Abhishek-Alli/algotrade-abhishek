"""
Test Delta Exchange API Connection
"""
import logging
from api_client import DeltaExchangeClient
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_delta_connection():
    """Test Delta Exchange connection"""
    print("="*60)
    print("Testing Delta Exchange API Connection")
    print("="*60)
    
    print(f"\nConfiguration:")
    print(f"  API Key: {Config.API_KEY[:10]}..." if Config.API_KEY else "  API Key: NOT SET")
    print(f"  API Secret: {'*' * 10}..." if Config.API_SECRET else "  API Secret: NOT SET")
    print(f"  Broker: {Config.BROKER}")
    print(f"  Testnet: {Config.DELTA_TESTNET}")
    
    if not Config.API_KEY or not Config.API_SECRET:
        print("\n" + "="*60)
        print("✗ API Credentials NOT SET!")
        print("="*60)
        print("\nPlease add in .env file:")
        print("  API_KEY=your_delta_api_key")
        print("  API_SECRET=your_delta_api_secret")
        print("  BROKER=delta")
        print("\n")
        return False
    
    try:
        print("\n1. Initializing Delta Exchange client...")
        client = DeltaExchangeClient(
            api_key=Config.API_KEY,
            api_secret=Config.API_SECRET,
            testnet=Config.DELTA_TESTNET
        )
        print("   ✓ Client initialized")
        
        print("\n2. Testing connection...")
        # Test with account balance (signed request)
        try:
            balance = client.get_account_balance()
            print("   ✓ Connection successful!")
            print(f"   ✓ Balance data received")
        except Exception as e:
            print(f"   ⚠ Balance fetch failed (might need IP whitelisting): {e}")
        
        # Test with public data (no signature needed)
        print("\n3. Testing public data access...")
        try:
            products = client.get_products()
            print(f"   ✓ Public data access successful!")
            print(f"   ✓ Found {len(products)} products")
            
            if products:
                print(f"\n   Sample products:")
                for product in products[:5]:
                    print(f"     - {product.get('symbol', 'N/A')}: {product.get('description', 'N/A')}")
        except Exception as e:
            print(f"   ✗ Public data access failed: {e}")
            return False
        
        print("\n" + "="*60)
        print("✓ Delta Exchange connection test PASSED!")
        print("="*60)
        print("\nAb aap trading system use kar sakte ho:")
        print("  python main.py")
        print("  python ai_main.py --broker delta --strategy ml")
        print("  python data_collector.py --broker delta --symbols 'BTCUSDT'")
        print("\n")
        
        return True
        
    except Exception as e:
        print("\n" + "="*60)
        print("✗ Delta Exchange connection test FAILED!")
        print("="*60)
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("1. Check API_KEY aur API_SECRET correct hai?")
        print("2. Check .env file exists aur properly formatted hai?")
        print("3. Check IP whitelisted hai? (for trading)")
        print("4. Check internet connection?")
        print("5. Check Delta Exchange service status?")
        print("\n")
        return False


if __name__ == "__main__":
    test_delta_connection()



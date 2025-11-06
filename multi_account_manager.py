"""
Multi-Account Manager
Manage multiple trading accounts with API keys
Store accounts securely and execute trades on selected accounts
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import logging
from api_client import DeltaExchangeClient, BinanceClient, ZerodhaKiteClient
from config import Config

logger = logging.getLogger(__name__)


class AccountInfo:
    """Account information container"""
    
    def __init__(self, account_id: str, account_name: str, broker: str, 
                 api_key: str, api_secret: str, api_passphrase: str = None,
                 testnet: bool = False, is_active: bool = True):
        self.account_id = account_id
        self.account_name = account_name
        self.broker = broker.lower()
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        self.testnet = testnet
        self.is_active = is_active
        self.created_at = datetime.now().isoformat()
        self.last_used = None
        self.total_trades = 0
        self.total_pnl = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary (excluding sensitive data)"""
        return {
            'account_id': self.account_id,
            'account_name': self.account_name,
            'broker': self.broker,
            'testnet': self.testnet,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'last_used': self.last_used,
            'total_trades': self.total_trades,
            'total_pnl': self.total_pnl
        }
    
    def to_dict_full(self) -> Dict:
        """Convert to dictionary with sensitive data (for internal use)"""
        return {
            'account_id': self.account_id,
            'account_name': self.account_name,
            'broker': self.broker,
            'api_key': self.api_key,
            'api_secret': self.api_secret,
            'api_passphrase': self.api_passphrase,
            'testnet': self.testnet,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'last_used': self.last_used,
            'total_trades': self.total_trades,
            'total_pnl': self.total_pnl
        }


class MultiAccountManager:
    """Manage multiple trading accounts"""
    
    def __init__(self, accounts_file: str = "accounts.json"):
        """
        Initialize multi-account manager
        
        Args:
            accounts_file: Path to JSON file storing accounts
        """
        self.accounts_file = accounts_file
        self.accounts: Dict[str, AccountInfo] = {}
        self.api_clients: Dict[str, any] = {}  # Cache for API clients
        self.load_accounts()
    
    def load_accounts(self):
        """Load accounts from file"""
        if os.path.exists(self.accounts_file):
            try:
                with open(self.accounts_file, 'r') as f:
                    data = json.load(f)
                    for account_id, account_data in data.items():
                        account = AccountInfo(
                            account_id=account_data['account_id'],
                            account_name=account_data['account_name'],
                            broker=account_data['broker'],
                            api_key=account_data['api_key'],
                            api_secret=account_data['api_secret'],
                            api_passphrase=account_data.get('api_passphrase'),
                            testnet=account_data.get('testnet', False),
                            is_active=account_data.get('is_active', True)
                        )
                        account.created_at = account_data.get('created_at', account.created_at)
                        account.last_used = account_data.get('last_used')
                        account.total_trades = account_data.get('total_trades', 0)
                        account.total_pnl = account_data.get('total_pnl', 0.0)
                        self.accounts[account_id] = account
                logger.info(f"Loaded {len(self.accounts)} accounts")
            except Exception as e:
                logger.error(f"Error loading accounts: {e}")
                self.accounts = {}
        else:
            self.accounts = {}
    
    def save_accounts(self):
        """Save accounts to file"""
        try:
            data = {}
            for account_id, account in self.accounts.items():
                data[account_id] = account.to_dict_full()
            
            with open(self.accounts_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.accounts)} accounts")
        except Exception as e:
            logger.error(f"Error saving accounts: {e}")
            raise
    
    def add_account(self, account_name: str, broker: str, api_key: str, 
                    api_secret: str, api_passphrase: str = None,
                    testnet: bool = False) -> str:
        """
        Add a new account
        
        Args:
            account_name: Name for the account
            broker: Broker name (delta, binance, zerodha)
            api_key: API key
            api_secret: API secret
            api_passphrase: API passphrase (for Zerodha access_token)
            testnet: Whether using testnet
        
        Returns:
            Account ID
        """
        account_id = f"{broker}_{account_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        account = AccountInfo(
            account_id=account_id,
            account_name=account_name,
            broker=broker,
            api_key=api_key,
            api_secret=api_secret,
            api_passphrase=api_passphrase,
            testnet=testnet
        )
        
        self.accounts[account_id] = account
        self.save_accounts()
        logger.info(f"Added account: {account_name} ({account_id})")
        return account_id
    
    def update_account(self, account_id: str, account_name: str = None,
                      api_key: str = None, api_secret: str = None,
                      api_passphrase: str = None, testnet: bool = None,
                      is_active: bool = None) -> bool:
        """Update account information"""
        if account_id not in self.accounts:
            return False
        
        account = self.accounts[account_id]
        
        if account_name is not None:
            account.account_name = account_name
        if api_key is not None:
            account.api_key = api_key
        if api_secret is not None:
            account.api_secret = api_secret
        if api_passphrase is not None:
            account.api_passphrase = api_passphrase
        if testnet is not None:
            account.testnet = testnet
        if is_active is not None:
            account.is_active = is_active
        
        # Clear cached client
        if account_id in self.api_clients:
            del self.api_clients[account_id]
        
        self.save_accounts()
        logger.info(f"Updated account: {account_id}")
        return True
    
    def delete_account(self, account_id: str) -> bool:
        """Delete an account"""
        if account_id not in self.accounts:
            return False
        
        account_name = self.accounts[account_id].account_name
        del self.accounts[account_id]
        
        # Clear cached client
        if account_id in self.api_clients:
            del self.api_clients[account_id]
        
        self.save_accounts()
        logger.info(f"Deleted account: {account_name} ({account_id})")
        return True
    
    def get_account(self, account_id: str) -> Optional[AccountInfo]:
        """Get account information (without sensitive data)"""
        if account_id in self.accounts:
            return self.accounts[account_id]
        return None
    
    def get_all_accounts(self, active_only: bool = False) -> List[Dict]:
        """Get all accounts"""
        accounts = []
        for account_id, account in self.accounts.items():
            if active_only and not account.is_active:
                continue
            accounts.append(account.to_dict())
        return accounts
    
    def get_api_client(self, account_id: str):
        """Get or create API client for account"""
        if account_id not in self.accounts:
            raise ValueError(f"Account {account_id} not found")
        
        # Return cached client if available
        if account_id in self.api_clients:
            return self.api_clients[account_id]
        
        account = self.accounts[account_id]
        
        # Create API client based on broker
        if account.broker == 'delta':
            client = DeltaExchangeClient(
                api_key=account.api_key,
                api_secret=account.api_secret,
                testnet=account.testnet
            )
        elif account.broker == 'binance':
            client = BinanceClient(testnet=account.testnet)
            client.api_key = account.api_key
            client.api_secret = account.api_secret
        elif account.broker == 'zerodha':
            client = ZerodhaKiteClient(
                api_key=account.api_key,
                api_secret=account.api_secret,
                access_token=account.api_passphrase
            )
        else:
            raise ValueError(f"Unknown broker: {account.broker}")
        
        # Cache client
        self.api_clients[account_id] = client
        
        # Update last used
        account.last_used = datetime.now().isoformat()
        self.save_accounts()
        
        return client
    
    def get_account_balance(self, account_id: str) -> float:
        """Get account balance"""
        try:
            client = self.get_api_client(account_id)
            balance_data = client.get_account_balance()
            
            if isinstance(balance_data, dict):
                if 'result' in balance_data:
                    balances = balance_data.get('result', {}).get('balances', [])
                    if balances:
                        return sum(float(b.get('balance', 0)) for b in balances)
                    return float(balance_data.get('result', {}).get('available_balance', 0))
                elif 'balances' in balance_data:
                    for asset in balance_data.get('balances', []):
                        if asset.get('asset') == 'USDT':
                            return float(asset.get('free', 0))
            return 0.0
        except Exception as e:
            logger.error(f"Error getting balance for {account_id}: {e}")
            return 0.0
    
    def execute_trade_on_accounts(self, account_ids: List[str], trade_data: Dict) -> Dict:
        """
        Execute trade on multiple accounts
        
        Args:
            account_ids: List of account IDs to execute trade on
            trade_data: Trade data (symbol, side, quantity, etc.)
        
        Returns:
            Dictionary with results for each account
        """
        results = {}
        
        for account_id in account_ids:
            if account_id not in self.accounts:
                results[account_id] = {
                    'success': False,
                    'error': 'Account not found'
                }
                continue
            
            account = self.accounts[account_id]
            if not account.is_active:
                results[account_id] = {
                    'success': False,
                    'error': 'Account is inactive'
                }
                continue
            
            try:
                client = self.get_api_client(account_id)
                
                # Execute trade
                if trade_data.get('order_type') == 'limit' and trade_data.get('price'):
                    # Place limit order - handle different broker signatures
                    try:
                        if account.broker == 'zerodha':
                            # Zerodha limit order signature
                            order = client.place_limit_order(
                                symbol=trade_data['symbol'],
                                side=trade_data['side'],
                                quantity=int(trade_data['quantity']),
                                price=trade_data['price']
                            )
                        else:
                            # Delta/Binance limit order signature
                            order = client.place_limit_order(
                                symbol=trade_data['symbol'],
                                side=trade_data['side'],
                                quantity=trade_data['quantity'],
                                price=trade_data['price']
                            )
                    except Exception as e:
                        logger.error(f"Error placing limit order: {e}")
                        raise
                else:
                    # Place market order
                    order = client.place_market_order(
                        symbol=trade_data['symbol'],
                        side=trade_data['side'],
                        quantity=trade_data['quantity']
                    )
                
                # Update account stats
                account.total_trades += 1
                account.last_used = datetime.now().isoformat()
                
                results[account_id] = {
                    'success': True,
                    'order': order,
                    'account_name': account.account_name
                }
                
                logger.info(f"Trade executed on {account.account_name} ({account_id})")
                
            except Exception as e:
                results[account_id] = {
                    'success': False,
                    'error': str(e),
                    'account_name': account.account_name
                }
                logger.error(f"Error executing trade on {account_id}: {e}")
        
        # Save accounts after updates
        self.save_accounts()
        
        return results
    
    def get_account_status(self, account_id: str) -> Dict:
        """Get account status including balance"""
        if account_id not in self.accounts:
            return {'error': 'Account not found'}
        
        account = self.accounts[account_id]
        balance = self.get_account_balance(account_id)
        
        return {
            'account_id': account_id,
            'account_name': account.account_name,
            'broker': account.broker,
            'balance': balance,
            'is_active': account.is_active,
            'total_trades': account.total_trades,
            'total_pnl': account.total_pnl,
            'last_used': account.last_used
        }


"""
API Client for broker/exchange integration
Supports multiple brokers with a unified interface
"""
import requests
import hmac
import hashlib
import time
from typing import Dict, Optional, List
import logging
from config import Config

logger = logging.getLogger(__name__)


class APIClient:
    """Base API client for trading operations"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, base_url: str = None):
        self.api_key = api_key or Config.API_KEY
        self.api_secret = api_secret or Config.API_SECRET
        self.base_url = base_url or Config.BASE_URL
        self.session = requests.Session()
        # Only add API key header if API key is provided (for public endpoints)
        if self.api_key:
            self.session.headers.update({
                'X-MBX-APIKEY': self.api_key
            })
    
    def _generate_signature(self, params: Dict) -> str:
        """Generate HMAC signature for authenticated requests"""
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get(self, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """Make GET request"""
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def _post(self, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """Make POST request"""
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, data=params)
        response.raise_for_status()
        return response.json()
    
    def _delete(self, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """Make DELETE request"""
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        url = f"{self.base_url}{endpoint}"
        response = self.session.delete(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_account_balance(self) -> Dict:
        """Get account balance"""
        return self._get('/api/v3/account', signed=True)
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        endpoint = f'/api/v3/ticker/price'
        params = {'symbol': symbol}
        response = self._get(endpoint, params=params)
        return float(response['price'])
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        """Get candlestick data"""
        endpoint = '/api/v3/klines'
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        return self._get(endpoint, params=params)
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict:
        """Place a market order"""
        endpoint = '/api/v3/order'
        params = {
            'symbol': symbol,
            'side': side.upper(),  # BUY or SELL
            'type': 'MARKET',
            'quantity': quantity
        }
        return self._post(endpoint, params=params, signed=True)
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict:
        """Place a limit order"""
        endpoint = '/api/v3/order'
        params = {
            'symbol': symbol,
            'side': side.upper(),
            'type': 'LIMIT',
            'timeInForce': 'GTC',
            'quantity': quantity,
            'price': price
        }
        return self._post(endpoint, params=params, signed=True)
    
    def place_stop_loss_order(self, symbol: str, side: str, quantity: float, stop_price: float) -> Dict:
        """Place a stop loss order"""
        endpoint = '/api/v3/order'
        params = {
            'symbol': symbol,
            'side': side.upper(),
            'type': 'STOP_LOSS',
            'timeInForce': 'GTC',
            'quantity': quantity,
            'stopPrice': stop_price
        }
        return self._post(endpoint, params=params, signed=True)
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get open orders"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._get('/api/v3/openOrders', params=params, signed=True)
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """Cancel an order"""
        endpoint = '/api/v3/order'
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._delete(endpoint, params=params, signed=True)
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict:
        """Get order status"""
        endpoint = '/api/v3/order'
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._get(endpoint, params=params, signed=True)


class BinanceClient(APIClient):
    """Binance-specific API client"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        if testnet:
            base_url = 'https://testnet.binance.vision'
        else:
            base_url = 'https://api.binance.com'
        # Allow initialization without API keys for public endpoints (chart viewing)
        super().__init__(api_key, api_secret, base_url)
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        """Get candlestick data (public endpoint - no API keys needed)"""
        endpoint = '/api/v3/klines'
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        # Public endpoint - no authentication needed
        response = self._get(endpoint, params=params, signed=False)
        
        # Convert Binance format to standard format
        candles = []
        for candle in response:
            candles.append({
                'timestamp': candle[0],  # Open time
                'open': float(candle[1]),
                'high': float(candle[2]),
                'low': float(candle[3]),
                'close': float(candle[4]),
                'volume': float(candle[5])
            })
        
        return candles


class CoinbaseClient(APIClient):
    """Coinbase-specific API client (placeholder for future implementation)"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        base_url = 'https://api.coinbase.com'
        super().__init__(api_key, api_secret, base_url)


class ZerodhaKiteClient(APIClient):
    """Zerodha Kite Connect API client for Indian stock market"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, access_token: str = None):
        try:
            from kiteconnect import KiteConnect
        except ImportError:
            raise ImportError("kiteconnect package required. Install with: pip install kiteconnect")
        
        self.api_key = api_key or Config.API_KEY
        self.api_secret = api_secret or Config.API_SECRET
        self.access_token = access_token or Config.API_PASSPHRASE
        
        self.kite = KiteConnect(api_key=self.api_key)
        if self.access_token:
            self.kite.set_access_token(self.access_token)
        
        logger.info("Zerodha Kite Client initialized")
    
    def get_access_token(self, request_token: str) -> str:
        """Generate access token from request token"""
        try:
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data['access_token']
            self.kite.set_access_token(self.access_token)
            logger.info("Access token generated successfully")
            return self.access_token
        except Exception as e:
            logger.error(f"Error generating access token: {e}")
            raise
    
    def get_account_balance(self) -> Dict:
        """Get account balance and margins"""
        try:
            margins = self.kite.margins()
            return margins
        except Exception as e:
            logger.error(f"Error fetching account balance: {e}")
            raise
    
    def get_current_price(self, symbol: str) -> float:
        """Get current LTP (Last Traded Price) for a symbol"""
        try:
            # Format: NSE:INFY or NFO:NIFTY24JANFUT
            ltp = self.kite.ltp([symbol])
            return float(ltp[symbol]['last_price'])
        except Exception as e:
            logger.error(f"Error fetching current price: {e}")
            raise
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        """Get historical candlestick data"""
        try:
            # Map interval to Kite format
            interval_map = {
                '1m': 'minute', '3m': '3minute', '5m': '5minute',
                '15m': '15minute', '30m': '30minute',
                '1h': 'hour', '1d': 'day', '1w': 'week'
            }
            kite_interval = interval_map.get(interval, 'hour')
            
            from datetime import datetime, timedelta
            to_date = datetime.now()
            from_date = to_date - timedelta(days=limit)
            
            historical_data = self.kite.historical_data(
                instrument_token=self._get_instrument_token(symbol),
                from_date=from_date,
                to_date=to_date,
                interval=kite_interval
            )
            
            return historical_data
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            raise
    
    def _get_instrument_token(self, symbol: str) -> int:
        """Get instrument token for symbol (helper method)"""
        # This would need instrument list from Kite
        # For now, return a placeholder
        instruments = self.kite.instruments()
        for instrument in instruments:
            if instrument['tradingsymbol'] == symbol.split(':')[-1]:
                return instrument['instrument_token']
        raise ValueError(f"Instrument not found: {symbol}")
    
    def place_market_order(self, symbol: str, side: str, quantity: int, 
                          product_type: str = 'MIS', exchange: str = 'NSE') -> Dict:
        """Place a market order for Indian stocks/F&O"""
        try:
            # Format symbol: NSE:INFY or NFO:NIFTY24JANFUT
            tradingsymbol = symbol.split(':')[-1] if ':' in symbol else symbol
            
            order = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=exchange,
                tradingsymbol=tradingsymbol,
                transaction_type=self.kite.TRANSACTION_TYPE_BUY if side.upper() == 'BUY' else self.kite.TRANSACTION_TYPE_SELL,
                quantity=int(quantity),
                product=product_type,  # MIS, CNC, NRML
                order_type=self.kite.ORDER_TYPE_MARKET
            )
            logger.info(f"Market order placed: {order}")
            return {'order_id': order}
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            raise
    
    def place_limit_order(self, symbol: str, side: str, quantity: int, price: float,
                         product_type: str = 'MIS', exchange: str = 'NSE') -> Dict:
        """Place a limit order"""
        try:
            tradingsymbol = symbol.split(':')[-1] if ':' in symbol else symbol
            
            order = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=exchange,
                tradingsymbol=tradingsymbol,
                transaction_type=self.kite.TRANSACTION_TYPE_BUY if side.upper() == 'BUY' else self.kite.TRANSACTION_TYPE_SELL,
                quantity=int(quantity),
                product=product_type,
                order_type=self.kite.ORDER_TYPE_LIMIT,
                price=float(price)
            )
            logger.info(f"Limit order placed: {order}")
            return {'order_id': order}
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            raise
    
    def place_stop_loss_order(self, symbol: str, side: str, quantity: int, 
                             trigger_price: float, product_type: str = 'MIS', 
                             exchange: str = 'NSE') -> Dict:
        """Place a stop loss order"""
        try:
            tradingsymbol = symbol.split(':')[-1] if ':' in symbol else symbol
            
            order = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=exchange,
                tradingsymbol=tradingsymbol,
                transaction_type=self.kite.TRANSACTION_TYPE_BUY if side.upper() == 'BUY' else self.kite.TRANSACTION_TYPE_SELL,
                quantity=int(quantity),
                product=product_type,
                order_type=self.kite.ORDER_TYPE_SL,
                trigger_price=float(trigger_price)
            )
            logger.info(f"Stop loss order placed: {order}")
            return {'order_id': order}
        except Exception as e:
            logger.error(f"Error placing stop loss order: {e}")
            raise
    
    def get_open_orders(self) -> List[Dict]:
        """Get open orders"""
        try:
            orders = self.kite.orders()
            return [order for order in orders if order['status'] == 'OPEN']
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            raise
    
    def cancel_order(self, order_id: str, variety: str = 'regular') -> Dict:
        """Cancel an order"""
        try:
            result = self.kite.cancel_order(variety=variety, order_id=order_id)
            logger.info(f"Order cancelled: {order_id}")
            return result
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            raise
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        try:
            positions = self.kite.positions()
            return positions.get('net', [])
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            raise
    
    def get_holdings(self) -> List[Dict]:
        """Get holdings (for CNC products)"""
        try:
            holdings = self.kite.holdings()
            return holdings
        except Exception as e:
            logger.error(f"Error fetching holdings: {e}")
            raise
    
    def get_instruments(self, exchange: str = None) -> List[Dict]:
        """Get instrument list"""
        try:
            if exchange:
                return self.kite.instruments(exchange)
            return self.kite.instruments()
        except Exception as e:
            logger.error(f"Error fetching instruments: {e}")
            raise


class AngelOneClient(APIClient):
    """Angel One SmartAPI client for Indian stock market"""
    
    def __init__(self, api_key: str = None, client_id: str = None, 
                 password: str = None, totp: str = None):
        try:
            from smartapi import SmartConnect
        except ImportError:
            raise ImportError("smartapi-python package required. Install with: pip install smartapi-python")
        
        self.api_key = api_key or Config.API_KEY
        self.client_id = client_id or Config.API_SECRET
        self.password = password
        self.totp = totp
        
        self.smart_api = SmartConnect(api_key=self.api_key)
        
        # Authenticate
        if self.client_id and self.password and self.totp:
            try:
                data = self.smart_api.generateSession(
                    clientId=self.client_id,
                    password=self.password,
                    totp=self.totp
                )
                if data['status']:
                    logger.info("Angel One SmartAPI authenticated successfully")
                else:
                    logger.error(f"Authentication failed: {data['message']}")
            except Exception as e:
                logger.error(f"Error authenticating: {e}")
        
        logger.info("Angel One SmartAPI Client initialized")
    
    def get_account_balance(self) -> Dict:
        """Get account balance and margins"""
        try:
            profile = self.smart_api.getProfile()
            return profile
        except Exception as e:
            logger.error(f"Error fetching account balance: {e}")
            raise
    
    def get_current_price(self, symbol: str, exchange: str = 'NSE') -> float:
        """Get current LTP"""
        try:
            ltp_data = self.smart_api.ltpData(
                exchange=exchange,
                tradingsymbol=symbol,
                symboltoken=self._get_symbol_token(symbol, exchange)
            )
            return float(ltp_data['data']['ltp'])
        except Exception as e:
            logger.error(f"Error fetching current price: {e}")
            raise
    
    def _get_symbol_token(self, symbol: str, exchange: str) -> str:
        """Get symbol token (helper method)"""
        # This would need master contract from Angel One
        # Placeholder implementation
        return "0"
    
    def place_market_order(self, symbol: str, side: str, quantity: int,
                          product_type: str = 'MIS', exchange: str = 'NSE') -> Dict:
        """Place a market order"""
        try:
            order = self.smart_api.placeOrder(
                orderparams={
                    "variety": "NORMAL",
                    "tradingsymbol": symbol,
                    "symboltoken": self._get_symbol_token(symbol, exchange),
                    "transactiontype": "BUY" if side.upper() == "BUY" else "SELL",
                    "exchange": exchange,
                    "ordertype": "MARKET",
                    "producttype": product_type,
                    "duration": "DAY",
                    "quantity": str(quantity)
                }
            )
            logger.info(f"Market order placed: {order}")
            return order
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            raise
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        try:
            positions = self.smart_api.position()
            return positions.get('data', [])
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            raise


class DeltaExchangeClient(APIClient):
    """Delta Exchange API client for crypto derivatives trading"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        self.api_key = api_key or Config.API_KEY
        self.api_secret = api_secret or Config.API_SECRET
        
        if testnet:
            base_url = 'https://testnet-api.delta.exchange'
        else:
            base_url = 'https://api.delta.exchange'
        
        super().__init__(api_key=self.api_key, api_secret=self.api_secret, base_url=base_url)
        self.session.headers = {
            'api-key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Delta Exchange Client initialized (Testnet: {testnet})")
    
    def _generate_signature(self, method: str, timestamp: int, request_path: str, 
                          query_params: str = '', body: str = '') -> str:
        """
        Generate Delta Exchange signature
        Format: method + timestamp + requestPath + query params + body
        """
        message = f"{method}{timestamp}{request_path}{query_params}{body}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get(self, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """Make GET request with Delta Exchange authentication"""
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        timestamp = int(time.time())
        
        if signed:
            # Build query string for signature
            query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
            signature = self._generate_signature('GET', timestamp, endpoint, query_string)
            
            self.session.headers.update({
                'api-key': self.api_key,
                'timestamp': str(timestamp),
                'signature': signature
            })
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def _post(self, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """Make POST request with Delta Exchange authentication"""
        if params is None:
            params = {}
        
        url = f"{self.base_url}{endpoint}"
        timestamp = int(time.time())
        
        if signed:
            # Convert params to JSON string for signature
            import json
            body = '' if not params else json.dumps(params, separators=(',', ':'))
            signature = self._generate_signature('POST', timestamp, endpoint, '', body)
            
            self.session.headers.update({
                'api-key': self.api_key,
                'timestamp': str(timestamp),
                'signature': signature
            })
        
        response = self.session.post(url, json=params)
        response.raise_for_status()
        return response.json()
    
    def get_account_balance(self) -> Dict:
        """Get account balance"""
        try:
            # Try different endpoints
            try:
                return self._get('/v2/portfolio', signed=True)
            except:
                # Fallback to balances endpoint
                return self._get('/v2/portfolio/balances', signed=True)
        except Exception as e:
            logger.error(f"Error fetching account balance: {e}")
            # Return empty dict if balance fetch fails (might need IP whitelisting)
            return {'result': {}, 'error': str(e)}
    
    def get_current_price(self, symbol: str) -> float:
        """Get current LTP (Last Traded Price) for a symbol"""
        try:
            # Get ticker data - try different endpoints
            try:
                response = self._get(f'/v2/tickers/{symbol}')
            except:
                # Fallback: get all tickers and filter
                response = self._get('/v2/tickers')
                tickers = response.get('result', [])
                for ticker in tickers:
                    if ticker.get('symbol') == symbol:
                        return float(ticker.get('close', 0))
                raise ValueError(f"Symbol {symbol} not found")
            
            # Handle different response formats
            if isinstance(response.get('result'), dict):
                return float(response.get('result', {}).get('close', 0))
            elif isinstance(response.get('result'), list) and response.get('result'):
                return float(response.get('result')[0].get('close', 0))
            else:
                return float(response.get('close', 0))
        except Exception as e:
            logger.error(f"Error fetching current price: {e}")
            raise
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        """Get candlestick data"""
        try:
            # Map interval to Delta Exchange format
            interval_map = {
                '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1h', '4h': '4h', '1d': '1d'
            }
            delta_interval = interval_map.get(interval, '1h')
            
            # Get historical data
            params = {
                'symbol': symbol,
                'resolution': delta_interval,
                'limit': limit
            }
            
            response = self._get('/v2/history/candles', params=params)
            
            # Convert to standard format
            candles = []
            for candle in response.get('result', []):
                candles.append({
                    'timestamp': candle.get('time', 0),
                    'open': float(candle.get('open', 0)),
                    'high': float(candle.get('high', 0)),
                    'low': float(candle.get('low', 0)),
                    'close': float(candle.get('close', 0)),
                    'volume': float(candle.get('volume', 0))
                })
            
            return candles
        except Exception as e:
            logger.error(f"Error fetching klines: {e}")
            raise
    
    def place_market_order(self, symbol: str, side: str, quantity: float, 
                          product_id: int = None) -> Dict:
        """Place a market order"""
        try:
            # Get product ID if not provided
            if product_id is None:
                product_id = self._get_product_id(symbol)
            
            order_params = {
                'product_id': product_id,
                'size': abs(quantity),
                'order_type': 'market_order',
                'side': 'buy' if side.upper() == 'BUY' else 'sell'
            }
            
            response = self._post('/v2/orders', params=order_params, signed=True)
            logger.info(f"Market order placed: {response}")
            return response.get('result', {})
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            raise
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float,
                         product_id: int = None) -> Dict:
        """Place a limit order"""
        try:
            if product_id is None:
                product_id = self._get_product_id(symbol)
            
            order_params = {
                'product_id': product_id,
                'size': abs(quantity),
                'limit_price': price,
                'order_type': 'limit_order',
                'side': 'buy' if side.upper() == 'BUY' else 'sell'
            }
            
            response = self._post('/v2/orders', params=order_params, signed=True)
            logger.info(f"Limit order placed: {response}")
            return response.get('result', {})
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            raise
    
    def place_stop_loss_order(self, symbol: str, side: str, quantity: float, 
                             stop_price: float, product_id: int = None) -> Dict:
        """Place a stop loss order"""
        try:
            if product_id is None:
                product_id = self._get_product_id(symbol)
            
            order_params = {
                'product_id': product_id,
                'size': abs(quantity),
                'stop_price': stop_price,
                'order_type': 'stop_order',
                'side': 'buy' if side.upper() == 'BUY' else 'sell'
            }
            
            response = self._post('/v2/orders', params=order_params, signed=True)
            logger.info(f"Stop loss order placed: {response}")
            return response.get('result', {})
        except Exception as e:
            logger.error(f"Error placing stop loss order: {e}")
            raise
    
    def _get_product_id(self, symbol: str) -> int:
        """Get product ID for a symbol"""
        try:
            # Get all products
            response = self._get('/v2/products')
            products = response.get('result', [])
            
            for product in products:
                if product.get('symbol') == symbol:
                    return product.get('id')
            
            raise ValueError(f"Product not found for symbol: {symbol}")
        except Exception as e:
            logger.error(f"Error getting product ID: {e}")
            raise
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get open orders"""
        try:
            params = {}
            if symbol:
                product_id = self._get_product_id(symbol)
                params['product_id'] = product_id
            
            response = self._get('/v2/orders', params=params, signed=True)
            return response.get('result', [])
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            raise
    
    def cancel_order(self, order_id: int) -> Dict:
        """Cancel an order"""
        try:
            response = self._post(f'/v2/orders/{order_id}/cancel', signed=True)
            logger.info(f"Order cancelled: {order_id}")
            return response.get('result', {})
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            raise
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        try:
            response = self._get('/v2/positions', signed=True)
            return response.get('result', [])
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            raise
    
    def get_products(self, contract_type: str = None) -> List[Dict]:
        """Get available products/contracts"""
        try:
            params = {}
            if contract_type:
                params['contract_type'] = contract_type  # perpetual, futures, call, put
            
            response = self._get('/v2/products', params=params)
            return response.get('result', [])
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            raise


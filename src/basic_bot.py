# src/basic_bot.py
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

from logger_setup import setup_logger

logger = setup_logger()

class BasicBot:
    def __init__(self, api_key, api_secret, base_url="https://testnet.binancefuture.com", recv_window=5000):
        self.api_key = api_key
        self.api_secret = api_secret.encode('utf-8')
        self.base_url = base_url.rstrip("/")
        self.recv_window = recv_window
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        })
        logger.info("BasicBot initialized with base_url=%s", self.base_url)

    def _sign(self, params: dict) -> dict:
        params = params.copy()
        params['timestamp'] = int(time.time() * 1000)
        params['recvWindow'] = self.recv_window
        query_string = urlencode(params, doseq=True)
        signature = hmac.new(self.api_secret, query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        params['signature'] = signature
        return params

    def _request(self, method, path, params=None):
        url = f"{self.base_url}{path}"
        params = params or {}
        signed = self._sign(params)
        logger.info("REQUEST %s %s %s", method, url, params)
        try:
            if method.upper() == "GET":
                r = self.session.get(url, params=signed, timeout=15)
            else:
                r = self.session.post(url, params=signed, timeout=15)
            logger.info("RESPONSE %s %s", r.status_code, r.text)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            logger.exception("HTTP error while calling %s: %s", url, e)
            raise

    def place_market_order(self, symbol: str, side: str, quantity: float, reduce_only=False):
        """
        Place a MARKET order on USDT-M futures (POST /fapi/v1/order)
        side: "BUY" or "SELL"
        """
        assert side in ("BUY", "SELL"), "side must be BUY or SELL"
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": float(quantity),
            "reduceOnly": str(reduce_only).lower()
        }
        return self._request("POST", "/fapi/v1/order", params)

    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float, time_in_force="GTC", reduce_only=False):
        """
        Place a LIMIT order on USDT-M futures
        """
        assert side in ("BUY", "SELL"), "side must be BUY or SELL"
        params = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "price": str(price),
            "quantity": float(quantity),
            "timeInForce": time_in_force,
            "reduceOnly": str(reduce_only).lower()
        }
        return self._request("POST", "/fapi/v1/order", params)

    def get_order(self, symbol: str, orderId: int):
        params = {"symbol": symbol, "orderId": orderId}
        return self._request("GET", "/fapi/v1/order", params)

    def get_account_balance(self):
        return self._request("GET", "/fapi/v2/balance", {})

    # Simple wrapper to validate symbol and quantity: (very minimal - real code should query exchange info)
    @staticmethod
    def validate_symbol(sym: str):
        if not sym.isalnum():
            raise ValueError("Symbol must be alphanumeric, e.g. BTCUSDT")
        return sym.upper()

    @staticmethod
    def validate_side(side: str):
        side = side.upper()
        if side not in ("BUY", "SELL"):
            raise ValueError("Side must be BUY or SELL")
        return side

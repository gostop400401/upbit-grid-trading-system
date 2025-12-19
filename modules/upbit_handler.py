import pyupbit
import asyncio
import os
import json
import logging
import websockets
from decimal import Decimal
from typing import Optional, Dict

logger = logging.getLogger("TradingSystem")

class UpbitHandler:
    def __init__(self, access_key: str, secret_key: str):
        self.access = access_key
        self.secret = secret_key
        self.upbit = pyupbit.Upbit(access_key, secret_key)
        self.websocket = None
        self.current_price = None
        self._ws_task = None
        self._running = False
        self.last_update_time = None

    async def get_current_price(self, ticker: str) -> float:
        """
        Get current price via REST API.
        """
        loop = asyncio.get_running_loop()
        price = await loop.run_in_executor(None, pyupbit.get_current_price, ticker)
        return float(price) if price else None

    async def get_completed_orders(self, ticker: str, limit: int = 5) -> list:
        """
        Get recently completed (done) orders.
        """
        try:
            loop = asyncio.get_running_loop()
            # pyupbit doesn't have a direct wrapper for filtering 'done' with limit easily in one func?
            # It has `get_order(ticker, state='done', ...)`
            # Let's use the underlying request or pyupbit's get_order
            # pyupbit.get_order(ticker_or_uuid, state, ...) returns list if ticker provided
            orders = await loop.run_in_executor(None, self.upbit.get_order, ticker, 'done', 1, limit)
            return orders if orders else []
        except Exception as e:
            logger.error(f"Error fetching completed orders: {e}")
            return []

    async def get_open_orders(self, ticker: str) -> list:
        """
        Get all open (wait) orders.
        """
        try:
            loop = asyncio.get_running_loop()
            orders = await loop.run_in_executor(None, self.upbit.get_order, ticker, 'wait')
            return orders if orders else []
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []

    async def get_balance(self, ticker: str) -> Decimal:
        """
        Get balance of specific ticker.
        If ticker is "KRW-USDT", it returns USDT balance.
        If ticker is "KRW", it returns KRW balance.
        """
        currency = ticker.split("-")[1] if "-" in ticker else ticker
        
        # Pyupbit get_balance returns float or 0
        loop = asyncio.get_running_loop()
        # API call is blocking, run in executor
        balance = await loop.run_in_executor(None, self.upbit.get_balance, currency)
        return Decimal(str(balance)) if balance else Decimal("0")

    async def get_total_balance(self, ticker: str) -> Decimal:
        """
        Get TOTAL balance (available + locked) of specific ticker.
        """
        currency = ticker.split("-")[1] if "-" in ticker else ticker
        
        try:
            loop = asyncio.get_running_loop()
            balances = await loop.run_in_executor(None, self.upbit.get_balances)
            
            for b in balances:
                if b.get('currency') == currency:
                    total = Decimal(str(b.get('balance', 0))) + Decimal(str(b.get('locked', 0)))
                    return total
            return Decimal("0")
        except Exception as e:
            logger.error(f"Error fetching total balance for {currency}: {e}")
            return Decimal("0")

    async def buy_limit_order(self, ticker: str, price: float, amount: float) -> Optional[str]:
        """
        Place a buy limit order.
        Returns UUID of the order if successful, None otherwise.
        """
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, 
                self.upbit.buy_limit_order, 
                ticker, price, amount
            )
            
            if result and 'uuid' in result:
                logger.info(f"Buy Order Placed: {ticker} @ {price}, Vol: {amount}, UUID: {result['uuid']}")
                return result['uuid']
            
            logger.error(f"Buy Order Failed: {result}")
            return None
        except Exception as e:
            logger.error(f"Error placing buy order: {e}")
            return None

    async def sell_limit_order(self, ticker: str, price: float, amount: float) -> Optional[str]:
        """
        Place a sell limit order.
        """
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, 
                self.upbit.sell_limit_order, 
                ticker, price, amount
            )
            
            if result and 'uuid' in result:
                logger.info(f"Sell Order Placed: {ticker} @ {price}, Vol: {amount}, UUID: {result['uuid']}")
                return result['uuid']
            
            logger.error(f"Sell Order Failed: {result}")
            return None
        except Exception as e:
            logger.error(f"Error placing sell order: {e}")
            return None

    async def cancel_order(self, uuid: str) -> bool:
        """
        Cancel an order by UUID.
        """
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, self.upbit.cancel_order, uuid)
            if result and 'uuid' in result:
                logger.info(f"Order Cancelled: {uuid}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error canceling order {uuid}: {e}")
            return False

    async def get_order_status(self, uuid: str) -> Optional[Dict]:
        """
        Get order status.
        Returns dict with keys: 'uuid', 'state', 'volume', 'remaining_volume', 'price', etc.
        """
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, self.upbit.get_order, uuid)
            return result
        except Exception as e:
            logger.error(f"Error getting order status {uuid}: {e}")
            return None

    async def connect_websocket(self, ticker: str, callback=None):
        """
        Connect to Upbit WebSocket for real-time price updates.
        ticker: e.g. "KRW-USDT"
        callback: async function(price) to call when price updates
        """
        self._running = True
        uri = "wss://api.upbit.com/websocket/v1"
        
        subscribe_fmt = [
            {"ticket": "UNIQUE_TICKET_ID"},
            {"type": "ticker", "codes": [ticker], "isOnlyRealtime": True}
        ]
        
        while self._running:
            try:
                async with websockets.connect(uri) as websocket:
                    self.websocket = websocket
                    await websocket.send(json.dumps(subscribe_fmt))
                    logger.info(f"Connected to WebSocket for {ticker}")
                    
                    while self._running:
                        try:
                            msg = await websocket.recv()
                            data = json.loads(msg)
                            
                            if 'trade_price' in data:
                                price = float(data['trade_price'])
                                self.current_price = price
                                
                                # Call callback if provided
                                if callback:
                                    await callback(price)
                                    
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("WebSocket connection closed. Reconnecting...")
                            break
                        except Exception as e:
                            logger.error(f"WebSocket Error: {e}")
                            break
            except Exception as e:
                logger.error(f"WebSocket Connection Failed: {e}. Retrying in 5s...")
                await asyncio.sleep(5)

    def stop_websocket(self):
        self._running = False
        if self._ws_task:
            self._ws_task.cancel()


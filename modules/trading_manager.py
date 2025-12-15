import asyncio
import logging
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime

from modules.upbit_handler import UpbitHandler
from models.contract import Contract
from models.trade import Trade
from database.database import set_config, get_config

logger = logging.getLogger("TradingSystem")

class TradingManager:
    def __init__(self, handler: UpbitHandler):
        self.handler = handler
        self.config = {}
        self.is_running = False
        self._monitor_task = None
        self._lock = asyncio.Lock()
        self.bot_start_time = datetime.now().timestamp()
        self.pending_buy_orders = {}  # Changed from set to dict {uuid: price} for tracking order prices
        self.notification_callback = None # Async callback for messages

    def set_notification_callback(self, callback):
        self.notification_callback = callback
    
    async def _send_notification(self, message: str):
        if self.notification_callback:
            try:
                await self.notification_callback(message)
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")

    async def validate_balance(self, ticker: str, grid_count: int, amount_per_grid: float, min_price: float, max_price: float) -> dict:
        """
        Validate if user has enough balance to start the grid.
        Returns dict with 'valid' (bool), 'required', 'balance', 'message'.
        """
        try:
            # Parse currency from ticker (e.g. KRW-USDT -> KRW is quote currency? No.
            # Upbit Ticker: KRW-BTC -> Market: KRW, Item: BTC.
            # We buy BTC with KRW.
            # format: QUOTE-BASE
            quote, base = ticker.split('-') 
            
            # Need Quote Currency (e.g. KRW) to buy Base Currency? 
            # Or if it represents USDT market... 
            # Let's check Upbit standard. KRW-BTC: price is in KRW.
            
            current_price = await self.handler.get_current_price(ticker)
            if not current_price:
                return {'valid': False, 'message': '현재가 조회 실패'}

            # Required Amount
            # We place buy orders at grid lines.
            # Total cost approx = sum of (price * amount) for all buy orders?
            # Actually, grid bot starts by placing BUY orders below current price.
            # And potentially holds asset for Sell orders above current price?
            # Simplified V1: We only place BUY orders initially.
            # So we need Quote Currency (e.g. KRW) for (Grid Count) * Amount * Price?
            # Wait, user inputs "Order Quantity" (amount_per_grid).
            # If ticker is KRW-USDT, amount is in USDT?
            # No, in standard API, volume is the unit of Base currency (USDT).
            # Price is in Quote currency (KRW).
            # Cost = Price * Volume.
            
            # Estimation:
            # Worst case: we buy at Max Price? No, we buy from Min to Max.
            # Max required = Max Price * Amount * Grid Count (Safe upper bound)
            # More accurate = Sum of grid prices * Amount
            
            # Re-calculate grid prices
            interval = (max_price - min_price) / (grid_count - 1) if grid_count > 1 else 0
            # Wait, grid_count calculation in bot was (max-min)/interval + 1.
            # Let's use the estimated grid count passed in.
            
            # Let's just use Average Price * Amount * Count for checking.
            avg_price = (min_price + max_price) / 2
            total_required_quote = avg_price * amount_per_grid * grid_count
            
            # Check Balance
            balance = await self.handler.get_balance(quote)
            
            valid = balance >= Decimal(str(total_required_quote))
            
            msg = f"**[자금 점검]**\n" \
                  f"- 필요 자금(예상): {total_required_quote:,.2f} {quote}\n" \
                  f"- 보유 자금: {balance:,.2f} {quote}\n"
            
            if valid:
                msg += "✅ 자금이 충분합니다."
            else:
                msg += f"❌ 자금이 부족합니다. (부족분: {Decimal(str(total_required_quote)) - balance:,.2f} {quote})"
                
            return {'valid': valid, 'required': total_required_quote, 'balance': balance, 'message': msg}

        except Exception as e:
            logger.error(f"Balance check error: {e}")
            return {'valid': False, 'message': f"자금 확인 중 오류: {e}"}

    async def recover_state(self):
        """
        Recover state on startup.
        Recovers both active contracts (sell orders) and pending buy orders.
        """
        logger.info("Starting State Recovery...")
        
        # 1. Recover Active Contracts (Sell Orders)
        active_contracts = await Contract.get_active_contracts()
        logger.info(f"Found {len(active_contracts)} active contracts from DB.")
        
        for contract in active_contracts:
            uuid = contract.order_uuid
            if not uuid:
                continue
                
            status = await self.handler.get_order_status(uuid)
            if not status or 'error' in status:
                logger.error(f"Order {uuid} for Contract {contract.id} not found.")
                continue
                
            state = status.get('state')
            if state == 'wait':
                logger.info(f"Contract {contract.id} Sell Order {uuid} is active.")
            elif state == 'done':
                logger.info(f"Contract {contract.id} Sell Order {uuid} is FILLED. Closing...")
                await self.process_sell_fill(contract, contract.target_price, contract.buy_amount)
            elif state == 'cancel':
                logger.warning(f"Contract {contract.id} Sell Order {uuid} was CANCELED. Re-placing...")
                new_uuid = await self.handler.sell_limit_order(contract.coin_ticker, contract.target_price, contract.buy_amount)
                if new_uuid:
                    from database.database import execute_write
                    await execute_write("UPDATE contracts SET order_uuid = ? WHERE id = ?", (new_uuid, contract.id))
        
        # 2. Recover Pending Buy Orders (CRITICAL FIX for restart)
        # Check if we have a saved config (meaning trading was active)
        saved_config = await get_config("last_grid_config")
        if saved_config:
            try:
                import ast
                self.config = ast.literal_eval(saved_config)
                ticker = self.config.get('coin_ticker')
                
                if ticker:
                    logger.info(f"Recovering pending buy orders for {ticker}...")
                    
                    # Get all open buy orders from exchange
                    open_orders = await self.handler.get_open_orders(ticker)
                    
                    if open_orders:
                        recovered_count = 0
                        for order in open_orders:
                            if order.get('side') == 'bid':  # Buy order
                                order_uuid = order.get('uuid')
                                order_price = float(order.get('price', 0))
                                
                                # Check if this order is not yet a contract
                                # (If it's already a contract, it will be filled soon)
                                if not await Contract.exists_buy_uuid(order_uuid):
                                    self.pending_buy_orders[order_uuid] = order_price
                                    recovered_count += 1
                                    logger.info(f"Recovered Pending Buy Order: {order_price} KRW (UUID: {order_uuid})")
                        
                        if recovered_count > 0:
                            logger.info(f"✅ Successfully recovered {recovered_count} pending buy order(s).")
                            logger.info(f"📊 Pending prices: {sorted(set(self.pending_buy_orders.values()))}")
                        else:
                            logger.info("No pending buy orders found to recover.")
                    else:
                        logger.info("No open orders found on exchange.")
            except Exception as e:
                logger.error(f"Error recovering pending buy orders: {e}", exc_info=True)

    async def start_trading(self, config: Dict) -> str:
        if self.is_running:
            return "Trading is already running."

        self.config = config
        self.is_running = True
        self.pending_buy_orders.clear() # Clear old tracking
        
        logger.info(f"Starting trading with config: {config}")
        await set_config("last_grid_config", str(config))

        await self._place_initial_orders()
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        return "Trading System Started."

    async def stop_trading(self):
        self.is_running = False
        if self._monitor_task:
            self._monitor_task.cancel()
        logger.info("Trading System Stopped.")

    async def _place_initial_orders(self):
        ticker = self.config['coin_ticker']
        min_price = self.config['min_price']
        max_price = self.config['max_price']
        interval = self.config['grid_interval']
        amount = self.config['amount_per_grid']

        current_price = self.handler.current_price
        if not current_price:
            current_price = await self.handler.get_current_price(ticker)
        
        if not current_price:
            logger.error("Could not get current price for initial setup.")
            return

        logger.info(f"Setting up grid. Current Price: {current_price}")

        active_contracts = await Contract.get_active_contracts()
        existing_grid_prices = {float(c.buy_price) for c in active_contracts}
        
        current_grid = min_price
        epsilon = 1e-4
        
        while current_grid <= max_price:
            is_exist = False
            for exist_p in existing_grid_prices:
                if abs(exist_p - current_grid) < epsilon:
                    is_exist = True
                    break
            
            if not is_exist and current_grid <= current_price:
                uuid = await self.handler.buy_limit_order(ticker, current_grid, amount)
                if uuid:
                    self.pending_buy_orders[uuid] = current_grid  # Store UUID with price
                    logger.info(f"Placed Initial Buy: {current_grid} (UUID: {uuid})")
            elif is_exist:
                logger.info(f"Skipping Grid {current_grid}: Active Contract Exists.")
                
            current_grid += interval

    async def _monitor_loop(self):
        while self.is_running:
            try:
                # 1. Sync Active Contracts (Sell Fills)
                active_contracts = await Contract.get_active_contracts()
                for contract in active_contracts:
                    await self._check_sell_fill(contract)
                
                # 2. Check for New Buy Fills from 'done' orders
                ticker = self.config.get('coin_ticker')
                if ticker:
                    done_orders = await self.handler.get_completed_orders(ticker, limit=10)
                    for order in done_orders:
                        # Ensure it's a BUY order
                        if order.get('side') != 'bid':
                            continue
                            
                        uuid = order.get('uuid')
                        
                        # Only process if it is in our pending list
                        if uuid not in self.pending_buy_orders:
                            continue
                            
                        # Double check if already processed (just in case)
                        if await Contract.exists_buy_uuid(uuid):
                            self.pending_buy_orders.pop(uuid, None)  # Remove from dict
                            continue

                        # It's a new fill from our order!
                        price = float(order.get('price', 0)) 
                        volume = float(order.get('volume', 0)) 
                        executed_vol = float(order.get('executed_volume', volume))
                        
                        logger.info(f"Detected Buy Fill: {uuid} @ {price}, Vol: {executed_vol}")
                        await self.process_buy_fill(uuid, price, executed_vol)
                        
                        # Remove from pending list
                        self.pending_buy_orders.pop(uuid, None)  # Remove from dict
                
                # 3. Fill Empty Grids (Dynamic Order Placement)
                await self._fill_empty_grids()

                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def process_buy_fill(self, order_uuid: str, price: float, volume: float):
        async with self._lock:
            # Check idempotency again
            if await Contract.exists_buy_uuid(order_uuid):
                logger.warning(f"Contract for buy order {order_uuid} already exists. Skipping.")
                return

            ticker = self.config['coin_ticker']
            profit_target = self.config.get('profit_interval', 3.0)
            target_price = price + profit_target
            
            # Create Contract
            contract = Contract(
                coin_ticker=ticker,
                buy_price=price,
                buy_amount=volume,
                target_price=target_price,
                status="ACTIVE",
                order_uuid=order_uuid, # Temp, updated below
                buy_order_uuid=order_uuid 
            )
            created_contract = await Contract.create(contract)
            logger.info(f"Created Contract {created_contract.id} for Order {order_uuid}")
            
            await self._send_notification(f"🔔 **매수 체결 알림**\n"
                                          f"- 티커: {ticker}\n"
                                          f"- 가격: {price}\n"
                                          f"- 수량: {volume}\n"
                                          f"- 계약 ID: {created_contract.id}")

            # Place Sell Order
            sell_uuid = await self.handler.sell_limit_order(ticker, target_price, volume)
            
            if sell_uuid:
                from database.database import execute_write
                await execute_write("UPDATE contracts SET order_uuid = ? WHERE id = ?", (sell_uuid, created_contract.id))
                logger.info(f"Updated Contract {created_contract.id} with Sell UUID {sell_uuid}")
            else:
                logger.error(f"Failed to place sell order for Contract {created_contract.id}")

            # Record Trade
            await Trade.create(Trade(
                contract_id=created_contract.id,
                type="BUY",
                price=price,
                amount=volume,
                fee=0.0, 
                profit=0.0
            ))

    async def _check_sell_fill(self, contract: Contract):
        # Check status of the sell order
        if not contract.order_uuid:
            return

        status = await self.handler.get_order_status(contract.order_uuid)
        if status and status.get('state') == 'done':
            # Filled!
            price = float(status.get('price', contract.target_price)) # Use target if price missing
            # accurate price should be calculated from trades if possible
            # But let's use the sell price for PnL
            
            await self.process_sell_fill(contract, price, contract.buy_amount)

    async def process_sell_fill(self, contract: Contract, price: float, volume: float):
        async with self._lock:
            logger.info(f"Processing Sell Fill for Contract {contract.id}")
            
            # 1. Close Contract
            profit = (price - contract.buy_price) * volume
            profit_rate = (price - contract.buy_price) / contract.buy_price
            
            await Contract.close_contract(contract.id, price, profit, profit_rate)
            logger.info(f"Closed Contract {contract.id}. Profit: {profit}")
            
            await self._send_notification(f"💰 **익절 알림 (매도 체결)**\n"
                                          f"- 티커: {contract.coin_ticker}\n"
                                          f"- 매도가: {price}\n"
                                          f"- 수익: {profit:.2f} ({(profit_rate*100):.2f}%)\n"
                                          f"- 계약 ID: {contract.id}")

            # 2. Record Trade
            await Trade.create(Trade(
                contract_id=contract.id,
                type="SELL",
                price=price,
                amount=volume,
                fee=0.0, 
                profit=profit
            ))
            
            # 3. Re-entry (Place Buy Order again at buy_price)
            ticker = contract.coin_ticker
            re_buy_price = contract.buy_price
            re_buy_amount = contract.buy_amount 
            
            new_buy_uuid = await self.handler.buy_limit_order(ticker, re_buy_price, re_buy_amount)
            if new_buy_uuid:
                self.pending_buy_orders[new_buy_uuid] = re_buy_price  # Track with price
                logger.info(f"Re-entry Buy Order Placed: {re_buy_price}, UUID: {new_buy_uuid}")
            else:
                logger.error("Failed to place Re-entry Buy Order")

    async def _fill_empty_grids(self):
        """
        Check for empty grid levels below current price where no order/contract exists,
        and place buy orders there.
        """
        try:
            ticker = self.config.get('coin_ticker')
            if not ticker: return
            
            min_price = self.config['min_price']
            max_price = self.config['max_price']
            interval = self.config['grid_interval']
            amount = self.config['amount_per_grid']
            
            # 1. Get Current Market Price
            current_price = await self.handler.get_current_price(ticker)
            if not current_price: return

            # 2. Get All Active States
            # Active Contracts (already bought)
            active_contracts = await Contract.get_active_contracts()
            active_buy_prices = {float(c.buy_price) for c in active_contracts}
            
            # Pending Buy Orders (locally tracked)
            # CRITICAL FIX: Use local pending_buy_orders dict which now stores {uuid: price}
            # This prevents duplicate orders when API responses are delayed
            pending_buy_prices = set(self.pending_buy_orders.values())
            
            # Also check exchange open orders as backup validation
            # This helps catch any orders that might have been placed outside this session
            open_orders = await self.handler.get_open_orders(ticker)
            open_buy_prices = set()
            if open_orders:
                for o in open_orders:
                    if o.get('side') == 'bid':
                         open_buy_prices.add(float(o.get('price')))
            
            # 3. Scan Grids
            current_grid = min_price
            epsilon = 1e-4
            
            while current_grid <= max_price:
                # Target must be <= Current Price (Don't buy above market)
                if current_grid <= current_price:
                    
                    # Check if occupied by Active Contract
                    is_contract_active = False
                    for price in active_buy_prices:
                        if abs(price - current_grid) < epsilon:
                            is_contract_active = True
                            break
                    
                    # Check if occupied by Pending Buy Order (LOCAL TRACKING)
                    is_pending = False
                    for price in pending_buy_prices:
                        if abs(price - current_grid) < epsilon:
                            is_pending = True
                            break
                    
                    # Check if occupied by Open Buy Order (EXCHANGE VERIFICATION)
                    is_order_open = False
                    for price in open_buy_prices:
                        if abs(price - current_grid) < epsilon:
                            is_order_open = True
                            break
                    
                    # If EMPTY (no contract, no pending, no open order), place buy order
                    if not is_contract_active and not is_pending and not is_order_open:
                        logger.info(f"Found Empty Grid at {current_grid} (Curr: {current_price}). Placing Buy Order...")
                        uuid = await self.handler.buy_limit_order(ticker, current_grid, amount)
                        if uuid:
                            self.pending_buy_orders[uuid] = current_grid  # Store with price
                
                current_grid += interval

        except Exception as e:
            logger.error(f"Error in _fill_empty_grids: {e}")

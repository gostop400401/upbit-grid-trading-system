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
        
        active_sell_count = 0
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
                active_sell_count += 1
            elif state == 'done':
                logger.info(f"Contract {contract.id} Sell Order {uuid} is FILLED. Closing...")
                await self.process_sell_fill(contract, contract.target_price, contract.buy_amount)
            elif state == 'cancel':
                logger.warning(f"Contract {contract.id} Sell Order {uuid} was CANCELED. Re-placing...")
                new_uuid = await self.handler.sell_limit_order(contract.coin_ticker, contract.target_price, contract.buy_amount)
                if new_uuid:
                    from database.database import execute_write
                    await execute_write("UPDATE contracts SET order_uuid = ? WHERE id = ?", (new_uuid, contract.id))
        
        # Summary for active sell orders
        if active_sell_count > 0:
            sell_prices = sorted(set(float(c.target_price) for c in active_contracts if c.order_uuid))
            logger.info(f"✅ Successfully recovered {active_sell_count} active sell order(s).")
            logger.info(f"📊 Sell prices: {sell_prices}")
        else:
            logger.info("No active sell orders to recover.")
        
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
                    
                    recovered_count = 0
                    if open_orders:
                        for order in open_orders:
                            if order.get('side') == 'bid':  # Buy order
                                order_uuid = order.get('uuid')
                                order_price = float(order.get('price', 0))
                                
                                # Check if this order is not yet a contract
                                if not await Contract.exists_buy_uuid(order_uuid):
                                    self.pending_buy_orders[order_uuid] = order_price
                                    recovered_count += 1
                                    logger.info(f"Recovered Pending Buy Order: {order_price} (UUID: {order_uuid})")
                    
                    # NEW: Also check recently completed orders just in case some filled while bot was starting
                    done_orders = await self.handler.get_completed_orders(ticker, limit=20)
                    if isinstance(done_orders, list):
                        for order in done_orders:
                            if order.get('side') == 'bid' and order.get('state') == 'done':
                                uuid = order.get('uuid')
                                if not await Contract.exists_buy_uuid(uuid):
                                    # This order was filled but we have no contract!
                                    # We can't put it in pending_buy_orders (it's done), 
                                    # so we should process it as a fill immediately if it's within our expected grids
                                    # For safety, we'll let the self-healing sync catch this.
                                    pass

                    if recovered_count > 0:
                        logger.info(f"✅ Successfully recovered {recovered_count} pending buy order(s).")
                    else:
                        logger.info("No pending buy orders found to recover.")
            except Exception as e:
                logger.error(f"Error recovering pending buy orders: {e}", exc_info=True)

    async def start_trading(self, config: Dict) -> str:
        # 🔒 CRITICAL: Lock으로 동시 start_trading 호출 방지
        async with self._lock:
            if self.is_running:
                return "Trading is already running."

            # 기존 태스크가 있다면 명시적으로 취소
            if self._monitor_task and not self._monitor_task.done():
                logger.warning("Cancelling existing monitor task...")
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    logger.info("Previous monitor task cancelled successfully.")

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

        # Get both active contracts and currently open orders on exchange
        active_contracts = await Contract.get_active_contracts()
        existing_grid_prices = {float(c.buy_price) for c in active_contracts}
        
        open_orders = await self.handler.get_open_orders(ticker)
        open_buy_prices = set()
        if open_orders:
            for o in open_orders:
                if o.get('side') == 'bid':
                    open_buy_prices.add(float(o.get('price')))
        
        current_grid = min_price
        epsilon = 1e-4
        
        while current_grid <= max_price:
            is_exist = False
            # Check DB
            for exist_p in existing_grid_prices:
                if abs(exist_p - current_grid) < epsilon:
                    is_exist = True
                    break
            
            # Check Exchange Open Orders
            if not is_exist:
                for open_p in open_buy_prices:
                    if abs(open_p - current_grid) < epsilon:
                        is_exist = True
                        # Also add to our local tracking if missing
                        # This handles cases where orders existed but weren't in memory
                        break

            if not is_exist and current_grid <= current_price:
                uuid = await self.handler.buy_limit_order(ticker, current_grid, amount)
                if uuid:
                    self.pending_buy_orders[uuid] = current_grid
                    logger.info(f"Placed Initial Buy: {current_grid} (UUID: {uuid})")
            elif is_exist:
                logger.info(f"Skipping Grid {current_grid}: Already occupied (Contract or Open Order).")
                
            current_grid += interval

    async def _monitor_loop(self):
        # NEW: Self-healing sync counter
        sync_counter = 0

        while self.is_running:
            try:
                # 1. Sync Active Contracts (Sell Fills)
                active_contracts = await Contract.get_active_contracts()
                for contract in active_contracts:
                    await self._check_sell_fill(contract)
                
                # 2. Check for New Buy Fills (Robust Polling)
                ticker = self.config.get('coin_ticker')
                if ticker:
                    # Method A: Specific status check for ALL pending orders (Most Reliable)
                    pending_uuids = list(self.pending_buy_orders.keys())
                    for uuid in pending_uuids:
                        status = await self.handler.get_order_status(uuid)
                        if status and status.get('state') == 'done':
                            price = float(status.get('price', 0))
                            volume = float(status.get('volume', 0))
                            executed_vol = float(status.get('executed_volume', volume))
                            
                            logger.info(f"✅ [Robust Check] Detected Buy Fill: {uuid} @ {price}")
                            await self.process_buy_fill(uuid, price, executed_vol)
                            self.pending_buy_orders.pop(uuid, None)
                    
                    # Method B: Fast Polling of recent done orders (Good for high frequency)
                    done_orders = await self.handler.get_completed_orders(ticker, limit=20)
                    if isinstance(done_orders, list):
                        for order in done_orders:
                            if order.get('side') != 'bid': continue
                            uuid = order.get('uuid')
                            
                            if uuid in self.pending_buy_orders:
                                # Found one through fast polling
                                price = float(order.get('price', 0)) 
                                volume = float(order.get('volume', 0)) 
                                executed_vol = float(order.get('executed_volume', volume))
                                
                                logger.info(f"Detected Buy Fill (Fast Poll): {uuid} @ {price}")
                                await self.process_buy_fill(uuid, price, executed_vol)
                                self.pending_buy_orders.pop(uuid, None)
                
                # 3. Fill Empty Grids
                await self._fill_empty_grids()

                # 4. Periodic Self-Healing Sync (Every 1 minute approx)
                sync_counter += 1
                if sync_counter >= 30: # 2s * 30 = 60s
                    await self._sync_with_exchange_balance()
                    sync_counter = 0

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

    async def _place_order_atomic(self, ticker: str, price: float, amount: float) -> Optional[str]:
        """
        🔒 원자적(Atomic) 주문 실행 함수
        
        "야, 나 이 가격에 주문 낼거다~" → "괜찮아/안돼"
        
        이 함수는 반드시 락(lock) 안에서만 호출되어야 합니다.
        주문 직전에 마지막으로 중복을 확인합니다.
        """
        epsilon = 1e-4
        
        # 마지막 순간 재확인: "이미 주문 있어?"
        # 1. 로컬 pending 확인
        for existing_price in self.pending_buy_orders.values():
            if abs(existing_price - price) < epsilon:
                logger.warning(f"🚫 Order rejected: Already have pending order at {price}")
                return None
        
        # 2. DB에서 active contracts 확인
        active_contracts = await Contract.get_active_contracts()
        for contract in active_contracts:
            if abs(float(contract.buy_price) - price) < epsilon:
                logger.warning(f"🚫 Order rejected: Active contract exists at {price}")
                return None
        
        # 3. 거래소에 실제 주문 확인 (최종 방어선)
        open_orders = await self.handler.get_open_orders(ticker)
        if open_orders:
            for order in open_orders:
                if order.get('side') == 'bid' and abs(float(order.get('price', 0)) - price) < epsilon:
                    logger.warning(f"🚫 Order rejected: Open order exists at {price}")
                    return None
        
        # ✅ 모든 체크 통과! "괜찮아~ 주문 넣어!"
        logger.info(f"✅ All checks passed. Placing order at {price}")
        uuid = await self.handler.buy_limit_order(ticker, price, amount)
        
        if uuid:
            self.pending_buy_orders[uuid] = price
            logger.info(f"📝 Order registered: UUID={uuid}, Price={price}")
        
        return uuid

    async def _fill_empty_grids(self):
        """
        Check for empty grid levels below current price where no order/contract exists,
        and place buy orders there.
        
        🔒 전체 함수가 락(lock)으로 보호됩니다 - Race Condition 방지
        """
        # 🔒 CRITICAL: 전체 함수를 락으로 보호 (문지기 패턴)
        async with self._lock:
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
                pending_buy_prices = set(self.pending_buy_orders.values())
                
                # Also check exchange open orders as backup validation
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
                            logger.info(f"Found Empty Grid at {current_grid} (Curr: {current_price}). Requesting order...")
                            # 🔒 원자적 주문 실행 (이미 락 안에 있음)
                            uuid = await self._place_order_atomic(ticker, current_grid, amount)
                            if uuid:
                                logger.info(f"✅ Order placed successfully at {current_grid}")
                            else:
                                logger.warning(f"⚠️ Order rejected at {current_grid} (duplicate detected)")
                    
                    current_grid += interval

            except Exception as e:
                logger.error(f"Error in _fill_empty_grids: {e}")

    async def _sync_with_exchange_balance(self):
        """
        Self-Healing Mechanism:
        Compares actual exchange balance with DB contracts.
        Rescues orphaned funds if mismatch discovered.
        """
        try:
            ticker = self.config.get('coin_ticker')
            if not ticker: return
            quote, base = ticker.split('-')
            
            # 1. Get Actual Balance from Exchange (TOTAL: available + locked)
            actual_base_bal = await self.handler.get_total_balance(base)
            
            # 2. Get Sum of base currency held in DB contracts
            active_contracts = await Contract.get_active_contracts()
            db_base_sum = sum(Decimal(str(c.buy_amount)) for c in active_contracts)
            
            # 3. Calculate Gap
            gap = actual_base_bal - db_base_sum
            grid_amount = Decimal(str(self.config.get('amount_per_grid', 0)))
            
            logger.info(f"⚖️ [Self-Healing Check] Ticker: {ticker}, Total: {actual_base_bal}, DB: {db_base_sum}, Gap: {gap}, GridSize: {grid_amount}")

            if gap >= grid_amount * Decimal("0.9"):
                logger.warning(f"⚖️ [Self-Healing] Balance Mismatch Found! Gap: {gap}")
                
                # Try to identify which buy order was filled but not recorded
                # We do this by looking at completed orders that are NOT in DB
                done_orders = await self.handler.get_completed_orders(ticker, limit=50)
                if isinstance(done_orders, list):
                    rescued_count = 0
                    for order in done_orders:
                        if rescued_count >= int(gap / grid_amount): break
                        
                        if order.get('side') == 'bid' and order.get('state') == 'done':
                            uuid = order.get('uuid')
                            if not await Contract.exists_buy_uuid(uuid):
                                # FOUND AN ORPHAN!
                                price = float(order.get('price', 0))
                                volume = float(order.get('volume', 0))
                                executed_vol = float(order.get('executed_volume', volume))
                                
                                logger.info(f"🚑 [Self-Healing] Rescuing orphaned fill: {uuid} @ {price}")
                                await self.process_buy_fill(uuid, price, executed_vol)
                                rescued_count += 1
                                
                    if rescued_count > 0:
                        await self._send_notification(f"🚑 **자기 치유(Self-Healing) 작동**\n"
                                                      f"데이터베이스에 누락되었던 {rescued_count}개의 계약을 거래소 이력에서 찾아 복구했습니다.")
        except Exception as e:
            logger.error(f"Error in _sync_with_exchange_balance: {e}")

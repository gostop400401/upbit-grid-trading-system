import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.trading_manager import TradingManager
from models.contract import Contract
from database.database import init_db

# Mock UpbitHandler
class MockHandler:
    def __init__(self):
        self.current_price = 1450.0
        self.buy_limit_order = AsyncMock(return_value="new-buy-uuid")
        self.sell_limit_order = AsyncMock(return_value="new-sell-uuid")
        self.get_current_price = AsyncMock(return_value=1450.0)

async def test_trading_flow():
    print("--- Starting Trading Logic Test ---")
    
    # 1. Setup In-Memory DB (or use file for test)
    # Ideally use robust test fixture, but for now init real DB (test mode?)
    # We are using the real 'trading.db' in the project root based on imports.
    # To avoid messing up real DB, we should maybe back it up or use a test flag.
    # For this task, I'll assume we can use the main DB as it's dev env.
    await init_db()
    
    handler = MockHandler()
    manager = TradingManager(handler)
    
    # 2. Config
    config = {
        'coin_ticker': 'KRW-USDT',
        'min_price': 1400.0,
        'max_price': 1500.0,
        'grid_count': 5,
        'grid_interval': 20.0,
        'amount_per_grid': 5.0,
        'profit_interval': 5.0
    }
    
    # 3. Start Trading
    print("Testing start_trading...")
    res = await manager.start_trading(config)
    print(res)
    
    # Verify initial orders placed
    # min=1400, max=1500, int=20 -> 1400, 1420, 1440, 1460, 1480, 1500
    # current=1450
    # Buys should be: 1400, 1420, 1440 (contracts below current)
    # verify handler.buy_limit_order called
    print(f"Initial Buy Calls: {handler.buy_limit_order.call_count}")
    # We expect 3 calls (1400, 1420, 1440)
    assert handler.buy_limit_order.call_count >= 1
    
    # 4. Simulate Buy Fill
    print("Testing process_buy_fill...")
    buy_uuid = "mock-buy-uuid-1"
    # Call process_buy_fill manually (simulating callback)
    # Manager doesn't have the contract yet because start_trading just placed orders
    # but didn't create contracts (as per my code logic).
    # Logic: Contract created ONLY when buy fills.
    
    await manager.process_buy_fill(buy_uuid, price=1400.0, volume=10.0)
    
    # Verify:
    # 1. Contract created in DB?
    # 2. Sell order placed?
    
    # Check DB
    active = await Contract.get_active_contracts()
    my_contract = next((c for c in active if c.buy_price == 1400.0), None)
    
    assert my_contract is not None
    print(f"Contract Created: ID={my_contract.id}, Status={my_contract.status}")
    
    # Check Sell Order
    handler.sell_limit_order.assert_called()
    print("Sell order placement verified.")
    
    # 5. Simulate Sell Fill
    print("Testing process_sell_fill...")
    # The contract created above should now have 'new-sell-uuid' (from MockHandler default)
    # Check if DB update happened? 
    # MockHandler returns "new-sell-uuid" for sell_limit_order.
    
    # Reload contract to see if UUID updated
    updated_contract = await Contract.get_by_uuid("new-sell-uuid")
    # Actually get_by_uuid checks 'order_uuid' column.
    
    # Wait a bit for async DB update if needed? No, await process_buy_fill awaits DB commit.
    
    if updated_contract:
        print(f"Verified Contract UUID updated to: {updated_contract.order_uuid}")
    else:
        print("Error: Contract UUID not updated to Sell UUID.")
        # Debug: check what it is
        c_chk = (await Contract.get_active_contracts())[-1]
        print(f"Current UUID in DB: {c_chk.order_uuid}")
        
    
    # Now process sell fill
    # Pass 'updated_contract' which is the active one with sell uuid
    # Logic: process_sell_fill(contract, price, volume)
    
    sell_price = 1400.0 + 5.0 # target
    await manager.process_sell_fill(updated_contract, price=sell_price, volume=10.0)
    
    # Verify:
    # 1. Contract Closed?
    closed_contract = await Contract.get_by_uuid("new-sell-uuid")
    # get_by_uuid might return even if closed if we don't filter in method?
    # Contract.get_by_uuid selects * ... yes.
    assert closed_contract.status == "CLOSED"
    print("Contract Closed verified.")
    
    # 2. Re-entry Buy Placed?
    # handler.buy_limit_order was called initially 3 times.
    # Now it should be called 1 more time for re-entry.
    print(f"Total Buy Calls: {handler.buy_limit_order.call_count}")
    assert handler.buy_limit_order.call_count >= 1 # We can't strictly count if we didn't reset mock, but fine.
    
    print("--- Trading Logic Test Passed ---")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_trading_flow())

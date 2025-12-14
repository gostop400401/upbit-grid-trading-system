import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.database import init_db
from models.contract import Contract
from models.trade import Trade

async def test_db_operations():
    print("--- Starting DB Test ---")
    
    # 1. Init DB
    await init_db()
    
    # 2. Create Contract
    print("Creating contract...")
    c = Contract(
        coin_ticker="KRW-USDT",
        buy_price=1400.0,
        buy_amount=10.0,
        target_price=1410.0,
        status="ACTIVE",
        order_uuid="uuid-1234"
    )
    created_c = await Contract.create(c)
    print(f"Contract created: ID={created_c.id}")
    
    # 3. Get Active Contracts
    active_contracts = await Contract.get_active_contracts()
    print(f"Active contracts count: {len(active_contracts)}")
    assert len(active_contracts) > 0
    assert active_contracts[-1].order_uuid == "uuid-1234"
    
    # 4. Create Trade (Buy)
    print("Creating trade...")
    t = Trade(
        contract_id=created_c.id,
        type="BUY",
        price=1400.0,
        amount=10.0,
        fee=0.05,
        profit=0.0
    )
    created_t = await Trade.create(t)
    print(f"Trade created: ID={created_t.id}")
    
    # 5. Close Contract
    print("Closing contract...")
    await Contract.close_contract(created_c.id, sell_price=1410.0, profit=100.0, profit_rate=0.7)
    
    # 6. Verify Close
    print("Verifying close...")
    active_now = await Contract.get_active_contracts()
    # Should not be in active list assuming we filtered by ACTIVE
    # (Actually my get_active_contracts logic selects * from contracts where status='ACTIVE')
    # So it should disappear from that list
    is_still_active = any(c.id == created_c.id for c in active_now)
    print(f"Is contract still active? {is_still_active}")
    assert not is_still_active
    
    print("--- DB Test Passed ---")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_db_operations())

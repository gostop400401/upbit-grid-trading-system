from dataclasses import dataclass
from typing import Optional, List
from database.database import execute_write, execute_read

@dataclass
class Contract:
    coin_ticker: str
    buy_price: float
    buy_amount: float
    target_price: float
    status: str # ACTIVE, CLOSED
    order_uuid: str # Current Active Order UUID (Sell UUID if Active)
    buy_order_uuid: str # Original Buy Order UUID
    id: Optional[int] = None
    created_at: Optional[str] = None
    sell_price: Optional[float] = None
    profit: Optional[float] = None
    profit_rate: Optional[float] = None
    finished_at: Optional[str] = None

    @classmethod
    async def create(cls, contract: 'Contract'):
        last_id = await execute_write("""
            INSERT INTO contracts (
                coin_ticker, buy_price, buy_amount, target_price, status, order_uuid, buy_order_uuid, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            contract.coin_ticker, 
            contract.buy_price, 
            contract.buy_amount, 
            contract.target_price, 
            contract.status, 
            contract.order_uuid,
            contract.buy_order_uuid
        ))
        contract.id = last_id
        return contract

    @classmethod
    async def get_active_contracts(cls) -> List['Contract']:
        rows = await execute_read("SELECT * FROM contracts WHERE status = 'ACTIVE'", fetch_all=True)
        contracts = []
        for row in rows:
            contracts.append(cls(
                id=row['id'],
                coin_ticker=row['coin_ticker'],
                buy_price=row['buy_price'],
                buy_amount=row['buy_amount'],
                target_price=row['target_price'],
                status=row['status'],
                order_uuid=row['order_uuid'],
                buy_order_uuid=row['buy_order_uuid'], # Load from DB
                created_at=row['created_at'],
                sell_price=row['sell_price'],
                profit=row['profit'],
                profit_rate=row['profit_rate'],
                finished_at=row['finished_at']
            ))
        return contracts

    @classmethod
    async def exists_buy_uuid(cls, uuid: str) -> bool:
        """Check if a contract with this buy_order_uuid already exists."""
        row = await execute_read("SELECT 1 FROM contracts WHERE buy_order_uuid = ?", (uuid,))
        return bool(row)
            
    @classmethod
    async def get_by_uuid(cls, uuid: str) -> Optional['Contract']:
        row = await execute_read("SELECT * FROM contracts WHERE order_uuid = ?", (uuid,))
        if row:
            return cls(
                id=row['id'],
                coin_ticker=row['coin_ticker'],
                buy_price=row['buy_price'],
                buy_amount=row['buy_amount'],
                target_price=row['target_price'],
                status=row['status'],
                order_uuid=row['order_uuid'],
                created_at=row['created_at'],
                sell_price=row['sell_price'],
                profit=row['profit'],
                profit_rate=row['profit_rate'],
                finished_at=row['finished_at']
            )
        return None

    @classmethod
    async def close_contract(cls, contract_id: int, sell_price: float, profit: float, profit_rate: float):
        await execute_write("""
            UPDATE contracts 
            SET status = 'CLOSED', 
                sell_price = ?, 
                profit = ?, 
                profit_rate = ?, 
                finished_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (sell_price, profit, profit_rate, contract_id))

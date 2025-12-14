from dataclasses import dataclass
from typing import Optional, List
from database.database import execute_write, execute_read

@dataclass
class Trade:
    contract_id: int
    type: str # BUY, SELL
    price: float
    amount: float
    fee: float
    profit: float # 0 for BUY
    id: Optional[int] = None
    executed_at: Optional[str] = None

    @classmethod
    async def create(cls, trade: 'Trade'):
        last_id = await execute_write("""
            INSERT INTO trades (
                contract_id, type, price, amount, fee, profit, executed_at
            ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            trade.contract_id,
            trade.type,
            trade.price,
            trade.amount,
            trade.fee,
            trade.profit
        ))
        trade.id = last_id
        return trade

    @classmethod
    async def get_by_contract_id(cls, contract_id: int) -> List['Trade']:
        rows = await execute_read("SELECT * FROM trades WHERE contract_id = ?", (contract_id,), fetch_all=True)
        trades = []
        for row in rows:
            trades.append(cls(
                id=row['id'],
                contract_id=row['contract_id'],
                type=row['type'],
                price=row['price'],
                amount=row['amount'],
                fee=row['fee'],
                profit=row['profit'],
                executed_at=row['executed_at']
            ))
        return trades

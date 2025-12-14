import sqlite3
import asyncio
import logging

logger = logging.getLogger("TradingSystem")
DB_FILE = "trading.db"

def get_connection():
    """Returns a synchronous sqlite3 connection."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

async def execute_write(sql: str, params: tuple = ()) -> int:
    """Execute INSERT/UPDATE/DELETE. Returns lastrowid."""
    loop = asyncio.get_running_loop()
    def _task():
        conn = get_connection()
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"DB Write Error: {e}\nSQL: {sql}\nParams: {params}")
            raise
        finally:
            conn.close()
    return await loop.run_in_executor(None, _task)

async def execute_read(sql: str, params: tuple = (), fetch_all: bool = False):
    """Execute SELECT. Returns dict or list of dicts."""
    loop = asyncio.get_running_loop()
    def _task():
        conn = get_connection()
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            cursor = conn.execute(sql, params)
            if fetch_all:
                return [dict(row) for row in cursor.fetchall()]
            else:
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"DB Read Error: {e}\nSQL: {sql}\nParams: {params}")
            raise
        finally:
            conn.close()
    return await loop.run_in_executor(None, _task)

async def init_db():
    """Initializes the database."""
    loop = asyncio.get_running_loop()
    def _init():
        conn = get_connection()
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            
            # Contracts Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contracts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    coin_ticker TEXT NOT NULL,
                    buy_price REAL NOT NULL,
                    buy_amount REAL NOT NULL,
                    target_price REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    order_uuid TEXT,
                    buy_order_uuid TEXT, -- New Column
                    sell_price REAL,
                    profit REAL,
                    profit_rate REAL,
                    finished_at DATETIME
                )
            """)
            
            # Trades Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_id INTEGER,
                    type TEXT NOT NULL,
                    price REAL NOT NULL,
                    amount REAL NOT NULL,
                    fee REAL NOT NULL,
                    profit REAL,
                    executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(contract_id) REFERENCES contracts(id)
                )
            """)
            
            # Config Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_contracts_uuid ON contracts(order_uuid);")
            conn.commit()
            print(f"Database initialized at {DB_FILE}")
        finally:
            conn.close()
    await loop.run_in_executor(None, _init)

async def set_config(key: str, value: str):
    await execute_write("""
        INSERT INTO config (key, value, updated_at) 
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET 
            value=excluded.value, 
            updated_at=CURRENT_TIMESTAMP
    """, (key, value))

async def get_config(key: str) -> str:
    row = await execute_read("SELECT value FROM config WHERE key = ?", (key,))
    return row['value'] if row else None

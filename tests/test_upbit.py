import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.upbit_handler import UpbitHandler
from modules.utils import setup_logger

logger = setup_logger()

async def test_websocket_callback(price):
    print(f"WS Price Update: {price}")
    # We only want to see a few updates then stop
    return

async def test_upbit():
    print("--- Starting Upbit API Test ---")
    load_dotenv()
    
    access = os.getenv("UPBIT_ACCESS_KEY")
    secret = os.getenv("UPBIT_SECRET_KEY")
    
    if not access or not secret:
        print("Error: API Keys not found in .env")
        return

    handler = UpbitHandler(access, secret)
    
    # 1. Test Balance (REST)
    print("Testing get_balance...")
    krw = await handler.get_balance("KRW")
    print(f"KRW Balance: {krw}")
    # Note: If no balance, it returns 0
    
    # 2. Test WebSocket
    print("Testing WebSocket (Listen for 5 seconds)...")
    
    # Run WS in background task
    ws_task = asyncio.create_task(handler.connect_websocket("KRW-USDT", test_websocket_callback))
    
    await asyncio.sleep(5)
    
    print(f"Current Price stored in handler: {handler.current_price}")
    assert handler.current_price is not None
    assert handler.current_price > 0
    
    handler.stop_websocket()
    ws_task.cancel()
    
    # 3. Test Order Status (using a fake UUID to see graceful fail)
    print("Testing get_order_status (Fake UUID)...")
    status = await handler.get_order_status("fake-uuid-123")
    if status is None:
        print("Successfully handled fake UUID")
    elif 'error' in status:
        print(f"API Returned Error as expected: {status}")
    
    print("--- Upbit Test Complete ---")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_upbit())
